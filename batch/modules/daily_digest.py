#!/usr/bin/env python
"""
일일 다이제스트 이메일 발송 모듈
매일 1회 실행하여 전일 알림을 요약 발송
"""

import json
import os
import smtplib
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Dict, List, Optional

import psycopg2

from loguru import logger


class DailyDigestSender:
    """일일 다이제스트 이메일 발송 클래스"""

    def __init__(self, db_url: Optional[str] = None):
        self.db_url = db_url or os.getenv(
            'DATABASE_URL', 'postgresql://blockmeta@localhost:5432/odin_db'
        )
        self.frontend_url = os.getenv('FRONTEND_URL', 'http://localhost:3000')
        self.emails_sent = 0

    def run(self, hours: int = 24) -> Dict:
        """일일 다이제스트 실행

        Args:
            hours: 몇 시간 전부터의 알림을 집계할지 (기본 24시간)

        Returns:
            dict: 실행 결과 통계
        """
        logger.info(f"📬 일일 다이제스트 시작 - 최근 {hours}시간 알림 집계")

        try:
            # 1. 다이제스트 활성화된 사용자 조회
            users = self._get_digest_users()
            logger.info(f"다이제스트 대상 사용자: {len(users)}명")

            if not users:
                logger.info("다이제스트 대상 사용자가 없습니다")
                return {"users": 0, "emails_sent": 0}

            # 2. 사용자별 알림 집계 및 발송
            for user in users:
                notifications = self._get_user_notifications(user['id'], hours)
                if notifications:
                    logger.info(
                        f"사용자 {user['id']} ({user['email']}): {len(notifications)}건 알림"
                    )
                    self._send_digest_email(user, notifications)
                else:
                    logger.debug(f"사용자 {user['id']}: 알림 없음 - 발송 건너뜀")

            logger.info(
                f"✅ 일일 다이제스트 완료 - {self.emails_sent}개 이메일 발송"
            )
            return {"users": len(users), "emails_sent": self.emails_sent}

        except Exception as e:
            logger.error(f"❌ 일일 다이제스트 실패: {e}")
            raise

    def _get_digest_users(self) -> List[Dict]:
        """daily_digest_enabled = true인 활성 사용자 조회"""
        with psycopg2.connect(self.db_url) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT u.id, u.email, u.full_name, u.username
                FROM users u
                JOIN user_notification_settings uns ON u.id = uns.user_id
                WHERE uns.daily_digest_enabled = true
                    AND u.is_active = true
                    AND u.email IS NOT NULL
                ORDER BY u.id
            """)
            columns = [desc[0] for desc in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]

    def _get_user_notifications(self, user_id: int, hours: int) -> List[Dict]:
        """사용자의 최근 N시간 알림 조회"""
        with psycopg2.connect(self.db_url) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT n.id, n.title, n.message, n.type, n.priority,
                       n.metadata, n.created_at, n.status
                FROM notifications n
                WHERE n.user_id = %s
                    AND n.created_at >= NOW() - INTERVAL '%s hours'
                ORDER BY n.created_at DESC
            """, (user_id, hours))
            columns = [desc[0] for desc in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]

    def _send_digest_email(self, user: Dict, notifications: List[Dict]):
        """다이제스트 이메일 발송"""
        smtp_host = os.getenv("SMTP_HOST") or os.getenv("EMAIL_HOST", "smtp.gmail.com")
        smtp_port = int(os.getenv("SMTP_PORT") or os.getenv("EMAIL_PORT", "587"))
        smtp_user = os.getenv("SMTP_USER") or os.getenv("EMAIL_USERNAME", "")
        smtp_password = os.getenv("SMTP_PASSWORD") or os.getenv("EMAIL_PASSWORD", "")

        if not smtp_user or not smtp_password:
            logger.warning("⚠️ SMTP 설정이 없습니다. 다이제스트 발송을 건너뜁니다.")
            return

        user_email = user['email']
        user_name = user.get('full_name') or user.get('username') or '사용자'
        count = len(notifications)

        try:
            html = self._generate_digest_html(user_name, notifications)

            msg = MIMEMultipart('alternative')
            msg['Subject'] = f"📋 ODIN-AI 일일 다이제스트 - {count}건의 알림 요약"
            msg['From'] = smtp_user
            msg['To'] = user_email
            msg.attach(MIMEText(html, 'html', 'utf-8'))

            with smtplib.SMTP(smtp_host, smtp_port) as server:
                server.starttls()
                server.login(smtp_user, smtp_password)
                server.send_message(msg)

            self.emails_sent += 1
            logger.info(f"📧 다이제스트 발송 성공: {user_email} ({count}건)")

            # 발송 로그 기록 (성공)
            self._log_send(user['id'], user_email, count, 'sent')

        except Exception as e:
            logger.error(f"❌ 다이제스트 발송 실패 ({user_email}): {e}")
            self._log_send(user['id'], user_email, count, 'failed', str(e))

    def _log_send(
        self,
        user_id: int,
        email: str,
        count: int,
        status: str,
        error: Optional[str] = None,
    ):
        """notification_send_logs 테이블에 발송 로그 기록

        실제 테이블 컬럼:
            notification_type, user_id, email_to, email_subject,
            status, sent_at, error_message, metadata
        """
        try:
            with psycopg2.connect(self.db_url) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO notification_send_logs (
                        notification_type, user_id, email_to, email_subject,
                        status, sent_at, error_message, metadata
                    ) VALUES (%s, %s, %s, %s, %s, NOW(), %s, %s)
                """, (
                    'daily_digest',
                    user_id,
                    email,
                    f"📋 ODIN-AI 일일 다이제스트 - {count}건의 알림 요약",
                    status,
                    error,
                    json.dumps(
                        {'notification_count': count},
                        ensure_ascii=False,
                    ),
                ))
                conn.commit()
        except Exception as e:
            logger.error(f"발송 로그 기록 실패: {e}")

    def _generate_digest_html(self, user_name: str, notifications: List[Dict]) -> str:
        """다이제스트 HTML 이메일 생성"""
        # 타입별 분류
        bid_matches = [n for n in notifications if n.get('type') == 'bid_match']
        others = [n for n in notifications if n.get('type') != 'bid_match']

        # 입찰 매칭 알림 테이블 행 생성 (최대 20건)
        bid_rows = ""
        for n in bid_matches[:20]:
            meta = n.get('metadata', {})
            if isinstance(meta, str):
                try:
                    meta = json.loads(meta)
                except Exception:
                    meta = {}
            price = meta.get('price')
            price_text = f"₩{price:,}" if price else "미공개"
            org = meta.get('organization', '')
            title = (n['title'] or '')[:60]
            bid_rows += f"""
            <tr>
                <td style="padding:8px;border-bottom:1px solid #eee;">{title}</td>
                <td style="padding:8px;border-bottom:1px solid #eee;">{org}</td>
                <td style="padding:8px;border-bottom:1px solid #eee;text-align:right;">{price_text}</td>
            </tr>"""

        # 입찰 매칭 알림 섹션
        bid_section = ""
        if bid_matches:
            remaining = len(bid_matches) - 20
            remaining_note = (
                f'<p style="font-size:12px;color:#999;margin-top:8px;">'
                f'외 {remaining}건 더 있습니다. 전체 알림은 아래 버튼에서 확인하세요.</p>'
                if remaining > 0 else ""
            )
            bid_section = f"""
            <h3 style="color:#1976d2;margin-top:24px;">입찰 매칭 알림 ({len(bid_matches)}건)</h3>
            <table style="width:100%;border-collapse:collapse;">
                <tr style="background:#f5f5f5;">
                    <th style="padding:8px;text-align:left;">공고명</th>
                    <th style="padding:8px;text-align:left;">발주기관</th>
                    <th style="padding:8px;text-align:right;">예정가격</th>
                </tr>
                {bid_rows}
            </table>
            {remaining_note}"""

        # 기타 알림 섹션 (최대 10건)
        other_section = ""
        if others:
            other_items = "".join(
                f"<li style='padding:4px 0;'>{n['title']}</li>"
                for n in others[:10]
            )
            remaining_other = len(others) - 10
            other_remaining_note = (
                f'<li style="color:#999;">외 {remaining_other}건...</li>'
                if remaining_other > 0 else ""
            )
            other_section = f"""
            <h3 style="color:#555;margin-top:24px;">기타 알림 ({len(others)}건)</h3>
            <ul style="padding-left:20px;line-height:1.8;">
                {other_items}
                {other_remaining_note}
            </ul>"""

        total = len(notifications)

        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
        </head>
        <body style="font-family:'Apple SD Gothic Neo','Malgun Gothic',sans-serif;max-width:640px;margin:0 auto;padding:20px;background:#f5f5f5;">
            <div style="background:white;border-radius:8px;overflow:hidden;box-shadow:0 2px 8px rgba(0,0,0,0.1);">
                <!-- 헤더 -->
                <div style="background:linear-gradient(135deg,#1976d2 0%,#42a5f5 100%);color:white;padding:28px 30px;">
                    <h1 style="margin:0 0 6px 0;font-size:20px;">📋 ODIN-AI 일일 다이제스트</h1>
                    <p style="margin:0;opacity:0.9;font-size:14px;">{user_name}님의 최근 24시간 알림 요약</p>
                </div>

                <!-- 본문 -->
                <div style="padding:24px 30px;">
                    <p style="color:#333;font-size:15px;margin-top:0;">
                        지난 24시간 동안 <strong style="color:#1976d2;">{total}건</strong>의 새로운 알림이 있습니다.
                    </p>

                    {bid_section}
                    {other_section}

                    <!-- CTA 버튼 -->
                    <div style="margin-top:28px;text-align:center;">
                        <a href="{self.frontend_url}/notifications"
                           style="display:inline-block;background:#1976d2;color:white;padding:12px 32px;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold;">
                            모든 알림 확인하기
                        </a>
                    </div>
                </div>

                <!-- 푸터 -->
                <div style="padding:16px 30px;background:#f9f9f9;border-top:1px solid #eee;">
                    <p style="font-size:12px;color:#999;margin:0;text-align:center;line-height:1.8;">
                        이 이메일은 ODIN-AI 일일 다이제스트 설정에 의해 자동 발송되었습니다.<br>
                        알림 설정 변경:
                        <a href="{self.frontend_url}/notifications" style="color:#1976d2;text-decoration:none;">알림 설정 페이지</a>
                        &nbsp;|&nbsp;
                        <a href="{self.frontend_url}/dashboard" style="color:#1976d2;text-decoration:none;">대시보드</a>
                    </p>
                </div>
            </div>
        </body>
        </html>
        """


# 독립 실행 지원
if __name__ == "__main__":
    import logging

    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    )

    sender = DailyDigestSender()
    result = sender.run(hours=24)
    print(f"\n결과: {result}")
