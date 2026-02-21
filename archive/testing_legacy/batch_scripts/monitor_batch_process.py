#!/usr/bin/env python
"""
대용량 배치 처리 모니터링 및 실행 스크립트
"""

import sys
import asyncio
import time
import psutil
from pathlib import Path
from datetime import datetime
from loguru import logger

# 프로젝트 경로 추가
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from src.database.models import BidDocument
from src.services.document_processor import DocumentProcessor
from src.core.config import get_batch_config

DATABASE_URL = "postgresql://blockmeta@localhost:5432/odin_db"

class BatchMonitor:
    """배치 처리 모니터"""

    def __init__(self):
        self.start_time = time.time()
        self.processed = 0
        self.failed = 0

    def log_resource_usage(self):
        """리소스 사용량 로깅"""
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()

        logger.info(f"📊 리소스 사용량:")
        logger.info(f"  - CPU: {cpu_percent}%")
        logger.info(f"  - 메모리: {memory.percent}% ({memory.used / (1024**3):.1f}GB / {memory.total / (1024**3):.1f}GB)")

    def log_progress(self, total, current):
        """진행률 로깅"""
        elapsed = time.time() - self.start_time
        rate = current / elapsed if elapsed > 0 else 0
        eta = (total - current) / rate if rate > 0 else 0

        logger.info(f"⏱️ 진행 상황:")
        logger.info(f"  - 진행률: {current}/{total} ({current/total*100:.1f}%)")
        logger.info(f"  - 처리 속도: {rate:.1f}개/초")
        logger.info(f"  - 예상 완료 시간: {eta/60:.1f}분")

async def process_batch(batch_size: str = "small"):
    """배치 처리 실행

    Args:
        batch_size: "small", "medium", "large", "xlarge"
    """
    logger.info(f"🚀 {batch_size.upper()} 배치 처리 시작")

    config = get_batch_config(batch_size)
    batch_count = config['batch_size']
    max_concurrent = config['max_concurrent']

    logger.info(f"설정: 배치 크기={batch_count}, 동시 처리={max_concurrent}")

    engine = create_engine(DATABASE_URL)
    Session = sessionmaker(bind=engine)
    session = Session()

    storage_path = Path("./storage")
    processor = DocumentProcessor(session, storage_path)
    monitor = BatchMonitor()

    try:
        # 처리 전 상태
        result = session.execute(text("""
            SELECT COUNT(*)
            FROM bid_documents
            WHERE processing_status = 'pending'
            AND download_status = 'completed'
        """)).scalar()

        total_pending = result
        logger.info(f"📋 처리 대상: {total_pending}개 문서")

        # 리소스 사용량 체크
        monitor.log_resource_usage()

        # 배치 처리 실행
        start_time = time.time()

        # process_pending_documents는 매개변수를 받지 않으므로
        # 대신 직접 대기 문서를 가져와서 처리
        pending_docs = session.query(BidDocument).filter(
            BidDocument.download_status == 'completed',
            BidDocument.processing_status == 'pending'
        ).limit(batch_count).all()

        logger.info(f"🔄 {len(pending_docs)}개 문서 처리 시작")

        success = 0
        failed = 0

        # 세마포어로 동시 처리 제한
        semaphore = asyncio.Semaphore(max_concurrent)

        async def process_with_semaphore(doc):
            async with semaphore:
                await processor._process_document(doc)
                session.refresh(doc)
                if doc.processing_status == 'completed':
                    return 'success'
                else:
                    return 'failed'

        # 병렬 처리
        tasks = [process_with_semaphore(doc) for doc in pending_docs]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        for result in results:
            if result == 'success':
                success += 1
            else:
                failed += 1

        elapsed_time = time.time() - start_time
        results = {'success': success, 'failed': failed}

        # 처리 결과
        success = results.get('success', 0)
        failed = results.get('failed', 0)

        logger.info(f"✅ 배치 처리 완료:")
        logger.info(f"  - 성공: {success}개")
        logger.info(f"  - 실패: {failed}개")
        logger.info(f"  - 소요 시간: {elapsed_time:.1f}초")
        logger.info(f"  - 처리 속도: {success/elapsed_time if elapsed_time > 0 else 0:.2f}개/초")

        # 성공률 계산
        total_processed = success + failed
        if total_processed > 0:
            success_rate = (success / total_processed) * 100
            logger.info(f"  - 성공률: {success_rate:.1f}%")

            if success_rate < 80:
                logger.warning("⚠️ 성공률이 80% 미만입니다. 문제를 확인하세요.")
                return False

        # 처리 후 리소스 체크
        monitor.log_resource_usage()

        # 남은 문서 수 확인
        remaining = session.execute(text("""
            SELECT COUNT(*)
            FROM bid_documents
            WHERE processing_status = 'pending'
            AND download_status = 'completed'
        """)).scalar()

        logger.info(f"📊 남은 대기 문서: {remaining}개")

        return True

    except Exception as e:
        logger.error(f"❌ 배치 처리 실패: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False
    finally:
        session.close()

async def main():
    """메인 실행 함수"""
    logger.info("=" * 60)
    logger.info("🚀 대용량 배치 처리 시작")
    logger.info(f"📅 시작 시간: {datetime.now()}")
    logger.info("=" * 60)

    # 배치 순서
    batch_sequence = ["small", "medium", "large", "xlarge"]

    for batch_size in batch_sequence:
        logger.info(f"\n{'=' * 40}")
        logger.info(f"Phase: {batch_size.upper()} 배치")
        logger.info(f"{'=' * 40}")

        success = await process_batch(batch_size)

        if not success:
            logger.error(f"❌ {batch_size.upper()} 배치 실패. 처리 중단.")
            break

        logger.info(f"✅ {batch_size.upper()} 배치 성공")

        # 다음 배치 전 대기
        if batch_size != batch_sequence[-1]:
            logger.info("⏳ 5초 후 다음 배치 시작...")
            await asyncio.sleep(5)

    # 최종 결과
    engine = create_engine(DATABASE_URL)
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT
                COUNT(*) as total,
                SUM(CASE WHEN processing_status = 'completed' THEN 1 ELSE 0 END) as completed,
                SUM(CASE WHEN processing_status = 'failed' THEN 1 ELSE 0 END) as failed
            FROM bid_documents
            WHERE download_status = 'completed'
        """)).first()

        total, completed, failed = result
        success_rate = (completed / total * 100) if total > 0 else 0

        logger.info("\n" + "=" * 60)
        logger.info("📊 최종 처리 결과")
        logger.info("=" * 60)
        logger.info(f"  - 전체 문서: {total}개")
        logger.info(f"  - 처리 완료: {completed}개")
        logger.info(f"  - 처리 실패: {failed}개")
        logger.info(f"  - 성공률: {success_rate:.1f}%")
        logger.info(f"📅 완료 시간: {datetime.now()}")
        logger.info("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())