"""
보안 관련 유틸리티
JWT 토큰 생성, 검증 및 비밀번호 해싱
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import jwt
from passlib.context import CryptContext
from fastapi import HTTPException, Security, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from backend.core.config import settings

# 비밀번호 해싱 설정
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT Bearer 인증
security = HTTPBearer()


class SecurityService:
    """보안 서비스"""

    def __init__(self):
        """서비스 초기화"""
        self.secret_key = settings.SECRET_KEY
        self.algorithm = settings.ALGORITHM
        self.access_token_expire_minutes = settings.ACCESS_TOKEN_EXPIRE_MINUTES
        self.refresh_token_expire_days = settings.REFRESH_TOKEN_EXPIRE_DAYS

    # ========== 비밀번호 관련 ==========

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """비밀번호 검증"""
        return pwd_context.verify(plain_password, hashed_password)

    @staticmethod
    def get_password_hash(password: str) -> str:
        """비밀번호 해싱"""
        return pwd_context.hash(password)

    # ========== JWT 토큰 관련 ==========

    def create_access_token(self, data: Dict[str, Any]) -> str:
        """액세스 토큰 생성"""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)
        to_encode.update({
            "exp": expire,
            "type": "access"
        })
        return jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)

    def create_refresh_token(self, data: Dict[str, Any]) -> str:
        """리프레시 토큰 생성"""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=self.refresh_token_expire_days)
        to_encode.update({
            "exp": expire,
            "type": "refresh"
        })
        return jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)

    def decode_token(self, token: str) -> Dict[str, Any]:
        """토큰 디코드"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired"
            )
        except jwt.JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )

    def verify_token(self, credentials: HTTPAuthorizationCredentials = Security(security)) -> Dict[str, Any]:
        """토큰 검증 (의존성 주입용)"""
        token = credentials.credentials
        payload = self.decode_token(token)

        # 토큰 타입 확인
        if payload.get("type") != "access":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type"
            )

        return payload

    def refresh_access_token(self, refresh_token: str) -> str:
        """리프레시 토큰으로 액세스 토큰 재발급"""
        payload = self.decode_token(refresh_token)

        # 리프레시 토큰 타입 확인
        if payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type"
            )

        # 새로운 액세스 토큰 생성
        user_data = {
            "sub": payload.get("sub"),
            "email": payload.get("email"),
            "name": payload.get("name")
        }
        return self.create_access_token(user_data)

    # ========== 토큰 생성 헬퍼 ==========

    def create_tokens(self, user_id: int, email: str, name: str) -> Dict[str, str]:
        """액세스 토큰과 리프레시 토큰 쌍 생성"""
        user_data = {
            "sub": str(user_id),
            "email": email,
            "name": name
        }

        return {
            "access_token": self.create_access_token(user_data),
            "refresh_token": self.create_refresh_token(user_data),
            "token_type": "bearer"
        }

    # ========== 이메일 검증 토큰 ==========

    def create_email_verification_token(self, email: str) -> str:
        """이메일 검증 토큰 생성"""
        data = {
            "email": email,
            "type": "email_verification"
        }
        expire = datetime.utcnow() + timedelta(hours=24)
        data["exp"] = expire
        return jwt.encode(data, self.secret_key, algorithm=self.algorithm)

    def verify_email_token(self, token: str) -> str:
        """이메일 검증 토큰 확인"""
        payload = self.decode_token(token)

        if payload.get("type") != "email_verification":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid token type"
            )

        return payload.get("email")

    # ========== 비밀번호 재설정 토큰 ==========

    def create_password_reset_token(self, email: str) -> str:
        """비밀번호 재설정 토큰 생성"""
        data = {
            "email": email,
            "type": "password_reset"
        }
        expire = datetime.utcnow() + timedelta(hours=1)
        data["exp"] = expire
        return jwt.encode(data, self.secret_key, algorithm=self.algorithm)

    def verify_password_reset_token(self, token: str) -> str:
        """비밀번호 재설정 토큰 확인"""
        payload = self.decode_token(token)

        if payload.get("type") != "password_reset":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid token type"
            )

        return payload.get("email")


# 전역 보안 서비스 인스턴스
security_service = SecurityService()