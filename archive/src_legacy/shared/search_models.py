"""
검색 최적화를 위한 추가 모델
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Index, Numeric
from sqlalchemy.dialects.postgresql import TSVECTOR
from datetime import datetime
from .database import Base


class BidDocumentSearch(Base):
    """입찰 문서 검색용 모델 (검색 최적화)"""
    __tablename__ = "bid_document_search"

    id = Column(Integer, primary_key=True, index=True)
    bid_announcement_id = Column(Integer, ForeignKey("bid_announcements.id"), nullable=False, index=True)
    bid_document_id = Column(Integer, ForeignKey("bid_documents.id"), nullable=False, index=True)

    # 검색 필드 (빠른 검색을 위해 주요 내용 저장)
    bid_notice_no = Column(String(50), nullable=False, index=True)
    title = Column(Text, nullable=False)
    organization_name = Column(String(200), nullable=False, index=True)
    announcement_date = Column(DateTime, nullable=False, index=True)
    bid_amount = Column(Numeric(15, 0), index=True)

    # 문서에서 추출된 주요 정보
    summary = Column(Text)  # 요약 (첫 500자)
    keywords = Column(Text)  # 추출된 키워드 (쉼표 구분)
    important_dates = Column(Text)  # 중요 날짜들
    requirements = Column(Text)  # 주요 요구사항

    # PostgreSQL 전체 텍스트 검색을 위한 벡터 컬럼
    search_vector = Column(TSVECTOR)

    # 마크다운 파일 경로 (상세 내용 접근용)
    markdown_file_path = Column(Text)

    # 타임스탬프
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 복합 인덱스 설정
    __table_args__ = (
        # 조직명 + 날짜 복합 인덱스
        Index('idx_org_date', 'organization_name', 'announcement_date'),
        # 금액 범위 검색을 위한 인덱스
        Index('idx_amount', 'bid_amount'),
        # 전체 텍스트 검색 인덱스 (GIN)
        Index('idx_search_vector', 'search_vector', postgresql_using='gin'),
    )


class SearchKeyword(Base):
    """검색 키워드 통계 모델"""
    __tablename__ = "search_keywords"

    id = Column(Integer, primary_key=True, index=True)
    keyword = Column(String(100), nullable=False, unique=True, index=True)
    search_count = Column(Integer, default=1)
    last_searched = Column(DateTime, default=datetime.utcnow)

    # 타임스탬프
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)