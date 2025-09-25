#!/usr/bin/env python3
"""
ODIN-AI 알림 서비스
배치 완료 이벤트를 받아 사용자 알림 규칙에 따라 알림 발송
"""

import os
import sys
import json
import time
import signal
from datetime import datetime
from pathlib import Path
from loguru import logger
from dotenv import load_dotenv

# 프로젝트 루트 경로 추가
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# 환경변수 로드
load_dotenv()

# 로거 설정
log_dir = Path("logs/alert")
log_dir.mkdir(parents=True, exist_ok=True)
log_file = log_dir / f"alert_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
logger.add(str(log_file), rotation="10 MB", retention="30 days", level="INFO")


class AlertService:
    """알림 서비스 메인 클래스"""

    def __init__(self):
        """초기화"""
        self.db_url = os.getenv('DATABASE_URL', 'postgresql://blockmeta@localhost:5432/odin_db')
        self.is_running = True
        self.event_bus = None
        self.matcher = None
        self.sender = None

        # 통계
        self.stats = {
            'events_received': 0,
            'matches_found': 0,
            'alerts_sent': 0,
            'errors': 0
        }

    def start(self):
        """서비스 시작"""
        logger.info("="*60)
        logger.info("🚀 ODIN-AI 알림 서비스 시작")
        logger.info(f"📅 시작 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info("="*60)

        try:
            # 컴포넌트 초기화
            self._initialize_components()

            # 이벤트 리스너 시작
            self._start_event_listener()

            # 메인 루프
            self._main_loop()

        except KeyboardInterrupt:
            logger.info("\n⏹️ 사용자에 의한 서비스 중지")
        except Exception as e:
            logger.error(f"❌ 서비스 오류: {e}")
            import traceback
            logger.error(traceback.format_exc())
        finally:
            self.stop()

    def _initialize_components(self):
        """컴포넌트 초기화"""
        logger.info("🔧 컴포넌트 초기화 중...")

        # 이벤트 버스 초기화
        from services.shared.events import EventBus, EventChannels
        self.event_bus = EventBus()

        # 매칭 엔진 초기화
        from services.alert.matcher import AlertMatcher
        self.matcher = AlertMatcher(self.db_url)

        # 발송 시스템 초기화
        from services.alert.sender import AlertSender
        self.sender = AlertSender(self.db_url)

        logger.info("✅ 컴포넌트 초기화 완료")

    def _start_event_listener(self):
        """이벤트 리스너 시작"""
        logger.info("📡 이벤트 리스너 설정 중...")

        # 배치 완료 이벤트 구독
        from services.shared.events import EventChannels
        self.event_bus.subscribe(
            EventChannels.BATCH,
            self.on_batch_completed
        )

        # 리스너 시작
        self.event_bus.start_listening()
        logger.info("✅ 이벤트 리스너 시작됨")

    def on_batch_completed(self, event_data: dict):
        """배치 완료 이벤트 처리

        Args:
            event_data: 이벤트 데이터
        """
        logger.info("="*40)
        logger.info("📨 배치 완료 이벤트 수신")
        logger.info(f"  - 타임스탬프: {event_data.get('timestamp')}")
        logger.info(f"  - 신규 공고: {event_data['stats'].get('new_bids', 0)}건")
        logger.info("="*40)

        self.stats['events_received'] += 1

        try:
            # 새로운 공고가 있는 경우에만 처리
            new_bid_ids = event_data.get('new_bid_ids', [])
            if not new_bid_ids:
                logger.info("ℹ️ 신규 공고 없음 - 처리 스킵")
                return

            # 날짜 설정 (환경변수 또는 현재 날짜)
            alert_date_str = os.getenv('ALERT_DATE')
            if alert_date_str:
                batch_date = datetime.strptime(alert_date_str, '%Y-%m-%d')
            else:
                batch_date = datetime.now()

            # 1. 알림 규칙과 매칭
            logger.info(f"🔍 알림 규칙 매칭 시작 (날짜: {batch_date.strftime('%Y-%m-%d')})...")
            matches = self.matcher.match_bids_with_rules(new_bid_ids, batch_date)
            self.stats['matches_found'] += len(matches)

            if not matches:
                logger.info("ℹ️ 매칭된 알림 없음")
                return

            logger.info(f"✅ {len(matches)}개 매칭 발견")

            # 2. 알림 큐 생성
            logger.info("📝 알림 큐 생성 중...")
            queue_ids = self.sender.queue_alerts(matches)

            # 3. 알림 발송
            logger.info("📤 알림 발송 시작...")
            sent_count = self.sender.process_queue()
            self.stats['alerts_sent'] += sent_count

            logger.info(f"✅ {sent_count}개 알림 발송 완료")

        except Exception as e:
            logger.error(f"❌ 이벤트 처리 실패: {e}")
            self.stats['errors'] += 1

    def _main_loop(self):
        """메인 루프"""
        logger.info("🔄 메인 루프 시작")

        while self.is_running:
            try:
                # 주기적 작업
                self._process_scheduled_tasks()

                # 통계 출력 (10분마다)
                if int(time.time()) % 600 == 0:
                    self._print_stats()

                # 대기
                time.sleep(10)

            except Exception as e:
                logger.error(f"메인 루프 오류: {e}")
                self.stats['errors'] += 1

    def _process_scheduled_tasks(self):
        """주기적 작업 처리"""
        # 일일 다이제스트 (매일 오전 9시)
        now = datetime.now()
        if now.hour == 9 and now.minute == 0:
            self._send_daily_digest()

        # 주간 리포트 (매주 월요일 오전 10시)
        if now.weekday() == 0 and now.hour == 10 and now.minute == 0:
            self._send_weekly_report()

    def _send_daily_digest(self):
        """일일 다이제스트 발송"""
        logger.info("📅 일일 다이제스트 발송 시작")
        try:
            sent = self.sender.send_daily_digest()
            logger.info(f"✅ 일일 다이제스트 {sent}개 발송")
        except Exception as e:
            logger.error(f"일일 다이제스트 발송 실패: {e}")

    def _send_weekly_report(self):
        """주간 리포트 발송"""
        logger.info("📊 주간 리포트 발송 시작")
        try:
            sent = self.sender.send_weekly_report()
            logger.info(f"✅ 주간 리포트 {sent}개 발송")
        except Exception as e:
            logger.error(f"주간 리포트 발송 실패: {e}")

    def _print_stats(self):
        """통계 출력"""
        logger.info("="*40)
        logger.info("📊 알림 서비스 통계")
        logger.info(f"  - 수신 이벤트: {self.stats['events_received']}개")
        logger.info(f"  - 매칭 발견: {self.stats['matches_found']}개")
        logger.info(f"  - 발송 알림: {self.stats['alerts_sent']}개")
        logger.info(f"  - 오류 발생: {self.stats['errors']}개")
        logger.info("="*40)

    def stop(self):
        """서비스 중지"""
        logger.info("🛑 알림 서비스 중지 중...")
        self.is_running = False

        if self.event_bus:
            self.event_bus.stop_listening()

        logger.info("✅ 알림 서비스 중지 완료")

        # 최종 통계 출력
        self._print_stats()


def handle_signal(signum, frame):
    """시그널 핸들러"""
    logger.info(f"시그널 {signum} 수신")
    sys.exit(0)


def main():
    """메인 함수

    사용법:
        python services/alert/main.py                    # 오늘 날짜 기준
        python services/alert/main.py --date 2025-09-25  # 특정 날짜
        python services/alert/main.py --daemon           # 데몬 모드 (계속 실행)
    """
    import argparse

    parser = argparse.ArgumentParser(description='ODIN-AI 알림 서비스')
    parser.add_argument('--date', help='처리할 날짜 (YYYY-MM-DD)', default=None)
    parser.add_argument('--daemon', action='store_true', help='데몬 모드로 실행')
    parser.add_argument('--dry-run', action='store_true', help='실제 발송하지 않고 테스트')

    args = parser.parse_args()

    # 날짜 설정
    if args.date:
        try:
            batch_date = datetime.strptime(args.date, '%Y-%m-%d')
            os.environ['ALERT_DATE'] = args.date
            logger.info(f"📅 지정된 날짜: {args.date}")
        except ValueError:
            logger.error(f"❌ 잘못된 날짜 형식: {args.date} (YYYY-MM-DD 필요)")
            sys.exit(1)

    # Dry run 모드
    if args.dry_run:
        os.environ['DRY_RUN'] = 'true'
        logger.info("🧪 Dry Run 모드: 실제 발송하지 않음")

    # Daemon 모드
    if args.daemon:
        os.environ['DAEMON_MODE'] = 'true'
        logger.info("👹 데몬 모드로 실행")

    # 시그널 핸들러 설정
    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)

    try:
        # 서비스 시작
        service = AlertService()
        service.start()
    except Exception as e:
        logger.error(f"❌ 서비스 시작 실패: {e}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)


if __name__ == "__main__":
    main()