"""
관리자 웹 - 알림 모니터링 API
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Optional
from database import get_db_connection
from api.admin_auth import get_current_admin
import logging
import json

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/admin/notifications", tags=["admin-notifications"])


@router.get("/stats")
async def get_notification_stats(current_admin: dict = Depends(get_current_admin)):
    """알림 발송 통계"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            # 전체 알림 통계
            cursor.execute("""
                SELECT
                    COUNT(*) as total_notifications,
                    COALESCE(SUM(CASE WHEN status = 'read' THEN 1 ELSE 0 END), 0) as read_count,
                    COALESCE(SUM(CASE WHEN status = 'unread' THEN 1 ELSE 0 END), 0) as unread_count
                FROM notifications
            """)
            row = cursor.fetchone()

            # 이메일 발송 통계
            cursor.execute("""
                SELECT
                    COUNT(*) as total_sent,
                    COALESCE(SUM(CASE WHEN status = 'sent' THEN 1 ELSE 0 END), 0) as success_count,
                    COALESCE(SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END), 0) as failed_count,
                    COALESCE(SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END), 0) as pending_count
                FROM notification_send_logs
            """)
            email_row = cursor.fetchone()

            # 오늘 발송 통계
            cursor.execute("""
                SELECT COUNT(*) as today_count
                FROM notification_send_logs
                WHERE sent_at >= CURRENT_DATE
            """)
            today_row = cursor.fetchone()

            # 활성 알림 규칙 수
            cursor.execute("SELECT COUNT(*) FROM alert_rules WHERE is_active = true")
            rules_row = cursor.fetchone()

            return {
                "total_notifications": row[0] or 0,
                "read_count": row[1] or 0,
                "unread_count": row[2] or 0,
                "total_sent": email_row[0] or 0,
                "success_count": email_row[1] or 0,
                "failed_count": email_row[2] or 0,
                "pending_count": email_row[3] or 0,
                "today_sent": today_row[0] or 0,
                "active_rules": rules_row[0] or 0
            }
    except Exception as e:
        logger.error(f"알림 통계 조회 실패: {e}")
        raise HTTPException(status_code=500, detail="서버 내부 오류가 발생했습니다")


@router.get("/list")
async def get_notifications_list(
    current_admin: dict = Depends(get_current_admin),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    user_id: Optional[int] = None,
    rule_id: Optional[int] = None,
    status: Optional[str] = None,
    start_date: Optional[str] = Query(None, description="시작 날짜 (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="종료 날짜 (YYYY-MM-DD)")
):
    """알림 목록 조회"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            base_conditions = "WHERE 1=1"
            params = []

            if user_id is not None:
                base_conditions += " AND n.user_id = %s"
                params.append(user_id)
            if rule_id is not None:
                base_conditions += " AND n.alert_rule_id = %s"
                params.append(rule_id)
            if status:
                base_conditions += " AND n.status = %s"
                params.append(status)
            if start_date:
                base_conditions += " AND n.created_at >= %s"
                params.append(start_date)
            if end_date:
                base_conditions += " AND n.created_at <= %s"
                params.append(end_date)

            count_query = f"""
                SELECT COUNT(*)
                FROM notifications n
                JOIN users u ON n.user_id = u.id
                LEFT JOIN alert_rules ar ON n.alert_rule_id = ar.id
                {base_conditions}
            """
            cursor.execute(count_query, params)
            total = cursor.fetchone()[0]

            data_query = f"""
                SELECT n.id, n.user_id, u.email, u.username, n.alert_rule_id,
                       ar.rule_name, n.title, n.message, n.type, n.status,
                       n.priority, n.metadata, n.created_at
                FROM notifications n
                JOIN users u ON n.user_id = u.id
                LEFT JOIN alert_rules ar ON n.alert_rule_id = ar.id
                {base_conditions}
                ORDER BY n.created_at DESC
                LIMIT %s OFFSET %s
            """
            cursor.execute(data_query, params + [limit, (page - 1) * limit])

            notifications = []
            for row in cursor.fetchall():
                metadata = row[11]
                if isinstance(metadata, str):
                    try:
                        metadata = json.loads(metadata)
                    except (json.JSONDecodeError, TypeError):
                        metadata = {}

                notifications.append({
                    "id": row[0],
                    "user_id": row[1],
                    "email": row[2],
                    "username": row[3],
                    "alert_rule_id": row[4],
                    "rule_name": row[5],
                    "title": row[6],
                    "message": row[7],
                    "type": row[8],
                    "status": row[9],
                    "priority": row[10],
                    "metadata": metadata,
                    "created_at": row[12].isoformat() if row[12] else None
                })

            return {
                "notifications": notifications,
                "total": total,
                "page": page,
                "limit": limit
            }
    except Exception as e:
        logger.error(f"알림 목록 조회 실패: {e}")
        raise HTTPException(status_code=500, detail="서버 내부 오류가 발생했습니다")


@router.get("/email-logs")
async def get_email_send_logs(
    current_admin: dict = Depends(get_current_admin),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    status: Optional[str] = None,
    start_date: Optional[str] = Query(None, description="시작 날짜 (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="종료 날짜 (YYYY-MM-DD)")
):
    """이메일 발송 로그 조회"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            base_conditions = "WHERE 1=1"
            params = []

            if status:
                base_conditions += " AND nsl.status = %s"
                params.append(status)
            if start_date:
                base_conditions += " AND nsl.sent_at >= %s"
                params.append(start_date)
            if end_date:
                base_conditions += " AND nsl.sent_at <= %s"
                params.append(end_date)

            count_query = f"""
                SELECT COUNT(*)
                FROM notification_send_logs nsl
                LEFT JOIN users u ON nsl.user_id = u.id
                {base_conditions}
            """
            cursor.execute(count_query, params)
            total = cursor.fetchone()[0]

            data_query = f"""
                SELECT nsl.id, nsl.notification_type, nsl.user_id, u.email as user_email,
                       u.username, nsl.email_to, nsl.email_subject, nsl.status,
                       nsl.sent_at, nsl.error_message, nsl.metadata
                FROM notification_send_logs nsl
                LEFT JOIN users u ON nsl.user_id = u.id
                {base_conditions}
                ORDER BY nsl.sent_at DESC
                LIMIT %s OFFSET %s
            """
            cursor.execute(data_query, params + [limit, (page - 1) * limit])

            logs = []
            for row in cursor.fetchall():
                metadata = row[10]
                if isinstance(metadata, str):
                    try:
                        metadata = json.loads(metadata)
                    except (json.JSONDecodeError, TypeError):
                        metadata = {}

                logs.append({
                    "id": row[0],
                    "notification_type": row[1],
                    "user_id": row[2],
                    "user_email": row[3],
                    "username": row[4],
                    "email_to": row[5],
                    "email_subject": row[6],
                    "status": row[7],
                    "sent_at": row[8].isoformat() if row[8] else None,
                    "error_message": row[9],
                    "metadata": metadata
                })

            return {
                "logs": logs,
                "total": total,
                "page": page,
                "limit": limit
            }
    except Exception as e:
        logger.error(f"이메일 로그 조회 실패: {e}")
        raise HTTPException(status_code=500, detail="서버 내부 오류가 발생했습니다")


@router.get("/detail/{notification_id}")
async def get_notification_detail(
    notification_id: int,
    current_admin: dict = Depends(get_current_admin)
):
    """알림 상세 조회"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                SELECT n.id, n.user_id, u.email, u.username, n.alert_rule_id,
                       ar.rule_name, n.title, n.message, n.type, n.status,
                       n.priority, n.metadata, n.created_at
                FROM notifications n
                JOIN users u ON n.user_id = u.id
                LEFT JOIN alert_rules ar ON n.alert_rule_id = ar.id
                WHERE n.id = %s
            """, (notification_id,))

            row = cursor.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="알림을 찾을 수 없습니다")

            metadata = row[11]
            if isinstance(metadata, str):
                try:
                    metadata = json.loads(metadata)
                except (json.JSONDecodeError, TypeError):
                    metadata = {}

            return {
                "id": row[0],
                "user_id": row[1],
                "email": row[2],
                "username": row[3],
                "alert_rule_id": row[4],
                "rule_name": row[5],
                "title": row[6],
                "message": row[7],
                "type": row[8],
                "status": row[9],
                "priority": row[10],
                "metadata": metadata,
                "created_at": row[12].isoformat() if row[12] else None
            }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"알림 상세 조회 실패: {e}")
        raise HTTPException(status_code=500, detail="서버 내부 오류가 발생했습니다")
