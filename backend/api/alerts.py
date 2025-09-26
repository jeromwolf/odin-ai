"""
알림 관리 API
사용자의 알림 규칙 생성, 조회, 수정, 삭제를 처리합니다.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, validator
import json
from datetime import datetime

from database import get_db_connection
from .auth import get_current_user

router = APIRouter(prefix="/api/alerts", tags=["alerts"])

# Pydantic Models
class AlertConditions(BaseModel):
    keywords: List[str] = []
    exclude_keywords: List[str] = []
    min_price: Optional[float] = None
    max_price: Optional[float] = None
    organizations: List[str] = []
    regions: List[str] = []
    categories: List[str] = []

class AlertRuleCreate(BaseModel):
    rule_name: str
    description: Optional[str] = ""
    conditions: AlertConditions
    match_type: str = "ANY"
    notification_channels: List[str] = ["email"]
    notification_timing: str = "immediate"
    notification_time: Optional[str] = "09:00:00"
    notification_day: Optional[int] = 1
    is_active: bool = True

    @validator('match_type')
    def validate_match_type(cls, v):
        if v not in ['ALL', 'ANY']:
            raise ValueError('match_type must be ALL or ANY')
        return v

    @validator('notification_timing')
    def validate_timing(cls, v):
        if v not in ['immediate', 'daily', 'weekly']:
            raise ValueError('notification_timing must be immediate, daily, or weekly')
        return v

    @validator('notification_channels')
    def validate_channels(cls, v):
        valid_channels = {'email', 'web', 'sms'}
        for channel in v:
            if channel not in valid_channels:
                raise ValueError(f'Invalid notification channel: {channel}')
        return v

class AlertRuleUpdate(BaseModel):
    rule_name: Optional[str] = None
    description: Optional[str] = None
    conditions: Optional[AlertConditions] = None
    match_type: Optional[str] = None
    notification_channels: Optional[List[str]] = None
    notification_timing: Optional[str] = None
    notification_time: Optional[str] = None
    notification_day: Optional[int] = None
    is_active: Optional[bool] = None

class AlertRuleResponse(BaseModel):
    id: int
    rule_name: str
    description: str
    conditions: Dict[str, Any]
    match_type: str
    notification_channels: List[str]
    notification_timing: str
    notification_time: Optional[str]
    notification_day: Optional[int]
    is_active: bool
    created_at: str
    updated_at: str
    last_triggered: Optional[str]
    trigger_count: int

@router.get("/rules", response_model=List[AlertRuleResponse])
async def get_alert_rules(
    current_user: dict = Depends(get_current_user),
    active_only: bool = False
):
    """사용자의 알림 규칙 목록 조회"""
    # 임시로 더미 데이터 반환 (데이터베이스 테이블 생성 전까지)
    from datetime import datetime

    dummy_rules = [
        AlertRuleResponse(
            id=1,
            rule_name="소프트웨어 개발 알림",
            description="소프트웨어 개발 관련 입찰 공고 알림",
            conditions={
                "keywords": ["소프트웨어", "개발", "SI"],
                "min_price": 50000000,
                "organizations": ["서울시", "경기도"]
            },
            match_type="ANY",
            notification_channels=["email", "web"],
            notification_timing="immediate",
            notification_time="09:00:00",
            notification_day=1,
            is_active=True,
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat(),
            last_triggered=None,
            trigger_count=5
        ),
        AlertRuleResponse(
            id=2,
            rule_name="건설 공사 알림",
            description="건설 관련 대규모 입찰 공고 알림",
            conditions={
                "keywords": ["건설", "시공", "공사"],
                "min_price": 100000000
            },
            match_type="ALL",
            notification_channels=["email"],
            notification_timing="daily",
            notification_time="08:00:00",
            notification_day=1,
            is_active=True,
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat(),
            last_triggered=None,
            trigger_count=3
        )
    ]

    if active_only:
        dummy_rules = [r for r in dummy_rules if r.is_active]

    return dummy_rules

@router.post("/rules", response_model=AlertRuleResponse)
async def create_alert_rule(
    rule: AlertRuleCreate,
    current_user: dict = Depends(get_current_user)
):
    """새 알림 규칙 생성"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            # 사용자의 알림 규칙 개수 확인 (제한이 있다면)
            cursor.execute(
                "SELECT COUNT(*) FROM alert_rules WHERE user_id = %s",
                (current_user["id"],)
            )
            rule_count = cursor.fetchone()[0]

            if rule_count >= 50:  # 최대 50개 제한
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="알림 규칙은 최대 50개까지 생성할 수 있습니다."
                )

            # 알림 규칙 생성
            insert_query = """
                INSERT INTO alert_rules (
                    user_id, rule_name, description, conditions, match_type,
                    notification_channels, notification_timing, notification_time,
                    notification_day, is_active
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id, created_at, updated_at
            """

            cursor.execute(insert_query, (
                current_user["id"],
                rule.rule_name,
                rule.description,
                json.dumps(rule.conditions.dict()),
                rule.match_type,
                rule.notification_channels,
                rule.notification_timing,
                rule.notification_time,
                rule.notification_day,
                rule.is_active
            ))

            result = cursor.fetchone()
            rule_id, created_at, updated_at = result
            conn.commit()

            return AlertRuleResponse(
                id=rule_id,
                rule_name=rule.rule_name,
                description=rule.description or "",
                conditions=rule.conditions.dict(),
                match_type=rule.match_type,
                notification_channels=rule.notification_channels,
                notification_timing=rule.notification_timing,
                notification_time=rule.notification_time,
                notification_day=rule.notification_day,
                is_active=rule.is_active,
                created_at=created_at.isoformat(),
                updated_at=updated_at.isoformat(),
                last_triggered=None,
                trigger_count=0
            )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"알림 규칙 생성 실패: {str(e)}"
        )

@router.get("/rules/{rule_id}", response_model=AlertRuleResponse)
async def get_alert_rule(
    rule_id: int,
    current_user: dict = Depends(get_current_user)
):
    """특정 알림 규칙 상세 조회"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                SELECT id, rule_name, description, conditions, match_type,
                       notification_channels, notification_timing, notification_time,
                       notification_day, is_active, created_at, updated_at,
                       last_triggered, trigger_count
                FROM alert_rules
                WHERE id = %s AND user_id = %s
            """, (rule_id, current_user["id"]))

            row = cursor.fetchone()
            if not row:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="알림 규칙을 찾을 수 없습니다."
                )

            return AlertRuleResponse(
                id=row[0],
                rule_name=row[1],
                description=row[2] or "",
                conditions=json.loads(row[3]) if isinstance(row[3], str) else row[3],
                match_type=row[4],
                notification_channels=row[5],
                notification_timing=row[6],
                notification_time=row[7].strftime('%H:%M:%S') if row[7] else None,
                notification_day=row[8],
                is_active=row[9],
                created_at=row[10].isoformat(),
                updated_at=row[11].isoformat(),
                last_triggered=row[12].isoformat() if row[12] else None,
                trigger_count=row[13] or 0
            )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"알림 규칙 조회 실패: {str(e)}"
        )

@router.put("/rules/{rule_id}", response_model=AlertRuleResponse)
async def update_alert_rule(
    rule_id: int,
    rule_update: AlertRuleUpdate,
    current_user: dict = Depends(get_current_user)
):
    """알림 규칙 수정"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            # 기존 규칙 확인
            cursor.execute(
                "SELECT id FROM alert_rules WHERE id = %s AND user_id = %s",
                (rule_id, current_user["id"])
            )

            if not cursor.fetchone():
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="알림 규칙을 찾을 수 없습니다."
                )

            # 업데이트할 필드 구성
            update_fields = []
            update_values = []

            if rule_update.rule_name is not None:
                update_fields.append("rule_name = %s")
                update_values.append(rule_update.rule_name)

            if rule_update.description is not None:
                update_fields.append("description = %s")
                update_values.append(rule_update.description)

            if rule_update.conditions is not None:
                update_fields.append("conditions = %s")
                update_values.append(json.dumps(rule_update.conditions.dict()))

            if rule_update.match_type is not None:
                update_fields.append("match_type = %s")
                update_values.append(rule_update.match_type)

            if rule_update.notification_channels is not None:
                update_fields.append("notification_channels = %s")
                update_values.append(rule_update.notification_channels)

            if rule_update.notification_timing is not None:
                update_fields.append("notification_timing = %s")
                update_values.append(rule_update.notification_timing)

            if rule_update.notification_time is not None:
                update_fields.append("notification_time = %s")
                update_values.append(rule_update.notification_time)

            if rule_update.notification_day is not None:
                update_fields.append("notification_day = %s")
                update_values.append(rule_update.notification_day)

            if rule_update.is_active is not None:
                update_fields.append("is_active = %s")
                update_values.append(rule_update.is_active)

            if not update_fields:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="업데이트할 필드가 없습니다."
                )

            # 업데이트 실행
            update_query = f"""
                UPDATE alert_rules
                SET {', '.join(update_fields)}, updated_at = CURRENT_TIMESTAMP
                WHERE id = %s AND user_id = %s
            """

            update_values.extend([rule_id, current_user["id"]])
            cursor.execute(update_query, update_values)
            conn.commit()

            # 업데이트된 규칙 반환
            return await get_alert_rule(rule_id, current_user)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"알림 규칙 수정 실패: {str(e)}"
        )

@router.delete("/rules/{rule_id}")
async def delete_alert_rule(
    rule_id: int,
    current_user: dict = Depends(get_current_user)
):
    """알림 규칙 삭제"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            # 규칙 존재 확인
            cursor.execute(
                "SELECT id FROM alert_rules WHERE id = %s AND user_id = %s",
                (rule_id, current_user["id"])
            )

            if not cursor.fetchone():
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="알림 규칙을 찾을 수 없습니다."
                )

            # 관련 알림 기록도 함께 삭제 (CASCADE로 자동 삭제됨)
            cursor.execute(
                "DELETE FROM alert_rules WHERE id = %s AND user_id = %s",
                (rule_id, current_user["id"])
            )

            conn.commit()

            return {"message": "알림 규칙이 삭제되었습니다."}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"알림 규칙 삭제 실패: {str(e)}"
        )

@router.get("/notifications")
async def get_user_notifications(
    current_user: dict = Depends(get_current_user),
    limit: int = 50,
    offset: int = 0,
    status_filter: Optional[str] = None
):
    """사용자 알림 기록 조회"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            query = """
                SELECT an.id, an.bid_notice_no, an.channel, an.status,
                       an.subject, an.content, an.sent_at, an.read_at,
                       an.created_at, ar.rule_name
                FROM alert_notifications an
                JOIN alert_rules ar ON an.alert_rule_id = ar.id
                WHERE an.user_id = %s
            """

            params = [current_user["id"]]

            if status_filter:
                query += " AND an.status = %s"
                params.append(status_filter)

            query += " ORDER BY an.created_at DESC LIMIT %s OFFSET %s"
            params.extend([limit, offset])

            cursor.execute(query, params)
            notifications = []

            for row in cursor.fetchall():
                notification = {
                    "id": row[0],
                    "bid_notice_no": row[1],
                    "channel": row[2],
                    "status": row[3],
                    "subject": row[4],
                    "content": row[5],
                    "sent_at": row[6].isoformat() if row[6] else None,
                    "read_at": row[7].isoformat() if row[7] else None,
                    "created_at": row[8].isoformat(),
                    "rule_name": row[9]
                }
                notifications.append(notification)

            return notifications

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"알림 기록 조회 실패: {str(e)}"
        )

@router.get("/stats")
async def get_alert_stats(current_user: dict = Depends(get_current_user)):
    """사용자 알림 시스템 통계"""
    # 임시로 더미 데이터 반환 (데이터베이스 테이블 생성 전까지)
    stats = {
        'active_rules': 3,
        'today_notifications': 5,
        'weekly_notifications': [
            {'date': '2025-09-26', 'notifications': 5},
            {'date': '2025-09-25', 'notifications': 3},
            {'date': '2025-09-24', 'notifications': 7},
            {'date': '2025-09-23', 'notifications': 2},
            {'date': '2025-09-22', 'notifications': 4},
            {'date': '2025-09-21', 'notifications': 6},
            {'date': '2025-09-20', 'notifications': 1}
        ],
        'channel_stats': {
            'email': {
                'total': 25,
                'sent': 24,
                'read': 20,
                'success_rate': 96.0,
                'read_rate': 83.3
            },
            'web': {
                'total': 15,
                'sent': 15,
                'read': 12,
                'success_rate': 100.0,
                'read_rate': 80.0
            }
        }
    }
    return stats

@router.post("/notifications/{notification_id}/read")
async def mark_notification_as_read(
    notification_id: int,
    current_user: dict = Depends(get_current_user)
):
    """알림을 읽음으로 표시"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                UPDATE alert_notifications
                SET read_at = CURRENT_TIMESTAMP
                WHERE id = %s AND user_id = %s AND read_at IS NULL
            """, (notification_id, current_user["id"]))

            if cursor.rowcount == 0:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="알림을 찾을 수 없거나 이미 읽은 알림입니다."
                )

            conn.commit()
            return {"message": "알림을 읽음으로 표시했습니다."}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"알림 읽음 표시 실패: {str(e)}"
        )