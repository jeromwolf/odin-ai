"""
Redis 캐싱 시스템
검색 결과와 대시보드 데이터를 캐싱하여 성능 향상
"""

import redis
import json
import hashlib
import logging
from typing import Optional, Any, Dict
from datetime import timedelta
import os

logger = logging.getLogger(__name__)

class RedisCache:
    def __init__(self):
        """Redis 연결 초기화"""
        self.client = None
        self.enabled = False

        try:
            # Redis 연결 시도
            self.client = redis.Redis(
                host=os.getenv('REDIS_HOST', 'localhost'),
                port=int(os.getenv('REDIS_PORT', 6379)),
                db=int(os.getenv('REDIS_DB', 0)),
                decode_responses=True,
                socket_connect_timeout=2,
                socket_timeout=2
            )
            # 연결 테스트
            self.client.ping()
            self.enabled = True
            logger.info("Redis cache connection successful")
        except (redis.ConnectionError, redis.TimeoutError) as e:
            logger.warning(f"Redis connection failed (caching disabled): {e}")
            self.enabled = False
        except Exception as e:
            logger.warning(f"Redis initialization failed: {e}")
            self.enabled = False

    def _make_key(self, prefix: str, params: Dict[str, Any]) -> str:
        """캐시 키 생성"""
        # 파라미터를 정렬하여 일관된 키 생성
        sorted_params = sorted(params.items())
        param_str = json.dumps(sorted_params, ensure_ascii=False)

        # MD5 해시로 키 길이 제한
        hash_digest = hashlib.md5(param_str.encode()).hexdigest()
        return f"{prefix}:{hash_digest}"

    def get(self, prefix: str, params: Dict[str, Any]) -> Optional[Dict]:
        """캐시에서 데이터 조회"""
        if not self.enabled:
            return None

        try:
            key = self._make_key(prefix, params)
            data = self.client.get(key)

            if data:
                logger.debug(f"Cache hit: {prefix}")
                return json.loads(data)
            else:
                logger.debug(f"Cache miss: {prefix}")
                return None
        except Exception as e:
            logger.error(f"Cache retrieval error: {e}")
            return None

    def set(self, prefix: str, params: Dict[str, Any], data: Dict, ttl_seconds: int = 300):
        """캐시에 데이터 저장 (기본 TTL: 5분)"""
        if not self.enabled:
            return False

        try:
            key = self._make_key(prefix, params)
            json_data = json.dumps(data, ensure_ascii=False)

            # TTL과 함께 저장
            self.client.setex(key, ttl_seconds, json_data)
            logger.debug(f"Cache saved: {prefix} (TTL: {ttl_seconds}s)")
            return True
        except Exception as e:
            logger.error(f"Cache save error: {e}")
            return False

    def delete(self, prefix: str, params: Dict[str, Any]) -> bool:
        """특정 캐시 삭제"""
        if not self.enabled:
            return False

        try:
            key = self._make_key(prefix, params)
            result = self.client.delete(key)
            if result:
                logger.debug(f"Cache deleted: {prefix}")
            return bool(result)
        except Exception as e:
            logger.error(f"Cache deletion error: {e}")
            return False

    def flush_pattern(self, pattern: str) -> int:
        """패턴에 맞는 모든 캐시 삭제"""
        if not self.enabled:
            return 0

        try:
            keys = self.client.keys(f"{pattern}:*")
            if keys:
                deleted = self.client.delete(*keys)
                logger.debug(f"{deleted} cache entries deleted (pattern: {pattern})")
                return deleted
            return 0
        except Exception as e:
            logger.error(f"Pattern cache deletion error: {e}")
            return 0

    def get_stats(self) -> Dict[str, Any]:
        """캐시 통계 조회"""
        if not self.enabled:
            return {"enabled": False}

        try:
            info = self.client.info('stats')
            memory = self.client.info('memory')

            return {
                "enabled": True,
                "total_connections": info.get('total_connections_received', 0),
                "total_commands": info.get('total_commands_processed', 0),
                "keyspace_hits": info.get('keyspace_hits', 0),
                "keyspace_misses": info.get('keyspace_misses', 0),
                "hit_rate": self._calculate_hit_rate(
                    info.get('keyspace_hits', 0),
                    info.get('keyspace_misses', 0)
                ),
                "used_memory_human": memory.get('used_memory_human', 'N/A'),
                "db_size": self.client.dbsize()
            }
        except Exception as e:
            logger.error(f"Cache statistics retrieval error: {e}")
            return {"enabled": False, "error": "cache error"}

    def _calculate_hit_rate(self, hits: int, misses: int) -> float:
        """캐시 히트율 계산"""
        total = hits + misses
        if total == 0:
            return 0.0
        return round((hits / total) * 100, 2)

# 싱글톤 인스턴스
cache = RedisCache()

# 캐시 TTL 설정 (초 단위)
CACHE_TTL = {
    "search": 300,           # 검색: 5분
    "dashboard": 60,         # 대시보드: 1분
    "statistics": 300,       # 통계: 5분
    "recommendations": 180,  # 추천: 3분
    "facets": 600,          # 패싯: 10분
}

def get_cached_or_fetch(
    cache_key: str,
    params: Dict[str, Any],
    fetch_func,
    ttl: Optional[int] = None
) -> Dict:
    """캐시 조회 또는 데이터 fetch 헬퍼 함수"""

    # 캐시 조회
    cached_data = cache.get(cache_key, params)
    if cached_data is not None:
        return cached_data

    # 캐시 미스 시 데이터 fetch
    data = fetch_func()

    # 결과 캐싱
    if data is not None:
        ttl_seconds = ttl or CACHE_TTL.get(cache_key, 300)
        cache.set(cache_key, params, data, ttl_seconds)

    return data