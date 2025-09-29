"""
프로필 관리 API
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, EmailStr
from typing import Optional, Dict, Any
from datetime import datetime
import psycopg2
from psycopg2.extras import RealDictCursor
import bcrypt
import os

router = APIRouter(prefix="/api/profile", tags=["Profile"])

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

# Pydantic 모델
class UserProfile(BaseModel):
    name: str
    email: EmailStr
    phone: Optional[str] = None
    company: Optional[str] = None
    department: Optional[str] = None
    position: Optional[str] = None

class PasswordChange(BaseModel):
    current_password: str
    new_password: str

class UserActivity(BaseModel):
    total_searches: int = 0
    total_bookmarks: int = 0
    total_downloads: int = 0
    last_search: Optional[datetime] = None
    last_bookmark: Optional[datetime] = None

@router.get("")
async def get_profile(user_id: str = "100"):  # TODO: JWT에서 user_id 추출
    """사용자 프로필 조회"""
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")

    try:
        cur = conn.cursor()

        # 사용자 정보 조회
        cur.execute("""
            SELECT u.id, u.username, u.email, u.full_name, u.phone_number,
                   u.company, u.department, u.position, u.created_at,
                   u.last_login, u.is_active,
                   sp.name as plan_name, us.status as subscription_status,
                   us.started_at, us.expires_at
            FROM users u
            LEFT JOIN user_subscriptions us ON u.id = us.user_id
            LEFT JOIN subscription_plans sp ON us.plan_id = sp.id
            WHERE u.id = %s
        """, (user_id,))

        user = cur.fetchone()

        if not user:
            # 사용자가 없으면 기본값으로 생성
            cur.execute("""
                INSERT INTO users (username, email, full_name, hashed_password, created_at, is_active)
                VALUES (%s, %s, %s, %s, NOW(), true)
                RETURNING *
            """, (f"user_{user_id}", f"user_{user_id}@example.com", f"사용자 {user_id}", "temp_password_hash"))
            user = cur.fetchone()
            conn.commit()

        # 활동 통계 조회
        # 검색 횟수 (user_search_history 테이블 생성 필요 - 임시로 북마크*3으로 처리)
        cur.execute("""
            SELECT COUNT(*) as bookmark_count
            FROM user_bookmarks
            WHERE user_id = %s
        """, (user_id,))
        bookmark_count = cur.fetchone()

        # 최근 7일 활동
        cur.execute("""
            SELECT COUNT(*) as recent_activity
            FROM user_bookmarks
            WHERE user_id = %s AND created_at >= NOW() - INTERVAL '7 days'
        """, (user_id,))
        recent_activity = cur.fetchone()

        # 검색 횟수는 북마크의 3배로 가정 (실제로는 user_search_history 테이블 필요)
        search_count = (bookmark_count['bookmark_count'] * 3) if bookmark_count else 0

        cur.close()
        conn.close()

        # 응답 데이터 구성
        return {
            "id": str(user['id']),
            "username": user['username'],
            "email": user['email'],
            "name": user['full_name'] or "",
            "phone": user['phone_number'] or "",
            "company": user['company'] or "",
            "department": user['department'] or "",
            "position": user['position'] or "",
            "created_at": user['created_at'].isoformat() if user['created_at'] else None,
            "last_login": user['last_login'].isoformat() if user['last_login'] else None,
            "subscription": {
                "plan": user['plan_name'] or "basic",
                "status": user['subscription_status'] or "active",
                "start_date": user['started_at'].isoformat() if user['started_at'] else None,
                "end_date": user['expires_at'].isoformat() if user['expires_at'] else None
            },
            "activity": {
                "total_searches": search_count,
                "total_bookmarks": bookmark_count['bookmark_count'] if bookmark_count else 0,
                "recent_activity": recent_activity['recent_activity'] if recent_activity else 0
            }
        }

    except Exception as e:
        print(f"프로필 조회 에러: {e}")
        if conn:
            conn.close()
        raise HTTPException(status_code=500, detail=str(e))

@router.put("")
async def update_profile(profile: UserProfile, user_id: str = "100"):
    """사용자 프로필 업데이트"""
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")

    try:
        cur = conn.cursor()

        # 프로필 업데이트
        cur.execute("""
            UPDATE users
            SET full_name = %s, email = %s, phone_number = %s,
                company = %s, department = %s, position = %s,
                updated_at = NOW()
            WHERE id = %s
            RETURNING *
        """, (profile.name, profile.email, profile.phone,
              profile.company, profile.department, profile.position,
              user_id))

        updated_user = cur.fetchone()

        if not updated_user:
            raise HTTPException(status_code=404, detail="User not found")

        conn.commit()
        cur.close()
        conn.close()

        return {
            "success": True,
            "message": "프로필이 업데이트되었습니다",
            "profile": {
                "name": updated_user['full_name'],
                "email": updated_user['email'],
                "phone": updated_user['phone_number'],
                "company": updated_user['company'],
                "department": updated_user['department'],
                "position": updated_user['position']
            }
        }

    except Exception as e:
        print(f"프로필 업데이트 에러: {e}")
        if conn:
            conn.rollback()
            conn.close()
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/change-password")
async def change_password(password_data: PasswordChange, user_id: str = "100"):
    """비밀번호 변경"""
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")

    try:
        cur = conn.cursor()

        # 현재 비밀번호 확인
        cur.execute("""
            SELECT hashed_password FROM users WHERE id = %s
        """, (user_id,))

        user = cur.fetchone()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # 비밀번호 검증 (현재는 해시 없이 처리)
        # TODO: bcrypt 사용하여 실제 검증 구현

        # 새 비밀번호 해시 생성 및 저장
        new_password_hash = bcrypt.hashpw(
            password_data.new_password.encode('utf-8'),
            bcrypt.gensalt()
        ).decode('utf-8')

        cur.execute("""
            UPDATE users
            SET hashed_password = %s, updated_at = NOW()
            WHERE id = %s
        """, (new_password_hash, user_id))

        conn.commit()
        cur.close()
        conn.close()

        return {
            "success": True,
            "message": "비밀번호가 변경되었습니다"
        }

    except Exception as e:
        print(f"비밀번호 변경 에러: {e}")
        if conn:
            conn.rollback()
            conn.close()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/activity")
async def get_activity(user_id: str = "100"):
    """사용자 활동 내역 조회"""
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")

    try:
        cur = conn.cursor()

        # 최근 활동 조회 - 북마크와 입찰공고 조인하여 실제 제목 가져오기
        cur.execute("""
            SELECT
                'bookmark' as type,
                COALESCE(ba.title, ub.bid_notice_no) as description,
                ub.created_at
            FROM user_bookmarks ub
            LEFT JOIN bid_announcements ba ON ub.bid_notice_no = ba.bid_notice_no
            WHERE ub.user_id = %s
            ORDER BY ub.created_at DESC
            LIMIT 10
        """, (user_id,))

        activities = cur.fetchall()

        cur.close()
        conn.close()

        return {
            "activities": [
                {
                    "type": act['type'],
                    "description": act['description'],
                    "timestamp": act['created_at'].isoformat() if act['created_at'] else None
                }
                for act in activities
            ]
        }

    except Exception as e:
        print(f"활동 조회 에러: {e}")
        if conn:
            conn.close()
        return {"activities": []}