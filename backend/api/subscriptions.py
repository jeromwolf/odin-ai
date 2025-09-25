"""
구독 관리 API
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from database import get_db_connection
from auth.dependencies import get_current_user, get_current_user_optional, User
from pydantic import BaseModel, EmailStr
import logging
import json

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/subscriptions", tags=["subscriptions"])

# Pydantic 모델
class SubscriptionPlan(BaseModel):
    name: str
    display_name: str
    description: Optional[str]
    price_monthly: int
    price_yearly: Optional[int]
    features: Dict[str, Any]

class SubscriptionCreate(BaseModel):
    plan_id: int
    billing_cycle: str = "monthly"
    promo_code: Optional[str] = None

class PaymentMethod(BaseModel):
    type: str  # card, bank_account
    card_last4: Optional[str]
    card_brand: Optional[str]
    bank_name: Optional[str]
    account_last4: Optional[str]

class BillingAddress(BaseModel):
    company_name: Optional[str]
    tax_id: Optional[str]
    address_line1: str
    address_line2: Optional[str]
    city: str
    state: Optional[str]
    postal_code: str
    country: str = "KR"
    phone: Optional[str]
    email: Optional[EmailStr]


@router.get("/plans")
async def get_subscription_plans(
    user: Optional[User] = Depends(get_current_user_optional)
):
    """모든 구독 플랜 조회"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            # 구독 플랜 조회
            cursor.execute("""
                SELECT
                    p.id,
                    p.name,
                    p.display_name,
                    p.description,
                    p.price_monthly,
                    p.price_yearly,
                    p.max_searches_per_day,
                    p.max_downloads_per_month,
                    p.max_bookmarks,
                    p.max_alerts,
                    p.api_rate_limit,
                    p.has_ai_recommendations,
                    p.has_advanced_search,
                    p.has_export_excel,
                    p.has_api_access,
                    p.has_priority_support,
                    p.has_custom_alerts,
                    p.has_team_collaboration,
                    p.badge_color,
                    p.badge_text,
                    p.sort_order
                FROM subscription_plans p
                WHERE p.is_active = true
                ORDER BY p.sort_order
            """)

            plans = []
            for row in cursor.fetchall():
                plan = {
                    "id": row[0],
                    "name": row[1],
                    "display_name": row[2],
                    "description": row[3],
                    "price_monthly": row[4],
                    "price_yearly": row[5],
                    "limits": {
                        "searches_per_day": row[6],
                        "downloads_per_month": row[7],
                        "bookmarks": row[8],
                        "alerts": row[9],
                        "api_rate_limit": row[10]
                    },
                    "features": {
                        "ai_recommendations": row[11],
                        "advanced_search": row[12],
                        "export_excel": row[13],
                        "api_access": row[14],
                        "priority_support": row[15],
                        "custom_alerts": row[16],
                        "team_collaboration": row[17]
                    },
                    "badge": {
                        "color": row[18],
                        "text": row[19]
                    } if row[18] or row[19] else None
                }

                # 각 플랜의 특징 리스트 조회
                cursor.execute("""
                    SELECT
                        feature_name,
                        feature_value,
                        feature_group
                    FROM subscription_features
                    WHERE plan_id = %s
                    ORDER BY sort_order
                """, (row[0],))

                features = []
                for f_row in cursor.fetchall():
                    features.append({
                        "name": f_row[0],
                        "value": f_row[1],
                        "group": f_row[2]
                    })

                plan["feature_list"] = features
                plans.append(plan)

            # 현재 사용자의 구독 정보
            current_subscription = None
            if user:
                cursor.execute("""
                    SELECT
                        s.id,
                        s.plan_id,
                        p.name,
                        p.display_name,
                        s.status,
                        s.billing_cycle,
                        s.expires_at,
                        s.auto_renew,
                        s.is_trial,
                        s.trial_ends_at
                    FROM user_subscriptions s
                    JOIN subscription_plans p ON s.plan_id = p.id
                    WHERE s.user_id = %s
                        AND s.status IN ('active', 'trial')
                    LIMIT 1
                """, (user.id,))

                sub_row = cursor.fetchone()
                if sub_row:
                    current_subscription = {
                        "id": sub_row[0],
                        "plan_id": sub_row[1],
                        "plan_name": sub_row[2],
                        "plan_display_name": sub_row[3],
                        "status": sub_row[4],
                        "billing_cycle": sub_row[5],
                        "expires_at": sub_row[6].isoformat() if sub_row[6] else None,
                        "auto_renew": sub_row[7],
                        "is_trial": sub_row[8],
                        "trial_ends_at": sub_row[9].isoformat() if sub_row[9] else None
                    }

            return {
                "plans": plans,
                "current_subscription": current_subscription
            }

    except Exception as e:
        logger.error(f"플랜 조회 실패: {e}")
        raise HTTPException(status_code=500, detail="플랜 조회 실패")


@router.get("/my-subscription")
async def get_my_subscription(user: User = Depends(get_current_user)):
    """내 구독 정보 조회"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            # 구독 정보 조회
            cursor.execute("""
                SELECT
                    s.*,
                    p.name as plan_name,
                    p.display_name as plan_display_name,
                    p.price_monthly,
                    p.price_yearly
                FROM user_subscriptions s
                JOIN subscription_plans p ON s.plan_id = p.id
                WHERE s.user_id = %s
                    AND s.status IN ('active', 'trial', 'cancelled')
                ORDER BY s.created_at DESC
                LIMIT 1
            """, (user.id,))

            row = cursor.fetchone()
            if not row:
                return {
                    "subscription": None,
                    "plan": "free",
                    "message": "무료 플랜 사용 중"
                }

            # 사용량 조회
            cursor.execute("""
                SELECT
                    searches_count,
                    downloads_count,
                    api_calls_count
                FROM subscription_usage
                WHERE user_id = %s AND date = CURRENT_DATE
            """, (user.id,))

            usage_row = cursor.fetchone()
            usage = {
                "searches_today": usage_row[0] if usage_row else 0,
                "downloads_today": usage_row[1] if usage_row else 0,
                "api_calls_today": usage_row[2] if usage_row else 0
            }

            # 월간 다운로드
            cursor.execute("""
                SELECT COALESCE(SUM(downloads_count), 0)
                FROM subscription_usage
                WHERE user_id = %s
                    AND date >= DATE_TRUNC('month', CURRENT_DATE)
            """, (user.id,))

            usage["downloads_this_month"] = cursor.fetchone()[0]

            # 북마크 수
            cursor.execute("""
                SELECT COUNT(*)
                FROM user_bookmarks
                WHERE user_id = %s
            """, (user.id,))

            usage["bookmarks_count"] = cursor.fetchone()[0]

            return {
                "subscription": {
                    "id": row[0],
                    "plan_name": row[17],
                    "plan_display_name": row[18],
                    "status": row[3],
                    "billing_cycle": row[4],
                    "started_at": row[5].isoformat() if row[5] else None,
                    "expires_at": row[6].isoformat() if row[6] else None,
                    "auto_renew": row[10],
                    "is_trial": row[11],
                    "trial_ends_at": row[12].isoformat() if row[12] else None,
                    "price": row[19] if row[4] == "monthly" else row[20]
                },
                "usage": usage
            }

    except Exception as e:
        logger.error(f"구독 정보 조회 실패: {e}")
        raise HTTPException(status_code=500, detail="구독 정보 조회 실패")


@router.post("/subscribe")
async def create_subscription(
    subscription: SubscriptionCreate,
    user: User = Depends(get_current_user)
):
    """구독 생성/변경 (실제 결제는 별도 처리)"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            # 플랜 정보 확인
            cursor.execute("""
                SELECT id, name, price_monthly, price_yearly
                FROM subscription_plans
                WHERE id = %s AND is_active = true
            """, (subscription.plan_id,))

            plan = cursor.fetchone()
            if not plan:
                raise HTTPException(status_code=404, detail="플랜을 찾을 수 없습니다")

            # 기존 구독 확인
            cursor.execute("""
                SELECT id, status
                FROM user_subscriptions
                WHERE user_id = %s
                ORDER BY created_at DESC
                LIMIT 1
            """, (user.id,))

            existing = cursor.fetchone()

            # 가격 계산
            if subscription.billing_cycle == "yearly":
                price = plan[3] or plan[2] * 12
                expires_at = datetime.now() + timedelta(days=365)
            else:
                price = plan[2]
                expires_at = datetime.now() + timedelta(days=30)

            # 프로모 코드 적용 (간단한 예시)
            discount = 0
            if subscription.promo_code:
                if subscription.promo_code == "WELCOME20":
                    discount = 20
                elif subscription.promo_code == "STUDENT50":
                    discount = 50

            final_price = price * (100 - discount) // 100

            # 무료 플랜인 경우 즉시 활성화
            if plan[1] == "free":
                status = "active"
            else:
                # 실제로는 결제 처리 후 활성화
                status = "pending"

            if existing:
                # 기존 구독 취소
                cursor.execute("""
                    UPDATE user_subscriptions
                    SET status = 'cancelled', cancelled_at = NOW()
                    WHERE id = %s
                """, (existing[0],))

            # 새 구독 생성
            cursor.execute("""
                INSERT INTO user_subscriptions (
                    user_id, plan_id, status, billing_cycle,
                    expires_at, promo_code, discount_percentage
                ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (
                user.id, subscription.plan_id, status,
                subscription.billing_cycle, expires_at,
                subscription.promo_code, discount
            ))

            new_sub_id = cursor.fetchone()[0]
            conn.commit()

            return {
                "subscription_id": new_sub_id,
                "status": status,
                "plan": plan[1],
                "price": final_price,
                "discount": discount,
                "expires_at": expires_at.isoformat(),
                "message": "구독이 생성되었습니다" if status == "active" else "결제 대기 중입니다"
            }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"구독 생성 실패: {e}")
        raise HTTPException(status_code=500, detail="구독 생성 실패")


@router.post("/cancel")
async def cancel_subscription(user: User = Depends(get_current_user)):
    """구독 취소"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            # 활성 구독 확인
            cursor.execute("""
                UPDATE user_subscriptions
                SET
                    status = 'cancelled',
                    cancelled_at = NOW(),
                    auto_renew = false
                WHERE user_id = %s
                    AND status = 'active'
                RETURNING id, expires_at
            """, (user.id,))

            result = cursor.fetchone()
            if not result:
                raise HTTPException(status_code=404, detail="활성 구독이 없습니다")

            conn.commit()

            return {
                "subscription_id": result[0],
                "expires_at": result[1].isoformat() if result[1] else None,
                "message": "구독이 취소되었습니다. 만료일까지 사용 가능합니다."
            }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"구독 취소 실패: {e}")
        raise HTTPException(status_code=500, detail="구독 취소 실패")


@router.get("/usage")
async def get_usage_stats(user: User = Depends(get_current_user)):
    """사용량 통계 조회"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            # 오늘 사용량
            cursor.execute("""
                SELECT * FROM check_subscription_limit(%s, 'search')
            """, (user.id,))
            result = cursor.fetchone()[0]
            search_limit = result if isinstance(result, dict) else json.loads(result)

            cursor.execute("""
                SELECT * FROM check_subscription_limit(%s, 'download')
            """, (user.id,))
            result = cursor.fetchone()[0]
            download_limit = result if isinstance(result, dict) else json.loads(result)

            cursor.execute("""
                SELECT * FROM check_subscription_limit(%s, 'bookmark')
            """, (user.id,))
            result = cursor.fetchone()[0]
            bookmark_limit = result if isinstance(result, dict) else json.loads(result)

            # 일별 사용량 추이 (최근 30일)
            cursor.execute("""
                SELECT
                    date,
                    searches_count,
                    downloads_count,
                    api_calls_count
                FROM subscription_usage
                WHERE user_id = %s
                    AND date >= CURRENT_DATE - INTERVAL '30 days'
                ORDER BY date DESC
            """, (user.id,))

            daily_usage = []
            for row in cursor.fetchall():
                daily_usage.append({
                    "date": row[0].isoformat(),
                    "searches": row[1],
                    "downloads": row[2],
                    "api_calls": row[3]
                })

            return {
                "limits": {
                    "search": search_limit,
                    "download": download_limit,
                    "bookmark": bookmark_limit
                },
                "daily_usage": daily_usage,
                "plan": search_limit.get("plan_name", "free")
            }

    except Exception as e:
        logger.error(f"사용량 조회 실패: {e}")
        raise HTTPException(status_code=500, detail="사용량 조회 실패")


@router.post("/check-limit")
async def check_limit(
    limit_type: str = Query(..., regex="^(search|download|bookmark|api)$"),
    user: User = Depends(get_current_user)
):
    """특정 기능의 사용 제한 체크"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                SELECT * FROM check_subscription_limit(%s, %s)
            """, (user.id, limit_type))

            raw_result = cursor.fetchone()[0]
            result = raw_result if isinstance(raw_result, dict) else json.loads(raw_result)

            if not result.get("allowed"):
                return {
                    "allowed": False,
                    "message": f"{limit_type} 한도를 초과했습니다",
                    "current": result.get("current_count"),
                    "limit": result.get("limit"),
                    "plan": result.get("plan_name"),
                    "upgrade_url": "/pricing"
                }

            return {
                "allowed": True,
                "current": result.get("current_count"),
                "limit": result.get("limit"),
                "remaining": (result.get("limit") or 999999) - result.get("current_count", 0)
            }

    except Exception as e:
        logger.error(f"제한 체크 실패: {e}")
        raise HTTPException(status_code=500, detail="제한 체크 실패")


@router.get("/invoices")
async def get_invoices(
    user: User = Depends(get_current_user),
    limit: int = Query(10, ge=1, le=100)
):
    """청구서 목록 조회"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                SELECT
                    i.id,
                    i.invoice_number,
                    i.total_amount,
                    i.status,
                    i.billing_period_start,
                    i.billing_period_end,
                    i.issued_at,
                    i.paid_at,
                    p.name as plan_name
                FROM invoices i
                LEFT JOIN user_subscriptions s ON i.subscription_id = s.id
                LEFT JOIN subscription_plans p ON s.plan_id = p.id
                WHERE i.user_id = %s
                ORDER BY i.issued_at DESC
                LIMIT %s
            """, (user.id, limit))

            invoices = []
            for row in cursor.fetchall():
                invoices.append({
                    "id": row[0],
                    "invoice_number": row[1],
                    "amount": row[2],
                    "status": row[3],
                    "period_start": row[4].isoformat() if row[4] else None,
                    "period_end": row[5].isoformat() if row[5] else None,
                    "issued_at": row[6].isoformat() if row[6] else None,
                    "paid_at": row[7].isoformat() if row[7] else None,
                    "plan": row[8]
                })

            return {
                "invoices": invoices,
                "total": len(invoices)
            }

    except Exception as e:
        logger.error(f"청구서 조회 실패: {e}")
        raise HTTPException(status_code=500, detail="청구서 조회 실패")