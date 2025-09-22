#!/usr/bin/env python
"""
깨끗한 상태에서 전체 파이프라인 테스트
"""

import sys
from pathlib import Path
from datetime import datetime
import asyncio

# 프로젝트 경로 추가
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from sqlalchemy import create_engine, text
from src.database.models import Base, BidAnnouncement, BidDocument, BidAttachment
from src.services.tag_generator import TagGenerator
from src.services.search_service import SearchService
from loguru import logger


def init_database():
    """데이터베이스 초기화"""
    logger.info("=" * 60)
    logger.info("🔧 데이터베이스 초기화")
    logger.info("=" * 60)

    db_url = "postgresql://blockmeta@localhost:5432/odin_db"
    engine = create_engine(db_url)

    # 테이블 생성
    Base.metadata.create_all(bind=engine)

    # 생성된 테이블 확인
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT tablename FROM pg_tables
            WHERE schemaname = 'public'
            ORDER BY tablename
        """))
        tables = [row[0] for row in result]

        logger.info(f"✅ 생성된 테이블: {', '.join(tables)}")

    return engine


def insert_test_data(engine):
    """테스트 데이터 삽입"""
    logger.info("\n" + "=" * 60)
    logger.info("📝 테스트 데이터 삽입")
    logger.info("=" * 60)

    from sqlalchemy.orm import sessionmaker
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        # 다양한 테스트 데이터
        test_data = [
            {
                "bid_notice_no": "TEST-2024-001",
                "bid_notice_ord": "000",
                "title": "AI 기반 스마트 행정 시스템 구축",
                "organization_name": "행정안전부",
                "announcement_date": datetime(2024, 10, 1),
                "bid_start_date": datetime(2024, 10, 2),
                "bid_end_date": datetime(2024, 10, 20),
                "estimated_price": 3500000000,
                "contract_method": "협상에 의한 계약",
                "detail_page_url": "https://example.com/TEST-001",
                "standard_doc_url": "https://example.com/docs/TEST-001.hwp",
                "status": "active"
            },
            {
                "bid_notice_no": "TEST-2024-002",
                "bid_notice_ord": "000",
                "title": "국립병원 의료정보 시스템 고도화",
                "organization_name": "보건복지부",
                "announcement_date": datetime(2024, 10, 1),
                "bid_start_date": datetime(2024, 10, 3),
                "bid_end_date": datetime(2024, 10, 25),
                "estimated_price": 2800000000,
                "contract_method": "제한경쟁",
                "detail_page_url": "https://example.com/TEST-002",
                "standard_doc_url": "https://example.com/docs/TEST-002.pdf",
                "status": "active"
            },
            {
                "bid_notice_no": "TEST-2024-003",
                "bid_notice_ord": "000",
                "title": "서울 지하철 9호선 연장 공사",
                "organization_name": "서울특별시 도시철도공사",
                "announcement_date": datetime(2024, 10, 1),
                "bid_start_date": datetime(2024, 10, 5),
                "bid_end_date": datetime(2024, 11, 5),
                "estimated_price": 150000000000,
                "contract_method": "일반경쟁",
                "detail_page_url": "https://example.com/TEST-003",
                "standard_doc_url": "https://example.com/docs/TEST-003.hwp",
                "status": "active"
            },
            {
                "bid_notice_no": "TEST-2024-004",
                "bid_notice_ord": "000",
                "title": "전국 초중고 디지털 교육 플랫폼 구축",
                "organization_name": "교육부",
                "announcement_date": datetime(2024, 10, 1),
                "bid_start_date": datetime(2024, 10, 10),
                "bid_end_date": datetime(2024, 10, 30),
                "estimated_price": 5500000000,
                "contract_method": "협상에 의한 계약",
                "detail_page_url": "https://example.com/TEST-004",
                "standard_doc_url": "https://example.com/docs/TEST-004.pdf",
                "status": "active"
            },
            {
                "bid_notice_no": "TEST-2024-005",
                "bid_notice_ord": "000",
                "title": "부산 신항만 물류 자동화 시설 건설",
                "organization_name": "해양수산부",
                "announcement_date": datetime(2024, 10, 2),
                "bid_start_date": datetime(2024, 10, 15),
                "bid_end_date": datetime(2024, 11, 15),
                "estimated_price": 80000000000,
                "contract_method": "일반경쟁",
                "detail_page_url": "https://example.com/TEST-005",
                "standard_doc_url": "https://example.com/docs/TEST-005.hwp",
                "status": "active"
            }
        ]

        for data in test_data:
            # 공고 생성
            announcement = BidAnnouncement(**data)
            session.add(announcement)

            # 문서 생성
            document = BidDocument(
                bid_notice_no=data["bid_notice_no"],
                document_type="standard",
                download_url=data["standard_doc_url"],
                download_status="completed",
                processing_status="pending",
                file_name=f"{data['bid_notice_no']}.hwp"
            )
            session.add(document)

            # 첨부파일 생성 (2개씩)
            for i in range(1, 3):
                attachment = BidAttachment(
                    bid_notice_no=data["bid_notice_no"],
                    attachment_index=i,
                    file_name=f"첨부_{data['bid_notice_no']}_{i}.pdf",
                    file_url=f"https://example.com/attach/{data['bid_notice_no']}_{i}.pdf",
                    file_type="pdf",
                    document_category="시방서" if i == 1 else "내역서",
                    should_download=True,
                    is_downloaded=False
                )
                session.add(attachment)

        session.commit()
        logger.info(f"✅ {len(test_data)}개 공고 및 관련 데이터 삽입 완료")

        return len(test_data)

    except Exception as e:
        session.rollback()
        logger.error(f"❌ 데이터 삽입 실패: {e}")
        return 0
    finally:
        session.close()


def generate_and_analyze_tags(engine):
    """태그 생성 및 분석"""
    logger.info("\n" + "=" * 60)
    logger.info("🏷️ 태그 생성 및 분석")
    logger.info("=" * 60)

    from sqlalchemy.orm import sessionmaker
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        tag_generator = TagGenerator(session)
        announcements = session.query(BidAnnouncement).all()

        tag_summary = {}

        for announcement in announcements:
            tags = tag_generator.process_announcement(announcement)
            logger.info(f"\n📌 [{announcement.bid_notice_no}]")
            logger.info(f"   제목: {announcement.title}")
            logger.info(f"   태그: {', '.join(tags)}")
            logger.info(f"   금액: {announcement.estimated_price:,}원")

            # 태그 통계
            for tag in tags:
                category = tag_generator._categorize_tag(tag)
                if category not in tag_summary:
                    tag_summary[category] = []
                tag_summary[category].append(tag)

        # 카테고리별 태그 요약
        logger.info("\n📊 카테고리별 태그 분포:")
        for category, tags in tag_summary.items():
            unique_tags = set(tags)
            logger.info(f"   {category}: {len(unique_tags)}종 ({', '.join(list(unique_tags)[:5])}...)")

        return True

    except Exception as e:
        logger.error(f"❌ 태그 생성 실패: {e}")
        return False
    finally:
        session.close()


def test_search_functionality(engine):
    """검색 기능 테스트"""
    logger.info("\n" + "=" * 60)
    logger.info("🔍 검색 기능 테스트")
    logger.info("=" * 60)

    from sqlalchemy.orm import sessionmaker
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        search_service = SearchService(session)

        # 검색 인덱스 생성
        announcements = session.query(BidAnnouncement).all()
        for announcement in announcements:
            search_service.create_search_index(announcement)

        # 다양한 검색 테스트
        test_cases = [
            {"name": "키워드 검색 (시스템)", "params": {"query": "시스템"}},
            {"name": "키워드 검색 (공사)", "params": {"query": "공사"}},
            {"name": "금액 범위 (10억-100억)", "params": {"price_min": 1000000000, "price_max": 10000000000}},
            {"name": "복합 검색 (IT + 50억이상)", "params": {"query": "시스템", "price_min": 5000000000}},
            {"name": "태그 검색", "params": {"tags": ["#IT", "#교육"]}},
        ]

        for test in test_cases:
            logger.info(f"\n🔎 {test['name']}")
            result = search_service.search(**test['params'])
            logger.info(f"   결과: {result['total']}건")

            for item in result['results'][:3]:
                logger.info(f"   • {item['title'][:40]}... ({item['organization_name']})")
                if item['tags']:
                    logger.info(f"     태그: {', '.join(item['tags'][:5])}")

        # 통계
        stats = search_service.get_statistics()
        logger.info(f"\n📈 전체 통계:")
        logger.info(f"   전체 공고: {stats['total_announcements']}건")
        logger.info(f"   활성 공고: {stats['active_announcements']}건")
        logger.info(f"   오늘 등록: {stats['today_announcements']}건")

        return True

    except Exception as e:
        logger.error(f"❌ 검색 테스트 실패: {e}")
        return False
    finally:
        session.close()


def verify_database_state(engine):
    """데이터베이스 최종 상태 확인"""
    logger.info("\n" + "=" * 60)
    logger.info("📊 데이터베이스 최종 상태")
    logger.info("=" * 60)

    with engine.connect() as conn:
        # 테이블별 레코드 수
        tables = [
            'bid_announcements',
            'bid_documents',
            'bid_attachments',
            'bid_tags',
            'bid_tag_relations',
            'bid_search_index'
        ]

        logger.info("테이블별 레코드 수:")
        for table in tables:
            try:
                result = conn.execute(text(f'SELECT COUNT(*) FROM "{table}"'))
                count = result.scalar()
                logger.info(f"   {table}: {count}건")
            except:
                logger.info(f"   {table}: 조회 실패")

        # 샘플 데이터
        result = conn.execute(text("""
            SELECT bid_notice_no, title, estimated_price
            FROM bid_announcements
            ORDER BY estimated_price DESC
            LIMIT 3
        """))

        logger.info("\n💰 고액 입찰 Top 3:")
        for row in result:
            logger.info(f"   [{row[0]}] {row[1][:30]}... - {row[2]:,}원")


def main():
    """메인 실행"""
    logger.info("\n" + "🚀" * 30)
    logger.info("클린 상태 파이프라인 테스트")
    logger.info("🚀" * 30)

    # 1. DB 초기화
    engine = init_database()

    # 2. 테스트 데이터 삽입
    count = insert_test_data(engine)
    if count == 0:
        logger.error("데이터 삽입 실패")
        return False

    # 3. 태그 생성 및 분석
    tag_success = generate_and_analyze_tags(engine)

    # 4. 검색 테스트
    search_success = test_search_functionality(engine)

    # 5. 최종 상태 확인
    verify_database_state(engine)

    # 결과 요약
    logger.info("\n" + "=" * 60)
    logger.info("✨ 테스트 완료")
    logger.info("=" * 60)
    logger.info(f"   데이터 삽입: ✅ {count}건")
    logger.info(f"   태그 생성: {'✅' if tag_success else '❌'}")
    logger.info(f"   검색 기능: {'✅' if search_success else '❌'}")

    if tag_success and search_success:
        logger.info("\n🎉 모든 테스트 성공!")
        logger.info("DBeaver에서 데이터를 확인해보세요.")
        return True
    else:
        logger.info("\n⚠️ 일부 테스트 실패")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)