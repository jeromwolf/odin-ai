"""
구독 관리 서비스
구독 플랜 변경, 결제 처리, 사용량 추적 등의 비즈니스 로직
"""

from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
import logging
import hashlib
import json

from backend.models.subscription_models import (
    Subscription, SubscriptionPlanDetail, Payment,
    UsageHistory, Coupon, CouponUse,
    SubscriptionPlan, PaymentStatus
)
from backend.models.user_models import User
from backend.core.email_service import EmailService
from backend.core.config import settings

logger = logging.getLogger(__name__)


class SubscriptionService:
    """
    구독 관리 서비스 클래스
    """

    def __init__(self, db: Session):
        """서비스 초기화"""
        self.db = db
        self.email_service = EmailService()

    # ========== 구독 생성 ==========

    @staticmethod
    def create_free_subscription(user_id: int, db: Session) -> Subscription:
        """
        무료 플랜 구독 생성
        
        Args:
            user_id: 사용자 ID
            db: 데이터베이스 세션
            
        Returns:
            생성된 구독 객체
        """
        try:
            # 무료 플랜 정보 조회
            free_plan = db.query(SubscriptionPlanDetail).filter(
                SubscriptionPlanDetail.plan_type == SubscriptionPlan.FREE
            ).first()

            if not free_plan:
                # 무료 플랜이 없으면 기본값으로 생성
                free_plan = SubscriptionPlanDetail(
                    plan_type=SubscriptionPlan.FREE,
                    plan_name="무료 플랜",
                    display_name="Free Plan",
                    monthly_price=0,
                    max_searches_per_month=100,
                    max_bookmarks=50,
                    max_email_alerts=10,
                    max_api_calls=1000,
                    features={
                        "basic_search": True,
                        "advanced_search": False,
                        "ai_analysis": False,
                        "api_access": False,
                        "custom_alerts": False,
                        "export_data": False
                    }
                )
                db.add(free_plan)
                db.flush()

            # 구독 생성
            subscription = Subscription(
                user_id=user_id,
                plan_type=SubscriptionPlan.FREE,
                plan_name=free_plan.plan_name,
                is_active=True,
                is_trial=False,
                started_at=datetime.utcnow(),
                monthly_price=0,
                max_searches_per_month=free_plan.max_searches_per_month,
                max_bookmarks=free_plan.max_bookmarks,
                max_email_alerts=free_plan.max_email_alerts,
                max_api_calls=free_plan.max_api_calls,
                features=free_plan.features,
                usage_reset_date=datetime.utcnow().replace(day=1)
            )

            db.add(subscription)
            db.commit()

            logger.info(f"무료 구독 생성 완료: user_id={user_id}")
            return subscription

        except Exception as e:
            db.rollback()
            logger.error(f"무료 구독 생성 실패: {e}")
            raise

    def start_trial(
        self,
        user_id: int,
        plan_type: SubscriptionPlan = SubscriptionPlan.PROFESSIONAL,
        trial_days: int = 7
    ) -> Subscription:
        """
        무료 체험 시작
        
        Args:
            user_id: 사용자 ID
            plan_type: 체험할 플랜 타입
            trial_days: 체험 기간 (일)
            
        Returns:
            체험 구독 객체
        """
        try:
            # 플랜 정보 조회
            plan = self.db.query(SubscriptionPlanDetail).filter(
                SubscriptionPlanDetail.plan_type == plan_type
            ).first()

            if not plan:
                raise ValueError(f"플랜을 찾을 수 없습니다: {plan_type}")

            # 기존 구독 업데이트 또는 신규 생성
            subscription = self.db.query(Subscription).filter(
                Subscription.user_id == user_id
            ).first()

            trial_end_date = datetime.utcnow() + timedelta(days=trial_days)

            if subscription:
                # 기존 구독 업데이트
                subscription.plan_type = plan_type
                subscription.plan_name = plan.plan_name
                subscription.is_trial = True
                subscription.trial_ends_at = trial_end_date
                subscription.max_searches_per_month = plan.max_searches_per_month
                subscription.max_bookmarks = plan.max_bookmarks
                subscription.max_email_alerts = plan.max_email_alerts
                subscription.max_api_calls = plan.max_api_calls
                subscription.features = plan.features
            else:
                # 신규 생성
                subscription = Subscription(
                    user_id=user_id,
                    plan_type=plan_type,
                    plan_name=plan.plan_name,
                    is_active=True,
                    is_trial=True,
                    started_at=datetime.utcnow(),
                    trial_ends_at=trial_end_date,
                    monthly_price=0,  # 체험 기간 중 무료
                    max_searches_per_month=plan.max_searches_per_month,
                    max_bookmarks=plan.max_bookmarks,
                    max_email_alerts=plan.max_email_alerts,
                    max_api_calls=plan.max_api_calls,
                    features=plan.features,
                    usage_reset_date=datetime.utcnow().replace(day=1)
                )
                self.db.add(subscription)

            self.db.commit()

            logger.info(f"무료 체험 시작: user_id={user_id}, plan={plan_type}, days={trial_days}")
            return subscription

        except Exception as e:
            self.db.rollback()
            logger.error(f"무료 체험 시작 실패: {e}")
            raise

    # ========== 구독 변경 ==========

    def upgrade_plan(
        self,
        subscription_id: int,
        new_plan_type: SubscriptionPlan,
        apply_immediately: bool = False
    ) -> Subscription:
        """
        구독 플랜 업그레이드
        
        Args:
            subscription_id: 구독 ID
            new_plan_type: 새 플랜 타입
            apply_immediately: 즉시 적용 여부
            
        Returns:
            업데이트된 구독 객체
        """
        try:
            # 구독 조회
            subscription = self.db.query(Subscription).filter(
                Subscription.id == subscription_id
            ).first()

            if not subscription:
                raise ValueError("구독을 찾을 수 없습니다")

            # 새 플랜 정보 조회
            new_plan = self.db.query(SubscriptionPlanDetail).filter(
                SubscriptionPlanDetail.plan_type == new_plan_type
            ).first()

            if not new_plan:
                raise ValueError(f"플랜을 찾을 수 없습니다: {new_plan_type}")

            # 즉시 적용 또는 다음 결제일 적용
            if apply_immediately:
                # 즉시 변경
                old_plan_type = subscription.plan_type
                subscription.plan_type = new_plan_type
                subscription.plan_name = new_plan.plan_name
                subscription.monthly_price = new_plan.monthly_price
                subscription.max_searches_per_month = new_plan.max_searches_per_month
                subscription.max_bookmarks = new_plan.max_bookmarks
                subscription.max_email_alerts = new_plan.max_email_alerts
                subscription.max_api_calls = new_plan.max_api_calls
                subscription.features = new_plan.features
                subscription.is_trial = False  # 체험 종료

                # 비례 정산 처리 (프로덕션에서 결제 연동 필요)
                self._process_proration(subscription, old_plan_type, new_plan_type)

            else:
                # 다음 결제일에 적용 (예약)
                subscription.pending_plan_type = new_plan_type
                subscription.pending_plan_change_date = subscription.next_billing_date

            subscription.updated_at = datetime.utcnow()
            self.db.commit()

            logger.info(
                f"플랜 업그레이드: subscription_id={subscription_id}, "
                f"new_plan={new_plan_type}, immediate={apply_immediately}"
            )
            return subscription

        except Exception as e:
            self.db.rollback()
            logger.error(f"플랜 업그레이드 실패: {e}")
            raise

    def is_downgrade(self, current_plan: SubscriptionPlan, new_plan: SubscriptionPlan) -> bool:
        """
        다운그레이드 여부 확인
        
        Args:
            current_plan: 현재 플랜
            new_plan: 새 플랜
            
        Returns:
            다운그레이드 여부
        """
        plan_hierarchy = {
            SubscriptionPlan.FREE: 0,
            SubscriptionPlan.BASIC: 1,
            SubscriptionPlan.PROFESSIONAL: 2,
            SubscriptionPlan.ENTERPRISE: 3
        }

        return plan_hierarchy.get(new_plan, 0) < plan_hierarchy.get(current_plan, 0)

    def _process_proration(self, subscription: Subscription, old_plan: SubscriptionPlan, new_plan: SubscriptionPlan):
        """
        비례 정산 처리 (내부 메서드)
        
        Args:
            subscription: 구독 객체
            old_plan: 이전 플랜
            new_plan: 새 플랜
        """
        # 실제 프로덕션에서는 결제 서비스와 연동
        # 현재는 로그만 남김
        days_remaining = 30  # 단순화를 위해 30일 기준
        if subscription.next_billing_date:
            days_remaining = (subscription.next_billing_date - datetime.utcnow()).days

        logger.info(
            f"비례 정산: old_plan={old_plan}, new_plan={new_plan}, "
            f"days_remaining={days_remaining}"
        )

    # ========== 사용량 관리 ==========

    def track_usage(
        self,
        user_id: int,
        usage_type: str,
        quantity: int = 1,
        details: Optional[Dict] = None
    ) -> bool:
        """
        사용량 추적
        
        Args:
            user_id: 사용자 ID
            usage_type: 사용 타입 (search, api_call, bookmark, email)
            quantity: 사용량
            details: 추가 정보
            
        Returns:
            사용 가능 여부
        """
        try:
            # 구독 조회
            subscription = self.db.query(Subscription).filter(
                Subscription.user_id == user_id,
                Subscription.is_active == True
            ).first()

            if not subscription:
                return False

            # 사용 제한 확인
            if not self._check_usage_limit(subscription, usage_type, quantity):
                return False

            # 사용량 기록
            usage_history = UsageHistory(
                subscription_id=subscription.id,
                user_id=user_id,
                usage_type=usage_type,
                quantity=quantity,
                details=details or {},
                used_at=datetime.utcnow()
            )
            self.db.add(usage_history)

            # 현재 사용량 업데이트
            if usage_type == "search":
                subscription.current_searches += quantity
            elif usage_type == "api_call":
                subscription.current_api_calls += quantity

            self.db.commit()

            logger.info(f"사용량 기록: user_id={user_id}, type={usage_type}, quantity={quantity}")
            return True

        except Exception as e:
            self.db.rollback()
            logger.error(f"사용량 추적 실패: {e}")
            return False

    def _check_usage_limit(self, subscription: Subscription, usage_type: str, quantity: int) -> bool:
        """
        사용 제한 확인 (내부 메서드)
        
        Args:
            subscription: 구독 객체
            usage_type: 사용 타입
            quantity: 사용량
            
        Returns:
            사용 가능 여부
        """
        if usage_type == "search":
            return (subscription.current_searches + quantity) <= subscription.max_searches_per_month
        elif usage_type == "api_call":
            return (subscription.current_api_calls + quantity) <= subscription.max_api_calls
        elif usage_type == "bookmark":
            # 북마크는 전체 개수 체크 필요
            current_bookmarks = self.db.query(func.count()).filter(
                # UserBidBookmark 조회 로직
            ).scalar() or 0
            return (current_bookmarks + quantity) <= subscription.max_bookmarks
        elif usage_type == "email":
            # 이메일 알림 수 체크
            return True  # 이메일은 별도 관리

        return True

    def reset_monthly_usage(self):
        """
        월별 사용량 리셋 (스케줄러에서 호출)
        """
        try:
            # 리셋 대상 구독 조회
            now = datetime.utcnow()
            subscriptions = self.db.query(Subscription).filter(
                and_(
                    Subscription.is_active == True,
                    or_(
                        Subscription.usage_reset_date <= now,
                        Subscription.usage_reset_date.is_(None)
                    )
                )
            ).all()

            for subscription in subscriptions:
                subscription.current_searches = 0
                subscription.current_api_calls = 0
                subscription.usage_reset_date = now.replace(day=1) + timedelta(days=32)
                subscription.usage_reset_date = subscription.usage_reset_date.replace(day=1)

            self.db.commit()
            logger.info(f"월별 사용량 리셋 완료: {len(subscriptions)}개 구독")

        except Exception as e:
            self.db.rollback()
            logger.error(f"월별 사용량 리셋 실패: {e}")

    # ========== 결제 처리 ==========

    def process_payment(
        self,
        subscription_id: int,
        amount: Decimal,
        payment_method: str,
        transaction_id: str
    ) -> Payment:
        """
        결제 처리
        
        Args:
            subscription_id: 구독 ID
            amount: 결제 금액
            payment_method: 결제 방법
            transaction_id: 거래 ID
            
        Returns:
            결제 객체
        """
        try:
            subscription = self.db.query(Subscription).filter(
                Subscription.id == subscription_id
            ).first()

            if not subscription:
                raise ValueError("구독을 찾을 수 없습니다")

            # 결제 기록 생성
            payment = Payment(
                subscription_id=subscription_id,
                user_id=subscription.user_id,
                amount=amount,
                currency="KRW",
                payment_method=payment_method,
                status=PaymentStatus.PENDING,
                transaction_id=transaction_id,
                billing_period_start=datetime.utcnow(),
                billing_period_end=datetime.utcnow() + timedelta(days=30)
            )

            self.db.add(payment)

            # 결제 처리 (실제 PG 연동 필요)
            payment.status = PaymentStatus.COMPLETED
            payment.processed_at = datetime.utcnow()

            # 구독 갱신
            subscription.next_billing_date = payment.billing_period_end
            subscription.is_active = True

            self.db.commit()

            logger.info(f"결제 처리 완료: payment_id={payment.id}, amount={amount}")
            return payment

        except Exception as e:
            self.db.rollback()
            logger.error(f"결제 처리 실패: {e}")
            raise

    def process_recurring_payments(self):
        """
        정기 결제 처리 (스케줄러에서 호출)
        """
        try:
            # 오늘 결제할 구독 조회
            today = datetime.utcnow().date()
            subscriptions = self.db.query(Subscription).filter(
                and_(
                    Subscription.is_active == True,
                    Subscription.next_billing_date <= today,
                    Subscription.plan_type != SubscriptionPlan.FREE
                )
            ).all()

            for subscription in subscriptions:
                try:
                    # 결제 처리 (실제 PG 연동 필요)
                    self.process_payment(
                        subscription_id=subscription.id,
                        amount=subscription.monthly_price,
                        payment_method=subscription.payment_method or "card",
                        transaction_id=f"AUTO_{subscription.id}_{today}"
                    )
                except Exception as e:
                    logger.error(f"정기 결제 실패: subscription_id={subscription.id}, error={e}")
                    # 결제 실패 알림 발송
                    self._send_payment_failure_notification(subscription)

            logger.info(f"정기 결제 처리 완료: {len(subscriptions)}건")

        except Exception as e:
            logger.error(f"정기 결제 처리 실패: {e}")

    # ========== 쿠폰 관리 ==========

    def apply_coupon(
        self,
        user_id: int,
        coupon_code: str,
        payment_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        쿠폰 적용
        
        Args:
            user_id: 사용자 ID
            coupon_code: 쿠폰 코드
            payment_id: 결제 ID (선택)
            
        Returns:
            적용 결과
        """
        try:
            # 쿠폰 조회
            coupon = self.db.query(Coupon).filter(
                Coupon.code == coupon_code,
                Coupon.is_active == True
            ).first()

            if not coupon:
                return {"success": False, "message": "유효하지 않은 쿠폰입니다"}

            # 유효성 검사
            validation = self._validate_coupon(coupon, user_id)
            if not validation["valid"]:
                return {"success": False, "message": validation["message"]}

            # 쿠폰 사용 기록
            coupon_use = CouponUse(
                coupon_id=coupon.id,
                user_id=user_id,
                payment_id=payment_id,
                discount_amount=validation["discount_amount"],
                used_at=datetime.utcnow()
            )
            self.db.add(coupon_use)

            # 쿠폰 사용 횟수 증가
            coupon.current_uses += 1

            self.db.commit()

            logger.info(f"쿠폰 적용: user_id={user_id}, coupon={coupon_code}")
            return {
                "success": True,
                "discount_amount": float(validation["discount_amount"]),
                "message": "쿠폰이 적용되었습니다"
            }

        except Exception as e:
            self.db.rollback()
            logger.error(f"쿠폰 적용 실패: {e}")
            return {"success": False, "message": "쿠폰 적용 중 오류가 발생했습니다"}

    def _validate_coupon(self, coupon: Coupon, user_id: int) -> Dict[str, Any]:
        """
        쿠폰 유효성 검사 (내부 메서드)
        
        Args:
            coupon: 쿠폰 객체
            user_id: 사용자 ID
            
        Returns:
            검증 결과
        """
        now = datetime.utcnow()

        # 유효 기간 확인
        if now < coupon.valid_from or now > coupon.valid_until:
            return {"valid": False, "message": "쿠폰 유효 기간이 아닙니다"}

        # 사용 횟수 확인
        if coupon.max_uses and coupon.current_uses >= coupon.max_uses:
            return {"valid": False, "message": "쿠폰 사용 한도를 초과했습니다"}

        # 사용자별 사용 횟수 확인
        user_uses = self.db.query(func.count(CouponUse.id)).filter(
            CouponUse.coupon_id == coupon.id,
            CouponUse.user_id == user_id
        ).scalar() or 0

        if user_uses >= coupon.max_uses_per_user:
            return {"valid": False, "message": "이미 사용한 쿠폰입니다"}

        # 할인 금액 계산 (단순화)
        discount_amount = coupon.discount_value

        return {
            "valid": True,
            "discount_amount": discount_amount,
            "message": "쿠폰 적용 가능"
        }

    # ========== 알림 ==========

    async def send_upgrade_confirmation(self, user_id: int, new_plan: SubscriptionPlanDetail):
        """
        업그레이드 확인 이메일 발송
        
        Args:
            user_id: 사용자 ID
            new_plan: 새 플랜 정보
        """
        try:
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                return

            await self.email_service.send_email(
                to_email=user.email,
                subject=f"구독 플랜이 {new_plan.display_name}로 변경되었습니다",
                template="subscription_upgrade.html",
                context={
                    "user_name": user.name,
                    "plan_name": new_plan.display_name,
                    "features": new_plan.features,
                    "price": new_plan.monthly_price
                }
            )

            logger.info(f"업그레이드 확인 이메일 발송: user_id={user_id}")

        except Exception as e:
            logger.error(f"업그레이드 확인 이메일 발송 실패: {e}")

    def _send_payment_failure_notification(self, subscription: Subscription):
        """
        결제 실패 알림 발송 (내부 메서드)
        
        Args:
            subscription: 구독 객체
        """
        try:
            user = self.db.query(User).filter(User.id == subscription.user_id).first()
            if not user:
                return

            # 이메일 발송 (비동기 처리 필요)
            logger.info(f"결제 실패 알림: user_id={subscription.user_id}")

        except Exception as e:
            logger.error(f"결제 실패 알림 발송 실패: {e}")

    # ========== 통계 ==========

    def get_subscription_statistics(self) -> Dict[str, Any]:
        """
        구독 통계 조회
        
        Returns:
            통계 정보
        """
        try:
            stats = {
                "total_subscriptions": self.db.query(func.count(Subscription.id)).scalar(),
                "active_subscriptions": self.db.query(func.count(Subscription.id)).filter(
                    Subscription.is_active == True
                ).scalar(),
                "trial_subscriptions": self.db.query(func.count(Subscription.id)).filter(
                    Subscription.is_trial == True
                ).scalar(),
                "plan_distribution": {},
                "monthly_revenue": 0
            }

            # 플랜별 분포
            plan_counts = self.db.query(
                Subscription.plan_type,
                func.count(Subscription.id).label('count'),
                func.sum(Subscription.monthly_price).label('revenue')
            ).filter(
                Subscription.is_active == True
            ).group_by(
                Subscription.plan_type
            ).all()

            for row in plan_counts:
                stats["plan_distribution"][row.plan_type.value] = row.count
                stats["monthly_revenue"] += float(row.revenue or 0)

            return stats

        except Exception as e:
            logger.error(f"구독 통계 조회 실패: {e}")
            return {}