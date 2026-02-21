"""
관리자 웹 - 인증 및 권한 관리 API
"""

from fastapi import APIRouter, HTTPException, Depends, Header, Query, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime, timedelta, timezone
from database import get_db_connection
from jose import JWTError, jwt
import logging
import hashlib
import html
import json

logger = logging.getLogger(__name__)

# JWT 설정
from auth.security import SECRET_KEY, ALGORITHM, verify_password, get_password_hash
from middleware.rate_limit import limiter
ACCESS_TOKEN_EXPIRE_MINUTES = 480  # 8시간

router = APIRouter(prefix="/api/admin/auth", tags=["admin-auth"])
security = HTTPBearer()


# ============================================
# Pydantic Models
# ============================================

class AdminLoginRequest(BaseModel):
    """관리자 로그인 요청"""
    email: EmailStr
    password: str


class AdminLoginResponse(BaseModel):
    """관리자 로그인 응답"""
    access_token: str
    token_type: str
    admin_info: dict


class AdminInfo(BaseModel):
    """관리자 정보"""
    id: int
    email: str
    username: str
    role: str
    last_login: Optional[datetime]


# ============================================
# Helper Functions
# ============================================

def create_admin_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """관리자 JWT 토큰 생성"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire, "type": "admin_access"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def safe_user_id(user_id: int) -> str:
    """사용자 ID를 해시 처리하여 안전하게 로깅"""
    return hashlib.sha256(str(user_id).encode()).hexdigest()[:8]


async def get_current_admin(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """
    현재 로그인한 관리자 정보 조회 (Dependency)

    JWT 토큰을 검증하고 관리자 정보를 반환합니다.
    """
    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        admin_id: int = payload.get("sub")
        role: str = payload.get("role")

        if admin_id is None:
            raise HTTPException(status_code=401, detail="인증 정보가 유효하지 않습니다")

        # 관리자 권한 확인
        if role not in ["admin", "super_admin"]:
            raise HTTPException(status_code=403, detail="관리자 권한이 필요합니다")

        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, email, username, full_name, is_active, is_superuser
                FROM users
                WHERE id = %s
            """, (admin_id,))

            row = cursor.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다")

            if not row[4]:  # is_active
                raise HTTPException(status_code=403, detail="비활성화된 계정입니다")

            if not row[5]:  # is_superuser
                raise HTTPException(status_code=403, detail="관리자 권한이 해제되었습니다")

            return {
                "id": row[0],
                "email": row[1],
                "username": row[2],
                "full_name": row[3],
                "role": "super_admin" if row[5] else "admin"
            }

    except JWTError:
        raise HTTPException(status_code=401, detail="토큰이 유효하지 않습니다")
    except Exception as e:
        logger.error(f"인증 처리 실패: {e}")
        raise HTTPException(status_code=500, detail="서버 내부 오류가 발생했습니다")


# ============================================
# API Endpoints
# ============================================

@limiter.limit("5/minute")
@router.post("/login", response_model=AdminLoginResponse)
async def admin_login(request: Request, login_data: AdminLoginRequest):
    """
    관리자 로그인

    - 이메일과 비밀번호로 인증
    - JWT 토큰 발급
    - 관리자 권한 확인
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            # 사용자 조회
            cursor.execute("""
                SELECT id, email, username, full_name, hashed_password, is_active, is_superuser
                FROM users
                WHERE email = %s
            """, (login_data.email,))

            row = cursor.fetchone()

            if not row:
                logger.warning(f"로그인 실패: 존재하지 않는 이메일 ({html.escape(str(login_data.email))})")
                raise HTTPException(status_code=401, detail="이메일 또는 비밀번호가 올바르지 않습니다")

            user_id, email, username, full_name, hashed_password, is_active, is_superuser = row

            # 계정 활성화 확인
            if not is_active:
                logger.warning(f"로그인 실패: 비활성화된 계정 (user_hash: {safe_user_id(user_id)})")
                raise HTTPException(status_code=403, detail="비활성화된 계정입니다")

            # 비밀번호 검증
            if not verify_password(login_data.password, hashed_password):
                logger.warning(f"로그인 실패: 잘못된 비밀번호 (user_hash: {safe_user_id(user_id)})")
                raise HTTPException(status_code=401, detail="이메일 또는 비밀번호가 올바르지 않습니다")

            # 관리자 권한 확인 (is_superuser 컬럼 기반)
            if not is_superuser:
                logger.warning(f"로그인 실패: 관리자 권한 없음 (user_hash: {safe_user_id(user_id)})")
                raise HTTPException(status_code=403, detail="관리자 권한이 없습니다")

            role = "super_admin" if is_superuser else "admin"

            # JWT 토큰 생성
            access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
            access_token = create_admin_access_token(
                data={"sub": user_id, "email": email, "role": role},
                expires_delta=access_token_expires
            )

            # 마지막 로그인 시간 업데이트
            cursor.execute("""
                UPDATE users
                SET last_login = NOW()
                WHERE id = %s
            """, (user_id,))

            # 관리자 활동 로그 기록
            login_details = json.dumps({"description": "관리자 로그인 성공", "email": email})
            cursor.execute("""
                INSERT INTO admin_activity_logs (admin_user_id, action, details)
                VALUES (%s, %s, %s::jsonb)
            """, (user_id, 'login', login_details))
            conn.commit()

            logger.info(f"관리자 로그인 성공 (user_hash: {safe_user_id(user_id)}, role: {role})")

            return AdminLoginResponse(
                access_token=access_token,
                token_type="bearer",
                admin_info={
                    "id": user_id,
                    "email": email,
                    "username": username,
                    "full_name": full_name,
                    "role": role
                }
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"로그인 처리 실패: {e}")
        raise HTTPException(status_code=500, detail="서버 내부 오류가 발생했습니다")


@router.post("/logout")
async def admin_logout(current_admin: dict = Depends(get_current_admin)):
    """
    관리자 로그아웃

    - 활동 로그 기록
    - 실제 토큰 무효화는 클라이언트에서 처리
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            # 관리자 활동 로그 기록
            logout_details = json.dumps({"description": "관리자 로그아웃", "email": current_admin["email"]})
            cursor.execute("""
                INSERT INTO admin_activity_logs (admin_user_id, action, details)
                VALUES (%s, %s, %s::jsonb)
            """, (current_admin["id"], 'logout', logout_details))
            conn.commit()

            logger.info(f"관리자 로그아웃 (user_hash: {safe_user_id(current_admin['id'])})")

            return {"message": "로그아웃되었습니다"}

    except Exception as e:
        logger.error(f"로그아웃 처리 실패: {e}")
        raise HTTPException(status_code=500, detail="서버 내부 오류가 발생했습니다")


@router.get("/me", response_model=AdminInfo)
async def get_current_admin_info(current_admin: dict = Depends(get_current_admin)):
    """
    현재 로그인한 관리자 정보 조회

    - JWT 토큰 기반 인증
    - 관리자 상세 정보 반환
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                SELECT id, email, username, last_login
                FROM users
                WHERE id = %s
            """, (current_admin["id"],))

            row = cursor.fetchone()

            if not row:
                raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다")

            return AdminInfo(
                id=row[0],
                email=row[1],
                username=row[2],
                role=current_admin["role"],
                last_login=row[3]
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"관리자 정보 조회 실패: {e}")
        raise HTTPException(status_code=500, detail="서버 내부 오류가 발생했습니다")


@router.get("/activity-logs")
async def get_admin_activity_logs(
    current_admin: dict = Depends(get_current_admin),
    limit: int = Query(50, ge=1, le=500)
):
    """
    관리자 활동 로그 조회

    - 최근 활동 내역
    - 본인 활동만 조회 (super_admin은 전체 조회 가능)
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            # super_admin은 모든 로그 조회 가능
            if current_admin["role"] == "super_admin":
                query = """
                    SELECT aal.id, aal.admin_user_id, u.email, u.username,
                           aal.activity_type, aal.description, aal.created_at
                    FROM admin_activity_logs aal
                    JOIN users u ON aal.admin_user_id = u.id
                    ORDER BY aal.created_at DESC
                    LIMIT %s
                """
                cursor.execute(query, (limit,))
            else:
                query = """
                    SELECT aal.id, aal.admin_user_id, u.email, u.username,
                           aal.activity_type, aal.description, aal.created_at
                    FROM admin_activity_logs aal
                    JOIN users u ON aal.admin_user_id = u.id
                    WHERE aal.admin_user_id = %s
                    ORDER BY aal.created_at DESC
                    LIMIT %s
                """
                cursor.execute(query, (current_admin["id"], limit))

            logs = []
            for row in cursor.fetchall():
                logs.append({
                    "id": row[0],
                    "admin_user_id": row[1],
                    "email": row[2],
                    "username": row[3],
                    "activity_type": row[4],
                    "description": row[5],
                    "created_at": row[6].isoformat()
                })

            return {"logs": logs, "total": len(logs)}

    except Exception as e:
        logger.error(f"활동 로그 조회 실패: {e}")
        raise HTTPException(status_code=500, detail="서버 내부 오류가 발생했습니다")
