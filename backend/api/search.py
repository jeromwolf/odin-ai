"""
검색 API
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List
from datetime import datetime, timezone
from database import get_db_connection
from psycopg2.extras import RealDictCursor
from errors import ErrorCode, ApiError
import logging

try:
    from cache import get_cached_or_fetch, CACHE_TTL
    CACHE_AVAILABLE = True
except ImportError:
    CACHE_AVAILABLE = False

try:
    from services.ontology_service import expand_search_terms
    ONTOLOGY_AVAILABLE = True
except ImportError:
    ONTOLOGY_AVAILABLE = False

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["search"])


def _build_search_where(
    q: Optional[str],
    start_date: Optional[str],
    end_date: Optional[str],
    min_price: Optional[int],
    max_price: Optional[int],
    organization: Optional[str],
    status: Optional[str],
) -> tuple:
    """검색 WHERE 절과 파라미터를 구성하는 헬퍼 함수.

    키워드(q)가 있을 때는 bid_tag_relations / bid_tags JOIN이 필요하므로
    호출 측에서 해당 JOIN을 포함한 FROM 절을 사용해야 합니다.

    Returns:
        (where_sql, params) - where_sql은 AND 구분 조건들의 문자열,
                              params는 대응하는 바인딩 값 목록.
    """
    conditions = []
    params = []

    if q:
        if ONTOLOGY_AVAILABLE:
            expanded = expand_search_terms(q)
            if expanded:
                like_conditions = []
                for keyword in expanded[:10]:
                    # ILIKE: 부분 매칭 (한국어 형태소 대응, pg_trgm GIN 인덱스 활용)
                    # FTS: 전체 단어 매칭 (GIN FTS 인덱스 활용)
                    like_conditions.append(
                        "(b.title ILIKE %s OR b.organization_name ILIKE %s "
                        "OR t.tag_name ILIKE %s "
                        "OR to_tsvector('simple', b.title) @@ plainto_tsquery('simple', %s))"
                    )
                    kw = f"%{keyword}%"
                    params.extend([kw, kw, kw, keyword])
                conditions.append("(" + " OR ".join(like_conditions) + ")")
            else:
                conditions.append(
                    "(b.title ILIKE %s OR b.organization_name ILIKE %s "
                    "OR t.tag_name ILIKE %s "
                    "OR to_tsvector('simple', b.title) @@ plainto_tsquery('simple', %s))"
                )
                search_term = f"%{q}%"
                params.extend([search_term, search_term, search_term, q])
        else:
            conditions.append(
                "(b.title ILIKE %s OR b.organization_name ILIKE %s "
                "OR t.tag_name ILIKE %s "
                "OR to_tsvector('simple', b.title) @@ plainto_tsquery('simple', %s))"
            )
            search_term = f"%{q}%"
            params.extend([search_term, search_term, search_term, q])

    if start_date:
        conditions.append("b.bid_start_date >= %s")
        params.append(start_date)

    if end_date:
        conditions.append("b.bid_end_date <= %s")
        params.append(end_date)

    if min_price is not None:
        conditions.append("b.estimated_price >= %s")
        params.append(min_price)

    if max_price is not None:
        conditions.append("b.estimated_price <= %s")
        params.append(max_price)

    if organization:
        conditions.append("b.organization_name ILIKE %s")
        params.append(f"%{organization}%")

    if status == "active":
        conditions.append("b.bid_end_date >= NOW()")
    elif status == "closed":
        conditions.append("b.bid_end_date < NOW()")

    where_sql = " AND ".join(conditions) if conditions else "1=1"
    return where_sql, params


def _search_bids_from_db(
    q: Optional[str],
    start_date: Optional[str],
    end_date: Optional[str],
    min_price: Optional[int],
    max_price: Optional[int],
    organization: Optional[str],
    status: Optional[str],
    page: int,
    limit: int,
) -> dict:
    """DB에서 직접 입찰 공고를 검색하는 내부 함수."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)

            # WHERE 절 공통 구성 (데이터 쿼리와 카운트 쿼리에서 공유)
            where_sql, base_params = _build_search_where(
                q, start_date, end_date, min_price, max_price, organization, status
            )

            # 키워드 검색 시 태그 JOIN 포함, 그 외에는 간단한 FROM
            if q:
                data_from = """
                    FROM bid_announcements b
                    LEFT JOIN bid_tag_relations btr ON b.bid_notice_no = btr.bid_notice_no
                    LEFT JOIN bid_tags t ON btr.tag_id = t.tag_id
                """
            else:
                data_from = "FROM bid_announcements b"

            # 키워드 검색 시 FTS 관련도 점수로 정렬, 그 외에는 최신순
            if q:
                # ts_rank: FTS 매칭 점수, similarity: pg_trgm 유사도 (0~1)
                # 두 점수를 결합하여 관련도 순으로 정렬
                rank_select = """,
                    ts_rank(to_tsvector('simple', b.title), plainto_tsquery('simple', %s)) AS fts_rank,
                    similarity(b.title, %s) AS trgm_rank"""
                rank_params = [q, q]
                order_by = "ORDER BY (fts_rank * 2 + trgm_rank) DESC, b.created_at DESC"
            else:
                rank_select = ""
                rank_params = []
                order_by = "ORDER BY b.created_at DESC"

            data_query = f"""
                SELECT DISTINCT
                    b.bid_notice_no,
                    b.title,
                    b.organization_name,
                    b.department_name,
                    b.estimated_price,
                    b.bid_start_date,
                    b.bid_end_date,
                    b.status,
                    b.bid_method,
                    b.contract_method,
                    b.region_restriction,
                    b.created_at,
                    CASE WHEN b.bid_end_date >= NOW() THEN EXTRACT(DAY FROM b.bid_end_date - NOW())::int ELSE NULL END as remaining_days,
                    CASE WHEN b.bid_end_date >= NOW() THEN 'active' ELSE 'closed' END as computed_status
                    {rank_select}
                {data_from}
                WHERE {where_sql}
                {order_by}
                LIMIT %s OFFSET %s
            """

            cursor.execute(data_query, rank_params + base_params + [limit, (page - 1) * limit])
            rows = cursor.fetchall()

            # bid_notice_no 목록 추출
            bid_nos = [row['bid_notice_no'] for row in rows]

            # extracted_info를 한 번에 조회 (N+1 → 1 쿼리)
            extracted_map = {}
            if bid_nos:
                cursor.execute("""
                    SELECT bid_notice_no, info_category, field_name, field_value
                    FROM bid_extracted_info
                    WHERE bid_notice_no = ANY(%s)
                    AND info_category IN ('requirements', 'contract_details', 'prices')
                """, (bid_nos,))
                for info_row in cursor.fetchall():
                    bno = info_row['bid_notice_no']
                    cat = info_row['info_category']
                    if bno not in extracted_map:
                        extracted_map[bno] = {}
                    if cat not in extracted_map[bno]:
                        extracted_map[bno][cat] = {}
                    extracted_map[bno][cat][info_row['field_name']] = info_row['field_value']

            # tags를 한 번에 조회 (N+1 → 1 쿼리)
            tags_map = {}
            if bid_nos:
                cursor.execute("""
                    SELECT btr.bid_notice_no, ARRAY_AGG(t.tag_name) AS tag_names
                    FROM bid_tags t
                    JOIN bid_tag_relations btr ON t.tag_id = btr.tag_id
                    WHERE btr.bid_notice_no = ANY(%s)
                    GROUP BY btr.bid_notice_no
                """, (bid_nos,))
                for tag_row in cursor.fetchall():
                    tags_map[tag_row['bid_notice_no']] = tag_row['tag_names'] if tag_row['tag_names'] else []

            # 결과 조합
            results = []
            for row in rows:
                bid_notice_no = row['bid_notice_no']

                results.append({
                    "bid_notice_no": row['bid_notice_no'],
                    "title": row['title'],
                    "organization_name": row['organization_name'],
                    "department_name": row['department_name'],
                    "estimated_price": row['estimated_price'],
                    "bid_start_date": row['bid_start_date'].isoformat() if row['bid_start_date'] else None,
                    "bid_end_date": row['bid_end_date'].isoformat() if row['bid_end_date'] else None,
                    "status": row['status'] or row['computed_status'],
                    "bid_method": row['bid_method'],
                    "contract_method": row['contract_method'],
                    "region_restriction": row['region_restriction'],
                    "remaining_days": row['remaining_days'],
                    "tags": tags_map.get(bid_notice_no, []),
                    "extracted_info": extracted_map.get(bid_notice_no, {})
                })

            # 전체 개수 조회 - 데이터 쿼리와 동일한 WHERE 절 재사용
            if q:
                count_query = f"""
                    SELECT COUNT(DISTINCT b.bid_notice_no) AS total_count
                    FROM bid_announcements b
                    LEFT JOIN bid_tag_relations btr ON b.bid_notice_no = btr.bid_notice_no
                    LEFT JOIN bid_tags t ON btr.tag_id = t.tag_id
                    WHERE {where_sql}
                """
            else:
                count_query = f"""
                    SELECT COUNT(*) AS total_count FROM bid_announcements b
                    WHERE {where_sql}
                """

            cursor.execute(count_query, base_params)
            total = cursor.fetchone()['total_count']

            return {
                "success": True,
                "data": results,
                "total": total,
                "page": page,
                "limit": limit,
                "total_pages": (total + limit - 1) // limit
            }

    except Exception as e:
        logger.error(f"검색 실패: {e}")
        raise ApiError(500, ErrorCode.SEARCH_FAILED, "검색 처리 중 오류가 발생했습니다")


@router.get("/search")
async def search_bids(
    q: Optional[str] = Query(None, max_length=500, description="검색 키워드 (최대 500자)"),
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    min_price: Optional[int] = None,
    max_price: Optional[int] = None,
    organization: Optional[str] = None,
    status: Optional[str] = None,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100)
):
    """입찰 공고 검색"""

    # 500자 제한 검증 (Query에서 이미 처리되지만 명시적으로 확인)
    if q and len(q) > 500:
        raise ApiError(422, ErrorCode.SEARCH_QUERY_TOO_LONG, "검색어는 500자를 초과할 수 없습니다")

    # 캐시 키 생성
    cache_params = {
        "q": q, "start_date": start_date, "end_date": end_date,
        "min_price": min_price, "max_price": max_price,
        "organization": organization, "status": status,
        "page": page, "limit": limit
    }

    if CACHE_AVAILABLE:
        def fetch_from_db():
            return _search_bids_from_db(
                q, start_date, end_date, min_price, max_price,
                organization, status, page, limit
            )
        return get_cached_or_fetch("search", cache_params, fetch_from_db, CACHE_TTL.get("search", 300))

    return _search_bids_from_db(
        q, start_date, end_date, min_price, max_price,
        organization, status, page, limit
    )


@router.get("/bids")
async def list_bids(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    sort: str = Query("created_at", regex="^(created_at|bid_end_date|estimated_price)$"),
    order: str = Query("desc", regex="^(asc|desc)$")
):
    """입찰 목록 조회"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)

            # SQL Injection 방어: whitelist 매핑
            SORT_COLUMNS = {
                "created_at": "created_at",
                "bid_end_date": "bid_end_date",
                "estimated_price": "estimated_price"
            }
            ORDER_DIRS = {
                "asc": "ASC",
                "desc": "DESC"
            }

            safe_sort = SORT_COLUMNS.get(sort, "created_at")
            safe_order = ORDER_DIRS.get(order, "DESC")

            query = f"""
                SELECT
                    bid_notice_no,
                    title,
                    organization_name,
                    estimated_price,
                    bid_end_date,
                    created_at
                FROM bid_announcements
                ORDER BY {safe_sort} {safe_order}
                LIMIT %s OFFSET %s
            """

            cursor.execute(query, (limit, (page - 1) * limit))

            results = []
            for row in cursor.fetchall():
                results.append({
                    "bid_notice_no": row['bid_notice_no'],
                    "title": row['title'],
                    "organization_name": row['organization_name'],
                    "estimated_price": row['estimated_price'],
                    "bid_end_date": row['bid_end_date'].isoformat() if row['bid_end_date'] else None,
                    "created_at": row['created_at'].isoformat() if row['created_at'] else None
                })

            cursor.execute("SELECT COUNT(*) AS total_count FROM bid_announcements")
            total = cursor.fetchone()['total_count']

            return {
                "success": True,
                "data": results,
                "total": total,
                "page": page,
                "limit": limit,
                "total_pages": (total + limit - 1) // limit
            }

    except Exception as e:
        logger.error(f"목록 조회 실패: {e}")
        raise ApiError(500, ErrorCode.SEARCH_FAILED, "목록 조회 중 오류가 발생했습니다")


@router.get("/bids/{bid_notice_no}")
async def get_bid_detail(bid_notice_no: str):
    """입찰 상세 조회"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)

            cursor.execute("""
                SELECT
                    bid_notice_no,
                    title,
                    organization_name,
                    department_name,
                    estimated_price,
                    bid_start_date,
                    bid_end_date,
                    announcement_date,
                    bid_method,
                    contract_method,
                    officer_name,
                    officer_phone,
                    officer_email,
                    detail_page_url,
                    created_at,
                    updated_at
                FROM bid_announcements
                WHERE bid_notice_no = %s
            """, (bid_notice_no,))

            row = cursor.fetchone()
            if not row:
                raise ApiError(404, ErrorCode.RESOURCE_NOT_FOUND, "입찰 공고를 찾을 수 없습니다")

            return {
                "success": True,
                "data": {
                    "bid_notice_no": row['bid_notice_no'],
                    "title": row['title'],
                    "organization_name": row['organization_name'],
                    "department_name": row['department_name'],
                    "estimated_price": row['estimated_price'],
                    "bid_start_date": row['bid_start_date'].isoformat() if row['bid_start_date'] else None,
                    "bid_end_date": row['bid_end_date'].isoformat() if row['bid_end_date'] else None,
                    "announcement_date": row['announcement_date'].isoformat() if row['announcement_date'] else None,
                    "bid_method": row['bid_method'],
                    "contract_method": row['contract_method'],
                    "officer_name": row['officer_name'],
                    "officer_phone": row['officer_phone'],
                    "officer_email": row['officer_email'],
                    "detail_page_url": row['detail_page_url'],
                    "created_at": row['created_at'].isoformat() if row['created_at'] else None,
                    "updated_at": row['updated_at'].isoformat() if row['updated_at'] else None
                }
            }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"상세 조회 실패: {e}")
        raise ApiError(500, ErrorCode.SERVER_ERROR, "상세 조회 중 오류가 발생했습니다")