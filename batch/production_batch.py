#!/usr/bin/env python
"""
ODIN-AI Production Batch System
메인 오케스트레이터 - 모든 모듈을 순차적으로 실행

실행 방법:
    python batch/production_batch.py
    TEST_MODE=true python batch/production_batch.py  # 테스트 모드
"""

import os
import sys
import time
import json
try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
from datetime import datetime
from pathlib import Path
from loguru import logger
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv 없으면 환경변수만 사용

# 프로젝트 루트 경로 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 모듈 임포트
from batch.modules.collector import APICollector
from batch.modules.downloader import DocumentDownloader
from batch.modules.processor import DocumentProcessorModule
from batch.modules.notification_matcher import NotificationMatcher
from batch.modules.email_reporter import EmailReporter

# 로거 설정
log_dir = Path("logs")
log_dir.mkdir(exist_ok=True)
log_file = log_dir / f"batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
logger.add(str(log_file), rotation="10 MB", retention="30 days", level="INFO")


class ProductionBatch:
    """프로덕션 배치 시스템 메인 클래스"""

    def __init__(self):
        """초기화"""
        self.test_mode = os.getenv('TEST_MODE', 'false').lower() == 'true'
        self.db_file_init = os.getenv('DB_FILE_INIT', 'false').lower() == 'true'
        self.db_url = os.getenv('DATABASE_URL', 'postgresql://blockmeta@localhost:5432/odin_db')
        self.start_time = time.time()

        # 통계 초기화
        self.stats = {
            'collected': 0,
            'downloaded': 0,
            'processed': 0,
            'failed': 0,
            'extracted_info': 0,
            'tags_created': 0,
            'attachments': 0,
            'notifications_created': 0,
            'emails_sent': 0
        }

        # 새로 수집된 공고 ID 저장
        self.new_bid_ids = []

        # 알림 실행 여부 (환경변수로 제어)
        self.enable_notification = os.getenv('ENABLE_NOTIFICATION', 'true').lower() == 'true'

    def run(self):
        """배치 실행 메인 함수"""
        logger.info("="*60)
        logger.info("🚀 ODIN-AI Production Batch 시작")
        logger.info(f"📅 실행 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"🔧 테스트 모드: {self.test_mode}")
        logger.info(f"🗂️ DB/파일 초기화: {self.db_file_init}")
        logger.info("="*60)

        try:
            # 1. DB/파일 완전 초기화 (DB_FILE_INIT=true인 경우)
            if self.db_file_init:
                logger.info("🗂️ DB_FILE_INIT=true: 완전 초기화 진행")
                self._complete_initialization()

            # 2. 테스트 모드 처리 (기존 유지)
            elif self.test_mode:
                logger.info("🧪 테스트 모드: DB 초기화 진행")
                self._initialize_test_mode()

            # 2. API 데이터 수집
            logger.info("\n" + "="*40)
            logger.info("📡 Phase 1: API 데이터 수집")
            logger.info("="*40)
            self._run_collector()

            # 3. 파일 다운로드
            logger.info("\n" + "="*40)
            logger.info("📥 Phase 2: 파일 다운로드")
            logger.info("="*40)
            self._run_downloader()

            # 4. 문서 처리
            logger.info("\n" + "="*40)
            logger.info("🔧 Phase 3: 문서 처리")
            logger.info("="*40)
            self._run_processor()

            # 5. 알림 매칭 (ENABLE_NOTIFICATION=true인 경우만)
            if self.enable_notification:
                logger.info("\n" + "="*40)
                logger.info("🔔 Phase 4: 알림 매칭")
                logger.info("="*40)
                self._run_notification_matcher()
            else:
                logger.info("\n⏭️ Phase 4: 알림 매칭 건너뜀 (ENABLE_NOTIFICATION=false)")

            # 6. 이메일 보고서 발송
            logger.info("\n" + "="*40)
            logger.info("📧 Phase 5: 보고서 발송")
            logger.info("="*40)
            self._send_report()

            # 7. 이벤트 발행 (Redis Pub/Sub)
            logger.info("\n" + "="*40)
            logger.info("📢 Phase 6: 이벤트 발행")
            logger.info("="*40)
            self._publish_event()

            # 7. 최종 통계
            self._print_final_stats()

        except Exception as e:
            logger.error(f"❌ 배치 실행 중 오류 발생: {e}")
            import traceback
            logger.error(traceback.format_exc())

            # 오류 발생 시에도 보고서 발송 시도
            try:
                self.stats['error'] = str(e)
                self._send_report()
            except:
                pass

        finally:
            elapsed = time.time() - self.start_time
            logger.info(f"\n⏱️ 총 실행 시간: {elapsed:.1f}초")
            logger.info("🏁 배치 종료")

    def _complete_initialization(self):
        """DB_FILE_INIT=true: 완전 초기화 (테이블 DROP + 파일 삭제)"""
        from sqlalchemy import create_engine, text
        import shutil

        logger.info("🗂️ 완전 초기화 시작: 테이블 DROP + 파일 삭제")

        engine = create_engine(self.db_url)
        with engine.connect() as conn:
            # 1. 모든 테이블 완전 삭제 (DROP)
            tables = [
                'bid_tag_relations',
                'bid_tags',
                'bid_schedule',
                'bid_extracted_info',
                'bid_attachments',
                'bid_documents',
                'bid_announcements',
                'bid_search_index'
            ]

            for table in tables:
                try:
                    conn.execute(text(f"DROP TABLE IF EXISTS {table} CASCADE"))
                    conn.commit()
                    logger.info(f"  🗑️ {table} 테이블 DROP 완료")
                except Exception as e:
                    logger.warning(f"  ⚠️ {table} DROP 실패: {e}")

            # 2. ORM으로 테이블 재생성
            try:
                from src.database.models import Base
                Base.metadata.create_all(engine)
                logger.info("  ✅ ORM 모델로 테이블 재생성 완료")
            except Exception as e:
                logger.error(f"  ❌ 테이블 재생성 실패: {e}")

        # 3. storage 디렉토리 완전 삭제 후 재생성
        storage_path = Path("./storage")
        if storage_path.exists():
            shutil.rmtree(storage_path)
            logger.info("  🗑️ storage 디렉토리 완전 삭제")

        # 필수 디렉토리 재생성
        storage_path.mkdir(exist_ok=True)
        (storage_path / "documents").mkdir(exist_ok=True)
        (storage_path / "markdown").mkdir(exist_ok=True)
        logger.info("  📁 storage 디렉토리 구조 재생성")

        # 4. logs 디렉토리 정리 (선택적)
        logs_path = Path("./logs")
        if logs_path.exists():
            # 오래된 로그 파일만 삭제 (현재 실행 중인 로그는 유지)
            import glob
            old_logs = glob.glob(str(logs_path / "batch_*.log"))
            for log_file in old_logs[:-5]:  # 최근 5개만 유지
                try:
                    Path(log_file).unlink()
                except:
                    pass
            logger.info("  🧹 오래된 로그 파일 정리")

        logger.info("🎯 완전 초기화 완료: 새로운 환경 준비됨")

    def _initialize_test_mode(self):
        """테스트 모드 초기화"""
        from sqlalchemy import create_engine, text

        engine = create_engine(self.db_url)
        with engine.connect() as conn:
            # 테이블 데이터 삭제
            tables = [
                'bid_tag_relations',
                'bid_tags',
                'bid_schedule',
                'bid_extracted_info',
                'bid_attachments',
                'bid_documents',
                'bid_announcements'
            ]

            for table in tables:
                try:
                    conn.execute(text(f"DELETE FROM {table}"))
                    conn.commit()
                    logger.info(f"  ✅ {table} 테이블 초기화")
                except Exception as e:
                    logger.warning(f"  ⚠️ {table} 초기화 실패: {e}")

            # storage 디렉토리 정리
            storage_path = Path("./storage")
            if storage_path.exists():
                import shutil
                for subdir in ['documents', 'markdown']:
                    dir_path = storage_path / subdir
                    if dir_path.exists():
                        shutil.rmtree(dir_path)
                        dir_path.mkdir(parents=True, exist_ok=True)
                        logger.info(f"  ✅ {dir_path} 디렉토리 초기화")

    def _run_collector(self):
        """API 수집 실행"""
        try:
            collector = APICollector(self.db_url)

            # 날짜 설정 (환경변수 또는 오늘 날짜)
            from datetime import datetime
            start_str = os.getenv('BATCH_START_DATE')
            end_str = os.getenv('BATCH_END_DATE')

            if start_str:
                start_date = datetime.strptime(start_str, '%Y-%m-%d')
            else:
                start_date = datetime.now()

            if end_str:
                end_date = datetime.strptime(end_str, '%Y-%m-%d')
            else:
                end_date = start_date

            logger.info(f"📅 수집 기간: {start_date.strftime('%Y-%m-%d')} ~ {end_date.strftime('%Y-%m-%d')}")

            if self.test_mode:
                result = collector.collect_by_date_range(
                    start_date=start_date,
                    end_date=end_date,
                    num_of_rows=50,     # 페이지당 50개
                    max_pages=2         # 최대 2페이지 (100건)
                )
            else:
                result = collector.collect_by_date_range(
                    start_date=start_date,
                    end_date=end_date,
                    num_of_rows=100,    # 페이지당 100개
                    max_pages=None      # 모든 페이지 수집
                )

            if result['status'] == 'success':
                self.stats['collected'] = result.get('saved', 0)
                # 새로 수집된 공고 ID 저장
                self.new_bid_ids = result.get('new_bid_ids', [])
                logger.info(f"✅ 수집 완료: {self.stats['collected']}건 (신규: {len(self.new_bid_ids)}건)")
            else:
                logger.error(f"❌ 수집 실패: {result.get('message')}")

        except Exception as e:
            logger.error(f"❌ API 수집 오류: {e}")

    def _run_downloader(self):
        """파일 다운로드 실행"""
        try:
            downloader = DocumentDownloader(self.db_url)

            # 대기 중인 파일 다운로드
            download_limit = 20 if self.test_mode else None  # 프로덕션에서는 제한 없음
            result = downloader.download_pending(limit=download_limit)

            self.stats['downloaded'] = result.get('success', 0)
            self.stats['failed'] += result.get('failed', 0)

            # 실패한 파일 재시도
            if result.get('failed', 0) > 0:
                logger.info("🔄 실패한 다운로드 재시도")
                retry_result = downloader.retry_failed(max_retries=2)
                self.stats['downloaded'] += retry_result.get('success', 0)

        except Exception as e:
            logger.error(f"❌ 다운로드 오류: {e}")

    def _run_processor(self):
        """문서 처리 실행"""
        try:
            processor = DocumentProcessorModule(self.db_url)

            # 다운로드 완료된 문서 처리
            process_limit = 20 if self.test_mode else None  # 프로덕션에서는 제한 없음
            result = processor.process_downloaded(limit=process_limit)

            self.stats['processed'] = result.get('success', 0)
            self.stats['failed'] += result.get('failed', 0)
            self.stats['extracted_info'] = result.get('info_extracted', 0)
            self.stats['extracted_info_count'] = result.get('info_extracted', 0)  # 이메일용
            self.stats['tags_created'] = result.get('tags_created', 0)
            self.stats['attachments'] = result.get('attachments', 0)
            self.stats['extracted_by_category'] = result.get('extracted_by_category', {})

        except Exception as e:
            logger.error(f"❌ 문서 처리 오류: {e}")

    def _run_notification_matcher(self):
        """알림 매칭 실행"""
        try:
            matcher = NotificationMatcher(self.db_url)

            # 새로 수집된 입찰공고에 대해 알림 매칭
            if self.new_bid_ids:
                logger.info(f"🔍 신규 입찰 {len(self.new_bid_ids)}건에 대해 알림 규칙 매칭 중...")
                result = matcher.process_new_bids(since_hours=24)  # 타임존 차이 고려하여 24시간으로 설정

                self.stats['notifications_created'] = result.get('notifications_created', 0)
                self.stats['emails_sent'] = result.get('emails_sent', 0)

                logger.info(f"✅ 알림 매칭 완료:")
                logger.info(f"   - 처리 대상: {result.get('processed_bids', 0)}건")
                logger.info(f"   - 알림 생성: {result.get('notifications_created', 0)}개")
                logger.info(f"   - 이메일 발송: {result.get('emails_sent', 0)}개")
            else:
                logger.info("💡 신규 입찰공고가 없어 알림 매칭을 건너뜁니다.")

        except Exception as e:
            logger.error(f"❌ 알림 매칭 오류: {e}")
            import traceback
            logger.error(traceback.format_exc())

    def _send_report(self):
        """이메일 보고서 발송 - 모든 문서 처리 완료 후에만 발송"""
        try:
            # 진행 중인 작업이 있는지 확인
            from sqlalchemy import create_engine, text
            engine = create_engine(self.db_url)
            with engine.connect() as conn:
                # pending 상태 문서 확인
                pending_result = conn.execute(text("""
                    SELECT COUNT(*) FROM bid_documents
                    WHERE download_status = 'completed'
                    AND processing_status = 'pending'
                """)).scalar()

                if pending_result > 0:
                    logger.warning(f"⚠️ 아직 {pending_result}개 문서가 처리 대기 중입니다.")
                    logger.warning("📧 모든 문서 처리 완료 후 이메일을 발송합니다.")

                    # JSON 보고서만 저장
                    reporter = EmailReporter(self.db_url)
                    self.stats['execution_time'] = time.time() - self.start_time
                    json_path = reporter.save_json_report(self.stats)
                    logger.info(f"📄 중간 보고서 저장: {json_path}")
                    return

            # 모든 처리가 완료된 경우에만 이메일 발송
            reporter = EmailReporter(self.db_url)

            # 실행 시간 추가
            self.stats['execution_time'] = time.time() - self.start_time

            # 이메일 발송
            email_sent = reporter.send_batch_report(self.stats)

            # JSON 보고서 저장
            json_path = reporter.save_json_report(self.stats)

            if email_sent:
                logger.info("✅ 이메일 보고서 발송 완료")
            else:
                logger.info(f"📄 JSON 보고서만 저장: {json_path}")

        except Exception as e:
            logger.error(f"❌ 보고서 발송 오류: {e}")

    def _publish_event(self):
        """배치 완료 이벤트 발행 (Redis Pub/Sub)"""
        if not REDIS_AVAILABLE:
            logger.warning("⚠️ Redis 모듈이 설치되지 않아 이벤트 발행을 건너뜁니다.")
            return

        try:
            # Redis 연결
            redis_client = redis.Redis(
                host=os.getenv('REDIS_HOST', 'localhost'),
                port=int(os.getenv('REDIS_PORT', 6379)),
                decode_responses=True
            )

            # 이벤트 데이터 생성
            event_data = {
                "type": "BATCH_COMPLETED",
                "timestamp": datetime.now().isoformat(),
                "stats": {
                    "collected": self.stats['collected'],
                    "downloaded": self.stats['downloaded'],
                    "processed": self.stats['processed'],
                    "failed": self.stats['failed'],
                    "new_bids": len(self.new_bid_ids),
                    "extracted_info": self.stats['extracted_info'],
                    "tags_created": self.stats['tags_created']
                },
                "new_bid_ids": self.new_bid_ids[:100],  # 최대 100개만 전송
                "execution_time_minutes": round((time.time() - self.start_time) / 60, 1)
            }

            # 이벤트 발행
            channel = 'batch:completed'
            redis_client.publish(channel, json.dumps(event_data, ensure_ascii=False))
            logger.info(f"✅ 이벤트 발행 성공: {channel}")
            logger.info(f"   - 신규 공고: {len(self.new_bid_ids)}건")
            logger.info(f"   - 처리 완료: {self.stats['processed']}건")

            # 이벤트를 큐에도 저장 (백업용)
            redis_client.lpush('event_queue', json.dumps(event_data, ensure_ascii=False))
            redis_client.expire('event_queue', 86400)  # 24시간 유지

        except Exception as e:
            logger.warning(f"⚠️ 이벤트 발행 실패 (배치는 정상 완료): {str(e)}")
            logger.warning("   알림 서비스가 실행 중이지 않을 수 있습니다.")

    def _print_final_stats(self):
        """최종 통계 출력"""
        logger.info("\n" + "="*60)
        logger.info("📊 최종 실행 결과")
        logger.info("="*60)
        logger.info(f"  📡 API 수집: {self.stats['collected']}건 (신규: {len(self.new_bid_ids)}건)")
        logger.info(f"  📥 다운로드: {self.stats['downloaded']}건")
        logger.info(f"  🔧 처리 완료: {self.stats['processed']}건")
        logger.info(f"  ❌ 실패: {self.stats['failed']}건")
        logger.info(f"  📋 추출 정보: {self.stats['extracted_info']}개")
        logger.info(f"  🏷️ 생성 태그: {self.stats['tags_created']}개")
        logger.info(f"  📎 첨부파일: {self.stats['attachments']}개")

        # 알림 통계 (실행된 경우만)
        if self.enable_notification:
            logger.info(f"  🔔 알림 생성: {self.stats['notifications_created']}개")
            logger.info(f"  📧 이메일 발송: {self.stats['emails_sent']}개")

        # 성공률 계산
        total_attempts = self.stats['downloaded'] + self.stats['failed']
        if total_attempts > 0:
            success_rate = (self.stats['processed'] / total_attempts) * 100
            logger.info(f"  📈 전체 성공률: {success_rate:.1f}%")


def main():
    """메인 함수

    사용법:
        python batch/production_batch.py                    # 오늘 날짜
        python batch/production_batch.py 2025-09-25        # 특정 날짜
        python batch/production_batch.py 2025-09-20 2025-09-25  # 날짜 범위
    """
    import argparse
    from datetime import datetime

    parser = argparse.ArgumentParser(description='ODIN-AI 배치 프로세스')
    parser.add_argument('start_date', nargs='?', help='시작 날짜 (YYYY-MM-DD)', default=None)
    parser.add_argument('end_date', nargs='?', help='종료 날짜 (YYYY-MM-DD)', default=None)
    parser.add_argument('--test', action='store_true', help='테스트 모드')
    parser.add_argument('--init', action='store_true', help='DB/파일 초기화')

    args = parser.parse_args()

    # 환경변수 설정
    if args.test:
        os.environ['TEST_MODE'] = 'true'
    if args.init:
        os.environ['DB_FILE_INIT'] = 'true'

    # 날짜 파싱
    if args.start_date:
        try:
            start_date = datetime.strptime(args.start_date, '%Y-%m-%d')
            os.environ['BATCH_START_DATE'] = args.start_date
        except ValueError:
            print(f"❌ 잘못된 날짜 형식: {args.start_date} (YYYY-MM-DD 형식 필요)")
            sys.exit(1)
    else:
        start_date = datetime.now()

    if args.end_date:
        try:
            end_date = datetime.strptime(args.end_date, '%Y-%m-%d')
            os.environ['BATCH_END_DATE'] = args.end_date
        except ValueError:
            print(f"❌ 잘못된 날짜 형식: {args.end_date} (YYYY-MM-DD 형식 필요)")
            sys.exit(1)
    else:
        end_date = start_date

    print(f"📅 배치 실행 날짜: {start_date.strftime('%Y-%m-%d')} ~ {end_date.strftime('%Y-%m-%d')}")

    batch = ProductionBatch()
    batch.run()


if __name__ == "__main__":
    main()