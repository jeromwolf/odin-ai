"""
북마크 API 엔드포인트
"""

from fastapi import APIRouter, HTTPException, Query, Depends
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel
import logging
import json

from database import get_db_connection
from auth.dependencies import get_current_user, User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/bookmarks", tags=["bookmarks"])


class BookmarkCreate(BaseModel):
    """북마크 생성 요청"""
    bid_notice_no: str  # bid_id 대신 bid_notice_no 사용
    title: Optional[str] = None
    organization_name: Optional[str] = None
    estimated_price: Optional[int] = None
    bid_end_date: Optional[datetime] = None
    notes: Optional[str] = None
    tags: Optional[List[str]] = []


class BookmarkUpdate(BaseModel):
    """북마크 수정 요청"""
    notes: Optional[str] = None
    tags: Optional[List[str]] = None


class BookmarkResponse(BaseModel):
    """북마크 응답"""
    id: int
    user_id: int
    bid_notice_no: str  # bid_id 대신 bid_notice_no 사용
    title: Optional[str]
    organization_name: Optional[str]
    estimated_price: Optional[int]
    bid_end_date: Optional[datetime]
    notes: Optional[str]
    tags: List[str]
    created_at: datetime
    is_expired: bool


# get_current_user는 이제 auth.dependencies에서 가져옴


@router.post("/")
async def create_bookmark(bookmark: BookmarkCreate, user: User = Depends(get_current_user)):
    """북마크 추가"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            # 먼저 bid_notice_no가 존재하는지 확인
            check_bid_query = """
            SELECT bid_notice_no, title, organization_name, estimated_price, bid_end_date
            FROM bid_announcements
            WHERE bid_notice_no = %s
            """
            cursor.execute(check_bid_query, (bookmark.bid_notice_no,))
            bid_info = cursor.fetchone()

            if not bid_info:
                # 존재하지 않으면 테스트용으로 생성
                cursor.execute("""
                    INSERT INTO bid_announcements (bid_notice_no, title, created_at, updated_at)
                    VALUES (%s, %s, NOW(), NOW())
                    ON CONFLICT (bid_notice_no) DO NOTHING
                """, (bookmark.bid_notice_no, bookmark.title or f"Test Bid {bookmark.bid_notice_no}"))
            else:
                # 실제 데이터로 업데이트
                if not bookmark.title:
                    bookmark.title = bid_info[1]
                if not bookmark.organization_name:
                    bookmark.organization_name = bid_info[2]
                if not bookmark.estimated_price:
                    bookmark.estimated_price = bid_info[3]
                if not bookmark.bid_end_date:
                    bookmark.bid_end_date = bid_info[4]

            # 중복 체크
            check_query = """
            SELECT id FROM user_bookmarks
            WHERE user_id = %s AND bid_notice_no = %s
            """
            cursor.execute(check_query, (user.id, bookmark.bid_notice_no))

            if cursor.fetchone():
                raise HTTPException(status_code=400, detail="이미 북마크된 공고입니다")

            # 북마크 추가
            insert_query = """
            INSERT INTO user_bookmarks (
                user_id, bid_notice_no, title, organization_name,
                estimated_price, bid_end_date, notes, tags
            ) VALUES (
                %s, %s, %s, %s,
                %s, %s, %s, %s
            ) RETURNING id
            """

            cursor.execute(insert_query, (
                user.id,
                bookmark.bid_notice_no,
                bookmark.title,
                bookmark.organization_name,
                bookmark.estimated_price,
                bookmark.bid_end_date,
                bookmark.notes,
                json.dumps(bookmark.tags or [])
            ))

            bookmark_id = cursor.fetchone()[0]
            conn.commit()

            return {
                "success": True,
                "message": "북마크가 추가되었습니다",
                "bookmark_id": bookmark_id
            }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"북마크 생성 실패: {e}")
        raise HTTPException(status_code=500, detail="북마크 추가 실패")


@router.delete("/{bid_notice_no}")
async def delete_bookmark(bid_notice_no: str, user: User = Depends(get_current_user)):
    """북마크 삭제"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            delete_query = """
            DELETE FROM user_bookmarks
            WHERE user_id = %s AND bid_notice_no = %s
            RETURNING id
            """

            cursor.execute(delete_query, (user.id, bid_notice_no))
            deleted_id = cursor.fetchone()
            conn.commit()

            if not deleted_id:
                # 404 대신 204 반환 (이미 삭제된 경우도 성공으로 처리)
                return {
                    "success": True,
                    "message": "북마크가 존재하지 않거나 이미 삭제되었습니다"
                }

            return {
                "success": True,
                "message": "북마크가 삭제되었습니다"
            }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"북마크 삭제 실패: {e}")
        raise HTTPException(status_code=500, detail="북마크 삭제 실패")


@router.get("/")
async def get_bookmarks(
    page: int = Query(1, ge=1, le=1000),
    size: int = Query(20, ge=1, le=100),
    sort: str = Query("created_at", regex="^(created_at|bid_end_date|title)$"),
    order: str = Query("desc", regex="^(asc|desc)$"),
    expired: Optional[bool] = None,
    user=Depends(get_current_user)
):
    """북마크 목록 조회"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            # 기본 쿼리
            base_query = """
            SELECT
                b.id,
                b.user_id,
                b.bid_notice_no,
                b.title,
                b.organization_name,
                b.estimated_price,
                b.bid_end_date,
                b.notes,
                b.tags,
                b.created_at,
                CASE WHEN b.bid_end_date < NOW() THEN true ELSE false END as is_expired
            FROM user_bookmarks b
            WHERE b.user_id = %s
            """

            params = [user.id]

            # 만료 여부 필터
            if expired is not None:
                if expired:
                    base_query += " AND b.bid_end_date < NOW()"
                else:
                    base_query += " AND b.bid_end_date >= NOW()"

            # 정렬
            base_query += f" ORDER BY b.{sort} {order.upper()}"

            # 페이지네이션
            offset = (page - 1) * size
            base_query += f" LIMIT {size} OFFSET {offset}"

            cursor.execute(base_query, params)

            bookmarks = []
            for row in cursor.fetchall():
                bookmarks.append({
                    'id': row[0],
                    'user_id': row[1],
                    'bid_notice_no': row[2],  # bid_id -> bid_notice_no
                    'title': row[3],
                    'organization_name': row[4],
                    'estimated_price': row[5],
                    'bid_end_date': row[6].isoformat() if row[6] else None,
                    'notes': row[7],
                    'tags': json.loads(row[8]) if row[8] else [],
                    'created_at': row[9].isoformat(),
                    'is_expired': row[10]
                })

            # 전체 개수
            count_query = """
            SELECT COUNT(*) FROM user_bookmarks WHERE user_id = %s
            """
            cursor.execute(count_query, (user.id,))
            total = cursor.fetchone()[0]

            return {
                "success": True,
                "data": bookmarks,
                "total": total,
                "page": page,
                "size": size,
                "total_pages": (total + size - 1) // size
            }

    except Exception as e:
        logger.error(f"북마크 목록 조회 실패: {e}")
        raise HTTPException(status_code=500, detail="북마크 목록 조회 실패")


@router.get("/check/{bid_id}")
async def check_bookmark(bid_id: str, user: User = Depends(get_current_user)):
    """북마크 여부 확인"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            query = """
            SELECT EXISTS(
                SELECT 1 FROM user_bookmarks
                WHERE user_id = %s AND bid_id = %s
            )
            """

            cursor.execute(query, (user.id, bid_id))
            is_bookmarked = cursor.fetchone()[0]

            return {
                "success": True,
                "bid_id": bid_id,
                "is_bookmarked": is_bookmarked
            }

    except Exception as e:
        logger.error(f"북마크 확인 실패: {e}")
        raise HTTPException(status_code=500, detail="북마크 확인 실패")


@router.put("/{bookmark_id}")
async def update_bookmark(
    bookmark_id: int,
    update: BookmarkUpdate,
    user=Depends(get_current_user)
):
    """북마크 수정 (메모, 태그)"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            # 권한 확인
            check_query = """
            SELECT id FROM user_bookmarks
            WHERE id = %s AND user_id = %s
            """

            cursor.execute(check_query, (bookmark_id, user.id))

            if not cursor.fetchone():
                raise HTTPException(status_code=404, detail="북마크를 찾을 수 없습니다")

            # 업데이트
            update_fields = []
            params = []

            if update.notes is not None:
                update_fields.append("notes = %s")
                params.append(update.notes)

            if update.tags is not None:
                update_fields.append("tags = %s")
                params.append(update.tags)

            if update_fields:
                update_fields.append("updated_at = NOW()")
                update_query = f"""
                UPDATE user_bookmarks
                SET {', '.join(update_fields)}
                WHERE id = %s AND user_id = %s
                """
                params.extend([bookmark_id, user.id])

                cursor.execute(update_query, params)
                conn.commit()

            return {
                "success": True,
                "message": "북마크가 수정되었습니다"
            }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"북마크 수정 실패: {e}")
        raise HTTPException(status_code=500, detail="북마크 수정 실패")


@router.post("/toggle")
async def toggle_bookmark(bookmark: BookmarkCreate, user: User = Depends(get_current_user)):
    """북마크 토글 (추가/삭제)"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            # PostgreSQL 함수 호출
            query = """
            SELECT toggle_bookmark(
                %s, %s, %s,
                %s, %s, %s
            )
            """

            cursor.execute(query, (
                user.id,
                bookmark.bid_id,
                bookmark.title,
                bookmark.organization_name,
                bookmark.estimated_price,
                bookmark.bid_end_date
            ))

            result = cursor.fetchone()[0]
            conn.commit()

            # JSON 파싱
            if isinstance(result, str):
                return json.loads(result)
            return result

    except Exception as e:
        logger.error(f"북마크 토글 실패: {e}")
        raise HTTPException(status_code=500, detail="북마크 토글 실패")


@router.get("/stats")
async def get_bookmark_stats(user=Depends(get_current_user)):
    """북마크 통계"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            query = """
            SELECT
                COUNT(*) as total,
                COUNT(CASE WHEN bid_end_date > NOW() THEN 1 END) as active,
                COUNT(CASE WHEN bid_end_date <= NOW() THEN 1 END) as expired,
                COUNT(CASE WHEN created_at > NOW() - INTERVAL '7 days' THEN 1 END) as recent
            FROM user_bookmarks
            WHERE user_id = %s
            """

            cursor.execute(query, (user.id,))
            row = cursor.fetchone()

            return {
                "success": True,
                "stats": {
                    "total": row[0],
                    "active": row[1],
                    "expired": row[2],
                    "recent": row[3]
                }
            }

    except Exception as e:
        logger.error(f"북마크 통계 조회 실패: {e}")
        raise HTTPException(status_code=500, detail="통계 조회 실패")