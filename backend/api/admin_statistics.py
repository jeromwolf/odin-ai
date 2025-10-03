"""
관리자 웹 - 통계 분석 API
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import List, Optional, Dict
from datetime import datetime, date, timedelta
from database import get_db_connection
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/admin/statistics", tags=["admin-statistics"])


# ============================================
# Pydantic Models
# ============================================

class BidCollectionStats(BaseModel):
    """입찰공고 수집 통계 모델"""
    date: str
    total_collected: int
    new_bids: int
    updated_bids: int
    total_amount: int


class BidCollectionStatsResponse(BaseModel):
    """입찰공고 수집 통계 응답"""
    stats: List[BidCollectionStats]
    summary: dict
    period: dict


class CategoryDistribution(BaseModel):
    """카테고리별 분포 모델"""
    category: str
    count: int
    percentage: float
    total_amount: int


class CategoryDistributionResponse(BaseModel):
    """카테고리별 분포 응답"""
    categories: List[CategoryDistribution]
    total_bids: int
    period: dict


class UserGrowthStats(BaseModel):
    """사용자 증가 통계 모델"""
    date: str
    new_users: int
    total_users: int
    active_users: int


class UserGrowthResponse(BaseModel):
    """사용자 증가 통계 응답"""
    growth: List[UserGrowthStats]
    summary: dict
    period: dict


class NotificationStats(BaseModel):
    """알림 발송 통계 모델"""
    date: str
    total_sent: int
    success_count: int
    failed_count: int
    success_rate: float


class NotificationStatsResponse(BaseModel):
    """알림 발송 통계 응답"""
    stats: List[NotificationStats]
    summary: dict
    period: dict


# ============================================
# API Endpoints
# ============================================

@router.get("/bid-collection", response_model=BidCollectionStatsResponse)
async def get_bid_collection_stats(
    start_date: Optional[date] = Query(None, description="시작 날짜"),
    end_date: Optional[date] = Query(None, description="종료 날짜"),
    group_by: str = Query("day", description="day/week/month")
):
    """
    입찰공고 수집 통계

    - 일별/주별/월별 수집 건수
    - 신규/갱신 비율
    - 예정가격 총액
    """
    try:
        # 기본값: 최근 30일
        if not end_date:
            end_date = date.today()
        if not start_date:
            start_date = end_date - timedelta(days=30)

        with get_db_connection() as conn:
            cursor = conn.cursor()

            # 그룹핑 기준 설정
            date_trunc = {
                'day': 'day',
                'week': 'week',
                'month': 'month'
            }.get(group_by, 'day')

            # 수집 통계 조회
            query = f"""
                SELECT
                    DATE_TRUNC('{date_trunc}', publish_date)::date as stat_date,
                    COUNT(*) as total_collected,
                    COUNT(*) FILTER (WHERE created_at::date = publish_date) as new_bids,
                    COUNT(*) FILTER (WHERE created_at::date != publish_date) as updated_bids,
                    COALESCE(SUM(estimated_price), 0) as total_amount
                FROM bid_announcements
                WHERE publish_date >= %s AND publish_date <= %s
                GROUP BY stat_date
                ORDER BY stat_date DESC
            """
            cursor.execute(query, (start_date, end_date))

            stats = []
            for row in cursor.fetchall():
                stats.append(BidCollectionStats(
                    date=row[0].isoformat(),
                    total_collected=row[1],
                    new_bids=row[2],
                    updated_bids=row[3],
                    total_amount=row[4]
                ))

            # 요약 통계
            summary_query = """
                SELECT
                    COUNT(*) as total,
                    COUNT(*) FILTER (WHERE created_at::date >= %s AND created_at::date <= %s) as new,
                    COALESCE(SUM(estimated_price), 0) as total_amount,
                    COALESCE(AVG(estimated_price), 0) as avg_amount
                FROM bid_announcements
                WHERE publish_date >= %s AND publish_date <= %s
            """
            cursor.execute(summary_query, (start_date, end_date, start_date, end_date))
            summary_row = cursor.fetchone()

            summary = {
                "total_collected": summary_row[0],
                "new_bids": summary_row[1],
                "total_amount": summary_row[2],
                "average_amount": round(summary_row[3], 0)
            }

            return BidCollectionStatsResponse(
                stats=stats,
                summary=summary,
                period={
                    "start": start_date.isoformat(),
                    "end": end_date.isoformat(),
                    "group_by": group_by
                }
            )

    except Exception as e:
        logger.error(f"입찰공고 수집 통계 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/category-distribution", response_model=CategoryDistributionResponse)
async def get_category_distribution(
    start_date: Optional[date] = Query(None, description="시작 날짜"),
    end_date: Optional[date] = Query(None, description="종료 날짜")
):
    """
    카테고리별 입찰 분포

    - 태그별 입찰 건수
    - 비율 계산
    - 예정가격 총액
    """
    try:
        # 기본값: 최근 30일
        if not end_date:
            end_date = date.today()
        if not start_date:
            start_date = end_date - timedelta(days=30)

        with get_db_connection() as conn:
            cursor = conn.cursor()

            # 전체 건수 조회
            cursor.execute("""
                SELECT COUNT(*) FROM bid_announcements
                WHERE publish_date >= %s AND publish_date <= %s
            """, (start_date, end_date))
            total_bids = cursor.fetchone()[0]

            if total_bids == 0:
                return CategoryDistributionResponse(
                    categories=[],
                    total_bids=0,
                    period={
                        "start": start_date.isoformat(),
                        "end": end_date.isoformat()
                    }
                )

            # 카테고리별 분포 조회
            query = """
                SELECT
                    t.tag_name as category,
                    COUNT(DISTINCT ba.id) as count,
                    COALESCE(SUM(ba.estimated_price), 0) as total_amount
                FROM bid_announcements ba
                JOIN bid_tag_relations btr ON ba.id = btr.bid_id
                JOIN bid_tags t ON btr.tag_id = t.id
                WHERE ba.publish_date >= %s AND ba.publish_date <= %s
                GROUP BY t.tag_name
                ORDER BY count DESC
                LIMIT 10
            """
            cursor.execute(query, (start_date, end_date))

            categories = []
            for row in cursor.fetchall():
                count = row[1]
                percentage = (count / total_bids * 100) if total_bids > 0 else 0
                categories.append(CategoryDistribution(
                    category=row[0],
                    count=count,
                    percentage=round(percentage, 2),
                    total_amount=row[2]
                ))

            return CategoryDistributionResponse(
                categories=categories,
                total_bids=total_bids,
                period={
                    "start": start_date.isoformat(),
                    "end": end_date.isoformat()
                }
            )

    except Exception as e:
        logger.error(f"카테고리별 분포 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/user-growth", response_model=UserGrowthResponse)
async def get_user_growth_stats(
    start_date: Optional[date] = Query(None, description="시작 날짜"),
    end_date: Optional[date] = Query(None, description="종료 날짜")
):
    """
    사용자 증가 추이

    - 일별 신규 가입자
    - 누적 사용자 수
    - 활성 사용자 수 (최근 30일 로그인)
    """
    try:
        # 기본값: 최근 30일
        if not end_date:
            end_date = date.today()
        if not start_date:
            start_date = end_date - timedelta(days=30)

        with get_db_connection() as conn:
            cursor = conn.cursor()

            # 일별 증가 추이
            query = """
                WITH date_series AS (
                    SELECT generate_series(%s::date, %s::date, '1 day'::interval)::date as date
                ),
                daily_new AS (
                    SELECT
                        created_at::date as date,
                        COUNT(*) as new_users
                    FROM users
                    WHERE created_at::date >= %s AND created_at::date <= %s
                    GROUP BY created_at::date
                ),
                daily_active AS (
                    SELECT
                        last_login_at::date as date,
                        COUNT(DISTINCT id) as active_users
                    FROM users
                    WHERE last_login_at IS NOT NULL
                      AND last_login_at::date >= %s AND last_login_at::date <= %s
                    GROUP BY last_login_at::date
                )
                SELECT
                    ds.date,
                    COALESCE(dn.new_users, 0) as new_users,
                    (SELECT COUNT(*) FROM users WHERE created_at::date <= ds.date) as total_users,
                    COALESCE(da.active_users, 0) as active_users
                FROM date_series ds
                LEFT JOIN daily_new dn ON ds.date = dn.date
                LEFT JOIN daily_active da ON ds.date = da.date
                ORDER BY ds.date DESC
            """
            cursor.execute(query, (start_date, end_date, start_date, end_date, start_date, end_date))

            growth = []
            for row in cursor.fetchall():
                growth.append(UserGrowthStats(
                    date=row[0].isoformat(),
                    new_users=row[1],
                    total_users=row[2],
                    active_users=row[3]
                ))

            # 요약 통계
            cursor.execute("""
                SELECT
                    COUNT(*) as total_users,
                    COUNT(*) FILTER (WHERE created_at >= %s) as new_users_period,
                    COUNT(*) FILTER (WHERE is_active = true) as active_users,
                    COUNT(*) FILTER (WHERE last_login_at >= NOW() - INTERVAL '30 days') as recent_active
                FROM users
            """, (start_date,))
            summary_row = cursor.fetchone()

            summary = {
                "total_users": summary_row[0],
                "new_users_in_period": summary_row[1],
                "active_users": summary_row[2],
                "recent_active_users": summary_row[3]
            }

            return UserGrowthResponse(
                growth=growth,
                summary=summary,
                period={
                    "start": start_date.isoformat(),
                    "end": end_date.isoformat()
                }
            )

    except Exception as e:
        logger.error(f"사용자 증가 통계 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/notifications", response_model=NotificationStatsResponse)
async def get_notification_stats(
    start_date: Optional[date] = Query(None, description="시작 날짜"),
    end_date: Optional[date] = Query(None, description="종료 날짜")
):
    """
    알림 발송 통계

    - 일별 발송 건수
    - 성공/실패 비율
    - 채널별 통계
    """
    try:
        # 기본값: 최근 30일
        if not end_date:
            end_date = date.today()
        if not start_date:
            start_date = end_date - timedelta(days=30)

        with get_db_connection() as conn:
            cursor = conn.cursor()

            # 일별 알림 통계
            query = """
                WITH date_series AS (
                    SELECT generate_series(%s::date, %s::date, '1 day'::interval)::date as date
                ),
                daily_stats AS (
                    SELECT
                        created_at::date as date,
                        COUNT(*) as total_sent,
                        COUNT(*) FILTER (WHERE status = 'sent') as success_count,
                        COUNT(*) FILTER (WHERE status = 'failed') as failed_count
                    FROM notification_send_logs
                    WHERE created_at::date >= %s AND created_at::date <= %s
                    GROUP BY created_at::date
                )
                SELECT
                    ds.date,
                    COALESCE(dst.total_sent, 0) as total_sent,
                    COALESCE(dst.success_count, 0) as success_count,
                    COALESCE(dst.failed_count, 0) as failed_count
                FROM date_series ds
                LEFT JOIN daily_stats dst ON ds.date = dst.date
                ORDER BY ds.date DESC
            """
            cursor.execute(query, (start_date, end_date, start_date, end_date))

            stats = []
            for row in cursor.fetchall():
                total_sent = row[1]
                success_count = row[2]
                success_rate = (success_count / total_sent * 100) if total_sent > 0 else 0

                stats.append(NotificationStats(
                    date=row[0].isoformat(),
                    total_sent=total_sent,
                    success_count=success_count,
                    failed_count=row[3],
                    success_rate=round(success_rate, 2)
                ))

            # 요약 통계
            cursor.execute("""
                SELECT
                    COUNT(*) as total,
                    COUNT(*) FILTER (WHERE status = 'sent') as success,
                    COUNT(*) FILTER (WHERE status = 'failed') as failed,
                    COUNT(*) FILTER (WHERE notification_channel = 'email') as email_count,
                    COUNT(*) FILTER (WHERE notification_channel = 'push') as push_count,
                    COUNT(*) FILTER (WHERE notification_channel = 'sms') as sms_count
                FROM notification_send_logs
                WHERE created_at::date >= %s AND created_at::date <= %s
            """, (start_date, end_date))
            summary_row = cursor.fetchone()

            total = summary_row[0]
            success = summary_row[1]
            success_rate = (success / total * 100) if total > 0 else 0

            summary = {
                "total_sent": total,
                "success_count": success,
                "failed_count": summary_row[2],
                "success_rate": round(success_rate, 2),
                "by_channel": {
                    "email": summary_row[3],
                    "push": summary_row[4],
                    "sms": summary_row[5]
                }
            }

            return NotificationStatsResponse(
                stats=stats,
                summary=summary,
                period={
                    "start": start_date.isoformat(),
                    "end": end_date.isoformat()
                }
            )

    except Exception as e:
        logger.error(f"알림 발송 통계 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))
