"""
검색 서비스 (최적화 버전)
Full-text search, 인덱스 활용, 캐싱 전략 적용
"""

from typing import Dict, List, Optional, Any, Union, Tuple
from datetime import datetime, timedelta
from enum import Enum
import re
import hashlib
import json
from functools import lru_cache
import asyncio
from concurrent.futures import ThreadPoolExecutor

from sqlalchemy import or_, and_, func, text, select
from sqlalchemy.orm import Session, joinedload, selectinload
from sqlalchemy.sql import Select
from sqlalchemy.dialects.postgresql import TSVECTOR
from loguru import logger
import redis
from redis.exceptions import RedisError

from backend.models.database import SessionLocal
from backend.models.bid_models import (
    BidAnnouncement,
    BidDocument,
    BidExtractedInfo,
    BidTag,
    BidTagRelation
)
from backend.models.user_models import Company


class SearchType(Enum):
    """검색 타입"""
    ALL = "all"
    BID = "bid"
    DOCUMENT = "document"
    COMPANY = "company"


class SortOrder(Enum):
    """정렬 순서"""
    RELEVANCE = "relevance"
    DATE_DESC = "date_desc"
    DATE_ASC = "date_asc"
    PRICE_DESC = "price_desc"
    PRICE_ASC = "price_asc"


class OptimizedSearchService:
    """최적화된 검색 서비스"""

    def __init__(self, db: Optional[Session] = None, redis_client: Optional[redis.Redis] = None):
        """초기화

        Args:
            db: 데이터베이스 세션
            redis_client: Redis 클라이언트 (캐싱용)
        """
        self.db = db or SessionLocal()
        self.redis_client = redis_client or self._init_redis()
        self.executor = ThreadPoolExecutor(max_workers=4)
        self._init_fulltext_search()

    def _init_redis(self) -> Optional[redis.Redis]:
        """Redis 초기화"""
        try:
            client = redis.Redis(
                host='localhost',
                port=6379,
                db=0,
                decode_responses=True,
                socket_keepalive=True,
                socket_keepalive_options={
                    1: 1,  # TCP_KEEPIDLE
                    2: 1,  # TCP_KEEPINTVL
                    3: 5,  # TCP_KEEPCNT
                }
            )
            client.ping()
            logger.info("Redis 연결 성공")
            return client
        except (RedisError, ConnectionError) as e:
            logger.warning(f"Redis 연결 실패, 메모리 캐시만 사용: {e}")
            return None

    def _init_fulltext_search(self):
        """PostgreSQL 전문 검색 초기화"""
        try:
            # 전문 검색 확장 및 한국어 설정
            self.db.execute(text("""
                CREATE EXTENSION IF NOT EXISTS pg_trgm;
                CREATE EXTENSION IF NOT EXISTS unaccent;

                -- 한국어 검색 설정이 없으면 생성
                DO $$
                BEGIN
                    IF NOT EXISTS (
                        SELECT 1 FROM pg_ts_config WHERE cfgname = 'korean_search'
                    ) THEN
                        CREATE TEXT SEARCH CONFIGURATION korean_search (COPY = simple);
                    END IF;
                END$$;
            """))
            self.db.commit()
            logger.info("전문 검색 초기화 완료")
        except Exception as e:
            logger.warning(f"전문 검색 초기화 실패: {e}")
            self.db.rollback()

    def _get_cache_key(self, params: Dict[str, Any]) -> str:
        """캐시 키 생성"""
        # 파라미터를 정렬하여 일관된 키 생성
        sorted_params = json.dumps(params, sort_keys=True, ensure_ascii=False)
        return f"search:{hashlib.md5(sorted_params.encode()).hexdigest()}"

    async def _get_from_cache(self, cache_key: str) -> Optional[Dict]:
        """캐시에서 결과 가져오기"""
        if not self.redis_client:
            return None

        try:
            cached = self.redis_client.get(cache_key)
            if cached:
                logger.debug(f"Cache hit: {cache_key}")
                return json.loads(cached)
        except RedisError as e:
            logger.error(f"Redis get error: {e}")

        return None

    async def _set_cache(self, cache_key: str, data: Dict, ttl: int = 300):
        """결과를 캐시에 저장 (TTL: 5분)"""
        if not self.redis_client:
            return

        try:
            self.redis_client.setex(
                cache_key,
                ttl,
                json.dumps(data, ensure_ascii=False, default=str)
            )
            logger.debug(f"Cache set: {cache_key}")
        except RedisError as e:
            logger.error(f"Redis set error: {e}")

    def _build_tsquery(self, query: str) -> str:
        """PostgreSQL tsquery 생성"""
        # 특수문자 제거 및 토큰화
        tokens = re.findall(r'\w+', query.lower())

        # 각 토큰을 OR로 연결 (더 많은 결과)
        # 또는 AND로 연결 (더 정확한 결과)
        if len(tokens) > 1:
            # 구문 검색과 개별 토큰 검색 조합
            phrase = ' <-> '.join(tokens)  # 인접한 단어
            individual = ' | '.join(tokens)  # 개별 단어
            return f"({phrase}) | ({individual})"
        elif tokens:
            return tokens[0]
        else:
            return ''

    async def search(
        self,
        query: str,
        search_type: SearchType = SearchType.ALL,
        filters: Optional[Dict[str, Any]] = None,
        sort_order: SortOrder = SortOrder.RELEVANCE,
        page: int = 1,
        page_size: int = 20,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """최적화된 통합 검색

        Args:
            query: 검색어
            search_type: 검색 타입
            filters: 필터 조건
            sort_order: 정렬 순서
            page: 페이지 번호
            page_size: 페이지 크기
            use_cache: 캐시 사용 여부

        Returns:
            검색 결과
        """
        # 캐시 키 생성
        cache_params = {
            "query": query,
            "type": search_type.value,
            "filters": filters or {},
            "sort": sort_order.value,
            "page": page,
            "size": page_size
        }
        cache_key = self._get_cache_key(cache_params)

        # 캐시 확인
        if use_cache:
            cached_result = await self._get_from_cache(cache_key)
            if cached_result:
                return cached_result

        # 실제 검색 수행
        try:
            # 병렬 검색 실행
            tasks = []

            if search_type in [SearchType.ALL, SearchType.BID]:
                tasks.append(self._search_bids_optimized(
                    query, filters, sort_order, page, page_size
                ))

            if search_type in [SearchType.ALL, SearchType.DOCUMENT]:
                tasks.append(self._search_documents_optimized(
                    query, filters, sort_order, page, page_size
                ))

            if search_type in [SearchType.ALL, SearchType.COMPANY]:
                tasks.append(self._search_companies_optimized(
                    query, filters, sort_order, page, page_size
                ))

            # 병렬 실행
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # 결과 통합
            combined_results = []
            total_count = 0
            facets = {}

            for result in results:
                if isinstance(result, Exception):
                    logger.error(f"Search task failed: {result}")
                    continue

                if result:
                    combined_results.extend(result.get("results", []))
                    total_count += result.get("count", 0)

                    # 패싯 병합
                    for key, values in result.get("facets", {}).items():
                        if key not in facets:
                            facets[key] = []
                        facets[key].extend(values)

            # 관련도 정렬 (search_type == ALL인 경우)
            if search_type == SearchType.ALL and sort_order == SortOrder.RELEVANCE:
                combined_results.sort(key=lambda x: x.get("score", 0), reverse=True)

            # 페이지네이션
            start_idx = (page - 1) * page_size
            end_idx = start_idx + page_size
            paginated_results = combined_results[start_idx:end_idx]

            response = {
                "query": query,
                "search_type": search_type.value,
                "page": page,
                "page_size": page_size,
                "results": paginated_results,
                "total_count": total_count,
                "facets": facets,
                "page_info": {
                    "current_page": page,
                    "total_pages": (total_count + page_size - 1) // page_size,
                    "has_next": end_idx < total_count,
                    "has_prev": page > 1
                }
            }

            # 캐시 저장
            if use_cache:
                await self._set_cache(cache_key, response)

            return response

        except Exception as e:
            logger.error(f"Search failed: {e}")
            return {
                "query": query,
                "search_type": search_type.value,
                "results": [],
                "total_count": 0,
                "error": str(e)
            }

    async def _search_bids_optimized(
        self,
        query: str,
        filters: Optional[Dict[str, Any]],
        sort_order: SortOrder,
        page: int,
        page_size: int
    ) -> Dict[str, Any]:
        """최적화된 입찰공고 검색"""
        try:
            # 기본 쿼리 구성
            stmt = select(BidAnnouncement)

            # Full-text search 적용
            if query:
                tsquery = self._build_tsquery(query)
                if tsquery:
                    # title과 organization에서 검색
                    stmt = stmt.filter(
                        or_(
                            text(f"to_tsvector('simple', title) @@ to_tsquery('simple', :query)"),
                            text(f"to_tsvector('simple', organization) @@ to_tsquery('simple', :query)")
                        )
                    ).params(query=tsquery)

            # 필터 적용
            if filters:
                stmt = self._apply_filters(stmt, filters, BidAnnouncement)

            # 정렬 적용
            if sort_order == SortOrder.RELEVANCE and query:
                # 관련도 점수 계산
                stmt = stmt.add_columns(
                    func.ts_rank(
                        func.to_tsvector('simple', BidAnnouncement.title),
                        func.to_tsquery('simple', tsquery)
                    ).label('rank')
                ).order_by(text('rank DESC'))
            else:
                stmt = self._apply_sorting(stmt, sort_order, BidAnnouncement)

            # 조인 최적화 - 필요한 관계만 로드
            stmt = stmt.options(
                selectinload(BidAnnouncement.documents),
                selectinload(BidAnnouncement.tags)
            )

            # 전체 카운트 (별도 쿼리)
            count_stmt = select(func.count()).select_from(stmt.subquery())
            total_count = self.db.execute(count_stmt).scalar()

            # 페이지네이션
            stmt = stmt.offset((page - 1) * page_size).limit(page_size)

            # 실행
            results = self.db.execute(stmt).unique().scalars().all()

            # 패싯 정보 수집 (병렬 처리)
            facets = await self._get_facets_async(filters)

            # 결과 포맷팅
            formatted_results = []
            for bid in results:
                formatted_results.append({
                    "id": str(bid.id),
                    "type": "bid",
                    "title": bid.title,
                    "organization": bid.organization,
                    "status": bid.status,
                    "price": float(bid.estimated_price) if bid.estimated_price else None,
                    "deadline": bid.deadline.isoformat() if bid.deadline else None,
                    "announcement_date": bid.announcement_date.isoformat() if bid.announcement_date else None,
                    "bid_notice_no": bid.bid_notice_no,
                    "score": getattr(bid, 'rank', 1.0) if query else 1.0,
                    "tags": [tag.name for tag in bid.tags] if bid.tags else []
                })

            return {
                "results": formatted_results,
                "count": total_count,
                "facets": facets
            }

        except Exception as e:
            logger.error(f"Bid search failed: {e}")
            return {"results": [], "count": 0, "facets": {}}

    async def _search_documents_optimized(
        self,
        query: str,
        filters: Optional[Dict[str, Any]],
        sort_order: SortOrder,
        page: int,
        page_size: int
    ) -> Dict[str, Any]:
        """최적화된 문서 검색"""
        try:
            stmt = select(BidDocument)

            # Full-text search on extracted_text
            if query:
                tsquery = self._build_tsquery(query)
                if tsquery:
                    stmt = stmt.filter(
                        text(f"to_tsvector('simple', extracted_text) @@ to_tsquery('simple', :query)")
                    ).params(query=tsquery)

            # 처리 완료된 문서만
            stmt = stmt.filter(BidDocument.processing_status == 'completed')

            # 필터 적용
            if filters:
                if filters.get('file_type'):
                    stmt = stmt.filter(BidDocument.file_type == filters['file_type'])

            # 정렬
            if sort_order == SortOrder.DATE_DESC:
                stmt = stmt.order_by(BidDocument.created_at.desc())
            elif sort_order == SortOrder.DATE_ASC:
                stmt = stmt.order_by(BidDocument.created_at.asc())

            # 카운트
            count_stmt = select(func.count()).select_from(stmt.subquery())
            total_count = self.db.execute(count_stmt).scalar()

            # 페이지네이션
            stmt = stmt.offset((page - 1) * page_size).limit(page_size)

            # 실행
            results = self.db.execute(stmt).scalars().all()

            # 포맷팅
            formatted_results = []
            for doc in results:
                # 매칭된 텍스트 하이라이트 (간단한 버전)
                highlight = []
                if query and doc.extracted_text:
                    # 검색어 주변 텍스트 추출
                    text_lower = doc.extracted_text.lower()
                    query_lower = query.lower()
                    pos = text_lower.find(query_lower)
                    if pos != -1:
                        start = max(0, pos - 50)
                        end = min(len(doc.extracted_text), pos + len(query) + 50)
                        highlight.append(doc.extracted_text[start:end])

                formatted_results.append({
                    "id": str(doc.id),
                    "type": "document",
                    "title": doc.file_name,
                    "filename": doc.file_name,
                    "file_type": doc.file_type,
                    "size": doc.file_size,
                    "modified": doc.updated_at.isoformat() if doc.updated_at else None,
                    "highlight": highlight,
                    "score": 1.0  # 실제 점수 계산 필요
                })

            return {
                "results": formatted_results,
                "count": total_count,
                "facets": {}
            }

        except Exception as e:
            logger.error(f"Document search failed: {e}")
            return {"results": [], "count": 0, "facets": {}}

    async def _search_companies_optimized(
        self,
        query: str,
        filters: Optional[Dict[str, Any]],
        sort_order: SortOrder,
        page: int,
        page_size: int
    ) -> Dict[str, Any]:
        """최적화된 기업 검색"""
        try:
            stmt = select(Company)

            if query:
                # 기업명, 사업자번호에서 검색
                stmt = stmt.filter(
                    or_(
                        Company.name.ilike(f"%{query}%"),
                        Company.business_number.ilike(f"%{query}%")
                    )
                )

            # 필터
            if filters:
                if filters.get('industry'):
                    stmt = stmt.filter(Company.industry == filters['industry'])
                if filters.get('region'):
                    stmt = stmt.filter(Company.region == filters['region'])

            # 카운트
            total_count = self.db.execute(
                select(func.count()).select_from(stmt.subquery())
            ).scalar()

            # 페이지네이션
            stmt = stmt.offset((page - 1) * page_size).limit(page_size)

            # 실행
            results = self.db.execute(stmt).scalars().all()

            # 포맷팅
            formatted_results = []
            for company in results:
                formatted_results.append({
                    "id": str(company.id),
                    "type": "company",
                    "name": company.name,
                    "business_number": company.business_number,
                    "industry": company.industry,
                    "region": company.region,
                    "score": 1.0
                })

            return {
                "results": formatted_results,
                "count": total_count,
                "facets": {}
            }

        except Exception as e:
            logger.error(f"Company search failed: {e}")
            return {"results": [], "count": 0, "facets": {}}

    def _apply_filters(self, stmt: Select, filters: Dict[str, Any], model) -> Select:
        """필터 조건 적용"""
        if not filters:
            return stmt

        # 날짜 범위
        if filters.get('start_date') and hasattr(model, 'announcement_date'):
            stmt = stmt.filter(model.announcement_date >= filters['start_date'])
        if filters.get('end_date') and hasattr(model, 'announcement_date'):
            stmt = stmt.filter(model.announcement_date <= filters['end_date'])

        # 가격 범위
        if filters.get('min_price') and hasattr(model, 'estimated_price'):
            stmt = stmt.filter(model.estimated_price >= filters['min_price'])
        if filters.get('max_price') and hasattr(model, 'estimated_price'):
            stmt = stmt.filter(model.estimated_price <= filters['max_price'])

        # 기관명
        if filters.get('organization') and hasattr(model, 'organization'):
            stmt = stmt.filter(model.organization == filters['organization'])

        # 상태
        if filters.get('status') and hasattr(model, 'status'):
            stmt = stmt.filter(model.status == filters['status'])

        return stmt

    def _apply_sorting(self, stmt: Select, sort_order: SortOrder, model) -> Select:
        """정렬 조건 적용"""
        if sort_order == SortOrder.DATE_DESC and hasattr(model, 'announcement_date'):
            stmt = stmt.order_by(model.announcement_date.desc())
        elif sort_order == SortOrder.DATE_ASC and hasattr(model, 'announcement_date'):
            stmt = stmt.order_by(model.announcement_date.asc())
        elif sort_order == SortOrder.PRICE_DESC and hasattr(model, 'estimated_price'):
            stmt = stmt.order_by(model.estimated_price.desc())
        elif sort_order == SortOrder.PRICE_ASC and hasattr(model, 'estimated_price'):
            stmt = stmt.order_by(model.estimated_price.asc())

        return stmt

    async def _get_facets_async(self, filters: Optional[Dict[str, Any]] = None) -> Dict[str, List]:
        """비동기로 패싯 정보 수집"""
        try:
            # 패싯 쿼리들을 병렬로 실행
            tasks = [
                self._get_organization_facets(),
                self._get_status_facets(),
                self._get_price_range_facets()
            ]

            results = await asyncio.gather(*tasks, return_exceptions=True)

            facets = {
                "organizations": results[0] if not isinstance(results[0], Exception) else [],
                "statuses": results[1] if not isinstance(results[1], Exception) else [],
                "price_ranges": results[2] if not isinstance(results[2], Exception) else []
            }

            return facets

        except Exception as e:
            logger.error(f"Facet collection failed: {e}")
            return {}

    async def _get_organization_facets(self) -> List[Dict]:
        """기관별 카운트"""
        result = self.db.execute(
            select(
                BidAnnouncement.organization,
                func.count(BidAnnouncement.id).label('count')
            )
            .filter(BidAnnouncement.status.in_(['active', 'pending']))
            .group_by(BidAnnouncement.organization)
            .order_by(text('count DESC'))
            .limit(10)
        ).all()

        return [{"name": org, "count": count} for org, count in result]

    async def _get_status_facets(self) -> List[Dict]:
        """상태별 카운트"""
        result = self.db.execute(
            select(
                BidAnnouncement.status,
                func.count(BidAnnouncement.id).label('count')
            )
            .group_by(BidAnnouncement.status)
        ).all()

        return [{"name": status, "count": count} for status, count in result]

    async def _get_price_range_facets(self) -> List[Dict]:
        """가격 범위별 카운트"""
        ranges = [
            (0, 10000000, "1천만원 미만"),
            (10000000, 50000000, "1천만원 ~ 5천만원"),
            (50000000, 100000000, "5천만원 ~ 1억원"),
            (100000000, 500000000, "1억원 ~ 5억원"),
            (500000000, None, "5억원 이상")
        ]

        facets = []
        for min_val, max_val, label in ranges:
            stmt = select(func.count(BidAnnouncement.id))
            stmt = stmt.filter(BidAnnouncement.estimated_price >= min_val)
            if max_val:
                stmt = stmt.filter(BidAnnouncement.estimated_price < max_val)

            count = self.db.execute(stmt).scalar()
            if count > 0:
                facets.append({"name": label, "count": count})

        return facets

    async def suggest(self, query: str, limit: int = 10) -> List[str]:
        """자동완성 제안 (최적화)"""
        cache_key = f"suggest:{query}:{limit}"

        # 캐시 확인
        if self.redis_client:
            try:
                cached = self.redis_client.get(cache_key)
                if cached:
                    return json.loads(cached)
            except RedisError:
                pass

        # DB에서 제안 가져오기
        suggestions = []

        try:
            # 제목에서 매칭되는 것 찾기
            stmt = select(BidAnnouncement.title).filter(
                BidAnnouncement.title.ilike(f"{query}%")
            ).limit(limit)

            results = self.db.execute(stmt).scalars().all()

            # 중복 제거 및 정렬
            seen = set()
            for title in results:
                # 제목을 단순화 (50자로 제한)
                simplified = title[:50]
                if simplified not in seen:
                    suggestions.append(simplified)
                    seen.add(simplified)

            # 캐시 저장
            if self.redis_client and suggestions:
                try:
                    self.redis_client.setex(
                        cache_key,
                        60,  # 1분 TTL
                        json.dumps(suggestions, ensure_ascii=False)
                    )
                except RedisError:
                    pass

            return suggestions[:limit]

        except Exception as e:
            logger.error(f"Suggest failed: {e}")
            return []

    def close(self):
        """리소스 정리"""
        if self.executor:
            self.executor.shutdown(wait=True)
        if self.db:
            self.db.close()
        if self.redis_client:
            self.redis_client.close()