"""
사용자 인증 API
"""

from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional
from datetime import datetime, timedelta, timezone
import html
import logging
from database import get_db_connection
from errors import ErrorCode, ApiError
from psycopg2.extras import RealDictCursor
from auth.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    create_refresh_token,
    create_email_verification_token,
    decode_token
)
from auth.dependencies import get_current_user, get_current_user_optional, User
from middleware.rate_limit import limiter
from services.email_service import send_verification_email

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
    marketing_consent: Optional[bool] = False

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


class EmailVerifyRequest(BaseModel):
    """이메일 인증 요청"""
    token: str


class ResendVerificationRequest(BaseModel):
    """인증 메일 재발송 요청"""
    email: EmailStr


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
    role: str = "user"  # "admin" or "user"


@router.post("/register", response_model=UserResponse)
async def register(user_data: UserRegister):
    """회원가입"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)

            # 이메일 중복 확인
            check_email_query = "SELECT id FROM users WHERE email = %s"
            cursor.execute(check_email_query, (user_data.email,))
            if cursor.fetchone():
                raise ApiError(400, ErrorCode.AUTH_DUPLICATE_EMAIL, "이미 등록된 이메일입니다")

            # 사용자명 중복 확인
            check_username_query = "SELECT id FROM users WHERE username = %s"
            cursor.execute(check_username_query, (user_data.username,))
            if cursor.fetchone():
                raise ApiError(400, ErrorCode.AUTH_DUPLICATE_EMAIL, "이미 사용중인 사용자명입니다")

            # XSS 방어를 위한 HTML 이스케이프
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

            # 이메일 인증 토큰 생성 (실제로는 이메일 전송 필요)
            verification_token = create_email_verification_token()
            token_query = """
                INSERT INTO email_verification_tokens (
                    user_id, token, expires_at
                ) VALUES (%s, %s, %s)
            """
            cursor.execute(token_query, (
                user_record['id'],
                verification_token,
                datetime.now(timezone.utc) + timedelta(hours=24)
            ))
            conn.commit()

            logger.info(f"회원가입 성공: {user_data.email} (인증토큰: {verification_token[:8]}...)")

            # 이메일 인증 메일 발송 (실패해도 회원가입은 성공으로 처리)
            try:
                send_verification_email(
                    to_email=user_data.email,
                    token=verification_token,
                    username=user_data.username
                )
            except Exception as email_err:
                logger.warning(f"인증 메일 발송 실패 (회원가입은 완료됨): {email_err}")

            return UserResponse(
                id=user_record['id'],
                email=user_record['email'],
                username=user_record['username'],
                full_name=user_record['full_name'],
                company=user_record['company'],
                is_active=user_record['is_active'],
                email_verified=user_record['email_verified'],
                created_at=user_record['created_at']
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"회원가입 실패: {e}")
        raise ApiError(500, ErrorCode.SERVER_ERROR, "회원가입 처리 중 오류가 발생했습니다")


@limiter.limit("5/minute")
@router.post("/login", response_model=TokenResponse)
async def login(request: Request, credentials: UserLogin):
    """로그인"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)

            # 사용자 조회
            query = """
                SELECT id, email, username, hashed_password, is_active
                FROM users
                WHERE email = %s
            """
            cursor.execute(query, (credentials.email,))
            user = cursor.fetchone()

            if not user:
                raise ApiError(401, ErrorCode.AUTH_LOGIN_FAILED, "이메일 또는 비밀번호가 일치하지 않습니다")

            # 비밀번호 검증
            if not verify_password(credentials.password, user['hashed_password']):
                raise ApiError(401, ErrorCode.AUTH_LOGIN_FAILED, "이메일 또는 비밀번호가 일치하지 않습니다")

            # 활성 사용자 확인
            if not user['is_active']:
                raise ApiError(403, ErrorCode.AUTH_INACTIVE_USER, "비활성화된 계정입니다")

            # 토큰 생성
            access_token = create_access_token(data={"sub": str(user['id'])})
            refresh_token = create_refresh_token(data={"sub": str(user['id'])})

            # 세션 저장
            session_query = """
                INSERT INTO user_sessions (
                    user_id, refresh_token, expires_at
                ) VALUES (%s, %s, %s)
            """
            cursor.execute(session_query, (
                user['id'],
                refresh_token,
                datetime.now(timezone.utc) + timedelta(days=7)
            ))

            # 마지막 로그인 시간 업데이트
            update_query = "UPDATE users SET last_login = %s WHERE id = %s"
            cursor.execute(update_query, (datetime.now(timezone.utc), user['id']))
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
        raise ApiError(500, ErrorCode.SERVER_ERROR, "로그인 처리 중 오류가 발생했습니다")


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(token_data: TokenRefresh):
    """토큰 갱신"""
    try:
        # 리프레시 토큰 검증
        payload = decode_token(token_data.refresh_token)
        if not payload or payload.get("type") != "refresh":
            raise ApiError(401, ErrorCode.AUTH_TOKEN_INVALID, "유효하지 않은 리프레시 토큰입니다")

        user_id = payload.get("sub")
        if not user_id:
            raise ApiError(401, ErrorCode.AUTH_TOKEN_INVALID, "유효하지 않은 리프레시 토큰입니다")

        with get_db_connection() as conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)

            # 세션 확인
            session_query = """
                SELECT id FROM user_sessions
                WHERE refresh_token = %s AND is_active = true
                AND expires_at > %s
            """
            cursor.execute(session_query, (
                token_data.refresh_token,
                datetime.now(timezone.utc)
            ))

            if not cursor.fetchone():
                raise ApiError(401, ErrorCode.AUTH_TOKEN_EXPIRED, "세션이 만료되었거나 유효하지 않습니다")

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
                datetime.now(timezone.utc) + timedelta(days=7),
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
        raise ApiError(500, ErrorCode.SERVER_ERROR, "토큰 갱신 중 오류가 발생했습니다")


@router.post("/logout")
async def logout(current_user: User = Depends(get_current_user_optional)):
    """로그아웃"""
    try:
        # 토큰이 유효하지 않아도 로그아웃 성공으로 처리 (클라이언트에서 토큰 제거 필요)
        if current_user:
            with get_db_connection() as conn:
                cursor = conn.cursor(cursor_factory=RealDictCursor)

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
        # 로그아웃은 실패해도 성공으로 처리 (클라이언트에서 토큰 제거해야 함)
        return {"message": "로그아웃되었습니다"}


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
        created_at=current_user.created_at,
        role="admin" if current_user.is_superuser else "user"
    )


@router.post("/verify-email")
async def verify_email(request: EmailVerifyRequest):
    """이메일 인증 토큰 검증"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)

            # 토큰 조회
            token_query = """
                SELECT id, user_id, expires_at, used
                FROM email_verification_tokens
                WHERE token = %s
            """
            cursor.execute(token_query, (request.token,))
            token_record = cursor.fetchone()

            if not token_record:
                raise ApiError(400, ErrorCode.AUTH_TOKEN_INVALID, "유효하지 않은 인증 토큰입니다")

            token_id = token_record['id']
            user_id = token_record['user_id']
            expires_at = token_record['expires_at']
            used = token_record['used']

            if used:
                raise ApiError(400, ErrorCode.AUTH_TOKEN_INVALID, "이미 사용된 인증 토큰입니다")

            # 만료 확인 (expires_at이 timezone-naive일 수 있으므로 변환)
            now_utc = datetime.now(timezone.utc)
            if expires_at.tzinfo is None:
                expires_at = expires_at.replace(tzinfo=timezone.utc)

            if now_utc > expires_at:
                raise ApiError(400, ErrorCode.AUTH_TOKEN_EXPIRED, "만료된 인증 토큰입니다. 인증 메일을 재발송해 주세요")

            # 이메일 인증 완료 처리
            cursor.execute(
                "UPDATE users SET email_verified = true WHERE id = %s",
                (user_id,)
            )
            cursor.execute(
                "UPDATE email_verification_tokens SET used = true WHERE id = %s",
                (token_id,)
            )
            conn.commit()

            logger.info(f"이메일 인증 완료: user_id={user_id}")
            return {"message": "이메일 인증이 완료되었습니다"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"이메일 인증 실패: {e}")
        raise ApiError(500, ErrorCode.SERVER_ERROR, "이메일 인증 처리 중 오류가 발생했습니다")


@limiter.limit("3/minute")
@router.post("/resend-verification")
async def resend_verification(request: Request, body: ResendVerificationRequest):
    """이메일 인증 메일 재발송"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)

            # 사용자 조회
            cursor.execute(
                "SELECT id, username, email_verified FROM users WHERE email = %s AND is_active = true",
                (body.email,)
            )
            user = cursor.fetchone()

            # 사용자가 없어도 동일한 응답 반환 (이메일 열거 공격 방지)
            if not user:
                return {"message": "인증 메일을 발송했습니다. 메일함을 확인해 주세요"}

            user_id = user['id']
            username = user['username']
            email_verified = user['email_verified']

            if email_verified:
                raise ApiError(400, ErrorCode.VALIDATION_FAILED, "이미 이메일 인증이 완료된 계정입니다")

            # 기존 미사용 토큰 만료 처리
            cursor.execute(
                "UPDATE email_verification_tokens SET used = true WHERE user_id = %s AND used = false",
                (user_id,)
            )

            # 새 토큰 생성
            new_token = create_email_verification_token()
            cursor.execute(
                """
                INSERT INTO email_verification_tokens (user_id, token, expires_at)
                VALUES (%s, %s, %s)
                """,
                (user_id, new_token, datetime.now(timezone.utc) + timedelta(hours=24))
            )
            conn.commit()

        # 이메일 발송 (DB 트랜잭션 완료 후)
        try:
            send_verification_email(
                to_email=body.email,
                token=new_token,
                username=username
            )
        except Exception as email_err:
            logger.warning(f"인증 메일 재발송 실패: {email_err}")

        return {"message": "인증 메일을 발송했습니다. 메일함을 확인해 주세요"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"인증 메일 재발송 실패: {e}")
        raise ApiError(500, ErrorCode.SERVER_ERROR, "인증 메일 재발송 중 오류가 발생했습니다")