"""
관리자 웹 - 시스템 모니터링 API
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import List, Optional, Dict
from datetime import datetime, timedelta
from database import get_db_connection
import psutil
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/admin/system", tags=["admin-system"])


# ============================================
# Pydantic Models
# ============================================

class SystemMetric(BaseModel):
    """시스템 메트릭 모델"""
    metric_type: str
    metric_value: float
    metric_unit: str
    recorded_at: datetime


class SystemMetricsResponse(BaseModel):
    """시스템 메트릭 응답"""
    metrics: List[SystemMetric]
    summary: Optional[dict] = None


class SystemStatusResponse(BaseModel):
    """실시간 시스템 상태 응답"""
    cpu_percent: float
    memory_percent: float
    memory_used_gb: float
    memory_total_gb: float
    disk_percent: float
    disk_used_gb: float
    disk_total_gb: float
    db_status: str
    db_connections: int
    timestamp: datetime


class APIPerformanceMetric(BaseModel):
    """API 성능 메트릭"""
    endpoint: str
    avg_response_time: float
    max_response_time: float
    request_count: int
    error_count: int
    error_rate: float


class APIPerformanceResponse(BaseModel):
    """API 성능 응답"""
    endpoints: List[APIPerformanceMetric]
    period: dict


class NotificationStatusResponse(BaseModel):
    """알림 발송 현황 응답"""
    total_sent: int
    success_count: int
    failed_count: int
    pending_count: int
    success_rate: float
    period: dict
    failure_reasons: Dict[str, int]


# ============================================
# API Endpoints
# ============================================

@router.get("/metrics", response_model=SystemMetricsResponse)
async def get_system_metrics(
    metric_type: Optional[str] = Query(None, description="cpu/memory/disk"),
    start_time: Optional[datetime] = Query(None, description="시작 시간"),
    end_time: Optional[datetime] = Query(None, description="종료 시간"),
    limit: int = Query(100, ge=1, le=1000, description="최대 데이터 포인트 수")
):
    """
    시스템 메트릭 조회

    - metric_type: cpu, memory, disk, api_response_time
    - start_time, end_time: 시간 범위
    - limit: 최대 데이터 포인트 수 (기본 100개)
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            # WHERE 조건 구성
            where_clauses = []
            params = []

            if metric_type:
                where_clauses.append("metric_type = %s")
                params.append(metric_type)

            if start_time:
                where_clauses.append("recorded_at >= %s")
                params.append(start_time)

            if end_time:
                where_clauses.append("recorded_at <= %s")
                params.append(end_time)

            where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"

            # 메트릭 조회
            query = f"""
                SELECT metric_type, metric_value, metric_unit, recorded_at
                FROM system_metrics
                WHERE {where_sql}
                ORDER BY recorded_at DESC
                LIMIT %s
            """
            cursor.execute(query, params + [limit])

            metrics = []
            for row in cursor.fetchall():
                metrics.append(SystemMetric(
                    metric_type=row[0],
                    metric_value=row[1],
                    metric_unit=row[2],
                    recorded_at=row[3]
                ))

            # 요약 통계 (최근 1시간)
            summary = None
            if not start_time and not end_time:
                summary_query = """
                    SELECT
                        metric_type,
                        AVG(metric_value) as avg_value,
                        MAX(metric_value) as max_value,
                        MIN(metric_value) as min_value
                    FROM system_metrics
                    WHERE recorded_at >= NOW() - INTERVAL '1 hour'
                    GROUP BY metric_type
                """
                cursor.execute(summary_query)
                summary = {}
                for row in cursor.fetchall():
                    summary[row[0]] = {
                        "avg": round(row[1], 2),
                        "max": round(row[2], 2),
                        "min": round(row[3], 2)
                    }

            return SystemMetricsResponse(
                metrics=metrics,
                summary=summary
            )

    except Exception as e:
        logger.error(f"시스템 메트릭 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status", response_model=SystemStatusResponse)
async def get_system_status():
    """
    실시간 시스템 상태 조회

    - CPU, 메모리, 디스크 사용률
    - 데이터베이스 상태
    - 현재 시간 기준
    """
    try:
        # CPU 사용률
        cpu_percent = psutil.cpu_percent(interval=1)

        # 메모리 사용률
        memory = psutil.virtual_memory()
        memory_percent = memory.percent
        memory_used_gb = memory.used / (1024 ** 3)
        memory_total_gb = memory.total / (1024 ** 3)

        # 디스크 사용률
        disk = psutil.disk_usage('/')
        disk_percent = disk.percent
        disk_used_gb = disk.used / (1024 ** 3)
        disk_total_gb = disk.total / (1024 ** 3)

        # 데이터베이스 상태
        db_status = "healthy"
        db_connections = 0
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                # 활성 연결 수 조회
                cursor.execute("""
                    SELECT COUNT(*)
                    FROM pg_stat_activity
                    WHERE state = 'active'
                """)
                db_connections = cursor.fetchone()[0]
        except Exception as e:
            logger.error(f"DB 상태 확인 실패: {e}")
            db_status = "error"

        # 메트릭 저장 (백그라운드 작업으로 처리하는 것이 좋음)
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT fn_record_metric(%s, %s, %s)",
                    ('cpu', cpu_percent, 'percent')
                )
                cursor.execute(
                    "SELECT fn_record_metric(%s, %s, %s)",
                    ('memory', memory_percent, 'percent')
                )
                cursor.execute(
                    "SELECT fn_record_metric(%s, %s, %s)",
                    ('disk', disk_percent, 'percent')
                )
                conn.commit()
        except Exception as e:
            logger.warning(f"메트릭 저장 실패: {e}")

        return SystemStatusResponse(
            cpu_percent=round(cpu_percent, 2),
            memory_percent=round(memory_percent, 2),
            memory_used_gb=round(memory_used_gb, 2),
            memory_total_gb=round(memory_total_gb, 2),
            disk_percent=round(disk_percent, 2),
            disk_used_gb=round(disk_used_gb, 2),
            disk_total_gb=round(disk_total_gb, 2),
            db_status=db_status,
            db_connections=db_connections,
            timestamp=datetime.now()
        )

    except Exception as e:
        logger.error(f"시스템 상태 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api-performance", response_model=APIPerformanceResponse)
async def get_api_performance(
    start_time: Optional[datetime] = Query(None, description="시작 시간"),
    end_time: Optional[datetime] = Query(None, description="종료 시간")
):
    """
    API 성능 통계

    - 엔드포인트별 평균 응답 시간, 요청 횟수, 에러율
    - 기본: 최근 1시간
    """
    try:
        # 기본값 설정
        if not end_time:
            end_time = datetime.now()
        if not start_time:
            start_time = end_time - timedelta(hours=1)

        with get_db_connection() as conn:
            cursor = conn.cursor()

            query = """
                SELECT
                    endpoint,
                    AVG(response_time_ms) as avg_response_time,
                    MAX(response_time_ms) as max_response_time,
                    COUNT(*) as request_count,
                    SUM(CASE WHEN status_code >= 500 THEN 1 ELSE 0 END) as error_count
                FROM api_performance_logs
                WHERE created_at >= %s AND created_at <= %s
                GROUP BY endpoint
                ORDER BY request_count DESC
                LIMIT 20
            """
            cursor.execute(query, (start_time, end_time))

            endpoints = []
            for row in cursor.fetchall():
                request_count = row[3]
                error_count = row[4]
                error_rate = (error_count / request_count * 100) if request_count > 0 else 0

                endpoints.append(APIPerformanceMetric(
                    endpoint=row[0],
                    avg_response_time=round(row[1], 2),
                    max_response_time=round(row[2], 2),
                    request_count=request_count,
                    error_count=error_count,
                    error_rate=round(error_rate, 2)
                ))

            return APIPerformanceResponse(
                endpoints=endpoints,
                period={
                    "start": start_time.isoformat(),
                    "end": end_time.isoformat()
                }
            )

    except Exception as e:
        logger.error(f"API 성능 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/notifications/status", response_model=NotificationStatusResponse)
async def get_notification_status(
    start_time: Optional[datetime] = Query(None, description="시작 시간"),
    end_time: Optional[datetime] = Query(None, description="종료 시간")
):
    """
    알림 발송 현황

    - 발송 성공/실패 건수
    - 성공률
    - 실패 원인별 분류
    """
    try:
        # 기본값: 오늘
        if not end_time:
            end_time = datetime.now()
        if not start_time:
            start_time = end_time.replace(hour=0, minute=0, second=0, microsecond=0)

        with get_db_connection() as conn:
            cursor = conn.cursor()

            # 전체 통계
            stats_query = """
                SELECT
                    COUNT(*) as total,
                    COALESCE(SUM(CASE WHEN status = 'sent' THEN 1 ELSE 0 END), 0) as success,
                    COALESCE(SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END), 0) as failed,
                    COALESCE(SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END), 0) as pending
                FROM notification_send_logs
                WHERE created_at >= %s AND created_at <= %s
            """
            cursor.execute(stats_query, (start_time, end_time))
            stats = cursor.fetchone()

            total_sent = stats[0] or 0
            success_count = stats[1] or 0
            failed_count = stats[2] or 0
            pending_count = stats[3] or 0
            success_rate = (success_count / total_sent * 100) if total_sent > 0 else 0

            # 실패 원인별 분류
            failure_query = """
                SELECT
                    SUBSTRING(error_message FROM 1 FOR 50) as error_type,
                    COUNT(*) as count
                FROM notification_send_logs
                WHERE status = 'failed'
                  AND created_at >= %s AND created_at <= %s
                  AND error_message IS NOT NULL
                GROUP BY error_type
                ORDER BY count DESC
                LIMIT 5
            """
            cursor.execute(failure_query, (start_time, end_time))

            failure_reasons = {}
            for row in cursor.fetchall():
                failure_reasons[row[0]] = row[1]

            return NotificationStatusResponse(
                total_sent=total_sent,
                success_count=success_count,
                failed_count=failed_count,
                pending_count=pending_count,
                success_rate=round(success_rate, 2),
                period={
                    "start": start_time.isoformat(),
                    "end": end_time.isoformat()
                },
                failure_reasons=failure_reasons
            )

    except Exception as e:
        logger.error(f"알림 발송 현황 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))
