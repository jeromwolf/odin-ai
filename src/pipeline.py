"""
Odin-AI 데이터 파이프라인 실행 파일
- 데이터 수집, 파일 다운로드, 문서 처리, 태그 생성, 검색 인덱스 생성을 오케스트레이션
"""

import asyncio
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional
from loguru import logger

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database.models import Base
from collector.api_collector import APICollector
from collector.file_downloader import FileDownloader
from services.document_processor import DocumentProcessor
from services.tag_generator import TagGenerator
from services.search_service import SearchService
from shared.config import settings


class OdinAIPipeline:
    """Odin-AI 데이터 파이프라인"""

    def __init__(self, db_url: Optional[str] = None):
        """
        파이프라인 초기화

        Args:
            db_url: 데이터베이스 연결 URL
        """
        # 데이터베이스 설정
        self.db_url = db_url or settings.database_url
        self.engine = create_engine(self.db_url)
        self.SessionLocal = sessionmaker(bind=self.engine)

        # 파일 경로 설정
        self.base_path = Path(settings.data_storage_path)
        self.base_path.mkdir(parents=True, exist_ok=True)

        # 로거 설정
        self._setup_logger()

    def _setup_logger(self):
        """로거 설정"""
        logger.remove()  # 기본 핸들러 제거

        # 콘솔 출력
        logger.add(
            sys.stderr,
            format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
            level="INFO"
        )

        # 파일 로깅
        log_path = self.base_path / "logs"
        log_path.mkdir(exist_ok=True)

        logger.add(
            log_path / "odin_ai_{time:YYYY-MM-DD}.log",
            format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {module}:{function}:{line} | {message}",
            level="DEBUG",
            rotation="1 day",
            retention="30 days"
        )

    def init_database(self):
        """데이터베이스 초기화"""
        logger.info("데이터베이스 초기화 시작")
        try:
            # 테이블 생성
            Base.metadata.create_all(bind=self.engine)
            logger.info("데이터베이스 테이블 생성 완료")
            return True
        except Exception as e:
            logger.error(f"데이터베이스 초기화 실패: {e}")
            return False

    async def collect_data(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        days_back: int = 7
    ):
        """
        공공데이터포털 API에서 데이터 수집

        Args:
            start_date: 수집 시작 날짜
            end_date: 수집 종료 날짜
            days_back: 시작 날짜가 없을 경우 며칠 전부터 수집할지

        Returns:
            수집 통계 (신규, 중복, 업데이트)
        """
        session = self.SessionLocal()

        try:
            # 날짜 범위 설정
            if not end_date:
                end_date = datetime.now()
            if not start_date:
                start_date = end_date - timedelta(days=days_back)

            logger.info(f"API 데이터 수집 시작: {start_date.date()} ~ {end_date.date()}")

            # API 수집기 초기화 및 실행
            collector = APICollector(session)
            new_count, duplicate_count, updated_count = await collector.collect_by_date_range(
                start_date,
                end_date
            )

            logger.info(
                f"API 수집 완료 - 신규: {new_count}, "
                f"중복: {duplicate_count}, 업데이트: {updated_count}"
            )

            return {
                'new': new_count,
                'duplicate': duplicate_count,
                'updated': updated_count
            }

        finally:
            session.close()

    async def download_files(self):
        """
        대기 중인 파일 다운로드

        Returns:
            다운로드 통계
        """
        session = self.SessionLocal()

        try:
            logger.info("파일 다운로드 시작")

            # 다운로더 초기화 및 실행
            downloader = FileDownloader(session, self.base_path)
            stats = await downloader.download_pending_documents()

            logger.info(
                f"다운로드 완료 - 성공: {stats['success']}, "
                f"중복: {stats['duplicate']}, 실패: {stats['failed']}"
            )

            # 실패한 파일 재시도
            if stats['failed'] > 0:
                logger.info("실패한 파일 재시도")
                retry_stats = await downloader.verify_downloads()
                logger.info(
                    f"재시도 결과 - 성공: {retry_stats['success']}, "
                    f"실패: {retry_stats['failed']}"
                )

            return stats

        finally:
            session.close()

    async def process_documents(self):
        """
        다운로드된 문서 처리 (텍스트 추출 및 마크다운 변환)

        Returns:
            처리 통계
        """
        session = self.SessionLocal()

        try:
            logger.info("문서 처리 시작")

            # 문서 처리기 초기화 및 실행
            processor = DocumentProcessor(session, self.base_path)
            stats = await processor.process_pending_documents()

            logger.info(
                f"문서 처리 완료 - 성공: {stats['success']}, "
                f"실패: {stats['failed']}"
            )

            # 전체 통계 조회
            total_stats = processor.get_processing_stats()
            logger.info(f"전체 문서 처리 현황: {total_stats}")

            return stats

        finally:
            session.close()

    def generate_tags(self, limit: int = 100):
        """
        공고에 대한 해시태그 자동 생성

        Args:
            limit: 처리할 공고 수 제한

        Returns:
            생성된 태그 통계
        """
        session = self.SessionLocal()

        try:
            logger.info("해시태그 생성 시작")

            # 태그 생성기 초기화
            tag_generator = TagGenerator(session)

            # 태그가 없는 공고 조회
            from database.models import BidAnnouncement
            announcements = session.query(BidAnnouncement).filter(
                ~BidAnnouncement.tags.any()
            ).limit(limit).all()

            total_tags = 0
            for announcement in announcements:
                tags = tag_generator.process_announcement(announcement)
                total_tags += len(tags)
                logger.debug(f"공고 {announcement.bid_notice_no}: {len(tags)}개 태그 생성")

            logger.info(f"해시태그 생성 완료 - {len(announcements)}개 공고, {total_tags}개 태그")

            # 인기 태그 조회
            popular_tags = tag_generator.get_popular_tags(10)
            logger.info(f"인기 태그 Top 10: {popular_tags}")

            return {
                'announcements_processed': len(announcements),
                'total_tags': total_tags,
                'popular_tags': popular_tags
            }

        finally:
            session.close()

    def build_search_index(self, limit: int = 100):
        """
        검색 인덱스 구축

        Args:
            limit: 처리할 공고 수 제한

        Returns:
            인덱스 생성 통계
        """
        session = self.SessionLocal()

        try:
            logger.info("검색 인덱스 구축 시작")

            # 검색 서비스 초기화
            search_service = SearchService(session)

            # 인덱스가 없는 공고 조회
            from database.models import BidAnnouncement, BidSearchIndex
            from sqlalchemy import not_

            indexed_nos = session.query(BidSearchIndex.bid_notice_no).subquery()
            announcements = session.query(BidAnnouncement).filter(
                ~BidAnnouncement.bid_notice_no.in_(indexed_nos)
            ).limit(limit).all()

            indexed_count = 0
            for announcement in announcements:
                search_service.create_search_index(announcement)
                indexed_count += 1

            logger.info(f"검색 인덱스 구축 완료 - {indexed_count}개 공고")

            # 검색 통계 조회
            stats = search_service.get_statistics()
            logger.info(f"검색 통계: {stats}")

            return {
                'indexed': indexed_count,
                'statistics': stats
            }

        finally:
            session.close()

    async def run_full_pipeline(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        days_back: int = 7
    ):
        """
        전체 파이프라인 실행

        Args:
            start_date: 수집 시작 날짜
            end_date: 수집 종료 날짜
            days_back: 시작 날짜가 없을 경우 며칠 전부터 수집할지

        Returns:
            전체 실행 통계
        """
        logger.info("=" * 50)
        logger.info("Odin-AI 전체 파이프라인 시작")
        logger.info("=" * 50)

        results = {}

        # 1. 데이터베이스 초기화
        if not self.init_database():
            logger.error("데이터베이스 초기화 실패. 파이프라인 중단")
            return None

        # 2. API 데이터 수집
        results['collection'] = await self.collect_data(start_date, end_date, days_back)

        # 3. 파일 다운로드
        results['download'] = await self.download_files()

        # 4. 문서 처리
        results['processing'] = await self.process_documents()

        # 5. 해시태그 생성
        results['tags'] = self.generate_tags()

        # 6. 검색 인덱스 구축
        results['index'] = self.build_search_index()

        logger.info("=" * 50)
        logger.info("Odin-AI 전체 파이프라인 완료")
        logger.info(f"실행 결과: {results}")
        logger.info("=" * 50)

        return results

    async def run_incremental(self):
        """
        증분 업데이트 실행 (최근 1일)

        Returns:
            실행 통계
        """
        logger.info("증분 업데이트 시작 (최근 1일)")
        return await self.run_full_pipeline(days_back=1)

    def search_test(self, query: str = None, tags: list = None):
        """
        검색 테스트

        Args:
            query: 검색어
            tags: 태그 리스트

        Returns:
            검색 결과
        """
        session = self.SessionLocal()

        try:
            search_service = SearchService(session)

            # 검색 실행
            results = search_service.search(
                query=query,
                tags=tags,
                page=1,
                page_size=10
            )

            logger.info(f"검색 결과: {results['total']}건")

            for idx, result in enumerate(results['results'], 1):
                logger.info(
                    f"{idx}. {result['title'][:50]}... "
                    f"({result['organization_name']}, {result['days_remaining']}일 남음)"
                )
                if result['tags']:
                    logger.info(f"   태그: {', '.join(result['tags'])}")

            return results

        finally:
            session.close()


async def main():
    """메인 실행 함수"""
    import argparse

    parser = argparse.ArgumentParser(description='Odin-AI 데이터 파이프라인')
    parser.add_argument(
        '--mode',
        choices=['full', 'incremental', 'collect', 'download', 'process', 'tags', 'index', 'search'],
        default='incremental',
        help='실행 모드'
    )
    parser.add_argument('--days', type=int, default=7, help='수집 일수 (full 모드)')
    parser.add_argument('--query', type=str, help='검색어 (search 모드)')
    parser.add_argument('--tags', type=str, nargs='+', help='태그 (search 모드)')
    parser.add_argument('--db-url', type=str, help='데이터베이스 URL')

    args = parser.parse_args()

    # 파이프라인 초기화
    pipeline = OdinAIPipeline(db_url=args.db_url)

    # 모드별 실행
    if args.mode == 'full':
        await pipeline.run_full_pipeline(days_back=args.days)
    elif args.mode == 'incremental':
        await pipeline.run_incremental()
    elif args.mode == 'collect':
        await pipeline.collect_data(days_back=args.days)
    elif args.mode == 'download':
        await pipeline.download_files()
    elif args.mode == 'process':
        await pipeline.process_documents()
    elif args.mode == 'tags':
        pipeline.generate_tags()
    elif args.mode == 'index':
        pipeline.build_search_index()
    elif args.mode == 'search':
        pipeline.search_test(query=args.query, tags=args.tags)


if __name__ == "__main__":
    asyncio.run(main())