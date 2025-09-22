"""
수집기 데몬 모드
백그라운드에서 실행되는 데몬 프로세스
스케줄러 + 모니터링 + 웹 인터페이스
"""

import asyncio
import signal
import sys
from datetime import datetime
from typing import Optional
from loguru import logger
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse

from shared.config import settings
from collector.core.scheduler import CollectorScheduler


class CollectorDaemon:
    """수집기 데몬"""

    def __init__(self):
        self.scheduler: Optional[CollectorScheduler] = None
        self.web_app: Optional[FastAPI] = None
        self.web_server: Optional[uvicorn.Server] = None
        self.running = False

        # 시그널 핸들러 등록
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

        # 웹 애플리케이션 설정
        self._setup_web_app()

    def _signal_handler(self, signum, frame):
        """시그널 핸들러"""
        logger.info(f"데몬 종료 시그널 수신: {signum}")
        self.stop()

    def _setup_web_app(self):
        """웹 애플리케이션 설정"""
        self.web_app = FastAPI(
            title="Odin-AI Collector Daemon",
            description="데이터 수집기 모니터링 및 제어 API",
            version="1.0.0"
        )

        # 라우트 등록
        self._register_routes()

    def _register_routes(self):
        """API 라우트 등록"""

        @self.web_app.get("/")
        async def root():
            """루트 엔드포인트"""
            return {
                "service": "Odin-AI Collector Daemon",
                "version": "1.0.0",
                "status": "running" if self.running else "stopped",
                "timestamp": datetime.utcnow().isoformat()
            }

        @self.web_app.get("/health")
        async def health_check():
            """헬스체크"""
            try:
                from shared.database import check_connection

                db_status = "ok" if check_connection() else "error"
                scheduler_status = "running" if self.scheduler and self.scheduler.running else "stopped"

                return {
                    "status": "healthy" if db_status == "ok" and scheduler_status == "running" else "unhealthy",
                    "database": db_status,
                    "scheduler": scheduler_status,
                    "timestamp": datetime.utcnow().isoformat()
                }

            except Exception as e:
                logger.error(f"헬스체크 오류: {e}")
                return JSONResponse(
                    status_code=500,
                    content={
                        "status": "unhealthy",
                        "error": str(e),
                        "timestamp": datetime.utcnow().isoformat()
                    }
                )

        @self.web_app.get("/status")
        async def get_status():
            """상태 조회"""
            if not self.scheduler:
                return {
                    "daemon": "stopped",
                    "scheduler": None
                }

            return {
                "daemon": "running" if self.running else "stopped",
                "scheduler": self.scheduler.get_job_status(),
                "timestamp": datetime.utcnow().isoformat()
            }

        @self.web_app.post("/jobs/{job_id}/pause")
        async def pause_job(job_id: str):
            """작업 일시정지"""
            if not self.scheduler:
                raise HTTPException(status_code=503, detail="스케줄러가 실행되지 않음")

            success = self.scheduler.pause_job(job_id)
            if success:
                return {"message": f"작업 '{job_id}' 일시정지됨"}
            else:
                raise HTTPException(status_code=400, detail="작업 일시정지 실패")

        @self.web_app.post("/jobs/{job_id}/resume")
        async def resume_job(job_id: str):
            """작업 재개"""
            if not self.scheduler:
                raise HTTPException(status_code=503, detail="스케줄러가 실행되지 않음")

            success = self.scheduler.resume_job(job_id)
            if success:
                return {"message": f"작업 '{job_id}' 재개됨"}
            else:
                raise HTTPException(status_code=400, detail="작업 재개 실패")

        @self.web_app.post("/jobs/{job_id}/trigger")
        async def trigger_job(job_id: str):
            """작업 즉시 실행"""
            if not self.scheduler:
                raise HTTPException(status_code=503, detail="스케줄러가 실행되지 않음")

            success = self.scheduler.trigger_job(job_id)
            if success:
                return {"message": f"작업 '{job_id}' 실행 예약됨"}
            else:
                raise HTTPException(status_code=400, detail="작업 실행 실패")

        @self.web_app.get("/logs/collection")
        async def get_collection_logs():
            """수집 로그 조회"""
            try:
                from shared.database import get_db_context
                from shared.models import CollectionLog

                with get_db_context() as db:
                    logs = db.query(CollectionLog).order_by(
                        CollectionLog.collection_date.desc()
                    ).limit(50).all()

                    return {
                        "logs": [
                            {
                                "id": log.id,
                                "type": log.collection_type,
                                "date": log.collection_date.isoformat(),
                                "status": log.status,
                                "total_found": log.total_found,
                                "new_items": log.new_items,
                                "start_time": log.start_time.isoformat() if log.start_time else None,
                                "end_time": log.end_time.isoformat() if log.end_time else None,
                                "error_message": log.error_message
                            }
                            for log in logs
                        ]
                    }

            except Exception as e:
                logger.error(f"로그 조회 오류: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.web_app.get("/stats/today")
        async def get_today_stats():
            """오늘 통계"""
            try:
                from shared.database import get_db_context
                from shared.models import CollectionLog, BidDocument

                today = datetime.utcnow().date()
                start_time = datetime.combine(today, datetime.min.time())
                end_time = datetime.combine(today, datetime.max.time())

                with get_db_context() as db:
                    # 수집 통계
                    collection_logs = db.query(CollectionLog).filter(
                        CollectionLog.collection_date >= start_time,
                        CollectionLog.collection_date <= end_time
                    ).all()

                    # 문서 처리 통계
                    processed_docs = db.query(BidDocument).filter(
                        BidDocument.updated_at >= start_time,
                        BidDocument.updated_at <= end_time,
                        BidDocument.processing_status == 'completed'
                    ).count()

                    pending_docs = db.query(BidDocument).filter(
                        BidDocument.download_status == 'pending'
                    ).count()

                    return {
                        "date": today.isoformat(),
                        "collections": {
                            "total_runs": len(collection_logs),
                            "successful_runs": len([log for log in collection_logs if log.status == 'completed']),
                            "total_found": sum(log.total_found or 0 for log in collection_logs),
                            "new_items": sum(log.new_items or 0 for log in collection_logs)
                        },
                        "documents": {
                            "processed_today": processed_docs,
                            "pending": pending_docs
                        }
                    }

            except Exception as e:
                logger.error(f"통계 조회 오류: {e}")
                raise HTTPException(status_code=500, detail=str(e))

    def start(self):
        """데몬 시작"""
        logger.info("Odin-AI 수집기 데몬 시작")

        try:
            # 스케줄러 시작
            self.scheduler = CollectorScheduler()
            self.scheduler.start()

            # 웹 서버 설정
            config = uvicorn.Config(
                app=self.web_app,
                host="0.0.0.0",
                port=8001,
                log_level="info"
            )
            self.web_server = uvicorn.Server(config)

            self.running = True
            logger.info("데몬 시작 완료")

            # 이벤트 루프 실행
            asyncio.run(self._run_forever())

        except Exception as e:
            logger.error(f"데몬 시작 실패: {e}")
            self.stop()
            sys.exit(1)

    async def _run_forever(self):
        """영구 실행"""
        try:
            # 웹 서버 시작
            await self.web_server.serve()
        except Exception as e:
            logger.error(f"웹 서버 실행 오류: {e}")
        finally:
            self.stop()

    def stop(self):
        """데몬 종료"""
        if self.running:
            logger.info("데몬 종료 중...")
            self.running = False

            # 스케줄러 종료
            if self.scheduler:
                self.scheduler.shutdown()

            # 웹 서버 종료
            if self.web_server:
                self.web_server.should_exit = True

            logger.info("데몬 종료 완료")

    def restart(self):
        """데몬 재시작"""
        logger.info("데몬 재시작")
        self.stop()
        asyncio.sleep(2)  # 잠시 대기
        self.start()

    def get_status(self) -> dict:
        """데몬 상태 조회"""
        return {
            "running": self.running,
            "scheduler": self.scheduler.get_job_status() if self.scheduler else None,
            "web_server": "running" if self.web_server else "stopped",
            "timestamp": datetime.utcnow().isoformat()
        }