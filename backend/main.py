"""
ODIN-AI Backend API
간단한 검색 API 백엔드
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi.errors import RateLimitExceeded
from middleware.rate_limit import limiter, _rate_limit_exceeded_handler
from datetime import datetime, timezone
import logging
import os
from database import close_pool, get_db_connection

logger = logging.getLogger(__name__)

# Redis 캐싱 시스템 임포트
try:
    from cache import cache, get_cached_or_fetch, CACHE_TTL
    CACHE_ENABLED = cache.enabled
except ImportError:
    CACHE_ENABLED = False
    logger.warning("캐싱 시스템 비활성화 (cache.py 없음)")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    yield
    # Shutdown
    close_pool()

app = FastAPI(title="ODIN-AI Search API", version="1.0.0", lifespan=lifespan)

# Rate Limiting 설정
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS 설정 - 환경변수에서 읽거나 개발 기본값 사용
_default_origins = "http://localhost:5173,http://localhost:9000,http://localhost:3000,http://localhost:8000,http://localhost:9029"
CORS_ORIGINS = [
    origin.strip()
    for origin in os.getenv("CORS_ORIGINS", _default_origins).split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 검색 라우터 추가
try:
    from api.search import router as search_router
    app.include_router(search_router)
    logger.info("검색 API 라우터 등록됨")
except ImportError as e:
    logger.warning(f"검색 API 라우터 로드 실패: {e}")

# 인증 라우터 추가
try:
    from api.auth import router as auth_router
    app.include_router(auth_router)
    logger.info("인증 API 라우터 등록됨")
except ImportError as e:
    logger.warning(f"인증 API 라우터 로드 실패: {e}")

# 프로필 라우터 추가
try:
    from api.profile import router as profile_router
    app.include_router(profile_router)
    logger.info("프로필 API 라우터 등록됨")
except ImportError as e:
    logger.warning(f"프로필 API 라우터 로드 실패: {e}")

# 북마크 라우터 임포트 및 추가
try:
    from api.bookmarks import router as bookmarks_router
    app.include_router(bookmarks_router)
    logger.info("북마크 API 라우터 등록됨")
except ImportError as e:
    logger.warning(f"북마크 API 라우터 로드 실패: {e}")

# 대시보드 라우터 추가
try:
    from api.dashboard import router as dashboard_router
    app.include_router(dashboard_router)
    logger.info("대시보드 API 라우터 등록됨")
except ImportError as e:
    logger.warning(f"대시보드 API 라우터 로드 실패: {e}")

# 구독 라우터 추가
try:
    from api.subscription import router as subscription_router
    app.include_router(subscription_router)
    logger.info("구독 API 라우터 등록됨")
except ImportError as e:
    logger.warning(f"구독 API 라우터 로드 실패: {e}")

# 결제 라우터 추가
try:
    from api.payments import router as payments_router
    app.include_router(payments_router)
    logger.info("결제 API 라우터 등록됨")
except ImportError as e:
    logger.warning(f"결제 API 라우터 로드 실패: {e}")

# 알림 라우터 추가
try:
    from api.notifications import router as notifications_router
    app.include_router(notifications_router)
    logger.info("알림 API 라우터 등록됨")
except ImportError as e:
    logger.warning(f"알림 API 라우터 로드 실패: {e}")

# AI 추천 라우터 추가
try:
    from api.recommendations import router as recommendations_router
    app.include_router(recommendations_router, prefix="/api/recommendations", tags=["recommendations"])
    logger.info("AI 추천 API 라우터 등록됨")
except ImportError as e:
    logger.warning(f"AI 추천 API 라우터 로드 실패: {e}")

# ============================================
# 관리자 웹 API 라우터 추가
# ============================================

# 관리자 인증 라우터 추가
try:
    from api.admin_auth import router as admin_auth_router
    app.include_router(admin_auth_router)
    logger.info("관리자 인증 API 라우터 등록됨")
except ImportError as e:
    logger.warning(f"관리자 인증 API 라우터 로드 실패: {e}")

# 관리자 배치 모니터링 라우터 추가
try:
    from api.admin_batch import router as admin_batch_router
    app.include_router(admin_batch_router)
    logger.info("관리자 배치 모니터링 API 라우터 등록됨")
except ImportError as e:
    logger.warning(f"관리자 배치 모니터링 API 라우터 로드 실패: {e}")

# 관리자 시스템 모니터링 라우터 추가
try:
    from api.admin_system import router as admin_system_router
    app.include_router(admin_system_router)
    logger.info("관리자 시스템 모니터링 API 라우터 등록됨")
except ImportError as e:
    logger.warning(f"관리자 시스템 모니터링 API 라우터 로드 실패: {e}")

# 관리자 사용자 관리 라우터 추가
try:
    from api.admin_users import router as admin_users_router
    app.include_router(admin_users_router)
    logger.info("관리자 사용자 관리 API 라우터 등록됨")
except ImportError as e:
    logger.warning(f"관리자 사용자 관리 API 라우터 로드 실패: {e}")

# 관리자 로그 조회 라우터 추가
try:
    from api.admin_logs import router as admin_logs_router
    app.include_router(admin_logs_router)
    logger.info("관리자 로그 조회 API 라우터 등록됨")
except ImportError as e:
    logger.warning(f"관리자 로그 조회 API 라우터 로드 실패: {e}")

# 관리자 통계 분석 라우터 추가
try:
    from api.admin_statistics import router as admin_statistics_router
    app.include_router(admin_statistics_router)
    logger.info("관리자 통계 분석 API 라우터 등록됨")
except ImportError as e:
    logger.warning(f"관리자 통계 분석 API 라우터 로드 실패: {e}")

# 관리자 알림 모니터링 라우터 추가
try:
    from api.admin_notifications import router as admin_notifications_router
    app.include_router(admin_notifications_router)
    logger.info("관리자 알림 모니터링 API 라우터 등록됨")
except ImportError as e:
    logger.warning(f"관리자 알림 모니터링 API 라우터 로드 실패: {e}")

# RAG 검색 라우터 추가
try:
    from api.rag_search import router as rag_search_router
    app.include_router(rag_search_router)
    logger.info("RAG 검색 API 라우터 등록됨")
except ImportError as e:
    logger.warning(f"RAG 검색 API 라우터 로드 실패: {e}")


@app.get("/")
async def root():
    return {"message": "ODIN-AI Search API", "version": "1.0.0"}


@app.get("/health")
async def health_check():
    db_status = "disconnected"
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            cursor.close()
            db_status = "connected"
    except Exception:
        pass

    redis_status = "disconnected"
    if CACHE_ENABLED:
        try:
            cache.client.ping()
            redis_status = "connected"
        except Exception:
            pass

    overall = "healthy" if db_status == "connected" else "unhealthy"

    return {
        "status": overall,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version": "1.0.0",
        "services": {
            "database": db_status,
            "redis": redis_status
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
