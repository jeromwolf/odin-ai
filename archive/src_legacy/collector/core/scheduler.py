"""
데이터 수집 스케줄러
정기적인 데이터 수집 작업 관리
"""

import asyncio
import signal
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger
from loguru import logger

from shared.config import settings
from collector.services.api_collector import APICollector
from collector.services.document_processor import DocumentProcessor


class CollectorScheduler:
    """데이터 수집 스케줄러"""

    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.running = False
        self.jobs: Dict[str, Any] = {}

        # 시그널 핸들러 등록
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def _signal_handler(self, signum, frame):
        """시그널 핸들러"""
        logger.info(f"스케줄러 종료 시그널 수신: {signum}")
        self.shutdown()

    def start(self):
        """스케줄러 시작"""
        logger.info("데이터 수집 스케줄러 시작")

        # 기본 작업 스케줄 등록
        self._register_jobs()

        # 스케줄러 시작
        self.scheduler.start()
        self.running = True

        logger.info("스케줄러 시작 완료")

    def shutdown(self):
        """스케줄러 종료"""
        if self.running:
            logger.info("스케줄러 종료 중...")
            self.running = False
            self.scheduler.shutdown(wait=True)
            logger.info("스케줄러 종료 완료")

    def _register_jobs(self):
        """작업 스케줄 등록"""

        # 1. 정기 데이터 수집 (30분마다)
        self.scheduler.add_job(
            self._collect_data_job,
            IntervalTrigger(minutes=settings.collection_interval_minutes),
            id='collect_data',
            name='정기 데이터 수집',
            max_instances=1,
            coalesce=True,
            replace_existing=True
        )
        logger.info(f"정기 수집 작업 등록: {settings.collection_interval_minutes}분 간격")

        # 2. 문서 처리 (15분마다)
        self.scheduler.add_job(
            self._process_documents_job,
            IntervalTrigger(minutes=15),
            id='process_documents',
            name='문서 처리',
            max_instances=1,
            coalesce=True,
            replace_existing=True
        )
        logger.info("문서 처리 작업 등록: 15분 간격")

        # 3. 헬스체크 (5분마다)
        self.scheduler.add_job(
            self._health_check_job,
            IntervalTrigger(minutes=5),
            id='health_check',
            name='헬스체크',
            max_instances=1,
            coalesce=True,
            replace_existing=True
        )
        logger.info("헬스체크 작업 등록: 5분 간격")

        # 4. 일일 통계 리포트 (매일 오전 9시)
        self.scheduler.add_job(
            self._daily_report_job,
            CronTrigger(hour=9, minute=0),
            id='daily_report',
            name='일일 통계 리포트',
            max_instances=1,
            coalesce=True,
            replace_existing=True
        )
        logger.info("일일 리포트 작업 등록: 매일 오전 9시")

        # 5. 오래된 로그 정리 (매일 새벽 2시)
        self.scheduler.add_job(
            self._cleanup_logs_job,
            CronTrigger(hour=2, minute=0),
            id='cleanup_logs',
            name='로그 정리',
            max_instances=1,
            coalesce=True,
            replace_existing=True
        )
        logger.info("로그 정리 작업 등록: 매일 새벽 2시")

    async def _collect_data_job(self):
        """정기 데이터 수집 작업"""
        job_start = datetime.utcnow()
        logger.info("정기 데이터 수집 작업 시작")

        try:
            # API 데이터 수집
            api_collector = APICollector()
            collected_data = await api_collector.collect_latest_bids()

            execution_time = (datetime.utcnow() - job_start).total_seconds()
            logger.info(
                f"정기 수집 완료: {len(collected_data)}건 수집, "
                f"실행시간 {execution_time:.2f}초"
            )

        except Exception as e:
            execution_time = (datetime.utcnow() - job_start).total_seconds()
            logger.error(f"정기 수집 실패: {e}, 실행시간 {execution_time:.2f}초")

    async def _process_documents_job(self):
        """문서 처리 작업"""
        job_start = datetime.utcnow()
        logger.info("문서 처리 작업 시작")

        try:
            # 문서 처리
            doc_processor = DocumentProcessor()
            processed_count = await doc_processor.process_pending_documents(limit=20)

            execution_time = (datetime.utcnow() - job_start).total_seconds()
            logger.info(
                f"문서 처리 완료: {processed_count}건 처리, "
                f"실행시간 {execution_time:.2f}초"
            )

        except Exception as e:
            execution_time = (datetime.utcnow() - job_start).total_seconds()
            logger.error(f"문서 처리 실패: {e}, 실행시간 {execution_time:.2f}초")

    async def _health_check_job(self):
        """헬스체크 작업"""
        try:
            from shared.database import check_connection

            # 데이터베이스 연결 확인
            if check_connection():
                logger.debug("헬스체크 정상: 데이터베이스 연결 OK")
            else:
                logger.error("헬스체크 실패: 데이터베이스 연결 불가")

            # 스케줄러 상태 확인
            running_jobs = [job.id for job in self.scheduler.get_jobs()]
            logger.debug(f"실행 중인 작업: {len(running_jobs)}개 - {running_jobs}")

        except Exception as e:
            logger.error(f"헬스체크 오류: {e}")

    async def _daily_report_job(self):
        """일일 통계 리포트 작업"""
        logger.info("일일 통계 리포트 작성 시작")

        try:
            from shared.database import get_db_context
            from shared.models import CollectionLog, BidDocument

            # 어제 날짜 계산
            yesterday = datetime.utcnow().date() - timedelta(days=1)
            start_time = datetime.combine(yesterday, datetime.min.time())
            end_time = datetime.combine(yesterday, datetime.max.time())

            with get_db_context() as db:
                # 수집 통계
                collection_stats = db.query(CollectionLog).filter(
                    CollectionLog.collection_date >= start_time,
                    CollectionLog.collection_date <= end_time
                ).all()

                # 문서 처리 통계
                doc_stats = db.query(BidDocument).filter(
                    BidDocument.updated_at >= start_time,
                    BidDocument.updated_at <= end_time,
                    BidDocument.processing_status == 'completed'
                ).count()

            # 통계 정보 로깅
            total_collected = sum(log.total_found or 0 for log in collection_stats)
            total_new = sum(log.new_items or 0 for log in collection_stats)
            successful_collections = len([log for log in collection_stats if log.status == 'completed'])

            logger.info(
                f"📊 일일 리포트 ({yesterday}):\n"
                f"  • 수집 작업: {len(collection_stats)}회 실행, {successful_collections}회 성공\n"
                f"  • 총 수집: {total_collected}건\n"
                f"  • 신규 데이터: {total_new}건\n"
                f"  • 문서 처리: {doc_stats}건"
            )

        except Exception as e:
            logger.error(f"일일 리포트 작성 실패: {e}")

    async def _cleanup_logs_job(self):
        """오래된 로그 정리 작업"""
        logger.info("로그 정리 작업 시작")

        try:
            from shared.database import get_db_context
            from shared.models import CollectionLog

            # 30일 이전 로그 삭제
            cutoff_date = datetime.utcnow() - timedelta(days=30)

            with get_db_context() as db:
                deleted_count = db.query(CollectionLog).filter(
                    CollectionLog.collection_date < cutoff_date
                ).delete()

                logger.info(f"로그 정리 완료: {deleted_count}건 삭제")

        except Exception as e:
            logger.error(f"로그 정리 실패: {e}")

    def get_job_status(self) -> Dict[str, Any]:
        """작업 상태 조회"""
        if not self.running:
            return {"status": "stopped", "jobs": []}

        jobs = []
        for job in self.scheduler.get_jobs():
            job_info = {
                "id": job.id,
                "name": job.name,
                "next_run": job.next_run_time,
                "trigger": str(job.trigger)
            }
            jobs.append(job_info)

        return {
            "status": "running",
            "jobs": jobs,
            "scheduler_state": self.scheduler.state
        }

    def pause_job(self, job_id: str) -> bool:
        """작업 일시정지"""
        try:
            self.scheduler.pause_job(job_id)
            logger.info(f"작업 일시정지: {job_id}")
            return True
        except Exception as e:
            logger.error(f"작업 일시정지 실패: {e}")
            return False

    def resume_job(self, job_id: str) -> bool:
        """작업 재개"""
        try:
            self.scheduler.resume_job(job_id)
            logger.info(f"작업 재개: {job_id}")
            return True
        except Exception as e:
            logger.error(f"작업 재개 실패: {e}")
            return False

    def trigger_job(self, job_id: str) -> bool:
        """작업 즉시 실행"""
        try:
            job = self.scheduler.get_job(job_id)
            if job:
                self.scheduler.modify_job(job_id, next_run_time=datetime.utcnow())
                logger.info(f"작업 즉시 실행 예약: {job_id}")
                return True
            else:
                logger.error(f"작업을 찾을 수 없음: {job_id}")
                return False
        except Exception as e:
            logger.error(f"작업 실행 실패: {e}")
            return False