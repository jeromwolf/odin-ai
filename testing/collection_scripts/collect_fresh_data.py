#!/usr/bin/env python
"""
Phase 1: 새로운 데이터 수집 및 다운로드
"""

import asyncio
import os
import sys
from pathlib import Path
from datetime import datetime
from loguru import logger

# 프로젝트 경로 추가
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.collector.api_collector import APICollector
from src.services.file_downloader import FileDownloader
from src.database.models import BidAnnouncement, BidDocument

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://blockmeta@localhost:5432/odin_db")


async def collect_and_download(num_items: int = 100):
    """데이터 수집 및 다운로드"""

    # DB 연결
    engine = create_engine(DATABASE_URL)
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        logger.info("=" * 60)
        logger.info("📥 Phase 1: 데이터 수집 시작")
        logger.info(f"목표: {num_items}개 공고")
        logger.info("=" * 60)

        # 1. API 수집
        logger.info("\n1️⃣ API 데이터 수집")
        collector = APICollector(session)

        # 최근 공고 수집
        announcements = await collector.collect_recent_announcements(
            max_items=num_items,
            search_type='입찰공고',
            date_from='20250901',
            date_to='20250922'
        )

        logger.info(f"✅ {len(announcements)}개 공고 수집")

        # 샘플 출력
        if announcements:
            for i, ann in enumerate(announcements[:5]):
                logger.info(f"  {i+1}. {ann.bid_notice_no}: {ann.title[:30]}...")

        # 2. 문서 메타데이터 수집
        logger.info("\n2️⃣ 문서 메타데이터 수집")
        total_documents = 0

        for ann in announcements:
            # 문서 정보 수집
            documents = await collector.collect_document_info(ann.bid_notice_no)
            total_documents += len(documents)

        session.commit()
        logger.info(f"✅ {total_documents}개 문서 메타데이터 저장")

        # 3. 파일 다운로드
        logger.info("\n3️⃣ 파일 다운로드")
        storage_path = Path("./storage")
        downloader = FileDownloader(session, storage_path)

        # 모든 대기 문서 다운로드
        download_results = await downloader.download_pending_documents()

        logger.info(f"✅ 다운로드 완료: 성공 {download_results['success']}개, 실패 {download_results['failed']}개")

        # 4. 최종 통계
        logger.info("\n" + "=" * 60)
        logger.info("📊 수집 결과")
        logger.info("=" * 60)

        # DB 통계
        ann_count = session.query(BidAnnouncement).count()
        doc_count = session.query(BidDocument).count()
        downloaded = session.query(BidDocument).filter(
            BidDocument.download_status == 'completed'
        ).count()

        logger.info(f"공고: {ann_count}개")
        logger.info(f"문서: {doc_count}개")
        logger.info(f"다운로드 완료: {downloaded}개")
        logger.info(f"다운로드 대기: {doc_count - downloaded}개")

        # 파일 형식별 통계
        from sqlalchemy import func
        file_stats = session.query(
            BidDocument.file_extension,
            func.count(BidDocument.document_id)
        ).group_by(BidDocument.file_extension).all()

        logger.info("\n📁 파일 형식별:")
        for ext, count in file_stats:
            logger.info(f"  {ext or 'unknown'}: {count}개")

        return True

    except Exception as e:
        logger.error(f"❌ 수집 실패: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

    finally:
        session.close()


if __name__ == "__main__":
    success = asyncio.run(collect_and_download(100))
    sys.exit(0 if success else 1)