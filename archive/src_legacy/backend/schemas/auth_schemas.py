"""
인증 관련 Pydantic 스키마
"""

from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime


# ========== 회원가입 ==========

class UserCreate(BaseModel):
    """회원가입 요청 스키마"""
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=100)
    name: str = Field(..., min_length=2, max_length=50)
    company_name: Optional[str] = Field(None, max_length=100)
    phone: Optional[str] = Field(None, regex=r"^\d{2,3}-\d{3,4}-\d{4}$")

    class Config:
        schema_extra = {
            "example": {
                "email": "user@example.com",
                "password": "SecurePass123!",
                "name": "홍길동",
                "company_name": "오딘AI",
                "phone": "010-1234-5678"
            }
        }


# ========== 로그인 ==========

class UserLogin(BaseModel):
    """로그인 요청 스키마"""
    email: EmailStr
    password: str

    class Config:
        schema_extra = {
            "example": {
                "email": "user@example.com",
                "password": "SecurePass123!"
            }
        }


# ========== 토큰 ==========

class TokenResponse(BaseModel):
    """토큰 응답 스키마"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds

    class Config:
        schema_extra = {
            "example": {
                "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
                "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
                "token_type": "bearer",
                "expires_in": 3600
            }
        }


class TokenData(BaseModel):
    """토큰 데이터 스키마"""
    sub: str  # user_id
    email: Optional[str] = None
    name: Optional[str] = None
    type: str  # access, refresh, email_verification, password_reset


# ========== 사용자 응답 ==========

class UserResponse(BaseModel):
    """사용자 응답 스키마"""
    id: int
    email: str
    name: str
    company_name: Optional[str]
    phone: Optional[str]
    is_active: bool
    created_at: datetime
    message: Optional[str] = None

    class Config:
        orm_mode = True
        schema_extra = {
            "example": {
                "id": 1,
                "email": "user@example.com",
                "name": "홍길동",
                "company_name": "오딘AI",
                "phone": "010-1234-5678",
                "is_active": True,
                "created_at": "2025-09-17T10:00:00Z"
            }
        }


class UserUpdate(BaseModel):
    """사용자 정보 수정 스키마"""
    name: Optional[str] = Field(None, min_length=2, max_length=50)
    company_name: Optional[str] = Field(None, max_length=100)
    phone: Optional[str] = Field(None, regex=r"^\d{2,3}-\d{3,4}-\d{4}$")

    class Config:
        schema_extra = {
            "example": {
                "name": "홍길동",
                "company_name": "오딘AI",
                "phone": "010-1234-5678"
            }
        }


# ========== 비밀번호 ==========

class PasswordChange(BaseModel):
    """비밀번호 변경 스키마"""
    current_password: str
    new_password: str = Field(..., min_length=8, max_length=100)

    class Config:
        schema_extra = {
            "example": {
                "current_password": "OldPass123!",
                "new_password": "NewPass456!"
            }
        }


class PasswordReset(BaseModel):
    """비밀번호 재설정 스키마"""
    token: str
    new_password: str = Field(..., min_length=8, max_length=100)

    class Config:
        schema_extra = {
            "example": {
                "token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
                "new_password": "NewSecurePass789!"
            }
        }


class PasswordResetRequest(BaseModel):
    """비밀번호 재설정 요청 스키마"""
    email: EmailStr

    class Config:
        schema_extra = {
            "example": {
                "email": "user@example.com"
            }
        }


# ========== 이메일 인증 ==========

class EmailVerification(BaseModel):
    """이메일 인증 스키마"""
    token: str

    class Config:
        schema_extra = {
            "example": {
                "token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
            }
        }


class ResendEmailVerification(BaseModel):
    """이메일 인증 재발송 스키마"""
    email: EmailStr

    class Config:
        schema_extra = {
            "example": {
                "email": "user@example.com"
            }
        }