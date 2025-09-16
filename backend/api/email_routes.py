"""
이메일 알림 API 엔드포인트
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from backend.services.email_service import email_service
from backend.models.database import get_db
from backend.models.user import User
from backend.models.subscription import Subscription
from backend.models.bid import Bid
from sqlalchemy import and_, or_

router = APIRouter(prefix="/api/email", tags=["이메일"])


@router.post("/send-test")
async def send_test_email(
    email: str,
    background_tasks: BackgroundTasks
):
    """
    테스트 이메일 발송
    """
    try:
        # 테스트 이메일 내용
        html_content = """
        <html>
        <body style="font-family: 'Noto Sans KR', sans-serif;">
            <h1>Odin-AI 테스트 이메일</h1>
            <p>이 이메일은 Odin-AI 이메일 서비스 테스트를 위해 발송되었습니다.</p>
            <p>현재 시간: {}</p>
        </body>
        </html>
        """.format(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        
        # 비동기로 이메일 발송
        background_tasks.add_task(
            email_service.send_email,
            to_email=email,
            subject="[Odin-AI] 테스트 이메일",
            html_content=html_content
        )
        
        return {
            "message": f"테스트 이메일이 {email}로 발송 예약되었습니다"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"이메일 발송 실패: {str(e)}")


@router.post("/send-bid-alerts/{user_id}")
async def send_bid_alerts(
    user_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    특정 사용자에게 입찰 알림 발송
    """
    try:
        # 사용자 확인
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다")
        
        # 사용자의 구독 정보 확인
        subscription = db.query(Subscription).filter(
            Subscription.user_id == user_id
        ).first()
        
        if not subscription or not subscription.email_enabled:
            raise HTTPException(status_code=400, detail="이메일 알림이 비활성화되어 있습니다")
        
        # 키워드에 맞는 최신 입찰 조회
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
        
        # 최근 24시간 내 공고
        yesterday = datetime.now() - timedelta(days=1)
        query = query.filter(Bid.created_at >= yesterday)
        query = query.limit(10)  # 최대 10건
        
        bids = query.all()
        
        if not bids:
            return {
                "message": "발송할 입찰 공고가 없습니다"
            }
        
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
                'category': bid.cntrct_cncls_mtd_nm
            })
        
        # 비동기로 이메일 발송
        background_tasks.add_task(
            email_service.send_bid_alerts,
            user_id=user_id,
            bids=bid_data,
            db=db
        )
        
        return {
            "message": f"{len(bids)}건의 입찰 알림이 발송 예약되었습니다",
            "bid_count": len(bids)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"알림 발송 실패: {str(e)}")


@router.post("/send-daily-summary")
async def send_daily_summary(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    모든 구독자에게 일일 요약 발송
    """
    try:
        # 이메일 알림을 활성화한 모든 구독자 조회
        subscriptions = db.query(Subscription).filter(
            Subscription.email_enabled == True
        ).all()
        
        sent_count = 0
        
        for subscription in subscriptions:
            # 각 사용자별 요약 데이터 준비
            today = datetime.now().date()
            
            # 오늘의 입찰 통계
            total_bids = db.query(Bid).filter(
                Bid.bid_notice_dt >= today
            ).count()
            
            new_bids = db.query(Bid).filter(
                and_(
                    Bid.created_at >= datetime.combine(today, datetime.min.time()),
                    Bid.created_at <= datetime.combine(today, datetime.max.time())
                )
            ).count()
            
            # 3일 이내 마감 임박
            deadline_soon = db.query(Bid).filter(
                and_(
                    Bid.bid_clse_dt >= datetime.now(),
                    Bid.bid_clse_dt <= datetime.now() + timedelta(days=3)
                )
            ).count()
            
            # 추천 입찰 (TOP 3)
            recommended = db.query(Bid).filter(
                Bid.bid_clse_dt >= datetime.now()
            ).order_by(Bid.presmpt_price.desc()).limit(3).all()
            
            recommended_data = []
            for bid in recommended:
                recommended_data.append({
                    'title': bid.bid_notice_nm,
                    'organization': bid.demand_instt_nm,
                    'deadline': bid.bid_clse_dt.strftime('%Y-%m-%d')
                })
            
            summary_data = {
                'total_bids': total_bids,
                'new_bids': new_bids,
                'deadline_soon': deadline_soon,
                'keywords': subscription.keywords or '설정된 키워드 없음',
                'recommended_bids': recommended_data
            }
            
            # 비동기로 각 사용자에게 발송
            background_tasks.add_task(
                email_service.send_daily_summary,
                user_id=subscription.user_id,
                summary_data=summary_data,
                db=db
            )
            
            sent_count += 1
        
        return {
            "message": f"{sent_count}명에게 일일 요약이 발송 예약되었습니다",
            "sent_count": sent_count
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"요약 발송 실패: {str(e)}")


@router.get("/subscription/{user_id}")
async def get_email_subscription(
    user_id: int,
    db: Session = Depends(get_db)
):
    """
    사용자의 이메일 구독 설정 조회
    """
    try:
        subscription = db.query(Subscription).filter(
            Subscription.user_id == user_id
        ).first()
        
        if not subscription:
            return {
                "email_enabled": False,
                "email_time": None,
                "keywords": None
            }
        
        return {
            "email_enabled": subscription.email_enabled,
            "email_time": subscription.email_time,
            "keywords": subscription.keywords
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"구독 정보 조회 실패: {str(e)}")


@router.put("/subscription/{user_id}")
async def update_email_subscription(
    user_id: int,
    email_enabled: bool,
    email_time: Optional[int] = 9,  # 기본 오전 9시
    keywords: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    사용자의 이메일 구독 설정 업데이트
    """
    try:
        # 사용자 확인
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다")
        
        # 구독 정보 조회 또는 생성
        subscription = db.query(Subscription).filter(
            Subscription.user_id == user_id
        ).first()
        
        if not subscription:
            subscription = Subscription(
                user_id=user_id,
                email_enabled=email_enabled,
                email_time=email_time,
                keywords=keywords
            )
            db.add(subscription)
        else:
            subscription.email_enabled = email_enabled
            subscription.email_time = email_time
            subscription.keywords = keywords
        
        db.commit()
        
        return {
            "message": "구독 설정이 업데이트되었습니다",
            "subscription": {
                "email_enabled": subscription.email_enabled,
                "email_time": subscription.email_time,
                "keywords": subscription.keywords
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"구독 설정 업데이트 실패: {str(e)}")