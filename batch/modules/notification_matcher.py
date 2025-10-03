#!/usr/bin/env python
"""
알림 매칭 프로세서
배치 프로그램 완료 후 새로운 입찰공고와 사용자 알림 규칙을 매칭하여 알림 생성
"""

import json
import psycopg2
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from loguru import logger
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os


class NotificationMatcher:
    """알림 매칭 및 발송 처리 클래스"""

    def __init__(self, db_url: str):
        self.db_url = db_url
        self.processed_count = 0
        self.notification_count = 0
        self.email_sent_count = 0

    def process_new_bids(self, since_hours: int = 4) -> Dict[str, Any]:
        """
        최근 N시간 내 새로 수집된 입찰공고에 대해 알림 매칭 처리

        Args:
            since_hours: 몇 시간 전부터의 데이터를 처리할지 (기본 4시간)
        """
        logger.info(f"🔔 알림 매칭 시작 - 최근 {since_hours}시간 데이터 처리")

        try:
            # 1. 최근 새로 추가된 입찰공고 조회
            new_bids = self._get_new_bids(since_hours)
            logger.info(f"📊 처리 대상 신규 입찰공고: {len(new_bids)}개")

            if not new_bids:
                logger.info("💡 처리할 신규 입찰공고가 없습니다")
                return {"processed_bids": 0, "notifications_created": 0, "emails_sent": 0}

            # 2. 활성화된 알림 규칙 조회
            alert_rules = self._get_active_alert_rules()
            logger.info(f"📋 활성 알림 규칙: {len(alert_rules)}개")

            # 3. 각 입찰공고별로 매칭 규칙 찾기 및 알림 생성
            for bid in new_bids:
                matching_rules = self._find_matching_rules(bid, alert_rules)

                for rule in matching_rules:
                    # 알림 생성
                    notification_id = self._create_notification(rule, bid)

                    # 이메일 발송 (즉시 알림인 경우)
                    if rule['notification_timing'] == 'immediate':
                        self._send_email_notification(rule, bid, notification_id)

                    self.notification_count += 1

                self.processed_count += 1

            logger.info(f"✅ 알림 매칭 완료 - 처리: {self.processed_count}개, 알림: {self.notification_count}개, 이메일: {self.email_sent_count}개")

            return {
                "processed_bids": self.processed_count,
                "notifications_created": self.notification_count,
                "emails_sent": self.email_sent_count
            }

        except Exception as e:
            logger.error(f"❌ 알림 매칭 처리 실패: {e}")
            raise

    def _get_new_bids(self, since_hours: int) -> List[Dict[str, Any]]:
        """최근 N시간 내 새로 수집된 입찰공고 조회"""
        with psycopg2.connect(self.db_url) as conn:
            cursor = conn.cursor()

            cursor.execute("""
                SELECT
                    ba.bid_notice_no,
                    ba.title,
                    ba.organization_name,
                    ba.department_name,
                    ba.estimated_price,
                    ba.bid_start_date,
                    ba.bid_end_date,
                    ba.bid_method,
                    ba.contract_method,
                    ba.region_restriction,
                    ba.created_at,
                    -- 태그 정보 추가
                    COALESCE(
                        array_agg(bt.tag_name) FILTER (WHERE bt.tag_name IS NOT NULL),
                        '{}'::text[]
                    ) as tags
                FROM bid_announcements ba
                LEFT JOIN bid_tag_relations btr ON ba.bid_notice_no = btr.bid_notice_no
                LEFT JOIN bid_tags bt ON btr.tag_id = bt.id
                WHERE ba.created_at >= NOW() - INTERVAL '%s hours'
                    AND ba.bid_end_date > NOW()  -- 아직 마감되지 않은 공고만
                GROUP BY ba.bid_notice_no, ba.title, ba.organization_name,
                         ba.department_name, ba.estimated_price, ba.bid_start_date,
                         ba.bid_end_date, ba.bid_method, ba.contract_method,
                         ba.region_restriction, ba.created_at
                ORDER BY ba.created_at DESC
            """, (since_hours,))

            columns = [desc[0] for desc in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]

    def _get_active_alert_rules(self) -> List[Dict[str, Any]]:
        """활성화된 알림 규칙들 조회"""
        with psycopg2.connect(self.db_url) as conn:
            cursor = conn.cursor()

            cursor.execute("""
                SELECT
                    ar.id,
                    ar.user_id,
                    ar.rule_name,
                    ar.conditions,
                    ar.notification_channels,
                    ar.notification_timing,
                    ar.notification_time,
                    u.email,
                    u.full_name
                FROM alert_rules ar
                JOIN users u ON ar.user_id = u.id
                WHERE ar.is_active = true
                    AND u.is_active = true
                ORDER BY ar.created_at
            """)

            columns = [desc[0] for desc in cursor.description]
            rules = [dict(zip(columns, row)) for row in cursor.fetchall()]

            # JSON 컬럼 파싱
            for rule in rules:
                if isinstance(rule['conditions'], str):
                    rule['conditions'] = json.loads(rule['conditions'])
                if isinstance(rule['notification_channels'], str):
                    rule['notification_channels'] = json.loads(rule['notification_channels'])

            return rules

    def _find_matching_rules(self, bid: Dict[str, Any], alert_rules: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """특정 입찰공고와 매칭되는 알림 규칙들 찾기"""
        matching_rules = []

        for rule in alert_rules:
            if self._is_bid_matching_rule(bid, rule):
                matching_rules.append(rule)

        return matching_rules

    def _is_bid_matching_rule(self, bid: Dict[str, Any], rule: Dict[str, Any]) -> bool:
        """입찰공고가 알림 규칙과 매칭되는지 확인"""
        conditions = rule['conditions']

        # 1. 키워드 매칭 (제목, 기관명)
        if 'keywords' in conditions and conditions['keywords']:
            keywords_matched = False
            title_and_org = f"{bid['title']} {bid['organization_name']}".lower()

            for keyword in conditions['keywords']:
                if keyword.lower() in title_and_org:
                    keywords_matched = True
                    break

            if not keywords_matched:
                return False

        # 2. 가격 범위 매칭
        if bid['estimated_price']:
            if 'price_min' in conditions and conditions['price_min']:
                if bid['estimated_price'] < conditions['price_min']:
                    return False

            if 'price_max' in conditions and conditions['price_max']:
                if bid['estimated_price'] > conditions['price_max']:
                    return False

        # 3. 기관 매칭
        if 'organizations' in conditions and conditions['organizations']:
            if not any(org in bid['organization_name'] for org in conditions['organizations']):
                return False

        # 4. 카테고리/태그 매칭
        if 'categories' in conditions and conditions['categories']:
            bid_tags = bid.get('tags', [])
            if not any(cat in bid_tags for cat in conditions['categories']):
                return False

        # 5. 지역 매칭
        if 'regions' in conditions and conditions['regions']:
            if bid['region_restriction']:
                if not any(region in bid['region_restriction'] for region in conditions['regions']):
                    return False

        logger.debug(f"✅ 매칭 성공: 규칙 '{rule['rule_name']}' - 입찰 '{bid['title'][:50]}...'")
        return True

    def _create_notification(self, rule: Dict[str, Any], bid: Dict[str, Any]) -> int:
        """알림 생성 및 DB 저장"""
        with psycopg2.connect(self.db_url) as conn:
            cursor = conn.cursor()

            # 중복 알림 방지 체크
            cursor.execute("""
                SELECT id FROM notifications
                WHERE user_id = %s AND alert_rule_id = %s
                    AND metadata->>'bid_notice_no' = %s
            """, (rule['user_id'], rule['id'], bid['bid_notice_no']))

            if cursor.fetchone():
                logger.debug(f"⚠️ 중복 알림 스킵: 사용자 {rule['user_id']}, 입찰 {bid['bid_notice_no']}")
                return None

            # 알림 생성
            title = f"🎯 새로운 입찰 매칭: {bid['title'][:50]}..."
            message = self._generate_notification_message(rule, bid)

            cursor.execute("""
                INSERT INTO notifications (
                    user_id, alert_rule_id, title, message, type, status, priority,
                    metadata, created_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW())
                RETURNING id
            """, (
                rule['user_id'],
                rule['id'],
                title,
                message,
                'bid_match',
                'unread',
                'normal',
                json.dumps({
                    'bid_notice_no': bid['bid_notice_no'],
                    'organization': bid['organization_name'],
                    'price': bid['estimated_price'],
                    'deadline': bid['bid_end_date'].isoformat() if bid['bid_end_date'] else None,
                    'rule_name': rule['rule_name']
                })
            ))

            notification_id = cursor.fetchone()[0]

            # alert_matches 테이블에도 기록
            cursor.execute("""
                INSERT INTO alert_matches (
                    alert_rule_id, bid_notice_no, match_score, matched_at
                ) VALUES (%s, %s, %s, NOW())
            """, (rule['id'], bid['bid_notice_no'], 85))  # 기본 매칭 점수

            # alert_rules 통계 업데이트
            cursor.execute("""
                UPDATE alert_rules
                SET match_count = match_count + 1, last_matched_at = NOW()
                WHERE id = %s
            """, (rule['id'],))

            conn.commit()

            logger.debug(f"📝 알림 생성 완료: ID {notification_id}, 사용자 {rule['user_id']}")
            return notification_id

    def _generate_notification_message(self, rule: Dict[str, Any], bid: Dict[str, Any]) -> str:
        """알림 메시지 생성"""
        price_text = f"₩{bid['estimated_price']:,}" if bid['estimated_price'] else "미공개"
        deadline_text = bid['bid_end_date'].strftime('%Y-%m-%d') if bid['bid_end_date'] else "미정"

        return f"""
🏛️ 발주기관: {bid['organization_name']}
💰 예정가격: {price_text}
📅 마감일: {deadline_text}
📍 지역: {bid.get('region_restriction', '전국')}
🏷️ 태그: {', '.join(bid.get('tags', [])[:3])}

🔗 상세보기: /bids/{bid['bid_notice_no']}
        """.strip()

    def _send_email_notification(self, rule: Dict[str, Any], bid: Dict[str, Any], notification_id: int):
        """이메일 알림 발송"""
        if 'email' not in rule['notification_channels']:
            return

        try:
            smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
            smtp_port = int(os.getenv("SMTP_PORT", "587"))
            smtp_user = os.getenv("SMTP_USER", "")
            smtp_password = os.getenv("SMTP_PASSWORD", "")

            if not smtp_user or not smtp_password:
                logger.warning("⚠️ SMTP 설정이 없어 이메일 발송을 건너뜁니다")
                return

            # 이메일 내용 생성
            subject = f"🎯 ODIN-AI 알림: {bid['title'][:50]}..."
            html_content = self._generate_email_html(rule, bid)

            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = smtp_user
            msg['To'] = rule['email']

            html_part = MIMEText(html_content, 'html', 'utf-8')
            msg.attach(html_part)

            # 이메일 발송
            with smtplib.SMTP(smtp_host, smtp_port) as server:
                server.starttls()
                server.login(smtp_user, smtp_password)
                server.send_message(msg)

            # 발송 기록 업데이트
            with psycopg2.connect(self.db_url) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO notification_history (
                        user_id, notification_type, channel, subject, content, recipient, status, sent_at
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, NOW())
                """, (rule['user_id'], 'bid_match', 'email', subject, html_content[:500], rule['email'], 'sent'))
                conn.commit()

            self.email_sent_count += 1
            logger.info(f"📧 이메일 발송 완료: {rule['email']} - {bid['title'][:30]}...")

        except Exception as e:
            logger.error(f"❌ 이메일 발송 실패: {e}")

    def _generate_email_html(self, rule: Dict[str, Any], bid: Dict[str, Any]) -> str:
        """이메일 HTML 템플릿 생성"""
        price_text = f"₩{bid['estimated_price']:,}" if bid['estimated_price'] else "미공개"
        deadline_text = bid['bid_end_date'].strftime('%Y년 %m월 %d일') if bid['bid_end_date'] else "미정"

        return f"""
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                .container {{ max-width: 600px; margin: 0 auto; font-family: 'Malgun Gothic', sans-serif; }}
                .header {{ background: #1976d2; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; background: #f5f5f5; }}
                .bid-info {{ background: white; padding: 15px; margin: 10px 0; border-radius: 5px; }}
                .footer {{ text-align: center; padding: 10px; font-size: 12px; color: #666; }}
                .btn {{ display: inline-block; padding: 10px 20px; background: #1976d2; color: white; text-decoration: none; border-radius: 3px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h2>🎯 ODIN-AI 입찰 알림</h2>
                    <p>새로운 입찰공고가 매칭되었습니다!</p>
                </div>
                <div class="content">
                    <h3>{bid['title']}</h3>
                    <div class="bid-info">
                        <p><strong>🏛️ 발주기관:</strong> {bid['organization_name']}</p>
                        <p><strong>💰 예정가격:</strong> {price_text}</p>
                        <p><strong>📅 마감일:</strong> {deadline_text}</p>
                        <p><strong>📍 지역제한:</strong> {bid.get('region_restriction', '전국')}</p>
                        <p><strong>🔗 입찰방법:</strong> {bid.get('bid_method', '미정')}</p>
                        <p><strong>🏷️ 태그:</strong> {', '.join(bid.get('tags', [])[:5])}</p>
                    </div>
                    <p style="text-align: center;">
                        <a href="http://localhost:3000/bids/{bid['bid_notice_no']}" class="btn">
                            📋 상세보기
                        </a>
                    </p>
                    <p><strong>📋 매칭 규칙:</strong> {rule['rule_name']}</p>
                </div>
                <div class="footer">
                    <p>ODIN-AI 공공입찰 정보 분석 플랫폼</p>
                    <p>알림 설정을 변경하려면 <a href="http://localhost:3000/notifications">여기</a>를 클릭하세요.</p>
                </div>
            </div>
        </body>
        </html>
        """


if __name__ == "__main__":
    # 테스트 실행
    import os
    from dotenv import load_dotenv

    load_dotenv()
    db_url = os.getenv('DATABASE_URL', 'postgresql://blockmeta@localhost:5432/odin_db')

    matcher = NotificationMatcher(db_url)
    result = matcher.process_new_bids(since_hours=24)  # 최근 24시간
    print(f"알림 매칭 완료: {result}")