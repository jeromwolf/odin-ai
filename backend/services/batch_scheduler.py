"""
APScheduler 기반 배치 스케줄러 서비스

batch_schedules 테이블에서 활성 스케줄을 읽어
CronTrigger 기반 정기 배치를 실행합니다.
"""

import os
import subprocess
import shutil
import logging
from datetime import datetime
from typing import Optional

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

logger = logging.getLogger(__name__)


class BatchSchedulerService:
    """APScheduler 기반 배치 스케줄러 (싱글톤)"""

    def __init__(self):
        self.scheduler: Optional[AsyncIOScheduler] = None
        self._started = False

    async def start(self):
        """스케줄러 시작 및 DB에서 활성 스케줄 로드"""
        if self._started:
            logger.warning("배치 스케줄러가 이미 실행 중입니다")
            return

        self.scheduler = AsyncIOScheduler(timezone="Asia/Seoul")
        self.scheduler.start()
        self._started = True
        logger.info("APScheduler 시작됨 (timezone=Asia/Seoul)")

        await self._load_schedules_from_db()

    async def shutdown(self):
        """스케줄러 종료"""
        if self.scheduler and self._started:
            self.scheduler.shutdown(wait=False)
            self._started = False
            logger.info("배치 스케줄러 종료됨")

    async def _load_schedules_from_db(self):
        """DB에서 활성 스케줄을 읽어 APScheduler 잡으로 등록"""
        try:
            from database import get_db_connection
            from psycopg2.extras import RealDictCursor

            with get_db_connection() as conn:
                cursor = conn.cursor(cursor_factory=RealDictCursor)
                cursor.execute("""
                    SELECT id, label, schedule_hour, schedule_minute,
                           days_of_week, is_active, options
                    FROM batch_schedules
                    WHERE is_active = true
                    ORDER BY id
                """)
                schedules = cursor.fetchall()

            for schedule in schedules:
                self._add_job_from_schedule(schedule)

            logger.info(f"배치 스케줄 {len(schedules)}개 로드 완료")

        except Exception as e:
            logger.warning(f"배치 스케줄 로드 실패 (DB 연결 오류): {e}")

    def _add_job_from_schedule(self, schedule: dict):
        """개별 스케줄 레코드를 APScheduler 잡으로 등록"""
        if not self.scheduler:
            return

        schedule_id = schedule["id"]
        job_id = f"batch_schedule_{schedule_id}"

        # days_of_week 매핑: DB "0,1,2,3,4" -> APScheduler "mon,tue,wed,thu,fri"
        day_of_week = None
        if schedule.get("days_of_week"):
            raw = schedule["days_of_week"].strip()
            if raw:
                day_of_week = raw  # APScheduler CronTrigger accepts "0,1,2,3,4"

        trigger = CronTrigger(
            hour=schedule["schedule_hour"],
            minute=schedule["schedule_minute"],
            day_of_week=day_of_week,
            timezone="Asia/Seoul",
        )

        options = schedule.get("options") or {}

        self.scheduler.add_job(
            self._run_batch,
            trigger=trigger,
            id=job_id,
            name=schedule.get("label", f"배치 #{schedule_id}"),
            kwargs={"schedule_id": schedule_id, "options": options},
            max_instances=1,
            coalesce=True,
            replace_existing=True,
        )

        logger.info(
            f"스케줄 등록: id={schedule_id}, "
            f"label={schedule.get('label')}, "
            f"시간={schedule['schedule_hour']:02d}:{schedule['schedule_minute']:02d}, "
            f"요일={day_of_week or '매일'}"
        )

    def _run_batch(self, schedule_id: int, options: dict):
        """
        production_batch.py를 subprocess로 실행
        (admin_batch.py execute_batch_manual과 동일한 패턴)
        """
        from pathlib import Path

        try:
            today = datetime.now().strftime('%Y-%m-%d')

            # 환경변수 설정
            env = os.environ.copy()
            db_url = os.getenv('DATABASE_URL')
            if not db_url:
                logger.error(f"스케줄 #{schedule_id}: DATABASE_URL 미설정, 배치 건너뜀")
                return

            env['DATABASE_URL'] = db_url
            env['BATCH_START_DATE'] = today
            env['BATCH_END_DATE'] = today
            env['TRIGGERED_BY'] = 'scheduler'
            env['BID_API_KEY'] = os.getenv('BID_API_KEY', '')

            # options JSONB에서 플래그 추출
            env['ENABLE_NOTIFICATION'] = "true" if options.get("enable_notification", True) else "false"
            env['ENABLE_EMBEDDING'] = "true" if options.get("enable_embedding", False) else "false"
            env['ENABLE_GRAPH_SYNC'] = "true" if options.get("enable_graph_sync", False) else "false"
            env['ENABLE_GRAPHRAG'] = "true" if options.get("enable_graphrag", False) else "false"
            env['ENABLE_AWARD_COLLECTION'] = "true" if options.get("enable_award_collection", False) else "false"
            env['ENABLE_DAILY_DIGEST'] = "true" if options.get("enable_daily_digest", False) else "false"

            # 프로젝트 루트 및 배치 스크립트 경로
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            batch_script = os.path.join(project_root, 'batch', 'production_batch.py')

            # 가상환경 Python 경로 (venv_test 우선, 없으면 시스템 python3)
            venv_python = os.path.join(project_root, 'venv_test', 'bin', 'python3')
            if not os.path.exists(venv_python):
                venv_python = shutil.which('python3') or 'python3'

            # 로그 파일
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            log_dir = Path(project_root) / 'backend' / 'logs'
            log_dir.mkdir(exist_ok=True)

            stdout_log = log_dir / f"scheduled_{schedule_id}_{timestamp}_stdout.log"
            stderr_log = log_dir / f"scheduled_{schedule_id}_{timestamp}_stderr.log"

            stdout_fh = open(stdout_log, 'w', buffering=1)
            stderr_fh = open(stderr_log, 'w', buffering=1)

            process = subprocess.Popen(
                [venv_python, batch_script],
                env=env,
                stdout=stdout_fh,
                stderr=stderr_fh,
                start_new_session=True,
                cwd=project_root,
            )

            logger.info(
                f"스케줄 배치 실행: schedule_id={schedule_id}, "
                f"PID={process.pid}, 날짜={today}"
            )

            # 프로세스 완료 대기 및 파일 핸들 정리
            process.wait()
            stdout_fh.close()
            stderr_fh.close()

            exit_code = process.returncode
            if exit_code == 0:
                logger.info(f"스케줄 배치 완료: schedule_id={schedule_id}, exit_code=0")
            else:
                logger.warning(f"스케줄 배치 비정상 종료: schedule_id={schedule_id}, exit_code={exit_code}")

        except Exception as e:
            logger.error(f"스케줄 배치 실행 실패: schedule_id={schedule_id}, error={e}")

    async def reload_schedules(self):
        """모든 잡 제거 후 DB에서 재로드"""
        if not self.scheduler:
            logger.warning("스케줄러가 시작되지 않았습니다")
            return

        # 기존 배치 스케줄 잡 전부 제거
        for job in self.scheduler.get_jobs():
            if job.id.startswith("batch_schedule_"):
                job.remove()

        logger.info("기존 배치 스케줄 잡 전부 제거됨")

        await self._load_schedules_from_db()

    def get_status(self) -> dict:
        """스케줄러 상태 및 등록된 잡 목록 반환"""
        if not self.scheduler or not self._started:
            return {
                "running": False,
                "jobs": [],
            }

        jobs = []
        for job in self.scheduler.get_jobs():
            if job.id.startswith("batch_schedule_"):
                jobs.append({
                    "job_id": job.id,
                    "name": job.name,
                    "next_run_time": job.next_run_time.isoformat() if job.next_run_time else None,
                    "schedule_id": int(job.id.replace("batch_schedule_", "")),
                })

        return {
            "running": self.scheduler.running,
            "jobs": jobs,
        }

    def get_next_run_for_schedule(self, schedule_id: int) -> Optional[str]:
        """특정 스케줄의 다음 실행 시각 반환"""
        if not self.scheduler or not self._started:
            return None

        job_id = f"batch_schedule_{schedule_id}"
        job = self.scheduler.get_job(job_id)
        if job and job.next_run_time:
            return job.next_run_time.isoformat()
        return None


# 싱글톤 인스턴스
batch_scheduler = BatchSchedulerService()
