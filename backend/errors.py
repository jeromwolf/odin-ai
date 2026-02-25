"""
구조화된 API 에러 응답 시스템

모든 API 에러 응답을 표준화된 형식으로 반환:
{
    "success": false,
    "error": {
        "code": "AUTH_TOKEN_EXPIRED",
        "message": "인증 토큰이 만료되었습니다",
        "detail": "optional extra info"
    }
}
"""

from fastapi import HTTPException
from fastapi.responses import JSONResponse
from typing import Optional


# ============================================================
# 에러 코드 정의
# ============================================================

class ErrorCode:
    """API 에러 코드 상수"""

    # 인증 (AUTH_*)
    AUTH_REQUIRED = "AUTH_REQUIRED"
    AUTH_TOKEN_EXPIRED = "AUTH_TOKEN_EXPIRED"
    AUTH_TOKEN_INVALID = "AUTH_TOKEN_INVALID"
    AUTH_FORBIDDEN = "AUTH_FORBIDDEN"
    AUTH_EMAIL_NOT_VERIFIED = "AUTH_EMAIL_NOT_VERIFIED"
    AUTH_INACTIVE_USER = "AUTH_INACTIVE_USER"
    AUTH_LOGIN_FAILED = "AUTH_LOGIN_FAILED"
    AUTH_DUPLICATE_EMAIL = "AUTH_DUPLICATE_EMAIL"

    # 검색 (SEARCH_*)
    SEARCH_QUERY_TOO_LONG = "SEARCH_QUERY_TOO_LONG"
    SEARCH_FAILED = "SEARCH_FAILED"

    # 리소스 (RESOURCE_*)
    RESOURCE_NOT_FOUND = "RESOURCE_NOT_FOUND"
    RESOURCE_ALREADY_EXISTS = "RESOURCE_ALREADY_EXISTS"

    # 입력값 (VALIDATION_*)
    VALIDATION_FAILED = "VALIDATION_FAILED"

    # 서비스 (SERVICE_*)
    SERVICE_UNAVAILABLE = "SERVICE_UNAVAILABLE"
    SERVICE_RAG_UNAVAILABLE = "SERVICE_RAG_UNAVAILABLE"
    SERVICE_GRAPH_UNAVAILABLE = "SERVICE_GRAPH_UNAVAILABLE"
    SERVICE_LLM_UNAVAILABLE = "SERVICE_LLM_UNAVAILABLE"

    # 요금제 (SUBSCRIPTION_*)
    SUBSCRIPTION_LIMIT_REACHED = "SUBSCRIPTION_LIMIT_REACHED"
    SUBSCRIPTION_UPGRADE_REQUIRED = "SUBSCRIPTION_UPGRADE_REQUIRED"

    # 서버 (SERVER_*)
    SERVER_ERROR = "SERVER_ERROR"
    SERVER_RATE_LIMIT = "SERVER_RATE_LIMIT"


# ============================================================
# 에러 응답 빌더
# ============================================================

def error_response(
    status_code: int,
    code: str,
    message: str,
    detail: Optional[str] = None,
) -> JSONResponse:
    """구조화된 에러 JSONResponse 생성"""
    body = {
        "success": False,
        "error": {
            "code": code,
            "message": message,
        }
    }
    if detail:
        body["error"]["detail"] = detail
    return JSONResponse(status_code=status_code, content=body)


class ApiError(HTTPException):
    """구조화된 API 에러 예외

    사용법:
        raise ApiError(404, ErrorCode.RESOURCE_NOT_FOUND, "입찰 공고를 찾을 수 없습니다")
    """
    def __init__(
        self,
        status_code: int,
        code: str,
        message: str,
        detail: Optional[str] = None,
    ):
        self.error_code = code
        self.error_message = message
        self.error_detail = detail
        # HTTPException.detail에 구조화된 dict 전달
        super().__init__(
            status_code=status_code,
            detail={
                "success": False,
                "error": {
                    "code": code,
                    "message": message,
                    **({"detail": detail} if detail else {}),
                }
            }
        )
