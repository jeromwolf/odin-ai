"""
Odin-AI FastAPI 애플리케이션
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn
from pathlib import Path

from backend.api import bid_routes, document_routes, system_routes, search_routes, email_routes
from backend.core.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    """애플리케이션 생명주기 관리"""
    # 시작 시
    print("🚀 Odin-AI 서버 시작")

    # 필수 디렉토리 생성
    dirs = [
        "storage/downloads/hwp",
        "storage/downloads/pdf",
        "storage/downloads/doc",
        "storage/downloads/unknown",
        "storage/processed/hwp",
        "storage/processed/pdf",
        "storage/processed/doc",
        "storage/processed/unknown",
        "logs"
    ]

    for dir_path in dirs:
        Path(dir_path).mkdir(parents=True, exist_ok=True)

    yield

    # 종료 시
    print("👋 Odin-AI 서버 종료")


# FastAPI 앱 생성
app = FastAPI(
    title="Odin-AI API",
    description="나라장터 입찰공고 분석 시스템",
    version="1.0.0",
    lifespan=lifespan
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 프로덕션에서는 구체적인 도메인 지정
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터 등록
app.include_router(bid_routes.router)
app.include_router(document_routes.router)
app.include_router(system_routes.router)
app.include_router(search_routes.router)
app.include_router(email_routes.router)


@app.get("/")
async def root():
    """루트 엔드포인트"""
    return {
        "name": "Odin-AI",
        "version": "1.0.0",
        "description": "나라장터 입찰공고 AI 분석 시스템",
        "endpoints": {
            "docs": "/docs",
            "redoc": "/redoc",
            "bids": "/api/bids",
            "documents": "/api/documents"
        }
    }


@app.get("/health")
async def health_check():
    """헬스체크 엔드포인트"""
    return {
        "status": "healthy",
        "service": "odin-ai",
        "version": "1.0.0"
    }


if __name__ == "__main__":
    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )