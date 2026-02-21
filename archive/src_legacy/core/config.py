"""
시스템 설정 파일
"""

from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    """애플리케이션 설정"""

    # 데이터베이스
    database_url: str = "postgresql://blockmeta@localhost:5432/odin_db"
    db_echo: bool = False

    # 파일 처리
    storage_path: str = "./storage"
    max_file_size: int = 100 * 1024 * 1024  # 100MB

    # 배치 처리 설정
    batch_size: int = 100  # 한 번에 처리할 문서 수
    max_concurrent: int = 5  # 동시 처리 최대 수
    process_timeout: int = 300  # 문서 처리 타임아웃 (초)

    # API 설정
    api_timeout: int = 30  # API 요청 타임아웃 (초)
    api_retry_count: int = 3  # API 재시도 횟수
    api_rate_limit: float = 0.5  # API 요청 간격 (초)

    # 크롤링 설정
    crawler_timeout: int = 60  # 크롤러 타임아웃 (초)
    crawler_delay: float = 2.0  # 크롤링 요청 간 지연 (초)
    user_agent: str = "Odin-AI/1.0 (contact@odin-ai.kr)"

    # 문서 처리 설정
    hwp_timeout: int = 30  # HWP 처리 타임아웃 (초)
    pdf_timeout: int = 30  # PDF 처리 타임아웃 (초)
    excel_timeout: int = 30  # Excel 처리 타임아웃 (초)

    # 로깅 설정
    log_level: str = "INFO"
    log_file: Optional[str] = "logs/odin.log"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"  # 추가 필드 무시

# 싱글톤 인스턴스
settings = Settings()

# 배치 처리 설정 상수
BATCH_CONFIG = {
    "small": {
        "batch_size": 10,
        "max_concurrent": 2,
        "timeout": 60
    },
    "medium": {
        "batch_size": 50,
        "max_concurrent": 5,
        "timeout": 180
    },
    "large": {
        "batch_size": 100,
        "max_concurrent": 10,
        "timeout": 300
    },
    "xlarge": {
        "batch_size": 500,
        "max_concurrent": 20,
        "timeout": 600
    }
}

def get_batch_config(size: str = "medium") -> dict:
    """배치 크기에 따른 설정 반환"""
    return BATCH_CONFIG.get(size, BATCH_CONFIG["medium"])