"""
관리자 웹 - 통계 분석 API
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel
from typing import List, Optional, Dict
from datetime import datetime, date, timedelta
from database import get_db_connection
from api.admin_auth import get_current_admin
from psycopg2.extras import RealDictCursor
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
    group_by: str = Query("day", description="day/week/month"),
    current_admin: dict = Depends(get_current_admin)
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
            cursor = conn.cursor(cursor_factory=RealDictCursor)

            # SQL Injection 방어: whitelist만 허용
            VALID_TRUNCS = {'day', 'week', 'month'}
            date_trunc = group_by if group_by in VALID_TRUNCS else 'day'

            # 수집 통계 조회
            query = f"""
                SELECT
                    DATE_TRUNC('{date_trunc}', announcement_date)::date as stat_date,
                    COUNT(*) as total_collected,
                    COUNT(*) FILTER (WHERE created_at::date = announcement_date::date) as new_bids,
                    COUNT(*) FILTER (WHERE created_at::date != announcement_date::date) as updated_bids,
                    COALESCE(SUM(estimated_price), 0) as total_amount
                FROM bid_announcements
                WHERE announcement_date >= %s AND announcement_date <= %s
                GROUP BY stat_date
                ORDER BY stat_date DESC
            """
            cursor.execute(query, (start_date, end_date))

            stats = []
            for row in cursor.fetchall():
                stats.append(BidCollectionStats(
                    date=row['stat_date'].isoformat(),
                    total_collected=row['total_collected'],
                    new_bids=row['new_bids'],
                    updated_bids=row['updated_bids'],
                    total_amount=row['total_amount']
                ))

            # 요약 통계
            summary_query = """
                SELECT
                    COUNT(*) as total,
                    COUNT(*) FILTER (WHERE created_at::date >= %s AND created_at::date <= %s) as new,
                    COALESCE(SUM(estimated_price), 0) as total_amount,
                    COALESCE(AVG(estimated_price), 0) as avg_amount
                FROM bid_announcements
                WHERE announcement_date >= %s AND announcement_date <= %s
            """
            cursor.execute(summary_query, (start_date, end_date, start_date, end_date))
            summary_row = cursor.fetchone()

            summary = {
                "total_collected": summary_row['total'],
                "new_bids": summary_row['new'],
                "total_amount": summary_row['total_amount'],
                "average_amount": round(summary_row['avg_amount'], 0)
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
        raise HTTPException(status_code=500, detail="서버 내부 오류가 발생했습니다")


@router.get("/category-distribution", response_model=CategoryDistributionResponse)
async def get_category_distribution(
    start_date: Optional[date] = Query(None, description="시작 날짜"),
    end_date: Optional[date] = Query(None, description="종료 날짜"),
    current_admin: dict = Depends(get_current_admin)
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
            cursor = conn.cursor(cursor_factory=RealDictCursor)

            # 전체 건수 조회
            cursor.execute("""
                SELECT COUNT(*) as count FROM bid_announcements
                WHERE announcement_date >= %s AND announcement_date <= %s
            """, (start_date, end_date))
            total_bids = cursor.fetchone()['count']

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
                JOIN bid_tag_relations btr ON ba.bid_notice_no = btr.bid_notice_no
                JOIN bid_tags t ON btr.tag_id = t.tag_id
                WHERE ba.announcement_date >= %s AND ba.announcement_date <= %s
                GROUP BY t.tag_name
                ORDER BY count DESC
                LIMIT 10
            """
            cursor.execute(query, (start_date, end_date))

            categories = []
            for row in cursor.fetchall():
                count = row['count']
                percentage = (count / total_bids * 100) if total_bids > 0 else 0
                categories.append(CategoryDistribution(
                    category=row['category'],
                    count=count,
                    percentage=round(percentage, 2),
                    total_amount=row['total_amount']
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
        raise HTTPException(status_code=500, detail="서버 내부 오류가 발생했습니다")


@router.get("/user-growth", response_model=UserGrowthResponse)
async def get_user_growth_stats(
    start_date: Optional[date] = Query(None, description="시작 날짜"),
    end_date: Optional[date] = Query(None, description="종료 날짜"),
    current_admin: dict = Depends(get_current_admin)
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
            cursor = conn.cursor(cursor_factory=RealDictCursor)

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
                        last_login::date as date,
                        COUNT(DISTINCT id) as active_users
                    FROM users
                    WHERE last_login IS NOT NULL
                      AND last_login::date >= %s AND last_login::date <= %s
                    GROUP BY last_login::date
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
                    date=row['date'].isoformat(),
                    new_users=row['new_users'],
                    total_users=row['total_users'],
                    active_users=row['active_users']
                ))

            # 요약 통계
            cursor.execute("""
                SELECT
                    COUNT(*) as total_users,
                    COUNT(*) FILTER (WHERE created_at >= %s) as new_users_period,
                    COUNT(*) FILTER (WHERE is_active = true) as active_users,
                    COUNT(*) FILTER (WHERE last_login >= NOW() - INTERVAL '30 days') as recent_active
                FROM users
            """, (start_date,))
            summary_row = cursor.fetchone()

            summary = {
                "total_users": summary_row['total_users'],
                "new_users_in_period": summary_row['new_users_period'],
                "active_users": summary_row['active_users'],
                "recent_active_users": summary_row['recent_active']
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
        raise HTTPException(status_code=500, detail="서버 내부 오류가 발생했습니다")


@router.get("/notifications", response_model=NotificationStatsResponse)
async def get_notification_stats(
    start_date: Optional[date] = Query(None, description="시작 날짜"),
    end_date: Optional[date] = Query(None, description="종료 날짜"),
    current_admin: dict = Depends(get_current_admin)
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
            cursor = conn.cursor(cursor_factory=RealDictCursor)

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
                total_sent = row['total_sent']
                success_count = row['success_count']
                success_rate = (success_count / total_sent * 100) if total_sent > 0 else 0

                stats.append(NotificationStats(
                    date=row['date'].isoformat(),
                    total_sent=total_sent,
                    success_count=success_count,
                    failed_count=row['failed_count'],
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

            total = summary_row['total']
            success = summary_row['success']
            success_rate = (success / total * 100) if total > 0 else 0

            summary = {
                "total_sent": total,
                "success_count": success,
                "failed_count": summary_row['failed'],
                "success_rate": round(success_rate, 2),
                "by_channel": {
                    "email": summary_row['email_count'],
                    "push": summary_row['push_count'],
                    "sms": summary_row['sms_count']
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
        raise HTTPException(status_code=500, detail="서버 내부 오류가 발생했습니다")
