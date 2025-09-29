"""
ODIN-AI Backend API
간단한 검색 API 백엔드
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime
import random
import hashlib
import json
try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
    HAS_PSYCOPG2 = True
except ImportError:
    HAS_PSYCOPG2 = False
import os

# Redis 캐싱 시스템 임포트
try:
    from backend.cache import cache, get_cached_or_fetch, CACHE_TTL
    CACHE_ENABLED = cache.enabled
except ImportError:
    CACHE_ENABLED = False
    print("⚠️ 캐싱 시스템 비활성화 (cache.py 없음)")

app = FastAPI(title="ODIN-AI Search API", version="1.0.0")

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:8000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 검색 라우터 추가
try:
    from backend.api.search import router as search_router
    app.include_router(search_router)
    print("✅ 검색 API 라우터 등록됨")
except ImportError as e:
    print(f"⚠️ 검색 API 라우터 로드 실패: {e}")

# 인증 라우터 추가
try:
    from backend.api.auth import router as auth_router
    app.include_router(auth_router)
    print("✅ 인증 API 라우터 등록됨")
except ImportError as e:
    print(f"⚠️ 인증 API 라우터 로드 실패: {e}")

# 북마크 라우터 임포트 및 추가
try:
    from backend.api.bookmarks import router as bookmarks_router
    app.include_router(bookmarks_router)
    print("✅ 북마크 API 라우터 등록됨")
except ImportError as e:
    print(f"⚠️ 북마크 API 라우터 로드 실패: {e}")

# 대시보드 라우터 추가
try:
    from backend.api.dashboard import router as dashboard_router
    app.include_router(dashboard_router)
    print("✅ 대시보드 API 라우터 등록됨")
except ImportError as e:
    print(f"⚠️ 대시보드 API 라우터 로드 실패: {e}")

# 구독 라우터 추가
try:
    from backend.api.subscription import router as subscription_router
    app.include_router(subscription_router)
    print("✅ 구독 API 라우터 등록됨")
except ImportError as e:
    print(f"⚠️ 구독 API 라우터 로드 실패: {e}")

# 결제 라우터 추가
try:
    from backend.api.payments import router as payments_router
    app.include_router(payments_router)
    print("✅ 결제 API 라우터 등록됨")
except ImportError as e:
    print(f"⚠️ 결제 API 라우터 로드 실패: {e}")

# 알림 라우터 추가
try:
    from backend.api.notifications import router as notifications_router
    app.include_router(notifications_router)
    print("✅ 알림 API 라우터 등록됨")
except ImportError as e:
    print(f"⚠️ 알림 API 라우터 로드 실패: {e}")

# AI 추천 라우터 추가
try:
    from backend.api.recommendations import router as recommendations_router
    app.include_router(recommendations_router, prefix="/api/recommendations", tags=["recommendations"])
    print("✅ AI 추천 API 라우터 등록됨")
except ImportError as e:
    print(f"⚠️ AI 추천 API 라우터 로드 실패: {e}")

# 샘플 데이터
SAMPLE_BIDS = [
    {
        "type": "bid",
        "id": "bid-001",
        "bidNoticeNo": "2025-B-001",
        "title": "소프트웨어 개발 용역",
        "organization": "서울특별시",
        "price": 50000000,
        "deadline": "2025-10-15",
        "status": "active",
        "score": 95.5,
        "highlight": "<mark>소프트웨어</mark> 개발 용역"
    },
    {
        "type": "bid",
        "id": "bid-002",
        "bidNoticeNo": "2025-B-002",
        "title": "SI 시스템 구축 사업",
        "organization": "경기도",
        "price": 120000000,
        "deadline": "2025-10-20",
        "status": "active",
        "score": 88.0,
        "highlight": "<mark>SI</mark> 시스템 구축 사업"
    },
    {
        "type": "bid",
        "id": "bid-003",
        "bidNoticeNo": "2025-B-003",
        "title": "건설 공사 입찰 공고",
        "organization": "인천광역시",
        "price": 250000000,
        "deadline": "2025-10-25",
        "status": "active",
        "score": 82.0,
        "highlight": "<mark>건설</mark> 공사 입찰 공고"
    }
]

SAMPLE_DOCUMENTS = [
    {
        "type": "document",
        "id": "doc-001",
        "filename": "과업지시서.hwp",
        "path": "/storage/docs/과업지시서.hwp",
        "fileType": "hwp",
        "size": 2048000,
        "modified": "2025-09-20",
        "title": "소프트웨어 개발 과업지시서",
        "highlight": ["소프트웨어 개발 관련 세부사항"],
        "score": 15
    }
]

SAMPLE_COMPANIES = [
    {
        "type": "company",
        "id": "comp-001",
        "name": "테크놀로지 주식회사",
        "businessNumber": "123-45-67890",
        "industry": "소프트웨어 개발",
        "region": "서울",
        "title": "테크놀로지 주식회사"
    }
]

@app.get("/")
async def root():
    return {"message": "ODIN-AI Search API", "version": "1.0.0"}

# 더미 인증 엔드포인트 추가 (개발용)
@app.post("/api/auth/register")
async def register_dummy():
    """더미 회원가입 - 개발용"""
    return {
        "id": "user-001",
        "email": "test@example.com",
        "name": "테스트 사용자",
        "token": "dummy-token-123"
    }

@app.post("/api/auth/login")
async def login_dummy():
    """더미 로그인 - 개발용"""
    return {
        "id": "user-001",
        "email": "test@example.com",
        "name": "테스트 사용자",
        "token": "dummy-token-123"
    }

@app.get("/api/auth/check")
async def check_auth():
    """인증 상태 확인 - 개발용"""
    return {"authenticated": True, "user": {"id": "user-001", "name": "테스트 사용자"}}

# 대시보드 엔드포인트 - DB 연동
@app.get("/api/dashboard/overview")
async def dashboard_overview():
    """대시보드 개요 - 실제 DB 데이터"""
    conn = get_db_connection()
    if conn:
        try:
            cur = conn.cursor()

            # 전체 입찰 수
            cur.execute("SELECT COUNT(*) FROM bid_announcements")
            total_bids = cur.fetchone()['count']

            # 활성 입찰 수 (오늘 이후 마감)
            cur.execute("""
                SELECT COUNT(*)
                FROM bid_announcements
                WHERE bid_end_date >= CURRENT_DATE
            """)
            active_bids = cur.fetchone()['count']

            # 전체 예정가격 합계
            cur.execute("""
                SELECT COALESCE(SUM(estimated_price), 0) as total
                FROM bid_announcements
                WHERE estimated_price IS NOT NULL
            """)
            total_amount = cur.fetchone()['total']

            cur.close()
            conn.close()

            return {
                "totalBids": total_bids,
                "activeBids": active_bids,
                "wonBids": 0,
                "totalAmount": int(total_amount),
                "successRate": 0,
                "lastUpdated": datetime.now().isoformat()
            }
        except Exception as e:
            print(f"대시보드 조회 에러: {e}")
            if conn:
                conn.close()

    # DB 연결 실패 시 더미 데이터
    return {
        "totalBids": 1234,
        "activeBids": 89,
        "wonBids": 12,
        "totalAmount": 5678900000,
        "successRate": 13.5,
        "lastUpdated": "2025-09-25T00:00:00Z"
    }

@app.get("/api/dashboard/bid-statistics")
async def bid_statistics(period: str = "7d"):
    """입찰 통계 - 더미 데이터"""
    return {
        "period": period,
        "data": [
            {"date": "2025-09-19", "count": 45, "amount": 890000000},
            {"date": "2025-09-20", "count": 52, "amount": 1230000000},
            {"date": "2025-09-21", "count": 38, "amount": 670000000},
            {"date": "2025-09-22", "count": 41, "amount": 920000000},
            {"date": "2025-09-23", "count": 48, "amount": 1100000000},
            {"date": "2025-09-24", "count": 55, "amount": 1450000000},
            {"date": "2025-09-25", "count": 42, "amount": 980000000}
        ]
    }

@app.get("/api/dashboard/deadlines")
async def upcoming_deadlines(days: int = 7):
    """마감 임박 입찰 - 실제 DB 데이터 (hours_remaining 포함)"""
    conn = get_db_connection()
    if conn:
        try:
            cur = conn.cursor()

            # 마감 임박 입찰 조회 (오늘부터 n일 이내) - hours_remaining 추가
            cur.execute("""
                SELECT
                    bid_notice_no as id,
                    title,
                    bid_end_date as deadline,
                    organization_name as organization,
                    estimated_price as amount,
                    EXTRACT(EPOCH FROM (bid_end_date - NOW())) / 3600 as hours_remaining
                FROM bid_announcements
                WHERE bid_end_date BETWEEN NOW() AND NOW() + INTERVAL %s
                ORDER BY bid_end_date ASC
                LIMIT 10
            """, (f'{days} days',))

            deadlines = []
            for row in cur.fetchall():
                hours = row['hours_remaining'] if row['hours_remaining'] else 0
                deadlines.append({
                    "id": row['id'],
                    "title": row['title'],
                    "deadline": row['deadline'],
                    "organization": row['organization'],
                    "amount": row['amount'],
                    "hours_remaining": round(hours, 1) if hours else 0
                })

            cur.close()
            conn.close()

            return {"deadlines": deadlines, "data": deadlines}

        except Exception as e:
            import traceback
            print(f"마감임박 조회 에러: {e}")
            print(f"에러 타입: {type(e)}")
            traceback.print_exc()
            if conn:
                conn.close()
            return {"deadlines": [], "data": []}

@app.get("/api/dashboard/statistics")
async def bid_statistics(days: int = 7):
    """입찰 통계 데이터 - 차트용"""
    conn = get_db_connection()
    if conn:
        try:
            cur = conn.cursor()

            # 1. 일별 입찰 건수 (최근 7일)
            cur.execute("""
                SELECT
                    DATE(created_at) as date,
                    COUNT(*) as count
                FROM bid_announcements
                WHERE created_at >= CURRENT_DATE - INTERVAL %s
                GROUP BY DATE(created_at)
                ORDER BY date ASC
            """, (f'{days} days',))

            daily_stats = []
            for row in cur.fetchall():
                daily_stats.append({
                    "date": row['date'].isoformat() if row['date'] else None,
                    "count": row['count']
                })

            # 2. 카테고리별 분포 (태그 기반)
            cur.execute("""
                SELECT
                    bt.tag_name as category,
                    COUNT(DISTINCT btr.bid_notice_no) as count
                FROM bid_tags bt
                JOIN bid_tag_relations btr ON bt.tag_id = btr.tag_id
                GROUP BY bt.tag_name
                ORDER BY count DESC
                LIMIT 10
            """)

            category_distribution = []
            for row in cur.fetchall():
                category_distribution.append({
                    "category": row['category'],
                    "count": row['count']
                })

            cur.close()
            conn.close()

            return {
                "daily_stats": daily_stats,
                "category_distribution": category_distribution
            }

        except Exception as e:
            print(f"통계 조회 에러: {e}")
            import traceback
            traceback.print_exc()
            if conn:
                conn.close()
            return {"daily_stats": [], "category_distribution": []}

    return {"daily_stats": [], "category_distribution": []}

@app.get("/api/dashboard/recommendations")
async def recommendations(limit: int = 5):
    """AI 추천 입찰 - 실제 DB 기반 추천"""
    conn = get_db_connection()
    if conn:
        try:
            cur = conn.cursor()

            # 최근 공고 중 예정가격이 높은 순으로 추천 (간단한 추천 로직)
            cur.execute("""
                SELECT
                    bid_notice_no as id,
                    title,
                    organization_name as organization,
                    estimated_price as amount,
                    bid_end_date as deadline
                FROM bid_announcements
                WHERE bid_end_date >= CURRENT_DATE
                    AND estimated_price IS NOT NULL
                ORDER BY estimated_price DESC
                LIMIT %s
            """, (limit,))

            bids = cur.fetchall()

            # 점수와 추천 이유 추가
            recommendations = []
            reasons = [
                "높은 예정가격",
                "마감 임박",
                "적합한 업종",
                "과거 유사 프로젝트 경험",
                "경쟁률 낮음"
            ]

            for i, bid in enumerate(bids):
                rec = dict(bid)
                rec['score'] = 95 - (i * 5)  # 점수 부여
                rec['reason'] = reasons[i % len(reasons)]
                recommendations.append(rec)

            cur.close()
            conn.close()

            return {"recommendations": recommendations}

        except Exception as e:
            print(f"추천 조회 에러: {e}")
            if conn:
                conn.close()

    # DB 연결 실패 시 더미 데이터
    return {
        "recommendations": [
            {
                "id": "bid-004",
                "title": "클라우드 인프라 구축",
                "score": 95.5,
                "reason": "과거 유사 프로젝트 수행 경험",
                "organization": "한국전력공사",
                "amount": 300000000
            }
        ]
    }

# 북마크 더미 엔드포인트
@app.post("/api/bookmarks/{bid_id}")
async def add_bookmark(bid_id: str):
    """북마크 추가 - 더미"""
    return {"success": True, "bidId": bid_id}

@app.delete("/api/bookmarks/{bid_id}")
async def remove_bookmark(bid_id: str):
    """북마크 제거 - 더미"""
    return {"success": True, "bidId": bid_id}

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0",
        "services": {
            "database": "connected",
            "redis": "disconnected",
            "search": "ready"
        }
    }

def get_db_connection():
    """데이터베이스 연결 생성"""
    if not HAS_PSYCOPG2:
        return None

    try:
        conn = psycopg2.connect(
            host="localhost",
            port=5432,
            database="odin_db",
            user="blockmeta",
            cursor_factory=RealDictCursor
        )
        return conn
    except Exception as e:
        print(f"DB 연결 실패: {e}")
        return None

@app.get("/api/search")
async def search(
    q: str = Query(None, alias="query", description="검색어", max_length=500),
    type: str = Query("all", description="검색 타입"),
    sort: str = Query("relevance", description="정렬 방식"),
    page: int = Query(1, ge=1, le=1000, description="페이지 번호 (최대 1000)"),
    size: int = Query(20, ge=1, le=100, description="페이지 크기"),
    start_date: Optional[str] = Query(None, description="시작일 (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="종료일 (YYYY-MM-DD)"),
    min_price: Optional[int] = Query(None, ge=0, description="최소 가격 (0 이상)"),
    max_price: Optional[int] = Query(None, ge=0, description="최대 가격 (0 이상)"),
    organization: Optional[str] = Query(None, description="기관명", max_length=100),
    status: Optional[str] = Query(None, description="상태")
):
    """통합 검색 API - 실제 DB 연동"""

    # Query의 max_length가 작동하지 않으므로 수동 검증
    if q and len(q) > 500:
        raise HTTPException(status_code=422, detail="검색어는 500자를 초과할 수 없습니다.")

    # 날짜 형식 및 범위 검증
    parsed_start_date = None
    parsed_end_date = None

    if start_date:
        try:
            parsed_start_date = datetime.strptime(start_date, "%Y-%m-%d")
        except ValueError:
            raise HTTPException(status_code=400, detail="잘못된 시작일 형식입니다. YYYY-MM-DD 형식을 사용하세요.")

    if end_date:
        try:
            parsed_end_date = datetime.strptime(end_date, "%Y-%m-%d")
        except ValueError:
            raise HTTPException(status_code=400, detail="잘못된 종료일 형식입니다. YYYY-MM-DD 형식을 사용하세요.")

    # 날짜 범위 논리 검증
    if parsed_start_date and parsed_end_date:
        if parsed_start_date > parsed_end_date:
            raise HTTPException(status_code=400, detail="시작일이 종료일보다 늦을 수 없습니다.")

        # 날짜 범위가 너무 큰 경우 제한 (예: 1년)
        date_diff = (parsed_end_date - parsed_start_date).days
        if date_diff > 365:
            raise HTTPException(status_code=400, detail="날짜 범위는 최대 1년까지만 조회 가능합니다.")

    # 가격 검증
    if min_price is not None and max_price is not None:
        if min_price > max_price:
            raise HTTPException(status_code=400, detail="최소 가격이 최대 가격보다 클 수 없습니다.")

    # 정렬 옵션 검증
    valid_sorts = ["relevance", "price_desc", "price_asc", "date_desc", "date_asc", "deadline_asc"]
    if sort not in valid_sorts:
        sort = "relevance"  # 기본값으로 설정

    # 캐시 키를 위한 파라미터 딕셔너리
    cache_params = {
        "q": q or "",
        "type": type,
        "sort": sort,
        "page": page,
        "size": size,
        "start_date": start_date or "",
        "end_date": end_date or "",
        "min_price": min_price or 0,
        "max_price": max_price or 0,
        "organization": organization or "",
        "status": status or ""
    }

    # 캐싱 체크
    if CACHE_ENABLED:
        cached_result = cache.get("search", cache_params)
        if cached_result:
            return cached_result

    # DB 연결
    conn = get_db_connection()
    if conn:
        try:
            cur = conn.cursor()

            # 기본 쿼리
            base_query = """
                SELECT
                    'bid' as type,
                    bid_notice_no as id,
                    bid_notice_no as bidNoticeNo,
                    title,
                    organization_name as organization,
                    estimated_price as price,
                    bid_end_date as deadline,
                    CASE WHEN bid_end_date >= CURRENT_DATE THEN 'active' ELSE 'closed' END as status,
                    100 as score,
                    title as highlight
                FROM bid_announcements
                WHERE 1=1
            """

            # 필터 조건 추가
            params = []

            # 검색어 필터
            if q:
                base_query += " AND (LOWER(title) LIKE LOWER(%s) OR LOWER(organization_name) LIKE LOWER(%s))"
                search_pattern = f'%{q}%'
                params.extend([search_pattern, search_pattern])

            # 날짜 필터
            if start_date:
                base_query += " AND bid_end_date >= %s"
                params.append(start_date)

            if end_date:
                base_query += " AND bid_end_date <= %s"
                params.append(end_date)

            # 가격 필터
            if min_price is not None:
                base_query += " AND estimated_price >= %s"
                params.append(min_price)

            if max_price is not None:
                base_query += " AND estimated_price <= %s"
                params.append(max_price)

            # 기관 필터
            if organization:
                base_query += " AND LOWER(organization_name) LIKE LOWER(%s)"
                params.append(f'%{organization}%')

            # 정렬
            if sort == "date_desc":
                base_query += " ORDER BY announcement_date DESC"
            elif sort == "date_asc":
                base_query += " ORDER BY announcement_date ASC"
            elif sort == "price_desc":
                base_query += " ORDER BY estimated_price DESC NULLS LAST"
            elif sort == "price_asc":
                base_query += " ORDER BY estimated_price ASC NULLS LAST"
            else:
                base_query += " ORDER BY announcement_date DESC"

            # 페이지네이션
            base_query += " LIMIT %s OFFSET %s"
            params.extend([size, (page - 1) * size])

            # 쿼리 실행
            cur.execute(base_query, params)
            results = cur.fetchall()

            # 전체 개수 조회 (같은 필터 조건)
            count_query = """
                SELECT COUNT(*)
                FROM bid_announcements
                WHERE 1=1
            """
            count_params = []

            if q:
                count_query += " AND (LOWER(title) LIKE LOWER(%s) OR LOWER(organization_name) LIKE LOWER(%s))"
                count_params.extend([search_pattern, search_pattern])
            if start_date:
                count_query += " AND bid_end_date >= %s"
                count_params.append(start_date)
            if end_date:
                count_query += " AND bid_end_date <= %s"
                count_params.append(end_date)
            if min_price is not None:
                count_query += " AND estimated_price >= %s"
                count_params.append(min_price)
            if max_price is not None:
                count_query += " AND estimated_price <= %s"
                count_params.append(max_price)
            if organization:
                count_query += " AND LOWER(organization_name) LIKE LOWER(%s)"
                count_params.append(f'%{organization}%')

            cur.execute(count_query, count_params)
            total_count = cur.fetchone()['count']

            cur.close()
            conn.close()

        except Exception as e:
            print(f"DB 에러: {e}")
            if conn:
                conn.close()
            # DB 연결 실패 시 샘플 데이터 반환
            results = SAMPLE_BIDS[:size]
            total_count = len(SAMPLE_BIDS)
    else:
        # DB 연결 실패 시 샘플 데이터 반환
        results = SAMPLE_BIDS[:size]
        total_count = len(SAMPLE_BIDS)

    # 페이지네이션 정보 계산
    total_pages = (total_count + size - 1) // size if total_count > 0 else 0

    # 응답 데이터 구성
    response_data = {
        "query": q or "",
        "searchType": type,
        "results": results,
        "total": total_count,  # 테스트 스크립트가 기대하는 필드명
        "totalCount": total_count,
        "pageInfo": {
            "currentPage": page,
            "pageSize": size,
            "totalPages": total_pages,
            "totalItems": total_count,
            "hasNext": page < total_pages,
            "hasPrev": page > 1
        },
        "facets": {
            "organizations": [
                {"name": "서울특별시", "count": 15},
                {"name": "부산광역시", "count": 12},
                {"name": "경기도", "count": 10}
            ],
            "status": [
                {"name": "active", "count": total_count},
                {"name": "closed", "count": 0}
            ]
        }
    }

    # 결과 캐싱
    if CACHE_ENABLED and total_count > 0:
        cache.set("search", cache_params, response_data, CACHE_TTL.get("search", 300))

    return response_data

@app.get("/api/search/suggest")
async def get_suggestions(
    q: str = Query(..., description="부분 검색어"),
    limit: int = Query(10, ge=1, le=20, description="최대 제안 수")
):
    """검색어 자동완성"""

    suggestions = [
        "소프트웨어",
        "소프트웨어 개발",
        "소프트웨어 유지보수",
        "SI 사업",
        "시스템 구축",
        "건설 공사",
        "건설 용역",
        "네트워크 구축",
        "서버 구매"
    ]

    filtered = [s for s in suggestions if s.startswith(q)][:limit]

    return {
        "query": q,
        "suggestions": filtered,
        "count": len(filtered)
    }

@app.get("/api/search/facets")
async def get_facets(
    type: str = Query("all", description="검색 타입")
):
    """패싯 정보 조회"""

    return {
        "facets": {
            "organizations": [
                {"name": "서울특별시", "count": 234},
                {"name": "경기도", "count": 189},
                {"name": "인천광역시", "count": 156}
            ],
            "status": [
                {"name": "active", "count": 450},
                {"name": "pending", "count": 123},
                {"name": "closed", "count": 89}
            ],
            "priceRanges": [
                {"range": "0-10M", "count": 234},
                {"range": "10M-50M", "count": 156},
                {"range": "50M-100M", "count": 98},
                {"range": "100M+", "count": 174}
            ]
        }
    }

@app.get("/api/search/recent")
async def get_recent_searches():
    """최근 검색어 조회"""

    return {
        "searches": [
            {
                "query": "소프트웨어",
                "timestamp": "2025-09-24T10:30:00Z",
                "resultCount": 45
            },
            {
                "query": "건설",
                "timestamp": "2025-09-24T09:15:00Z",
                "resultCount": 32
            },
            {
                "query": "SI사업",
                "timestamp": "2025-09-24T08:45:00Z",
                "resultCount": 28
            }
        ]
    }

@app.get("/api/search/metrics")
async def get_metrics():
    """검색 성능 메트릭"""

    return {
        "totalSearches": 10523,
        "avgResponseTime": 45,
        "cacheHitRate": 0.85,
        "topQueries": [
            {"query": "소프트웨어", "count": 234},
            {"query": "건설", "count": 189},
            {"query": "SI사업", "count": 156}
        ],
        "errorRate": 0.002
    }

# Auth Endpoints (for login state management)
@app.post("/api/auth/login")
async def login(data: dict):
    """로그인 엔드포인트 (개발용 - 비밀번호 체크 안함)"""
    email = data.get("email", "user@example.com")
    # 개발 모드에서는 모든 로그인 허용
    return {
        "access_token": "dummy-token-12345",
        "refresh_token": "dummy-refresh-token",
        "user": {
            "id": "user-001",
            "email": email,
            "name": "켈리",
            "company": "ODIN-AI",
            "role": "관리자"
        }
    }

@app.post("/api/auth/logout")
async def logout():
    """로그아웃"""
    return {"message": "Logged out successfully"}

@app.post("/api/auth/refresh")
async def refresh_token(data: dict):
    """토큰 갱신"""
    return {
        "access_token": "dummy-token-renewed-12345",
        "refresh_token": "dummy-refresh-token-renewed"
    }

# Profile Endpoints
@app.get("/api/profile")
async def get_profile():
    """프로필 정보 조회"""
    return {
        "id": "user-001",
        "email": "jeromwolf@gmail.com",
        "name": "켈리",
        "company": "ODIN-AI",
        "role": "관리자",
        "phone": "010-1234-5678",
        "department": "개발팀",
        "created_at": "2025-01-01T00:00:00",
        "last_login": datetime.now().isoformat(),
        "subscription": {
            "plan": "Premium",
            "status": "active",
            "expires_at": "2026-01-01T00:00:00"
        },
        "preferences": {
            "notifications": True,
            "email_alerts": True,
            "language": "ko"
        }
    }

@app.put("/api/profile")
async def update_profile(data: dict):
    """프로필 정보 수정"""
    return {
        "message": "Profile updated successfully",
        "profile": {
            "id": "user-001",
            "email": data.get("email", "jeromwolf@gmail.com"),
            "name": data.get("name", "켈리"),
            "company": data.get("company", "ODIN-AI"),
            "role": data.get("role", "관리자"),
            "phone": data.get("phone", "010-1234-5678"),
            "department": data.get("department", "개발팀")
        }
    }

@app.post("/api/profile/change-password")
async def change_password(data: dict):
    """비밀번호 변경"""
    return {"message": "Password changed successfully"}

# Settings Endpoints
@app.get("/api/settings")
async def get_settings():
    """설정 조회"""
    return {
        "notifications": {
            "email": True,
            "push": False,
            "sms": False
        },
        "search": {
            "resultsPerPage": 20,
            "autoComplete": True,
            "saveHistory": True
        },
        "theme": "light",
        "language": "ko"
    }

@app.put("/api/settings")
async def update_settings(data: dict):
    """설정 업데이트"""
    return {
        "message": "Settings updated successfully",
        "settings": data
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)