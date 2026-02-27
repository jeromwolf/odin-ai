"""
알림 처리 엔진
새로운 입찰 공고에 대해 사용자 알림 규칙을 검사하고 알림을 발송합니다.
"""

import asyncio
import json
import logging
import os
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from psycopg2.extras import RealDictCursor

from database import get_db_connection

FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")
from .notification_service import NotificationService

logger = logging.getLogger(__name__)

@dataclass
class BidAnnouncement:
    """입찰 공고 데이터"""
    bid_notice_no: str
    title: str
    organization_name: str
    estimated_price: Optional[float]
    bid_start_date: Optional[datetime]
    bid_end_date: Optional[datetime]
    region_restriction: Optional[str]
    bid_category: Optional[str]
    qualification_summary: Optional[str]
    contract_method: Optional[str]
    created_at: datetime

@dataclass
class AlertRule:
    """알림 규칙"""
    id: int
    user_id: int
    rule_name: str
    conditions: Dict[str, Any]
    match_type: str
    notification_channels: List[str]
    notification_timing: str
    is_active: bool

class AlertEngine:
    """알림 처리 엔진"""

    def __init__(self):
        self.notification_service = NotificationService()

    async def process_new_bids(self, bids: List[BidAnnouncement]) -> Dict[str, int]:
        """
        새로운 입찰 공고들에 대해 알림 규칙을 검사하고 알림을 발송

        Returns:
            Dict[str, int]: 처리 통계
        """
        stats = {
            'total_bids': len(bids),
            'total_rules_checked': 0,
            'total_matches': 0,
            'notifications_sent': 0,
            'errors': 0
        }

        logger.info(f"새로운 입찰 공고 {len(bids)}개에 대한 알림 처리 시작")

        try:
            # 활성화된 알림 규칙들 가져오기 (sync DB를 thread에서 실행)
            alert_rules = await asyncio.to_thread(self._get_active_alert_rules)
            stats['total_rules_checked'] = len(alert_rules)

            # 각 입찰 공고에 대해 알림 규칙 검사 (순수 계산)
            for bid in bids:
                matches = self._check_bid_against_rules(bid, alert_rules)
                stats['total_matches'] += len(matches)

                # 매칭된 규칙들에 대해 알림 발송
                for rule, match_details in matches:
                    try:
                        await self._send_notification(bid, rule, match_details)
                        stats['notifications_sent'] += 1
                    except Exception as e:
                        logger.error(f"알림 발송 실패 (rule_id: {rule.id}): {e}")
                        stats['errors'] += 1

        except Exception as e:
            logger.error(f"알림 엔진 처리 중 오류: {e}")
            stats['errors'] += 1

        logger.info(f"알림 처리 완료: {stats}")
        return stats

    def _get_active_alert_rules(self) -> List[AlertRule]:
        """활성화된 알림 규칙들 조회"""
        with get_db_connection() as conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)

            query = """
                SELECT id, user_id, rule_name, conditions, match_type,
                       notification_channels, notification_timing, is_active
                FROM alert_rules
                WHERE is_active = true
                ORDER BY user_id, created_at
            """

            cursor.execute(query)
            rules = []

            for row in cursor.fetchall():
                rule = AlertRule(
                    id=row['id'],
                    user_id=row['user_id'],
                    rule_name=row['rule_name'],
                    conditions=json.loads(row['conditions']) if isinstance(row['conditions'], str) else row['conditions'],
                    match_type=row['match_type'],
                    notification_channels=row['notification_channels'],
                    notification_timing=row['notification_timing'],
                    is_active=row['is_active']
                )
                rules.append(rule)

            return rules

    def _check_bid_against_rules(
        self,
        bid: BidAnnouncement,
        rules: List[AlertRule]
    ) -> List[Tuple[AlertRule, Dict[str, Any]]]:
        """입찰 공고가 알림 규칙들과 매칭되는지 검사 (순수 계산, I/O 없음)"""
        matches = []

        for rule in rules:
            match_result = self._evaluate_rule_conditions(bid, rule)
            if match_result['matched']:
                matches.append((rule, match_result))

        return matches

    def _evaluate_rule_conditions(
        self,
        bid: BidAnnouncement,
        rule: AlertRule
    ) -> Dict[str, Any]:
        """알림 규칙의 조건들을 평가"""
        conditions = rule.conditions
        results = []
        match_details = {
            'matched': False,
            'matched_conditions': [],
            'failed_conditions': []
        }

        # 키워드 검사
        if 'keywords' in conditions and conditions['keywords']:
            keyword_match = self._check_keywords(bid.title, conditions['keywords'])
            results.append(keyword_match)
            if keyword_match:
                match_details['matched_conditions'].append('keywords')
            else:
                match_details['failed_conditions'].append('keywords')

        # 제외 키워드 검사
        if 'exclude_keywords' in conditions and conditions['exclude_keywords']:
            exclude_match = not self._check_keywords(bid.title, conditions['exclude_keywords'])
            results.append(exclude_match)
            if exclude_match:
                match_details['matched_conditions'].append('exclude_keywords')
            else:
                match_details['failed_conditions'].append('exclude_keywords')

        # 가격 범위 검사
        if bid.estimated_price:
            if 'min_price' in conditions and conditions['min_price']:
                price_min_match = bid.estimated_price >= conditions['min_price']
                results.append(price_min_match)
                if price_min_match:
                    match_details['matched_conditions'].append('min_price')
                else:
                    match_details['failed_conditions'].append('min_price')

            if 'max_price' in conditions and conditions['max_price']:
                price_max_match = bid.estimated_price <= conditions['max_price']
                results.append(price_max_match)
                if price_max_match:
                    match_details['matched_conditions'].append('max_price')
                else:
                    match_details['failed_conditions'].append('max_price')

        # 기관 검사
        if 'organizations' in conditions and conditions['organizations']:
            org_match = any(
                org.lower() in bid.organization_name.lower()
                for org in conditions['organizations']
            )
            results.append(org_match)
            if org_match:
                match_details['matched_conditions'].append('organizations')
            else:
                match_details['failed_conditions'].append('organizations')

        # 지역 검사
        if 'regions' in conditions and conditions['regions'] and bid.region_restriction:
            region_match = any(
                region.lower() in bid.region_restriction.lower()
                for region in conditions['regions']
            )
            results.append(region_match)
            if region_match:
                match_details['matched_conditions'].append('regions')
            else:
                match_details['failed_conditions'].append('regions')

        # 카테고리 검사
        if 'categories' in conditions and conditions['categories'] and bid.bid_category:
            category_match = any(
                category.lower() in bid.bid_category.lower()
                for category in conditions['categories']
            )
            results.append(category_match)
            if category_match:
                match_details['matched_conditions'].append('categories')
            else:
                match_details['failed_conditions'].append('categories')

        # 매칭 타입에 따른 최종 결과
        if rule.match_type == 'ALL':
            match_details['matched'] = all(results) if results else False
        else:  # 'ANY'
            match_details['matched'] = any(results) if results else False

        return match_details

    def _check_keywords(self, text: str, keywords: List[str]) -> bool:
        """키워드 매칭 검사"""
        text_lower = text.lower()
        return any(keyword.lower() in text_lower for keyword in keywords)

    async def _send_notification(
        self,
        bid: BidAnnouncement,
        rule: AlertRule,
        match_details: Dict[str, Any]
    ):
        """알림 발송"""

        # 즉시 알림인 경우에만 바로 발송
        if rule.notification_timing == 'immediate':
            for channel in rule.notification_channels:
                await self._send_immediate_notification(bid, rule, channel, match_details)
        else:
            # 일일/주간 알림은 스케줄링 (알림 기록만 저장)
            await self._schedule_notification(bid, rule, match_details)

        # 알림 규칙 트리거 횟수 업데이트 (sync DB를 thread에서 실행)
        await asyncio.to_thread(self._update_rule_trigger_count, rule.id)

    async def _send_immediate_notification(
        self,
        bid: BidAnnouncement,
        rule: AlertRule,
        channel: str,
        match_details: Dict[str, Any]
    ):
        """즉시 알림 발송"""
        try:
            # 알림 기록 생성 (sync DB를 thread에서 실행)
            notification_id = await asyncio.to_thread(
                self._create_notification_record, bid, rule, channel
            )

            # 템플릿 기반 메시지 생성
            template_data = {
                'title': bid.title,
                'bid_notice_no': bid.bid_notice_no,
                'organization_name': bid.organization_name,
                'estimated_price': f"{bid.estimated_price:,.0f}원" if bid.estimated_price else "미정",
                'bid_end_date': bid.bid_end_date.strftime('%Y-%m-%d %H:%M') if bid.bid_end_date else "미정",
                'detail_url': f"{FRONTEND_URL}/bids/{bid.bid_notice_no}",
                'matched_conditions': ', '.join(match_details['matched_conditions'])
            }

            if channel == 'email':
                await self.notification_service.send_email_notification(
                    rule.user_id,
                    template_name='bid_match_email',
                    template_data=template_data
                )
            elif channel == 'web':
                await self.notification_service.send_web_notification(
                    rule.user_id,
                    template_name='bid_match_web',
                    template_data=template_data
                )
            elif channel == 'sms':
                await self.notification_service.send_sms_notification(
                    rule.user_id,
                    template_data=template_data
                )

            # 발송 완료 상태 업데이트 (sync DB를 thread에서 실행)
            await asyncio.to_thread(self._update_notification_status, notification_id, 'sent')

        except Exception as e:
            logger.error(f"즉시 알림 발송 실패 (rule_id: {rule.id}, channel: {channel}): {e}")
            await asyncio.to_thread(self._update_notification_status, notification_id, 'failed', str(e))

    async def _schedule_notification(
        self,
        bid: BidAnnouncement,
        rule: AlertRule,
        match_details: Dict[str, Any]
    ):
        """일일/주간 알림 스케줄링 (기록 저장)"""
        for channel in rule.notification_channels:
            await asyncio.to_thread(
                self._create_notification_record, bid, rule, channel, 'pending'
            )

    def _create_notification_record(
        self,
        bid: BidAnnouncement,
        rule: AlertRule,
        channel: str,
        status: str = 'pending'
    ) -> int:
        """알림 기록 생성"""
        with get_db_connection() as conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)

            subject = f"[ODIN-AI] 새로운 입찰 공고: {bid.title}"
            content = f"{bid.organization_name} - {bid.title}"

            query = """
                INSERT INTO notifications (
                    user_id, alert_rule_id, title, message,
                    type, status, metadata
                ) VALUES (%s, %s, %s, %s, %s, %s, %s::jsonb)
                RETURNING id
            """

            import json
            metadata = json.dumps({
                "bid_notice_no": bid.bid_notice_no,
                "channel": channel
            })

            cursor.execute(query, (
                rule.user_id, rule.id, subject, content,
                'alert', status, metadata
            ))

            notification_id = cursor.fetchone()['id']
            conn.commit()
            return notification_id

    def _update_notification_status(
        self,
        notification_id: int,
        status: str,
        error_message: str = None
    ):
        """알림 상태 업데이트"""
        with get_db_connection() as conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)

            if status == 'sent':
                query = """
                    UPDATE alert_notifications
                    SET status = %s, sent_at = CURRENT_TIMESTAMP
                    WHERE id = %s
                """
                cursor.execute(query, (status, notification_id))
            else:
                query = """
                    UPDATE alert_notifications
                    SET status = %s, error_message = %s
                    WHERE id = %s
                """
                cursor.execute(query, (status, error_message, notification_id))

            conn.commit()

    def _update_rule_trigger_count(self, rule_id: int):
        """알림 규칙 트리거 횟수 업데이트"""
        with get_db_connection() as conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)

            query = """
                UPDATE alert_rules
                SET updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
            """
            cursor.execute(query, (rule_id,))
            conn.commit()

    async def process_scheduled_notifications(self):
        """스케줄된 알림들 처리 (일일/주간 배치)"""
        logger.info("스케줄된 알림 처리 시작")

        # 일일 알림 처리
        await self._process_daily_notifications()

        # 주간 알림 처리 (월요일에만)
        if datetime.now(timezone.utc).weekday() == 0:  # 월요일
            await self._process_weekly_notifications()

    async def _process_daily_notifications(self):
        """일일 알림 처리"""
        with get_db_connection() as conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)

            # 어제부터 오늘까지의 pending 알림들을 사용자별로 그룹화
            query = """
                SELECT n.user_id, COUNT(*) as count,
                       ARRAY_AGG(DISTINCT (n.metadata->>'bid_notice_no')) as bid_notices
                FROM notifications n
                JOIN alert_rules ar ON n.alert_rule_id = ar.id
                WHERE n.status = 'unread'
                  AND ar.notification_timing = 'daily'
                  AND n.created_at >= CURRENT_DATE - INTERVAL '1 day'
                GROUP BY n.user_id
            """

            cursor.execute(query)
            daily_summaries = cursor.fetchall()

            for row in daily_summaries:
                user_id = row['user_id']
                count = row['count']
                bid_notices = row['bid_notices']
                await self._send_daily_summary(user_id, count, bid_notices)

                # 처리된 알림들 상태 업데이트
                update_query = """
                    UPDATE notifications
                    SET status = 'read'
                    WHERE user_id = %s AND status = 'unread'
                      AND created_at >= CURRENT_DATE - INTERVAL '1 day'
                """
                cursor.execute(update_query, (user_id,))

            conn.commit()

    async def _send_daily_summary(self, user_id: int, count: int, bid_notices: List[str]):
        """일일 요약 알림 발송"""
        template_data = {
            'count': count,
            'date': datetime.now(timezone.utc).strftime('%Y년 %m월 %d일'),
            'bid_notices': bid_notices[:10],  # 최대 10개만
            'dashboard_url': f'{FRONTEND_URL}/dashboard'
        }

        await self.notification_service.send_email_notification(
            user_id,
            template_name='daily_summary_email',
            template_data=template_data
        )