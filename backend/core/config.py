"""
Core configuration settings for Odin-AI
"""

from typing import Optional, List
from pydantic_settings import BaseSettings
from pydantic import validator
import os
from pathlib import Path


class Settings(BaseSettings):
    """Application settings"""

    # Basic App Settings
    PROJECT_NAME: str = "Odin-AI"
    VERSION: str = "0.1.0"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True

    # Security
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Database
    DATABASE_URL: str
    REDIS_URL: str = "redis://localhost:6379/0"

    # Public Data Portal API
    PUBLIC_DATA_API_KEY: str
    PUBLIC_DATA_BASE_URL: str = "https://www.data.go.kr/"

    # G2B Crawler Settings
    G2B_LOGIN_ID: Optional[str] = None
    G2B_LOGIN_PASSWORD: Optional[str] = None
    CRAWLER_DELAY_MIN: int = 2
    CRAWLER_DELAY_MAX: int = 5
    CRAWLER_USER_AGENT: str = "Odin-AI/1.0 (contact@odin-ai.kr)"

    # AI/ML Settings
    OPENAI_API_KEY: str
    PINECONE_API_KEY: Optional[str] = None
    PINECONE_ENVIRONMENT: Optional[str] = None

    # Email Settings
    SMTP_SERVER: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USERNAME: str
    SMTP_PASSWORD: str

    # File Storage
    UPLOAD_DIR: str = "./uploaded_files"
    PROCESSED_DIR: str = "./processed_docs"
    TEMP_DIR: str = "./temp_files"

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "./logs/odin-ai.log"

    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 60
    RATE_LIMIT_PER_HOUR: int = 1000

    # Celery
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/1"

    # CORS Settings
    BACKEND_CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8080"]

    @validator("BACKEND_CORS_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v: str | List[str]) -> List[str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)

    @validator("DATABASE_URL", pre=True)
    def validate_database_url(cls, v: str) -> str:
        if not v:
            raise ValueError("DATABASE_URL must be set")
        return v

    @validator("SECRET_KEY", pre=True)
    def validate_secret_key(cls, v: str) -> str:
        if not v:
            raise ValueError("SECRET_KEY must be set")
        return v

    def create_directories(self):
        """Create necessary directories"""
        directories = [
            self.UPLOAD_DIR,
            self.PROCESSED_DIR,
            self.TEMP_DIR,
            Path(self.LOG_FILE).parent
        ]

        for directory in directories:
            Path(directory).mkdir(parents=True, exist_ok=True)

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


# Global settings instance
settings = Settings()

# Create directories on import
settings.create_directories()