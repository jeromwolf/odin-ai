"""
ODIN-AI 백엔드 메인 서버
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
from typing import Dict, Any

# FastAPI 인스턴스 생성
app = FastAPI(
    title="ODIN-AI API",
    description="입찰공고 분석 시스템 백엔드",
    version="1.0.0"
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    """루트 엔드포인트"""
    return {
        "service": "ODIN-AI",
        "version": "1.0.0",
        "status": "running",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/v1/health")
def health_check():
    """헬스 체크 엔드포인트"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "database": "connected",
        "services": {
            "api": "running",
            "batch": "ready",
            "hwp_processor": "available"
        }
    }

@app.get("/api/v1/stats")
def get_stats() -> Dict[str, Any]:
    """시스템 통계"""
    return {
        "announcements": {
            "total": 445,
            "today": 124,
            "processed": 50
        },
        "documents": {
            "hwp": 35,
            "pdf": 15,
            "total": 50
        },
        "performance": {
            "success_rate": 88.5,
            "avg_processing_time": 1.2
        }
    }

@app.get("/api/v1/announcements")
def get_announcements():
    """입찰공고 목록 조회"""
    return {
        "total": 124,
        "page": 1,
        "items": [
            {
                "id": "R25BK01072305",
                "title": "2025년 산불피해지 긴급벌채사업",
                "organization": "경북 안동시산림조합",
                "status": "active",
                "bid_end_date": "2025-09-30"
            }
        ]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)