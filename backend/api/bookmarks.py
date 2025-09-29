"""
북마크 관리 API
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import psycopg2
from psycopg2.extras import RealDictCursor
from auth.dependencies import get_current_user_optional

router = APIRouter(prefix="/api/bookmarks", tags=["Bookmarks"])

def get_db_connection():
    """데이터베이스 연결"""
    try:
        conn = psycopg2.connect(
            host="localhost",
            port=5432,
            database="odin_db",
            user="blockmeta",
            cursor_factory=RealDictCursor
        )
        return conn
    except Exception as e:
        print(f"DB 연결 실패: {e}")
        return None

class BookmarkCreate(BaseModel):
    bid_notice_no: str
    note: Optional[str] = None

@router.get("")
async def get_bookmarks(current_user = Depends(get_current_user_optional)):
    """사용자의 북마크 목록 조회"""
    # JWT 토큰에서 사용자 ID 추출, 없으면 기본값 100 사용 (개발용)
    user_id = current_user.id if current_user else "100"

    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")

    try:
        cur = conn.cursor()

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
        """, (user_id,))

        bookmarks = cur.fetchall()
        cur.close()
        conn.close()

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

        return result

    except Exception as e:
        print(f"북마크 조회 에러: {e}")
        if conn:
            conn.close()
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{bid_notice_no}")
async def add_bookmark(bid_notice_no: str, current_user = Depends(get_current_user_optional)):
    """북마크 추가"""
    # JWT 토큰에서 사용자 ID 추출, 없으면 기본값 100 사용 (개발용)
    user_id = current_user.id if current_user else "100"

    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")

    try:
        cur = conn.cursor()

        # 이미 북마크가 있는지 확인
        cur.execute("""
            SELECT id FROM user_bookmarks
            WHERE user_id = %s AND (bid_id = %s OR bid_notice_no = %s)
        """, (user_id, bid_notice_no, bid_notice_no))

        existing = cur.fetchone()

        if existing:
            cur.close()
            conn.close()
            return {"message": "이미 북마크되어 있습니다.", "id": existing['id']}

        # 북마크 추가 - bid_id와 bid_notice_no 모두 설정
        cur.execute("""
            INSERT INTO user_bookmarks (user_id, bid_id, bid_notice_no, created_at)
            VALUES (%s, %s, %s, NOW())
            RETURNING id
        """, (user_id, bid_notice_no, bid_notice_no))

        bookmark_id = cur.fetchone()['id']
        conn.commit()
        cur.close()
        conn.close()

        return {
            "success": True,
            "message": "북마크가 추가되었습니다.",
            "id": bookmark_id
        }

    except Exception as e:
        print(f"북마크 추가 에러: {e}")
        if conn:
            conn.rollback()
            conn.close()
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{bid_notice_no}")
async def remove_bookmark(bid_notice_no: str, current_user = Depends(get_current_user_optional)):
    """북마크 삭제"""
    # JWT 토큰에서 사용자 ID 추출, 없으면 기본값 100 사용 (개발용)
    user_id = current_user.id if current_user else "100"

    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")

    try:
        cur = conn.cursor()

        # 북마크 삭제
        cur.execute("""
            DELETE FROM user_bookmarks
            WHERE user_id = %s AND (bid_id = %s OR bid_notice_no = %s)
            RETURNING id
        """, (user_id, bid_notice_no, bid_notice_no))

        deleted = cur.fetchone()

        if not deleted:
            cur.close()
            conn.close()
            raise HTTPException(status_code=404, detail="북마크를 찾을 수 없습니다.")

        conn.commit()
        cur.close()
        conn.close()

        return {
            "success": True,
            "message": "북마크가 삭제되었습니다."
        }

    except Exception as e:
        print(f"북마크 삭제 에러: {e}")
        if conn:
            conn.rollback()
            conn.close()
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{bid_notice_no}/note")
async def update_bookmark_note(bid_notice_no: str, note: str, current_user = Depends(get_current_user_optional)):
    """북마크 메모 업데이트"""
    # JWT 토큰에서 사용자 ID 추출, 없으면 기본값 100 사용 (개발용)
    user_id = current_user.id if current_user else "100"

    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")

    try:
        cur = conn.cursor()

        # 메모 업데이트
        cur.execute("""
            UPDATE user_bookmarks
            SET notes = %s
            WHERE user_id = %s AND (bid_id = %s OR bid_notice_no = %s)
            RETURNING id
        """, (note, user_id, bid_notice_no, bid_notice_no))

        updated = cur.fetchone()

        if not updated:
            cur.close()
            conn.close()
            raise HTTPException(status_code=404, detail="북마크를 찾을 수 없습니다.")

        conn.commit()
        cur.close()
        conn.close()

        return {
            "success": True,
            "message": "메모가 업데이트되었습니다."
        }

    except Exception as e:
        print(f"메모 업데이트 에러: {e}")
        if conn:
            conn.rollback()
            conn.close()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/check/{bid_notice_no}")
async def check_bookmark(bid_notice_no: str, current_user = Depends(get_current_user_optional)):
    """특정 공고가 북마크되어 있는지 확인"""
    # JWT 토큰에서 사용자 ID 추출, 없으면 기본값 100 사용 (개발용)
    user_id = current_user.id if current_user else "100"

    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")

    try:
        cur = conn.cursor()

        cur.execute("""
            SELECT id FROM user_bookmarks
            WHERE user_id = %s AND (bid_id = %s OR bid_notice_no = %s)
        """, (user_id, bid_notice_no, bid_notice_no))

        bookmark = cur.fetchone()
        cur.close()
        conn.close()

        return {
            "is_bookmarked": bookmark is not None,
            "bookmark_id": bookmark['id'] if bookmark else None
        }

    except Exception as e:
        print(f"북마크 확인 에러: {e}")
        if conn:
            conn.close()
        raise HTTPException(status_code=500, detail=str(e))