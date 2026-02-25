"""
알림 서비스
이메일, 웹푸시, SMS 알림을 통합 처리하는 서비스
"""

import asyncio
import os
import smtplib
import json
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone

from database import get_db_connection
from psycopg2.extras import RealDictCursor

logger = logging.getLogger(__name__)

class NotificationService:
    """통합 알림 서비스"""

    def __init__(self):
        # 이메일 설정 (환경변수에서 가져와야 함)
        self.smtp_server = "smtp.gmail.com"
        self.smtp_port = 587
        self.email_user = os.getenv("SMTP_USER", "")
        self.email_password = os.getenv("SMTP_PASSWORD", "")

    async def send_email_notification(
        self,
        user_id: int,
        template_name: str,
        template_data: Dict[str, Any],
        override_email: Optional[str] = None
    ) -> bool:
        """이메일 알림 발송"""
        try:
            # 사용자 이메일 조회 (sync DB를 thread에서 실행)
            user_email = override_email or await asyncio.to_thread(self._get_user_email, user_id)
            if not user_email:
                logger.warning(f"사용자 이메일을 찾을 수 없음: user_id={user_id}")
                return False

            # 템플릿 조회 및 렌더링 (sync DB를 thread에서 실행)
            template = await asyncio.to_thread(self._get_email_template, template_name)
            if not template:
                logger.error(f"이메일 템플릿을 찾을 수 없음: {template_name}")
                return False

            subject = self._render_template(template['subject_template'], template_data)
            content = self._render_template(template['content_template'], template_data)

            # 이메일 발송 (sync SMTP를 thread에서 실행)
            return await asyncio.to_thread(self._send_email, user_email, subject, content)

        except Exception as e:
            logger.error(f"이메일 알림 발송 실패: {e}")
            return False

    async def send_web_notification(
        self,
        user_id: int,
        template_name: str,
        template_data: Dict[str, Any]
    ) -> bool:
        """웹 푸시 알림 발송"""
        try:
            # 웹 알림 템플릿 조회 (sync DB를 thread에서 실행)
            template = await asyncio.to_thread(self._get_web_template, template_name)
            if not template:
                logger.error(f"웹 알림 템플릿을 찾을 수 없음: {template_name}")
                return False

            title = self._render_template(template['subject_template'], template_data)
            message = self._render_template(template['content_template'], template_data)

            # 웹 알림 저장 (sync DB를 thread에서 실행)
            await asyncio.to_thread(self._store_web_notification, user_id, title, message)

            return True

        except Exception as e:
            logger.error(f"웹 푸시 알림 발송 실패: {e}")
            return False

    async def send_sms_notification(
        self,
        user_id: int,
        template_data: Dict[str, Any]
    ) -> bool:
        """SMS 알림 발송"""
        try:
            # SMS는 간단한 메시지로만 구성
            phone_number = await asyncio.to_thread(self._get_user_phone, user_id)
            if not phone_number:
                logger.warning(f"사용자 전화번호를 찾을 수 없음: user_id={user_id}")
                return False

            message = f"[ODIN-AI] 새로운 입찰: {template_data.get('title', '알림')}"

            # 실제 SMS 발송 로직 (여기서는 로그만)
            logger.info(f"SMS 발송: {phone_number} - {message}")

            return True

        except Exception as e:
            logger.error(f"SMS 알림 발송 실패: {e}")
            return False

    def _get_user_email(self, user_id: int) -> Optional[str]:
        """사용자 이메일 조회"""
        with get_db_connection() as conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute("SELECT email FROM users WHERE id = %s", (user_id,))
            result = cursor.fetchone()
            return result['email'] if result else None

    def _get_user_phone(self, user_id: int) -> Optional[str]:
        """사용자 전화번호 조회"""
        with get_db_connection() as conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute(
                "SELECT sms_phone_number FROM user_notification_settings WHERE user_id = %s",
                (user_id,)
            )
            result = cursor.fetchone()
            return result['sms_phone_number'] if result else None

    def _get_email_template(self, template_name: str) -> Optional[Dict[str, str]]:
        """이메일 템플릿 조회"""
        with get_db_connection() as conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute(
                "SELECT subject_template, content_template FROM notification_templates "
                "WHERE template_name = %s AND channel = 'email' AND is_active = true",
                (template_name,)
            )
            result = cursor.fetchone()
            if result:
                return {
                    'subject_template': result['subject_template'],
                    'content_template': result['content_template']
                }
            return None

    def _get_web_template(self, template_name: str) -> Optional[Dict[str, str]]:
        """웹 알림 템플릿 조회"""
        with get_db_connection() as conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute(
                "SELECT subject_template, content_template FROM notification_templates "
                "WHERE template_name = %s AND channel = 'web' AND is_active = true",
                (template_name,)
            )
            result = cursor.fetchone()
            if result:
                return {
                    'subject_template': result['subject_template'],
                    'content_template': result['content_template']
                }
            return None

    def _render_template(self, template: str, data: Dict[str, Any]) -> str:
        """템플릿 렌더링 (간단한 문자열 치환)"""
        result = template
        for key, value in data.items():
            placeholder = "{{" + key + "}}"
            result = result.replace(placeholder, str(value))
        return result

    def _send_email(self, to_email: str, subject: str, content: str) -> bool:
        """실제 이메일 발송"""
        try:
            # MIME 메시지 생성
            msg = MIMEMultipart('alternative')
            msg['From'] = self.email_user
            msg['To'] = to_email
            msg['Subject'] = subject

            # HTML 콘텐츠 추가
            html_part = MIMEText(content, 'html', 'utf-8')
            msg.attach(html_part)

            # SMTP 서버 연결 및 발송
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.email_user, self.email_password)
            server.send_message(msg)
            server.quit()

            logger.info(f"이메일 발송 성공: {to_email}")
            return True

        except Exception as e:
            logger.error(f"이메일 발송 실패: {e}")
            return False

    def _store_web_notification(self, user_id: int, title: str, message: str):
        """웹 알림 저장"""
        with get_db_connection() as conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)

            # 웹 알림용 별도 테이블이 있다면 저장
            # 여기서는 간단히 alert_notifications 테이블에 저장
            cursor.execute("""
                INSERT INTO alert_notifications (
                    user_id, bid_notice_no, channel, status,
                    subject, content, created_at
                ) VALUES (%s, 'WEB_NOTIFICATION', 'web', 'sent', %s, %s, %s)
            """, (user_id, title, message, datetime.now(timezone.utc)))

            conn.commit()

    async def send_batch_summary(self, batch_stats: Dict[str, Any]):
        """배치 처리 결과 요약 이메일 발송 (관리자용)"""
        admin_emails_str = os.getenv("ADMIN_NOTIFICATION_EMAILS", "")
        admin_emails = [e.strip() for e in admin_emails_str.split(",") if e.strip()]
        if not admin_emails:
            logger.warning("ADMIN_NOTIFICATION_EMAILS 미설정 - 배치 요약 이메일 발송 생략")
            return

        subject = f"[ODIN-AI] 배치 처리 완료 - {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M')}"

        content = f"""
        <h2>배치 처리 완료 보고서</h2>
        <ul>
            <li>처리된 입찰 공고: {batch_stats.get('total_bids', 0)}개</li>
            <li>검사된 알림 규칙: {batch_stats.get('total_rules_checked', 0)}개</li>
            <li>매칭된 규칙: {batch_stats.get('total_matches', 0)}개</li>
            <li>발송된 알림: {batch_stats.get('notifications_sent', 0)}개</li>
            <li>오류 발생: {batch_stats.get('errors', 0)}건</li>
        </ul>
        <p>처리 시간: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')}</p>
        """

        for admin_email in admin_emails:
            await asyncio.to_thread(self._send_email, admin_email, subject, content)

    def get_user_notification_stats(self, user_id: int) -> Dict[str, Any]:
        """사용자 알림 통계 조회"""
        with get_db_connection() as conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)

            # 최근 30일 알림 통계
            cursor.execute("""
                SELECT
                    channel,
                    COUNT(*) as total_count,
                    COUNT(CASE WHEN status = 'sent' THEN 1 END) as sent_count,
                    COUNT(CASE WHEN status = 'failed' THEN 1 END) as failed_count,
                    COUNT(CASE WHEN read_at IS NOT NULL THEN 1 END) as read_count
                FROM alert_notifications
                WHERE user_id = %s
                  AND created_at >= CURRENT_DATE - INTERVAL '30 days'
                GROUP BY channel
            """, (user_id,))

            stats = {}
            for row in cursor.fetchall():
                channel = row['channel']
                total = row['total_count']
                sent = row['sent_count']
                failed = row['failed_count']
                read = row['read_count']
                stats[channel] = {
                    'total': total,
                    'sent': sent,
                    'failed': failed,
                    'read': read,
                    'success_rate': (sent / total * 100) if total > 0 else 0,
                    'read_rate': (read / sent * 100) if sent > 0 else 0
                }

            return stats