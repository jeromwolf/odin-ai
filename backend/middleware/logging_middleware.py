"""
구조화된 로깅 및 요청 모니터링 미들웨어
"""
import time
import logging
import json
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger("odin.access")


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """HTTP 요청/응답 로깅 미들웨어"""

    SKIP_PATHS = {"/health", "/docs", "/openapi.json", "/redoc", "/favicon.ico"}

    async def dispatch(self, request: Request, call_next) -> Response:
        # 헬스체크 등 불필요한 경로 스킵
        if request.url.path in self.SKIP_PATHS:
            return await call_next(request)

        start_time = time.time()

        # 요청 처리
        try:
            response = await call_next(request)
        except Exception as exc:
            duration_ms = round((time.time() - start_time) * 1000, 2)
            logger.error(json.dumps({
                "type": "request",
                "method": request.method,
                "path": request.url.path,
                "status": 500,
                "duration_ms": duration_ms,
                "error": str(exc)[:200],
                "client_ip": request.client.host if request.client else None,
            }, ensure_ascii=False))
            raise

        duration_ms = round((time.time() - start_time) * 1000, 2)

        # 로그 레벨 결정
        log_level = logging.INFO
        if response.status_code >= 500:
            log_level = logging.ERROR
        elif response.status_code >= 400:
            log_level = logging.WARNING

        log_data = {
            "type": "request",
            "method": request.method,
            "path": request.url.path,
            "status": response.status_code,
            "duration_ms": duration_ms,
            "client_ip": request.client.host if request.client else None,
        }

        # 느린 요청 경고 (3초 이상)
        if duration_ms > 3000:
            log_data["slow_request"] = True
            log_level = logging.WARNING

        logger.log(log_level, json.dumps(log_data, ensure_ascii=False))

        # 응답 헤더에 처리 시간 추가
        response.headers["X-Process-Time"] = str(duration_ms)
        return response
