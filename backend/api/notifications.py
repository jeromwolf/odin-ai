"""
알림 시스템 API
"""

from fastapi import APIRouter, HTTPException, Depends, Query, BackgroundTasks
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from database import get_db_connection
from auth.dependencies import get_current_user, User
from pydantic import BaseModel
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
    email_enabled: Optional[bool]
    sms_enabled: Optional[bool]
    web_enabled: Optional[bool]
    push_enabled: Optional[bool]
    alert_match_enabled: Optional[bool]
    deadline_reminder_enabled: Optional[bool]
    daily_digest_enabled: Optional[bool]
    weekly_report_enabled: Optional[bool]
    quiet_hours_enabled: Optional[bool]
    email_address: Optional[str]
    phone_number: Optional[str]


@router.get("/")
async def get_notifications(
    user: User = Depends(get_current_user),
    status_filter: Optional[str] = Query(None, regex="^(unread|read|all)$"),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100)
):
    """알림 목록 조회"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

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
                    "id": row[0],
                    "title": row[1],
                    "message": row[2],
                    "type": row[3],
                    "status": row[4],
                    "priority": row[5],
                    "metadata": row[6],
                    "created_at": row[7].isoformat() if row[7] else None,
                    "read_at": row[8].isoformat() if row[8] else None
                })

            # 전체 개수 (status_filter 적용)
            count_query = "SELECT COUNT(*) FROM notifications WHERE user_id = %s"
            count_params = [user.id]
            if status_filter and status_filter != "all":
                count_query += " AND status = %s"
                count_params.append(status_filter)
            cursor.execute(count_query, count_params)
            total = cursor.fetchone()[0]

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
            cursor = conn.cursor()

            # 조건 쿼리
            where_clauses = ["user_id = %s"]
            params = [user.id]

            if is_active is not None:
                where_clauses.append("is_active = %s")
                params.append(is_active)

            where_sql = " AND ".join(where_clauses)

            # 전체 개수
            cursor.execute(f"""
                SELECT COUNT(*) FROM alert_rules
                WHERE {where_sql}
            """, params)
            total = cursor.fetchone()[0]

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
                rules.append({
                    "id": row[0],
                    "rule_name": row[1],
                    "description": row[2],
                    "is_active": row[3],
                    "conditions": row[4] if isinstance(row[4], dict) else json.loads(row[4]) if row[4] else {},
                    "notification_channels": row[5] if isinstance(row[5], list) else json.loads(row[5]) if row[5] else [],
                    "notification_timing": row[6],
                    "notification_time": str(row[7]) if row[7] else None,
                    "notification_day": row[8],
                    "statistics": {
                        "match_count": row[9],
                        "notification_count": row[10],
                        "last_matched_at": row[11].isoformat() if row[11] else None,
                        "last_notified_at": row[12].isoformat() if row[12] else None
                    },
                    "created_at": row[13].isoformat() if row[13] else None,
                    "updated_at": row[14].isoformat() if row[14] else None
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
            cursor = conn.cursor()

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

            rule_id = cursor.fetchone()[0]
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
            cursor = conn.cursor()

            # 권한 확인
            cursor.execute("""
                SELECT user_id FROM alert_rules
                WHERE id = %s
            """, (rule_id,))

            result = cursor.fetchone()
            if not result or result[0] != user.id:
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
            cursor = conn.cursor()

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
            cursor = conn.cursor()

            # 규칙 조회
            cursor.execute("""
                SELECT conditions
                FROM alert_rules
                WHERE id = %s AND user_id = %s
            """, (rule_id, user.id))

            result = cursor.fetchone()
            if not result:
                raise HTTPException(status_code=404, detail="알림 규칙을 찾을 수 없습니다")

            conditions = result[0] if isinstance(result[0], dict) else json.loads(result[0])

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
                    "bid_notice_no": row[0],
                    "title": row[1],
                    "organization": row[2],
                    "price": row[3],
                    "deadline": row[4].isoformat() if row[4] else None,
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
            cursor = conn.cursor()

            # 조건 쿼리
            where_clauses = ["user_id = %s"]
            params = [user.id]

            if notification_type:
                where_clauses.append("notification_type = %s")
                params.append(notification_type)

            if status:
                where_clauses.append("status = %s")
                params.append(status)

            where_sql = " AND ".join(where_clauses)

            # 전체 개수
            cursor.execute(f"""
                SELECT COUNT(*) FROM notification_history
                WHERE {where_sql}
            """, params)
            total = cursor.fetchone()[0]

            # 페이징 조회
            params.extend([(page - 1) * limit, limit])
            cursor.execute(f"""
                SELECT
                    id,
                    notification_type,
                    channel,
                    subject,
                    content,
                    recipient,
                    status,
                    sent_at,
                    opened_at,
                    clicked_at,
                    created_at
                FROM notification_history
                WHERE {where_sql}
                ORDER BY created_at DESC
                OFFSET %s LIMIT %s
            """, params)

            notifications = []
            for row in cursor.fetchall():
                notifications.append({
                    "id": row[0],
                    "type": row[1],
                    "channel": row[2],
                    "subject": row[3],
                    "content": row[4][:200] + "..." if len(row[4]) > 200 else row[4],
                    "recipient": row[5],
                    "status": row[6],
                    "sent_at": row[7].isoformat() if row[7] else None,
                    "opened_at": row[8].isoformat() if row[8] else None,
                    "clicked_at": row[9].isoformat() if row[9] else None,
                    "created_at": row[10].isoformat() if row[10] else None
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
            cursor = conn.cursor()

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
                    "email": row[0],
                    "sms": row[1],
                    "web": row[2],
                    "push": row[3]
                },
                "types": {
                    "alert_match": row[4],
                    "deadline_reminder": row[5],
                    "system": row[6],
                    "marketing": row[7]
                },
                "digest": {
                    "daily_enabled": row[8],
                    "daily_time": str(row[9]) if row[9] else None,
                    "weekly_enabled": row[10],
                    "weekly_day": row[11],
                    "weekly_time": str(row[12]) if row[12] else None
                },
                "quiet_hours": {
                    "enabled": row[13],
                    "start": str(row[14]) if row[14] else None,
                    "end": str(row[15]) if row[15] else None
                },
                "contacts": {
                    "email": row[16],
                    "phone": row[17]
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
            cursor = conn.cursor()

            # 업데이트 쿼리 생성
            update_fields = []
            params = []

            for field, value in settings.dict(exclude_unset=True).items():
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
    status: str = Query("pending", regex="^(pending|processing|sent|failed)$")
):
    """알림 대기열 조회"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                SELECT
                    id,
                    notification_type,
                    subject,
                    channels,
                    status,
                    scheduled_for,
                    attempts,
                    created_at
                FROM notification_queue
                WHERE user_id = %s AND status = %s
                ORDER BY priority ASC, scheduled_for ASC
                LIMIT 50
            """, (user.id, status))

            queue = []
            for row in cursor.fetchall():
                queue.append({
                    "id": row[0],
                    "type": row[1],
                    "subject": row[2],
                    "channels": row[3] if isinstance(row[3], list) else json.loads(row[3]) if row[3] else [],
                    "status": row[4],
                    "scheduled_for": row[5].isoformat() if row[5] else None,
                    "attempts": row[6],
                    "created_at": row[7].isoformat() if row[7] else None
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