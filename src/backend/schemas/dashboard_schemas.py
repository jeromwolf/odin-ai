"""
대시보드 관련 Pydantic 스키마
"""

from pydantic import BaseModel, Field
from typing import Dict, List, Any, Optional
from datetime import datetime
from enum import Enum


# ========== 대시보드 개요 ==========

class DashboardOverview(BaseModel):
    """대시보드 개요 스키마"""
    today_stats: Dict[str, int] = Field(..., description="오늘의 통계")
    weekly_trend: Dict[str, Any] = Field(..., description="주간 트렌드")
    last_updated: datetime = Field(..., description="최종 업데이트 시간")

    class Config:
        schema_extra = {
            "example": {
                "today_stats": {
                    "new_bids": 42,
                    "upcoming_deadlines": 7,
                    "bookmarks": 15,
                    "matched_bids": 23
                },
                "weekly_trend": {
                    "total_bids": 285,
                    "trend_percentage": 12.5,
                    "trend_direction": "up"
                },
                "last_updated": "2025-09-17T10:30:00Z"
            }
        }


# ========== 입찰 통계 ==========

class BidStatistics(BaseModel):
    """입찰 통계 스키마"""
    period: str = Field(..., description="통계 기간")
    daily_stats: List[Dict[str, Any]] = Field(..., description="일별 통계")
    category_distribution: List[Dict[str, Any]] = Field(..., description="카테고리별 분포")
    price_ranges: Dict[str, int] = Field(..., description="금액대별 분포")
    top_organizations: List[Dict[str, Any]] = Field(..., description="상위 발주기관")
    avg_competition_rate: float = Field(..., description="평균 경쟁률")

    class Config:
        schema_extra = {
            "example": {
                "period": "7d",
                "daily_stats": [
                    {"date": "2025-09-11", "count": 45},
                    {"date": "2025-09-12", "count": 52}
                ],
                "category_distribution": [
                    {"category": "IT/소프트웨어", "count": 120, "percentage": 35.2},
                    {"category": "건설", "count": 89, "percentage": 26.1}
                ],
                "price_ranges": {
                    "1억 미만": 150,
                    "1억-10억": 200,
                    "10억-50억": 50,
                    "50억-100억": 10,
                    "100억 이상": 5
                },
                "top_organizations": [
                    {"name": "한국전력공사", "count": 25, "total_amount": 5000000000}
                ],
                "avg_competition_rate": 5.2
            }
        }


# ========== 마감 임박 ==========

class UrgencyLevel(str, Enum):
    """긴급도 레벨"""
    CRITICAL = "critical"  # 24시간 이내
    HIGH = "high"  # 3일 이내
    MEDIUM = "medium"  # 7일 이내
    LOW = "low"  # 7일 이후


class UpcomingDeadlines(BaseModel):
    """마감 임박 입찰 스키마"""
    bid_id: int = Field(..., description="입찰 ID")
    bid_notice_no: str = Field(..., description="입찰공고번호")
    title: str = Field(..., description="입찰 제목")
    organization: str = Field(..., description="발주기관")
    closing_date: datetime = Field(..., description="마감일시")
    hours_remaining: int = Field(..., description="남은 시간")
    estimated_price: Optional[int] = Field(None, description="예정가격")
    is_bookmarked: bool = Field(..., description="북마크 여부")
    urgency_level: UrgencyLevel = Field(..., description="긴급도")

    class Config:
        schema_extra = {
            "example": {
                "bid_id": 123,
                "bid_notice_no": "20250917-001",
                "title": "2025년도 정보시스템 유지보수",
                "organization": "한국전력공사",
                "closing_date": "2025-09-20T14:00:00Z",
                "hours_remaining": 72,
                "estimated_price": 150000000,
                "is_bookmarked": True,
                "urgency_level": "high"
            }
        }


# ========== AI 추천 ==========

class RecommendedBids(BaseModel):
    """AI 추천 입찰 스키마"""
    bid_id: int = Field(..., description="입찰 ID")
    bid_notice_no: str = Field(..., description="입찰공고번호")
    title: str = Field(..., description="입찰 제목")
    organization: str = Field(..., description="발주기관")
    closing_date: datetime = Field(..., description="마감일시")
    estimated_price: Optional[int] = Field(None, description="예정가격")
    ai_score: int = Field(..., ge=0, le=100, description="AI 매칭 점수")
    success_probability: float = Field(..., ge=0, le=100, description="예상 성공률")
    match_reasons: List[str] = Field(..., description="매칭 이유")
    is_bookmarked: bool = Field(..., description="북마크 여부")

    class Config:
        schema_extra = {
            "example": {
                "bid_id": 456,
                "bid_notice_no": "20250917-002",
                "title": "클라우드 서비스 구축 사업",
                "organization": "정부통합전산센터",
                "closing_date": "2025-09-25T14:00:00Z",
                "estimated_price": 500000000,
                "ai_score": 92,
                "success_probability": 78.5,
                "match_reasons": [
                    "사용자 관심 분야 일치",
                    "예산 범위 적합",
                    "과거 유사 입찰 성공 이력"
                ],
                "is_bookmarked": False
            }
        }


# ========== 최근 활동 ==========

class ActivityType(str, Enum):
    """활동 타입"""
    BOOKMARK = "bookmark"
    VIEW = "view"
    SEARCH = "search"
    DOWNLOAD = "download"
    BID_SUBMIT = "bid_submit"


class RecentActivity(BaseModel):
    """최근 활동 스키마"""
    activity_type: ActivityType = Field(..., description="활동 타입")
    activity_time: datetime = Field(..., description="활동 시간")
    title: str = Field(..., description="활동 제목")
    description: Optional[str] = Field(None, description="활동 설명")
    link: Optional[str] = Field(None, description="관련 링크")

    class Config:
        schema_extra = {
            "example": {
                "activity_type": "bookmark",
                "activity_time": "2025-09-17T09:15:00Z",
                "title": "입찰 북마크: AI 플랫폼 구축 사업",
                "description": "한국정보화진흥원",
                "link": "/bids/789"
            }
        }


# ========== 시장 트렌드 ==========

class MarketTrends(BaseModel):
    """시장 트렌드 스키마"""
    industry_growth: List[Dict[str, Any]] = Field(..., description="업종별 성장률")
    trending_keywords: List[Dict[str, Any]] = Field(..., description="인기 키워드")
    insights: List[Dict[str, Any]] = Field(..., description="시장 인사이트")
    analysis_date: datetime = Field(..., description="분석 날짜")

    class Config:
        schema_extra = {
            "example": {
                "industry_growth": [
                    {"industry": "IT/소프트웨어", "current_count": 450, "growth_rate": 15.2},
                    {"industry": "건설", "current_count": 320, "growth_rate": -5.3}
                ],
                "trending_keywords": [
                    {"keyword": "AI", "count": 245, "growth": 15.2},
                    {"keyword": "클라우드", "count": 189, "growth": 8.7}
                ],
                "insights": [
                    {
                        "type": "trend",
                        "title": "IT 서비스 입찰 15% 증가",
                        "description": "지난달 대비 IT 관련 입찰이 15% 증가했습니다.",
                        "importance": "high"
                    }
                ],
                "analysis_date": "2025-09-17T00:00:00Z"
            }
        }


# ========== 사용자 통계 ==========

class UserStats(BaseModel):
    """사용자 통계 스키마"""
    total_bookmarks: int = Field(..., description="총 북마크 수")
    total_searches: int = Field(..., description="총 검색 수")
    success_rate: float = Field(..., description="입찰 성공률")
    active_bids: int = Field(..., description="진행 중인 입찰")
    won_bids: int = Field(..., description="낙찰된 입찰")
    lost_bids: int = Field(..., description="실패한 입찰")
    member_since: datetime = Field(..., description="가입일")

    class Config:
        schema_extra = {
            "example": {
                "total_bookmarks": 45,
                "total_searches": 128,
                "success_rate": 32.5,
                "active_bids": 3,
                "won_bids": 12,
                "lost_bids": 25,
                "member_since": "2025-01-15T00:00:00Z"
            }
        }


# ========== 알림 ==========

class NotificationType(str, Enum):
    """알림 타입"""
    BID_MATCH = "bid_match"  # 입찰 매칭
    DEADLINE = "deadline"  # 마감 임박
    RESULT = "result"  # 입찰 결과
    SYSTEM = "system"  # 시스템 알림


class DashboardNotification(BaseModel):
    """대시보드 알림 스키마"""
    id: int = Field(..., description="알림 ID")
    type: NotificationType = Field(..., description="알림 타입")
    title: str = Field(..., description="알림 제목")
    message: str = Field(..., description="알림 내용")
    created_at: datetime = Field(..., description="생성 시간")
    is_read: bool = Field(..., description="읽음 여부")
    action_link: Optional[str] = Field(None, description="액션 링크")

    class Config:
        schema_extra = {
            "example": {
                "id": 1,
                "type": "bid_match",
                "title": "새로운 매칭 입찰",
                "message": "관심 키워드와 일치하는 새로운 입찰이 등록되었습니다.",
                "created_at": "2025-09-17T10:00:00Z",
                "is_read": False,
                "action_link": "/bids/new"
            }
        }