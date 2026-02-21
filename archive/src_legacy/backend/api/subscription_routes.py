"""
구독 관리 API 엔드포인트
구독 플랜 조회, 변경, 결제 관리
"""

from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from decimal import Decimal

from backend.core.database import get_db
from backend.core.security import security_service
from backend.models.subscription_models import (
    Subscription, SubscriptionPlanDetail, Payment,
    UsageHistory, Coupon, CouponUse,
    SubscriptionPlan, PaymentStatus
)
from backend.models.user_models import User
from backend.services.subscription_service import SubscriptionService
from backend.schemas.subscription_schemas import (
    SubscriptionResponse, PlanDetailResponse, PaymentRequest,
    SubscriptionUpgrade, UsageResponse, CouponValidation
)

router = APIRouter(prefix="/api/subscription", tags=["구독"])


# ========== 구독 플랜 조회 ==========

@router.get("/plans", response_model=List[PlanDetailResponse])
async def get_subscription_plans(
    db: Session = Depends(get_db)
):
    """
    모든 구독 플랜 조회

    - 사용 가능한 모든 플랜 정보
    - 가격 및 기능 비교
    """
    try:
        plans = db.query(SubscriptionPlanDetail).filter(
            SubscriptionPlanDetail.is_active == True
        ).order_by(SubscriptionPlanDetail.sort_order).all()

        return [PlanDetailResponse.from_orm(plan) for plan in plans]

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"플랜 조회 실패: {str(e)}")


@router.get("/plans/{plan_type}", response_model=PlanDetailResponse)
async def get_subscription_plan_detail(
    plan_type: SubscriptionPlan,
    db: Session = Depends(get_db)
):
    """
    특정 구독 플랜 상세 조회
    """
    try:
        plan = db.query(SubscriptionPlanDetail).filter(
            SubscriptionPlanDetail.plan_type == plan_type,
            SubscriptionPlanDetail.is_active == True
        ).first()

        if not plan:
            raise HTTPException(status_code=404, detail="플랜을 찾을 수 없습니다")

        return PlanDetailResponse.from_orm(plan)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"플랜 조회 실패: {str(e)}")


# ========== 현재 구독 정보 ==========

@router.get("/current", response_model=SubscriptionResponse)
async def get_current_subscription(
    token: dict = Depends(security_service.verify_token),
    db: Session = Depends(get_db)
):
    """
    현재 사용자의 구독 정보 조회
    """
    user_id = int(token.get("sub"))

    try:
        subscription = db.query(Subscription).filter(
            Subscription.user_id == user_id
        ).first()

        if not subscription:
            # 구독이 없으면 무료 플랜 생성
            subscription = SubscriptionService.create_free_subscription(user_id, db)

        return SubscriptionResponse.from_orm(subscription)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"구독 정보 조회 실패: {str(e)}")


# ========== 구독 플랜 변경 ==========

@router.post("/upgrade")
async def upgrade_subscription(
    upgrade_data: SubscriptionUpgrade,
    background_tasks: BackgroundTasks,
    token: dict = Depends(security_service.verify_token),
    db: Session = Depends(get_db)
):
    """
    구독 플랜 업그레이드

    - 상위 플랜으로 변경
    - 즉시 적용 또는 다음 결제일 적용
    """
    user_id = int(token.get("sub"))

    try:
        service = SubscriptionService(db)

        # 현재 구독 확인
        current_subscription = db.query(Subscription).filter(
            Subscription.user_id == user_id
        ).first()

        if not current_subscription:
            raise HTTPException(status_code=404, detail="구독 정보가 없습니다")

        # 플랜 유효성 검증
        new_plan = db.query(SubscriptionPlanDetail).filter(
            SubscriptionPlanDetail.plan_type == upgrade_data.new_plan_type,
            SubscriptionPlanDetail.is_active == True
        ).first()

        if not new_plan:
            raise HTTPException(status_code=404, detail="유효하지 않은 플랜입니다")

        # 다운그레이드 방지
        if service.is_downgrade(current_subscription.plan_type, upgrade_data.new_plan_type):
            raise HTTPException(status_code=400, detail="다운그레이드는 지원하지 않습니다")

        # 업그레이드 처리
        updated_subscription = service.upgrade_plan(
            subscription_id=current_subscription.id,
            new_plan_type=upgrade_data.new_plan_type,
            apply_immediately=upgrade_data.apply_immediately
        )

        # 이메일 알림 (백그라운드)
        background_tasks.add_task(
            service.send_upgrade_confirmation,
            user_id=user_id,
            new_plan=new_plan
        )

        return {
            "message": "구독 플랜이 변경되었습니다",
            "subscription": SubscriptionResponse.from_orm(updated_subscription)
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"플랜 변경 실패: {str(e)}")


# ========== 구독 취소 ==========

@router.post("/cancel")
async def cancel_subscription(
    reason: Optional[str] = None,
    token: dict = Depends(security_service.verify_token),
    db: Session = Depends(get_db)
):
    """
    구독 취소

    - 현재 결제 기간 종료 후 취소
    - 즉시 취소 옵션 제공
    """
    user_id = int(token.get("sub"))

    try:
        subscription = db.query(Subscription).filter(
            Subscription.user_id == user_id,
            Subscription.is_active == True
        ).first()

        if not subscription:
            raise HTTPException(status_code=404, detail="활성 구독이 없습니다")

        if subscription.plan_type == SubscriptionPlan.FREE:
            raise HTTPException(status_code=400, detail="무료 플랜은 취소할 수 없습니다")

        # 취소 처리
        subscription.cancelled_at = datetime.utcnow()
        subscription.cancellation_reason = reason

        # 다음 결제일에 비활성화 예정
        if subscription.expires_at:
            subscription.is_active = False  # 만료일에 자동 비활성화
        else:
            subscription.expires_at = subscription.next_billing_date or datetime.utcnow()

        db.commit()

        return {
            "message": "구독이 취소되었습니다",
            "expires_at": subscription.expires_at,
            "refund_available": False  # 환불 정책에 따라 결정
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"구독 취소 실패: {str(e)}")


# ========== 사용량 조회 ==========

@router.get("/usage", response_model=UsageResponse)
async def get_usage_statistics(
    period: str = Query("current", description="조회 기간 (current, last_month)"),
    token: dict = Depends(security_service.verify_token),
    db: Session = Depends(get_db)
):
    """
    사용량 통계 조회

    - 현재 월 사용량
    - 사용 제한 대비 사용률
    """
    user_id = int(token.get("sub"))

    try:
        subscription = db.query(Subscription).filter(
            Subscription.user_id == user_id
        ).first()

        if not subscription:
            raise HTTPException(status_code=404, detail="구독 정보가 없습니다")

        # 기간 설정
        if period == "current":
            start_date = subscription.usage_reset_date or datetime.now().replace(day=1)
            end_date = datetime.now()
        else:  # last_month
            end_date = datetime.now().replace(day=1) - timedelta(days=1)
            start_date = end_date.replace(day=1)

        # 사용량 집계
        usage_data = db.query(
            UsageHistory.usage_type,
            func.sum(UsageHistory.quantity).label('total')
        ).filter(
            UsageHistory.subscription_id == subscription.id,
            UsageHistory.used_at >= start_date,
            UsageHistory.used_at <= end_date
        ).group_by(UsageHistory.usage_type).all()

        # 사용량 정리
        usage_summary = {
            "search": 0,
            "api_call": 0,
            "bookmark": 0,
            "email": 0
        }

        for usage in usage_data:
            if usage.usage_type in usage_summary:
                usage_summary[usage.usage_type] = usage.total or 0

        # 사용률 계산
        usage_percentage = {
            "search": (usage_summary["search"] / subscription.max_searches_per_month * 100)
                     if subscription.max_searches_per_month > 0 else 0,
            "api_call": (usage_summary["api_call"] / subscription.max_api_calls * 100)
                       if subscription.max_api_calls > 0 else 0,
            "bookmark": (usage_summary["bookmark"] / subscription.max_bookmarks * 100)
                       if subscription.max_bookmarks > 0 else 0,
            "email": (usage_summary["email"] / subscription.max_email_alerts * 100)
                    if subscription.max_email_alerts > 0 else 0
        }

        return UsageResponse(
            period=period,
            start_date=start_date,
            end_date=end_date,
            usage_summary=usage_summary,
            usage_percentage=usage_percentage,
            limits={
                "max_searches": subscription.max_searches_per_month,
                "max_api_calls": subscription.max_api_calls,
                "max_bookmarks": subscription.max_bookmarks,
                "max_email_alerts": subscription.max_email_alerts
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"사용량 조회 실패: {str(e)}")


# ========== 결제 이력 ==========

@router.get("/payments", response_model=List[Dict[str, Any]])
async def get_payment_history(
    limit: int = Query(10, ge=1, le=50),
    offset: int = Query(0, ge=0),
    token: dict = Depends(security_service.verify_token),
    db: Session = Depends(get_db)
):
    """
    결제 이력 조회
    """
    user_id = int(token.get("sub"))

    try:
        payments = db.query(Payment).filter(
            Payment.user_id == user_id
        ).order_by(Payment.created_at.desc()).limit(limit).offset(offset).all()

        return [
            {
                "id": payment.id,
                "amount": float(payment.amount),
                "currency": payment.currency,
                "status": payment.status.value,
                "payment_method": payment.payment_method,
                "billing_period": f"{payment.billing_period_start.date()} ~ {payment.billing_period_end.date()}",
                "processed_at": payment.processed_at,
                "receipt_url": payment.receipt_url
            }
            for payment in payments
        ]

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"결제 이력 조회 실패: {str(e)}")


# ========== 쿠폰 적용 ==========

@router.post("/apply-coupon")
async def apply_coupon(
    coupon_data: CouponValidation,
    token: dict = Depends(security_service.verify_token),
    db: Session = Depends(get_db)
):
    """
    쿠폰 적용

    - 쿠폰 코드 유효성 검증
    - 할인 금액 계산
    """
    user_id = int(token.get("sub"))

    try:
        # 쿠폰 조회
        coupon = db.query(Coupon).filter(
            Coupon.code == coupon_data.code,
            Coupon.is_active == True
        ).first()

        if not coupon:
            raise HTTPException(status_code=404, detail="유효하지 않은 쿠폰입니다")

        # 유효 기간 확인
        now = datetime.utcnow()
        if now < coupon.valid_from or now > coupon.valid_until:
            raise HTTPException(status_code=400, detail="쿠폰 유효 기간이 아닙니다")

        # 사용 횟수 확인
        if coupon.max_uses and coupon.current_uses >= coupon.max_uses:
            raise HTTPException(status_code=400, detail="쿠폰 사용 한도를 초과했습니다")

        # 사용자별 사용 횟수 확인
        user_uses = db.query(CouponUse).filter(
            CouponUse.coupon_id == coupon.id,
            CouponUse.user_id == user_id
        ).count()

        if user_uses >= coupon.max_uses_per_user:
            raise HTTPException(status_code=400, detail="이미 사용한 쿠폰입니다")

        # 플랜 적용 가능 여부 확인
        if coupon.applicable_plans:
            if coupon_data.plan_type not in coupon.applicable_plans:
                raise HTTPException(status_code=400, detail="해당 플랜에 적용할 수 없는 쿠폰입니다")

        # 할인 금액 계산
        plan = db.query(SubscriptionPlanDetail).filter(
            SubscriptionPlanDetail.plan_type == coupon_data.plan_type
        ).first()

        if not plan:
            raise HTTPException(status_code=404, detail="플랜을 찾을 수 없습니다")

        base_amount = float(plan.monthly_price)

        if coupon.discount_type == "percentage":
            discount_amount = base_amount * (float(coupon.discount_value) / 100)
        else:  # fixed
            discount_amount = float(coupon.discount_value)

        final_amount = max(0, base_amount - discount_amount)

        return {
            "valid": True,
            "coupon_code": coupon.code,
            "description": coupon.description,
            "base_amount": base_amount,
            "discount_amount": discount_amount,
            "final_amount": final_amount,
            "discount_type": coupon.discount_type,
            "discount_value": float(coupon.discount_value)
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"쿠폰 적용 실패: {str(e)}")


# ========== 무료 체험 시작 ==========

@router.post("/start-trial")
async def start_free_trial(
    plan_type: SubscriptionPlan = SubscriptionPlan.PROFESSIONAL,
    token: dict = Depends(security_service.verify_token),
    db: Session = Depends(get_db)
):
    """
    무료 체험 시작

    - 7일 무료 체험
    - 프로페셔널 플랜 기능 제공
    """
    user_id = int(token.get("sub"))

    try:
        # 기존 구독 확인
        existing = db.query(Subscription).filter(
            Subscription.user_id == user_id
        ).first()

        if existing and existing.is_trial:
            raise HTTPException(status_code=400, detail="이미 무료 체험 중입니다")

        if existing and existing.trial_ends_at:
            raise HTTPException(status_code=400, detail="무료 체험은 한 번만 가능합니다")

        # 무료 체험 시작
        service = SubscriptionService(db)
        trial_subscription = service.start_trial(
            user_id=user_id,
            plan_type=plan_type,
            trial_days=7
        )

        return {
            "message": "7일 무료 체험이 시작되었습니다",
            "trial_ends_at": trial_subscription.trial_ends_at,
            "plan_features": trial_subscription.features
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"무료 체험 시작 실패: {str(e)}")