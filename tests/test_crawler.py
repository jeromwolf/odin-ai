#!/usr/bin/env python3
"""
나라장터 크롤러 테스트 스크립트
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime, timedelta

# 프로젝트 루트를 경로에 추가
sys.path.append(str(Path(__file__).parent))

from backend.services.g2b_crawler import G2BCrawler
from backend.services.crawler_manager import CrawlerManager, DataSource


async def test_crawler_basic():
    """기본 크롤러 테스트"""
    print("=" * 60)
    print("나라장터 크롤러 기본 테스트")
    print("=" * 60)

    try:
        async with G2BCrawler() as crawler:
            # 상태 확인
            health = await crawler.health_check()
            if health.get("success"):
                print("✅ 크롤러 초기화 성공")
                print(f"   - 웹사이트 제목: {health.get('website_title', 'N/A')[:50]}...")
            else:
                print("❌ 크롤러 초기화 실패")
                return False

            # 입찰공고 목록 조회 (첫 페이지만)
            print("\n📋 입찰공고 목록 조회 테스트...")
            result = await crawler.get_bid_announcements(
                page=1,
                keyword="시스템 개발",
                start_date=datetime.now().strftime("%Y/%m/%d"),
                end_date=(datetime.now() + timedelta(days=30)).strftime("%Y/%m/%d")
            )

            if result.get("success"):
                items = result.get("items", [])
                print(f"✅ 입찰공고 조회 성공: {len(items)}건")
                print(f"   - 총 건수: {result.get('total_count', 0):,}건")
                print(f"   - 총 페이지: {result.get('total_pages', 1)}페이지")

                # 상위 3건 출력
                for i, item in enumerate(items[:3], 1):
                    print(f"\n   [{i}] {item.get('bid_notice_name', 'N/A')[:40]}...")
                    print(f"       - 공고번호: {item.get('bid_notice_no', 'N/A')}")
                    print(f"       - 기관: {item.get('agency', 'N/A')}")
                    print(f"       - 공고일: {item.get('announcement_date', 'N/A')}")
                    print(f"       - 마감일: {item.get('deadline_date', 'N/A')}")

                # 첫 번째 항목 상세 조회 테스트
                if items and items[0].get("bid_notice_no"):
                    print(f"\n📄 상세 정보 조회 테스트...")
                    bid_no = items[0]["bid_notice_no"]
                    detail = await crawler.get_bid_detail(bid_no)

                    if detail.get("success"):
                        detail_info = detail.get("detail_info", {})
                        parsed_fields = detail_info.get("parsed_fields", {})
                        print(f"✅ 상세 정보 조회 성공")
                        print(f"   - 파싱된 필드: {len(parsed_fields)}개")

                        # 주요 필드 출력
                        key_fields = ["공고명", "공고기관", "계약방법", "개찰일시", "추정가격"]
                        for field in key_fields:
                            if field in parsed_fields:
                                value = parsed_fields[field][:50] + "..." if len(parsed_fields[field]) > 50 else parsed_fields[field]
                                print(f"       - {field}: {value}")

                        # 첨부파일 정보
                        attachments = detail_info.get("attachments", [])
                        if attachments:
                            print(f"   - 첨부파일: {len(attachments)}개")
                            for att in attachments[:2]:
                                print(f"       - {att.get('filename', 'N/A')} ({att.get('type', 'unknown')})")

                    else:
                        print(f"❌ 상세 정보 조회 실패: {detail.get('error', 'Unknown error')}")

            else:
                print(f"❌ 입찰공고 조회 실패: {result.get('error', 'Unknown error')}")
                return False

        return True

    except Exception as e:
        print(f"❌ 크롤러 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_crawler_manager():
    """크롤러 매니저 통합 테스트"""
    print("\n" + "=" * 60)
    print("크롤러 매니저 통합 테스트")
    print("=" * 60)

    try:
        async with CrawlerManager() as manager:
            # 상태 확인
            health = await manager.health_check()
            print(f"✅ 매니저 상태: {health.get('manager_status', 'unknown')}")

            # API 상태 확인
            api_status = health.get("api_status", {})
            if api_status.get("success"):
                print("✅ API 클라이언트: 정상")
            else:
                print("⚠️ API 클라이언트: 연결 불가")

            # 크롤러 상태 확인
            crawler_status = health.get("crawler_status", {})
            if crawler_status.get("success"):
                print("✅ 웹 크롤러: 정상")
            else:
                print("⚠️ 웹 크롤러: 연결 불가")

            # 통합 데이터 수집 테스트 (API 우선)
            print(f"\n📊 통합 데이터 수집 테스트 (API 우선)...")
            start_date = datetime.now().strftime("%Y%m%d0000")
            end_date = (datetime.now() + timedelta(days=7)).strftime("%Y%m%d2359")

            result = await manager.collect_bid_data(
                source=DataSource.HYBRID,
                start_date=start_date,
                end_date=end_date,
                max_items=20,
                keywords=["시스템", "개발"]
            )

            if result.get("success"):
                print(f"✅ 통합 수집 성공")
                print(f"   - 총 수집: {result.get('total_collected', 0)}건")
                print(f"   - 고유 항목: {result.get('unique_items', 0)}건")
                print(f"   - 저장됨: {result.get('saved_items', 0)}건")

                stats = result.get("stats", {})
                print(f"   - API 요청: {stats.get('api_requests', 0)}회")
                print(f"   - 크롤러 요청: {stats.get('crawler_requests', 0)}회")
                print(f"   - 중복 항목: {stats.get('duplicate_items', 0)}건")

                # 수집된 항목 샘플
                items = result.get("items", [])
                if items:
                    print(f"\n📋 수집된 항목 샘플 ({min(3, len(items))}건):")
                    for i, item in enumerate(items[:3], 1):
                        print(f"   [{i}] {item.get('bid_notice_name', 'N/A')[:40]}...")
                        print(f"       - 소스: {item.get('source', 'N/A')}")
                        print(f"       - 공고번호: {item.get('bid_notice_no', 'N/A')}")
                        print(f"       - 기관: {item.get('notice_inst_name', 'N/A')}")

            else:
                print(f"❌ 통합 수집 실패: {result.get('error', 'Unknown error')}")
                return False

            # 통계 조회
            print(f"\n📈 크롤링 통계 조회...")
            stats = await manager.get_crawl_stats()
            if "error" not in stats:
                db_stats = stats.get("database_stats", {})
                print(f"✅ 통계 조회 성공")
                print(f"   - 총 입찰공고: {db_stats.get('total_bids', 0):,}건")
                print(f"   - API 소스: {db_stats.get('api_sourced', 0):,}건")
                print(f"   - 크롤러 소스: {db_stats.get('crawler_sourced', 0):,}건")
            else:
                print(f"❌ 통계 조회 실패: {stats.get('error')}")

        return True

    except Exception as e:
        print(f"❌ 매니저 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_api_only():
    """API 전용 테스트"""
    print("\n" + "=" * 60)
    print("API 전용 데이터 수집 테스트")
    print("=" * 60)

    try:
        async with CrawlerManager() as manager:
            result = await manager.collect_bid_data(
                source=DataSource.API,
                max_items=10
            )

            if result.get("success"):
                print(f"✅ API 전용 수집 성공: {result.get('saved_items', 0)}건 저장")
                return True
            else:
                print(f"❌ API 전용 수집 실패: {result.get('error')}")
                return False

    except Exception as e:
        print(f"❌ API 전용 테스트 실패: {e}")
        return False


async def main():
    """메인 테스트 실행"""
    print("🚀 나라장터 크롤러 종합 테스트 시작\n")

    tests = [
        ("API 전용 테스트", test_api_only),
        ("기본 크롤러", test_crawler_basic),
        ("크롤러 매니저", test_crawler_manager),
    ]

    results = []
    for name, test_func in tests:
        try:
            print(f"\n{'='*60}")
            print(f"🧪 {name} 시작")
            print(f"{'='*60}")

            result = await test_func()
            results.append((name, result))
        except Exception as e:
            print(f"❌ {name} 실행 중 오류: {e}")
            results.append((name, False))

    # 결과 요약
    print(f"\n{'='*60}")
    print("🏁 크롤러 테스트 결과 요약")
    print(f"{'='*60}")

    success_count = 0
    for name, result in results:
        if result:
            print(f"✅ {name}: 성공")
            success_count += 1
        else:
            print(f"❌ {name}: 실패")

    print(f"\n📊 총 {len(results)}개 테스트 중 {success_count}개 성공")

    if success_count > 0:
        print("🎉 크롤러 시스템 작동 확인!")
        print("💡 다음 단계: HWP 파서 통합")
        return 0
    else:
        print("⚠️ 모든 테스트 실패")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)