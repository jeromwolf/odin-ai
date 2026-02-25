"""
인증 의존성 및 미들웨어
"""

from fastapi import Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
from datetime import datetime, timezone
from database import get_db_connection
from .security import decode_token
from psycopg2.extras import RealDictCursor
from errors import ErrorCode, ApiError
import logging

logger = logging.getLogger(__name__)

# Bearer 토큰 스키마
bearer_scheme = HTTPBearer(auto_error=False)


class User:
    """사용자 모델"""
    def __init__(self, user_data: dict):
        self.id = user_data.get('id')
        self.email = user_data.get('email')
        self.username = user_data.get('username')
        self.full_name = user_data.get('full_name')
        self.is_active = user_data.get('is_active', True)
        self.is_superuser = user_data.get('is_superuser', False)
        self.email_verified = user_data.get('email_verified', False)
        self.created_at = user_data.get('created_at')


async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme)
) -> Optional[User]:
    """현재 사용자 가져오기 (선택적)"""
    if not credentials:
        return None

    try:
        # 토큰 디코드
        payload = decode_token(credentials.credentials)
        if not payload:
            return None

        # 토큰 타입 확인
        if payload.get("type") != "access":
            return None

        user_id = payload.get("sub")
        if not user_id:
            return None

        # 데이터베이스에서 사용자 조회
        with get_db_connection() as conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            query = """
                SELECT id, email, username, full_name, is_active,
                       is_superuser, email_verified, created_at
                FROM users
                WHERE id = %s AND is_active = true
            """
            cursor.execute(query, (user_id,))
            user_data = cursor.fetchone()

            if not user_data:
                return None

            # 사용자 객체 생성
            user = User({
                'id': user_data['id'],
                'email': user_data['email'],
                'username': user_data['username'],
                'full_name': user_data['full_name'],
                'is_active': user_data['is_active'],
                'is_superuser': user_data['is_superuser'],
                'email_verified': user_data['email_verified'],
                'created_at': user_data['created_at']
            })

            # last_login은 로그인 시에만 갱신 (auth.py login 엔드포인트에서 처리)
            return user

    except Exception as e:
        logger.error(f"사용자 인증 오류: {e}")
        return None


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)
) -> User:
    """현재 사용자 가져오기 (필수)"""
    if not credentials:
        raise ApiError(401, ErrorCode.AUTH_REQUIRED, "인증 토큰이 필요합니다")

    user = await get_current_user_optional(credentials)
    if not user:
        raise ApiError(401, ErrorCode.AUTH_TOKEN_INVALID, "유효하지 않은 인증 정보입니다")

    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """활성 사용자 확인"""
    if not current_user.is_active:
        raise ApiError(400, ErrorCode.AUTH_INACTIVE_USER, "비활성 사용자입니다")
    return current_user


async def get_current_verified_user(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """이메일 인증된 사용자 확인"""
    if not current_user.email_verified:
        raise ApiError(400, ErrorCode.AUTH_EMAIL_NOT_VERIFIED, "이메일 인증이 필요합니다")
    return current_user


async def get_current_superuser(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """관리자 확인"""
    if not current_user.is_superuser:
        raise ApiError(403, ErrorCode.AUTH_FORBIDDEN, "관리자 권한이 필요합니다")
    return current_user