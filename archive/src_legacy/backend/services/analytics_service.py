"""
분석 및 통계 서비스
대시보드와 리포트를 위한 데이터 분석 서비스
"""

from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta, date
from sqlalchemy import func, and_, or_, case, extract
from sqlalchemy.orm import Session
from collections import defaultdict
import logging

from backend.models.bid_models import BidAnnouncement, BidDocument
from backend.models.user_models import User, UserBidBookmark

logger = logging.getLogger(__name__)


class AnalyticsService:
    """분석 및 통계 서비스"""

    def __init__(self, db: Session):
        """서비스 초기화"""
        self.db = db

    def get_daily_bid_count(self, start_date: datetime, end_date: Optional[datetime] = None) -> List[Dict]:
        """
        일별 입찰 공고 수 집계
        """
        if not end_date:
            end_date = datetime.now()

        try:
            # 일별 집계 쿼리
            results = self.db.query(
                func.date(BidAnnouncement.announcement_date).label('date'),
                func.count(BidAnnouncement.id).label('count')
            ).filter(
                and_(
                    BidAnnouncement.announcement_date >= start_date,
                    BidAnnouncement.announcement_date <= end_date
                )
            ).group_by(
                func.date(BidAnnouncement.announcement_date)
            ).order_by(
                func.date(BidAnnouncement.announcement_date)
            ).all()

            # 결과 포맷팅
            daily_stats = []
            for row in results:
                daily_stats.append({
                    "date": row.date.strftime("%Y-%m-%d") if row.date else None,
                    "count": row.count
                })

            # 빈 날짜 채우기
            current_date = start_date.date()
            end = end_date.date()
            date_dict = {stat["date"]: stat["count"] for stat in daily_stats}

            complete_stats = []
            while current_date <= end:
                date_str = current_date.strftime("%Y-%m-%d")
                complete_stats.append({
                    "date": date_str,
                    "count": date_dict.get(date_str, 0)
                })
                current_date += timedelta(days=1)

            return complete_stats

        except Exception as e:
            logger.error(f"일별 입찰 수 집계 실패: {e}")
            return []

    def get_category_distribution(self, start_date: datetime) -> List[Dict]:
        """
        카테고리별 입찰 분포
        """
        try:
            # 카테고리별 집계
            results = self.db.query(
                BidAnnouncement.industry_type,
                func.count(BidAnnouncement.id).label('count')
            ).filter(
                BidAnnouncement.announcement_date >= start_date
            ).group_by(
                BidAnnouncement.industry_type
            ).order_by(
                func.count(BidAnnouncement.id).desc()
            ).limit(10).all()

            # 결과 포맷팅
            categories = []
            total_count = sum(row.count for row in results)

            for row in results:
                category = row.industry_type or "기타"
                percentage = (row.count / total_count * 100) if total_count > 0 else 0

                categories.append({
                    "category": category,
                    "count": row.count,
                    "percentage": round(percentage, 1)
                })

            return categories

        except Exception as e:
            logger.error(f"카테고리별 분포 집계 실패: {e}")
            return []

    def get_price_range_distribution(self, start_date: datetime) -> Dict[str, int]:
        """
        금액대별 입찰 분포
        """
        try:
            # 금액대별 집계
            price_ranges = {
                "1억 미만": 0,
                "1억-10억": 0,
                "10억-50억": 0,
                "50억-100억": 0,
                "100억 이상": 0
            }

            # 각 범위별 카운트
            results = self.db.query(BidAnnouncement).filter(
                and_(
                    BidAnnouncement.announcement_date >= start_date,
                    BidAnnouncement.bid_amount.isnot(None)
                )
            ).all()

            for bid in results:
                amount = bid.bid_amount
                if amount < 100000000:  # 1억
                    price_ranges["1억 미만"] += 1
                elif amount < 1000000000:  # 10억
                    price_ranges["1억-10억"] += 1
                elif amount < 5000000000:  # 50억
                    price_ranges["10억-50억"] += 1
                elif amount < 10000000000:  # 100억
                    price_ranges["50억-100억"] += 1
                else:
                    price_ranges["100억 이상"] += 1

            return price_ranges

        except Exception as e:
            logger.error(f"금액대별 분포 집계 실패: {e}")
            return {}

    def get_top_organizations(self, start_date: datetime, limit: int = 10) -> List[Dict]:
        """
        상위 발주기관
        """
        try:
            results = self.db.query(
                BidAnnouncement.organization_name,
                func.count(BidAnnouncement.id).label('count'),
                func.sum(BidAnnouncement.bid_amount).label('total_amount')
            ).filter(
                BidAnnouncement.announcement_date >= start_date
            ).group_by(
                BidAnnouncement.organization_name
            ).order_by(
                func.count(BidAnnouncement.id).desc()
            ).limit(limit).all()

            organizations = []
            for row in results:
                organizations.append({
                    "name": row.organization_name,
                    "count": row.count,
                    "total_amount": row.total_amount or 0
                })

            return organizations

        except Exception as e:
            logger.error(f"상위 발주기관 집계 실패: {e}")
            return []

    def get_industry_growth_rate(self, start_date: datetime) -> List[Dict]:
        """
        업종별 성장률 계산
        """
        try:
            # 현재 기간 데이터
            current_period = self.db.query(
                BidAnnouncement.industry_type,
                func.count(BidAnnouncement.id).label('count')
            ).filter(
                BidAnnouncement.announcement_date >= start_date
            ).group_by(
                BidAnnouncement.industry_type
            ).all()

            # 이전 기간 데이터
            period_days = (datetime.now() - start_date).days
            prev_start = start_date - timedelta(days=period_days)
            prev_end = start_date

            previous_period = self.db.query(
                BidAnnouncement.industry_type,
                func.count(BidAnnouncement.id).label('count')
            ).filter(
                and_(
                    BidAnnouncement.announcement_date >= prev_start,
                    BidAnnouncement.announcement_date < prev_end
                )
            ).group_by(
                BidAnnouncement.industry_type
            ).all()

            # 성장률 계산
            current_dict = {row.industry_type: row.count for row in current_period}
            previous_dict = {row.industry_type: row.count for row in previous_period}

            growth_rates = []
            for industry in current_dict.keys():
                current = current_dict[industry]
                previous = previous_dict.get(industry, 0)

                if previous > 0:
                    growth_rate = ((current - previous) / previous) * 100
                else:
                    growth_rate = 100 if current > 0 else 0

                growth_rates.append({
                    "industry": industry or "기타",
                    "current_count": current,
                    "previous_count": previous,
                    "growth_rate": round(growth_rate, 1)
                })

            # 성장률 순으로 정렬
            growth_rates.sort(key=lambda x: x["growth_rate"], reverse=True)

            return growth_rates[:10]  # 상위 10개

        except Exception as e:
            logger.error(f"업종별 성장률 계산 실패: {e}")
            return []

    def get_user_statistics(self, user_id: int) -> Dict[str, Any]:
        """
        사용자별 통계
        """
        try:
            # 북마크 수
            bookmark_count = self.db.query(func.count(UserBidBookmark.id)).filter(
                UserBidBookmark.user_id == user_id
            ).scalar()

            # 최근 7일 활동
            week_ago = datetime.now() - timedelta(days=7)
            recent_bookmarks = self.db.query(func.count(UserBidBookmark.id)).filter(
                and_(
                    UserBidBookmark.user_id == user_id,
                    UserBidBookmark.bookmark_date >= week_ago
                )
            ).scalar()

            return {
                "total_bookmarks": bookmark_count,
                "recent_bookmarks": recent_bookmarks,
                "member_since": self.db.query(User.created_at).filter(
                    User.id == user_id
                ).scalar()
            }

        except Exception as e:
            logger.error(f"사용자 통계 조회 실패: {e}")
            return {}

    def get_monthly_summary(self, year: int, month: int) -> Dict[str, Any]:
        """
        월별 요약 통계
        """
        try:
            # 월 시작과 끝 날짜
            start_date = datetime(year, month, 1)
            if month == 12:
                end_date = datetime(year + 1, 1, 1) - timedelta(days=1)
            else:
                end_date = datetime(year, month + 1, 1) - timedelta(days=1)

            # 총 입찰 수
            total_bids = self.db.query(func.count(BidAnnouncement.id)).filter(
                and_(
                    BidAnnouncement.announcement_date >= start_date,
                    BidAnnouncement.announcement_date <= end_date
                )
            ).scalar()

            # 총 금액
            total_amount = self.db.query(func.sum(BidAnnouncement.bid_amount)).filter(
                and_(
                    BidAnnouncement.announcement_date >= start_date,
                    BidAnnouncement.announcement_date <= end_date
                )
            ).scalar() or 0

            # 평균 금액
            avg_amount = total_amount / total_bids if total_bids > 0 else 0

            # 주요 발주기관
            top_org = self.db.query(
                BidAnnouncement.organization_name,
                func.count(BidAnnouncement.id).label('count')
            ).filter(
                and_(
                    BidAnnouncement.announcement_date >= start_date,
                    BidAnnouncement.announcement_date <= end_date
                )
            ).group_by(
                BidAnnouncement.organization_name
            ).order_by(
                func.count(BidAnnouncement.id).desc()
            ).first()

            return {
                "year": year,
                "month": month,
                "total_bids": total_bids,
                "total_amount": total_amount,
                "average_amount": avg_amount,
                "top_organization": {
                    "name": top_org.organization_name if top_org else None,
                    "count": top_org.count if top_org else 0
                }
            }

        except Exception as e:
            logger.error(f"월별 요약 통계 조회 실패: {e}")
            return {}

    def get_competition_analysis(self, bid_notice_no: str) -> Dict[str, Any]:
        """
        특정 입찰의 경쟁 분석
        """
        try:
            # 입찰 정보
            bid = self.db.query(BidAnnouncement).filter(
                BidAnnouncement.bid_notice_no == bid_notice_no
            ).first()

            if not bid:
                return {}

            # 유사 입찰 찾기 (같은 기관, 비슷한 금액대)
            similar_bids = self.db.query(BidAnnouncement).filter(
                and_(
                    BidAnnouncement.organization_name == bid.organization_name,
                    BidAnnouncement.bid_amount.between(
                        bid.bid_amount * 0.8,
                        bid.bid_amount * 1.2
                    ) if bid.bid_amount else True,
                    BidAnnouncement.id != bid.id
                )
            ).limit(10).all()

            # 예상 경쟁률 (모의 데이터)
            expected_competition = 5 + (hash(bid_notice_no) % 10)

            return {
                "bid_notice_no": bid_notice_no,
                "expected_competition_rate": expected_competition,
                "similar_bids_count": len(similar_bids),
                "organization_avg_competition": expected_competition * 0.9,
                "industry_avg_competition": expected_competition * 1.1
            }

        except Exception as e:
            logger.error(f"경쟁 분석 실패: {e}")
            return {}