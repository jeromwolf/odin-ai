"""배치 처리 API"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from typing import Optional, Dict, Any
from datetime import datetime
import logging
import sys
import os

# 프로젝트 경로 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from batch.retry_handler import BatchRetryHandler, BatchRetryExecutor, RetryConfig, with_retry

router = APIRouter(
    prefix="/api/batch",
    tags=["batch"]
)

logger = logging.getLogger(__name__)

# 재시도 핸들러 초기화
retry_handler = BatchRetryHandler()
retry_executor = BatchRetryExecutor()


@router.get("/status")
async def get_batch_status():
    """배치 시스템 상태 확인"""
    try:
        # 실패한 작업 수 확인
        pending_retries = retry_handler.get_pending_retries()

        return {
            "status": "operational",
            "pending_retries": len(pending_retries),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"배치 상태 확인 실패: {e}")
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }


@router.post("/retry/{task_id}")
async def retry_failed_task(
    task_id: str,
    batch_name: Optional[str] = None,
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    """특정 작업 재시도"""
    try:
        # 백그라운드로 재시도 실행
        background_tasks.add_task(
            _retry_single_task,
            batch_name=batch_name,
            task_id=task_id
        )

        return {
            "message": f"작업 {task_id} 재시도 시작됨",
            "batch_name": batch_name,
            "task_id": task_id
        }
    except Exception as e:
        logger.error(f"재시도 시작 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/retry/all")
async def retry_all_failed_tasks(
    batch_name: Optional[str] = None,
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    """모든 실패 작업 재시도"""
    try:
        # 백그라운드로 모든 재시도 실행
        background_tasks.add_task(
            _retry_all_tasks,
            batch_name=batch_name
        )

        pending_count = len(retry_handler.get_pending_retries(batch_name))

        return {
            "message": f"{pending_count}개 작업 재시도 시작",
            "batch_name": batch_name,
            "pending_count": pending_count
        }
    except Exception as e:
        logger.error(f"전체 재시도 시작 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/retry/history")
async def get_retry_history(
    batch_name: Optional[str] = None,
    limit: int = 100
):
    """재시도 이력 조회"""
    try:
        import psycopg2
        from psycopg2.extras import RealDictCursor

        DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://blockmeta@localhost:5432/odin_db")
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor(cursor_factory=RealDictCursor)

        query = """
            SELECT * FROM batch_retry_history
            WHERE 1=1
        """
        params = []

        if batch_name:
            query += " AND batch_name = %s"
            params.append(batch_name)

        query += " ORDER BY created_at DESC LIMIT %s"
        params.append(limit)

        cur.execute(query, params)
        history = cur.fetchall()

        cur.close()
        conn.close()

        return {
            "history": history,
            "count": len(history),
            "batch_name": batch_name
        }
    except Exception as e:
        logger.error(f"이력 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/failed")
async def get_failed_tasks(
    batch_name: Optional[str] = None,
    status: str = "pending"
):
    """실패한 작업 목록 조회"""
    try:
        import psycopg2
        from psycopg2.extras import RealDictCursor

        DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://blockmeta@localhost:5432/odin_db")
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor(cursor_factory=RealDictCursor)

        query = """
            SELECT * FROM batch_failed_tasks
            WHERE status = %s
        """
        params = [status]

        if batch_name:
            query += " AND batch_name = %s"
            params.append(batch_name)

        query += " ORDER BY error_count DESC, created_at DESC"

        cur.execute(query, params)
        tasks = cur.fetchall()

        cur.close()
        conn.close()

        return {
            "tasks": tasks,
            "count": len(tasks),
            "batch_name": batch_name,
            "status": status
        }
    except Exception as e:
        logger.error(f"실패 작업 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/failed/{task_id}")
async def delete_failed_task(
    task_id: str,
    batch_name: Optional[str] = None
):
    """실패한 작업 삭제"""
    try:
        import psycopg2

        DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://blockmeta@localhost:5432/odin_db")
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()

        if batch_name:
            cur.execute("""
                DELETE FROM batch_failed_tasks
                WHERE task_id = %s AND batch_name = %s
            """, (task_id, batch_name))
        else:
            cur.execute("""
                DELETE FROM batch_failed_tasks
                WHERE task_id = %s
            """, (task_id,))

        deleted_count = cur.rowcount
        conn.commit()
        cur.close()
        conn.close()

        if deleted_count == 0:
            raise HTTPException(status_code=404, detail="작업을 찾을 수 없습니다")

        return {
            "message": f"작업 {task_id} 삭제됨",
            "task_id": task_id,
            "batch_name": batch_name
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"작업 삭제 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/test-retry")
async def test_retry_mechanism():
    """재시도 메커니즘 테스트"""
    try:
        # 재시도 설정
        config = RetryConfig(
            max_attempts=3,
            initial_delay=0.5,
            backoff_factor=2.0
        )

        # 테스트 함수
        @with_retry(config)
        def test_function(batch_name="test", task_id="test-001"):
            import random
            if random.random() < 0.5:  # 50% 실패
                raise ConnectionError("테스트 연결 실패")
            return "성공"

        # 실행
        try:
            result = test_function()
            return {
                "status": "success",
                "message": "재시도 메커니즘 테스트 성공",
                "result": result
            }
        except Exception as e:
            return {
                "status": "failed",
                "message": "재시도 메커니즘 테스트 실패",
                "error": str(e)
            }
    except Exception as e:
        logger.error(f"테스트 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# 백그라운드 작업 함수들
def _retry_single_task(batch_name: Optional[str], task_id: str):
    """단일 작업 재시도 (백그라운드)"""
    try:
        # 실제 재시도 로직
        logger.info(f"재시도 시작: {batch_name}/{task_id}")
        # 구현 필요
    except Exception as e:
        logger.error(f"재시도 실패: {e}")


def _retry_all_tasks(batch_name: Optional[str]):
    """모든 작업 재시도 (백그라운드)"""
    try:
        results = retry_executor.process_failed_tasks(batch_name)
        logger.info(f"재시도 완료: {results}")
        return results
    except Exception as e:
        logger.error(f"전체 재시도 실패: {e}")
        return None