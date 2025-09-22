"""
데이터베이스 모델 정의 (설계 기반)
"""

from sqlalchemy import (
    Column, String, Integer, BigInteger, Float, Boolean,
    DateTime, Text, ForeignKey, Index, UniqueConstraint,
    func
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()


class BidAnnouncement(Base):
    """입찰공고 메인 테이블"""
    __tablename__ = 'bid_announcements'

    # 기본 키
    bid_notice_no = Column(String(20), primary_key=True)
    bid_notice_ord = Column(String(3), default='000')

    # 공고 정보
    title = Column(String(500), nullable=False)
    organization_code = Column(String(20))
    organization_name = Column(String(200))
    department_name = Column(String(200))

    # 일정
    announcement_date = Column(DateTime)
    bid_start_date = Column(DateTime)
    bid_end_date = Column(DateTime)
    opening_date = Column(DateTime)

    # 금액
    estimated_price = Column(BigInteger)
    assigned_budget = Column(BigInteger)

    # 입찰 정보
    bid_method = Column(String(50))
    contract_method = Column(String(50))

    # 담당자
    officer_name = Column(String(100))
    officer_phone = Column(String(50))
    officer_email = Column(String(100))

    # URL
    detail_page_url = Column(Text)
    standard_doc_url = Column(Text)

    # 상태
    status = Column(String(20), default='active')
    collection_status = Column(String(20), default='pending')

    # 메타데이터
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)
    collected_at = Column(DateTime)

    # 관계
    documents = relationship("BidDocument", back_populates="announcement")
    attachments = relationship("BidAttachment", back_populates="announcement")
    search_index = relationship("BidSearchIndex", back_populates="announcement", uselist=False)
    tag_relations = relationship("BidTagRelation", back_populates="announcement")

    # 인덱스
    __table_args__ = (
        Index('idx_announcement_date', 'announcement_date'),
        Index('idx_organization', 'organization_code', 'organization_name'),
        Index('idx_status', 'status', 'collection_status'),
        Index('idx_dates', 'bid_start_date', 'bid_end_date'),
    )


class BidDocument(Base):
    """문서 저장 테이블"""
    __tablename__ = 'bid_documents'

    document_id = Column(Integer, primary_key=True, autoincrement=True)
    bid_notice_no = Column(String(20), ForeignKey('bid_announcements.bid_notice_no'), nullable=False)

    # 문서 정보
    document_type = Column(String(20))  # 'standard', 'attachment1', etc
    file_name = Column(String(500))
    file_extension = Column(String(10))
    file_size = Column(BigInteger)

    # URL 정보
    download_url = Column(Text)
    file_seq = Column(Integer)

    # 저장 정보
    storage_path = Column(Text)
    markdown_path = Column(Text)

    # 처리 상태
    download_status = Column(String(20), default='pending')
    processing_status = Column(String(20), default='pending')

    # 추출된 내용
    extracted_text = Column(Text)
    text_length = Column(Integer)
    extraction_method = Column(String(50))

    # 메타데이터
    downloaded_at = Column(DateTime)
    processed_at = Column(DateTime)
    error_message = Column(Text)

    # 관계
    announcement = relationship("BidAnnouncement", back_populates="documents")

    # 인덱스
    __table_args__ = (
        Index('idx_bid_doc', 'bid_notice_no', 'document_type'),
        Index('idx_doc_status', 'download_status', 'processing_status'),
    )


class BidAttachment(Base):
    """첨부파일 메타 테이블"""
    __tablename__ = 'bid_attachments'

    attachment_id = Column(Integer, primary_key=True, autoincrement=True)
    bid_notice_no = Column(String(20), ForeignKey('bid_announcements.bid_notice_no'), nullable=False)

    # 첨부파일 정보
    attachment_index = Column(Integer)  # 1~10
    file_name = Column(String(500))
    file_url = Column(Text)
    file_type = Column(String(50))

    # 분류
    document_category = Column(String(50))  # '시방서', '내역서', '도면', etc

    # 처리 여부
    should_download = Column(Boolean, default=False)
    is_downloaded = Column(Boolean, default=False)

    # 관계
    announcement = relationship("BidAnnouncement", back_populates="attachments")

    # 인덱스
    __table_args__ = (
        Index('idx_bid_attach', 'bid_notice_no', 'attachment_index'),
    )


class BidSearchIndex(Base):
    """검색 최적화 테이블"""
    __tablename__ = 'bid_search_index'

    search_id = Column(Integer, primary_key=True, autoincrement=True)
    bid_notice_no = Column(String(20), ForeignKey('bid_announcements.bid_notice_no'), nullable=False)

    # 검색 필드
    search_title = Column(Text)
    search_organization = Column(Text)
    search_content = Column(Text)

    # 카테고리
    industry_category = Column(String(100))
    region = Column(String(100))

    # 금액 범위 (검색용)
    price_range = Column(String(20))

    # 관계
    announcement = relationship("BidAnnouncement", back_populates="search_index")

    # 인덱스
    __table_args__ = (
        Index('idx_category', 'industry_category', 'region'),
    )


class BidTag(Base):
    """태그 마스터 테이블"""
    __tablename__ = 'bid_tags'

    tag_id = Column(Integer, primary_key=True, autoincrement=True)
    tag_name = Column(String(100), unique=True, nullable=False)
    tag_category = Column(String(50))  # 'industry', 'technology', 'region', 'requirement'

    # 통계
    usage_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

    # 관계
    tag_relations = relationship("BidTagRelation", back_populates="tag")

    # 인덱스
    __table_args__ = (
        Index('idx_tag_name', 'tag_name'),
        Index('idx_tag_category', 'tag_category'),
    )


class BidTagRelation(Base):
    """공고-태그 연결 테이블"""
    __tablename__ = 'bid_tag_relations'

    relation_id = Column(Integer, primary_key=True, autoincrement=True)
    bid_notice_no = Column(String(20), ForeignKey('bid_announcements.bid_notice_no'), nullable=False)
    tag_id = Column(Integer, ForeignKey('bid_tags.tag_id'), nullable=False)

    # 태그 메타데이터
    relevance_score = Column(Float, default=1.0)  # 관련도 점수
    source = Column(String(50))  # 'auto', 'manual', 'ai'
    created_at = Column(DateTime, default=datetime.utcnow)

    # 관계
    announcement = relationship("BidAnnouncement", back_populates="tag_relations")
    tag = relationship("BidTag", back_populates="tag_relations")

    # 인덱스 및 제약
    __table_args__ = (
        UniqueConstraint('bid_notice_no', 'tag_id', name='unique_bid_tag'),
        Index('idx_bid_tags', 'bid_notice_no'),
        Index('idx_tag_bids', 'tag_id'),
    )