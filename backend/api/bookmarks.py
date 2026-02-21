"""
북마크 관리 API
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from datetime import datetime
import logging
from psycopg2.extras import RealDictCursor
from database import get_db_connection
from auth.dependencies import get_current_user, User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/bookmarks", tags=["Bookmarks"])

@router.get("")
async def get_bookmarks(
    current_user: User = Depends(get_current_user),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100)
):
    """사용자의 북마크 목록 조회 (페이지네이션 지원)"""
    user_id = current_user.id
    offset = (page - 1) * limit

    try:
        with get_db_connection() as conn:
            cur = conn.cursor(cursor_factory=RealDictCursor)

            # 전체 개수 조회
            cur.execute("""
                SELECT COUNT(*) as total FROM user_bookmarks WHERE user_id = %s
            """, (user_id,))
            total = cur.fetchone()['total']

            # 북마크와 입찰공고 정보 조인하여 조회
            cur.execute("""
                SELECT
                    ub.id,
                    ub.bid_notice_no,
                    ba.title,
                    ba.organization_name as organization,
                    ba.bid_end_date,
                    ba.estimated_price,
                    COALESCE(
                        (SELECT tags.tag_name
                         FROM bid_tags tags
                         JOIN bid_tag_relations btr ON tags.tag_id = btr.tag_id
                         WHERE btr.bid_notice_no = ub.bid_notice_no
                         LIMIT 1),
                        '기타'
                    ) as category,
                    ARRAY(
                        SELECT tags.tag_name
                        FROM bid_tags tags
                        JOIN bid_tag_relations btr ON tags.tag_id = btr.tag_id
                        WHERE btr.bid_notice_no = ub.bid_notice_no
                    ) as tags,
                    ub.created_at,
                    ub.notes as note
                FROM user_bookmarks ub
                LEFT JOIN bid_announcements ba ON ub.bid_notice_no = ba.bid_notice_no
                WHERE ub.user_id = %s
                ORDER BY ub.created_at DESC
                LIMIT %s OFFSET %s
            """, (user_id, limit, offset))

            bookmarks = cur.fetchall()

            # 결과 포맷팅
            result = []
            for bookmark in bookmarks:
                result.append({
                    "id": str(bookmark['id']),
                    "bid_notice_no": bookmark['bid_notice_no'],
                    "title": bookmark['title'] or '제목 없음',
                    "organization": bookmark['organization'] or '기관명 없음',
                    "bid_end_date": bookmark['bid_end_date'].isoformat() if bookmark['bid_end_date'] else None,
                    "estimated_price": float(bookmark['estimated_price']) if bookmark['estimated_price'] else 0,
                    "category": bookmark['category'],
                    "tags": bookmark['tags'] if bookmark['tags'] else [],
                    "created_at": bookmark['created_at'].isoformat() if bookmark['created_at'] else None,
                    "note": bookmark['note']
                })

            return {
                "success": True,
                "data": result,
                "total": total,
                "page": page,
                "limit": limit,
                "total_pages": (total + limit - 1) // limit
            }

    except Exception as e:
        logger.error(f"북마크 조회 에러: {e}")
        raise HTTPException(status_code=500, detail="서버 내부 오류가 발생했습니다")

@router.post("/{bid_notice_no}")
async def add_bookmark(bid_notice_no: str, current_user: User = Depends(get_current_user)):
    """북마크 추가"""
    user_id = current_user.id

    try:
        with get_db_connection() as conn:
            cur = conn.cursor(cursor_factory=RealDictCursor)

            # 이미 북마크가 있는지 확인
            cur.execute("""
                SELECT id FROM user_bookmarks
                WHERE user_id = %s AND (bid_id = %s OR bid_notice_no = %s)
            """, (user_id, bid_notice_no, bid_notice_no))

            existing = cur.fetchone()

            if existing:
                return {"message": "이미 북마크되어 있습니다.", "id": existing['id']}

            # 북마크 추가 - bid_id와 bid_notice_no 모두 설정
            cur.execute("""
                INSERT INTO user_bookmarks (user_id, bid_id, bid_notice_no, created_at)
                VALUES (%s, %s, %s, NOW())
                RETURNING id
            """, (user_id, bid_notice_no, bid_notice_no))

            bookmark_id = cur.fetchone()['id']
            conn.commit()

            return {
                "success": True,
                "message": "북마크가 추가되었습니다.",
                "id": bookmark_id
            }

    except Exception as e:
        logger.error(f"북마크 추가 에러: {e}")
        raise HTTPException(status_code=500, detail="서버 내부 오류가 발생했습니다")

@router.delete("/{bid_notice_no}")
async def remove_bookmark(bid_notice_no: str, current_user: User = Depends(get_current_user)):
    """북마크 삭제"""
    user_id = current_user.id

    try:
        with get_db_connection() as conn:
            cur = conn.cursor(cursor_factory=RealDictCursor)

            # 북마크 삭제
            cur.execute("""
                DELETE FROM user_bookmarks
                WHERE user_id = %s AND (bid_id = %s OR bid_notice_no = %s)
                RETURNING id
            """, (user_id, bid_notice_no, bid_notice_no))

            deleted = cur.fetchone()

            if not deleted:
                raise HTTPException(status_code=404, detail="북마크를 찾을 수 없습니다.")

            conn.commit()

            return {
                "success": True,
                "message": "북마크가 삭제되었습니다."
            }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"북마크 삭제 에러: {e}")
        raise HTTPException(status_code=500, detail="서버 내부 오류가 발생했습니다")

@router.put("/{bid_notice_no}/note")
async def update_bookmark_note(bid_notice_no: str, note: str, current_user: User = Depends(get_current_user)):
    """북마크 메모 업데이트"""
    user_id = current_user.id

    try:
        with get_db_connection() as conn:
            cur = conn.cursor(cursor_factory=RealDictCursor)

            # 메모 업데이트
            cur.execute("""
                UPDATE user_bookmarks
                SET notes = %s
                WHERE user_id = %s AND (bid_id = %s OR bid_notice_no = %s)
                RETURNING id
            """, (note, user_id, bid_notice_no, bid_notice_no))

            updated = cur.fetchone()

            if not updated:
                raise HTTPException(status_code=404, detail="북마크를 찾을 수 없습니다.")

            conn.commit()

            return {
                "success": True,
                "message": "메모가 업데이트되었습니다."
            }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"메모 업데이트 에러: {e}")
        raise HTTPException(status_code=500, detail="서버 내부 오류가 발생했습니다")

@router.get("/check/{bid_notice_no}")
async def check_bookmark(bid_notice_no: str, current_user: User = Depends(get_current_user)):
    """특정 공고가 북마크되어 있는지 확인"""
    user_id = current_user.id

    try:
        with get_db_connection() as conn:
            cur = conn.cursor(cursor_factory=RealDictCursor)

            cur.execute("""
                SELECT id FROM user_bookmarks
                WHERE user_id = %s AND (bid_id = %s OR bid_notice_no = %s)
            """, (user_id, bid_notice_no, bid_notice_no))

            bookmark = cur.fetchone()

            return {
                "is_bookmarked": bookmark is not None,
                "bookmark_id": bookmark['id'] if bookmark else None
            }

    except Exception as e:
        logger.error(f"북마크 확인 에러: {e}")
        raise HTTPException(status_code=500, detail="서버 내부 오류가 발생했습니다")
