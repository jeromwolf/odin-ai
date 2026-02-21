"""
구독/결제 시스템 API
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta, timezone
from pydantic import BaseModel
from auth.dependencies import get_current_user, User
from database import get_db_connection
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/subscription", tags=["subscription"])


class SubscriptionPlan(BaseModel):
    """구독 플랜 모델"""
    plan_id: str
    name: str
    price: int
    features: List[str]
    max_bookmarks: int
    max_alerts: int
    api_calls_per_month: int
    priority_support: bool


class SubscriptionCreate(BaseModel):
    """구독 신청 모델"""
    plan_id: str
    payment_method: Optional[str] = "card"


class CheckoutRequest(BaseModel):
    """결제 요청 모델"""
    plan_id: str
    payment_method: str
    billing_info: Optional[Dict[str, Any]] = {}


# 미리 정의된 플랜들
SUBSCRIPTION_PLANS = [
    {
        "plan_id": "free",
        "name": "Free",
        "price": 0,
        "features": [
            "기본 검색",
            "북마크 10개",
            "알림 3개",
            "월 100회 API 호출"
        ],
        "max_bookmarks": 10,
        "max_alerts": 3,
        "api_calls_per_month": 100,
        "priority_support": False
    },
    {
        "plan_id": "basic",
        "name": "Basic",
        "price": 9900,
        "features": [
            "고급 검색",
            "북마크 50개",
            "알림 10개",
            "월 1000회 API 호출",
            "이메일 알림"
        ],
        "max_bookmarks": 50,
        "max_alerts": 10,
        "api_calls_per_month": 1000,
        "priority_support": False
    },
    {
        "plan_id": "pro",
        "name": "Professional",
        "price": 29900,
        "features": [
            "고급 검색",
            "무제한 북마크",
            "알림 50개",
            "월 10000회 API 호출",
            "이메일/SMS 알림",
            "AI 추천",
            "우선 지원"
        ],
        "max_bookmarks": -1,  # 무제한
        "max_alerts": 50,
        "api_calls_per_month": 10000,
        "priority_support": True
    },
    {
        "plan_id": "enterprise",
        "name": "Enterprise",
        "price": 99900,
        "features": [
            "모든 Pro 기능",
            "무제한 북마크",
            "무제한 알림",
            "무제한 API 호출",
            "전용 지원",
            "커스텀 통합",
            "SLA 보장"
        ],
        "max_bookmarks": -1,
        "max_alerts": -1,
        "api_calls_per_month": -1,
        "priority_support": True
    }
]


@router.get("/plans")
async def get_subscription_plans():
    """구독 플랜 목록 조회"""
    return {
        "success": True,
        "plans": SUBSCRIPTION_PLANS
    }


@router.get("/plans/{plan_id}")
async def get_plan_details(plan_id: str):
    """특정 플랜 상세 조회"""
    plan = next((p for p in SUBSCRIPTION_PLANS if p["plan_id"] == plan_id), None)
    if not plan:
        raise HTTPException(status_code=404, detail="플랜을 찾을 수 없습니다")

    return {
        "success": True,
        "plan": plan
    }


@router.post("/subscribe")
async def create_subscription(
    subscription: SubscriptionCreate,
    user: User = Depends(get_current_user)
):
    """구독 신청"""
    # 플랜 확인
    plan = next((p for p in SUBSCRIPTION_PLANS if p["plan_id"] == subscription.plan_id), None)
    if not plan:
        raise HTTPException(status_code=404, detail="플랜을 찾을 수 없습니다")

    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            # 기존 구독 확인
            cursor.execute("""
                SELECT id, plan_id, status FROM user_subscriptions
                WHERE user_id = %s AND status = 'active'
            """, (user.id,))

            existing = cursor.fetchone()
            if existing:
                if existing[1] == subscription.plan_id:
                    return {
                        "success": False,
                        "message": "이미 동일한 플랜을 구독 중입니다"
                    }
                else:
                    # 기존 구독 취소
                    cursor.execute("""
                        UPDATE user_subscriptions
                        SET status = 'cancelled', cancelled_at = NOW()
                        WHERE id = %s
                    """, (existing[0],))

            # 새 구독 생성
            cursor.execute("""
                INSERT INTO user_subscriptions (
                    user_id, plan_id, status, payment_method,
                    started_at, next_billing_date
                ) VALUES (
                    %s, %s, 'active', %s,
                    NOW(), NOW() + INTERVAL '30 days'
                ) RETURNING id
            """, (user.id, subscription.plan_id, subscription.payment_method))

            subscription_id = cursor.fetchone()[0]
            conn.commit()

            return {
                "success": True,
                "message": "구독이 성공적으로 신청되었습니다",
                "subscription_id": subscription_id,
                "plan": plan
            }

    except Exception as e:
        logger.error(f"구독 신청 실패: {e}")
        raise HTTPException(status_code=500, detail="구독 신청 중 오류가 발생했습니다")


@router.get("/current")
async def get_current_subscription(user: User = Depends(get_current_user)):
    """현재 구독 상태 조회"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                SELECT plan_id, status, started_at, next_billing_date
                FROM user_subscriptions
                WHERE user_id = %s AND status = 'active'
                ORDER BY started_at DESC
                LIMIT 1
            """, (user.id,))

            result = cursor.fetchone()
            if result:
                plan = next((p for p in SUBSCRIPTION_PLANS if p["plan_id"] == result[0]), None)
                return {
                    "success": True,
                    "has_subscription": True,
                    "subscription": {
                        "plan_id": result[0],
                        "plan": plan,
                        "status": result[1],
                        "started_at": result[2].isoformat() if result[2] else None,
                        "next_billing_date": result[3].isoformat() if result[3] else None
                    }
                }

    except Exception as e:
        logger.error(f"구독 조회 실패: {e}")
        raise HTTPException(status_code=500, detail="구독 조회 중 오류가 발생했습니다")

    # 구독이 없으면 Free 플랜
    free_plan = SUBSCRIPTION_PLANS[0]
    return {
        "success": True,
        "has_subscription": False,
        "subscription": {
            "plan_id": "free",
            "plan": free_plan,
            "status": "active"
        }
    }


@router.post("/checkout")
async def checkout(
    request: CheckoutRequest,
    user: User = Depends(get_current_user)
):
    """결제 처리"""
    # 플랜 확인
    plan = next((p for p in SUBSCRIPTION_PLANS if p["plan_id"] == request.plan_id), None)
    if not plan:
        raise HTTPException(status_code=404, detail="플랜을 찾을 수 없습니다")

    # 실제 결제 처리는 Stripe 등 결제 서비스 연동 필요
    # 여기서는 시뮬레이션

    if plan["price"] == 0:
        # 무료 플랜은 바로 활성화
        return await create_subscription(
            SubscriptionCreate(plan_id=request.plan_id, payment_method="free"),
            user
        )

    # 유료 플랜 결제 시뮬레이션
    payment_id = f"pay_sim_{user.id}_{request.plan_id}_{datetime.now(timezone.utc).timestamp()}"

    return {
        "success": True,
        "message": "결제가 성공적으로 처리되었습니다",
        "payment_id": payment_id,
        "plan": plan,
        "amount": plan["price"],
        "currency": "KRW",
        "status": "completed"
    }


@router.post("/cancel")
async def cancel_subscription(user: User = Depends(get_current_user)):
    """구독 취소"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                UPDATE user_subscriptions
                SET status = 'cancelled', cancelled_at = NOW()
                WHERE user_id = %s AND status = 'active'
                RETURNING id
            """, (user.id,))

            result = cursor.fetchone()
            conn.commit()

            if result:
                return {
                    "success": True,
                    "message": "구독이 취소되었습니다"
                }
            else:
                raise HTTPException(status_code=404, detail="활성 구독이 없습니다")

    except Exception as e:
        logger.error(f"구독 취소 실패: {e}")
        raise HTTPException(status_code=500, detail="구독 취소 중 오류가 발생했습니다")


@router.get("/usage")
async def get_usage_stats(user: User = Depends(get_current_user)):
    """사용량 통계 조회"""
    # 현재 구독 플랜 확인
    subscription = await get_current_subscription(user)
    plan = subscription["subscription"]["plan"]

    # 실제 사용량을 DB에서 조회
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT COUNT(*) FROM user_bookmarks WHERE user_id = %s",
                (user.id,)
            )
            bookmarks_used = cursor.fetchone()[0]

            cursor.execute(
                "SELECT COUNT(*) FROM alert_rules WHERE user_id = %s AND is_active = true",
                (user.id,)
            )
            alerts_used = cursor.fetchone()[0]

    # TODO: API 호출 추적 테이블이 없으므로 0으로 설정
    api_calls_used = 0

    usage = {
        "bookmarks": {
            "used": bookmarks_used,
            "limit": plan["max_bookmarks"] if plan["max_bookmarks"] > 0 else "무제한"
        },
        "alerts": {
            "used": alerts_used,
            "limit": plan["max_alerts"] if plan["max_alerts"] > 0 else "무제한"
        },
        "api_calls": {
            "used": api_calls_used,
            "limit": plan["api_calls_per_month"] if plan["api_calls_per_month"] > 0 else "무제한"
        }
    }

    return {
        "success": True,
        "plan_id": plan["plan_id"],
        "usage": usage
    }