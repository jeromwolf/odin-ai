"""
검색 서비스 모듈
"""

from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
from sqlalchemy import and_, or_, func, text
from sqlalchemy.orm import Session
from loguru import logger

from src.database.models import (
    BidAnnouncement, BidDocument, BidSearchIndex,
    BidTag, BidTagRelation
)


class SearchService:
    """검색 서비스"""

    def __init__(self, db_session: Session):
        self.db_session = db_session

    def search(
        self,
        query: str = None,
        tags: List[str] = None,
        organization: str = None,
        date_from: datetime = None,
        date_to: datetime = None,
        price_min: int = None,
        price_max: int = None,
        contract_method: str = None,
        status: str = 'active',
        page: int = 1,
        page_size: int = 20,
        sort_by: str = 'announcement_date',
        sort_order: str = 'desc'
    ) -> Dict[str, Any]:
        """
        통합 검색
        Returns: 검색 결과와 메타데이터
        """
        # 기본 쿼리
        base_query = self.db_session.query(BidAnnouncement)

        # 상태 필터
        if status:
            base_query = base_query.filter(BidAnnouncement.status == status)

        # 키워드 검색
        if query:
            base_query = self._apply_keyword_search(base_query, query)

        # 태그 검색
        if tags:
            bid_notice_nos = self._search_by_tags(tags)
            if bid_notice_nos:
                base_query = base_query.filter(
                    BidAnnouncement.bid_notice_no.in_(bid_notice_nos)
                )
            else:
                # 태그가 없으면 빈 결과
                return {
                    'results': [],
                    'total': 0,
                    'page': page,
                    'page_size': page_size,
                    'total_pages': 0
                }

        # 기관명 필터
        if organization:
            base_query = base_query.filter(
                BidAnnouncement.organization_name.contains(organization)
            )

        # 날짜 범위 필터
        if date_from:
            base_query = base_query.filter(
                BidAnnouncement.announcement_date >= date_from
            )
        if date_to:
            base_query = base_query.filter(
                BidAnnouncement.announcement_date <= date_to
            )

        # 가격 범위 필터
        if price_min is not None:
            base_query = base_query.filter(
                or_(
                    BidAnnouncement.estimated_price >= price_min,
                    BidAnnouncement.assigned_budget >= price_min
                )
            )
        if price_max is not None:
            base_query = base_query.filter(
                or_(
                    BidAnnouncement.estimated_price <= price_max,
                    BidAnnouncement.assigned_budget <= price_max
                )
            )

        # 계약 방법 필터
        if contract_method:
            base_query = base_query.filter(
                BidAnnouncement.contract_method.contains(contract_method)
            )

        # 전체 건수
        total = base_query.count()

        # 정렬
        if sort_order == 'desc':
            base_query = base_query.order_by(
                getattr(BidAnnouncement, sort_by).desc()
            )
        else:
            base_query = base_query.order_by(
                getattr(BidAnnouncement, sort_by).asc()
            )

        # 페이징
        offset = (page - 1) * page_size
        results = base_query.offset(offset).limit(page_size).all()

        # 결과 포맷팅
        formatted_results = []
        for announcement in results:
            formatted = self._format_announcement(announcement)
            formatted_results.append(formatted)

        # 전체 페이지 수
        total_pages = (total + page_size - 1) // page_size

        return {
            'results': formatted_results,
            'total': total,
            'page': page,
            'page_size': page_size,
            'total_pages': total_pages,
            'query_params': {
                'query': query,
                'tags': tags,
                'organization': organization,
                'date_from': date_from.isoformat() if date_from else None,
                'date_to': date_to.isoformat() if date_to else None,
                'price_min': price_min,
                'price_max': price_max
            }
        }

    def _apply_keyword_search(self, query, keyword: str):
        """키워드 검색 적용"""
        # 여러 필드에서 검색
        search_conditions = [
            BidAnnouncement.title.contains(keyword),
            BidAnnouncement.organization_name.contains(keyword),
        ]

        # 문서 내용에서도 검색 (extracted_text가 있는 경우)
        doc_subquery = self.db_session.query(BidDocument.bid_notice_no).filter(
            BidDocument.extracted_text.contains(keyword)
        ).subquery()

        search_conditions.append(
            BidAnnouncement.bid_notice_no.in_(doc_subquery)
        )

        return query.filter(or_(*search_conditions))

    def _search_by_tags(self, tags: List[str]) -> List[str]:
        """태그로 검색"""
        # 태그 ID 조회
        tag_ids = []
        for tag_name in tags:
            if not tag_name.startswith('#'):
                tag_name = f"#{tag_name}"

            tag = self.db_session.query(BidTag).filter(
                BidTag.tag_name == tag_name
            ).first()
            if tag:
                tag_ids.append(tag.tag_id)

        if not tag_ids:
            return []

        # 모든 태그를 가진 공고 조회 (AND 조건)
        subquery = self.db_session.query(
            BidTagRelation.bid_notice_no
        ).filter(
            BidTagRelation.tag_id.in_(tag_ids)
        ).group_by(
            BidTagRelation.bid_notice_no
        ).having(
            func.count(BidTagRelation.tag_id) == len(tag_ids)
        ).subquery()

        results = self.db_session.query(subquery.c.bid_notice_no).all()
        return [r[0] for r in results]

    def _format_announcement(self, announcement: BidAnnouncement) -> Dict:
        """공고 정보 포맷팅"""
        # 태그 조회
        tags = []
        tag_relations = self.db_session.query(BidTagRelation).filter(
            BidTagRelation.bid_notice_no == announcement.bid_notice_no
        ).all()

        for relation in tag_relations:
            tag = self.db_session.query(BidTag).filter(
                BidTag.tag_id == relation.tag_id
            ).first()
            if tag:
                tags.append(tag.tag_name)

        # 문서 상태 조회
        documents = self.db_session.query(BidDocument).filter(
            BidDocument.bid_notice_no == announcement.bid_notice_no
        ).all()

        doc_stats = {
            'total': len(documents),
            'downloaded': sum(1 for d in documents if d.download_status == 'completed'),
            'processed': sum(1 for d in documents if d.processing_status == 'completed')
        }

        return {
            'bid_notice_no': announcement.bid_notice_no,
            'title': announcement.title,
            'organization_name': announcement.organization_name,
            'announcement_date': announcement.announcement_date.isoformat() if announcement.announcement_date else None,
            'bid_start_date': announcement.bid_start_date.isoformat() if announcement.bid_start_date else None,
            'bid_end_date': announcement.bid_end_date.isoformat() if announcement.bid_end_date else None,
            'opening_date': announcement.opening_date.isoformat() if announcement.opening_date else None,
            'estimated_price': announcement.estimated_price,
            'assigned_budget': announcement.assigned_budget,
            'contract_method': announcement.contract_method,
            'detail_page_url': announcement.detail_page_url,
            'tags': tags,
            'document_stats': doc_stats,
            'is_urgent': self._is_urgent(announcement),
            'days_remaining': self._get_days_remaining(announcement)
        }

    def _is_urgent(self, announcement: BidAnnouncement) -> bool:
        """긴급 공고 여부"""
        if not announcement.bid_end_date:
            return False

        days_remaining = (announcement.bid_end_date - datetime.now()).days
        return days_remaining <= 7

    def _get_days_remaining(self, announcement: BidAnnouncement) -> Optional[int]:
        """마감일까지 남은 일수"""
        if not announcement.bid_end_date:
            return None

        delta = announcement.bid_end_date - datetime.now()
        return delta.days if delta.days >= 0 else 0

    def search_similar(
        self,
        bid_notice_no: str,
        limit: int = 10
    ) -> List[Dict]:
        """유사 공고 검색"""
        # 기준 공고 조회
        base_announcement = self.db_session.query(BidAnnouncement).filter(
            BidAnnouncement.bid_notice_no == bid_notice_no
        ).first()

        if not base_announcement:
            return []

        # 기준 공고의 태그 조회
        base_tags = self.db_session.query(BidTag.tag_id).join(
            BidTagRelation
        ).filter(
            BidTagRelation.bid_notice_no == bid_notice_no
        ).all()

        if not base_tags:
            return []

        base_tag_ids = [t[0] for t in base_tags]

        # 유사 공고 조회 (같은 태그를 많이 가진 순)
        similar_query = self.db_session.query(
            BidAnnouncement,
            func.count(BidTagRelation.tag_id).label('tag_match_count')
        ).join(
            BidTagRelation
        ).filter(
            and_(
                BidTagRelation.tag_id.in_(base_tag_ids),
                BidAnnouncement.bid_notice_no != bid_notice_no,
                BidAnnouncement.status == 'active'
            )
        ).group_by(
            BidAnnouncement.bid_notice_no
        ).order_by(
            func.count(BidTagRelation.tag_id).desc()
        ).limit(limit)

        results = []
        for announcement, match_count in similar_query:
            formatted = self._format_announcement(announcement)
            formatted['similarity_score'] = match_count / len(base_tag_ids)
            results.append(formatted)

        return results

    def get_statistics(self) -> Dict:
        """검색 통계"""
        # 전체 공고 수
        total_announcements = self.db_session.query(
            func.count(BidAnnouncement.bid_notice_no)
        ).scalar()

        # 활성 공고 수
        active_announcements = self.db_session.query(
            func.count(BidAnnouncement.bid_notice_no)
        ).filter(
            BidAnnouncement.status == 'active'
        ).scalar()

        # 오늘 등록된 공고
        today = datetime.now().date()
        today_announcements = self.db_session.query(
            func.count(BidAnnouncement.bid_notice_no)
        ).filter(
            func.date(BidAnnouncement.created_at) == today
        ).scalar()

        # 인기 태그 Top 10
        popular_tags = self.db_session.query(
            BidTag.tag_name,
            BidTag.usage_count
        ).order_by(
            BidTag.usage_count.desc()
        ).limit(10).all()

        # 기관별 공고 수 Top 10
        top_organizations = self.db_session.query(
            BidAnnouncement.organization_name,
            func.count(BidAnnouncement.bid_notice_no).label('count')
        ).group_by(
            BidAnnouncement.organization_name
        ).order_by(
            func.count(BidAnnouncement.bid_notice_no).desc()
        ).limit(10).all()

        return {
            'total_announcements': total_announcements,
            'active_announcements': active_announcements,
            'today_announcements': today_announcements,
            'popular_tags': [
                {'name': tag, 'count': count}
                for tag, count in popular_tags
            ],
            'top_organizations': [
                {'name': org, 'count': count}
                for org, count in top_organizations
            ]
        }

    def create_search_index(self, announcement: BidAnnouncement):
        """검색 인덱스 생성/업데이트"""
        # 기존 인덱스 확인
        existing = self.db_session.query(BidSearchIndex).filter(
            BidSearchIndex.bid_notice_no == announcement.bid_notice_no
        ).first()

        # 문서 내용 조회
        documents = self.db_session.query(BidDocument).filter(
            BidDocument.bid_notice_no == announcement.bid_notice_no,
            BidDocument.processing_status == 'completed'
        ).all()

        # 전체 텍스트 조합
        full_text = f"{announcement.title} {announcement.organization_name}"
        for doc in documents:
            if doc.extracted_text:
                full_text += f" {doc.extracted_text[:1000]}"

        # 카테고리 결정
        industry_category = self._determine_industry(announcement.title)
        region = self._extract_region(announcement.organization_name)
        price_range = self._get_price_range(
            announcement.estimated_price or announcement.assigned_budget
        )

        if existing:
            # 업데이트
            existing.search_title = announcement.title
            existing.search_organization = announcement.organization_name
            existing.search_content = full_text[:5000]
            existing.industry_category = industry_category
            existing.region = region
            existing.price_range = price_range
        else:
            # 새로 생성
            index = BidSearchIndex(
                bid_notice_no=announcement.bid_notice_no,
                search_title=announcement.title,
                search_organization=announcement.organization_name,
                search_content=full_text[:5000],
                industry_category=industry_category,
                region=region,
                price_range=price_range
            )
            self.db_session.add(index)

        try:
            self.db_session.commit()
            logger.info(f"검색 인덱스 생성/업데이트: {announcement.bid_notice_no}")
        except Exception as e:
            self.db_session.rollback()
            logger.error(f"검색 인덱스 생성 실패: {e}")

    def _determine_industry(self, title: str) -> str:
        """산업 분류 결정"""
        industries = {
            '건설': ['건축', '건설', '토목', '시공', '공사'],
            'IT': ['시스템', '소프트웨어', 'SW', '개발', '구축'],
            '의료': ['병원', '의료', '보건', '약품'],
            '교육': ['학교', '교육', '대학']
        }

        for industry, keywords in industries.items():
            for keyword in keywords:
                if keyword in title:
                    return industry

        return '기타'

    def _extract_region(self, org_name: str) -> str:
        """지역 추출"""
        regions = [
            '서울', '부산', '대구', '인천', '광주', '대전',
            '울산', '세종', '경기', '강원', '충북', '충남',
            '전북', '전남', '경북', '경남', '제주'
        ]

        for region in regions:
            if region in org_name:
                return region

        return '전국'

    def _get_price_range(self, price: Optional[int]) -> str:
        """가격 범위"""
        if not price:
            return '미정'

        if price < 100_000_000:
            return '1억미만'
        elif price < 1_000_000_000:
            return '1억-10억'
        elif price < 10_000_000_000:
            return '10억-100억'
        else:
            return '100억이상'