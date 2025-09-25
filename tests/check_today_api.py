#!/usr/bin/env python
"""
오늘 날짜 API 데이터 확인 스크립트
"""

import os
import sys
from datetime import datetime
from pathlib import Path

# 프로젝트 루트 경로 추가
sys.path.append(str(Path.cwd()))

from batch.modules.collector import APICollector
from loguru import logger

def main():
    """오늘 날짜 API 데이터 확인"""

    # DB URL 설정
    db_url = os.getenv('DATABASE_URL', 'postgresql://blockmeta@localhost:5432/odin_db')

    # Collector 초기화
    collector = APICollector(db_url)

    # 오늘 날짜만 조회
    today = datetime.now()

    logger.info(f"📅 오늘 날짜 조회: {today.strftime('%Y-%m-%d')}")

    # API 수집 (저장하지 않고 카운트만)
    result = collector.collect_by_date_range(
        start_date=today,
        end_date=today,
        num_of_rows=1,  # 첫 페이지만 조회해서 totalCount 확인
        max_pages=1
    )

    if result['status'] == 'success':
        logger.info(f"✅ 조회 성공")
        logger.info(f"📊 오늘 공고 총 개수: {result.get('total_count', 0)}개")
        logger.info(f"📄 100개씩 페이지 수: {(result.get('total_count', 0) + 99) // 100}페이지")
        logger.info(f"📄 50개씩 페이지 수: {(result.get('total_count', 0) + 49) // 50}페이지")
    else:
        logger.error(f"❌ 조회 실패: {result.get('message')}")

    return result

if __name__ == "__main__":
    main()