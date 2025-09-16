"""
이메일 알림 서비스
"""

import smtplib
import asyncio
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import logging
from jinja2 import Template

from backend.core.config import settings
from backend.models.database import get_db
from backend.models.user import User
from backend.models.subscription import Subscription
from backend.models.bid import Bid
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

logger = logging.getLogger(__name__)


class EmailService:
    """이메일 발송 서비스"""
    
    def __init__(self):
        """서비스 초기화"""
        self.smtp_server = settings.SMTP_SERVER
        self.smtp_port = settings.SMTP_PORT
        self.smtp_user = settings.SMTP_USERNAME
        self.smtp_password = settings.SMTP_PASSWORD
        self.from_email = f"noreply@{settings.PROJECT_NAME.lower()}.kr"
        
        # 이메일 템플릿
        self.bid_alert_template = """
        <html>
        <head>
            <style>
                body { font-family: 'Noto Sans KR', sans-serif; line-height: 1.6; }
                .container { max-width: 600px; margin: 0 auto; padding: 20px; }
                .header { background: #2563eb; color: white; padding: 20px; border-radius: 8px 8px 0 0; }
                .content { background: #f8f9fa; padding: 20px; border: 1px solid #dee2e6; }
                .bid-item { background: white; padding: 15px; margin: 10px 0; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
                .bid-title { font-size: 18px; font-weight: bold; color: #212529; margin-bottom: 10px; }
                .bid-info { color: #6c757d; margin: 5px 0; }
                .bid-deadline { color: #dc3545; font-weight: bold; }
                .bid-price { color: #28a745; font-weight: bold; }
                .btn { display: inline-block; padding: 10px 20px; background: #2563eb; color: white; text-decoration: none; border-radius: 5px; margin: 10px 5px; }
                .footer { text-align: center; padding: 20px; color: #6c757d; font-size: 12px; }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🔔 Odin-AI 입찰공고 알림</h1>
                    <p>{{ user_name }}님께 맞춤 입찰 정보를 전달해드립니다.</p>
                </div>
                
                <div class="content">
                    <h2>📋 오늘의 입찰공고 ({{ bid_count }}건)</h2>
                    
                    {% for bid in bids %}
                    <div class="bid-item">
                        <div class="bid-title">{{ bid.title }}</div>
                        <div class="bid-info">📍 기관: {{ bid.organization }}</div>
                        <div class="bid-info">📅 공고일: {{ bid.announcement_date }}</div>
                        <div class="bid-info bid-deadline">⏰ 마감일: {{ bid.deadline }}</div>
                        {% if bid.estimated_price %}
                        <div class="bid-info bid-price">💰 예정가격: {{ bid.estimated_price }}원</div>
                        {% endif %}
                        <div class="bid-info">🏷️ 분야: {{ bid.category }}</div>
                        
                        {% if bid.success_probability %}
                        <div class="bid-info">
                            🎯 예상 성공률: 
                            <span style="color: {% if bid.success_probability > 70 %}#28a745{% elif bid.success_probability > 40 %}#ffc107{% else %}#dc3545{% endif %}">
                                {{ bid.success_probability }}%
                            </span>
                        </div>
                        {% endif %}
                        
                        <a href="{{ base_url }}/bids/{{ bid.id }}" class="btn">상세보기</a>
                    </div>
                    {% endfor %}
                    
                    <div style="text-align: center; margin-top: 30px;">
                        <a href="{{ base_url }}/dashboard" class="btn">대시보드에서 더 보기</a>
                    </div>
                </div>
                
                <div class="footer">
                    <p>이 이메일은 Odin-AI 입찰공고 알림 서비스에서 발송되었습니다.</p>
                    <p>알림 설정을 변경하시려면 <a href="{{ base_url }}/settings">여기</a>를 클릭하세요.</p>
                    <p>© 2025 Odin-AI. All rights reserved.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        self.daily_summary_template = """
        <html>
        <head>
            <style>
                body { font-family: 'Noto Sans KR', sans-serif; line-height: 1.6; }
                .container { max-width: 600px; margin: 0 auto; padding: 20px; }
                .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; border-radius: 8px 8px 0 0; }
                .stats { display: flex; justify-content: space-around; padding: 20px; background: white; }
                .stat-item { text-align: center; }
                .stat-number { font-size: 32px; font-weight: bold; color: #2563eb; }
                .stat-label { color: #6c757d; font-size: 14px; }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>📊 일일 입찰 요약 리포트</h1>
                    <p>{{ date }} 기준</p>
                </div>
                
                <div class="stats">
                    <div class="stat-item">
                        <div class="stat-number">{{ total_bids }}</div>
                        <div class="stat-label">전체 공고</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-number">{{ new_bids }}</div>
                        <div class="stat-label">신규 공고</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-number">{{ deadline_soon }}</div>
                        <div class="stat-label">마감 임박</div>
                    </div>
                </div>
                
                <div class="content">
                    <h3>🔥 주요 키워드</h3>
                    <p>{{ keywords }}</p>
                    
                    <h3>💡 추천 입찰</h3>
                    {% for bid in recommended_bids %}
                    <div style="padding: 10px; margin: 10px 0; background: #f8f9fa; border-left: 4px solid #2563eb;">
                        <strong>{{ bid.title }}</strong><br>
                        <small>{{ bid.organization }} | 마감: {{ bid.deadline }}</small>
                    </div>
                    {% endfor %}
                </div>
            </div>
        </body>
        </html>
        """
    
    async def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None
    ) -> bool:
        """이메일 발송"""
        try:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.from_email
            msg['To'] = to_email
            
            # 텍스트 버전 추가
            if text_content:
                part1 = MIMEText(text_content, 'plain')
                msg.attach(part1)
            
            # HTML 버전 추가
            part2 = MIMEText(html_content, 'html')
            msg.attach(part2)
            
            # SMTP 연결 및 발송
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg)
            
            logger.info(f"Email sent successfully to {to_email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {str(e)}")
            return False
    
    async def send_bid_alerts(
        self,
        user_id: int,
        bids: List[Dict],
        db: Session
    ) -> bool:
        """입찰 알림 이메일 발송"""
        try:
            # 사용자 정보 조회
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                logger.error(f"User not found: {user_id}")
                return False
            
            # 이메일 템플릿 렌더링
            template = Template(self.bid_alert_template)
            html_content = template.render(
                user_name=user.name,
                bid_count=len(bids),
                bids=bids,
                base_url=f"http://localhost:8000"
            )
            
            # 이메일 발송
            subject = f"[Odin-AI] {len(bids)}건의 새로운 입찰공고가 있습니다"
            return await self.send_email(
                to_email=user.email,
                subject=subject,
                html_content=html_content
            )
            
        except Exception as e:
            logger.error(f"Failed to send bid alerts: {str(e)}")
            return False
    
    async def send_daily_summary(
        self,
        user_id: int,
        summary_data: Dict,
        db: Session
    ) -> bool:
        """일일 요약 이메일 발송"""
        try:
            # 사용자 정보 조회
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                logger.error(f"User not found: {user_id}")
                return False
            
            # 이메일 템플릿 렌더링
            template = Template(self.daily_summary_template)
            html_content = template.render(
                date=datetime.now().strftime('%Y년 %m월 %d일'),
                **summary_data
            )
            
            # 이메일 발송
            subject = f"[Odin-AI] {datetime.now().strftime('%m월 %d일')} 입찰 요약 리포트"
            return await self.send_email(
                to_email=user.email,
                subject=subject,
                html_content=html_content
            )
            
        except Exception as e:
            logger.error(f"Failed to send daily summary: {str(e)}")
            return False
    
    async def process_scheduled_emails(self, db: Session):
        """예약된 이메일 처리 (Celery 태스크에서 호출)"""
        try:
            current_hour = datetime.now().hour
            
            # 현재 시간에 이메일 받기로 설정한 사용자 조회
            subscriptions = db.query(Subscription).filter(
                and_(
                    Subscription.email_enabled == True,
                    Subscription.email_time == current_hour
                )
            ).all()
            
            for subscription in subscriptions:
                # 사용자의 키워드에 맞는 입찰 조회
                keywords = subscription.keywords.split(',') if subscription.keywords else []
                
                query = db.query(Bid)
                if keywords:
                    keyword_filters = []
                    for keyword in keywords:
                        keyword_filters.append(
                            or_(
                                Bid.title.contains(keyword.strip()),
                                Bid.description.contains(keyword.strip())
                            )
                        )
                    query = query.filter(or_(*keyword_filters))
                
                # 최근 24시간 내 공고만
                yesterday = datetime.now() - timedelta(days=1)
                query = query.filter(Bid.created_at >= yesterday)
                
                bids = query.all()
                
                if bids:
                    # 입찰 데이터 변환
                    bid_data = []
                    for bid in bids:
                        bid_data.append({
                            'id': bid.id,
                            'title': bid.bid_notice_nm,
                            'organization': bid.demand_instt_nm,
                            'announcement_date': bid.bid_notice_dt.strftime('%Y-%m-%d'),
                            'deadline': bid.bid_clse_dt.strftime('%Y-%m-%d %H:%M'),
                            'estimated_price': f"{bid.presmpt_price:,}" if bid.presmpt_price else None,
                            'category': bid.cntrct_cncls_mtd_nm,
                            'success_probability': None  # AI 분석 결과 추가 예정
                        })
                    
                    # 이메일 발송
                    await self.send_bid_alerts(
                        user_id=subscription.user_id,
                        bids=bid_data,
                        db=db
                    )
                    
                    logger.info(f"Sent {len(bids)} bid alerts to user {subscription.user_id}")
            
            logger.info(f"Processed {len(subscriptions)} email subscriptions")
            
        except Exception as e:
            logger.error(f"Failed to process scheduled emails: {str(e)}")


# 싱글톤 인스턴스
email_service = EmailService()