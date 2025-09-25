"""
알림 발송 시스템
이메일, 웹 푸시, SMS 등 다양한 채널로 알림 발송
"""

import os
import smtplib
import json
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from loguru import logger
from jinja2 import Template


class AlertSender:
    """알림 발송 시스템"""

    def __init__(self, db_url: str):
        """초기화

        Args:
            db_url: 데이터베이스 URL
        """
        self.db_url = db_url
        self.engine = create_engine(db_url)
        Session = sessionmaker(bind=self.engine)
        self.session = Session()

        # 이메일 설정
        self.smtp_host = os.getenv('EMAIL_HOST', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('EMAIL_PORT', 587))
        self.smtp_username = os.getenv('EMAIL_USERNAME')
        self.smtp_password = os.getenv('EMAIL_PASSWORD')
        self.email_from = os.getenv('EMAIL_FROM')
        self.email_enabled = os.getenv('EMAIL_ENABLED', 'false').lower() == 'true'

    def queue_alerts(self, matches: List[Dict]) -> List[int]:
        """알림 큐에 추가

        Args:
            matches: 매칭 결과 리스트

        Returns:
            list: 생성된 큐 ID 리스트
        """
        queue_ids = []

        try:
            for match in matches:
                # 사용자 정보 조회
                user = self._get_user_info(match['user_id'])
                if not user:
                    continue

                # 각 채널별로 큐 생성
                for channel in match.get('channels', ['email']):
                    queue_id = self._create_queue_entry(
                        user_id=match['user_id'],
                        channel=channel,
                        match=match,
                        user=user
                    )
                    if queue_id:
                        queue_ids.append(queue_id)

            logger.info(f"📝 {len(queue_ids)}개 알림 큐 생성")
            return queue_ids

        except Exception as e:
            logger.error(f"큐 생성 실패: {e}")
            return []

    def _create_queue_entry(self, user_id: int, channel: str, match: Dict, user: Dict) -> Optional[int]:
        """알림 큐 항목 생성 (중복 체크 포함)

        Args:
            user_id: 사용자 ID
            channel: 알림 채널
            match: 매칭 정보
            user: 사용자 정보

        Returns:
            int: 큐 ID
        """
        try:
            # 중복 알림 체크 (같은 날, 같은 사용자, 같은 공고)
            duplicate_check = """
            SELECT id, status, created_at
            FROM alert_queue
            WHERE user_id = :user_id
            AND bid_id = :bid_id
            AND channel = :channel
            AND DATE(created_at) = :today
            """

            existing = self.session.execute(text(duplicate_check), {
                'user_id': user_id,
                'bid_id': match.get('bid_id'),
                'channel': channel,
                'today': datetime.now().date()
            }).first()

            if existing:
                logger.warning(f"⚠️ 중복 알림 스킵: user={user_id}, bid={match.get('bid_id')}, channel={channel}")
                logger.warning(f"   기존 알림: id={existing[0]}, status={existing[1]}, created={existing[2]}")
                return None
            # 알림 내용 생성
            content = self._generate_alert_content(match, user, channel)

            # 수신자 정보
            recipient = None
            if channel == 'email':
                recipient = user.get('email')
            elif channel == 'sms':
                recipient = user.get('phone')

            if not recipient:
                logger.warning(f"수신자 정보 없음: user_id={user_id}, channel={channel}")
                return None

            # 큐 저장
            insert_query = """
            INSERT INTO alert_queue (
                user_id, bid_id, rule_id, match_id, channel, recipient,
                subject, content, priority, status,
                created_at, scheduled_at, queue_date
            ) VALUES (
                :user_id, :bid_id, :rule_id, :match_id, :channel, :recipient,
                :subject, :content, :priority, 'pending',
                :created_at, :scheduled_at, :queue_date
            ) RETURNING id
            """

            result = self.session.execute(text(insert_query), {
                'user_id': user_id,
                'bid_id': match.get('bid_id'),
                'rule_id': match.get('rule_id'),
                'match_id': match.get('match_id'),
                'channel': channel,
                'recipient': recipient,
                'subject': f"[ODIN-AI] 새로운 입찰 공고: {match['bid_title'][:50]}",
                'content': content,
                'priority': self._calculate_priority(match),
                'created_at': datetime.now(),
                'scheduled_at': datetime.now(),  # 즉시 발송
                'queue_date': datetime.now().date()  # 큐 생성 날짜
            })

            queue_id = result.scalar()
            self.session.commit()

            return queue_id

        except Exception as e:
            logger.error(f"큐 항목 생성 실패: {e}")
            self.session.rollback()
            return None

    def process_queue(self, limit: int = 100) -> int:
        """알림 큐 처리

        Args:
            limit: 처리할 최대 개수

        Returns:
            int: 발송된 알림 수
        """
        sent_count = 0

        try:
            # 대기 중인 알림 조회
            query = """
            SELECT
                id, user_id, channel, recipient,
                subject, content, priority
            FROM alert_queue
            WHERE status = 'pending'
            AND scheduled_at <= :now
            ORDER BY priority DESC, created_at
            LIMIT :limit
            """

            result = self.session.execute(text(query), {
                'now': datetime.now(),
                'limit': limit
            })

            for row in result:
                queue_id = row[0]
                channel = row[2]
                recipient = row[3]
                subject = row[4]
                content = row[5]

                # 채널별 발송
                success = False
                if channel == 'email':
                    success = self._send_email(recipient, subject, content)
                elif channel == 'sms':
                    success = self._send_sms(recipient, content)
                elif channel == 'push':
                    success = self._send_push(row[1], subject, content)

                # 발송 상태 업데이트
                if success:
                    self._update_queue_status(queue_id, 'sent')
                    sent_count += 1
                else:
                    self._update_queue_status(queue_id, 'failed')

            logger.info(f"📤 {sent_count}개 알림 발송 완료")
            return sent_count

        except Exception as e:
            logger.error(f"큐 처리 실패: {e}")
            return sent_count

    def _send_email(self, to_email: str, subject: str, content: str) -> bool:
        """이메일 발송

        Args:
            to_email: 수신자 이메일
            subject: 제목
            content: 내용

        Returns:
            bool: 성공 여부
        """
        if not self.email_enabled:
            logger.debug(f"이메일 비활성화 (수신: {to_email})")
            return True  # 개발 환경에서는 성공으로 처리

        if not all([self.smtp_username, self.smtp_password, self.email_from]):
            logger.warning("이메일 설정 누락")
            return False

        try:
            # 이메일 메시지 생성
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.email_from
            msg['To'] = to_email

            # HTML 파트 추가
            html_part = MIMEText(content, 'html', 'utf-8')
            msg.attach(html_part)

            # SMTP 서버 연결 및 발송
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_username, self.smtp_password)
                server.send_message(msg)

            logger.debug(f"✉️ 이메일 발송 성공: {to_email}")
            return True

        except Exception as e:
            logger.error(f"이메일 발송 실패: {e}")
            return False

    def _send_sms(self, phone: str, content: str) -> bool:
        """SMS 발송

        Args:
            phone: 수신자 전화번호
            content: 내용

        Returns:
            bool: 성공 여부
        """
        # SMS API 연동 (예: Twilio, 알리고 등)
        logger.debug(f"📱 SMS 발송 (미구현): {phone}")
        return False  # 아직 미구현

    def _send_push(self, user_id: int, title: str, content: str) -> bool:
        """웹 푸시 알림 발송

        Args:
            user_id: 사용자 ID
            title: 제목
            content: 내용

        Returns:
            bool: 성공 여부
        """
        # 웹 푸시 API 연동
        logger.debug(f"🔔 푸시 알림 (미구현): user_id={user_id}")
        return False  # 아직 미구현

    def _generate_alert_content(self, match: Dict, user: Dict, channel: str) -> str:
        """알림 내용 생성

        Args:
            match: 매칭 정보
            user: 사용자 정보
            channel: 알림 채널

        Returns:
            str: 생성된 내용
        """
        if channel == 'email':
            return self._generate_email_content(match, user)
        elif channel == 'sms':
            return self._generate_sms_content(match, user)
        else:
            return self._generate_default_content(match, user)

    def _generate_email_content(self, match: Dict, user: Dict) -> str:
        """이메일 내용 생성"""
        template = """
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body { font-family: Arial, sans-serif; line-height: 1.6; }
                .container { max-width: 600px; margin: 0 auto; padding: 20px; }
                .header { background: #007bff; color: white; padding: 20px; text-align: center; }
                .content { padding: 20px; background: #f8f9fa; }
                .bid-info { background: white; padding: 15px; margin: 10px 0; border-radius: 5px; }
                .label { font-weight: bold; color: #495057; }
                .button { display: inline-block; padding: 10px 20px; background: #007bff; color: white; text-decoration: none; border-radius: 5px; margin: 10px 0; }
                .footer { text-align: center; padding: 20px; color: #6c757d; font-size: 12px; }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h2>🔔 새로운 입찰 공고 알림</h2>
                </div>
                <div class="content">
                    <p>안녕하세요, {{ user_name }}님!</p>
                    <p>설정하신 알림 규칙 <strong>"{{ rule_name }}"</strong>에 매칭되는 새로운 입찰 공고가 등록되었습니다.</p>

                    <div class="bid-info">
                        <h3>📋 공고 정보</h3>
                        <p><span class="label">공고명:</span> {{ bid_title }}</p>
                        <p><span class="label">공고번호:</span> {{ bid_id }}</p>
                        <p><span class="label">매칭 점수:</span> {{ match_score }}%</p>
                        <p><span class="label">알림 시간:</span> {{ matched_at }}</p>
                    </div>

                    <div style="text-align: center;">
                        <a href="{{ detail_url }}" class="button">상세 보기</a>
                    </div>
                </div>
                <div class="footer">
                    <p>본 메일은 ODIN-AI 알림 서비스에서 발송되었습니다.</p>
                    <p>알림 설정을 변경하시려면 <a href="{{ settings_url }}">여기</a>를 클릭하세요.</p>
                </div>
            </div>
        </body>
        </html>
        """

        t = Template(template)
        return t.render(
            user_name=user.get('name', '사용자'),
            rule_name=match.get('rule_name', '알림 규칙'),
            bid_title=match.get('bid_title', ''),
            bid_id=match.get('bid_id', ''),
            match_score=int(match.get('match_score', 0) * 100),
            matched_at=match.get('matched_at', datetime.now()).strftime('%Y-%m-%d %H:%M'),
            detail_url=f"https://odin-ai.com/bids/{match.get('bid_id')}",
            settings_url="https://odin-ai.com/settings/alerts"
        )

    def _generate_sms_content(self, match: Dict, user: Dict) -> str:
        """SMS 내용 생성"""
        return f"""[ODIN-AI]
새 입찰공고: {match.get('bid_title', '')[:30]}...
매칭점수: {int(match.get('match_score', 0) * 100)}%
상세: odin.ai/{match.get('bid_id', '')[:8]}"""

    def _generate_default_content(self, match: Dict, user: Dict) -> str:
        """기본 내용 생성"""
        return f"""새로운 입찰 공고 알림
공고명: {match.get('bid_title', '')}
공고번호: {match.get('bid_id', '')}
매칭 점수: {int(match.get('match_score', 0) * 100)}%"""

    def _get_user_info(self, user_id: int) -> Optional[Dict]:
        """사용자 정보 조회"""
        query = """
        SELECT id, email, name, phone
        FROM users
        WHERE id = :user_id
        """

        result = self.session.execute(text(query), {'user_id': user_id})
        row = result.first()

        if row:
            return {
                'id': row[0],
                'email': row[1],
                'name': row[2],
                'phone': row[3]
            }
        return None

    def _calculate_priority(self, match: Dict) -> int:
        """알림 우선순위 계산"""
        score = match.get('match_score', 0)
        if score > 0.8:
            return 3  # 높음
        elif score > 0.5:
            return 2  # 중간
        else:
            return 1  # 낮음

    def _update_queue_status(self, queue_id: int, status: str):
        """큐 상태 업데이트"""
        update_query = """
        UPDATE alert_queue
        SET status = :status, sent_at = :sent_at
        WHERE id = :queue_id
        """

        self.session.execute(text(update_query), {
            'status': status,
            'sent_at': datetime.now() if status == 'sent' else None,
            'queue_id': queue_id
        })
        self.session.commit()

    def send_daily_digest(self) -> int:
        """일일 다이제스트 발송"""
        # TODO: 구현 필요
        logger.info("일일 다이제스트 발송 (미구현)")
        return 0

    def send_weekly_report(self) -> int:
        """주간 리포트 발송"""
        # TODO: 구현 필요
        logger.info("주간 리포트 발송 (미구현)")
        return 0