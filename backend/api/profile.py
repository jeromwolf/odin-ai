"""
프로필 관리 API
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, EmailStr
from typing import Optional, Dict, Any
from datetime import datetime
import logging
from psycopg2.extras import RealDictCursor
from auth.security import verify_password, get_password_hash
from database import get_db_connection
from auth.dependencies import get_current_user, User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/profile", tags=["Profile"])

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
async def get_profile(current_user: User = Depends(get_current_user)):
    """사용자 프로필 조회"""
    user_id = current_user.id

    try:
        with get_db_connection() as conn:
            cur = conn.cursor(cursor_factory=RealDictCursor)

            # 사용자 정보 조회
            cur.execute("""
                SELECT u.id, u.username, u.email, u.full_name, u.phone_number,
                       u.company, u.department, u.position, u.created_at,
                       u.last_login, u.is_active, u.is_superuser,
                       sp.name as plan_name, us.status as subscription_status,
                       us.started_at, us.expires_at
                FROM users u
                LEFT JOIN user_subscriptions us ON u.id = us.user_id
                LEFT JOIN subscription_plans sp ON us.plan_id = sp.id
                WHERE u.id = %s
            """, (user_id,))

            user = cur.fetchone()

            if not user:
                raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다")

            # 활동 통계 조회
            # 검색 횟수 (user_search_history 테이블 미구현 - 0으로 반환)
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

            search_count = 0  # TODO: user_search_history 테이블 구현 필요

            # 응답 데이터 구성
            return {
                "success": True,
                "data": {
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
                    "role": "admin" if user.get('is_superuser') else "user",
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
            }

    except Exception as e:
        logger.error(f"프로필 조회 에러: {e}")
        raise HTTPException(status_code=500, detail="서버 내부 오류가 발생했습니다")

@router.put("")
async def update_profile(profile: UserProfile, current_user: User = Depends(get_current_user)):
    """사용자 프로필 업데이트"""
    user_id = current_user.id

    try:
        with get_db_connection() as conn:
            cur = conn.cursor(cursor_factory=RealDictCursor)

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

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"프로필 업데이트 에러: {e}")
        raise HTTPException(status_code=500, detail="서버 내부 오류가 발생했습니다")

@router.post("/change-password")
async def change_password(password_data: PasswordChange, current_user: User = Depends(get_current_user)):
    """비밀번호 변경"""
    user_id = current_user.id

    try:
        with get_db_connection() as conn:
            cur = conn.cursor(cursor_factory=RealDictCursor)

            # 현재 비밀번호 확인
            cur.execute("""
                SELECT hashed_password FROM users WHERE id = %s
            """, (user_id,))

            user = cur.fetchone()
            if not user:
                raise HTTPException(status_code=404, detail="User not found")

            # 현재 비밀번호 검증
            if not verify_password(password_data.current_password, user['hashed_password']):
                raise HTTPException(status_code=400, detail="현재 비밀번호가 올바르지 않습니다")

            # 새 비밀번호 해시 생성 및 저장
            new_password_hash = get_password_hash(password_data.new_password)

            cur.execute("""
                UPDATE users
                SET hashed_password = %s, updated_at = NOW()
                WHERE id = %s
            """, (new_password_hash, user_id))

            conn.commit()

            return {
                "success": True,
                "message": "비밀번호가 변경되었습니다"
            }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"비밀번호 변경 에러: {e}")
        raise HTTPException(status_code=500, detail="서버 내부 오류가 발생했습니다")

@router.get("/activity")
async def get_activity(current_user: User = Depends(get_current_user)):
    """사용자 활동 내역 조회"""
    user_id = current_user.id

    try:
        with get_db_connection() as conn:
            cur = conn.cursor(cursor_factory=RealDictCursor)

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
        logger.error(f"활동 조회 에러: {e}")
        raise HTTPException(status_code=500, detail="서버 내부 오류가 발생했습니다")
