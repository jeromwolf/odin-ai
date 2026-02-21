"""
관리자 웹 - 사용자 관리 API
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, EmailStr
from typing import List, Optional
from datetime import datetime
from database import get_db_connection
from api.admin_auth import get_current_admin
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/admin/users", tags=["admin-users"])


# Pydantic Models
class UserResponse(BaseModel):
    id: int
    email: str
    username: str
    full_name: Optional[str]
    company: Optional[str]
    is_active: bool
    email_verified: bool
    created_at: datetime
    last_login: Optional[datetime]


class UserListResponse(BaseModel):
    users: List[UserResponse]
    total: int
    page: int


class UserDetailResponse(BaseModel):
    user: UserResponse
    statistics: dict
    recent_activity: List[dict]


# API Endpoints
@router.get("/", response_model=UserListResponse)
async def get_users(
    search: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    current_admin: dict = Depends(get_current_admin)
):
    """사용자 목록 조회"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            where_clauses = []
            params = []

            if search:
                where_clauses.append("(email LIKE %s OR username LIKE %s OR full_name LIKE %s)")
                search_pattern = f"%{search}%"
                params.extend([search_pattern, search_pattern, search_pattern])

            if is_active is not None:
                where_clauses.append("is_active = %s")
                params.append(is_active)

            where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"

            # 총 개수
            cursor.execute(f"SELECT COUNT(*) FROM users WHERE {where_sql}", params)
            total = cursor.fetchone()[0]

            # 데이터 조회
            offset = (page - 1) * limit
            query = f"""
                SELECT id, email, username, full_name, company,
                       is_active, email_verified, created_at, last_login
                FROM users
                WHERE {where_sql}
                ORDER BY created_at DESC
                LIMIT %s OFFSET %s
            """
            cursor.execute(query, params + [limit, offset])

            users = []
            for row in cursor.fetchall():
                users.append(UserResponse(
                    id=row[0], email=row[1], username=row[2],
                    full_name=row[3], company=row[4], is_active=row[5],
                    email_verified=row[6], created_at=row[7],
                    last_login=row[8]
                ))

            return UserListResponse(users=users, total=total, page=page)

    except Exception as e:
        logger.error(f"사용자 목록 조회 실패: {e}")
        raise HTTPException(status_code=500, detail="서버 내부 오류가 발생했습니다")


@router.get("/{user_id}", response_model=UserDetailResponse)
async def get_user_detail(
    user_id: int,
    current_admin: dict = Depends(get_current_admin)
):
    """사용자 상세 정보"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            # 사용자 정보
            cursor.execute("""
                SELECT id, email, username, full_name, company,
                       is_active, email_verified, created_at, last_login
                FROM users WHERE id = %s
            """, (user_id,))
            row = cursor.fetchone()

            if not row:
                raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다")

            user = UserResponse(
                id=row[0], email=row[1], username=row[2],
                full_name=row[3], company=row[4], is_active=row[5],
                email_verified=row[6], created_at=row[7],
                last_login=row[8]
            )

            # 통계
            cursor.execute("SELECT COUNT(*) FROM user_bookmarks WHERE user_id = %s", (user_id,))
            bookmark_count = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM alert_rules WHERE user_id = %s", (user_id,))
            notification_rule_count = cursor.fetchone()[0]

            statistics = {
                "bookmarks": bookmark_count,
                "notification_rules": notification_rule_count
            }

            # 최근 활동 (TODO: user_activity_logs 테이블 필요)
            recent_activity = []

            return UserDetailResponse(
                user=user,
                statistics=statistics,
                recent_activity=recent_activity
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"사용자 상세 조회 실패: {e}")
        raise HTTPException(status_code=500, detail="서버 내부 오류가 발생했습니다")


@router.patch("/{user_id}")
async def update_user(
    user_id: int,
    is_active: Optional[bool] = None,
    current_admin: dict = Depends(get_current_admin)
):
    """사용자 계정 관리 (활성화/비활성화)"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            if is_active is not None:
                cursor.execute(
                    "UPDATE users SET is_active = %s WHERE id = %s",
                    (is_active, user_id)
                )
                conn.commit()
                if cursor.rowcount == 0:
                    raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다")

            return {"success": True, "message": "사용자 정보가 업데이트되었습니다"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"사용자 업데이트 실패: {e}")
        raise HTTPException(status_code=500, detail="서버 내부 오류가 발생했습니다")


@router.get("/statistics/summary")
async def get_user_statistics(current_admin: dict = Depends(get_current_admin)):
    """사용자 통계 요약"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("SELECT COUNT(*) FROM users")
            total_users = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM users WHERE is_active = true")
            active_users = cursor.fetchone()[0]

            cursor.execute("""
                SELECT COUNT(*) FROM users
                WHERE created_at >= CURRENT_DATE - INTERVAL '30 days'
            """)
            new_users_30d = cursor.fetchone()[0]

            return {
                "total_users": total_users,
                "active_users": active_users,
                "inactive_users": total_users - active_users,
                "new_users_last_30_days": new_users_30d
            }

    except Exception as e:
        logger.error(f"사용자 통계 조회 실패: {e}")
        raise HTTPException(status_code=500, detail="서버 내부 오류가 발생했습니다")
