"""
관리자 웹 - 배치 스케줄 관리 API

batch_schedules 테이블의 CRUD + 스케줄러 상태 조회
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from database import get_db_connection
from api.admin_auth import get_current_admin
from psycopg2.extras import RealDictCursor
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/admin/batch", tags=["admin-batch-schedule"])


# ============================================
# Pydantic Models
# ============================================

class ScheduleCreateRequest(BaseModel):
    """스케줄 생성 요청"""
    label: str = Field(..., min_length=1, max_length=100, description="스케줄 이름")
    schedule_hour: int = Field(..., ge=0, le=23, description="실행 시 (0-23)")
    schedule_minute: int = Field(0, ge=0, le=59, description="실행 분 (0-59)")
    days_of_week: Optional[str] = Field(None, description="요일 (0=월 ~ 6=일, 쉼표 구분). NULL이면 매일")
    is_active: bool = Field(True, description="활성 상태")
    options: Optional[dict] = Field(None, description="배치 옵션 (JSONB)")


class ScheduleUpdateRequest(BaseModel):
    """스케줄 수정 요청"""
    label: Optional[str] = Field(None, min_length=1, max_length=100)
    schedule_hour: Optional[int] = Field(None, ge=0, le=23)
    schedule_minute: Optional[int] = Field(None, ge=0, le=59)
    days_of_week: Optional[str] = None
    is_active: Optional[bool] = None
    options: Optional[dict] = None


class ScheduleResponse(BaseModel):
    """스케줄 응답"""
    id: int
    label: str
    schedule_hour: int
    schedule_minute: int
    days_of_week: Optional[str]
    is_active: bool
    options: dict
    created_by: Optional[int]
    created_at: datetime
    updated_at: datetime
    next_run: Optional[str] = None


class ScheduleListResponse(BaseModel):
    """스케줄 목록 응답"""
    success: bool
    schedules: List[ScheduleResponse]
    total: int


class SchedulerStatusResponse(BaseModel):
    """스케줄러 상태 응답"""
    success: bool
    running: bool
    jobs: list
    is_running: bool
    total_schedules: int
    active_schedules: int
    next_run: Optional[str]


# ============================================
# API Endpoints
# ============================================

@router.get("/schedules", response_model=ScheduleListResponse)
async def list_schedules(current_admin: dict = Depends(get_current_admin)):
    """
    배치 스케줄 목록 조회

    - 모든 스케줄 반환 (활성/비활성 모두)
    - 스케줄러에서 다음 실행 시각 포함
    """
    try:
        from services.batch_scheduler import batch_scheduler

        with get_db_connection() as conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute("""
                SELECT id, label, schedule_hour, schedule_minute,
                       days_of_week, is_active, options,
                       created_by, created_at, updated_at
                FROM batch_schedules
                ORDER BY schedule_hour, schedule_minute, id
            """)
            rows = cursor.fetchall()

        schedules = []
        for row in rows:
            next_run = batch_scheduler.get_next_run_for_schedule(row["id"])
            schedules.append(ScheduleResponse(
                id=row["id"],
                label=row["label"],
                schedule_hour=row["schedule_hour"],
                schedule_minute=row["schedule_minute"],
                days_of_week=row["days_of_week"],
                is_active=row["is_active"],
                options=row["options"] or {},
                created_by=row["created_by"],
                created_at=row["created_at"],
                updated_at=row["updated_at"],
                next_run=next_run,
            ))

        return ScheduleListResponse(
            success=True,
            schedules=schedules,
            total=len(schedules),
        )

    except Exception as e:
        logger.error(f"스케줄 목록 조회 실패: {e}")
        raise HTTPException(status_code=500, detail="스케줄 목록을 불러오는데 실패했습니다")


@router.post("/schedules", response_model=ScheduleResponse, status_code=201)
async def create_schedule(
    request: ScheduleCreateRequest,
    current_admin: dict = Depends(get_current_admin),
):
    """
    배치 스케줄 생성

    - 새 스케줄을 DB에 저장
    - 스케줄러에 즉시 반영 (reload)
    """
    try:
        from services.batch_scheduler import batch_scheduler

        default_options = {
            "enable_notification": True,
            "enable_embedding": False,
            "enable_graph_sync": False,
            "enable_graphrag": False,
            "enable_award_collection": False,
            "enable_daily_digest": False,
        }
        options = request.options if request.options is not None else default_options

        with get_db_connection() as conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute("""
                INSERT INTO batch_schedules
                    (label, schedule_hour, schedule_minute, days_of_week,
                     is_active, options, created_by, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s::jsonb, %s, NOW(), NOW())
                RETURNING id, label, schedule_hour, schedule_minute,
                          days_of_week, is_active, options,
                          created_by, created_at, updated_at
            """, (
                request.label,
                request.schedule_hour,
                request.schedule_minute,
                request.days_of_week,
                request.is_active,
                __import__('json').dumps(options),
                current_admin["id"],
            ))
            row = cursor.fetchone()
            conn.commit()

        # 스케줄러 리로드
        await batch_scheduler.reload_schedules()

        next_run = batch_scheduler.get_next_run_for_schedule(row["id"])

        logger.info(f"스케줄 생성: id={row['id']}, label={row['label']}, admin={current_admin['id']}")

        return ScheduleResponse(
            id=row["id"],
            label=row["label"],
            schedule_hour=row["schedule_hour"],
            schedule_minute=row["schedule_minute"],
            days_of_week=row["days_of_week"],
            is_active=row["is_active"],
            options=row["options"] or {},
            created_by=row["created_by"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            next_run=next_run,
        )

    except Exception as e:
        logger.error(f"스케줄 생성 실패: {e}")
        raise HTTPException(status_code=500, detail="스케줄 생성에 실패했습니다")


@router.put("/schedules/{schedule_id}", response_model=ScheduleResponse)
async def update_schedule(
    schedule_id: int,
    request: ScheduleUpdateRequest,
    current_admin: dict = Depends(get_current_admin),
):
    """
    배치 스케줄 수정

    - 변경된 필드만 업데이트
    - 스케줄러에 즉시 반영
    """
    try:
        from services.batch_scheduler import batch_scheduler

        # 동적 SET 절 구성
        set_clauses = []
        params = []

        if request.label is not None:
            set_clauses.append("label = %s")
            params.append(request.label)

        if request.schedule_hour is not None:
            set_clauses.append("schedule_hour = %s")
            params.append(request.schedule_hour)

        if request.schedule_minute is not None:
            set_clauses.append("schedule_minute = %s")
            params.append(request.schedule_minute)

        if request.days_of_week is not None:
            set_clauses.append("days_of_week = %s")
            params.append(request.days_of_week if request.days_of_week != "" else None)

        if request.is_active is not None:
            set_clauses.append("is_active = %s")
            params.append(request.is_active)

        if request.options is not None:
            set_clauses.append("options = %s::jsonb")
            params.append(__import__('json').dumps(request.options))

        if not set_clauses:
            raise HTTPException(status_code=400, detail="수정할 필드가 없습니다")

        set_clauses.append("updated_at = NOW()")
        params.append(schedule_id)

        with get_db_connection() as conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)

            # 존재 확인
            cursor.execute("SELECT id FROM batch_schedules WHERE id = %s", (schedule_id,))
            if not cursor.fetchone():
                raise HTTPException(status_code=404, detail="스케줄을 찾을 수 없습니다")

            set_sql = ", ".join(set_clauses)
            cursor.execute(f"""
                UPDATE batch_schedules
                SET {set_sql}
                WHERE id = %s
                RETURNING id, label, schedule_hour, schedule_minute,
                          days_of_week, is_active, options,
                          created_by, created_at, updated_at
            """, params)
            row = cursor.fetchone()
            conn.commit()

        # 스케줄러 리로드
        await batch_scheduler.reload_schedules()

        next_run = batch_scheduler.get_next_run_for_schedule(row["id"])

        logger.info(f"스케줄 수정: id={schedule_id}, admin={current_admin['id']}")

        return ScheduleResponse(
            id=row["id"],
            label=row["label"],
            schedule_hour=row["schedule_hour"],
            schedule_minute=row["schedule_minute"],
            days_of_week=row["days_of_week"],
            is_active=row["is_active"],
            options=row["options"] or {},
            created_by=row["created_by"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            next_run=next_run,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"스케줄 수정 실패: {e}")
        raise HTTPException(status_code=500, detail="스케줄 수정에 실패했습니다")


@router.delete("/schedules/{schedule_id}")
async def delete_schedule(
    schedule_id: int,
    current_admin: dict = Depends(get_current_admin),
):
    """
    배치 스케줄 삭제

    - DB에서 삭제 후 스케줄러 리로드
    """
    try:
        from services.batch_scheduler import batch_scheduler

        with get_db_connection() as conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)

            cursor.execute("SELECT id, label FROM batch_schedules WHERE id = %s", (schedule_id,))
            row = cursor.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="스케줄을 찾을 수 없습니다")

            label = row["label"]
            cursor.execute("DELETE FROM batch_schedules WHERE id = %s", (schedule_id,))
            conn.commit()

        # 스케줄러 리로드
        await batch_scheduler.reload_schedules()

        logger.info(f"스케줄 삭제: id={schedule_id}, label={label}, admin={current_admin['id']}")

        return {
            "success": True,
            "message": f"스케줄 '{label}'이(가) 삭제되었습니다",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"스케줄 삭제 실패: {e}")
        raise HTTPException(status_code=500, detail="스케줄 삭제에 실패했습니다")


@router.patch("/schedules/{schedule_id}/toggle")
async def toggle_schedule(
    schedule_id: int,
    current_admin: dict = Depends(get_current_admin),
):
    """
    배치 스케줄 활성/비활성 토글

    - is_active 반전
    - 스케줄러에 즉시 반영
    """
    try:
        from services.batch_scheduler import batch_scheduler

        with get_db_connection() as conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)

            cursor.execute(
                "SELECT id, label, is_active FROM batch_schedules WHERE id = %s",
                (schedule_id,),
            )
            row = cursor.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="스케줄을 찾을 수 없습니다")

            new_state = not row["is_active"]

            cursor.execute("""
                UPDATE batch_schedules
                SET is_active = %s, updated_at = NOW()
                WHERE id = %s
            """, (new_state, schedule_id))
            conn.commit()

        # 스케줄러 리로드
        await batch_scheduler.reload_schedules()

        state_label = "활성화" if new_state else "비활성화"
        logger.info(f"스케줄 토글: id={schedule_id}, is_active={new_state}, admin={current_admin['id']}")

        return {
            "success": True,
            "is_active": new_state,
            "message": f"스케줄 '{row['label']}'이(가) {state_label}되었습니다",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"스케줄 토글 실패: {e}")
        raise HTTPException(status_code=500, detail="스케줄 상태 변경에 실패했습니다")


@router.get("/scheduler/status", response_model=SchedulerStatusResponse)
async def get_scheduler_status(current_admin: dict = Depends(get_current_admin)):
    """
    배치 스케줄러 상태 조회

    - 스케줄러 실행 여부
    - 등록된 잡 목록 및 다음 실행 시각
    """
    try:
        from services.batch_scheduler import batch_scheduler

        status = batch_scheduler.get_status()

        # batch_schedules 테이블에서 전체/활성 스케줄 수 조회
        total_schedules = 0
        active_schedules = 0
        next_run: Optional[str] = None

        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT
                        COUNT(*) AS total,
                        COUNT(*) FILTER (WHERE is_active = TRUE) AS active
                    FROM batch_schedules
                """)
                row = cursor.fetchone()
                if row:
                    total_schedules = row[0] or 0
                    active_schedules = row[1] or 0
        except Exception as db_err:
            logger.warning(f"batch_schedules 테이블 조회 실패 (무시): {db_err}")

        # 다음 실행 시각: 스케줄러 잡 중 가장 이른 next_run_time
        jobs = status.get("jobs", [])
        next_run_times = [
            j.get("next_run_time") for j in jobs if j.get("next_run_time")
        ]
        if next_run_times:
            next_run = min(next_run_times)

        return SchedulerStatusResponse(
            success=True,
            running=status["running"],
            jobs=jobs,
            is_running=status["running"],
            total_schedules=total_schedules,
            active_schedules=active_schedules,
            next_run=next_run,
        )

    except Exception as e:
        logger.error(f"스케줄러 상태 조회 실패: {e}")
        raise HTTPException(status_code=500, detail="스케줄러 상태를 조회할 수 없습니다")
