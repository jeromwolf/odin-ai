"""
알림 시스템 API
"""

from fastapi import APIRouter, HTTPException, Depends, Query, BackgroundTasks
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from database import get_db_connection
from auth.dependencies import get_current_user, User
from pydantic import BaseModel
from psycopg2.extras import RealDictCursor
import logging
import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/notifications", tags=["notifications"])

# Pydantic 모델
class AlertRule(BaseModel):
    rule_name: str
    description: Optional[str]
    conditions: Dict[str, Any]
    notification_channels: List[str] = ["email", "web"]
    notification_timing: str = "immediate"
    notification_time: Optional[str] = None
    notification_day: Optional[int] = None

class AlertRuleUpdate(BaseModel):
    rule_name: Optional[str]
    description: Optional[str]
    conditions: Optional[Dict[str, Any]]
    is_active: Optional[bool]
    notification_channels: Optional[List[str]]
    notification_timing: Optional[str]

class NotificationSettings(BaseModel):
    email_enabled: Optional[bool] = None
    sms_enabled: Optional[bool] = None
    web_enabled: Optional[bool] = None
    push_enabled: Optional[bool] = None
    alert_match_enabled: Optional[bool] = None
    deadline_reminder_enabled: Optional[bool] = None
    daily_digest_enabled: Optional[bool] = None
    weekly_report_enabled: Optional[bool] = None
    quiet_hours_enabled: Optional[bool] = None
    email_address: Optional[str] = None
    phone_number: Optional[str] = None


@router.get("/")
async def get_notifications(
    user: User = Depends(get_current_user),
    status_filter: Optional[str] = Query(None, pattern="^(unread|read|all)$"),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100)
):
    """알림 목록 조회"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)

            # 기본 쿼리
            query = """
                SELECT
                    id, title, message, type, status, priority,
                    metadata, created_at, read_at
                FROM notifications
                WHERE user_id = %s
            """
            params = [user.id]

            # 상태 필터
            if status_filter and status_filter != "all":
                query += " AND status = %s"
                params.append(status_filter)

            # 정렬 및 페이지네이션
            query += " ORDER BY created_at DESC LIMIT %s OFFSET %s"
            params.extend([limit, (page - 1) * limit])

            cursor.execute(query, params)

            notifications = []
            for row in cursor.fetchall():
                notifications.append({
                    "id": row["id"],
                    "title": row["title"],
                    "message": row["message"],
                    "type": row["type"],
                    "status": row["status"],
                    "priority": row["priority"],
                    "metadata": row["metadata"],
                    "created_at": row["created_at"].isoformat() if row["created_at"] else None,
                    "read_at": row["read_at"].isoformat() if row["read_at"] else None
                })

            # 전체 개수 (status_filter 적용)
            count_query = "SELECT COUNT(*) AS cnt FROM notifications WHERE user_id = %s"
            count_params = [user.id]
            if status_filter and status_filter != "all":
                count_query += " AND status = %s"
                count_params.append(status_filter)
            cursor.execute(count_query, count_params)
            total = cursor.fetchone()["cnt"]

            return {
                "success": True,
                "data": notifications,
                "total": total,
                "page": page,
                "limit": limit,
                "total_pages": (total + limit - 1) // limit
            }

    except Exception as e:
        logger.error(f"알림 목록 조회 실패: {e}")
        raise HTTPException(status_code=500, detail="알림 목록 조회 실패")


@router.get("/rules")
async def get_alert_rules(
    user: User = Depends(get_current_user),
    is_active: Optional[bool] = None,
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100)
):
    """알림 규칙 목록 조회"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)

            # 조건 쿼리
            where_clauses = ["user_id = %s"]
            params = [user.id]

            if is_active is not None:
                where_clauses.append("is_active = %s")
                params.append(is_active)

            where_sql = " AND ".join(where_clauses)

            # 전체 개수
            cursor.execute(f"""
                SELECT COUNT(*) AS cnt FROM alert_rules
                WHERE {where_sql}
            """, params)
            total = cursor.fetchone()["cnt"]

            # 페이징 조회
            params.extend([(page - 1) * limit, limit])
            cursor.execute(f"""
                SELECT
                    id,
                    rule_name,
                    description,
                    is_active,
                    conditions,
                    notification_channels,
                    notification_timing,
                    notification_time,
                    notification_day,
                    match_count,
                    notification_count,
                    last_matched_at,
                    last_notified_at,
                    created_at,
                    updated_at
                FROM alert_rules
                WHERE {where_sql}
                ORDER BY created_at DESC
                OFFSET %s LIMIT %s
            """, params)

            rules = []
            for row in cursor.fetchall():
                conditions_val = row["conditions"]
                channels_val = row["notification_channels"]
                rules.append({
                    "id": row["id"],
                    "rule_name": row["rule_name"],
                    "description": row["description"],
                    "is_active": row["is_active"],
                    "conditions": conditions_val if isinstance(conditions_val, dict) else json.loads(conditions_val) if conditions_val else {},
                    "notification_channels": channels_val if isinstance(channels_val, list) else json.loads(channels_val) if channels_val else [],
                    "notification_timing": row["notification_timing"],
                    "notification_time": str(row["notification_time"]) if row["notification_time"] else None,
                    "notification_day": row["notification_day"],
                    "statistics": {
                        "match_count": row["match_count"],
                        "notification_count": row["notification_count"],
                        "last_matched_at": row["last_matched_at"].isoformat() if row["last_matched_at"] else None,
                        "last_notified_at": row["last_notified_at"].isoformat() if row["last_notified_at"] else None
                    },
                    "created_at": row["created_at"].isoformat() if row["created_at"] else None,
                    "updated_at": row["updated_at"].isoformat() if row["updated_at"] else None
                })

            return {
                "success": True,
                "data": rules,
                "total": total,
                "page": page,
                "limit": limit,
                "total_pages": (total + limit - 1) // limit
            }

    except Exception as e:
        logger.error(f"알림 규칙 조회 실패: {e}")
        raise HTTPException(status_code=500, detail="알림 규칙 조회 실패")


@router.post("/rules")
async def create_alert_rule(
    rule: AlertRule,
    user: User = Depends(get_current_user)
):
    """알림 규칙 생성"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)

            cursor.execute("""
                INSERT INTO alert_rules (
                    user_id, rule_name, description,
                    conditions, notification_channels,
                    notification_timing, notification_time, notification_day
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (
                user.id,
                rule.rule_name,
                rule.description,
                json.dumps(rule.conditions),
                json.dumps(rule.notification_channels),
                rule.notification_timing,
                rule.notification_time,
                rule.notification_day
            ))

            rule_id = cursor.fetchone()["id"]
            conn.commit()

            return {
                "id": rule_id,
                "message": "알림 규칙이 생성되었습니다"
            }

    except Exception as e:
        logger.error(f"알림 규칙 생성 실패: {e}")
        raise HTTPException(status_code=500, detail="알림 규칙 생성 실패")


@router.put("/rules/{rule_id}")
async def update_alert_rule(
    rule_id: int,
    rule: AlertRuleUpdate,
    user: User = Depends(get_current_user)
):
    """알림 규칙 수정"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)

            # 권한 확인
            cursor.execute("""
                SELECT user_id FROM alert_rules
                WHERE id = %s
            """, (rule_id,))

            result = cursor.fetchone()
            if not result or result["user_id"] != user.id:
                raise HTTPException(status_code=404, detail="알림 규칙을 찾을 수 없습니다")

            # 업데이트 쿼리 생성
            update_fields = []
            params = []

            if rule.rule_name is not None:
                update_fields.append("rule_name = %s")
                params.append(rule.rule_name)

            if rule.description is not None:
                update_fields.append("description = %s")
                params.append(rule.description)

            if rule.conditions is not None:
                update_fields.append("conditions = %s")
                params.append(json.dumps(rule.conditions))

            if rule.is_active is not None:
                update_fields.append("is_active = %s")
                params.append(rule.is_active)

            if rule.notification_channels is not None:
                update_fields.append("notification_channels = %s")
                params.append(json.dumps(rule.notification_channels))

            if rule.notification_timing is not None:
                update_fields.append("notification_timing = %s")
                params.append(rule.notification_timing)

            if update_fields:
                params.append(rule_id)
                cursor.execute(f"""
                    UPDATE alert_rules
                    SET {', '.join(update_fields)}
                    WHERE id = %s
                """, params)
                conn.commit()

            return {"message": "알림 규칙이 수정되었습니다"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"알림 규칙 수정 실패: {e}")
        raise HTTPException(status_code=500, detail="알림 규칙 수정 실패")


@router.delete("/rules/{rule_id}")
async def delete_alert_rule(
    rule_id: int,
    user: User = Depends(get_current_user)
):
    """알림 규칙 삭제"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)

            cursor.execute("""
                DELETE FROM alert_rules
                WHERE id = %s AND user_id = %s
                RETURNING id
            """, (rule_id, user.id))

            if not cursor.fetchone():
                raise HTTPException(status_code=404, detail="알림 규칙을 찾을 수 없습니다")

            conn.commit()

            return {"message": "알림 규칙이 삭제되었습니다"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"알림 규칙 삭제 실패: {e}")
        raise HTTPException(status_code=500, detail="알림 규칙 삭제 실패")


@router.post("/rules/{rule_id}/test")
async def test_alert_rule(
    rule_id: int,
    user: User = Depends(get_current_user),
    limit: int = Query(5, ge=1, le=20)
):
    """알림 규칙 테스트 (매칭 시뮬레이션)"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)

            # 규칙 조회
            cursor.execute("""
                SELECT conditions
                FROM alert_rules
                WHERE id = %s AND user_id = %s
            """, (rule_id, user.id))

            result = cursor.fetchone()
            if not result:
                raise HTTPException(status_code=404, detail="알림 규칙을 찾을 수 없습니다")

            conditions = result["conditions"] if isinstance(result["conditions"], dict) else json.loads(result["conditions"])

            # 조건에 따른 쿼리 생성
            where_clauses = []
            params = []

            # 키워드 조건
            if conditions.get('keywords'):
                keyword_conditions = []
                for keyword in conditions['keywords']:
                    keyword_conditions.append("title ILIKE %s")
                    params.append(f"%{keyword}%")
                where_clauses.append(f"({' OR '.join(keyword_conditions)})")

            # 가격 조건
            if conditions.get('price_min'):
                where_clauses.append("estimated_price >= %s")
                params.append(conditions['price_min'])

            if conditions.get('price_max'):
                where_clauses.append("estimated_price <= %s")
                params.append(conditions['price_max'])

            # 기관 조건
            if conditions.get('organizations'):
                org_placeholders = ','.join(['%s'] * len(conditions['organizations']))
                where_clauses.append(f"organization_name IN ({org_placeholders})")
                params.extend(conditions['organizations'])

            # 최종 쿼리
            where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"
            params.append(limit)

            cursor.execute(f"""
                SELECT
                    bid_notice_no,
                    title,
                    organization_name,
                    estimated_price,
                    bid_end_date
                FROM bid_announcements
                WHERE {where_sql}
                    AND bid_end_date >= NOW()
                ORDER BY created_at DESC
                LIMIT %s
            """, params)

            matches = []
            for row in cursor.fetchall():
                matches.append({
                    "bid_notice_no": row["bid_notice_no"],
                    "title": row["title"],
                    "organization": row["organization_name"],
                    "price": row["estimated_price"],
                    "deadline": row["bid_end_date"].isoformat() if row["bid_end_date"] else None,
                    "match_score": 85  # 실제로는 계산된 점수
                })

            return {
                "rule_id": rule_id,
                "conditions": conditions,
                "matches": matches,
                "total_matches": len(matches)
            }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"알림 규칙 테스트 실패: {e}")
        raise HTTPException(status_code=500, detail="알림 규칙 테스트 실패")


@router.get("/history")
async def get_notification_history(
    user: User = Depends(get_current_user),
    notification_type: Optional[str] = None,
    status: Optional[str] = None,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100)
):
    """알림 발송 이력 조회"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)

            # 조건 쿼리 (notifications 테이블 사용)
            where_clauses = ["n.user_id = %s"]
            params = [user.id]

            if notification_type:
                where_clauses.append("n.type = %s")
                params.append(notification_type)

            if status:
                where_clauses.append("n.status = %s")
                params.append(status)

            where_sql = " AND ".join(where_clauses)

            # 전체 개수
            cursor.execute(f"""
                SELECT COUNT(*) AS cnt FROM notifications n
                WHERE {where_sql}
            """, params)
            total = cursor.fetchone()["cnt"]

            # 페이징 조회 — JOIN alert_rules for rule_name
            params.extend([(page - 1) * limit, limit])
            cursor.execute(f"""
                SELECT
                    n.id,
                    n.type,
                    n.title,
                    n.message,
                    n.status,
                    n.priority,
                    n.metadata,
                    n.read_at,
                    n.created_at,
                    ar.rule_name
                FROM notifications n
                LEFT JOIN alert_rules ar ON ar.id = n.alert_rule_id
                WHERE {where_sql}
                ORDER BY n.created_at DESC
                OFFSET %s LIMIT %s
            """, params)

            notifications = []
            for row in cursor.fetchall():
                message_val = row["message"]
                notifications.append({
                    "id": row["id"],
                    "type": row["type"],
                    "channel": "web",
                    "subject": row["title"],
                    "content": message_val[:200] + "..." if message_val and len(message_val) > 200 else message_val,
                    "recipient": None,
                    "status": row["status"],
                    "rule_name": row["rule_name"],
                    "priority": row["priority"],
                    "sent_at": row["created_at"].isoformat() if row["created_at"] else None,
                    "opened_at": row["read_at"].isoformat() if row["read_at"] else None,
                    "clicked_at": None,
                    "created_at": row["created_at"].isoformat() if row["created_at"] else None
                })

            return {
                "success": True,
                "data": notifications,
                "total": total,
                "page": page,
                "limit": limit,
                "total_pages": (total + limit - 1) // limit
            }

    except Exception as e:
        logger.error(f"알림 이력 조회 실패: {e}")
        raise HTTPException(status_code=500, detail="알림 이력 조회 실패")


@router.get("/settings")
async def get_notification_settings(user: User = Depends(get_current_user)):
    """알림 설정 조회"""
    user_id = user.id

    try:
        with get_db_connection() as conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)

            cursor.execute("""
                SELECT
                    email_enabled, sms_enabled, web_enabled, push_enabled,
                    alert_match_enabled, deadline_reminder_enabled,
                    system_notification_enabled, marketing_enabled,
                    daily_digest_enabled, daily_digest_time,
                    weekly_report_enabled, weekly_report_day, weekly_report_time,
                    quiet_hours_enabled, quiet_hours_start, quiet_hours_end,
                    email_address, phone_number
                FROM user_notification_settings
                WHERE user_id = %s
            """, (user_id,))

            row = cursor.fetchone()

            # 설정이 없으면 기본값으로 생성
            if not row:
                default_email = user.email
                cursor.execute("""
                    INSERT INTO user_notification_settings (user_id, email_address)
                    VALUES (%s, %s)
                    RETURNING *
                """, (user_id, default_email))
                conn.commit()

                cursor.execute("""
                    SELECT
                        email_enabled, sms_enabled, web_enabled, push_enabled,
                        alert_match_enabled, deadline_reminder_enabled,
                        system_notification_enabled, marketing_enabled,
                        daily_digest_enabled, daily_digest_time,
                        weekly_report_enabled, weekly_report_day, weekly_report_time,
                        quiet_hours_enabled, quiet_hours_start, quiet_hours_end,
                        email_address, phone_number
                    FROM user_notification_settings
                    WHERE user_id = %s
                """, (user_id,))
                row = cursor.fetchone()

            return {
                "channels": {
                    "email": row["email_enabled"],
                    "sms": row["sms_enabled"],
                    "web": row["web_enabled"],
                    "push": row["push_enabled"]
                },
                "types": {
                    "alert_match": row["alert_match_enabled"],
                    "deadline_reminder": row["deadline_reminder_enabled"],
                    "system": row["system_notification_enabled"],
                    "marketing": row["marketing_enabled"]
                },
                "digest": {
                    "daily_enabled": row["daily_digest_enabled"],
                    "daily_time": str(row["daily_digest_time"]) if row["daily_digest_time"] else None,
                    "weekly_enabled": row["weekly_report_enabled"],
                    "weekly_day": row["weekly_report_day"],
                    "weekly_time": str(row["weekly_report_time"]) if row["weekly_report_time"] else None
                },
                "quiet_hours": {
                    "enabled": row["quiet_hours_enabled"],
                    "start": str(row["quiet_hours_start"]) if row["quiet_hours_start"] else None,
                    "end": str(row["quiet_hours_end"]) if row["quiet_hours_end"] else None
                },
                "contacts": {
                    "email": row["email_address"],
                    "phone": row["phone_number"]
                }
            }

    except Exception as e:
        logger.error(f"알림 설정 조회 실패: {e}")
        raise HTTPException(status_code=500, detail="알림 설정 조회 실패")


@router.put("/settings")
async def update_notification_settings(
    settings: NotificationSettings,
    user: User = Depends(get_current_user)
):
    """알림 설정 업데이트"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)

            # 업데이트 쿼리 생성
            update_fields = []
            params = []

            # SQL 컬럼명 화이트리스트 (필드명 인젝션 방지)
            ALLOWED_SETTINGS_COLUMNS = {
                'email_enabled', 'sms_enabled', 'web_enabled', 'push_enabled',
                'alert_match_enabled', 'deadline_reminder_enabled',
                'daily_digest_enabled', 'weekly_report_enabled',
                'quiet_hours_enabled', 'email_address', 'phone_number'
            }

            for field, value in settings.dict(exclude_unset=True).items():
                if field not in ALLOWED_SETTINGS_COLUMNS:
                    continue
                update_fields.append(f"{field} = %s")
                params.append(value)

            if update_fields:
                params.append(user.id)
                cursor.execute(f"""
                    UPDATE user_notification_settings
                    SET {', '.join(update_fields)}
                    WHERE user_id = %s
                """, params)

                # 업데이트된 행이 없으면 새로 생성
                if cursor.rowcount == 0:
                    cursor.execute("""
                        INSERT INTO user_notification_settings (user_id, email_address)
                        VALUES (%s, %s)
                    """, (user.id, user.email))

                conn.commit()

            return {"message": "알림 설정이 업데이트되었습니다"}

    except Exception as e:
        logger.error(f"알림 설정 업데이트 실패: {e}")
        raise HTTPException(status_code=500, detail="알림 설정 업데이트 실패")


@router.get("/queue")
async def get_notification_queue(
    user: User = Depends(get_current_user),
    status: str = Query("pending", pattern="^(pending|processing|sent|failed)$")
):
    """알림 대기열 조회 — pending/unread notifications treated as queue"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)

            # Map legacy queue status names to notifications.status values
            # pending/processing → unread, sent → read, failed → remains as-is
            status_map = {
                "pending": "unread",
                "processing": "unread",
                "sent": "read",
                "failed": "unread",
            }
            db_status = status_map.get(status, "unread")

            cursor.execute("""
                SELECT
                    n.id,
                    n.type,
                    n.title,
                    n.message,
                    n.status,
                    n.priority,
                    n.metadata,
                    n.created_at,
                    ar.rule_name,
                    ar.notification_channels
                FROM notifications n
                LEFT JOIN alert_rules ar ON ar.id = n.alert_rule_id
                WHERE n.user_id = %s AND n.status = %s
                ORDER BY n.priority ASC, n.created_at ASC
                LIMIT 50
            """, (user.id, db_status))

            queue = []
            for row in cursor.fetchall():
                channels_val = row["notification_channels"]
                queue.append({
                    "id": row["id"],
                    "type": row["type"],
                    "subject": row["title"],
                    "channels": channels_val if isinstance(channels_val, list) else json.loads(channels_val) if channels_val else ["web"],
                    "status": status,
                    "rule_name": row["rule_name"],
                    "scheduled_for": None,
                    "attempts": 0,
                    "created_at": row["created_at"].isoformat() if row["created_at"] else None
                })

            return {
                "queue": queue,
                "total": len(queue)
            }

    except Exception as e:
        logger.error(f"알림 대기열 조회 실패: {e}")
        raise HTTPException(status_code=500, detail="알림 대기열 조회 실패")


# 이메일 발송 함수 (실제 구현시 Celery 등으로 비동기 처리)
async def send_email_notification(to_email: str, subject: str, content: str, html_content: Optional[str] = None):
    """이메일 알림 발송"""
    try:
        # SMTP 설정 (환경변수로 관리)
        smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
        smtp_port = int(os.getenv("SMTP_PORT", "587"))
        smtp_user = os.getenv("SMTP_USER", "")
        smtp_password = os.getenv("SMTP_PASSWORD", "")

        if not smtp_user or not smtp_password:
            logger.warning("SMTP 설정이 없어 이메일 발송을 건너뜁니다")
            return False

        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = smtp_user
        msg['To'] = to_email

        # 텍스트 파트
        text_part = MIMEText(content, 'plain', 'utf-8')
        msg.attach(text_part)

        # HTML 파트
        if html_content:
            html_part = MIMEText(html_content, 'html', 'utf-8')
            msg.attach(html_part)

        # 이메일 발송
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_password)
            server.send_message(msg)

        return True

    except Exception as e:
        logger.error(f"이메일 발송 실패: {e}")
        return False