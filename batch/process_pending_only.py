#!/usr/bin/env python
"""
Pending 문서만 처리하는 배치 스크립트
- API 수집 건너뛰기
- 다운로드와 처리만 진행
- 모든 pending 완료 후 이메일 발송
"""

import os
import sys
import time
from datetime import datetime
from pathlib import Path
from loguru import logger

# 프로젝트 루트 경로 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from batch.modules.downloader import DocumentDownloader
from batch.modules.processor import DocumentProcessorModule
from batch.modules.email_reporter import EmailReporter
from sqlalchemy import create_engine, text

# 로거 설정
log_dir = Path("logs")
log_dir.mkdir(exist_ok=True)
log_file = log_dir / f"pending_batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
logger.add(str(log_file), rotation="10 MB", retention="7 days", level="INFO")


class PendingBatchProcessor:
    """Pending 문서 전용 배치 프로세서"""

    def __init__(self):
        """초기화"""
        self.db_url = os.getenv('DATABASE_URL', 'postgresql://blockmeta@localhost:5432/odin_db')
        self.start_time = time.time()

        # 통계 초기화
        self.stats = {
            'initial_pending': 0,
            'downloaded': 0,
            'processed': 0,
            'failed': 0,
            'remaining_pending': 0
        }

    def check_pending_status(self):
        """Pending 문서 상태 확인"""
        engine = create_engine(self.db_url)
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT
                    COUNT(*) as total,
                    SUM(CASE WHEN download_status = 'completed' THEN 1 ELSE 0 END) as ready,
                    SUM(CASE WHEN download_status = 'pending' THEN 1 ELSE 0 END) as need_download
                FROM bid_documents
                WHERE processing_status = 'pending'
            """)).first()

            return {
                'total': result[0] or 0,
                'ready_to_process': result[1] or 0,
                'need_download': result[2] or 0
            }

    def run(self):
        """배치 실행"""
        logger.info("="*60)
        logger.info("🚀 Pending 문서 처리 배치 시작")
        logger.info(f"📅 실행 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info("="*60)

        try:
            # 1. 초기 상태 확인
            initial_status = self.check_pending_status()
            self.stats['initial_pending'] = initial_status['total']

            logger.info(f"📊 초기 Pending 상태:")
            logger.info(f"  - 총 Pending: {initial_status['total']}개")
            logger.info(f"  - 다운로드 필요: {initial_status['need_download']}개")
            logger.info(f"  - 처리 가능: {initial_status['ready_to_process']}개")

            if initial_status['total'] == 0:
                logger.info("✅ 처리할 pending 문서가 없습니다.")
                return

            # 2. 파일 다운로드 (필요한 경우)
            if initial_status['need_download'] > 0:
                logger.info("\n" + "="*40)
                logger.info("📥 Phase 1: 파일 다운로드")
                logger.info("="*40)

                downloader = DocumentDownloader(self.db_url)

                # 배치로 다운로드 (100개씩)
                batch_size = 100
                total_downloaded = 0

                while True:
                    result = downloader.download_pending(limit=batch_size)

                    if result['success'] == 0 and result['failed'] == 0:
                        break  # 더 이상 다운로드할 것이 없음

                    total_downloaded += result['success']
                    self.stats['downloaded'] = total_downloaded
                    self.stats['failed'] += result['failed']

                    logger.info(f"  배치 다운로드: 성공 {result['success']}, 실패 {result['failed']}")

                    # 실패한 것들 재시도
                    if result['failed'] > 0:
                        retry_result = downloader.retry_failed(max_retries=2)
                        total_downloaded += retry_result['success']
                        self.stats['downloaded'] = total_downloaded
                        logger.info(f"  재시도 결과: 성공 {retry_result['success']}")

                logger.info(f"✅ 다운로드 완료: 총 {total_downloaded}개")

            # 3. 문서 처리
            logger.info("\n" + "="*40)
            logger.info("🔧 Phase 2: 문서 처리")
            logger.info("="*40)

            processor = DocumentProcessorModule(self.db_url)

            # 처리 가능한 모든 문서 처리
            batch_size = 50
            total_processed = 0

            while True:
                # 현재 처리 가능한 문서 확인
                current_status = self.check_pending_status()

                if current_status['ready_to_process'] == 0:
                    break  # 더 이상 처리할 것이 없음

                result = processor.process_downloaded(limit=batch_size)

                if result['success'] == 0 and result['failed'] == 0:
                    break

                total_processed += result['success']
                self.stats['processed'] = total_processed
                self.stats['failed'] += result['failed']

                logger.info(f"  배치 처리: 성공 {result['success']}, 실패 {result['failed']}")

                # 진행 상황 표시
                remaining = current_status['total'] - total_processed
                progress = (total_processed / self.stats['initial_pending']) * 100
                logger.info(f"  진행률: {progress:.1f}% ({total_processed}/{self.stats['initial_pending']})")

            logger.info(f"✅ 처리 완료: 총 {total_processed}개")

            # 4. 최종 상태 확인
            final_status = self.check_pending_status()
            self.stats['remaining_pending'] = final_status['total']

            logger.info("\n" + "="*40)
            logger.info("📊 최종 결과")
            logger.info("="*40)
            logger.info(f"  - 초기 Pending: {self.stats['initial_pending']}개")
            logger.info(f"  - 다운로드: {self.stats['downloaded']}개")
            logger.info(f"  - 처리 완료: {self.stats['processed']}개")
            logger.info(f"  - 실패: {self.stats['failed']}개")
            logger.info(f"  - 남은 Pending: {self.stats['remaining_pending']}개")

            # 5. 이메일 보고서 발송
            if self.stats['remaining_pending'] == 0:
                logger.info("\n" + "="*40)
                logger.info("📧 모든 pending 처리 완료 - 이메일 발송")
                logger.info("="*40)

                reporter = EmailReporter(self.db_url)
                self.stats['execution_time'] = time.time() - self.start_time

                email_sent = reporter.send_batch_report(self.stats)
                json_path = reporter.save_json_report(self.stats)

                if email_sent:
                    logger.info("✅ 이메일 보고서 발송 완료")
                else:
                    logger.info(f"📄 JSON 보고서 저장: {json_path}")
            else:
                logger.warning(f"⚠️ {self.stats['remaining_pending']}개의 pending 문서가 남아있어 이메일을 발송하지 않습니다.")

        except Exception as e:
            logger.error(f"❌ 배치 실행 중 오류: {e}")
            import traceback
            logger.error(traceback.format_exc())

        finally:
            elapsed = time.time() - self.start_time
            logger.info(f"\n⏱️ 총 실행 시간: {elapsed:.1f}초 ({elapsed/60:.1f}분)")
            logger.info("🏁 배치 종료")


def main():
    """메인 함수"""
    processor = PendingBatchProcessor()
    processor.run()


if __name__ == "__main__":
    main()