"""
공통 설정 모듈
"""

import os
from typing import Optional
from pydantic_settings import BaseSettings
from pathlib import Path


class Settings(BaseSettings):
    """전역 설정 클래스"""
    
    # 데이터베이스 설정
    database_url: str = os.getenv("DATABASE_URL", "postgresql://blockmeta@localhost:5432/odin_db")
    
    # API 설정
    public_data_api_key: str = "6h2l2VPWSfA2vG3xSFr7gf6iwaZT2dmzcoCOzklLnOIJY6sw17lrwHNQ3WxPdKMDIN%2FmMlv2vBTWTIzBDPKVdw%3D%3D"
    public_data_base_url: str = "http://apis.data.go.kr/1230000/ad/BidPublicInfoService"
    
    # 파일 저장 설정
    data_storage_path: str = os.getenv("DATA_STORAGE_PATH", "./storage")
    storage_path: Path = Path("./storage")
    hwp_storage_path: Path = Path("./storage/hwp")
    pdf_storage_path: Path = Path("./storage/pdf")
    md_storage_path: Path = Path("./storage/markdown")
    
    # 수집 설정
    collection_interval_minutes: int = 30
    collection_batch_size: int = 100
    max_retry_attempts: int = 3
    
    # 처리 설정
    processing_workers: int = 4
    processing_timeout_seconds: int = 300
    
    # 로깅 설정
    log_level: str = "INFO"
    log_file: Optional[str] = None
    
    # Redis 설정 (선택적)
    redis_url: Optional[str] = "redis://localhost:6379/0"
    
    # 이메일 설정
    smtp_server: Optional[str] = None
    smtp_port: Optional[int] = 587
    smtp_username: Optional[str] = None
    smtp_password: Optional[str] = None
    
    # 웹 설정
    web_base_url: str = "http://localhost:8000"
    web_secret_key: str = "your-secret-key-here"
    
    # 디버그 모드
    debug: bool = False

    # Selenium 설정
    selenium_headless: bool = True
    selenium_timeout: int = 30
    selenium_download_path: Path = Path("./storage/downloads/selenium")
    chrome_driver_path: Optional[str] = None

    # 환경 변수에서 추가로 올 수 있는 필드들
    secret_key: Optional[str] = None
    openai_api_key: Optional[str] = None
    environment: Optional[str] = None

    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "allow"  # 추가 필드 허용


# 전역 설정 인스턴스
settings = Settings()


def setup_directories():
    """필요한 디렉토리 생성"""
    directories = [
        settings.storage_path,
        settings.hwp_storage_path,
        settings.pdf_storage_path,
        settings.md_storage_path,
        settings.selenium_download_path,
    ]

    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)


def get_db_url() -> str:
    """데이터베이스 URL 반환"""
    return settings.database_url


def get_storage_path(file_type: str = "general") -> Path:
    """파일 타입에 따른 저장 경로 반환"""
    if file_type == "hwp":
        return settings.hwp_storage_path
    elif file_type == "pdf":
        return settings.pdf_storage_path
    elif file_type == "markdown":
        return settings.md_storage_path
    else:
        return settings.storage_path


def is_debug_mode() -> bool:
    """디버그 모드 확인"""
    return settings.debug