"""
대시보드 API 엔드포인트
사용자별 맞춤 대시보드 데이터 제공
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List

from backend.core.database import get_db
from backend.core.security import security_service
from backend.models.user_models import User, UserBidBookmark
from backend.models.bid_models import BidAnnouncement, BidDocument
from backend.services.analytics_service import AnalyticsService
from backend.schemas.dashboard_schemas import (
    DashboardOverview, BidStatistics, RecentActivity,
    UpcomingDeadlines, RecommendedBids, MarketTrends
)

router = APIRouter(prefix="/api/dashboard", tags=["대시보드"])


@router.get("/overview", response_model=DashboardOverview)
async def get_dashboard_overview(
    token: dict = Depends(security_service.verify_token),
    db: Session = Depends(get_db)
):
    """
    대시보드 개요

    - 오늘의 통계
    - 최근 활동
    - 알림 요약
    """
    user_id = int(token.get("sub"))

    try:
        analytics = AnalyticsService(db)

        # 오늘의 통계
        today = datetime.now().date()

        # 신규 입찰 공고 (24시간 내)
        new_bids = db.query(func.count(BidAnnouncement.id)).filter(
            BidAnnouncement.created_at >= datetime.now() - timedelta(days=1)
        ).scalar()

        # 마감 임박 (3일 이내)
        upcoming_deadlines = db.query(func.count(BidAnnouncement.id)).filter(
            and_(
                BidAnnouncement.closing_date >= datetime.now(),
                BidAnnouncement.closing_date <= datetime.now() + timedelta(days=3)
            )
        ).scalar()

        # 사용자 북마크 수
        bookmarks = db.query(func.count(UserBidBookmark.id)).filter(
            UserBidBookmark.user_id == user_id
        ).scalar()

        # 매칭된 입찰 (사용자 키워드 기반)
        user = db.query(User).filter(User.id == user_id).first()
        matched_bids = 0

        if user and hasattr(user, 'preferences') and user.preferences:
            keywords = user.preferences.interested_categories or []
            if keywords:
                matched_query = db.query(BidAnnouncement)
                for keyword in keywords:
                    matched_query = matched_query.filter(
                        or_(
                            BidAnnouncement.bid_notice_name.contains(keyword),
                            BidAnnouncement.organization_name.contains(keyword)
                        )
                    )
                matched_bids = matched_query.count()

        # 주간 트렌드
        week_ago = datetime.now() - timedelta(days=7)

        weekly_bids = db.query(func.count(BidAnnouncement.id)).filter(
            BidAnnouncement.created_at >= week_ago
        ).scalar()

        prev_week_bids = db.query(func.count(BidAnnouncement.id)).filter(
            and_(
                BidAnnouncement.created_at >= week_ago - timedelta(days=7),
                BidAnnouncement.created_at < week_ago
            )
        ).scalar()

        trend_percentage = 0
        if prev_week_bids > 0:
            trend_percentage = ((weekly_bids - prev_week_bids) / prev_week_bids) * 100

        return DashboardOverview(
            today_stats={
                "new_bids": new_bids,
                "upcoming_deadlines": upcoming_deadlines,
                "bookmarks": bookmarks,
                "matched_bids": matched_bids
            },
            weekly_trend={
                "total_bids": weekly_bids,
                "trend_percentage": round(trend_percentage, 1),
                "trend_direction": "up" if trend_percentage > 0 else "down"
            },
            last_updated=datetime.now()
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"대시보드 데이터 조회 실패: {str(e)}")


@router.get("/statistics", response_model=BidStatistics)
async def get_bid_statistics(
    period: str = Query("7d", description="통계 기간 (7d, 30d, 90d)"),
    token: dict = Depends(security_service.verify_token),
    db: Session = Depends(get_db)
):
    """
    입찰 통계

    - 기간별 입찰 통계
    - 분야별 분포
    - 금액대별 분포
    """
    user_id = int(token.get("sub"))

    try:
        # 기간 설정
        period_map = {
            "7d": 7,
            "30d": 30,
            "90d": 90
        }
        days = period_map.get(period, 7)
        start_date = datetime.now() - timedelta(days=days)

        analytics = AnalyticsService(db)

        # 일별 입찰 수
        daily_stats = analytics.get_daily_bid_count(start_date)

        # 분야별 분포
        category_distribution = analytics.get_category_distribution(start_date)

        # 금액대별 분포
        price_ranges = analytics.get_price_range_distribution(start_date)

        # 기관별 TOP 10
        top_organizations = analytics.get_top_organizations(start_date, limit=10)

        # 평균 경쟁률 (모의 데이터)
        avg_competition_rate = 5.2

        return BidStatistics(
            period=period,
            daily_stats=daily_stats,
            category_distribution=category_distribution,
            price_ranges=price_ranges,
            top_organizations=top_organizations,
            avg_competition_rate=avg_competition_rate
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"통계 조회 실패: {str(e)}")


@router.get("/upcoming-deadlines", response_model=List[UpcomingDeadlines])
async def get_upcoming_deadlines(
    days: int = Query(7, description="며칠 이내 마감"),
    limit: int = Query(10, description="최대 결과 수"),
    token: dict = Depends(security_service.verify_token),
    db: Session = Depends(get_db)
):
    """
    마감 임박 입찰

    - 지정 기간 내 마감되는 입찰
    - 사용자 관심 분야 우선 표시
    """
    user_id = int(token.get("sub"))

    try:
        deadline = datetime.now() + timedelta(days=days)

        # 마감 임박 입찰 조회
        bids = db.query(BidAnnouncement).filter(
            and_(
                BidAnnouncement.closing_date >= datetime.now(),
                BidAnnouncement.closing_date <= deadline
            )
        ).order_by(BidAnnouncement.closing_date.asc()).limit(limit).all()

        results = []
        for bid in bids:
            hours_remaining = (bid.closing_date - datetime.now()).total_seconds() / 3600

            results.append(UpcomingDeadlines(
                bid_id=bid.id,
                bid_notice_no=bid.bid_notice_no,
                title=bid.bid_notice_name,
                organization=bid.organization_name,
                closing_date=bid.closing_date,
                hours_remaining=int(hours_remaining),
                estimated_price=bid.bid_amount,
                is_bookmarked=db.query(UserBidBookmark).filter(
                    and_(
                        UserBidBookmark.user_id == user_id,
                        UserBidBookmark.bid_notice_no == bid.bid_notice_no
                    )
                ).first() is not None,
                urgency_level="critical" if hours_remaining < 24 else (
                    "high" if hours_remaining < 72 else "medium"
                )
            ))

        return results

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"마감 임박 입찰 조회 실패: {str(e)}")


@router.get("/recommended", response_model=List[RecommendedBids])
async def get_recommended_bids(
    limit: int = Query(5, description="추천 개수"),
    token: dict = Depends(security_service.verify_token),
    db: Session = Depends(get_db)
):
    """
    AI 추천 입찰

    - 사용자 선호도 기반 추천
    - 성공 확률 높은 입찰
    """
    user_id = int(token.get("sub"))

    try:
        # 사용자 선호도 가져오기
        user = db.query(User).filter(User.id == user_id).first()

        # 추천 쿼리 생성
        query = db.query(BidAnnouncement).filter(
            BidAnnouncement.closing_date >= datetime.now()
        )

        # 사용자 선호도가 있으면 필터링
        if user and hasattr(user, 'preferences') and user.preferences:
            if user.preferences.interested_categories:
                # 카테고리 필터링
                for category in user.preferences.interested_categories:
                    query = query.filter(
                        BidAnnouncement.bid_notice_name.contains(category)
                    )

            if user.preferences.budget_range_min:
                query = query.filter(
                    BidAnnouncement.bid_amount >= user.preferences.budget_range_min
                )

            if user.preferences.budget_range_max:
                query = query.filter(
                    BidAnnouncement.bid_amount <= user.preferences.budget_range_max
                )

        # 최신순으로 정렬
        bids = query.order_by(BidAnnouncement.announcement_date.desc()).limit(limit).all()

        results = []
        for bid in bids:
            # AI 점수 계산 (모의)
            ai_score = 75 + (hash(bid.bid_notice_no) % 20)  # 75-95 사이

            results.append(RecommendedBids(
                bid_id=bid.id,
                bid_notice_no=bid.bid_notice_no,
                title=bid.bid_notice_name,
                organization=bid.organization_name,
                closing_date=bid.closing_date,
                estimated_price=bid.bid_amount,
                ai_score=ai_score,
                success_probability=ai_score * 0.9,  # 성공 확률
                match_reasons=[
                    "사용자 관심 분야 일치",
                    "예산 범위 적합",
                    "과거 유사 입찰 성공 이력"
                ][:2],  # 2개만 표시
                is_bookmarked=db.query(UserBidBookmark).filter(
                    and_(
                        UserBidBookmark.user_id == user_id,
                        UserBidBookmark.bid_notice_no == bid.bid_notice_no
                    )
                ).first() is not None
            ))

        return results

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"추천 입찰 조회 실패: {str(e)}")


@router.get("/recent-activity", response_model=List[RecentActivity])
async def get_recent_activity(
    limit: int = Query(10, description="활동 개수"),
    token: dict = Depends(security_service.verify_token),
    db: Session = Depends(get_db)
):
    """
    최근 활동 내역

    - 최근 조회한 입찰
    - 북마크 활동
    - 검색 이력
    """
    user_id = int(token.get("sub"))

    try:
        activities = []

        # 최근 북마크
        bookmarks = db.query(UserBidBookmark).filter(
            UserBidBookmark.user_id == user_id
        ).order_by(UserBidBookmark.bookmark_date.desc()).limit(5).all()

        for bookmark in bookmarks:
            bid = db.query(BidAnnouncement).filter(
                BidAnnouncement.bid_notice_no == bookmark.bid_notice_no
            ).first()

            if bid:
                activities.append(RecentActivity(
                    activity_type="bookmark",
                    activity_time=bookmark.bookmark_date,
                    title=f"입찰 북마크: {bid.bid_notice_name[:30]}...",
                    description=bid.organization_name,
                    link=f"/bids/{bid.id}"
                ))

        # 최근 검색 (UserSearchHistory가 있다면)
        # ... 검색 이력 추가 ...

        # 시간순 정렬
        activities.sort(key=lambda x: x.activity_time, reverse=True)

        return activities[:limit]

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"최근 활동 조회 실패: {str(e)}")


@router.get("/market-trends", response_model=MarketTrends)
async def get_market_trends(
    token: dict = Depends(security_service.verify_token),
    db: Session = Depends(get_db)
):
    """
    시장 트렌드 분석

    - 업종별 동향
    - 주요 키워드
    - 시장 인사이트
    """
    try:
        analytics = AnalyticsService(db)

        # 최근 30일 데이터
        start_date = datetime.now() - timedelta(days=30)

        # 업종별 성장률
        industry_growth = analytics.get_industry_growth_rate(start_date)

        # 인기 키워드 (모의 데이터)
        trending_keywords = [
            {"keyword": "AI", "count": 245, "growth": 15.2},
            {"keyword": "클라우드", "count": 189, "growth": 8.7},
            {"keyword": "보안", "count": 156, "growth": 12.3},
            {"keyword": "빅데이터", "count": 134, "growth": -2.1},
            {"keyword": "IoT", "count": 98, "growth": 5.6}
        ]

        # 시장 인사이트
        insights = [
            {
                "type": "trend",
                "title": "IT 서비스 입찰 15% 증가",
                "description": "지난달 대비 IT 관련 입찰이 15% 증가했습니다.",
                "importance": "high"
            },
            {
                "type": "alert",
                "title": "건설 분야 경쟁률 상승",
                "description": "평균 경쟁률이 7:1로 전월 대비 2포인트 상승했습니다.",
                "importance": "medium"
            },
            {
                "type": "opportunity",
                "title": "신규 발주기관 증가",
                "description": "이번 달 신규 발주기관이 23개 추가되었습니다.",
                "importance": "high"
            }
        ]

        return MarketTrends(
            industry_growth=industry_growth,
            trending_keywords=trending_keywords,
            insights=insights,
            analysis_date=datetime.now()
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"시장 트렌드 조회 실패: {str(e)}")


@router.post("/bookmark/{bid_id}")
async def toggle_bookmark(
    bid_id: int,
    token: dict = Depends(security_service.verify_token),
    db: Session = Depends(get_db)
):
    """
    북마크 토글

    - 입찰 북마크 추가/제거
    """
    user_id = int(token.get("sub"))

    try:
        # 입찰 확인
        bid = db.query(BidAnnouncement).filter(BidAnnouncement.id == bid_id).first()
        if not bid:
            raise HTTPException(status_code=404, detail="입찰을 찾을 수 없습니다")

        # 기존 북마크 확인
        existing = db.query(UserBidBookmark).filter(
            and_(
                UserBidBookmark.user_id == user_id,
                UserBidBookmark.bid_notice_no == bid.bid_notice_no
            )
        ).first()

        if existing:
            # 북마크 제거
            db.delete(existing)
            db.commit()
            return {"message": "북마크가 제거되었습니다", "bookmarked": False}
        else:
            # 북마크 추가
            bookmark = UserBidBookmark(
                user_id=user_id,
                bid_notice_no=bid.bid_notice_no
            )
            db.add(bookmark)
            db.commit()
            return {"message": "북마크가 추가되었습니다", "bookmarked": True}

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"북마크 처리 실패: {str(e)}")