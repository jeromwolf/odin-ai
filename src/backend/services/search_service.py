"""
검색 서비스
입찰공고와 문서를 검색하는 통합 검색 시스템
"""

from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
from enum import Enum
import re
from pathlib import Path
import json

from sqlalchemy import or_, and_, func, text
from sqlalchemy.orm import Session
from loguru import logger

from backend.models.database import SessionLocal
from backend.models.bid_models import BidAnnouncement, BidDocument
from backend.models.user_models import Company


class SearchType(Enum):
    """검색 타입"""
    ALL = "all"  # 전체 검색
    BID = "bid"  # 입찰공고만
    DOCUMENT = "document"  # 문서만
    COMPANY = "company"  # 기업 정보


class SortOrder(Enum):
    """정렬 순서"""
    RELEVANCE = "relevance"  # 관련도순
    DATE_DESC = "date_desc"  # 최신순
    DATE_ASC = "date_asc"  # 오래된순
    PRICE_DESC = "price_desc"  # 가격 높은순
    PRICE_ASC = "price_asc"  # 가격 낮은순


class SearchService:
    """검색 서비스"""

    def __init__(self, db: Optional[Session] = None):
        """초기화"""
        self.db = db or SessionLocal()
        self._init_fulltext_search()

    def _init_fulltext_search(self):
        """PostgreSQL 전문 검색 초기화"""
        try:
            # 한국어 검색을 위한 설정
            self.db.execute(text("""
                CREATE EXTENSION IF NOT EXISTS pg_trgm;
                CREATE EXTENSION IF NOT EXISTS unaccent;
            """))
            self.db.commit()
            logger.info("전문 검색 확장 초기화 완료")
        except Exception as e:
            logger.warning(f"전문 검색 확장 초기화 실패 (이미 존재할 수 있음): {e}")
            self.db.rollback()

    async def search(
        self,
        query: str,
        search_type: SearchType = SearchType.ALL,
        filters: Optional[Dict[str, Any]] = None,
        sort_order: SortOrder = SortOrder.RELEVANCE,
        page: int = 1,
        page_size: int = 20
    ) -> Dict[str, Any]:
        """통합 검색

        Args:
            query: 검색어
            search_type: 검색 타입
            filters: 추가 필터 조건
            sort_order: 정렬 순서
            page: 페이지 번호
            page_size: 페이지 크기

        Returns:
            검색 결과
        """
        try:
            results = {
                "query": query,
                "search_type": search_type.value,
                "page": page,
                "page_size": page_size,
                "results": [],
                "total_count": 0,
                "facets": {}
            }

            # 검색어 전처리
            processed_query = self._process_query(query)

            # 검색 타입별 처리
            if search_type == SearchType.BID or search_type == SearchType.ALL:
                bid_results = await self._search_bids(
                    processed_query, filters, sort_order, page, page_size
                )
                results["bid_results"] = bid_results
                results["total_count"] += bid_results.get("total", 0)

            if search_type == SearchType.DOCUMENT or search_type == SearchType.ALL:
                doc_results = await self._search_documents(
                    processed_query, filters, sort_order, page, page_size
                )
                results["document_results"] = doc_results
                results["total_count"] += doc_results.get("total", 0)

            if search_type == SearchType.COMPANY or search_type == SearchType.ALL:
                company_results = await self._search_companies(
                    processed_query, filters, page, page_size
                )
                results["company_results"] = company_results
                results["total_count"] += company_results.get("total", 0)

            # 통합 결과 생성
            if search_type == SearchType.ALL:
                results["results"] = self._merge_results(
                    bid_results.get("items", []),
                    doc_results.get("items", []),
                    company_results.get("items", [])
                )[:page_size]

            # 패싯 정보 추가
            results["facets"] = await self._generate_facets(processed_query, filters)

            return results

        except Exception as e:
            logger.error(f"검색 실패: {e}")
            return {
                "error": str(e),
                "query": query,
                "results": [],
                "total_count": 0
            }

    async def _search_bids(
        self,
        query: str,
        filters: Optional[Dict[str, Any]],
        sort_order: SortOrder,
        page: int,
        page_size: int
    ) -> Dict[str, Any]:
        """입찰공고 검색"""
        try:
            # 기본 쿼리
            db_query = self.db.query(BidAnnouncement)

            # 텍스트 검색
            if query:
                # PostgreSQL 전문 검색 사용
                search_conditions = or_(
                    BidAnnouncement.bid_notice_name.ilike(f"%{query}%"),
                    BidAnnouncement.notice_inst_name.ilike(f"%{query}%"),
                    BidAnnouncement.demand_inst_name.ilike(f"%{query}%"),
                    BidAnnouncement.industry_type.ilike(f"%{query}%")
                )
                db_query = db_query.filter(search_conditions)

            # 필터 적용
            if filters:
                db_query = self._apply_bid_filters(db_query, filters)

            # 정렬 적용
            db_query = self._apply_sort_order(db_query, sort_order)

            # 전체 카운트
            total_count = db_query.count()

            # 페이지네이션
            offset = (page - 1) * page_size
            items = db_query.offset(offset).limit(page_size).all()

            # 결과 포맷팅
            results = []
            for item in items:
                result = {
                    "type": "bid",
                    "id": item.id,
                    "bid_notice_no": item.bid_notice_no,
                    "title": item.bid_notice_name,
                    "organization": item.notice_inst_name,
                    "price": item.presumpt_price,
                    "deadline": item.bid_close_date.isoformat() if item.bid_close_date else None,
                    "status": item.bid_status,
                    "score": self._calculate_relevance_score(query, item) if query else 1.0,
                    "highlight": self._generate_highlight(query, item.bid_notice_name) if query else None
                }
                results.append(result)

            return {
                "items": results,
                "total": total_count,
                "page": page,
                "pages": (total_count + page_size - 1) // page_size
            }

        except Exception as e:
            logger.error(f"입찰공고 검색 실패: {e}")
            return {"items": [], "total": 0}

    async def _search_documents(
        self,
        query: str,
        filters: Optional[Dict[str, Any]],
        sort_order: SortOrder,
        page: int,
        page_size: int
    ) -> Dict[str, Any]:
        """문서 검색 (MD 파일)"""
        try:
            results = []

            # 문서 디렉토리 검색
            doc_dirs = [
                Path("storage/processed/hwp"),
                Path("storage/processed/pdf"),
                Path("storage/processed/doc")
            ]

            all_docs = []
            for doc_dir in doc_dirs:
                if doc_dir.exists():
                    for md_file in doc_dir.glob("*.md"):
                        try:
                            with open(md_file, 'r', encoding='utf-8') as f:
                                content = f.read()

                            # 검색어 매칭
                            if query and query.lower() in content.lower():
                                score = content.lower().count(query.lower())

                                # 메타데이터 추출
                                metadata = self._extract_metadata(content)

                                all_docs.append({
                                    "type": "document",
                                    "filename": md_file.name,
                                    "path": str(md_file),
                                    "file_type": doc_dir.name,
                                    "score": score,
                                    "size": md_file.stat().st_size,
                                    "modified": datetime.fromtimestamp(md_file.stat().st_mtime).isoformat(),
                                    "title": metadata.get("title", md_file.stem),
                                    "highlight": self._generate_text_highlight(query, content),
                                    "metadata": metadata
                                })
                        except Exception as e:
                            logger.warning(f"문서 읽기 실패 {md_file}: {e}")
                            continue

            # 정렬
            if sort_order == SortOrder.RELEVANCE:
                all_docs.sort(key=lambda x: x["score"], reverse=True)
            elif sort_order == SortOrder.DATE_DESC:
                all_docs.sort(key=lambda x: x["modified"], reverse=True)
            elif sort_order == SortOrder.DATE_ASC:
                all_docs.sort(key=lambda x: x["modified"])

            # 페이지네이션
            total = len(all_docs)
            start_idx = (page - 1) * page_size
            end_idx = start_idx + page_size
            results = all_docs[start_idx:end_idx]

            return {
                "items": results,
                "total": total,
                "page": page,
                "pages": (total + page_size - 1) // page_size
            }

        except Exception as e:
            logger.error(f"문서 검색 실패: {e}")
            return {"items": [], "total": 0}

    async def _search_companies(
        self,
        query: str,
        filters: Optional[Dict[str, Any]],
        page: int,
        page_size: int
    ) -> Dict[str, Any]:
        """기업 정보 검색"""
        try:
            # 기본 쿼리
            db_query = self.db.query(Company)

            # 텍스트 검색
            if query:
                search_conditions = or_(
                    Company.name.ilike(f"%{query}%"),
                    Company.business_number.ilike(f"%{query}%"),
                    Company.industry.ilike(f"%{query}%")
                )
                db_query = db_query.filter(search_conditions)

            # 필터 적용
            if filters:
                if filters.get("industry"):
                    db_query = db_query.filter(Company.industry == filters["industry"])
                if filters.get("region"):
                    db_query = db_query.filter(Company.region.ilike(f"%{filters['region']}%"))

            # 전체 카운트
            total_count = db_query.count()

            # 페이지네이션
            offset = (page - 1) * page_size
            items = db_query.offset(offset).limit(page_size).all()

            # 결과 포맷팅
            results = []
            for item in items:
                result = {
                    "type": "company",
                    "id": item.id,
                    "name": item.name,
                    "business_number": item.business_number,
                    "industry": item.industry,
                    "region": item.region,
                    "created_at": item.created_at.isoformat() if item.created_at else None
                }
                results.append(result)

            return {
                "items": results,
                "total": total_count,
                "page": page,
                "pages": (total_count + page_size - 1) // page_size
            }

        except Exception as e:
            logger.error(f"기업 검색 실패: {e}")
            return {"items": [], "total": 0}

    def _process_query(self, query: str) -> str:
        """검색어 전처리"""
        if not query:
            return ""

        # 특수문자 제거 (검색에 필요한 것만 남김)
        query = re.sub(r'[^\w\s\-\.]', ' ', query)

        # 연속된 공백 제거
        query = ' '.join(query.split())

        return query.strip()

    def _apply_bid_filters(self, query, filters: Dict[str, Any]):
        """입찰공고 필터 적용"""
        # 날짜 필터
        if filters.get("start_date"):
            query = query.filter(BidAnnouncement.bid_notice_date >= filters["start_date"])
        if filters.get("end_date"):
            query = query.filter(BidAnnouncement.bid_notice_date <= filters["end_date"])

        # 가격 필터
        if filters.get("min_price"):
            query = query.filter(BidAnnouncement.presumpt_price >= filters["min_price"])
        if filters.get("max_price"):
            query = query.filter(BidAnnouncement.presumpt_price <= filters["max_price"])

        # 기관 필터
        if filters.get("organization"):
            query = query.filter(
                BidAnnouncement.notice_inst_name.ilike(f"%{filters['organization']}%")
            )

        # 상태 필터
        if filters.get("status"):
            query = query.filter(BidAnnouncement.bid_status == filters["status"])

        # 산업 분야 필터
        if filters.get("industry"):
            query = query.filter(
                BidAnnouncement.industry_type.ilike(f"%{filters['industry']}%")
            )

        return query

    def _apply_sort_order(self, query, sort_order: SortOrder):
        """정렬 순서 적용"""
        if sort_order == SortOrder.DATE_DESC:
            return query.order_by(BidAnnouncement.bid_notice_date.desc())
        elif sort_order == SortOrder.DATE_ASC:
            return query.order_by(BidAnnouncement.bid_notice_date.asc())
        elif sort_order == SortOrder.PRICE_DESC:
            return query.order_by(BidAnnouncement.presumpt_price.desc().nullslast())
        elif sort_order == SortOrder.PRICE_ASC:
            return query.order_by(BidAnnouncement.presumpt_price.asc().nullsfirst())
        else:
            # 관련도순 (기본)
            return query.order_by(BidAnnouncement.bid_notice_date.desc())

    def _calculate_relevance_score(self, query: str, item: BidAnnouncement) -> float:
        """관련도 점수 계산"""
        if not query:
            return 1.0

        score = 0.0
        query_lower = query.lower()

        # 제목 매칭 (가중치 높음)
        if item.bid_notice_name and query_lower in item.bid_notice_name.lower():
            score += 10.0 * item.bid_notice_name.lower().count(query_lower)

        # 기관명 매칭
        if item.notice_inst_name and query_lower in item.notice_inst_name.lower():
            score += 5.0 * item.notice_inst_name.lower().count(query_lower)

        # 산업 분야 매칭
        if item.industry_type and query_lower in item.industry_type.lower():
            score += 3.0 * item.industry_type.lower().count(query_lower)

        return min(score, 100.0)  # 최대 100점

    def _generate_highlight(self, query: str, text: str, max_length: int = 200) -> str:
        """검색어 하이라이트 생성"""
        if not query or not text:
            return text[:max_length] if text else ""

        # 검색어 위치 찾기
        pos = text.lower().find(query.lower())
        if pos == -1:
            return text[:max_length]

        # 전후 문맥 포함
        start = max(0, pos - 50)
        end = min(len(text), pos + len(query) + 150)

        highlighted = text[start:end]

        # 검색어 강조 (마크다운 형식)
        highlighted = highlighted.replace(
            query, f"**{query}**", 1
        )

        if start > 0:
            highlighted = "..." + highlighted
        if end < len(text):
            highlighted = highlighted + "..."

        return highlighted

    def _generate_text_highlight(self, query: str, content: str, context_size: int = 100) -> List[str]:
        """텍스트 하이라이트 생성 (여러 매칭 부분)"""
        if not query or not content:
            return []

        highlights = []
        query_lower = query.lower()
        content_lower = content.lower()

        # 모든 매칭 위치 찾기
        start = 0
        while True:
            pos = content_lower.find(query_lower, start)
            if pos == -1:
                break

            # 전후 문맥 추출
            context_start = max(0, pos - context_size)
            context_end = min(len(content), pos + len(query) + context_size)

            highlight = content[context_start:context_end]

            # 검색어 강조
            highlight = highlight.replace(
                content[pos:pos+len(query)],
                f"**{content[pos:pos+len(query)]}**"
            )

            if context_start > 0:
                highlight = "..." + highlight
            if context_end < len(content):
                highlight = highlight + "..."

            highlights.append(highlight)

            start = pos + len(query)

            # 최대 3개까지만
            if len(highlights) >= 3:
                break

        return highlights

    def _extract_metadata(self, content: str) -> Dict[str, Any]:
        """마크다운 파일에서 메타데이터 추출"""
        metadata = {}

        # 제목 추출 (첫 번째 # 헤더)
        title_match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
        if title_match:
            metadata["title"] = title_match.group(1)

        # 날짜 패턴 추출
        date_patterns = [
            r'(\d{4}[-/.]\d{1,2}[-/.]\d{1,2})',
            r'(\d{4}년\s*\d{1,2}월\s*\d{1,2}일)'
        ]

        for pattern in date_patterns:
            date_match = re.search(pattern, content)
            if date_match:
                metadata["date"] = date_match.group(1)
                break

        # 금액 패턴 추출
        price_pattern = r'(\d{1,3}(?:,\d{3})*(?:\.\d+)?)\s*(?:원|천원|백만원|억원)'
        price_match = re.search(price_pattern, content)
        if price_match:
            metadata["price"] = price_match.group(0)

        return metadata

    def _merge_results(self, bids: List, docs: List, companies: List) -> List[Dict]:
        """검색 결과 통합"""
        all_results = []

        # 각 타입별로 상위 결과 추가
        all_results.extend(bids[:5])
        all_results.extend(docs[:5])
        all_results.extend(companies[:5])

        # 점수 기준 정렬
        all_results.sort(key=lambda x: x.get("score", 0), reverse=True)

        return all_results

    async def _generate_facets(self, query: str, filters: Optional[Dict]) -> Dict[str, Any]:
        """패싯 정보 생성 (필터 옵션)"""
        facets = {}

        try:
            # 기관별 카운트
            org_counts = self.db.query(
                BidAnnouncement.notice_inst_name,
                func.count(BidAnnouncement.id).label('count')
            ).group_by(
                BidAnnouncement.notice_inst_name
            ).order_by(
                func.count(BidAnnouncement.id).desc()
            ).limit(10).all()

            facets["organizations"] = [
                {"name": org, "count": count}
                for org, count in org_counts if org
            ]

            # 상태별 카운트
            status_counts = self.db.query(
                BidAnnouncement.bid_status,
                func.count(BidAnnouncement.id).label('count')
            ).group_by(
                BidAnnouncement.bid_status
            ).all()

            facets["status"] = [
                {"name": status, "count": count}
                for status, count in status_counts if status
            ]

            # 가격 범위
            price_ranges = [
                ("1천만원 미만", 0, 10000000),
                ("1천만원 ~ 5천만원", 10000000, 50000000),
                ("5천만원 ~ 1억원", 50000000, 100000000),
                ("1억원 ~ 5억원", 100000000, 500000000),
                ("5억원 이상", 500000000, None)
            ]

            price_facets = []
            for label, min_price, max_price in price_ranges:
                query = self.db.query(func.count(BidAnnouncement.id))
                if min_price is not None:
                    query = query.filter(BidAnnouncement.presumpt_price >= min_price)
                if max_price is not None:
                    query = query.filter(BidAnnouncement.presumpt_price < max_price)

                count = query.scalar()
                if count > 0:
                    price_facets.append({"range": label, "count": count})

            facets["price_ranges"] = price_facets

        except Exception as e:
            logger.error(f"패싯 생성 실패: {e}")

        return facets

    async def suggest(self, query: str, max_suggestions: int = 10) -> List[str]:
        """검색어 자동완성"""
        suggestions = []

        try:
            # 입찰공고 제목에서 제안
            bid_suggestions = self.db.query(BidAnnouncement.bid_notice_name).filter(
                BidAnnouncement.bid_notice_name.ilike(f"{query}%")
            ).distinct().limit(max_suggestions).all()

            for (title,) in bid_suggestions:
                if title:
                    # 검색어와 유사한 부분 추출
                    words = title.split()
                    for word in words:
                        if word.lower().startswith(query.lower()):
                            suggestions.append(word)
                            if len(suggestions) >= max_suggestions:
                                break

            # 중복 제거 및 정렬
            suggestions = list(set(suggestions))[:max_suggestions]
            suggestions.sort()

        except Exception as e:
            logger.error(f"자동완성 생성 실패: {e}")

        return suggestions

    def close(self):
        """데이터베이스 연결 종료"""
        if self.db:
            self.db.close()