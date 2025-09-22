#!/usr/bin/env python3
"""
Odin-AI 데이터 수집기 메인 프로그램

사용법:
    python main.py --mode once                    # 일회성 수집
    python main.py --mode schedule                # 스케줄 모드
    python main.py --mode process-documents       # 문서 처리만
    python main.py --mode daemon                  # 데몬 모드
"""

import asyncio
import sys
import signal
from pathlib import Path
from typing import Optional
import click
from loguru import logger

# 프로젝트 루트 경로 추가
sys.path.append(str(Path(__file__).parent.parent))

from shared.config import settings, setup_directories
from shared.database import check_connection, create_tables
from collector.core.scheduler import CollectorScheduler
from collector.services.api_collector import APICollector
from collector.services.document_processor import DocumentProcessor
from collector.core.daemon import CollectorDaemon


class CollectorApp:
    """수집기 메인 애플리케이션"""
    
    def __init__(self):
        self.scheduler: Optional[CollectorScheduler] = None
        self.daemon: Optional[CollectorDaemon] = None
        self.running = False
        
        # 시그널 핸들러 등록
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """시그널 핸들러"""
        logger.info(f"종료 시그널 수신: {signum}")
        self.stop()
    
    def setup(self):
        """애플리케이션 초기 설정"""
        logger.info("Odin-AI 데이터 수집기 시작")
        
        # 디렉토리 설정
        setup_directories()
        logger.info("저장 디렉토리 설정 완료")
        
        # 데이터베이스 연결 확인
        if not check_connection():
            logger.error("데이터베이스 연결 실패")
            sys.exit(1)
        
        # 테이블 생성
        create_tables()
        
        logger.info("초기 설정 완료")
    
    async def run_once(self):
        """일회성 데이터 수집"""
        logger.info("일회성 데이터 수집 시작")
        
        try:
            # API 데이터 수집
            api_collector = APICollector()
            collected_data = await api_collector.collect_latest_bids()
            logger.info(f"수집 완료: {len(collected_data)}건")
            
            # 문서 처리
            doc_processor = DocumentProcessor()
            await doc_processor.process_pending_documents()
            
            logger.info("일회성 수집 완료")
            
        except Exception as e:
            logger.error(f"일회성 수집 실패: {e}")
            raise
    
    def run_scheduled(self):
        """스케줄 모드 실행"""
        logger.info("스케줄 모드 시작")
        
        try:
            self.scheduler = CollectorScheduler()
            self.scheduler.start()
            self.running = True
            
            # 메인 루프 유지
            while self.running:
                asyncio.sleep(1)
                
        except KeyboardInterrupt:
            logger.info("사용자에 의해 중단됨")
        except Exception as e:
            logger.error(f"스케줄러 실행 오류: {e}")
        finally:
            self.stop()
    
    async def process_documents_only(self):
        """문서 처리만 실행"""
        logger.info("문서 처리 전용 모드 시작")
        
        try:
            doc_processor = DocumentProcessor()
            await doc_processor.process_pending_documents()
            logger.info("문서 처리 완료")
            
        except Exception as e:
            logger.error(f"문서 처리 실패: {e}")
            raise
    
    def run_daemon(self):
        """데몬 모드 실행"""
        logger.info("데몬 모드 시작")
        
        try:
            self.daemon = CollectorDaemon()
            self.daemon.start()
            self.running = True
            
            # 메인 루프 유지
            while self.running:
                asyncio.sleep(1)
                
        except KeyboardInterrupt:
            logger.info("사용자에 의해 중단됨")
        except Exception as e:
            logger.error(f"데몬 실행 오류: {e}")
        finally:
            self.stop()
    
    def stop(self):
        """애플리케이션 종료"""
        logger.info("애플리케이션 종료 중...")
        self.running = False
        
        if self.scheduler:
            self.scheduler.shutdown()
            
        if self.daemon:
            self.daemon.stop()
        
        logger.info("종료 완료")


@click.command()
@click.option(
    '--mode', 
    type=click.Choice(['once', 'schedule', 'process-documents', 'daemon']),
    default='once',
    help='실행 모드 선택'
)
@click.option('--debug', is_flag=True, help='디버그 모드 활성화')
def main(mode: str, debug: bool):
    """
Odin-AI 데이터 수집기 메인 엔트리포인트
    
\b
Modes:
    once              - 일회성 데이터 수집
    schedule          - 주기적 스케줄 수집
    process-documents - 문서 처리만 실행
    daemon            - 데몬 모드 (스케줄 + 모니터링)
    """
    
    # 로깅 설정
    log_level = "DEBUG" if debug else settings.log_level
    logger.remove()
    logger.add(
        sys.stdout,
        level=log_level,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
    )
    
    if settings.log_file:
        logger.add(
            settings.log_file,
            level=log_level,
            rotation="1 day",
            retention="30 days",
            compression="gzip"
        )
    
    # 애플리케이션 실행
    app = CollectorApp()
    app.setup()
    
    try:
        if mode == 'once':
            asyncio.run(app.run_once())
        elif mode == 'schedule':
            app.run_scheduled()
        elif mode == 'process-documents':
            asyncio.run(app.process_documents_only())
        elif mode == 'daemon':
            app.run_daemon()
    except Exception as e:
        logger.error(f"애플리케이션 실행 오류: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()