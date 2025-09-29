"""
대시보드 API - 실제 데이터베이스 연동
"""

from fastapi import APIRouter, HTTPException, Query, Depends
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from database import get_db_connection
from auth.dependencies import get_current_user_optional, get_current_user, User
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("/stats")
async def get_dashboard_stats(user: User = Depends(get_current_user)):
    """대시보드 전체 통계"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            # 전체 입찰 수
            cursor.execute("SELECT COUNT(*) FROM bid_announcements")
            total_bids = cursor.fetchone()[0]

            # 활성 입찰 수
            cursor.execute("""
                SELECT COUNT(*) FROM bid_announcements
                WHERE bid_end_date >= NOW()
            """)
            active_bids = cursor.fetchone()[0]

            # 총 예정가격
            cursor.execute("""
                SELECT COALESCE(SUM(estimated_price), 0)
                FROM bid_announcements
                WHERE estimated_price IS NOT NULL
            """)
            total_price = cursor.fetchone()[0]

            # 평균 예정가격
            cursor.execute("""
                SELECT COALESCE(AVG(estimated_price), 0)
                FROM bid_announcements
                WHERE estimated_price IS NOT NULL
            """)
            avg_price = cursor.fetchone()[0]

            return {
                "total_bids": total_bids,
                "active_bids": active_bids,
                "total_price": float(total_price),
                "average_price": float(avg_price),
                "last_updated": datetime.now().isoformat()
            }

    except Exception as e:
        logger.error(f"대시보드 통계 조회 실패: {e}")
        raise HTTPException(status_code=500, detail="대시보드 통계 조회 실패")


@router.get("/active-bids")
async def get_active_bids(user: User = Depends(get_current_user)):
    """활성 입찰 수 조회"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT COUNT(*) FROM bid_announcements
                WHERE bid_end_date >= NOW()
            """)
            count = cursor.fetchone()[0]
            return {"active_bids": count}
    except Exception as e:
        logger.error(f"활성 입찰 조회 실패: {e}")
        raise HTTPException(status_code=500, detail="활성 입찰 조회 실패")


@router.get("/total-price")
async def get_total_price(user: User = Depends(get_current_user)):
    """총 예정가격 조회"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT COALESCE(SUM(estimated_price), 0)
                FROM bid_announcements
                WHERE estimated_price IS NOT NULL
            """)
            total = cursor.fetchone()[0]
            return {"total_price": float(total)}
    except Exception as e:
        logger.error(f"총 예정가격 조회 실패: {e}")
        raise HTTPException(status_code=500, detail="총 예정가격 조회 실패")


@router.get("/statistics")
async def get_dashboard_statistics(days: int = Query(7, ge=1, le=30)):
    """대시보드 통계 데이터 (차트용)"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            # 1. 일별 입찰 통계 (최근 N일)
            cursor.execute("""
                SELECT
                    DATE(created_at) as date,
                    COUNT(*) as count
                FROM bid_announcements
                WHERE created_at >= CURRENT_DATE - INTERVAL '%s days'
                GROUP BY DATE(created_at)
                ORDER BY date ASC
            """, (days,))

            daily_stats = []
            for row in cursor.fetchall():
                daily_stats.append({
                    "date": row[0].isoformat(),
                    "count": row[1]
                })

            # 2. 카테고리별 분포 (태그 기반)
            cursor.execute("""
                SELECT
                    t.tag_name as category,
                    COUNT(DISTINCT btr.bid_notice_no) as count
                FROM bid_tags t
                JOIN bid_tag_relations btr ON t.tag_id = btr.tag_id
                JOIN bid_announcements b ON btr.bid_notice_no = b.bid_notice_no
                WHERE b.created_at >= CURRENT_DATE - INTERVAL '%s days'
                GROUP BY t.tag_name
                ORDER BY count DESC
                LIMIT 10
            """, (days,))

            category_distribution = []
            for row in cursor.fetchall():
                category_distribution.append({
                    "category": row[0],
                    "count": row[1],
                    "percentage": 0  # 계산은 프론트에서
                })

            # 퍼센트 계산
            total = sum(item["count"] for item in category_distribution)
            if total > 0:
                for item in category_distribution:
                    item["percentage"] = round((item["count"] / total) * 100, 1)

            return {
                "daily_stats": daily_stats,
                "category_distribution": category_distribution,
                "period_days": days
            }

    except Exception as e:
        logger.error(f"통계 데이터 조회 실패: {e}")
        raise HTTPException(status_code=500, detail="통계 데이터 조회 실패")


@router.get("/closed-bids")
async def get_closed_bids(user: User = Depends(get_current_user)):
    """마감 입찰 수 조회"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT COUNT(*) FROM bid_announcements
                WHERE bid_end_date < NOW()
            """)
            count = cursor.fetchone()[0]
            return {"closed_bids": count}
    except Exception as e:
        logger.error(f"마감 입찰 조회 실패: {e}")
        raise HTTPException(status_code=500, detail="마감 입찰 조회 실패")


@router.get("/trends")
async def get_trends(user: User = Depends(get_current_user)):
    """일별 추이 데이터"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT
                    DATE(created_at) as date,
                    COUNT(*) as count
                FROM bid_announcements
                WHERE created_at >= CURRENT_DATE - INTERVAL '7 days'
                GROUP BY DATE(created_at)
                ORDER BY date
            """)

            trends = []
            for row in cursor.fetchall():
                trends.append({
                    "date": row[0].isoformat(),
                    "count": row[1]
                })

            return {"trends": trends}
    except Exception as e:
        logger.error(f"추이 데이터 조회 실패: {e}")
        raise HTTPException(status_code=500, detail="추이 데이터 조회 실패")


@router.get("/overview")
async def get_dashboard_overview(user: Optional[User] = Depends(get_current_user_optional)):
    """대시보드 개요 데이터 (실제 DB)"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            # 전체 입찰 수
            cursor.execute("SELECT COUNT(*) FROM bid_announcements")
            total_bids = cursor.fetchone()[0]

            # 활성 입찰 수 (마감일이 지나지 않은)
            cursor.execute("""
                SELECT COUNT(*) FROM bid_announcements
                WHERE bid_end_date >= NOW()
            """)
            active_bids = cursor.fetchone()[0]

            # 마감된 입찰 수
            expired_bids = total_bids - active_bids

            # 총 예정가격 (null 제외)
            cursor.execute("""
                SELECT COALESCE(SUM(estimated_price), 0)
                FROM bid_announcements
                WHERE estimated_price IS NOT NULL
            """)
            total_price = cursor.fetchone()[0]

            # 평균 경쟁률 (더미 - 향후 실제 데이터로)
            avg_competition_rate = 7.5

            # 오늘 신규 입찰
            cursor.execute("""
                SELECT COUNT(*) FROM bid_announcements
                WHERE created_at >= CURRENT_DATE
            """)
            today_new = cursor.fetchone()[0]

            # 이번 주 신규 입찰
            cursor.execute("""
                SELECT COUNT(*) FROM bid_announcements
                WHERE created_at >= date_trunc('week', CURRENT_DATE)
            """)
            week_new = cursor.fetchone()[0]

            # 마감 임박 (3일 이내)
            cursor.execute("""
                SELECT COUNT(*) FROM bid_announcements
                WHERE bid_end_date BETWEEN NOW() AND NOW() + INTERVAL '3 days'
            """)
            deadline_soon = cursor.fetchone()[0]

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
                    "bookmarks": user_row[0],
                    "active_bookmarks": user_row[1],
                    "alerts": 0  # 알림 시스템 구현 후
                }

            return {
                "total_bids": total_bids,
                "active_bids": active_bids,
                "expired_bids": expired_bids,
                "total_price": float(total_price),
                "average_competition_rate": avg_competition_rate,
                "today_new": today_new,
                "week_new": week_new,
                "deadline_soon": deadline_soon,
                "user_stats": user_stats,
                "last_updated": datetime.now().isoformat()
            }

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
        with get_db_connection() as conn:
            cursor = conn.cursor()

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
                    "date": row[0].isoformat(),
                    "count": row[1],
                    "total_price": float(row[2])
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
                total_count += row[1]

            # 퍼센트 계산하여 추가
            for row in rows:
                percentage = round((row[1] / total_count * 100), 1) if total_count > 0 else 0
                category_distribution.append({
                    "category": row[0],
                    "count": row[1],
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
                    "organization": row[0],
                    "count": row[1],
                    "total_price": float(row[2])
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
                    "range": row[0],
                    "count": row[1]
                })

            return {
                "daily_stats": daily_stats,
                "category_distribution": category_distribution,
                "organization_stats": organization_stats,
                "price_distribution": price_distribution,
                "period": {
                    "days": days,
                    "start_date": (datetime.now() - timedelta(days=days)).date().isoformat(),
                    "end_date": datetime.now().date().isoformat()
                }
            }

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
            cursor = conn.cursor()

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
                hours = row[5]
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
                    "bid_id": row[0],
                    "title": row[1],
                    "organization": row[2],
                    "price": float(row[3]) if row[3] else None,
                    "deadline": row[4].isoformat(),
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

                bookmarked_ids = {row[0] for row in cursor.fetchall()}
                for deadline in deadlines:
                    deadline["is_bookmarked"] = deadline["bid_id"] in bookmarked_ids

            return {
                "data": deadlines,  # 프론트엔드가 data 필드를 기대함
                "deadlines": deadlines,
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
            cursor = conn.cursor()

            # 사용자 북마크 기반 추천 (간단한 로직)
            # 1. 사용자가 북마크한 입찰의 기관들 찾기
            cursor.execute("""
                SELECT DISTINCT organization_name
                FROM user_bookmarks
                WHERE user_id = %s AND organization_name IS NOT NULL
                LIMIT 10
            """, (user.id,))

            user_orgs = [row[0] for row in cursor.fetchall()]

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
                        "bid_id": row[0],
                        "title": row[1],
                        "organization": row[2],
                        "price": float(row[3]) if row[3] else None,
                        "deadline": row[4].isoformat() if row[4] else None,
                        "score": 85,  # 더미 점수
                        "reason": f"{row[2]}의 다른 입찰",
                        "is_bookmarked": row[5]
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
                        "bid_id": row[0],
                        "title": row[1],
                        "organization": row[2],
                        "price": float(row[3]) if row[3] else None,
                        "deadline": row[4].isoformat() if row[4] else None,
                        "score": 70,
                        "reason": "최신 입찰",
                        "is_bookmarked": row[5]
                    })

            return {
                "recommendations": recommendations[:10],
                "total": len(recommendations),
                "algorithm": "bookmark_based_v1"
            }

    except Exception as e:
        logger.error(f"추천 조회 실패: {e}")
        raise HTTPException(status_code=500, detail="추천 데이터 조회 실패")


@router.get("/trends")
async def get_bid_trends(
    period: str = Query("week", regex="^(day|week|month|year)$"),
    user: Optional[User] = Depends(get_current_user_optional)
):
    """입찰 트렌드 분석"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

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
                    "period": str(row[0]),
                    "count": row[1]
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
                    "keyword": row[0],
                    "count": row[1]
                })

            return {
                "trends": trends,
                "top_keywords": top_keywords,
                "period": period,
                "interval": interval
            }

    except Exception as e:
        logger.error(f"트렌드 조회 실패: {e}")
        raise HTTPException(status_code=500, detail="트렌드 데이터 조회 실패")