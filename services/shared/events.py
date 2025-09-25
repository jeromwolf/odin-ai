"""
이벤트 버스 시스템
Redis Pub/Sub을 활용한 이벤트 기반 통신
"""

import json
import redis
import threading
from typing import Dict, Any, Callable, Optional
from datetime import datetime
import logging
import os

logger = logging.getLogger(__name__)


class EventBus:
    """Redis 기반 이벤트 버스"""

    def __init__(self, redis_host: str = None, redis_port: int = None):
        """초기화

        Args:
            redis_host: Redis 호스트 (기본: localhost)
            redis_port: Redis 포트 (기본: 6379)
        """
        self.redis_host = redis_host or os.getenv('REDIS_HOST', 'localhost')
        self.redis_port = redis_port or int(os.getenv('REDIS_PORT', 6379))

        # Redis 클라이언트
        self.redis_client = redis.Redis(
            host=self.redis_host,
            port=self.redis_port,
            decode_responses=True
        )

        # Pub/Sub 인스턴스
        self.pubsub = None
        self.listener_thread = None
        self.handlers = {}
        self.is_running = False

    def publish(self, channel: str, event_data: Dict[str, Any]) -> bool:
        """이벤트 발행

        Args:
            channel: 채널명
            event_data: 이벤트 데이터

        Returns:
            bool: 성공 여부
        """
        try:
            # 타임스탬프 추가
            if 'timestamp' not in event_data:
                event_data['timestamp'] = datetime.now().isoformat()

            # JSON으로 직렬화
            message = json.dumps(event_data, ensure_ascii=False)

            # 발행
            self.redis_client.publish(channel, message)
            logger.info(f"✅ 이벤트 발행: {channel}")

            # 백업용 큐에도 저장
            self.redis_client.lpush(f"queue:{channel}", message)
            self.redis_client.expire(f"queue:{channel}", 86400)  # 24시간

            return True

        except Exception as e:
            logger.error(f"❌ 이벤트 발행 실패: {e}")
            return False

    def subscribe(self, channel: str, handler: Callable) -> None:
        """채널 구독

        Args:
            channel: 구독할 채널
            handler: 이벤트 핸들러 함수
        """
        if not self.pubsub:
            self.pubsub = self.redis_client.pubsub()

        # 채널 구독
        self.pubsub.subscribe(channel)
        self.handlers[channel] = handler
        logger.info(f"📡 채널 구독: {channel}")

    def start_listening(self) -> None:
        """리스너 시작 (별도 스레드)"""
        if self.is_running:
            logger.warning("리스너가 이미 실행 중입니다")
            return

        self.is_running = True
        self.listener_thread = threading.Thread(target=self._listen)
        self.listener_thread.daemon = True
        self.listener_thread.start()
        logger.info("🎧 이벤트 리스너 시작")

    def _listen(self) -> None:
        """이벤트 수신 루프"""
        try:
            for message in self.pubsub.listen():
                if not self.is_running:
                    break

                # 메시지 타입 확인
                if message['type'] != 'message':
                    continue

                channel = message['channel']
                data = message['data']

                # 핸들러 실행
                if channel in self.handlers:
                    try:
                        event_data = json.loads(data)
                        logger.info(f"📨 이벤트 수신: {channel}")
                        self.handlers[channel](event_data)
                    except Exception as e:
                        logger.error(f"이벤트 처리 실패: {e}")

        except Exception as e:
            logger.error(f"리스너 오류: {e}")
        finally:
            self.is_running = False

    def stop_listening(self) -> None:
        """리스너 중지"""
        self.is_running = False
        if self.pubsub:
            self.pubsub.close()
        logger.info("🛑 이벤트 리스너 중지")

    def get_queue_size(self, channel: str) -> int:
        """큐 크기 확인

        Args:
            channel: 채널명

        Returns:
            int: 큐에 있는 메시지 수
        """
        return self.redis_client.llen(f"queue:{channel}")

    def get_pending_events(self, channel: str, count: int = 10) -> list:
        """대기 중인 이벤트 조회

        Args:
            channel: 채널명
            count: 조회할 개수

        Returns:
            list: 이벤트 목록
        """
        messages = self.redis_client.lrange(f"queue:{channel}", 0, count - 1)
        return [json.loads(msg) for msg in messages]


class EventTypes:
    """이벤트 타입 상수"""
    BATCH_COMPLETED = "BATCH_COMPLETED"
    BATCH_FAILED = "BATCH_FAILED"
    ALERT_TRIGGERED = "ALERT_TRIGGERED"
    ALERT_SENT = "ALERT_SENT"
    DOCUMENT_PROCESSED = "DOCUMENT_PROCESSED"
    USER_ACTION = "USER_ACTION"


class EventChannels:
    """이벤트 채널 상수"""
    BATCH = "batch:completed"
    ALERT = "alert:trigger"
    NOTIFICATION = "notification:send"
    SYSTEM = "system:status"