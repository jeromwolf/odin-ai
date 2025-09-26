#!/usr/bin/env python3
"""배치 재시도 메커니즘"""

import time
import logging
from typing import Any, Callable, Optional, Dict
from functools import wraps
import traceback
from datetime import datetime
import psycopg2
from psycopg2.extras import RealDictCursor
import json
import os

# 로거 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 데이터베이스 연결
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://blockmeta@localhost:5432/odin_db")


class RetryConfig:
    """재시도 설정"""
    def __init__(
        self,
        max_attempts: int = 3,
        initial_delay: float = 1.0,
        backoff_factor: float = 2.0,
        max_delay: float = 60.0,
        retry_on: tuple = (Exception,),
        ignore_on: tuple = ()
    ):
        self.max_attempts = max_attempts
        self.initial_delay = initial_delay
        self.backoff_factor = backoff_factor
        self.max_delay = max_delay
        self.retry_on = retry_on
        self.ignore_on = ignore_on


class BatchRetryHandler:
    """배치 작업 재시도 핸들러"""

    def __init__(self):
        self.retry_history = []
        self.setup_database()

    def setup_database(self):
        """재시도 이력 테이블 생성"""
        try:
            conn = psycopg2.connect(DATABASE_URL)
            cur = conn.cursor()

            # 재시도 이력 테이블
            cur.execute("""
                CREATE TABLE IF NOT EXISTS batch_retry_history (
                    id SERIAL PRIMARY KEY,
                    batch_name VARCHAR(100) NOT NULL,
                    task_id VARCHAR(100),
                    attempt_number INTEGER NOT NULL,
                    status VARCHAR(20) NOT NULL,
                    error_message TEXT,
                    error_type VARCHAR(100),
                    retry_after FLOAT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)

            # 실패한 작업 큐
            cur.execute("""
                CREATE TABLE IF NOT EXISTS batch_failed_tasks (
                    id SERIAL PRIMARY KEY,
                    batch_name VARCHAR(100) NOT NULL,
                    task_id VARCHAR(100) NOT NULL,
                    task_data JSONB,
                    error_count INTEGER DEFAULT 1,
                    last_error TEXT,
                    last_attempt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    next_retry TIMESTAMP,
                    status VARCHAR(20) DEFAULT 'pending',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(batch_name, task_id)
                );
            """)

            conn.commit()
            cur.close()
            conn.close()
            logger.info("재시도 테이블 설정 완료")
        except Exception as e:
            logger.error(f"테이블 생성 실패: {e}")

    def log_retry_attempt(
        self,
        batch_name: str,
        task_id: str,
        attempt: int,
        status: str,
        error: Optional[Exception] = None,
        retry_after: Optional[float] = None
    ):
        """재시도 시도 기록"""
        try:
            conn = psycopg2.connect(DATABASE_URL)
            cur = conn.cursor()

            cur.execute("""
                INSERT INTO batch_retry_history
                (batch_name, task_id, attempt_number, status, error_message, error_type, retry_after)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (
                batch_name,
                task_id,
                attempt,
                status,
                str(error) if error else None,
                type(error).__name__ if error else None,
                retry_after
            ))

            conn.commit()
            cur.close()
            conn.close()
        except Exception as e:
            logger.error(f"재시도 로그 기록 실패: {e}")

    def add_failed_task(
        self,
        batch_name: str,
        task_id: str,
        task_data: Dict,
        error: Exception
    ):
        """실패한 작업을 큐에 추가"""
        try:
            conn = psycopg2.connect(DATABASE_URL)
            cur = conn.cursor()

            cur.execute("""
                INSERT INTO batch_failed_tasks
                (batch_name, task_id, task_data, last_error, next_retry)
                VALUES (%s, %s, %s, %s, CURRENT_TIMESTAMP + INTERVAL '5 minutes')
                ON CONFLICT (batch_name, task_id)
                DO UPDATE SET
                    error_count = batch_failed_tasks.error_count + 1,
                    last_error = EXCLUDED.last_error,
                    last_attempt = CURRENT_TIMESTAMP,
                    next_retry = CURRENT_TIMESTAMP + INTERVAL '5 minutes' * batch_failed_tasks.error_count
            """, (
                batch_name,
                task_id,
                json.dumps(task_data),
                str(error)
            ))

            conn.commit()
            cur.close()
            conn.close()
            logger.info(f"실패 작업 추가: {batch_name}/{task_id}")
        except Exception as e:
            logger.error(f"실패 작업 추가 오류: {e}")

    def get_pending_retries(self, batch_name: Optional[str] = None) -> list:
        """재시도 대기 중인 작업 조회"""
        try:
            conn = psycopg2.connect(DATABASE_URL)
            cur = conn.cursor(cursor_factory=RealDictCursor)

            query = """
                SELECT * FROM batch_failed_tasks
                WHERE status = 'pending'
                AND (next_retry IS NULL OR next_retry <= CURRENT_TIMESTAMP)
            """
            params = []

            if batch_name:
                query += " AND batch_name = %s"
                params.append(batch_name)

            query += " ORDER BY error_count ASC, next_retry ASC LIMIT 100"

            cur.execute(query, params)
            tasks = cur.fetchall()

            cur.close()
            conn.close()

            return tasks
        except Exception as e:
            logger.error(f"대기 작업 조회 실패: {e}")
            return []

    def mark_task_completed(self, batch_name: str, task_id: str):
        """작업 완료 표시"""
        try:
            conn = psycopg2.connect(DATABASE_URL)
            cur = conn.cursor()

            cur.execute("""
                UPDATE batch_failed_tasks
                SET status = 'completed'
                WHERE batch_name = %s AND task_id = %s
            """, (batch_name, task_id))

            conn.commit()
            cur.close()
            conn.close()
            logger.info(f"작업 완료: {batch_name}/{task_id}")
        except Exception as e:
            logger.error(f"작업 완료 표시 실패: {e}")


def with_retry(config: Optional[RetryConfig] = None):
    """재시도 데코레이터"""
    if config is None:
        config = RetryConfig()

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            handler = BatchRetryHandler()
            batch_name = kwargs.get('batch_name', func.__name__)
            task_id = kwargs.get('task_id', str(time.time()))

            last_exception = None
            delay = config.initial_delay

            for attempt in range(1, config.max_attempts + 1):
                try:
                    # 작업 실행
                    result = func(*args, **kwargs)

                    # 성공 로그
                    if attempt > 1:
                        handler.log_retry_attempt(
                            batch_name, task_id, attempt, 'success'
                        )
                        logger.info(f"재시도 {attempt}회 만에 성공: {batch_name}/{task_id}")

                    return result

                except config.ignore_on as e:
                    # 무시할 예외는 재시도하지 않음
                    logger.warning(f"무시된 예외: {e}")
                    raise

                except config.retry_on as e:
                    last_exception = e

                    # 재시도 로그
                    handler.log_retry_attempt(
                        batch_name, task_id, attempt, 'failed', e, delay
                    )

                    if attempt < config.max_attempts:
                        logger.warning(
                            f"시도 {attempt}/{config.max_attempts} 실패: {e}. "
                            f"{delay:.1f}초 후 재시도..."
                        )
                        time.sleep(delay)

                        # 지수 백오프
                        delay = min(delay * config.backoff_factor, config.max_delay)
                    else:
                        # 최대 시도 횟수 초과
                        handler.add_failed_task(
                            batch_name,
                            task_id,
                            {'args': args, 'kwargs': kwargs},
                            e
                        )
                        logger.error(
                            f"최대 재시도 {config.max_attempts}회 초과: {batch_name}/{task_id}"
                        )

            # 모든 재시도 실패
            raise last_exception

        return wrapper
    return decorator


class BatchRetryExecutor:
    """배치 재시도 실행기"""

    def __init__(self):
        self.handler = BatchRetryHandler()

    def process_failed_tasks(self, batch_name: Optional[str] = None):
        """실패한 작업 재처리"""
        tasks = self.handler.get_pending_retries(batch_name)

        if not tasks:
            logger.info("재시도할 작업 없음")
            return {"processed": 0, "success": 0, "failed": 0}

        results = {"processed": 0, "success": 0, "failed": 0}

        for task in tasks:
            results["processed"] += 1

            try:
                # 작업 데이터 복원
                task_data = task['task_data']

                # 배치별 처리 로직 실행
                if task['batch_name'] == 'api_collection':
                    self._retry_api_collection(task_data)
                elif task['batch_name'] == 'file_download':
                    self._retry_file_download(task_data)
                elif task['batch_name'] == 'document_processing':
                    self._retry_document_processing(task_data)
                else:
                    logger.warning(f"알 수 없는 배치 타입: {task['batch_name']}")
                    continue

                # 성공 표시
                self.handler.mark_task_completed(
                    task['batch_name'],
                    task['task_id']
                )
                results["success"] += 1

            except Exception as e:
                logger.error(f"재시도 실패: {task['task_id']}: {e}")
                results["failed"] += 1

        return results

    def _retry_api_collection(self, task_data):
        """API 수집 재시도"""
        from batch.modules.collector import DataCollector
        collector = DataCollector()
        # 실제 재시도 로직
        logger.info(f"API 수집 재시도: {task_data}")

    def _retry_file_download(self, task_data):
        """파일 다운로드 재시도"""
        from batch.modules.downloader import FileDownloader
        downloader = FileDownloader()
        # 실제 재시도 로직
        logger.info(f"파일 다운로드 재시도: {task_data}")

    def _retry_document_processing(self, task_data):
        """문서 처리 재시도"""
        from batch.modules.processor import DocumentProcessor
        processor = DocumentProcessor()
        # 실제 재시도 로직
        logger.info(f"문서 처리 재시도: {task_data}")


# 사용 예제
if __name__ == "__main__":
    # 재시도 설정
    retry_config = RetryConfig(
        max_attempts=3,
        initial_delay=1.0,
        backoff_factor=2.0,
        retry_on=(ConnectionError, TimeoutError, psycopg2.OperationalError)
    )

    # 재시도 데코레이터 사용
    @with_retry(retry_config)
    def sample_batch_task(batch_name="test", task_id="001"):
        """샘플 배치 작업"""
        import random
        if random.random() < 0.7:  # 70% 실패
            raise ConnectionError("연결 실패")
        return "성공"

    # 테스트 실행
    try:
        result = sample_batch_task()
        print(f"결과: {result}")
    except Exception as e:
        print(f"최종 실패: {e}")

    # 실패 작업 재처리
    executor = BatchRetryExecutor()
    results = executor.process_failed_tasks()
    print(f"재처리 결과: {results}")