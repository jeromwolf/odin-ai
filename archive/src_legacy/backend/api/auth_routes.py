"""
인증 관련 API 엔드포인트
회원가입, 로그인, 로그아웃, 토큰 갱신 등
"""

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime, timedelta
import re

from backend.core.database import get_db
from backend.core.security import security_service
from backend.models.user_models import User, UserSession
from backend.services.email_service import email_service
from backend.schemas.auth_schemas import (
    UserCreate, UserLogin, UserResponse,
    TokenResponse, PasswordReset, EmailVerification
)

router = APIRouter(prefix="/api/auth", tags=["인증"])


# ========== 회원가입 ==========

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    회원가입

    - 이메일 중복 확인
    - 비밀번호 강도 검증
    - 이메일 인증 메일 발송
    """
    # 이메일 중복 확인
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="이미 등록된 이메일입니다"
        )

    # 비밀번호 강도 검증
    if not validate_password_strength(user_data.password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="비밀번호는 8자 이상, 대소문자, 숫자, 특수문자를 포함해야 합니다"
        )

    # 이메일 형식 검증
    if not validate_email_format(user_data.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="올바른 이메일 형식이 아닙니다"
        )

    # 사용자 생성
    hashed_password = security_service.get_password_hash(user_data.password)
    new_user = User(
        email=user_data.email,
        password_hash=hashed_password,
        name=user_data.name,
        company_name=user_data.company_name,
        phone=user_data.phone,
        is_active=False,  # 이메일 인증 전까지 비활성화
        created_at=datetime.utcnow()
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # 이메일 인증 토큰 생성
    verification_token = security_service.create_email_verification_token(new_user.email)

    # 백그라운드에서 이메일 발송
    background_tasks.add_task(
        email_service.send_verification_email,
        email=new_user.email,
        name=new_user.name,
        verification_token=verification_token
    )

    return UserResponse(
        id=new_user.id,
        email=new_user.email,
        name=new_user.name,
        company_name=new_user.company_name,
        phone=new_user.phone,
        is_active=new_user.is_active,
        created_at=new_user.created_at,
        message="회원가입이 완료되었습니다. 이메일 인증을 진행해주세요."
    )


# ========== 로그인 ==========

@router.post("/login", response_model=TokenResponse)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """
    로그인

    - 이메일과 비밀번호로 인증
    - JWT 액세스 토큰과 리프레시 토큰 발급
    """
    # 사용자 조회
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not security_service.verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="이메일 또는 비밀번호가 올바르지 않습니다",
            headers={"WWW-Authenticate": "Bearer"}
        )

    # 계정 활성화 확인
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="이메일 인증이 필요합니다"
        )

    # 토큰 생성
    tokens = security_service.create_tokens(
        user_id=user.id,
        email=user.email,
        name=user.name
    )

    # 세션 저장
    session = UserSession(
        user_id=user.id,
        access_token=tokens["access_token"],
        refresh_token=tokens["refresh_token"],
        expires_at=datetime.utcnow() + timedelta(days=7),
        created_at=datetime.utcnow()
    )
    db.add(session)

    # 마지막 로그인 시간 업데이트
    user.last_login_at = datetime.utcnow()
    db.commit()

    return TokenResponse(
        access_token=tokens["access_token"],
        refresh_token=tokens["refresh_token"],
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )


# ========== 로그아웃 ==========

@router.post("/logout")
async def logout(
    token: dict = Depends(security_service.verify_token),
    db: Session = Depends(get_db)
):
    """
    로그아웃

    - 현재 세션 무효화
    """
    user_id = int(token.get("sub"))

    # 해당 사용자의 모든 세션 삭제
    db.query(UserSession).filter(UserSession.user_id == user_id).delete()
    db.commit()

    return {"message": "로그아웃되었습니다"}


# ========== 토큰 갱신 ==========

@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    refresh_token: str,
    db: Session = Depends(get_db)
):
    """
    액세스 토큰 갱신

    - 리프레시 토큰으로 새로운 액세스 토큰 발급
    """
    try:
        # 새로운 액세스 토큰 생성
        new_access_token = security_service.refresh_access_token(refresh_token)

        # 세션 업데이트
        session = db.query(UserSession).filter(
            UserSession.refresh_token == refresh_token
        ).first()

        if session:
            session.access_token = new_access_token
            session.updated_at = datetime.utcnow()
            db.commit()

        return TokenResponse(
            access_token=new_access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="토큰 갱신 실패"
        )


# ========== 이메일 인증 ==========

@router.post("/verify-email")
async def verify_email(
    data: EmailVerification,
    db: Session = Depends(get_db)
):
    """
    이메일 인증

    - 이메일 인증 토큰 확인
    - 계정 활성화
    """
    try:
        # 토큰에서 이메일 추출
        email = security_service.verify_email_token(data.token)

        # 사용자 조회
        user = db.query(User).filter(User.email == email).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="사용자를 찾을 수 없습니다"
            )

        # 이미 인증된 경우
        if user.is_active:
            return {"message": "이미 인증된 계정입니다"}

        # 계정 활성화
        user.is_active = True
        user.email_verified_at = datetime.utcnow()
        db.commit()

        return {"message": "이메일 인증이 완료되었습니다"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="인증 토큰이 유효하지 않습니다"
        )


# ========== 비밀번호 재설정 요청 ==========

@router.post("/request-password-reset")
async def request_password_reset(
    email: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    비밀번호 재설정 요청

    - 이메일로 재설정 링크 발송
    """
    # 사용자 조회
    user = db.query(User).filter(User.email == email).first()
    if not user:
        # 보안상 사용자 존재 여부를 알려주지 않음
        return {"message": "비밀번호 재설정 링크가 이메일로 발송되었습니다"}

    # 재설정 토큰 생성
    reset_token = security_service.create_password_reset_token(user.email)

    # 백그라운드에서 이메일 발송
    background_tasks.add_task(
        email_service.send_password_reset_email,
        email=user.email,
        name=user.name,
        reset_token=reset_token
    )

    return {"message": "비밀번호 재설정 링크가 이메일로 발송되었습니다"}


# ========== 비밀번호 재설정 ==========

@router.post("/reset-password")
async def reset_password(
    data: PasswordReset,
    db: Session = Depends(get_db)
):
    """
    비밀번호 재설정

    - 토큰 확인 후 새 비밀번호 설정
    """
    try:
        # 토큰에서 이메일 추출
        email = security_service.verify_password_reset_token(data.token)

        # 사용자 조회
        user = db.query(User).filter(User.email == email).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="사용자를 찾을 수 없습니다"
            )

        # 비밀번호 강도 검증
        if not validate_password_strength(data.new_password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="비밀번호는 8자 이상, 대소문자, 숫자, 특수문자를 포함해야 합니다"
            )

        # 비밀번호 업데이트
        user.password_hash = security_service.get_password_hash(data.new_password)
        user.updated_at = datetime.utcnow()

        # 모든 세션 무효화
        db.query(UserSession).filter(UserSession.user_id == user.id).delete()

        db.commit()

        return {"message": "비밀번호가 재설정되었습니다. 다시 로그인해주세요."}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="재설정 토큰이 유효하지 않습니다"
        )


# ========== 현재 사용자 정보 ==========

@router.get("/me", response_model=UserResponse)
async def get_current_user(
    token: dict = Depends(security_service.verify_token),
    db: Session = Depends(get_db)
):
    """
    현재 로그인한 사용자 정보 조회
    """
    user_id = int(token.get("sub"))
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="사용자를 찾을 수 없습니다"
        )

    return UserResponse(
        id=user.id,
        email=user.email,
        name=user.name,
        company_name=user.company_name,
        phone=user.phone,
        is_active=user.is_active,
        created_at=user.created_at
    )


# ========== 유틸리티 함수 ==========

def validate_password_strength(password: str) -> bool:
    """비밀번호 강도 검증"""
    if len(password) < 8:
        return False
    if not re.search(r"[A-Z]", password):
        return False
    if not re.search(r"[a-z]", password):
        return False
    if not re.search(r"\d", password):
        return False
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        return False
    return True


def validate_email_format(email: str) -> bool:
    """이메일 형식 검증"""
    email_regex = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return re.match(email_regex, email) is not None