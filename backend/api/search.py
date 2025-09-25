"""
검색 API
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List
from datetime import datetime
from database import get_db_connection
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["search"])


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

    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            # 기본 쿼리
            query = """
                SELECT
                    bid_notice_no,
                    title,
                    organization_name,
                    department_name,
                    estimated_price,
                    bid_start_date,
                    bid_end_date,
                    status
                FROM bid_announcements
                WHERE 1=1
            """

            params = []

            # 키워드 검색
            if q:
                query += " AND (title ILIKE %s OR organization_name ILIKE %s)"
                params.extend([f"%{q}%", f"%{q}%"])

            # 날짜 범위
            if start_date:
                query += " AND bid_start_date >= %s"
                params.append(start_date)

            if end_date:
                query += " AND bid_end_date <= %s"
                params.append(end_date)

            # 가격 범위
            if min_price is not None:
                query += " AND estimated_price >= %s"
                params.append(min_price)

            if max_price is not None:
                query += " AND estimated_price <= %s"
                params.append(max_price)

            # 기관명
            if organization:
                query += " AND organization_name ILIKE %s"
                params.append(f"%{organization}%")

            # 상태
            if status:
                if status == "active":
                    query += " AND bid_end_date >= NOW()"
                elif status == "closed":
                    query += " AND bid_end_date < NOW()"

            # 정렬 및 페이지네이션
            query += " ORDER BY created_at DESC"
            query += " LIMIT %s OFFSET %s"
            params.extend([limit, (page - 1) * limit])

            cursor.execute(query, params)
            results = []

            for row in cursor.fetchall():
                results.append({
                    "bid_notice_no": row[0],
                    "title": row[1],
                    "organization_name": row[2],
                    "department_name": row[3],
                    "estimated_price": row[4],
                    "bid_start_date": row[5].isoformat() if row[5] else None,
                    "bid_end_date": row[6].isoformat() if row[6] else None,
                    "status": row[7] or ("active" if row[6] and row[6] >= datetime.now() else "closed")
                })

            # 전체 개수 조회
            count_query = """
                SELECT COUNT(*) FROM bid_announcements WHERE 1=1
            """
            count_params = []

            if q:
                count_query += " AND (title ILIKE %s OR organization_name ILIKE %s)"
                count_params.extend([f"%{q}%", f"%{q}%"])

            if start_date:
                count_query += " AND bid_start_date >= %s"
                count_params.append(start_date)

            if end_date:
                count_query += " AND bid_end_date <= %s"
                count_params.append(end_date)

            if min_price is not None:
                count_query += " AND estimated_price >= %s"
                count_params.append(min_price)

            if max_price is not None:
                count_query += " AND estimated_price <= %s"
                count_params.append(max_price)

            if organization:
                count_query += " AND organization_name ILIKE %s"
                count_params.append(f"%{organization}%")

            if status:
                if status == "active":
                    count_query += " AND bid_end_date >= NOW()"
                elif status == "closed":
                    count_query += " AND bid_end_date < NOW()"

            cursor.execute(count_query, count_params)
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

            query = f"""
                SELECT
                    bid_notice_no,
                    title,
                    organization_name,
                    estimated_price,
                    bid_end_date,
                    created_at
                FROM bid_announcements
                ORDER BY {sort} {order.upper()}
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