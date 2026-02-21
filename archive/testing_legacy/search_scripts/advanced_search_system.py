#!/usr/bin/env python
"""
Phase 5: 고급 검색 시스템 구현
공고 데이터에 대한 복합 조건 검색 및 필터링 API
"""

import sys
from pathlib import Path
import time
from typing import Dict, List, Optional, Union, Tuple
from datetime import datetime, timedelta
from decimal import Decimal

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, str(Path.cwd() / 'src'))

from sqlalchemy import create_engine, text, and_, or_, func
from sqlalchemy.orm import sessionmaker
from src.database.models import BidAnnouncement, BidExtractedInfo, BidDocument

class AdvancedSearchSystem:
    """고급 검색 시스템"""

    def __init__(self, database_url: str = "postgresql://blockmeta@localhost:5432/odin_db"):
        self.engine = create_engine(database_url)
        Session = sessionmaker(bind=self.engine)
        self.session = Session()

    def search_by_price_range(self,
                             min_price: Optional[int] = None,
                             max_price: Optional[int] = None,
                             limit: int = 50) -> Dict:
        """금액 범위로 공고 검색"""

        print(f"💰 금액 범위 검색: {min_price:,}원 ~ {max_price:,}원")

        start_time = time.time()

        query = self.session.query(BidAnnouncement)

        # 기본 금액 필터
        if min_price is not None:
            query = query.filter(BidAnnouncement.estimated_price >= min_price)
        if max_price is not None:
            query = query.filter(BidAnnouncement.estimated_price <= max_price)

        # 추출된 정보에서도 검색
        extracted_query = self.session.query(BidExtractedInfo).filter(
            BidExtractedInfo.info_category == 'prices'
        )

        results = query.limit(limit).all()

        # 추출된 가격 정보도 함께 조회
        enhanced_results = []
        for announcement in results:
            extracted_prices = self.session.query(BidExtractedInfo).filter(
                BidExtractedInfo.bid_notice_no == announcement.bid_notice_no,
                BidExtractedInfo.info_category == 'prices'
            ).all()

            enhanced_results.append({
                'announcement': announcement,
                'extracted_prices': {info.field_name: info.field_value for info in extracted_prices}
            })

        processing_time = time.time() - start_time

        return {
            'results': enhanced_results,
            'count': len(enhanced_results),
            'processing_time': processing_time,
            'query_type': 'price_range'
        }

    def search_by_deadline(self, days_ahead: int = 7, limit: int = 50) -> Dict:
        """마감일 기준 검색 (N일 내 마감)"""

        print(f"📅 마감일 검색: {days_ahead}일 내 마감")

        start_time = time.time()

        target_date = datetime.now() + timedelta(days=days_ahead)

        query = self.session.query(BidAnnouncement).filter(
            and_(
                BidAnnouncement.bid_end_date <= target_date,
                BidAnnouncement.bid_end_date >= datetime.now()
            )
        ).order_by(BidAnnouncement.bid_end_date)

        results = query.limit(limit).all()

        # 각 공고별 추출된 일정 정보 추가
        enhanced_results = []
        for announcement in results:
            extracted_dates = self.session.query(BidExtractedInfo).filter(
                BidExtractedInfo.bid_notice_no == announcement.bid_notice_no,
                BidExtractedInfo.info_category == 'dates'
            ).all()

            days_left = (announcement.bid_end_date - datetime.now()).days if announcement.bid_end_date else None

            enhanced_results.append({
                'announcement': announcement,
                'days_left': days_left,
                'extracted_dates': {info.field_name: info.field_value for info in extracted_dates}
            })

        processing_time = time.time() - start_time

        return {
            'results': enhanced_results,
            'count': len(enhanced_results),
            'processing_time': processing_time,
            'query_type': 'deadline'
        }

    def search_by_industry(self, industry_keywords: List[str], limit: int = 50) -> Dict:
        """업종별 검색"""

        print(f"🏢 업종별 검색: {', '.join(industry_keywords)}")

        start_time = time.time()

        # 제목에서 업종 키워드 검색
        title_conditions = []
        for keyword in industry_keywords:
            title_conditions.append(BidAnnouncement.title.ilike(f'%{keyword}%'))

        query = self.session.query(BidAnnouncement).filter(
            or_(*title_conditions)
        )

        results = query.limit(limit).all()

        # 추출된 계약 정보도 함께 조회
        enhanced_results = []
        for announcement in results:
            extracted_contract = self.session.query(BidExtractedInfo).filter(
                BidExtractedInfo.bid_notice_no == announcement.bid_notice_no,
                BidExtractedInfo.info_category == 'contract_details'
            ).all()

            # 매칭된 키워드 찾기
            matched_keywords = []
            for keyword in industry_keywords:
                if keyword in announcement.title:
                    matched_keywords.append(keyword)

            enhanced_results.append({
                'announcement': announcement,
                'matched_keywords': matched_keywords,
                'extracted_contract': {info.field_name: info.field_value for info in extracted_contract}
            })

        processing_time = time.time() - start_time

        return {
            'results': enhanced_results,
            'count': len(enhanced_results),
            'processing_time': processing_time,
            'query_type': 'industry'
        }

    def search_by_region(self, region_keywords: List[str], limit: int = 50) -> Dict:
        """지역별 검색"""

        print(f"📍 지역별 검색: {', '.join(region_keywords)}")

        start_time = time.time()

        # 기관명과 제목에서 지역 키워드 검색
        region_conditions = []
        for keyword in region_keywords:
            region_conditions.extend([
                BidAnnouncement.organization_name.ilike(f'%{keyword}%'),
                BidAnnouncement.title.ilike(f'%{keyword}%')
            ])

        query = self.session.query(BidAnnouncement).filter(
            or_(*region_conditions)
        )

        results = query.limit(limit).all()

        enhanced_results = []
        for announcement in results:
            # 매칭된 지역 키워드 찾기
            matched_regions = []
            for keyword in region_keywords:
                if (keyword in (announcement.organization_name or '') or
                    keyword in (announcement.title or '')):
                    matched_regions.append(keyword)

            enhanced_results.append({
                'announcement': announcement,
                'matched_regions': matched_regions
            })

        processing_time = time.time() - start_time

        return {
            'results': enhanced_results,
            'count': len(enhanced_results),
            'processing_time': processing_time,
            'query_type': 'region'
        }

    def complex_search(self,
                      min_price: Optional[int] = None,
                      max_price: Optional[int] = None,
                      days_ahead: Optional[int] = None,
                      industry_keywords: Optional[List[str]] = None,
                      region_keywords: Optional[List[str]] = None,
                      sort_by: str = 'bid_end_date',
                      sort_order: str = 'asc',
                      limit: int = 50) -> Dict:
        """복합 조건 검색"""

        print(f"🔍 복합 조건 검색")
        print(f"  - 금액: {min_price:,}원 ~ {max_price:,}원" if min_price or max_price else "  - 금액: 제한 없음")
        print(f"  - 마감: {days_ahead}일 내" if days_ahead else "  - 마감: 제한 없음")
        print(f"  - 업종: {', '.join(industry_keywords)}" if industry_keywords else "  - 업종: 제한 없음")
        print(f"  - 지역: {', '.join(region_keywords)}" if region_keywords else "  - 지역: 제한 없음")

        start_time = time.time()

        # 기본 쿼리
        query = self.session.query(BidAnnouncement)
        conditions = []

        # 금액 조건
        if min_price is not None:
            conditions.append(BidAnnouncement.estimated_price >= min_price)
        if max_price is not None:
            conditions.append(BidAnnouncement.estimated_price <= max_price)

        # 마감일 조건
        if days_ahead is not None:
            target_date = datetime.now() + timedelta(days=days_ahead)
            conditions.extend([
                BidAnnouncement.bid_end_date <= target_date,
                BidAnnouncement.bid_end_date >= datetime.now()
            ])

        # 업종 조건
        if industry_keywords:
            industry_conditions = []
            for keyword in industry_keywords:
                industry_conditions.append(BidAnnouncement.title.ilike(f'%{keyword}%'))
            conditions.append(or_(*industry_conditions))

        # 지역 조건
        if region_keywords:
            region_conditions = []
            for keyword in region_keywords:
                region_conditions.extend([
                    BidAnnouncement.organization_name.ilike(f'%{keyword}%'),
                    BidAnnouncement.title.ilike(f'%{keyword}%')
                ])
            conditions.append(or_(*region_conditions))

        # 모든 조건 적용
        if conditions:
            query = query.filter(and_(*conditions))

        # 정렬
        if sort_by == 'bid_end_date':
            if sort_order == 'desc':
                query = query.order_by(BidAnnouncement.bid_end_date.desc())
            else:
                query = query.order_by(BidAnnouncement.bid_end_date.asc())
        elif sort_by == 'estimated_price':
            if sort_order == 'desc':
                query = query.order_by(BidAnnouncement.estimated_price.desc())
            else:
                query = query.order_by(BidAnnouncement.estimated_price.asc())
        elif sort_by == 'announcement_date':
            if sort_order == 'desc':
                query = query.order_by(BidAnnouncement.announcement_date.desc())
            else:
                query = query.order_by(BidAnnouncement.announcement_date.asc())

        results = query.limit(limit).all()

        # 결과 강화 (추출된 정보 포함)
        enhanced_results = []
        for announcement in results:
            # 추출된 모든 정보 조회
            extracted_info = self.session.query(BidExtractedInfo).filter(
                BidExtractedInfo.bid_notice_no == announcement.bid_notice_no
            ).all()

            # 카테고리별로 정리
            extracted_data = {}
            for info in extracted_info:
                if info.info_category not in extracted_data:
                    extracted_data[info.info_category] = {}
                extracted_data[info.info_category][info.field_name] = info.field_value

            # 매칭 정보
            matched_info = {}
            if industry_keywords:
                matched_info['industries'] = [kw for kw in industry_keywords if kw in announcement.title]
            if region_keywords:
                matched_info['regions'] = [kw for kw in region_keywords
                                         if kw in (announcement.organization_name or '') or
                                            kw in (announcement.title or '')]

            enhanced_results.append({
                'announcement': announcement,
                'extracted_data': extracted_data,
                'matched_info': matched_info,
                'days_left': (announcement.bid_end_date - datetime.now()).days if announcement.bid_end_date else None
            })

        processing_time = time.time() - start_time

        return {
            'results': enhanced_results,
            'count': len(enhanced_results),
            'total_conditions': len(conditions),
            'processing_time': processing_time,
            'query_type': 'complex',
            'sort': f"{sort_by}_{sort_order}"
        }

    def get_search_statistics(self) -> Dict:
        """검색 통계 정보"""

        start_time = time.time()

        with self.engine.connect() as conn:
            # 기본 통계
            total_announcements = conn.execute(text("SELECT COUNT(*) FROM bid_announcements")).scalar()
            total_documents = conn.execute(text("SELECT COUNT(*) FROM bid_documents")).scalar()
            total_extracted = conn.execute(text("SELECT COUNT(*) FROM bid_extracted_info")).scalar()

            # 금액 통계
            price_stats = conn.execute(text("""
                SELECT
                    MIN(estimated_price) as min_price,
                    MAX(estimated_price) as max_price,
                    AVG(estimated_price) as avg_price,
                    COUNT(*) as price_count
                FROM bid_announcements
                WHERE estimated_price IS NOT NULL AND estimated_price > 0
            """)).first()

            # 마감일 통계
            deadline_stats = conn.execute(text("""
                SELECT
                    COUNT(*) as active_count,
                    COUNT(CASE WHEN bid_end_date <= CURRENT_DATE + INTERVAL '7 days' THEN 1 END) as week_deadline,
                    COUNT(CASE WHEN bid_end_date <= CURRENT_DATE + INTERVAL '30 days' THEN 1 END) as month_deadline
                FROM bid_announcements
                WHERE bid_end_date >= CURRENT_DATE
            """)).first()

            # 카테고리별 추출 정보
            category_stats = conn.execute(text("""
                SELECT info_category, COUNT(*) as count
                FROM bid_extracted_info
                GROUP BY info_category
                ORDER BY count DESC
            """)).fetchall()

            # 인기 키워드 (제목에서)
            popular_keywords = conn.execute(text("""
                WITH title_words AS (
                    SELECT unnest(string_to_array(title, ' ')) as word
                    FROM bid_announcements
                    WHERE title IS NOT NULL
                )
                SELECT word, COUNT(*) as frequency
                FROM title_words
                WHERE length(word) >= 2
                GROUP BY word
                ORDER BY frequency DESC
                LIMIT 20
            """)).fetchall()

        processing_time = time.time() - start_time

        return {
            'basic_stats': {
                'total_announcements': total_announcements,
                'total_documents': total_documents,
                'total_extracted_info': total_extracted
            },
            'price_stats': {
                'min_price': price_stats[0] if price_stats[0] else 0,
                'max_price': price_stats[1] if price_stats[1] else 0,
                'avg_price': int(price_stats[2]) if price_stats[2] else 0,
                'price_count': price_stats[3]
            },
            'deadline_stats': {
                'active_count': deadline_stats[0],
                'week_deadline': deadline_stats[1],
                'month_deadline': deadline_stats[2]
            },
            'category_distribution': [{'category': row[0], 'count': row[1]} for row in category_stats],
            'popular_keywords': [{'word': row[0], 'frequency': row[1]} for row in popular_keywords],
            'processing_time': processing_time
        }

    def create_search_indexes(self):
        """검색 최적화를 위한 인덱스 생성"""

        print("🔧 검색 최적화 인덱스 생성 중...")

        indexes = [
            # 금액 범위 검색 인덱스
            "CREATE INDEX IF NOT EXISTS idx_estimated_price_range ON bid_announcements(estimated_price) WHERE estimated_price IS NOT NULL",

            # 날짜 기반 검색 인덱스
            "CREATE INDEX IF NOT EXISTS idx_bid_end_date_active ON bid_announcements(bid_end_date) WHERE bid_end_date >= CURRENT_DATE",
            "CREATE INDEX IF NOT EXISTS idx_announcement_date ON bid_announcements(announcement_date)",

            # 텍스트 검색 인덱스
            "CREATE INDEX IF NOT EXISTS idx_title_gin ON bid_announcements USING gin(to_tsvector('korean', title))",
            "CREATE INDEX IF NOT EXISTS idx_organization_gin ON bid_announcements USING gin(to_tsvector('korean', organization_name))",

            # 복합 인덱스
            "CREATE INDEX IF NOT EXISTS idx_price_deadline ON bid_announcements(estimated_price, bid_end_date) WHERE estimated_price IS NOT NULL AND bid_end_date IS NOT NULL",

            # 추출 정보 인덱스
            "CREATE INDEX IF NOT EXISTS idx_extracted_category_notice ON bid_extracted_info(info_category, bid_notice_no)",
            "CREATE INDEX IF NOT EXISTS idx_extracted_confidence ON bid_extracted_info(confidence_score) WHERE confidence_score >= 0.7"
        ]

        with self.engine.connect() as conn:
            for idx_sql in indexes:
                try:
                    conn.execute(text(idx_sql))
                    conn.commit()
                    print(f"✅ 인덱스 생성 완료")
                except Exception as e:
                    print(f"⚠️ 인덱스 생성 스킵: {str(e)[:50]}...")

        print("🎯 검색 최적화 인덱스 생성 완료")

    def close(self):
        """세션 종료"""
        self.session.close()


def test_advanced_search_system():
    """고급 검색 시스템 테스트"""

    print("🚀 Phase 5: 고급 검색 시스템 테스트")
    print("=" * 80)

    search_system = AdvancedSearchSystem()

    try:
        # 검색 최적화 인덱스 생성
        search_system.create_search_indexes()
        print()

        # 1. 통계 정보 확인
        print("📊 검색 통계 정보")
        print("-" * 40)
        stats = search_system.get_search_statistics()

        print(f"전체 공고: {stats['basic_stats']['total_announcements']:,}개")
        print(f"전체 문서: {stats['basic_stats']['total_documents']:,}개")
        print(f"추출 정보: {stats['basic_stats']['total_extracted_info']:,}개")

        if stats['price_stats']['price_count'] > 0:
            print(f"금액 범위: {stats['price_stats']['min_price']:,}원 ~ {stats['price_stats']['max_price']:,}원")
            print(f"평균 금액: {stats['price_stats']['avg_price']:,}원")

        print(f"활성 공고: {stats['deadline_stats']['active_count']:,}개")
        print(f"7일 내 마감: {stats['deadline_stats']['week_deadline']:,}개")
        print(f"30일 내 마감: {stats['deadline_stats']['month_deadline']:,}개")
        print()

        # 2. 금액 범위 검색 테스트
        print("💰 금액 범위 검색 테스트")
        print("-" * 40)
        price_results = search_system.search_by_price_range(
            min_price=1000000,  # 100만원 이상
            max_price=100000000,  # 1억원 이하
            limit=10
        )

        print(f"검색 결과: {price_results['count']}개")
        print(f"처리 시간: {price_results['processing_time']:.3f}초")

        for i, result in enumerate(price_results['results'][:3], 1):
            ann = result['announcement']
            print(f"  {i}. {ann.bid_notice_no}: {ann.title[:40]}...")
            print(f"     추정가격: {ann.estimated_price:,}원" if ann.estimated_price else "     추정가격: N/A")
            if result['extracted_prices']:
                print(f"     추출가격: {result['extracted_prices']}")
        print()

        # 3. 마감일 검색 테스트
        print("📅 마감일 검색 테스트 (7일 내)")
        print("-" * 40)
        deadline_results = search_system.search_by_deadline(days_ahead=7, limit=10)

        print(f"검색 결과: {deadline_results['count']}개")
        print(f"처리 시간: {deadline_results['processing_time']:.3f}초")

        for i, result in enumerate(deadline_results['results'][:3], 1):
            ann = result['announcement']
            print(f"  {i}. {ann.bid_notice_no}: {ann.title[:40]}...")
            print(f"     마감일: {ann.bid_end_date}")
            print(f"     남은일수: {result['days_left']}일" if result['days_left'] is not None else "     남은일수: N/A")
        print()

        # 4. 업종별 검색 테스트
        print("🏢 업종별 검색 테스트")
        print("-" * 40)
        industry_results = search_system.search_by_industry(
            industry_keywords=['건축', '전기', '토목'],
            limit=10
        )

        print(f"검색 결과: {industry_results['count']}개")
        print(f"처리 시간: {industry_results['processing_time']:.3f}초")

        for i, result in enumerate(industry_results['results'][:3], 1):
            ann = result['announcement']
            print(f"  {i}. {ann.bid_notice_no}: {ann.title[:40]}...")
            print(f"     매칭 키워드: {result['matched_keywords']}")
        print()

        # 5. 복합 조건 검색 테스트
        print("🔍 복합 조건 검색 테스트")
        print("-" * 40)
        complex_results = search_system.complex_search(
            min_price=5000000,  # 500만원 이상
            max_price=50000000,  # 5천만원 이하
            days_ahead=30,  # 30일 내 마감
            industry_keywords=['공사'],
            sort_by='bid_end_date',
            sort_order='asc',
            limit=10
        )

        print(f"검색 결과: {complex_results['count']}개")
        print(f"처리 시간: {complex_results['processing_time']:.3f}초")
        print(f"적용 조건: {complex_results['total_conditions']}개")

        for i, result in enumerate(complex_results['results'][:3], 1):
            ann = result['announcement']
            print(f"  {i}. {ann.bid_notice_no}: {ann.title[:40]}...")
            print(f"     금액: {ann.estimated_price:,}원" if ann.estimated_price else "     금액: N/A")
            print(f"     마감: {ann.bid_end_date} ({result['days_left']}일 남음)" if result['days_left'] is not None else "     마감: N/A")
            if result['matched_info']:
                print(f"     매칭: {result['matched_info']}")
        print()

        # 6. 성능 요약
        print("📈 성능 요약")
        print("-" * 40)
        total_time = (price_results['processing_time'] +
                     deadline_results['processing_time'] +
                     industry_results['processing_time'] +
                     complex_results['processing_time'])

        print(f"총 검색 테스트 시간: {total_time:.3f}초")
        print(f"평균 검색 응답시간: {total_time/4:.3f}초")
        print(f"목표 달성: {'✅' if total_time/4 < 0.5 else '❌'} (목표: 500ms 이내)")

        return True

    except Exception as e:
        print(f"❌ 검색 시스템 테스트 실패: {e}")
        return False

    finally:
        search_system.close()


if __name__ == "__main__":
    success = test_advanced_search_system()

    if success:
        print("\n🎉 Phase 5: 고급 검색 시스템 구현 성공!")
    else:
        print("\n❌ Phase 5: 고급 검색 시스템 구현 실패")