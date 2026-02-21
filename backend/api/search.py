"""
검색 API
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List
from datetime import datetime, timezone
from database import get_db_connection
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
                # Build OR conditions for each expanded keyword
                like_conditions = []
                for keyword in expanded[:10]:  # Limit to 10 expanded terms
                    like_conditions.append("(b.title ILIKE %s OR b.organization_name ILIKE %s OR t.tag_name ILIKE %s)")
                    kw = f"%{keyword}%"
                    params.extend([kw, kw, kw])
                conditions.append("(" + " OR ".join(like_conditions) + ")")
            else:
                # No ontology match - use original keyword
                conditions.append(
                    "(b.title ILIKE %s OR b.organization_name ILIKE %s OR t.tag_name ILIKE %s)"
                )
                search_term = f"%{q}%"
                params.extend([search_term, search_term, search_term])
        else:
            # Ontology not available - use original
            conditions.append(
                "(b.title ILIKE %s OR b.organization_name ILIKE %s OR t.tag_name ILIKE %s)"
            )
            search_term = f"%{q}%"
            params.extend([search_term, search_term, search_term])

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
            cursor = conn.cursor()

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
                {data_from}
                WHERE {where_sql}
                ORDER BY b.created_at DESC
                LIMIT %s OFFSET %s
            """

            cursor.execute(data_query, base_params + [limit, (page - 1) * limit])
            rows = cursor.fetchall()

            # bid_notice_no 목록 추출
            bid_nos = [row[0] for row in rows]

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
                    bno = info_row[0]
                    cat = info_row[1]
                    if bno not in extracted_map:
                        extracted_map[bno] = {}
                    if cat not in extracted_map[bno]:
                        extracted_map[bno][cat] = {}
                    extracted_map[bno][cat][info_row[2]] = info_row[3]

            # tags를 한 번에 조회 (N+1 → 1 쿼리)
            tags_map = {}
            if bid_nos:
                cursor.execute("""
                    SELECT btr.bid_notice_no, ARRAY_AGG(t.tag_name)
                    FROM bid_tags t
                    JOIN bid_tag_relations btr ON t.tag_id = btr.tag_id
                    WHERE btr.bid_notice_no = ANY(%s)
                    GROUP BY btr.bid_notice_no
                """, (bid_nos,))
                for tag_row in cursor.fetchall():
                    tags_map[tag_row[0]] = tag_row[1] if tag_row[1] else []

            # 결과 조합
            results = []
            for row in rows:
                bid_notice_no = row[0]

                results.append({
                    "bid_notice_no": row[0],
                    "title": row[1],
                    "organization_name": row[2],
                    "department_name": row[3],
                    "estimated_price": row[4],
                    "bid_start_date": row[5].isoformat() if row[5] else None,
                    "bid_end_date": row[6].isoformat() if row[6] else None,
                    "status": row[7] or row[13],
                    "bid_method": row[8],
                    "contract_method": row[9],
                    "region_restriction": row[10],
                    "remaining_days": row[12],
                    "tags": tags_map.get(bid_notice_no, []),
                    "extracted_info": extracted_map.get(bid_notice_no, {})
                })

            # 전체 개수 조회 - 데이터 쿼리와 동일한 WHERE 절 재사용
            if q:
                count_query = f"""
                    SELECT COUNT(DISTINCT b.bid_notice_no)
                    FROM bid_announcements b
                    LEFT JOIN bid_tag_relations btr ON b.bid_notice_no = btr.bid_notice_no
                    LEFT JOIN bid_tags t ON btr.tag_id = t.tag_id
                    WHERE {where_sql}
                """
            else:
                count_query = f"""
                    SELECT COUNT(*) FROM bid_announcements b
                    WHERE {where_sql}
                """

            cursor.execute(count_query, base_params)
            total = cursor.fetchone()[0]

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
        raise HTTPException(status_code=500, detail="검색 처리 중 오류가 발생했습니다")


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
        raise HTTPException(status_code=422, detail="검색어는 500자를 초과할 수 없습니다")

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
            cursor = conn.cursor()

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
                    "bid_notice_no": row[0],
                    "title": row[1],
                    "organization_name": row[2],
                    "estimated_price": row[3],
                    "bid_end_date": row[4].isoformat() if row[4] else None,
                    "created_at": row[5].isoformat() if row[5] else None
                })

            cursor.execute("SELECT COUNT(*) FROM bid_announcements")
            total = cursor.fetchone()[0]

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
        raise HTTPException(status_code=500, detail="목록 조회 중 오류가 발생했습니다")


@router.get("/bids/{bid_notice_no}")
async def get_bid_detail(bid_notice_no: str):
    """입찰 상세 조회"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

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
                raise HTTPException(status_code=404, detail="입찰 공고를 찾을 수 없습니다")

            return {
                "success": True,
                "data": {
                    "bid_notice_no": row[0],
                    "title": row[1],
                    "organization_name": row[2],
                    "department_name": row[3],
                    "estimated_price": row[4],
                    "bid_start_date": row[5].isoformat() if row[5] else None,
                    "bid_end_date": row[6].isoformat() if row[6] else None,
                    "announcement_date": row[7].isoformat() if row[7] else None,
                    "bid_method": row[8],
                    "contract_method": row[9],
                    "officer_name": row[10],
                    "officer_phone": row[11],
                    "officer_email": row[12],
                    "detail_page_url": row[13],
                    "created_at": row[14].isoformat() if row[14] else None,
                    "updated_at": row[15].isoformat() if row[15] else None
                }
            }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"상세 조회 실패: {e}")
        raise HTTPException(status_code=500, detail="상세 조회 중 오류가 발생했습니다")