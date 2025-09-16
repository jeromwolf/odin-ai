#!/usr/bin/env python3
"""
실제 API 테스트 스크립트 (새 URL 기준)
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime

# 프로젝트 루트를 경로에 추가
sys.path.append(str(Path(__file__).parent))

from backend.services.public_data_client import public_data_client


async def test_construction_bids():
    """공사 입찰공고 조회 테스트"""
    print("=" * 60)
    print("공사 입찰공고 조회 테스트")
    print("=" * 60)

    try:
        # 2025년 9월 데이터로 테스트 (현재 날짜)
        result = await public_data_client.get_bid_construction_list(
            page=1,
            size=5,
            inquiry_div="1",  # 전체
            start_date="202509010000",  # 2025년 9월 1일
            end_date="202509162359"     # 2025년 9월 16일 (오늘)
        )

        if result["success"]:
            print("✅ 공사 입찰공고 조회 성공!")
            print(f"   - 총 건수: {result.get('total_count', 0):,}건")

            items = result.get("items", [])
            print(f"   - 조회된 건수: {len(items)}건")

            # 상위 3건 표시
            for i, item in enumerate(items[:3], 1):
                print(f"\n   [{i}] 공고정보:")
                for key, value in item.items():
                    print(f"       - {key}: {value}")
                print("   " + "-" * 50)

        else:
            print("❌ 공사 입찰공고 조회 실패")
            print(f"   - 오류: {result}")

        return result

    except Exception as e:
        print(f"❌ 테스트 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        return {"success": False, "error": str(e)}


async def test_direct_url():
    """직접 URL 테스트"""
    print("\n" + "=" * 60)
    print("직접 URL 테스트")
    print("=" * 60)

    import httpx
    from backend.core.config import settings

    url = "http://apis.data.go.kr/1230000/ad/BidPublicInfoService/getBidPblancListInfoCnstwk"

    params = {
        "serviceKey": settings.PUBLIC_DATA_API_KEY,
        "pageNo": 1,
        "numOfRows": 3,
        "inqryDiv": 1,
        "inqryBgnDt": "202509010000",  # 2025년 9월 1일
        "inqryEndDt": "202509162359",  # 2025년 9월 16일 (오늘)
        "type": "json"
    }

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            print(f"🔗 요청 URL: {url}")
            print(f"📋 매개변수: {params}")

            response = await client.get(url, params=params)

            print(f"📊 응답 코드: {response.status_code}")
            print(f"📄 응답 헤더: {dict(response.headers)}")
            print(f"📝 응답 내용 (첫 500자): {response.text[:500]}...")

            if response.status_code == 200:
                try:
                    data = response.json()
                    print(f"✅ JSON 파싱 성공!")
                    print(f"📊 응답 구조: {list(data.keys())}")
                    return data
                except Exception as e:
                    print(f"❌ JSON 파싱 실패: {e}")
            else:
                print(f"❌ HTTP 오류: {response.status_code}")

    except Exception as e:
        print(f"❌ 직접 요청 실패: {e}")
        import traceback
        traceback.print_exc()


async def main():
    """메인 테스트 실행"""
    print("\n🚀 실제 나라장터 API 테스트 시작\n")

    # API 키 확인
    from backend.core.config import settings
    api_key = settings.PUBLIC_DATA_API_KEY

    print(f"🔑 API 키: {api_key[:20]}...{api_key[-10:] if len(api_key) > 30 else api_key}")
    print(f"📅 테스트 일시: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # 순차 테스트 실행
    tests = [
        ("직접 URL 테스트", test_direct_url),
        ("공사 입찰공고 조회 테스트", test_construction_bids),
    ]

    results = []
    for name, test_func in tests:
        print(f"\n{'='*60}")
        print(f"🧪 {name} 시작")
        print(f"{'='*60}")

        try:
            result = await test_func()
            results.append((name, result))
        except Exception as e:
            print(f"❌ {name} 실행 중 오류: {e}")
            results.append((name, {"success": False, "error": str(e)}))

    # 결과 요약
    print(f"\n{'='*60}")
    print("🏁 테스트 결과 요약")
    print(f"{'='*60}")

    success_count = 0
    for name, result in results:
        if result and (result.get("success", False) or isinstance(result, dict) and "error" not in result):
            print(f"✅ {name}: 성공")
            success_count += 1
        else:
            print(f"❌ {name}: 실패")

    print(f"\n📊 총 {len(results)}개 테스트 중 {success_count}개 성공")

    if success_count > 0:
        print("🎉 일부 테스트 성공! API 연결 확인됨")
        return 0
    else:
        print("⚠️ 모든 테스트 실패")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)