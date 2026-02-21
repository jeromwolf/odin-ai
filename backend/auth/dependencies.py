"""
인증 의존성 및 미들웨어
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
from datetime import datetime, timezone
from database import get_db_connection
from .security import decode_token
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
            cursor = conn.cursor()
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
                'id': user_data[0],
                'email': user_data[1],
                'username': user_data[2],
                'full_name': user_data[3],
                'is_active': user_data[4],
                'is_superuser': user_data[5],
                'email_verified': user_data[6],
                'created_at': user_data[7]
            })

            # 마지막 로그인 시간 업데이트
            update_query = "UPDATE users SET last_login = %s WHERE id = %s"
            cursor.execute(update_query, (datetime.now(timezone.utc), user_id))
            conn.commit()

            return user

    except Exception as e:
        logger.error(f"사용자 인증 오류: {e}")
        return None


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)
) -> User:
    """현재 사용자 가져오기 (필수)"""
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="인증 토큰이 필요합니다",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = await get_current_user_optional(credentials)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="유효하지 않은 인증 정보입니다",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """활성 사용자 확인"""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="비활성 사용자입니다"
        )
    return current_user


async def get_current_verified_user(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """이메일 인증된 사용자 확인"""
    if not current_user.email_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="이메일 인증이 필요합니다"
        )
    return current_user


async def get_current_superuser(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """관리자 확인"""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="관리자 권한이 필요합니다"
        )
    return current_user