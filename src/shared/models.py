"""
공통 데이터베이스 모델
"""

from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, ForeignKey, Numeric, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base


class BidAnnouncement(Base):
    """입찰 공고 모델"""
    __tablename__ = "bid_announcements"

    id = Column(Integer, primary_key=True, index=True)
    bid_notice_no = Column(String(50), unique=True, nullable=False, index=True)
    title = Column(Text, nullable=False)
    organization_name = Column(String(200), nullable=False)
    contact_info = Column(Text)
    
    # 날짜 정보
    announcement_date = Column(DateTime, nullable=False)
    document_submission_start = Column(DateTime)
    document_submission_end = Column(DateTime)
    opening_date = Column(DateTime)
    
    # 금액 정보
    bid_amount = Column(Numeric(15, 0))
    currency = Column(String(10), default="KRW")
    
    # 분류 정보
    industry_type = Column(String(100))
    location = Column(String(100))
    
    # 추가 정보
    bid_method = Column(String(50))
    qualification = Column(Text)
    notes = Column(Text)
    
    # 링크 정보
    detail_url = Column(Text)
    document_url = Column(Text)
    
    # 내부 관리
    status = Column(String(20), default="active")
    is_processed = Column(Boolean, default=False)
    
    # 타임스탬프
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 관계 설정
    documents = relationship("BidDocument", back_populates="bid_announcement")
    bookmarks = relationship("UserBidBookmark", back_populates="bid_announcement")


class BidDocument(Base):
    """입찰 첫부 문서 모델"""
    __tablename__ = "bid_documents"

    id = Column(Integer, primary_key=True, index=True)
    bid_announcement_id = Column(Integer, ForeignKey("bid_announcements.id"), nullable=False)

    # 파일 정보
    file_name = Column(String(255), nullable=False)
    file_path = Column(Text)
    file_size = Column(Integer)
    file_type = Column(String(10))

    # 다운로드 정보
    download_url = Column(Text)
    download_status = Column(String(20), default="pending")

    # 처리 정보 - 마크다운 파일 경로 추가
    markdown_file_path = Column(Text)  # 마크다운 파일 경로
    extracted_text_length = Column(Integer)  # 추출된 텍스트 길이
    processed_at = Column(DateTime)  # 처리 시간
    processing_status = Column(String(20), default="pending")
    processing_error = Column(Text)
    
    # 메타데이터
    file_metadata = Column(JSON)
    
    # 타임스탬프
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 관계 설정
    bid_announcement = relationship("BidAnnouncement", back_populates="documents")


class CollectionLog(Base):
    """데이터 수집 로그 모델"""
    __tablename__ = "collection_logs"

    id = Column(Integer, primary_key=True, index=True)
    
    # 수집 정보
    collection_type = Column(String(50), nullable=False)  # 'api', 'crawler', 'manual'
    collection_date = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    # 결과 정보
    total_found = Column(Integer, default=0)
    new_items = Column(Integer, default=0)
    updated_items = Column(Integer, default=0)
    failed_items = Column(Integer, default=0)
    
    # 상태 정보
    status = Column(String(20), nullable=False)  # 'running', 'completed', 'failed'
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime)
    
    # 오류 정보
    error_message = Column(Text)
    error_details = Column(JSON)
    
    # 추가 정보
    notes = Column(Text)
    
    # 타임스탬프
    created_at = Column(DateTime, default=datetime.utcnow)


class User(Base):
    """사용자 모델 (기본)"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False)
    company = Column(String(200))
    
    # 인증 정보
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    
    # 타임스탬프
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 관계 설정
    bookmarks = relationship("UserBidBookmark", back_populates="user")


class UserBidBookmark(Base):
    """사용자 입찰 북마크 모델"""
    __tablename__ = "user_bid_bookmarks"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    bid_announcement_id = Column(Integer, ForeignKey("bid_announcements.id"), nullable=False)
    
    # 북마크 정보
    bookmark_date = Column(DateTime, default=datetime.utcnow)
    notes = Column(Text)
    
    # 타임스탬프
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 관계 설정
    user = relationship("User", back_populates="bookmarks")
    bid_announcement = relationship("BidAnnouncement", back_populates="bookmarks")