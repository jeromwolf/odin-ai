"""
사용자 인증 API
"""

from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional
from datetime import datetime, timedelta
import logging
from database import get_db_connection
from auth.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    create_refresh_token,
    create_email_verification_token,
    decode_token
)
from auth.dependencies import get_current_user, User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/auth", tags=["authentication"])


# Request/Response 모델
class UserRegister(BaseModel):
    """회원가입 요청"""
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=8, max_length=100)
    full_name: Optional[str] = None
    company: Optional[str] = None
    phone_number: Optional[str] = None

    @validator('username')
    def username_alphanumeric(cls, v):
        assert v.replace('_', '').replace('-', '').isalnum(), '사용자명은 영문, 숫자, -, _만 가능합니다'
        return v


class UserLogin(BaseModel):
    """로그인 요청"""
    email: EmailStr
    password: str


class TokenRefresh(BaseModel):
    """토큰 갱신 요청"""
    refresh_token: str


class TokenResponse(BaseModel):
    """토큰 응답"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class UserResponse(BaseModel):
    """사용자 정보 응답"""
    id: int
    email: str
    username: str
    full_name: Optional[str]
    company: Optional[str]
    is_active: bool
    email_verified: bool
    created_at: datetime


@router.post("/register", response_model=UserResponse)
async def register(user_data: UserRegister):
    """회원가입"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            # 이메일 중복 확인
            check_email_query = "SELECT id FROM users WHERE email = %s"
            cursor.execute(check_email_query, (user_data.email,))
            if cursor.fetchone():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="이미 등록된 이메일입니다"
                )

            # 사용자명 중복 확인
            check_username_query = "SELECT id FROM users WHERE username = %s"
            cursor.execute(check_username_query, (user_data.username,))
            if cursor.fetchone():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="이미 사용중인 사용자명입니다"
                )

            # XSS 방어를 위한 HTML 이스케이프
            import html
            safe_full_name = html.escape(user_data.full_name) if user_data.full_name else None
            safe_company = html.escape(user_data.company) if user_data.company else None

            # 비밀번호 해싱
            hashed_password = get_password_hash(user_data.password)

            # 사용자 생성
            insert_query = """
                INSERT INTO users (
                    email, username, hashed_password, full_name,
                    company, phone_number, is_active, email_verified
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, true, false
                ) RETURNING id, email, username, full_name, company, is_active, email_verified, created_at
            """

            cursor.execute(insert_query, (
                user_data.email,
                user_data.username,
                hashed_password,
                safe_full_name,  # XSS 방어 적용
                safe_company,    # XSS 방어 적용
                user_data.phone_number
            ))

            user_record = cursor.fetchone()
            conn.commit()

            # 이메일 인증 토큰 생성 (실제로는 이메일 전송 필요)
            verification_token = create_email_verification_token()
            token_query = """
                INSERT INTO email_verification_tokens (
                    user_id, token, expires_at
                ) VALUES (%s, %s, %s)
            """
            cursor.execute(token_query, (
                user_record[0],
                verification_token,
                datetime.utcnow() + timedelta(hours=24)
            ))
            conn.commit()

            # TODO: 이메일 발송 로직 추가
            logger.info(f"회원가입 성공: {user_data.email}")
            logger.info(f"인증 토큰: {verification_token}")  # 개발용 로그

            return UserResponse(
                id=user_record[0],
                email=user_record[1],
                username=user_record[2],
                full_name=user_record[3],
                company=user_record[4],
                is_active=user_record[5],
                email_verified=user_record[6],
                created_at=user_record[7]
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"회원가입 실패: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="회원가입 처리 중 오류가 발생했습니다"
        )


@router.post("/login", response_model=TokenResponse)
async def login(credentials: UserLogin):
    """로그인"""
    try:
        # XSS 방어를 위한 HTML 이스케이프
        import html
        safe_email = html.escape(str(credentials.email))

        with get_db_connection() as conn:
            cursor = conn.cursor()

            # 사용자 조회
            query = """
                SELECT id, email, username, hashed_password, is_active
                FROM users
                WHERE email = %s
            """
            cursor.execute(query, (credentials.email,))
            user = cursor.fetchone()

            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="이메일 또는 비밀번호가 일치하지 않습니다"
                )

            # 비밀번호 검증
            if not verify_password(credentials.password, user[3]):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="이메일 또는 비밀번호가 일치하지 않습니다"
                )

            # 활성 사용자 확인
            if not user[4]:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="비활성화된 계정입니다"
                )

            # 토큰 생성
            access_token = create_access_token(data={"sub": str(user[0])})
            refresh_token = create_refresh_token(data={"sub": str(user[0])})

            # 세션 저장
            session_query = """
                INSERT INTO user_sessions (
                    user_id, refresh_token, expires_at
                ) VALUES (%s, %s, %s)
            """
            cursor.execute(session_query, (
                user[0],
                refresh_token,
                datetime.utcnow() + timedelta(days=7)
            ))

            # 마지막 로그인 시간 업데이트
            update_query = "UPDATE users SET last_login = %s WHERE id = %s"
            cursor.execute(update_query, (datetime.utcnow(), user[0]))
            conn.commit()

            return TokenResponse(
                access_token=access_token,
                refresh_token=refresh_token,
                token_type="bearer",
                expires_in=1800  # 30분
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"로그인 실패: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="로그인 처리 중 오류가 발생했습니다"
        )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(token_data: TokenRefresh):
    """토큰 갱신"""
    try:
        # 리프레시 토큰 검증
        payload = decode_token(token_data.refresh_token)
        if not payload or payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="유효하지 않은 리프레시 토큰입니다"
            )

        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="유효하지 않은 리프레시 토큰입니다"
            )

        with get_db_connection() as conn:
            cursor = conn.cursor()

            # 세션 확인
            session_query = """
                SELECT id FROM user_sessions
                WHERE refresh_token = %s AND is_active = true
                AND expires_at > %s
            """
            cursor.execute(session_query, (
                token_data.refresh_token,
                datetime.utcnow()
            ))

            if not cursor.fetchone():
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="세션이 만료되었거나 유효하지 않습니다"
                )

            # 새 토큰 생성
            access_token = create_access_token(data={"sub": user_id})
            new_refresh_token = create_refresh_token(data={"sub": user_id})

            # 리프레시 토큰 업데이트
            update_query = """
                UPDATE user_sessions
                SET refresh_token = %s, expires_at = %s
                WHERE refresh_token = %s
            """
            cursor.execute(update_query, (
                new_refresh_token,
                datetime.utcnow() + timedelta(days=7),
                token_data.refresh_token
            ))
            conn.commit()

            return TokenResponse(
                access_token=access_token,
                refresh_token=new_refresh_token,
                token_type="bearer",
                expires_in=1800
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"토큰 갱신 실패: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="토큰 갱신 중 오류가 발생했습니다"
        )


@router.post("/logout")
async def logout(current_user: User = Depends(get_current_user)):
    """로그아웃"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            # 모든 세션 비활성화
            query = """
                UPDATE user_sessions
                SET is_active = false
                WHERE user_id = %s AND is_active = true
            """
            cursor.execute(query, (current_user.id,))
            conn.commit()

            return {"message": "로그아웃되었습니다"}

    except Exception as e:
        logger.error(f"로그아웃 실패: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="로그아웃 처리 중 오류가 발생했습니다"
        )


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    """현재 사용자 정보"""
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        username=current_user.username,
        full_name=current_user.full_name,
        company=None,  # TODO: company 필드 추가
        is_active=current_user.is_active,
        email_verified=current_user.email_verified,
        created_at=current_user.created_at
    )