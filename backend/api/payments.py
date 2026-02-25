"""
결제 처리 API (토스페이먼츠)
"""

from fastapi import APIRouter, HTTPException, Depends, Request, Query
from typing import Optional, Dict, Any
from datetime import datetime
from database import get_db_connection
from auth.dependencies import get_current_user, User
from pydantic import BaseModel
from psycopg2.extras import RealDictCursor
import logging
import requests
import base64
import json
import os
import hashlib
import secrets

logger = logging.getLogger(__name__)

FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")

router = APIRouter(prefix="/api/payments", tags=["payments"])

# 토스페이먼츠 설정 (실제 사용시 환경변수로 관리)
TOSS_CLIENT_KEY = os.getenv("TOSS_CLIENT_KEY", "")
TOSS_SECRET_KEY = os.getenv("TOSS_SECRET_KEY", "")
TOSS_API_URL = "https://api.tosspayments.com/v1"
USE_TEST_MODE = os.getenv("PAYMENT_TEST_MODE", "true").lower() == "true"
TOSS_WEBHOOK_SECRET = os.getenv("TOSS_WEBHOOK_SECRET", "")

# Authorization 헤더 생성
def get_auth_header():
    auth_string = f"{TOSS_SECRET_KEY}:"
    encoded = base64.b64encode(auth_string.encode()).decode()
    return {"Authorization": f"Basic {encoded}"}

def verify_webhook_signature(signature: str, body: bytes) -> bool:
    """토스페이먼츠 웹훅 서명 검증"""
    if not TOSS_WEBHOOK_SECRET:
        logger.warning("TOSS_WEBHOOK_SECRET not configured, skipping signature verification")
        return True
    import hmac
    expected = hmac.HMAC(
        TOSS_WEBHOOK_SECRET.encode(),
        body,
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, signature or "")

# Pydantic 모델
class PaymentRequest(BaseModel):
    subscription_id: int
    payment_method: str = "card"  # card, transfer, etc
    return_url: Optional[str] = None

class PaymentConfirm(BaseModel):
    payment_key: str
    order_id: str
    amount: int

class BillingKeyRequest(BaseModel):
    card_number: str
    card_expiry_year: str
    card_expiry_month: str
    card_password: str  # 앞 2자리
    birth_or_business: str  # 생년월일 6자리 또는 사업자번호
    customer_name: str

class PaymentWebhook(BaseModel):
    event_type: str
    payment_key: str
    order_id: str
    status: str
    data: Dict[str, Any]


@router.post("/request")
async def request_payment(
    payment: PaymentRequest,
    user: User = Depends(get_current_user)
):
    """결제 요청 생성"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)

            # 구독 정보 조회
            cursor.execute("""
                SELECT
                    s.id,
                    s.plan_id,
                    s.billing_cycle,
                    p.name,
                    p.display_name,
                    p.price_monthly,
                    p.price_yearly,
                    s.discount_percentage
                FROM user_subscriptions s
                JOIN subscription_plans p ON s.plan_id = p.id
                WHERE s.id = %s AND s.user_id = %s
            """, (payment.subscription_id, user.id))

            sub_data = cursor.fetchone()
            if not sub_data:
                raise HTTPException(status_code=404, detail="구독 정보를 찾을 수 없습니다")

            # 가격 계산
            if sub_data["billing_cycle"] == "yearly":
                amount = sub_data["price_yearly"] or sub_data["price_monthly"] * 12
            else:
                amount = sub_data["price_monthly"]

            # 할인 적용
            if sub_data["discount_percentage"]:
                amount = amount * (100 - sub_data["discount_percentage"]) // 100

            # 주문 ID 생성
            order_id = f"SUB_{user.id}_{sub_data['id']}_{secrets.token_hex(8)}"

            # 결제 내역 생성
            cursor.execute("""
                INSERT INTO payment_history (
                    user_id, subscription_id, amount, currency,
                    payment_method, status, description
                ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (
                user.id, payment.subscription_id, amount, "KRW",
                payment.payment_method, "pending",
                f"{sub_data['display_name']} - {sub_data['billing_cycle']} 구독"
            ))

            payment_id = cursor.fetchone()["id"]

            # 토스페이먼츠 결제 요청 데이터
            payment_data = {
                "amount": amount,
                "orderId": order_id,
                "orderName": f"ODIN-AI {sub_data['display_name']} 구독",
                "customerName": user.username,
                "customerEmail": user.email,
                "successUrl": payment.return_url or f"{FRONTEND_URL}/payment/success",
                "failUrl": f"{FRONTEND_URL}/payment/fail",
            }

            if USE_TEST_MODE:
                # 테스트 모드에서는 실제 API 호출 없이 성공 응답
                payment_url = f"https://payment.tosspayments.com/test/{order_id}"
                payment_key = f"test_pk_{secrets.token_hex(16)}"
            else:
                # 실제 토스페이먼츠 API 호출
                response = requests.post(
                    f"{TOSS_API_URL}/payments",
                    json=payment_data,
                    headers={
                        **get_auth_header(),
                        "Content-Type": "application/json"
                    }
                )

                if response.status_code != 200:
                    raise HTTPException(
                        status_code=response.status_code,
                        detail="결제 요청 실패"
                    )

                result = response.json()
                payment_url = result.get("checkout", {}).get("url")
                payment_key = result.get("paymentKey")

            # 결제 정보 업데이트
            cursor.execute("""
                UPDATE payment_history
                SET transaction_id = %s
                WHERE id = %s
            """, (order_id, payment_id))
            conn.commit()

            return {
                "payment_id": payment_id,
                "order_id": order_id,
                "amount": amount,
                "payment_url": payment_url,
                "payment_key": payment_key,
                "test_mode": USE_TEST_MODE
            }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"결제 요청 실패: {e}")
        raise HTTPException(status_code=500, detail="결제 요청 처리 실패")


@router.post("/confirm")
async def confirm_payment(
    confirm: PaymentConfirm,
    user: User = Depends(get_current_user)
):
    """결제 승인"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)

            # 결제 내역 확인
            cursor.execute("""
                SELECT id, amount, subscription_id
                FROM payment_history
                WHERE transaction_id = %s AND user_id = %s AND status = 'pending'
            """, (confirm.order_id, user.id))

            payment = cursor.fetchone()
            if not payment:
                raise HTTPException(status_code=404, detail="결제 정보를 찾을 수 없습니다")

            if payment["amount"] != confirm.amount:
                raise HTTPException(status_code=400, detail="결제 금액이 일치하지 않습니다")

            if USE_TEST_MODE:
                # 테스트 모드에서는 즉시 승인
                approval_status = "completed"
            else:
                # 실제 토스페이먼츠 승인 API 호출
                response = requests.post(
                    f"{TOSS_API_URL}/payments/{confirm.payment_key}",
                    json={
                        "orderId": confirm.order_id,
                        "amount": confirm.amount
                    },
                    headers={
                        **get_auth_header(),
                        "Content-Type": "application/json"
                    }
                )

                if response.status_code != 200:
                    cursor.execute("""
                        UPDATE payment_history
                        SET status = 'failed', failed_at = NOW()
                        WHERE id = %s
                    """, (payment["id"],))
                    raise HTTPException(status_code=400, detail="결제 승인 실패")

                approval_status = "completed"

            # 결제 성공 처리
            cursor.execute("""
                UPDATE payment_history
                SET status = %s, processed_at = NOW()
                WHERE id = %s
            """, (approval_status, payment["id"]))

            # 구독 활성화
            cursor.execute("""
                UPDATE user_subscriptions
                SET
                    status = 'active',
                    last_payment_date = NOW(),
                    last_payment_amount = %s
                WHERE id = %s
            """, (confirm.amount, payment["subscription_id"]))

            conn.commit()

            return {
                "status": "success",
                "payment_id": payment["id"],
                "subscription_id": payment["subscription_id"],
                "message": "결제가 성공적으로 완료되었습니다"
            }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"결제 승인 실패: {e}")
        raise HTTPException(status_code=500, detail="결제 승인 처리 실패")


@router.post("/billing-key")
async def register_billing_key(
    billing: BillingKeyRequest,
    user: User = Depends(get_current_user)
):
    """빌링키 등록 (정기결제용)"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)

            if USE_TEST_MODE:
                # 테스트 모드에서는 더미 빌링키 생성
                billing_key = f"test_billing_{user.id}_{secrets.token_hex(8)}"
            else:
                # 실제 토스페이먼츠 빌링키 발급 API
                customer_key = f"user_{user.id}"

                response = requests.post(
                    f"{TOSS_API_URL}/billing/authorizations/card",
                    json={
                        "cardNumber": billing.card_number,
                        "cardExpiryYear": billing.card_expiry_year,
                        "cardExpiryMonth": billing.card_expiry_month,
                        "cardPassword": billing.card_password,
                        "birthOrBusinessNumber": billing.birth_or_business,
                        "customerKey": customer_key,
                        "customerName": billing.customer_name
                    },
                    headers={
                        **get_auth_header(),
                        "Content-Type": "application/json"
                    }
                )

                if response.status_code != 200:
                    raise HTTPException(status_code=400, detail="빌링키 발급 실패")

                result = response.json()
                billing_key = result.get("billingKey")

            # 결제 수단 저장
            cursor.execute("""
                INSERT INTO payment_methods (
                    user_id, type, card_last4, card_brand,
                    billing_key, is_default
                ) VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (billing_key) DO UPDATE
                SET is_active = true
                RETURNING id
            """, (
                user.id, "card",
                billing.card_number[-4:] if len(billing.card_number) >= 4 else "****",
                "unknown",  # 실제로는 API 응답에서 가져옴
                billing_key,
                True
            ))

            method_id = cursor.fetchone()["id"]
            conn.commit()

            return {
                "method_id": method_id,
                "billing_key": billing_key if USE_TEST_MODE else None,
                "message": "결제 수단이 등록되었습니다"
            }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"빌링키 등록 실패: {e}")
        raise HTTPException(status_code=500, detail="결제 수단 등록 실패")


@router.post("/webhook")
async def payment_webhook(
    webhook: PaymentWebhook,
    request: Request
):
    """토스페이먼츠 웹훅 처리"""
    try:
        # 웹훅 서명 검증
        if not USE_TEST_MODE:
            signature = request.headers.get("Toss-Signature", "")
            body = await request.body()
            if not verify_webhook_signature(signature, body):
                raise HTTPException(status_code=401, detail="Invalid webhook signature")

        with get_db_connection() as conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)

            if webhook.event_type == "PAYMENT_STATUS_CHANGED":
                # 결제 상태 변경 처리
                cursor.execute("""
                    UPDATE payment_history
                    SET
                        status = %s,
                        gateway_response = %s,
                        processed_at = CASE
                            WHEN %s IN ('DONE', 'PAID') THEN NOW()
                            ELSE processed_at
                        END,
                        failed_at = CASE
                            WHEN %s IN ('CANCELED', 'FAILED') THEN NOW()
                            ELSE failed_at
                        END
                    WHERE transaction_id = %s
                """, (
                    webhook.status.lower(),
                    json.dumps(webhook.data),
                    webhook.status,
                    webhook.status,
                    webhook.order_id
                ))

                conn.commit()

            return {"received": True}

    except Exception as e:
        logger.error(f"웹훅 처리 실패: {e}")
        # 웹훅은 실패해도 200 반환 (재시도 방지)
        return {"received": False, "error": "처리 중 오류 발생"}


@router.get("/history")
async def get_payment_history(
    user: User = Depends(get_current_user),
    limit: int = Query(10, ge=1, le=100)
):
    """결제 내역 조회"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)

            cursor.execute("""
                SELECT
                    h.id,
                    h.amount,
                    h.currency,
                    h.payment_method,
                    h.status,
                    h.description,
                    h.created_at,
                    h.processed_at,
                    p.display_name as plan_name
                FROM payment_history h
                LEFT JOIN user_subscriptions s ON h.subscription_id = s.id
                LEFT JOIN subscription_plans p ON s.plan_id = p.id
                WHERE h.user_id = %s
                ORDER BY h.created_at DESC
                LIMIT %s
            """, (user.id, limit))

            history = []
            for row in cursor.fetchall():
                history.append({
                    "id": row["id"],
                    "amount": row["amount"],
                    "currency": row["currency"],
                    "method": row["payment_method"],
                    "status": row["status"],
                    "description": row["description"],
                    "created_at": row["created_at"].isoformat() if row["created_at"] else None,
                    "processed_at": row["processed_at"].isoformat() if row["processed_at"] else None,
                    "plan": row["plan_name"]
                })

            return {
                "history": history,
                "total": len(history)
            }

    except Exception as e:
        logger.error(f"결제 내역 조회 실패: {e}")
        raise HTTPException(status_code=500, detail="결제 내역 조회 실패")


@router.delete("/methods/{method_id}")
async def delete_payment_method(
    method_id: int,
    user: User = Depends(get_current_user)
):
    """결제 수단 삭제"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)

            cursor.execute("""
                UPDATE payment_methods
                SET is_active = false
                WHERE id = %s AND user_id = %s
                RETURNING id
            """, (method_id, user.id))

            if not cursor.fetchone():
                raise HTTPException(status_code=404, detail="결제 수단을 찾을 수 없습니다")

            conn.commit()

            return {"message": "결제 수단이 삭제되었습니다"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"결제 수단 삭제 실패: {e}")
        raise HTTPException(status_code=500, detail="결제 수단 삭제 실패")