"""
대시보드 API - 실제 데이터베이스 연동
"""

from fastapi import APIRouter, HTTPException, Query, Depends
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta, timezone
from database import get_db_connection
from auth.dependencies import get_current_user_optional, get_current_user, User
from psycopg2.extras import RealDictCursor
import logging

try:
    from cache import get_cached_or_fetch, CACHE_TTL
    CACHE_AVAILABLE = True
except ImportError:
    CACHE_AVAILABLE = False

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("/overview")
async def get_dashboard_overview(user: Optional[User] = Depends(get_current_user_optional)):
    """대시보드 개요 데이터 (실제 DB)"""
    try:
        cache_params = {"endpoint": "overview", "user_id": user.id if user else "anonymous"}

        def fetch_overview():
            with get_db_connection() as conn:
                cursor = conn.cursor(cursor_factory=RealDictCursor)

                # 전체/활성/가격/신규/마감임박 통계를 단일 쿼리로 조회
                cursor.execute("""
                    SELECT
                        COUNT(*) as total_bids,
                        COUNT(*) FILTER (WHERE bid_end_date >= NOW()) as active_bids,
                        COALESCE(SUM(estimated_price) FILTER (WHERE estimated_price IS NOT NULL), 0) as total_price,
                        COUNT(*) FILTER (WHERE created_at >= CURRENT_DATE) as today_new,
                        COUNT(*) FILTER (WHERE created_at >= date_trunc('week', CURRENT_DATE)) as week_new,
                        COUNT(*) FILTER (WHERE bid_end_date BETWEEN NOW() AND NOW() + INTERVAL '3 days') as deadline_soon
                    FROM bid_announcements
                """)
                row = cursor.fetchone()
                total_bids = row['total_bids']
                active_bids = row['active_bids']
                total_price = row['total_price']
                today_new = row['today_new']
                week_new = row['week_new']
                deadline_soon = row['deadline_soon']
                expired_bids = total_bids - active_bids

                # 사용자별 통계 (로그인한 경우)
                user_stats = None
                if user:
                    cursor.execute("""
                        SELECT
                            COUNT(*) as bookmark_count,
                            COUNT(CASE WHEN b.bid_end_date >= NOW() THEN 1 END) as active_bookmarks
                        FROM user_bookmarks ub
                        LEFT JOIN bid_announcements b ON ub.bid_id = b.bid_notice_no
                        WHERE ub.user_id = %s
                    """, (user.id,))
                    user_row = cursor.fetchone()
                    user_stats = {
                        "bookmarks": user_row['bookmark_count'],
                        "active_bookmarks": user_row['active_bookmarks'],
                        "alerts": 0  # 알림 시스템 구현 후
                    }

                return {
                    "success": True,
                    "data": {
                        "total_bids": total_bids,
                        "active_bids": active_bids,
                        "expired_bids": expired_bids,
                        "total_price": float(total_price),
                        "average_competition_rate": None,
                        "today_new": today_new,
                        "week_new": week_new,
                        "deadline_soon": deadline_soon,
                        "user_stats": user_stats,
                        "last_updated": datetime.now(timezone.utc).isoformat()
                    }
                }

        if CACHE_AVAILABLE:
            return get_cached_or_fetch("dashboard", cache_params, fetch_overview, CACHE_TTL.get("dashboard", 60))
        return fetch_overview()

    except Exception as e:
        logger.error(f"대시보드 개요 조회 실패: {e}")
        raise HTTPException(status_code=500, detail="대시보드 데이터 조회 실패")


@router.get("/statistics")
async def get_bid_statistics(
    days: int = Query(7, ge=1, le=365),
    user: Optional[User] = Depends(get_current_user_optional)
):
    """입찰 통계 데이터 (실제 DB)"""
    try:
        cache_params = {"endpoint": "statistics", "days": days}

        def fetch_statistics():
            with get_db_connection() as conn:
                cursor = conn.cursor(cursor_factory=RealDictCursor)

                # 일별 입찰 통계
                cursor.execute("""
                    SELECT
                        DATE(created_at) as date,
                        COUNT(*) as count,
                        COALESCE(SUM(estimated_price), 0) as total_price
                    FROM bid_announcements
                    WHERE created_at >= CURRENT_DATE - INTERVAL %s
                    GROUP BY DATE(created_at)
                    ORDER BY date ASC
                """, (f"{days} days",))

                daily_stats = []
                for row in cursor.fetchall():
                    daily_stats.append({
                        "date": row['date'].isoformat(),
                        "count": row['count'],
                        "total_price": float(row['total_price'])
                    })

                # 카테고리별 분포 (태그 기반)
                cursor.execute("""
                    SELECT
                        t.tag_name as category,
                        COUNT(DISTINCT btr.bid_notice_no) as count
                    FROM bid_tags t
                    JOIN bid_tag_relations btr ON t.tag_id = btr.tag_id
                    GROUP BY t.tag_name
                    ORDER BY count DESC
                    LIMIT 10
                """)

                category_distribution = []
                total_count = 0
                rows = cursor.fetchall()

                # 전체 개수 계산
                for row in rows:
                    total_count += row['count']

                # 퍼센트 계산하여 추가
                for row in rows:
                    percentage = round((row['count'] / total_count * 100), 1) if total_count > 0 else 0
                    category_distribution.append({
                        "category": row['category'],
                        "count": row['count'],
                        "percentage": percentage
                    })

                # 기관별 TOP 10
                cursor.execute("""
                    SELECT
                        organization_name,
                        COUNT(*) as count,
                        COALESCE(SUM(estimated_price), 0) as total_price
                    FROM bid_announcements
                    WHERE organization_name IS NOT NULL
                    GROUP BY organization_name
                    ORDER BY count DESC
                    LIMIT 10
                """)

                organization_stats = []
                for row in cursor.fetchall():
                    organization_stats.append({
                        "organization": row['organization_name'],
                        "count": row['count'],
                        "total_price": float(row['total_price'])
                    })

                # 가격대별 분포
                cursor.execute("""
                    SELECT
                        CASE
                            WHEN estimated_price < 10000000 THEN '1천만원 미만'
                            WHEN estimated_price < 50000000 THEN '1천만원~5천만원'
                            WHEN estimated_price < 100000000 THEN '5천만원~1억원'
                            WHEN estimated_price < 500000000 THEN '1억원~5억원'
                            WHEN estimated_price < 1000000000 THEN '5억원~10억원'
                            ELSE '10억원 이상'
                        END as price_range,
                        COUNT(*) as count
                    FROM bid_announcements
                    WHERE estimated_price IS NOT NULL
                    GROUP BY 1
                    ORDER BY
                        MIN(estimated_price)
                """)

                price_distribution = []
                for row in cursor.fetchall():
                    price_distribution.append({
                        "range": row['price_range'],
                        "count": row['count']
                    })

                return {
                    "success": True,
                    "data": {
                        "daily_stats": daily_stats,
                        "category_distribution": category_distribution,
                        "organization_stats": organization_stats,
                        "price_distribution": price_distribution,
                        "period": {
                            "days": days,
                            "start_date": (datetime.now(timezone.utc) - timedelta(days=days)).date().isoformat(),
                            "end_date": datetime.now(timezone.utc).date().isoformat()
                        }
                    }
                }

        if CACHE_AVAILABLE:
            return get_cached_or_fetch("dashboard", cache_params, fetch_statistics, CACHE_TTL.get("dashboard", 60))
        return fetch_statistics()

    except Exception as e:
        logger.error(f"통계 조회 실패: {e}")
        raise HTTPException(status_code=500, detail="통계 데이터 조회 실패")


@router.get("/deadlines")
async def get_approaching_deadlines(
    days: int = Query(7, ge=1, le=30),
    limit: int = Query(10, ge=1, le=50),
    user: Optional[User] = Depends(get_current_user_optional)
):
    """마감 임박 입찰 목록 (실제 DB)"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)

            # 마감 임박 입찰 조회
            cursor.execute("""
                SELECT
                    bid_notice_no,
                    title,
                    organization_name,
                    estimated_price,
                    bid_end_date,
                    EXTRACT(EPOCH FROM (bid_end_date - NOW())) / 3600 as hours_remaining
                FROM bid_announcements
                WHERE bid_end_date >= NOW()
                    AND bid_end_date <= NOW() + INTERVAL %s
                ORDER BY bid_end_date ASC
                LIMIT %s
            """, (f"{days} days", limit))

            deadlines = []
            for row in cursor.fetchall():
                hours = row['hours_remaining']
                if hours < 24:
                    urgency = "urgent"
                    remaining_text = f"{int(hours)}시간"
                elif hours < 72:
                    urgency = "warning"
                    remaining_text = f"{int(hours/24)}일"
                else:
                    urgency = "normal"
                    remaining_text = f"{int(hours/24)}일"

                deadlines.append({
                    "bid_id": row['bid_notice_no'],
                    "title": row['title'],
                    "organization": row['organization_name'],
                    "price": float(row['estimated_price']) if row['estimated_price'] else None,
                    "deadline": row['bid_end_date'].isoformat(),
                    "hours_remaining": round(hours, 1),
                    "remaining_text": remaining_text,
                    "urgency": urgency
                })

            # 사용자 북마크 체크 (로그인한 경우)
            if user and deadlines:
                bid_ids = [d["bid_id"] for d in deadlines]
                cursor.execute("""
                    SELECT bid_id FROM user_bookmarks
                    WHERE user_id = %s AND bid_id = ANY(%s)
                """, (user.id, bid_ids))

                bookmarked_ids = {row['bid_id'] for row in cursor.fetchall()}
                for deadline in deadlines:
                    deadline["is_bookmarked"] = deadline["bid_id"] in bookmarked_ids

            return {
                "success": True,
                "data": deadlines,
                "total": len(deadlines),
                "filter": {
                    "days": days,
                    "limit": limit
                }
            }

    except Exception as e:
        logger.error(f"마감임박 조회 실패: {e}")
        raise HTTPException(status_code=500, detail="마감임박 데이터 조회 실패")


@router.get("/recommendations")
async def get_recommendations(
    user: User = Depends(get_current_user)
):
    """AI 추천 입찰 (향후 실제 AI 모델 연동)"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)

            # 사용자 북마크 기반 추천 (간단한 로직)
            # 1. 사용자가 북마크한 입찰의 기관들 찾기 (bid_announcements JOIN)
            cursor.execute("""
                SELECT DISTINCT ba.organization_name
                FROM user_bookmarks ub
                JOIN bid_announcements ba ON ub.bid_notice_no = ba.bid_notice_no
                WHERE ub.user_id = %s AND ba.organization_name IS NOT NULL
                LIMIT 10
            """, (user.id,))

            user_orgs = [row['organization_name'] for row in cursor.fetchall()]

            recommendations = []

            if user_orgs:
                # 같은 기관의 다른 입찰 추천
                cursor.execute("""
                    SELECT
                        b.bid_notice_no,
                        b.title,
                        b.organization_name,
                        b.estimated_price,
                        b.bid_end_date,
                        CASE
                            WHEN ub.id IS NOT NULL THEN true
                            ELSE false
                        END as is_bookmarked
                    FROM bid_announcements b
                    LEFT JOIN user_bookmarks ub ON
                        b.bid_notice_no = ub.bid_id AND ub.user_id = %s
                    WHERE b.organization_name = ANY(%s)
                        AND b.bid_end_date >= NOW()
                        AND ub.id IS NULL  -- 아직 북마크하지 않은 것만
                    ORDER BY b.created_at DESC
                    LIMIT 5
                """, (user.id, user_orgs))

                for row in cursor.fetchall():
                    recommendations.append({
                        "bid_id": row['bid_notice_no'],
                        "title": row['title'],
                        "organization": row['organization_name'],
                        "price": float(row['estimated_price']) if row['estimated_price'] else None,
                        "deadline": row['bid_end_date'].isoformat() if row['bid_end_date'] else None,
                        "score": 85,  # 더미 점수
                        "reason": f"{row['organization_name']}의 다른 입찰",
                        "is_bookmarked": row['is_bookmarked']
                    })

            # 추천이 없으면 최신 입찰 추천
            if len(recommendations) < 5:
                cursor.execute("""
                    SELECT
                        b.bid_notice_no,
                        b.title,
                        b.organization_name,
                        b.estimated_price,
                        b.bid_end_date,
                        CASE
                            WHEN ub.id IS NOT NULL THEN true
                            ELSE false
                        END as is_bookmarked
                    FROM bid_announcements b
                    LEFT JOIN user_bookmarks ub ON
                        b.bid_notice_no = ub.bid_id AND ub.user_id = %s
                    WHERE b.bid_end_date >= NOW()
                    ORDER BY b.created_at DESC
                    LIMIT %s
                """, (user.id, 10 - len(recommendations)))

                for row in cursor.fetchall():
                    recommendations.append({
                        "bid_id": row['bid_notice_no'],
                        "title": row['title'],
                        "organization": row['organization_name'],
                        "price": float(row['estimated_price']) if row['estimated_price'] else None,
                        "deadline": row['bid_end_date'].isoformat() if row['bid_end_date'] else None,
                        "score": 70,
                        "reason": "최신 입찰",
                        "is_bookmarked": row['is_bookmarked']
                    })

            return {
                "success": True,
                "data": recommendations[:10],
                "total": len(recommendations),
                "algorithm": "bookmark_based_v1"
            }

    except Exception as e:
        logger.error(f"추천 조회 실패: {e}")
        raise HTTPException(status_code=500, detail="추천 데이터 조회 실패")


@router.get("/trends")
async def get_bid_trends(
    period: str = Query("week", pattern="^(day|week|month|year)$"),
    user: Optional[User] = Depends(get_current_user_optional)
):
    """입찰 트렌드 분석"""
    try:
        cache_params = {"endpoint": "trends", "period": period}

        def fetch_trends():
            with get_db_connection() as conn:
                cursor = conn.cursor(cursor_factory=RealDictCursor)

                # 기간 설정
                if period == "day":
                    interval = "1 day"
                    group_by = "hour"
                elif period == "week":
                    interval = "7 days"
                    group_by = "day"
                elif period == "month":
                    interval = "30 days"
                    group_by = "day"
                else:  # year
                    interval = "365 days"
                    group_by = "month"

                # 트렌드 데이터 조회
                if group_by == "hour":
                    cursor.execute("""
                        SELECT
                            EXTRACT(HOUR FROM created_at) as period,
                            COUNT(*) as count
                        FROM bid_announcements
                        WHERE created_at >= NOW() - INTERVAL %s
                        GROUP BY EXTRACT(HOUR FROM created_at)
                        ORDER BY period
                    """, (interval,))
                elif group_by == "day":
                    cursor.execute("""
                        SELECT
                            DATE(created_at) as period,
                            COUNT(*) as count
                        FROM bid_announcements
                        WHERE created_at >= NOW() - INTERVAL %s
                        GROUP BY DATE(created_at)
                        ORDER BY period
                    """, (interval,))
                else:  # month
                    cursor.execute("""
                        SELECT
                            DATE_TRUNC('month', created_at) as period,
                            COUNT(*) as count
                        FROM bid_announcements
                        WHERE created_at >= NOW() - INTERVAL %s
                        GROUP BY DATE_TRUNC('month', created_at)
                        ORDER BY period
                    """, (interval,))

                trends = []
                for row in cursor.fetchall():
                    trends.append({
                        "period": str(row['period']),
                        "count": row['count']
                    })

                # 인기 키워드 (태그 기반)
                cursor.execute("""
                    SELECT
                        t.tag_name,
                        COUNT(DISTINCT btr.bid_notice_no) as count
                    FROM bid_tags t
                    JOIN bid_tag_relations btr ON t.tag_id = btr.tag_id
                    JOIN bid_announcements b ON btr.bid_notice_no = b.bid_notice_no
                    WHERE b.created_at >= NOW() - INTERVAL %s
                    GROUP BY t.tag_name
                    ORDER BY count DESC
                    LIMIT 10
                """, (interval,))

                top_keywords = []
                for row in cursor.fetchall():
                    top_keywords.append({
                        "keyword": row['tag_name'],
                        "count": row['count']
                    })

                return {
                    "success": True,
                    "data": {
                        "trends": trends,
                        "top_keywords": top_keywords,
                        "period": period,
                        "interval": interval
                    }
                }

        if CACHE_AVAILABLE:
            return get_cached_or_fetch("dashboard", cache_params, fetch_trends, CACHE_TTL.get("dashboard", 60))
        return fetch_trends()

    except Exception as e:
        logger.error(f"트렌드 조회 실패: {e}")
        raise HTTPException(status_code=500, detail="트렌드 데이터 조회 실패")