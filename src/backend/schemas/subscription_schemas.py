"""
구독 관련 Pydantic 스키마
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any, List
from datetime import datetime
from decimal import Decimal
from enum import Enum

from backend.models.subscription_models import SubscriptionPlan, PaymentStatus


# ========== 구독 플랜 스키마 ==========

class PlanDetailResponse(BaseModel):
    """구독 플랜 상세 응답"""
    id: int
    plan_type: SubscriptionPlan
    plan_name: str
    display_name: str
    monthly_price: float
    annual_price: Optional[float]
    discount_rate: int
    max_searches_per_month: int
    max_bookmarks: int
    max_email_alerts: int
    max_api_calls: int
    max_users: int
    features: Dict[str, bool]
    description: Optional[str]
    highlights: Optional[List[str]]
    is_popular: bool
    is_recommended: bool

    class Config:
        orm_mode = True
        schema_extra = {
            "example": {
                "id": 1,
                "plan_type": "professional",
                "plan_name": "프로페셔널",
                "display_name": "Professional Plan",
                "monthly_price": 99000,
                "annual_price": 990000,
                "discount_rate": 17,
                "max_searches_per_month": 5000,
                "max_bookmarks": 500,
                "max_email_alerts": 100,
                "max_api_calls": 10000,
                "max_users": 5,
                "features": {
                    "basic_search": True,
                    "advanced_search": True,
                    "ai_analysis": True,
                    "api_access": True,
                    "custom_alerts": True,
                    "export_data": True,
                    "priority_support": True,
                    "dedicated_manager": False
                },
                "description": "성장하는 기업을 위한 전문가 플랜",
                "highlights": [
                    "AI 기반 입찰 분석",
                    "무제한 검색",
                    "API 접근",
                    "우선 지원"
                ],
                "is_popular": True,
                "is_recommended": True
            }
        }


# ========== 구독 스키마 ==========

class SubscriptionResponse(BaseModel):
    """구독 정보 응답"""
    id: int
    user_id: int
    plan_type: SubscriptionPlan
    plan_name: str
    is_active: bool
    is_trial: bool
    started_at: datetime
    expires_at: Optional[datetime]
    trial_ends_at: Optional[datetime]
    payment_method: Optional[str]
    next_billing_date: Optional[datetime]
    monthly_price: float
    max_searches_per_month: int
    max_bookmarks: int
    max_email_alerts: int
    max_api_calls: int
    features: Optional[Dict[str, bool]]
    current_searches: int
    current_api_calls: int
    usage_reset_date: Optional[datetime]
    cancelled_at: Optional[datetime]

    class Config:
        orm_mode = True
        schema_extra = {
            "example": {
                "id": 1,
                "user_id": 123,
                "plan_type": "professional",
                "plan_name": "프로페셔널",
                "is_active": True,
                "is_trial": False,
                "started_at": "2025-01-01T00:00:00Z",
                "expires_at": None,
                "trial_ends_at": None,
                "payment_method": "card",
                "next_billing_date": "2025-10-01T00:00:00Z",
                "monthly_price": 99000,
                "max_searches_per_month": 5000,
                "max_bookmarks": 500,
                "max_email_alerts": 100,
                "max_api_calls": 10000,
                "features": {
                    "ai_analysis": True,
                    "api_access": True
                },
                "current_searches": 1250,
                "current_api_calls": 3200,
                "usage_reset_date": "2025-10-01T00:00:00Z",
                "cancelled_at": None
            }
        }


class SubscriptionUpgrade(BaseModel):
    """구독 업그레이드 요청"""
    new_plan_type: SubscriptionPlan = Field(..., description="새 플랜 타입")
    apply_immediately: bool = Field(False, description="즉시 적용 여부")
    coupon_code: Optional[str] = Field(None, description="쿠폰 코드")

    class Config:
        schema_extra = {
            "example": {
                "new_plan_type": "enterprise",
                "apply_immediately": True,
                "coupon_code": "UPGRADE20"
            }
        }


# ========== 결제 스키마 ==========

class PaymentRequest(BaseModel):
    """결제 요청"""
    plan_type: SubscriptionPlan = Field(..., description="플랜 타입")
    payment_method: str = Field(..., description="결제 방법")
    billing_period: str = Field("monthly", description="결제 주기")
    coupon_code: Optional[str] = Field(None, description="쿠폰 코드")
    card_number: Optional[str] = Field(None, description="카드 번호")
    card_expiry: Optional[str] = Field(None, description="카드 유효기간")
    card_cvc: Optional[str] = Field(None, description="CVC")

    @validator('card_number')
    def validate_card_number(cls, v):
        if v:
            # 카드 번호 마스킹
            return v[-4:].rjust(len(v), '*')
        return v

    class Config:
        schema_extra = {
            "example": {
                "plan_type": "professional",
                "payment_method": "card",
                "billing_period": "monthly",
                "coupon_code": "NEWUSER20",
                "card_number": "1234-5678-9012-3456",
                "card_expiry": "12/25",
                "card_cvc": "123"
            }
        }


class PaymentResponse(BaseModel):
    """결제 응답"""
    id: int
    amount: float
    currency: str
    status: PaymentStatus
    payment_method: str
    transaction_id: Optional[str]
    receipt_url: Optional[str]
    billing_period_start: datetime
    billing_period_end: datetime
    processed_at: Optional[datetime]

    class Config:
        orm_mode = True
        schema_extra = {
            "example": {
                "id": 1,
                "amount": 99000,
                "currency": "KRW",
                "status": "completed",
                "payment_method": "card",
                "transaction_id": "txn_1234567890",
                "receipt_url": "https://receipts.example.com/1234567890",
                "billing_period_start": "2025-09-01T00:00:00Z",
                "billing_period_end": "2025-10-01T00:00:00Z",
                "processed_at": "2025-09-01T10:30:00Z"
            }
        }


# ========== 사용량 스키마 ==========

class UsageResponse(BaseModel):
    """사용량 응답"""
    period: str
    start_date: datetime
    end_date: datetime
    usage_summary: Dict[str, int]
    usage_percentage: Dict[str, float]
    limits: Dict[str, int]

    class Config:
        schema_extra = {
            "example": {
                "period": "current",
                "start_date": "2025-09-01T00:00:00Z",
                "end_date": "2025-09-17T00:00:00Z",
                "usage_summary": {
                    "search": 1250,
                    "api_call": 3200,
                    "bookmark": 45,
                    "email": 23
                },
                "usage_percentage": {
                    "search": 25.0,
                    "api_call": 32.0,
                    "bookmark": 9.0,
                    "email": 23.0
                },
                "limits": {
                    "max_searches": 5000,
                    "max_api_calls": 10000,
                    "max_bookmarks": 500,
                    "max_email_alerts": 100
                }
            }
        }


class UsageTrackingRequest(BaseModel):
    """사용량 추적 요청"""
    usage_type: str = Field(..., description="사용 타입")
    quantity: int = Field(1, description="사용량")
    details: Optional[Dict[str, Any]] = Field(None, description="추가 정보")

    class Config:
        schema_extra = {
            "example": {
                "usage_type": "search",
                "quantity": 1,
                "details": {
                    "query": "건설 입찰",
                    "filters": ["서울", "1억 이상"]
                }
            }
        }


# ========== 쿠폰 스키마 ==========

class CouponValidation(BaseModel):
    """쿠폰 검증 요청"""
    code: str = Field(..., description="쿠폰 코드")
    plan_type: SubscriptionPlan = Field(..., description="적용할 플랜")

    class Config:
        schema_extra = {
            "example": {
                "code": "NEWUSER20",
                "plan_type": "professional"
            }
        }


class CouponResponse(BaseModel):
    """쿠폰 응답"""
    valid: bool
    coupon_code: str
    description: Optional[str]
    discount_type: str
    discount_value: float
    base_amount: float
    discount_amount: float
    final_amount: float
    message: Optional[str]

    class Config:
        schema_extra = {
            "example": {
                "valid": True,
                "coupon_code": "NEWUSER20",
                "description": "신규 가입자 20% 할인",
                "discount_type": "percentage",
                "discount_value": 20.0,
                "base_amount": 99000,
                "discount_amount": 19800,
                "final_amount": 79200,
                "message": "쿠폰이 적용되었습니다"
            }
        }


# ========== 구독 관리 스키마 ==========

class SubscriptionCancellation(BaseModel):
    """구독 취소 요청"""
    reason: Optional[str] = Field(None, description="취소 사유")
    feedback: Optional[str] = Field(None, description="피드백")
    immediate: bool = Field(False, description="즉시 취소 여부")

    class Config:
        schema_extra = {
            "example": {
                "reason": "서비스 불필요",
                "feedback": "가격이 너무 비쌉니다",
                "immediate": False
            }
        }


class TrialStartRequest(BaseModel):
    """무료 체험 시작 요청"""
    plan_type: SubscriptionPlan = Field(
        SubscriptionPlan.PROFESSIONAL,
        description="체험할 플랜"
    )
    marketing_consent: bool = Field(False, description="마케팅 수신 동의")

    class Config:
        schema_extra = {
            "example": {
                "plan_type": "professional",
                "marketing_consent": True
            }
        }


# ========== 통계 스키마 ==========

class SubscriptionStatistics(BaseModel):
    """구독 통계"""
    total_subscriptions: int
    active_subscriptions: int
    trial_subscriptions: int
    plan_distribution: Dict[str, int]
    monthly_revenue: float
    churn_rate: Optional[float]
    average_lifetime_value: Optional[float]

    class Config:
        schema_extra = {
            "example": {
                "total_subscriptions": 1500,
                "active_subscriptions": 1200,
                "trial_subscriptions": 150,
                "plan_distribution": {
                    "free": 500,
                    "basic": 400,
                    "professional": 250,
                    "enterprise": 50
                },
                "monthly_revenue": 125000000,
                "churn_rate": 5.2,
                "average_lifetime_value": 2500000
            }
        }