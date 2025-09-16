#!/usr/bin/env python3
"""
FastAPI 엔드포인트 테스트
"""

import asyncio
import aiohttp
import json
from datetime import datetime, timedelta

API_BASE_URL = "http://localhost:8095"


async def test_root_endpoint():
    """루트 엔드포인트 테스트"""
    print("=" * 60)
    print("🔍 루트 엔드포인트 테스트")
    print("=" * 60)

    async with aiohttp.ClientSession() as session:
        async with session.get(f"{API_BASE_URL}/") as response:
            if response.status == 200:
                data = await response.json()
                print(f"✅ 서버 정보:")
                print(f"   - 이름: {data['name']}")
                print(f"   - 버전: {data['version']}")
                print(f"   - 설명: {data['description']}")
                return True
            else:
                print(f"❌ 실패: HTTP {response.status}")
                return False


async def test_health_endpoint():
    """헬스체크 엔드포인트 테스트"""
    print("\n" + "=" * 60)
    print("🔍 헬스체크 엔드포인트 테스트")
    print("=" * 60)

    async with aiohttp.ClientSession() as session:
        async with session.get(f"{API_BASE_URL}/health") as response:
            if response.status == 200:
                data = await response.json()
                print(f"✅ 서비스 상태: {data['status']}")
                return True
            else:
                print(f"❌ 실패: HTTP {response.status}")
                return False


async def test_bid_search():
    """입찰공고 검색 API 테스트"""
    print("\n" + "=" * 60)
    print("🔍 입찰공고 검색 API 테스트")
    print("=" * 60)

    async with aiohttp.ClientSession() as session:
        # 최근 7일 검색
        params = {
            "start_date": (datetime.now() - timedelta(days=7)).strftime("%Y%m%d"),
            "end_date": datetime.now().strftime("%Y%m%d"),
            "page": 1,
            "size": 5
        }

        async with session.get(
            f"{API_BASE_URL}/api/bids/search",
            params=params
        ) as response:
            if response.status == 200:
                data = await response.json()
                print(f"✅ 검색 결과: {len(data)}건")

                if data:
                    for i, bid in enumerate(data[:3], 1):
                        print(f"\n[{i}] {bid.get('bid_notice_name', 'N/A')}")
                        print(f"   - 공고번호: {bid.get('bid_notice_no', 'N/A')}")
                        print(f"   - 기관: {bid.get('notice_inst_name', 'N/A')}")
                        print(f"   - 예정가격: {bid.get('pre_price', 'N/A'):,}원" if bid.get('pre_price') else "   - 예정가격: 미공개")
                return True
            else:
                print(f"❌ 실패: HTTP {response.status}")
                text = await response.text()
                print(f"   오류: {text[:200]}")
                return False


async def test_bid_stats():
    """입찰공고 통계 API 테스트"""
    print("\n" + "=" * 60)
    print("📊 입찰공고 통계 API 테스트")
    print("=" * 60)

    async with aiohttp.ClientSession() as session:
        async with session.get(f"{API_BASE_URL}/api/bids/stats/summary") as response:
            if response.status == 200:
                data = await response.json()
                print(f"✅ 통계 정보:")
                print(f"   - 조회 기간: {data['period']['start_date']} ~ {data['period']['end_date']}")
                print(f"   - 총 공고 수: {data.get('total_count', 0):,}건")

                if data.get('by_type'):
                    print(f"\n📌 유형별 통계:")
                    for type_name, count in data['by_type'].items():
                        print(f"   - {type_name}: {count:,}건")

                if data.get('price_ranges'):
                    print(f"\n💰 가격대별 통계:")
                    for range_name, count in data['price_ranges'].items():
                        print(f"   - {range_name}: {count}건")

                return True
            else:
                print(f"❌ 실패: HTTP {response.status}")
                return False


async def test_document_status():
    """문서 처리 서비스 상태 테스트"""
    print("\n" + "=" * 60)
    print("📄 문서 처리 서비스 상태 테스트")
    print("=" * 60)

    async with aiohttp.ClientSession() as session:
        async with session.get(f"{API_BASE_URL}/api/documents/status") as response:
            if response.status == 200:
                data = await response.json()
                print(f"✅ 서비스 상태:")

                # Docker 서비스 상태
                health = data.get('service_health', {})
                print(f"\n🐳 Docker 서비스:")
                print(f"   - HWP 서비스: {'✅' if health.get('hwp_service') else '❌'}")
                print(f"   - PDF 서비스: {'✅' if health.get('pdf_service') else '❌'}")
                print(f"   - 로컬 처리기: {'✅' if health.get('local_processor') else '❌'}")

                # 처리된 문서 통계
                docs = data.get('processed_documents', {})
                print(f"\n📊 처리된 문서:")
                print(f"   - HWP: {docs.get('hwp', 0)}개")
                print(f"   - PDF: {docs.get('pdf', 0)}개")
                print(f"   - DOC: {docs.get('doc', 0)}개")
                print(f"   - 총합: {data.get('total_documents', 0)}개")

                return True
            else:
                print(f"❌ 실패: HTTP {response.status}")
                return False


async def test_document_search():
    """문서 검색 API 테스트"""
    print("\n" + "=" * 60)
    print("🔍 문서 검색 API 테스트")
    print("=" * 60)

    async with aiohttp.ClientSession() as session:
        params = {
            "keyword": "입찰",
            "limit": 5
        }

        async with session.get(
            f"{API_BASE_URL}/api/documents/search",
            params=params
        ) as response:
            if response.status == 200:
                data = await response.json()
                print(f"✅ 검색 결과:")
                print(f"   - 키워드: {data['keyword']}")
                print(f"   - 결과 수: {data['total_results']}개")

                if data.get('results'):
                    print(f"\n📄 매칭 문서:")
                    for i, result in enumerate(data['results'][:3], 1):
                        print(f"   [{i}] {result['filename']}")
                        print(f"       타입: {result['file_type']}")
                        print(f"       매칭 횟수: {result['total_matches']}회")

                return True
            else:
                print(f"❌ 실패: HTTP {response.status}")
                return False


async def test_api_documentation():
    """API 문서 접근 테스트"""
    print("\n" + "=" * 60)
    print("📚 API 문서 접근 테스트")
    print("=" * 60)

    async with aiohttp.ClientSession() as session:
        # Swagger UI 테스트
        async with session.get(f"{API_BASE_URL}/docs") as response:
            if response.status == 200:
                print(f"✅ Swagger UI 접근 가능")
                print(f"   URL: {API_BASE_URL}/docs")
            else:
                print(f"❌ Swagger UI 접근 실패")

        # ReDoc 테스트
        async with session.get(f"{API_BASE_URL}/redoc") as response:
            if response.status == 200:
                print(f"✅ ReDoc 접근 가능")
                print(f"   URL: {API_BASE_URL}/redoc")
            else:
                print(f"❌ ReDoc 접근 실패")

    return True


async def main():
    """메인 테스트 실행"""
    print("🚀 Odin-AI API 테스트 시작\n")

    tests = [
        ("루트 엔드포인트", test_root_endpoint),
        ("헬스체크", test_health_endpoint),
        ("입찰공고 검색", test_bid_search),
        ("입찰공고 통계", test_bid_stats),
        ("문서 서비스 상태", test_document_status),
        ("문서 검색", test_document_search),
        ("API 문서", test_api_documentation),
    ]

    results = []
    for name, test_func in tests:
        try:
            result = await test_func()
            results.append((name, result))
        except Exception as e:
            print(f"❌ {name} 실행 중 오류: {e}")
            results.append((name, False))

    # 결과 요약
    print(f"\n{'='*60}")
    print("🏁 API 테스트 결과 요약")
    print(f"{'='*60}")

    success_count = 0
    for name, result in results:
        if result:
            print(f"✅ {name}: 성공")
            success_count += 1
        else:
            print(f"❌ {name}: 실패")

    print(f"\n📊 총 {len(results)}개 테스트 중 {success_count}개 성공")

    if success_count == len(results):
        print("\n🎉 모든 API 테스트 통과!")
        print("\n💡 API 문서 확인:")
        print(f"   - Swagger UI: {API_BASE_URL}/docs")
        print(f"   - ReDoc: {API_BASE_URL}/redoc")
        return 0
    else:
        print(f"\n⚠️ {len(results) - success_count}개 테스트 실패")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)