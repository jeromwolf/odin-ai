"""
관리자 웹 - 로그 조회 API
"""

from fastapi import APIRouter, HTTPException, Query, Response
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, date
from database import get_db_connection
import logging
import zipfile
import io
from pathlib import Path

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/admin/logs", tags=["admin-logs"])


# Pydantic Models
class LogEntry(BaseModel):
    id: int
    execution_id: Optional[int]
    log_level: str
    message: str
    context: Optional[dict]
    created_at: datetime


class LogListResponse(BaseModel):
    logs: List[LogEntry]
    total: int
    page: int


# API Endpoints
@router.get("/", response_model=LogListResponse)
async def get_logs(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    level: Optional[str] = Query(None),
    keyword: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=200)
):
    """로그 검색 및 조회"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            where_clauses = []
            params = []

            if start_date:
                where_clauses.append("DATE(created_at) >= %s")
                params.append(start_date)

            if end_date:
                where_clauses.append("DATE(created_at) <= %s")
                params.append(end_date)

            if level:
                where_clauses.append("log_level = %s")
                params.append(level.upper())

            if keyword:
                where_clauses.append("message LIKE %s")
                params.append(f"%{keyword}%")

            where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"

            # 총 개수
            cursor.execute(f"SELECT COUNT(*) FROM batch_detail_logs WHERE {where_sql}", params)
            total = cursor.fetchone()[0]

            # 로그 조회
            offset = (page - 1) * limit
            query = f"""
                SELECT id, execution_id, log_level, message, context, created_at
                FROM batch_detail_logs
                WHERE {where_sql}
                ORDER BY created_at DESC
                LIMIT %s OFFSET %s
            """
            cursor.execute(query, params + [limit, offset])

            logs = []
            for row in cursor.fetchall():
                logs.append(LogEntry(
                    id=row[0],
                    execution_id=row[1],
                    log_level=row[2],
                    message=row[3],
                    context=row[4],
                    created_at=row[5]
                ))

            return LogListResponse(logs=logs, total=total, page=page)

    except Exception as e:
        logger.error(f"로그 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/download/{log_date}")
async def download_logs(log_date: date):
    """로그 파일 다운로드 (ZIP)"""
    try:
        log_dir = Path("logs")
        if not log_dir.exists():
            raise HTTPException(status_code=404, detail="로그 디렉토리가 없습니다")

        # 해당 날짜의 로그 파일 찾기
        log_files = list(log_dir.glob(f"batch_{log_date.strftime('%Y%m%d')}*.log"))

        if not log_files:
            raise HTTPException(status_code=404, detail="해당 날짜의 로그 파일이 없습니다")

        # ZIP 파일 생성
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for log_file in log_files:
                zip_file.write(log_file, log_file.name)

        zip_buffer.seek(0)

        return Response(
            content=zip_buffer.getvalue(),
            media_type="application/zip",
            headers={
                "Content-Disposition": f"attachment; filename=logs_{log_date}.zip"
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"로그 다운로드 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/errors/statistics")
async def get_error_statistics(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None)
):
    """에러 로그 통계"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            where_clauses = ["log_level = 'ERROR'"]
            params = []

            if start_date:
                where_clauses.append("DATE(created_at) >= %s")
                params.append(start_date)

            if end_date:
                where_clauses.append("DATE(created_at) <= %s")
                params.append(end_date)

            where_sql = " AND ".join(where_clauses)

            # TOP 에러
            query = f"""
                SELECT
                    SUBSTRING(message FROM 1 FOR 100) as error_msg,
                    COUNT(*) as count
                FROM batch_detail_logs
                WHERE {where_sql}
                GROUP BY error_msg
                ORDER BY count DESC
                LIMIT 10
            """
            cursor.execute(query, params)

            top_errors = []
            for row in cursor.fetchall():
                top_errors.append({"message": row[0], "count": row[1]})

            # 에러 추이 (일별)
            trend_query = f"""
                SELECT
                    DATE(created_at) as error_date,
                    COUNT(*) as count
                FROM batch_detail_logs
                WHERE {where_sql}
                GROUP BY error_date
                ORDER BY error_date DESC
                LIMIT 30
            """
            cursor.execute(trend_query, params)

            error_trend = []
            for row in cursor.fetchall():
                error_trend.append({
                    "date": row[0].isoformat(),
                    "count": row[1]
                })

            return {
                "top_errors": top_errors,
                "error_trend": error_trend
            }

    except Exception as e:
        logger.error(f"에러 통계 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))
