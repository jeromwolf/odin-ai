"""
이메일 스케줄러 서비스
정기적인 이메일 발송을 관리하는 스케줄러
"""

import asyncio
from datetime import datetime, time, timedelta
from typing import Optional
import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy import and_

from backend.models.database import SessionLocal
from backend.models.user_models import User
from backend.models.subscription_models import EmailSubscription
from backend.models.bid_models import BidAnnouncement
from backend.services.email_service import EmailService
from backend.core.config import settings

logger = logging.getLogger(__name__)


class EmailScheduler:
    """이메일 발송 스케줄러"""

    def __init__(self):
        """스케줄러 초기화"""
        self.scheduler = AsyncIOScheduler()
        self.email_service = EmailService()
        self.is_running = False

        # 스케줄 작업 설정
        self._setup_schedules()

    def _setup_schedules(self):
        """스케줄 작업 설정"""

        # 1. 일일 요약 이메일 (매일 오전 9시)
        self.scheduler.add_job(
            func=self.send_daily_summary,
            trigger=CronTrigger(hour=9, minute=0),
            id='daily_summary',
            name='일일 요약 이메일',
            replace_existing=True,
            misfire_grace_time=3600  # 1시간 내 실행
        )

        # 2. 실시간 알림 (매 30분마다)
        self.scheduler.add_job(
            func=self.send_realtime_alerts,
            trigger=CronTrigger(minute='*/30'),
            id='realtime_alerts',
            name='실시간 입찰 알림',
            replace_existing=True,
            misfire_grace_time=600  # 10분 내 실행
        )

        # 3. 마감 임박 알림 (매일 오후 2시)
        self.scheduler.add_job(
            func=self.send_deadline_alerts,
            trigger=CronTrigger(hour=14, minute=0),
            id='deadline_alerts',
            name='마감 임박 알림',
            replace_existing=True,
            misfire_grace_time=3600
        )

        # 4. 주간 보고서 (매주 월요일 오전 10시)
        self.scheduler.add_job(
            func=self.send_weekly_report,
            trigger=CronTrigger(day_of_week='mon', hour=10, minute=0),
            id='weekly_report',
            name='주간 보고서',
            replace_existing=True,
            misfire_grace_time=7200  # 2시간 내 실행
        )

        logger.info("이메일 스케줄 설정 완료")

    def start(self):
        """스케줄러 시작"""
        if not self.is_running:
            self.scheduler.start()
            self.is_running = True
            logger.info("이메일 스케줄러 시작됨")

    def stop(self):
        """스케줄러 중지"""
        if self.is_running:
            self.scheduler.shutdown()
            self.is_running = False
            logger.info("이메일 스케줄러 중지됨")

    async def send_daily_summary(self):
        """일일 요약 이메일 발송"""
        db = SessionLocal()
        try:
            logger.info("일일 요약 이메일 발송 시작")

            # 이메일 알림이 활성화된 모든 구독자
            subscriptions = db.query(EmailSubscription).filter(
                EmailSubscription.is_active == True,
                EmailSubscription.daily_summary == True
            ).all()

            sent_count = 0
            error_count = 0

            for subscription in subscriptions:
                try:
                    # 사용자별 맞춤 데이터 수집
                    user = db.query(User).filter(User.id == subscription.user_id).first()
                    if not user:
                        continue

                    # 오늘의 통계
                    today = datetime.now().date()

                    # 새로운 입찰공고 (24시간 내)
                    new_bids = db.query(BidAnnouncement).filter(
                        BidAnnouncement.created_at >= datetime.now() - timedelta(days=1)
                    ).count()

                    # 마감 임박 (3일 이내)
                    deadline_soon = db.query(BidAnnouncement).filter(
                        and_(
                            BidAnnouncement.closing_date >= datetime.now(),
                            BidAnnouncement.closing_date <= datetime.now() + timedelta(days=3)
                        )
                    ).count()

                    # 키워드 매칭 입찰
                    keyword_bids = []
                    if subscription.keywords:
                        keywords = [k.strip() for k in subscription.keywords.split(',')]
                        for keyword in keywords[:5]:  # 최대 5개 키워드
                            bids = db.query(BidAnnouncement).filter(
                                BidAnnouncement.bid_notice_name.contains(keyword)
                            ).limit(3).all()

                            for bid in bids:
                                keyword_bids.append({
                                    'keyword': keyword,
                                    'title': bid.bid_notice_name,
                                    'organization': bid.organization_name,
                                    'deadline': bid.closing_date.strftime('%Y-%m-%d %H:%M')
                                })

                    # 이메일 발송
                    await self.email_service.send_daily_summary(
                        to_email=user.email,
                        user_name=user.name,
                        new_bids=new_bids,
                        deadline_soon=deadline_soon,
                        keyword_bids=keyword_bids
                    )

                    sent_count += 1

                except Exception as e:
                    logger.error(f"사용자 {subscription.user_id} 이메일 발송 실패: {e}")
                    error_count += 1

            logger.info(f"일일 요약 이메일 발송 완료: 성공 {sent_count}건, 실패 {error_count}건")

        except Exception as e:
            logger.error(f"일일 요약 이메일 발송 중 오류: {e}")
        finally:
            db.close()

    async def send_realtime_alerts(self):
        """실시간 입찰 알림 발송"""
        db = SessionLocal()
        try:
            logger.info("실시간 입찰 알림 발송 시작")

            # 실시간 알림이 활성화된 구독자
            subscriptions = db.query(EmailSubscription).filter(
                EmailSubscription.is_active == True,
                EmailSubscription.realtime_alerts == True
            ).all()

            sent_count = 0

            for subscription in subscriptions:
                try:
                    user = db.query(User).filter(User.id == subscription.user_id).first()
                    if not user:
                        continue

                    # 최근 30분 내 등록된 입찰공고
                    recent_bids = db.query(BidAnnouncement).filter(
                        BidAnnouncement.created_at >= datetime.now() - timedelta(minutes=30)
                    )

                    # 키워드 필터링
                    if subscription.keywords:
                        keywords = [k.strip() for k in subscription.keywords.split(',')]
                        bid_list = []

                        for bid in recent_bids:
                            for keyword in keywords:
                                if keyword.lower() in bid.bid_notice_name.lower():
                                    bid_list.append({
                                        'title': bid.bid_notice_name,
                                        'organization': bid.organization_name,
                                        'amount': f"{bid.bid_amount:,}" if bid.bid_amount else "미정",
                                        'deadline': bid.closing_date.strftime('%Y-%m-%d %H:%M'),
                                        'url': f"{settings.APP_URL}/bids/{bid.id}"
                                    })
                                    break

                        if bid_list:
                            await self.email_service.send_realtime_alert(
                                to_email=user.email,
                                user_name=user.name,
                                bids=bid_list
                            )
                            sent_count += 1

                except Exception as e:
                    logger.error(f"사용자 {subscription.user_id} 실시간 알림 실패: {e}")

            logger.info(f"실시간 입찰 알림 발송 완료: {sent_count}건")

        except Exception as e:
            logger.error(f"실시간 알림 발송 중 오류: {e}")
        finally:
            db.close()

    async def send_deadline_alerts(self):
        """마감 임박 알림 발송"""
        db = SessionLocal()
        try:
            logger.info("마감 임박 알림 발송 시작")

            # 마감 알림이 활성화된 구독자
            subscriptions = db.query(EmailSubscription).filter(
                EmailSubscription.is_active == True,
                EmailSubscription.deadline_alerts == True
            ).all()

            sent_count = 0

            for subscription in subscriptions:
                try:
                    user = db.query(User).filter(User.id == subscription.user_id).first()
                    if not user:
                        continue

                    # 24시간 내 마감되는 입찰
                    deadline_bids = db.query(BidAnnouncement).filter(
                        and_(
                            BidAnnouncement.closing_date >= datetime.now(),
                            BidAnnouncement.closing_date <= datetime.now() + timedelta(hours=24)
                        )
                    )

                    # 키워드 필터링
                    bid_list = []
                    if subscription.keywords:
                        keywords = [k.strip() for k in subscription.keywords.split(',')]

                        for bid in deadline_bids:
                            for keyword in keywords:
                                if keyword.lower() in bid.bid_notice_name.lower():
                                    remaining_hours = (bid.closing_date - datetime.now()).total_seconds() / 3600
                                    bid_list.append({
                                        'title': bid.bid_notice_name,
                                        'organization': bid.organization_name,
                                        'deadline': bid.closing_date.strftime('%Y-%m-%d %H:%M'),
                                        'remaining_hours': int(remaining_hours),
                                        'url': f"{settings.APP_URL}/bids/{bid.id}"
                                    })
                                    break

                    if bid_list:
                        await self.email_service.send_deadline_alert(
                            to_email=user.email,
                            user_name=user.name,
                            bids=bid_list
                        )
                        sent_count += 1

                except Exception as e:
                    logger.error(f"사용자 {subscription.user_id} 마감 알림 실패: {e}")

            logger.info(f"마감 임박 알림 발송 완료: {sent_count}건")

        except Exception as e:
            logger.error(f"마감 알림 발송 중 오류: {e}")
        finally:
            db.close()

    async def send_weekly_report(self):
        """주간 보고서 발송"""
        db = SessionLocal()
        try:
            logger.info("주간 보고서 발송 시작")

            # 주간 보고서를 구독한 사용자
            subscriptions = db.query(EmailSubscription).filter(
                EmailSubscription.is_active == True,
                EmailSubscription.weekly_report == True
            ).all()

            sent_count = 0
            week_ago = datetime.now() - timedelta(days=7)

            for subscription in subscriptions:
                try:
                    user = db.query(User).filter(User.id == subscription.user_id).first()
                    if not user:
                        continue

                    # 주간 통계
                    total_bids = db.query(BidAnnouncement).filter(
                        BidAnnouncement.created_at >= week_ago
                    ).count()

                    # 분야별 통계
                    industry_stats = {}

                    # 금액대별 통계
                    price_ranges = {
                        '1억 미만': 0,
                        '1억-10억': 0,
                        '10억-50억': 0,
                        '50억 이상': 0
                    }

                    bids = db.query(BidAnnouncement).filter(
                        BidAnnouncement.created_at >= week_ago
                    ).all()

                    for bid in bids:
                        # 금액대 분류
                        if bid.bid_amount:
                            if bid.bid_amount < 100000000:
                                price_ranges['1억 미만'] += 1
                            elif bid.bid_amount < 1000000000:
                                price_ranges['1억-10억'] += 1
                            elif bid.bid_amount < 5000000000:
                                price_ranges['10억-50억'] += 1
                            else:
                                price_ranges['50억 이상'] += 1

                    # 이메일 발송
                    await self.email_service.send_weekly_report(
                        to_email=user.email,
                        user_name=user.name,
                        total_bids=total_bids,
                        price_ranges=price_ranges,
                        top_organizations=[]  # TODO: 상위 발주기관 통계
                    )

                    sent_count += 1

                except Exception as e:
                    logger.error(f"사용자 {subscription.user_id} 주간 보고서 실패: {e}")

            logger.info(f"주간 보고서 발송 완료: {sent_count}건")

        except Exception as e:
            logger.error(f"주간 보고서 발송 중 오류: {e}")
        finally:
            db.close()


# 전역 스케줄러 인스턴스
email_scheduler = EmailScheduler()