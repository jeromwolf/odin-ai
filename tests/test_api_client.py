#!/usr/bin/env python3
"""
공공데이터포털 API 클라이언트 테스트 스크립트
"""

import asyncio
import sys
from pathlib import Path

# 프로젝트 루트를 경로에 추가
sys.path.append(str(Path(__file__).parent))

from backend.services.public_data_client import public_data_client


async def test_api_connection():
    """API 연결 테스트"""
    print("=" * 60)
    print("공공데이터포털 API 연결 테스트")
    print("=" * 60)

    try:
        # 연결 테스트
        result = await public_data_client.test_connection()

        if result["success"]:
            print("✅ API 연결 성공!")
            print(f"   - API 키 유효: {result['api_key_valid']}")

            # 테스트 결과가 있으면 표시
            if "test_result" in result:
                test_data = result["test_result"]
                total_count = test_data.get("total_count", 0)
                print(f"   - 전체 입찰공고 수: {total_count:,}건")

                items = test_data.get("items", [])
                if items:
                    first_item = items[0]
                    print(f"   - 최신 공고: {first_item.get('bidNtceNm', 'N/A')}")
        else:
            print("❌ API 연결 실패")
            print(f"   - 오류: {result['message']}")
            print(f"   - API 키 유효: {result['api_key_valid']}")

        return result

    except Exception as e:
        print(f"❌ 테스트 중 오류 발생: {e}")
        return {"success": False, "error": str(e)}


async def test_bid_announcements():
    """입찰공고 조회 테스트"""
    print("\n" + "=" * 60)
    print("입찰공고 목록 조회 테스트")
    print("=" * 60)

    try:
        # 최근 1일간 공고 조회
        result = await public_data_client.get_bid_announcements(
            page=1,
            size=5  # 5건만 테스트
        )

        if result["success"]:
            print(f"✅ 입찰공고 조회 성공!")
            print(f"   - 총 공고 수: {result.get('total_count', 0):,}건")

            items = result.get("items", [])
            print(f"   - 조회된 공고: {len(items)}건")

            # 상위 3건 표시
            for i, item in enumerate(items[:3], 1):
                print(f"\n   [{i}] {item.get('bidNtceNm', 'N/A')}")
                print(f"       - 공고기관: {item.get('ntceInsttNm', 'N/A')}")
                print(f"       - 공고일시: {item.get('bidNtceDt', 'N/A')}")
                print(f"       - 예정가격: {item.get('presmptPrce', 'N/A')}")
        else:
            print("❌ 입찰공고 조회 실패")

    except Exception as e:
        print(f"❌ 테스트 중 오류 발생: {e}")


async def test_keyword_search():
    """키워드 검색 테스트"""
    print("\n" + "=" * 60)
    print("키워드 검색 테스트 ('AI', '데이터', '분석')")
    print("=" * 60)

    try:
        # 최근 7일간 키워드 검색
        keywords = ["AI", "데이터", "분석", "인공지능", "빅데이터"]

        result = await public_data_client.search_recent_bids(
            days=7,
            keywords=keywords
        )

        if result["success"]:
            print(f"✅ 키워드 검색 성공!")
            print(f"   - 전체 공고: {result.get('total_count', 0)}건")
            print(f"   - 필터링된 공고: {result.get('filtered_count', 0)}건")
            print(f"   - 키워드: {', '.join(keywords)}")

            items = result.get("items", [])
            for i, item in enumerate(items[:3], 1):
                print(f"\n   [{i}] {item.get('bidNtceNm', 'N/A')}")
                print(f"       - 공고기관: {item.get('ntceInsttNm', 'N/A')}")
                print(f"       - 공고일시: {item.get('bidNtceDt', 'N/A')}")
        else:
            print("❌ 키워드 검색 실패")

    except Exception as e:
        print(f"❌ 테스트 중 오류 발생: {e}")


async def main():
    """메인 테스트 실행"""
    print("\n🚀 공공데이터포털 API 클라이언트 테스트 시작\n")

    # API 키 확인
    from backend.core.config import settings
    api_key = settings.PUBLIC_DATA_API_KEY

    if not api_key or api_key == "test-api-key":
        print("⚠️  경고: 실제 API 키가 설정되지 않았습니다.")
        print("   .env 파일에 PUBLIC_DATA_API_KEY를 설정하세요.")
        print("   현재 더미 키로 테스트를 시도합니다 (실패 예상).\n")

    # 순차 테스트 실행
    tests = [
        ("API 연결 테스트", test_api_connection),
        ("입찰공고 조회 테스트", test_bid_announcements),
        ("키워드 검색 테스트", test_keyword_search)
    ]

    results = []
    for name, test_func in tests:
        try:
            result = await test_func()
            results.append((name, result))
        except Exception as e:
            print(f"❌ {name} 실행 중 오류: {e}")
            results.append((name, {"success": False, "error": str(e)}))

    # 결과 요약
    print("\n" + "=" * 60)
    print("테스트 결과 요약")
    print("=" * 60)

    success_count = 0
    for name, result in results:
        if result and result.get("success", False):
            print(f"✅ {name}: 성공")
            success_count += 1
        else:
            print(f"❌ {name}: 실패")

    print(f"\n총 {len(results)}개 테스트 중 {success_count}개 성공")

    if success_count == len(results):
        print("🎉 모든 테스트 통과!")
        return 0
    else:
        print("⚠️ 일부 테스트 실패")
        if api_key == "test-api-key":
            print("\n💡 실제 API 키를 설정하면 테스트가 성공할 수 있습니다.")
            print("   docs/API_KEY_SETUP.md 파일을 참고하세요.")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)