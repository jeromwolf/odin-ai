"""
관리자 웹 - 배치 모니터링 API
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime, date
from database import get_db_connection
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/admin/batch", tags=["admin-batch"])


# ============================================
# Pydantic Models
# ============================================

class BatchExecutionResponse(BaseModel):
    """배치 실행 응답 모델"""
    id: int
    batch_type: str
    status: str
    start_time: datetime
    end_time: Optional[datetime]
    duration_seconds: Optional[int]
    total_items: int
    success_items: int
    failed_items: int
    skipped_items: int
    error_message: Optional[str]
    error_count: int
    triggered_by: str
    created_at: datetime


class BatchExecutionListResponse(BaseModel):
    """배치 실행 목록 응답"""
    executions: List[BatchExecutionResponse]
    total: int
    page: int
    limit: int


class BatchDetailLog(BaseModel):
    """배치 상세 로그 모델"""
    id: int
    execution_id: int
    log_level: str
    message: str
    context: Optional[dict]
    created_at: datetime


class BatchExecutionDetailResponse(BaseModel):
    """배치 실행 상세 응답"""
    execution: BatchExecutionResponse
    detail_logs: List[BatchDetailLog]
    statistics: dict


class BatchStatisticsResponse(BaseModel):
    """배치 통계 응답"""
    batch_type: str
    date_range: dict
    total_executions: int
    success_count: int
    failed_count: int
    success_rate: float
    avg_duration_seconds: float
    max_duration_seconds: int
    min_duration_seconds: int
    total_items_processed: int
    total_success_items: int
    total_failed_items: int


class BatchManualRunRequest(BaseModel):
    """배치 수동 실행 요청"""
    batch_type: str = Field(..., description="collector/downloader/processor/notification")
    test_mode: bool = Field(default=False, description="테스트 모드 (DB 저장 안 함)")
    date_range: Optional[dict] = Field(None, description="특정 날짜 범위")


class BatchManualRunResponse(BaseModel):
    """배치 수동 실행 응답"""
    task_id: int
    status: str
    message: str


# ============================================
# API Endpoints
# ============================================

@router.get("/executions", response_model=BatchExecutionListResponse)
async def get_batch_executions(
    start_date: Optional[date] = Query(None, description="시작 날짜"),
    end_date: Optional[date] = Query(None, description="종료 날짜"),
    batch_type: Optional[str] = Query(None, description="배치 타입"),
    status: Optional[str] = Query(None, description="상태"),
    page: int = Query(1, ge=1, description="페이지 번호"),
    limit: int = Query(20, ge=1, le=100, description="페이지당 항목 수")
):
    """
    배치 실행 이력 조회

    - start_date, end_date: 날짜 범위 필터
    - batch_type: collector/downloader/processor/notification
    - status: running/success/failed
    - page, limit: 페이지네이션
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            # WHERE 조건 구성
            where_clauses = []
            params = []

            if start_date:
                where_clauses.append("DATE(start_time) >= %s")
                params.append(start_date)

            if end_date:
                where_clauses.append("DATE(start_time) <= %s")
                params.append(end_date)

            if batch_type:
                where_clauses.append("batch_type = %s")
                params.append(batch_type)

            if status:
                where_clauses.append("status = %s")
                params.append(status)

            where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"

            # 총 개수 조회
            count_query = f"""
                SELECT COUNT(*)
                FROM batch_execution_logs
                WHERE {where_sql}
            """
            cursor.execute(count_query, params)
            total = cursor.fetchone()[0]

            # 데이터 조회
            offset = (page - 1) * limit
            data_query = f"""
                SELECT
                    id, batch_type, status, start_time, end_time,
                    duration_seconds, total_items, success_items,
                    failed_items, skipped_items, error_message,
                    error_count, triggered_by, created_at
                FROM batch_execution_logs
                WHERE {where_sql}
                ORDER BY start_time DESC
                LIMIT %s OFFSET %s
            """
            cursor.execute(data_query, params + [limit, offset])

            executions = []
            for row in cursor.fetchall():
                executions.append(BatchExecutionResponse(
                    id=row[0],
                    batch_type=row[1],
                    status=row[2],
                    start_time=row[3],
                    end_time=row[4],
                    duration_seconds=row[5],
                    total_items=row[6],
                    success_items=row[7],
                    failed_items=row[8],
                    skipped_items=row[9],
                    error_message=row[10],
                    error_count=row[11],
                    triggered_by=row[12],
                    created_at=row[13]
                ))

            return BatchExecutionListResponse(
                executions=executions,
                total=total,
                page=page,
                limit=limit
            )

    except Exception as e:
        logger.error(f"배치 실행 이력 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/executions/{execution_id}", response_model=BatchExecutionDetailResponse)
async def get_batch_execution_detail(execution_id: int):
    """
    배치 실행 상세 정보 조회

    - execution_id: 배치 실행 ID
    - 실행 정보 + 상세 로그 + 통계
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            # 배치 실행 정보 조회
            exec_query = """
                SELECT
                    id, batch_type, status, start_time, end_time,
                    duration_seconds, total_items, success_items,
                    failed_items, skipped_items, error_message,
                    error_count, triggered_by, created_at
                FROM batch_execution_logs
                WHERE id = %s
            """
            cursor.execute(exec_query, (execution_id,))
            row = cursor.fetchone()

            if not row:
                raise HTTPException(status_code=404, detail="배치 실행 정보를 찾을 수 없습니다")

            execution = BatchExecutionResponse(
                id=row[0],
                batch_type=row[1],
                status=row[2],
                start_time=row[3],
                end_time=row[4],
                duration_seconds=row[5],
                total_items=row[6],
                success_items=row[7],
                failed_items=row[8],
                skipped_items=row[9],
                error_message=row[10],
                error_count=row[11],
                triggered_by=row[12],
                created_at=row[13]
            )

            # 상세 로그 조회 (최근 100개)
            log_query = """
                SELECT id, execution_id, log_level, message, context, created_at
                FROM batch_detail_logs
                WHERE execution_id = %s
                ORDER BY created_at DESC
                LIMIT 100
            """
            cursor.execute(log_query, (execution_id,))

            detail_logs = []
            for log_row in cursor.fetchall():
                detail_logs.append(BatchDetailLog(
                    id=log_row[0],
                    execution_id=log_row[1],
                    log_level=log_row[2],
                    message=log_row[3],
                    context=log_row[4],
                    created_at=log_row[5]
                ))

            # 통계 계산
            statistics = {
                "success_rate": (execution.success_items / execution.total_items * 100) if execution.total_items > 0 else 0,
                "error_rate": (execution.failed_items / execution.total_items * 100) if execution.total_items > 0 else 0,
                "log_levels": {},
            }

            # 로그 레벨별 카운트
            level_query = """
                SELECT log_level, COUNT(*)
                FROM batch_detail_logs
                WHERE execution_id = %s
                GROUP BY log_level
            """
            cursor.execute(level_query, (execution_id,))
            for level_row in cursor.fetchall():
                statistics["log_levels"][level_row[0]] = level_row[1]

            return BatchExecutionDetailResponse(
                execution=execution,
                detail_logs=detail_logs,
                statistics=statistics
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"배치 실행 상세 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/statistics", response_model=List[BatchStatisticsResponse])
async def get_batch_statistics(
    start_date: Optional[date] = Query(None, description="시작 날짜"),
    end_date: Optional[date] = Query(None, description="종료 날짜"),
    batch_type: Optional[str] = Query(None, description="배치 타입 (전체일 경우 생략)")
):
    """
    배치 실행 통계

    - 배치 타입별 성공/실패 횟수, 평균 처리 시간 등
    - 날짜 범위 지정 가능
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            # WHERE 조건 구성
            where_clauses = ["status IN ('success', 'failed')"]
            params = []

            if start_date:
                where_clauses.append("DATE(start_time) >= %s")
                params.append(start_date)

            if end_date:
                where_clauses.append("DATE(start_time) <= %s")
                params.append(end_date)

            if batch_type:
                where_clauses.append("batch_type = %s")
                params.append(batch_type)

            where_sql = " AND ".join(where_clauses)

            # 통계 조회
            stats_query = f"""
                SELECT
                    batch_type,
                    COUNT(*) as total_executions,
                    SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) as success_count,
                    SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed_count,
                    AVG(duration_seconds) as avg_duration_seconds,
                    MAX(duration_seconds) as max_duration_seconds,
                    MIN(duration_seconds) as min_duration_seconds,
                    SUM(total_items) as total_items_processed,
                    SUM(success_items) as total_success_items,
                    SUM(failed_items) as total_failed_items
                FROM batch_execution_logs
                WHERE {where_sql}
                GROUP BY batch_type
                ORDER BY batch_type
            """
            cursor.execute(stats_query, params)

            statistics = []
            for row in cursor.fetchall():
                total_exec = row[1]
                success_count = row[2]
                success_rate = (success_count / total_exec * 100) if total_exec > 0 else 0

                statistics.append(BatchStatisticsResponse(
                    batch_type=row[0],
                    date_range={
                        "start": start_date.isoformat() if start_date else None,
                        "end": end_date.isoformat() if end_date else None
                    },
                    total_executions=total_exec,
                    success_count=success_count,
                    failed_count=row[3],
                    success_rate=round(success_rate, 2),
                    avg_duration_seconds=round(row[4], 2) if row[4] else 0,
                    max_duration_seconds=row[5] or 0,
                    min_duration_seconds=row[6] or 0,
                    total_items_processed=row[7] or 0,
                    total_success_items=row[8] or 0,
                    total_failed_items=row[9] or 0
                ))

            return statistics

    except Exception as e:
        logger.error(f"배치 통계 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/execute", response_model=BatchManualRunResponse)
async def execute_batch_manual(request: BatchManualRunRequest):
    """
    배치 수동 실행

    - batch_type: collector/downloader/processor/notification
    - test_mode: 테스트 모드 (DB 저장 안 함)
    - date_range: 특정 날짜만 처리 (선택사항)

    **주의**: 실제 배치 실행은 Celery 등 백그라운드 작업으로 처리 필요
    현재는 배치 실행 로그만 생성
    """
    try:
        # 배치 타입 검증
        valid_types = ['collector', 'downloader', 'processor', 'notification']
        if request.batch_type not in valid_types:
            raise HTTPException(
                status_code=400,
                detail=f"유효하지 않은 배치 타입입니다. ({', '.join(valid_types)})"
            )

        with get_db_connection() as conn:
            cursor = conn.cursor()

            # 배치 실행 로그 생성 (함수 사용)
            cursor.execute(
                "SELECT fn_batch_start(%s, %s, %s)",
                (request.batch_type, 'manual', None)  # TODO: 관리자 user_id 추가
            )
            task_id = cursor.fetchone()[0]
            conn.commit()

            # TODO: 실제 배치 실행 로직
            # - Celery 태스크로 비동기 실행
            # - 또는 subprocess로 배치 스크립트 실행
            # - 현재는 로그만 생성

            logger.info(f"배치 수동 실행 요청: {request.batch_type}, task_id={task_id}")

            return BatchManualRunResponse(
                task_id=task_id,
                status="queued",
                message=f"{request.batch_type} 배치가 대기열에 추가되었습니다"
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"배치 수동 실행 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# Helper Functions
# ============================================

def get_recent_batch_status():
    """최근 배치 실행 상태 조회 (대시보드용)"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            query = """
                SELECT
                    batch_type,
                    status,
                    start_time,
                    success_items,
                    failed_items
                FROM batch_execution_logs
                WHERE start_time >= NOW() - INTERVAL '1 day'
                ORDER BY start_time DESC
                LIMIT 5
            """
            cursor.execute(query)

            results = []
            for row in cursor.fetchall():
                results.append({
                    "batch_type": row[0],
                    "status": row[1],
                    "start_time": row[2].isoformat(),
                    "success_items": row[3],
                    "failed_items": row[4]
                })

            return results

    except Exception as e:
        logger.error(f"최근 배치 상태 조회 실패: {e}")
        return []
