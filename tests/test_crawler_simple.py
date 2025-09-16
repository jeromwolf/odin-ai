#!/usr/bin/env python3
"""
크롤러 간단한 데이터 수집 테스트
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime

# 프로젝트 루트를 경로에 추가
sys.path.append(str(Path(__file__).parent))

from backend.services.crawler_manager import CrawlerManager, DataSource


async def test_data_collection():
    """간단한 데이터 수집 테스트"""
    print("🚀 크롤러 데이터 수집 테스트")
    print("=" * 50)

    try:
        async with CrawlerManager() as manager:
            print("✅ 크롤러 매니저 초기화 완료")

            # API에서 입찰공고 데이터 수집
            result = await manager.collect_bid_data(
                source=DataSource.API,
                max_items=10
            )

            if result.get("success"):
                print(f"✅ 데이터 수집 성공!")
                print(f"   - 총 수집: {result.get('total_collected', 0)}건")
                print(f"   - 고유 항목: {result.get('unique_items', 0)}건")
                print(f"   - DB 저장: {result.get('saved_items', 0)}건")

                items = result.get("items", [])
                if items:
                    print(f"\n📋 수집된 데이터 샘플 (상위 3건):")
                    for i, item in enumerate(items[:3], 1):
                        print(f"   [{i}] {item.get('bid_notice_name', 'N/A')[:50]}...")
                        print(f"       공고번호: {item.get('bid_notice_no', 'N/A')}")
                        print(f"       기관명: {item.get('notice_inst_name', 'N/A')}")
                        print(f"       입찰방법: {item.get('bid_method', 'N/A')}")
                        if item.get('presumpt_price'):
                            print(f"       추정가격: {item['presumpt_price']:,}원")

                stats = result.get("stats", {})
                print(f"\n📊 수집 통계:")
                print(f"   - API 요청: {stats.get('api_requests', 0)}회")
                print(f"   - 성공 항목: {stats.get('successful_items', 0)}건")
                print(f"   - 실패 항목: {stats.get('failed_items', 0)}건")
                print(f"   - 중복 항목: {stats.get('duplicate_items', 0)}건")

                return True
            else:
                print(f"❌ 데이터 수집 실패: {result.get('error', 'Unknown error')}")
                return False

    except Exception as e:
        print(f"❌ 테스트 실행 실패: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    result = asyncio.run(test_data_collection())
    if result:
        print("\n🎉 크롤러 시스템 정상 작동!")
        sys.exit(0)
    else:
        print("\n⚠️ 크롤러 시스템 점검 필요")
        sys.exit(1)