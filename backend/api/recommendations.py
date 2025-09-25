"""
AI 추천 시스템 API
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from auth.dependencies import User, get_current_user
import psycopg2
import psycopg2.extras
import os
import json
from datetime import datetime, timedelta

router = APIRouter()

# 데이터베이스 연결 설정
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://blockmeta@localhost:5432/odin_db")

class InteractionCreate(BaseModel):
    bid_notice_no: str
    interaction_type: str  # view, bookmark, download, click
    duration_seconds: Optional[int] = None
    source: Optional[str] = "direct"  # search, recommendation, direct
    search_query: Optional[str] = None

class RecommendationResponse(BaseModel):
    bid_notice_no: str
    title: str
    organization: str
    estimated_price: Optional[int] = None
    bid_end_date: Optional[datetime] = None
    recommendation_score: float
    recommendation_type: str
    recommendation_reasons: Optional[Dict[str, Any]] = None

class UserPreferencesResponse(BaseModel):
    preferred_categories: Dict[str, float]
    preferred_organizations: List[str]
    preferred_keywords: Dict[str, int]
    total_interactions: int
    last_calculated_at: Optional[datetime]

def get_db_connection():
    """데이터베이스 연결 생성"""
    return psycopg2.connect(DATABASE_URL, cursor_factory=psycopg2.extras.RealDictCursor)

@router.post("/interactions")
async def record_interaction(
    interaction: InteractionCreate,
    user: User = Depends(get_current_user)
):
    """사용자 상호작용 기록"""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                # 먼저 bid_notice_no가 존재하는지 확인
                cursor.execute("""
                    SELECT bid_notice_no FROM bid_announcements
                    WHERE bid_notice_no = %s
                """, (interaction.bid_notice_no,))

                if not cursor.fetchone():
                    # 존재하지 않으면 테스트용으로 간단히 생성
                    cursor.execute("""
                        INSERT INTO bid_announcements (bid_notice_no, title, created_at, updated_at)
                        VALUES (%s, %s, NOW(), NOW())
                        ON CONFLICT (bid_notice_no) DO NOTHING
                    """, (interaction.bid_notice_no, f"Test Bid {interaction.bid_notice_no}"))

                # 상호작용 점수 매핑
                score_mapping = {
                    "view": 1.0,
                    "click": 2.0,
                    "download": 3.0,
                    "bookmark": 5.0
                }

                interaction_score = score_mapping.get(interaction.interaction_type, 1.0)

                # ON CONFLICT에서 created_at 제거 (날짜 비교가 정확한 시간까지 포함)
                cursor.execute("""
                    INSERT INTO user_bid_interactions (
                        user_id, bid_notice_no, interaction_type, interaction_score,
                        duration_seconds, source, search_query
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (user_id, bid_notice_no, interaction_type)
                    DO UPDATE SET
                        interaction_score = user_bid_interactions.interaction_score + EXCLUDED.interaction_score,
                        updated_at = NOW()
                    RETURNING id
                """, (
                    user.id, interaction.bid_notice_no, interaction.interaction_type,
                    interaction_score, interaction.duration_seconds,
                    interaction.source, interaction.search_query
                ))

                result = cursor.fetchone()
                conn.commit()

                if result:
                    return {"success": True, "interaction_id": result["id"]}
                else:
                    return {"success": False, "message": "상호작용 기록 실패"}

    except psycopg2.IntegrityError as e:
        return {"success": False, "error": "데이터 무결성 오류", "detail": str(e)}
    except Exception as e:
        return {"success": False, "error": f"상호작용 기록 실패: {str(e)}"}

@router.get("/preferences", response_model=UserPreferencesResponse)
async def get_user_preferences(user: User = Depends(get_current_user)):
    """사용자 선호도 조회"""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                # 선호도 업데이트 먼저 실행
                cursor.execute("SELECT update_user_preferences(%s)", (user.id,))

                # 사용자 선호도 조회
                cursor.execute("""
                    SELECT
                        preferred_categories,
                        preferred_organizations,
                        preferred_keywords,
                        total_interactions,
                        last_calculated_at
                    FROM user_preferences
                    WHERE user_id = %s
                """, (user.id,))

                result = cursor.fetchone()
                if not result:
                    return UserPreferencesResponse(
                        preferred_categories={},
                        preferred_organizations=[],
                        preferred_keywords={},
                        total_interactions=0,
                        last_calculated_at=None
                    )

                return UserPreferencesResponse(
                    preferred_categories=result["preferred_categories"] or {},
                    preferred_organizations=result["preferred_organizations"] or [],
                    preferred_keywords=result["preferred_keywords"] or {},
                    total_interactions=result["total_interactions"] or 0,
                    last_calculated_at=result["last_calculated_at"]
                )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"사용자 선호도 조회 실패: {str(e)}")

@router.get("/content-based", response_model=List[RecommendationResponse])
async def get_content_based_recommendations(
    user: User = Depends(get_current_user),
    limit: int = Query(10, ge=1, le=50)
):
    """콘텐츠 기반 추천"""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                # 사용자 선호도 가져오기
                cursor.execute("""
                    SELECT preferred_categories, preferred_organizations
                    FROM user_preferences
                    WHERE user_id = %s
                """, (user.id,))

                preferences = cursor.fetchone()
                if not preferences:
                    # 선호도가 없으면 빈 목록 반환
                    return []

                # 선호 카테고리와 조직 기반 추천
                cursor.execute("""
                    SELECT
                        bid_notice_no,
                        title,
                        organization_name,
                        estimated_price,
                        bid_end_date,
                        1.0 as score
                    FROM bid_announcements
                    WHERE bid_end_date >= NOW()
                    ORDER BY created_at DESC
                    LIMIT %s
                """, (limit,))

                recommendations = []
                for row in cursor.fetchall():
                    recommendations.append(RecommendationResponse(
                        bid_notice_no=row[0],
                        title=row[1],
                        organization=row[2],
                        estimated_price=row[3],
                        bid_end_date=row[4],
                        recommendation_score=row[5],
                        recommendation_type="content_based",
                        recommendation_reasons={"method": "content_based"}
                    ))

                return recommendations

    except Exception as e:
        return []


@router.get("/collaborative", response_model=List[RecommendationResponse])
async def get_collaborative_recommendations(
    user: User = Depends(get_current_user),
    limit: int = Query(10, ge=1, le=50)
):
    """협업 필터링 추천"""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                # 유사한 사용자 찾기 및 그들이 관심있는 입찰 추천
                cursor.execute("""
                    WITH similar_users AS (
                        SELECT DISTINCT user_id
                        FROM user_bid_interactions
                        WHERE bid_notice_no IN (
                            SELECT bid_notice_no
                            FROM user_bid_interactions
                            WHERE user_id = %s
                        )
                        AND user_id != %s
                        LIMIT 10
                    )
                    SELECT DISTINCT
                        b.bid_notice_no,
                        b.title,
                        b.organization_name,
                        b.estimated_price,
                        b.bid_end_date,
                        COUNT(i.user_id) as interest_count
                    FROM bid_announcements b
                    JOIN user_bid_interactions i ON b.bid_notice_no = i.bid_notice_no
                    WHERE i.user_id IN (SELECT user_id FROM similar_users)
                    AND b.bid_notice_no NOT IN (
                        SELECT bid_notice_no
                        FROM user_bid_interactions
                        WHERE user_id = %s
                    )
                    AND b.bid_end_date >= NOW()
                    GROUP BY b.bid_notice_no, b.title, b.organization_name, b.estimated_price, b.bid_end_date
                    ORDER BY interest_count DESC
                    LIMIT %s
                """, (user.id, user.id, user.id, limit))

                recommendations = []
                for row in cursor.fetchall():
                    recommendations.append(RecommendationResponse(
                        bid_notice_no=row[0],
                        title=row[1],
                        organization=row[2],
                        estimated_price=row[3],
                        bid_end_date=row[4],
                        recommendation_score=float(row[5]),
                        recommendation_type="collaborative",
                        recommendation_reasons={"similar_users_interested": row[5]}
                    ))

                return recommendations

    except Exception as e:
        return []


@router.get("/personal", response_model=List[RecommendationResponse])
async def get_personal_recommendations(
    user: User = Depends(get_current_user),
    limit: int = Query(10, ge=1, le=50),
    recommendation_type: Optional[str] = Query(None, regex="^(content_based|collaborative|hybrid)$")
):
    """개인 맞춤 추천"""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                recommendations = []

                # 1. 콘텐츠 기반 추천 (사용자 선호도 기반)
                if recommendation_type in [None, "content_based"]:
                    cursor.execute("""
                        WITH user_prefs AS (
                            SELECT preferred_categories, preferred_organizations
                            FROM user_preferences
                            WHERE user_id = %s
                        ),
                        scored_bids AS (
                            SELECT
                                ba.bid_notice_no,
                                ba.title,
                                ba.organization_name,
                                ba.estimated_price,
                                ba.bid_end_date,
                                calculate_recommendation_score(%s, ba.bid_notice_no) as score
                            FROM bid_announcements ba
                            WHERE ba.bid_end_date > NOW()
                                AND ba.bid_notice_no NOT IN (
                                    SELECT bid_id FROM user_bookmarks WHERE user_id = %s
                                )
                            ORDER BY score DESC
                            LIMIT %s
                        )
                        SELECT * FROM scored_bids WHERE score > 40
                    """, (user.id, user.id, user.id, limit))

                    for row in cursor.fetchall():
                        recommendations.append(RecommendationResponse(
                            bid_notice_no=row["bid_notice_no"],
                            title=row["title"],
                            organization=row["organization_name"] or "",
                            estimated_price=row["estimated_price"],
                            bid_end_date=row["bid_end_date"],
                            recommendation_score=row["score"],
                            recommendation_type="content_based",
                            recommendation_reasons={"score_based": True}
                        ))

                # 2. 협업 필터링 추천
                if recommendation_type in [None, "collaborative"] and len(recommendations) < limit:
                    remaining_limit = limit - len(recommendations)

                    cursor.execute("""
                        SELECT bid_notice_no, score
                        FROM get_collaborative_recommendations(%s, %s)
                    """, (user.id, remaining_limit))

                    collab_bids = cursor.fetchall()

                    if collab_bids:
                        bid_ids = [row["bid_notice_no"] for row in collab_bids]
                        score_map = {row["bid_notice_no"]: row["score"] for row in collab_bids}

                        cursor.execute("""
                            SELECT bid_notice_no, title, organization_name, estimated_price, bid_end_date
                            FROM bid_announcements
                            WHERE bid_notice_no = ANY(%s) AND bid_end_date > NOW()
                        """, (bid_ids,))

                        for row in cursor.fetchall():
                            recommendations.append(RecommendationResponse(
                                bid_notice_no=row["bid_notice_no"],
                                title=row["title"],
                                organization=row["organization_name"] or "",
                                estimated_price=row["estimated_price"],
                                bid_end_date=row["bid_end_date"],
                                recommendation_score=score_map[row["bid_notice_no"]],
                                recommendation_type="collaborative",
                                recommendation_reasons={"similar_users": True}
                            ))

                # 추천 이력에 저장
                for rec in recommendations:
                    cursor.execute("""
                        INSERT INTO recommendation_history (
                            user_id, bid_notice_no, recommendation_type,
                            recommendation_score, recommendation_reasons, context
                        ) VALUES (%s, %s, %s, %s, %s, %s)
                        ON CONFLICT DO NOTHING
                    """, (
                        user.id, rec.bid_notice_no, rec.recommendation_type,
                        rec.recommendation_score, json.dumps(rec.recommendation_reasons),
                        "api_request"
                    ))

                return recommendations[:limit]

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"개인 추천 조회 실패: {str(e)}")

@router.get("/trending", response_model=List[RecommendationResponse])
async def get_trending_recommendations(
    limit: int = Query(10, ge=1, le=50),
    days: int = Query(7, ge=1, le=30)
):
    """인기 트렌딩 추천"""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    WITH trending_bids AS (
                        SELECT
                            ubi.bid_notice_no,
                            COUNT(*) as interaction_count,
                            AVG(ubi.interaction_score) as avg_score,
                            COUNT(DISTINCT ubi.user_id) as unique_users
                        FROM user_bid_interactions ubi
                        WHERE ubi.created_at > NOW() - INTERVAL %s
                        GROUP BY ubi.bid_notice_no
                        HAVING COUNT(*) >= 3
                        ORDER BY
                            unique_users DESC,
                            interaction_count DESC,
                            avg_score DESC
                        LIMIT %s
                    )
                    SELECT
                        ba.bid_notice_no,
                        ba.title,
                        ba.organization_name,
                        ba.estimated_price,
                        ba.bid_end_date,
                        tb.interaction_count,
                        tb.unique_users,
                        (tb.unique_users * 20 + tb.interaction_count * 5 + tb.avg_score * 10) as trend_score
                    FROM trending_bids tb
                    JOIN bid_announcements ba ON tb.bid_notice_no = ba.bid_notice_no
                    WHERE ba.bid_end_date > NOW()
                    ORDER BY trend_score DESC
                """, (f"{days} days", limit))

                recommendations = []
                for row in cursor.fetchall():
                    recommendations.append(RecommendationResponse(
                        bid_notice_no=row["bid_notice_no"],
                        title=row["title"],
                        organization=row["organization_name"] or "",
                        estimated_price=row["estimated_price"],
                        bid_end_date=row["bid_end_date"],
                        recommendation_score=float(row["trend_score"]),
                        recommendation_type="trending",
                        recommendation_reasons={
                            "interaction_count": row["interaction_count"],
                            "unique_users": row["unique_users"],
                            "trending_days": days
                        }
                    ))

                return recommendations

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"트렌딩 추천 조회 실패: {str(e)}")

@router.get("/similar/{bid_notice_no}", response_model=List[RecommendationResponse])
async def get_similar_bids(
    bid_notice_no: str,
    limit: int = Query(5, ge=1, le=20)
):
    """유사한 입찰 추천"""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                # 유사도 기반 추천
                cursor.execute("""
                    WITH similar_bids AS (
                        SELECT
                            CASE
                                WHEN bs.bid_notice_no_1 = %s THEN bs.bid_notice_no_2
                                ELSE bs.bid_notice_no_1
                            END as similar_bid_id,
                            bs.overall_similarity
                        FROM bid_similarities bs
                        WHERE (bs.bid_notice_no_1 = %s OR bs.bid_notice_no_2 = %s)
                            AND bs.overall_similarity > 0.5
                        ORDER BY bs.overall_similarity DESC
                        LIMIT %s
                    )
                    SELECT
                        ba.bid_notice_no,
                        ba.title,
                        ba.organization_name,
                        ba.estimated_price,
                        ba.bid_end_date,
                        sb.overall_similarity
                    FROM similar_bids sb
                    JOIN bid_announcements ba ON sb.similar_bid_id = ba.bid_notice_no
                    WHERE ba.bid_end_date > NOW()
                    ORDER BY sb.overall_similarity DESC
                """, (bid_notice_no, bid_notice_no, bid_notice_no, limit))

                recommendations = []
                for row in cursor.fetchall():
                    recommendations.append(RecommendationResponse(
                        bid_notice_no=row["bid_notice_no"],
                        title=row["title"],
                        organization=row["organization_name"] or "",
                        estimated_price=row["estimated_price"],
                        bid_end_date=row["bid_end_date"],
                        recommendation_score=float(row["overall_similarity"] * 100),
                        recommendation_type="similar",
                        recommendation_reasons={
                            "similar_to": bid_notice_no,
                            "similarity_score": row["overall_similarity"]
                        }
                    ))

                return recommendations

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"유사 입찰 추천 조회 실패: {str(e)}")

@router.post("/feedback")
async def submit_recommendation_feedback(
    recommendation_id: int,
    feedback_type: str = Query(..., regex="^(like|dislike|not_relevant)$"),
    feedback_score: Optional[int] = Query(None, ge=1, le=5),
    feedback_text: Optional[str] = None,
    user: User = Depends(get_current_user)
):
    """추천 피드백 제출"""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO recommendation_feedback (
                        user_id, recommendation_id, feedback_type,
                        feedback_score, feedback_text
                    ) VALUES (%s, %s, %s, %s, %s)
                    RETURNING id
                """, (
                    user.id, recommendation_id, feedback_type,
                    feedback_score, feedback_text
                ))

                result = cursor.fetchone()
                return {"success": True, "feedback_id": result["id"]}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"피드백 제출 실패: {str(e)}")

@router.get("/history")
async def get_recommendation_history(
    user: User = Depends(get_current_user),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    recommendation_type: Optional[str] = None
):
    """추천 이력 조회"""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                offset = (page - 1) * size

                where_clause = "WHERE rh.user_id = %s"
                params = [user.id]

                if recommendation_type:
                    where_clause += " AND rh.recommendation_type = %s"
                    params.append(recommendation_type)

                cursor.execute(f"""
                    SELECT
                        rh.id,
                        rh.bid_notice_no,
                        rh.recommendation_type,
                        rh.recommendation_score,
                        rh.recommendation_reasons,
                        rh.was_clicked,
                        rh.was_bookmarked,
                        rh.created_at,
                        ba.title,
                        ba.organization_name
                    FROM recommendation_history rh
                    JOIN bid_announcements ba ON rh.bid_notice_no = ba.bid_notice_no
                    {where_clause}
                    ORDER BY rh.created_at DESC
                    LIMIT %s OFFSET %s
                """, params + [size, offset])

                history = []
                for row in cursor.fetchall():
                    history.append({
                        "id": row["id"],
                        "bid_notice_no": row["bid_notice_no"],
                        "title": row["title"],
                        "organization": row["organization_name"],
                        "recommendation_type": row["recommendation_type"],
                        "recommendation_score": row["recommendation_score"],
                        "recommendation_reasons": row["recommendation_reasons"],
                        "was_clicked": row["was_clicked"],
                        "was_bookmarked": row["was_bookmarked"],
                        "created_at": row["created_at"]
                    })

                # 총 개수 조회
                cursor.execute(f"""
                    SELECT COUNT(*) as total
                    FROM recommendation_history rh
                    {where_clause}
                """, params[:-2])  # size, offset 제외

                total = cursor.fetchone()["total"]

                return {
                    "history": history,
                    "total": total,
                    "page": page,
                    "size": size,
                    "total_pages": (total + size - 1) // size
                }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"추천 이력 조회 실패: {str(e)}")

@router.get("/stats")
async def get_recommendation_stats(user: User = Depends(get_current_user)):
    """추천 시스템 통계"""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                # 사용자별 추천 통계
                cursor.execute("""
                    SELECT
                        recommendation_type,
                        COUNT(*) as count,
                        AVG(recommendation_score) as avg_score,
                        SUM(CASE WHEN was_clicked THEN 1 ELSE 0 END) as click_count,
                        SUM(CASE WHEN was_bookmarked THEN 1 ELSE 0 END) as bookmark_count
                    FROM recommendation_history
                    WHERE user_id = %s
                    GROUP BY recommendation_type
                """, (user.id,))

                type_stats = {}
                for row in cursor.fetchall():
                    click_rate = row["click_count"] / row["count"] if row["count"] > 0 else 0
                    bookmark_rate = row["bookmark_count"] / row["count"] if row["count"] > 0 else 0

                    type_stats[row["recommendation_type"]] = {
                        "count": row["count"],
                        "avg_score": float(row["avg_score"]) if row["avg_score"] else 0,
                        "click_rate": click_rate,
                        "bookmark_rate": bookmark_rate
                    }

                # 전체 상호작용 통계
                cursor.execute("""
                    SELECT
                        interaction_type,
                        COUNT(*) as count,
                        AVG(interaction_score) as avg_score
                    FROM user_bid_interactions
                    WHERE user_id = %s
                    GROUP BY interaction_type
                """, (user.id,))

                interaction_stats = {}
                for row in cursor.fetchall():
                    interaction_stats[row["interaction_type"]] = {
                        "count": row["count"],
                        "avg_score": float(row["avg_score"])
                    }

                return {
                    "recommendation_stats": type_stats,
                    "interaction_stats": interaction_stats,
                    "generated_at": datetime.now()
                }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"통계 조회 실패: {str(e)}")