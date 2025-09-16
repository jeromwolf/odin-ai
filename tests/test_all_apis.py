#!/usr/bin/env python3
"""
조달청 나라장터 전체 API 서비스 테스트
"""

import asyncio
import aiohttp
import json
from datetime import datetime, timedelta

API_BASE_URL = "http://localhost:8095"


async def test_bid_search():
    """입찰공고 검색 API 테스트"""
    print("=" * 60)
    print("🔍 입찰공고 검색 API 테스트")
    print("=" * 60)

    async with aiohttp.ClientSession() as session:
        # 2025년 9월 데이터 검색
        params = {
            "start_date": "20250901",
            "end_date": "20250916",
            "page": 1,
            "size": 3
        }

        async with session.get(
            f"{API_BASE_URL}/api/bids/search",
            params=params
        ) as response:
            if response.status == 200:
                data = await response.json()
                print(f"✅ 입찰공고 검색 성공: {len(data)}건")

                for i, bid in enumerate(data, 1):
                    print(f"\n[{i}] {bid.get('bid_notice_name', 'N/A')}")
                    print(f"   - 공고번호: {bid.get('bid_notice_no', 'N/A')}")
                    print(f"   - 기관: {bid.get('notice_inst_name', 'N/A')}")

                return True
            else:
                print(f"❌ 실패: HTTP {response.status}")
                return False


async def test_user_info():
    """사용자정보 서비스 API 테스트"""
    print("\n" + "=" * 60)
    print("👥 사용자정보 서비스 API 테스트")
    print("=" * 60)

    async with aiohttp.ClientSession() as session:
        params = {
            "page": 1,
            "size": 5
        }

        async with session.get(
            f"{API_BASE_URL}/api/bids/users",
            params=params
        ) as response:
            if response.status == 200:
                data = await response.json()
                print(f"✅ 사용자정보 조회 성공: {len(data)}건")

                if data:
                    for i, user in enumerate(data[:3], 1):
                        print(f"\n[{i}] 사용자 정보")
                        for key in list(user.keys())[:3]:
                            print(f"   - {key}: {user.get(key, 'N/A')}")

                return True
            else:
                print(f"❌ 실패: HTTP {response.status}")
                text = await response.text()
                print(f"   오류: {text[:200]}")
                return False


async def test_contract_info():
    """계약정보 서비스 API 테스트"""
    print("\n" + "=" * 60)
    print("📝 계약정보 서비스 API 테스트")
    print("=" * 60)

    async with aiohttp.ClientSession() as session:
        params = {
            "start_date": "20250801",
            "end_date": "20250916",
            "page": 1,
            "size": 5
        }

        async with session.get(
            f"{API_BASE_URL}/api/bids/contracts",
            params=params
        ) as response:
            if response.status == 200:
                data = await response.json()
                print(f"✅ 계약정보 조회 성공: {len(data)}건")

                if data:
                    for i, contract in enumerate(data[:3], 1):
                        print(f"\n[{i}] 계약 정보")
                        for key in list(contract.keys())[:3]:
                            print(f"   - {key}: {contract.get(key, 'N/A')}")

                return True
            else:
                print(f"❌ 실패: HTTP {response.status}")
                text = await response.text()
                print(f"   오류: {text[:200]}")
                return False


async def test_bid_success():
    """낙찰정보 서비스 API 테스트"""
    print("\n" + "=" * 60)
    print("🏆 낙찰정보 서비스 API 테스트")
    print("=" * 60)

    async with aiohttp.ClientSession() as session:
        params = {
            "start_date": "20250801",
            "end_date": "20250916",
            "page": 1,
            "size": 5
        }

        async with session.get(
            f"{API_BASE_URL}/api/bids/success",
            params=params
        ) as response:
            if response.status == 200:
                data = await response.json()
                print(f"✅ 낙찰정보 조회 성공: {len(data)}건")

                if data:
                    for i, success in enumerate(data[:3], 1):
                        print(f"\n[{i}] 낙찰 정보")
                        for key in list(success.keys())[:3]:
                            print(f"   - {key}: {success.get(key, 'N/A')}")

                return True
            else:
                print(f"❌ 실패: HTTP {response.status}")
                text = await response.text()
                print(f"   오류: {text[:200]}")
                return False


async def test_pre_specs():
    """사전규격정보 서비스 API 테스트"""
    print("\n" + "=" * 60)
    print("📋 사전규격정보 서비스 API 테스트")
    print("=" * 60)

    async with aiohttp.ClientSession() as session:
        params = {
            "page": 1,
            "size": 5
        }

        async with session.get(
            f"{API_BASE_URL}/api/bids/pre-specs",
            params=params
        ) as response:
            if response.status == 200:
                data = await response.json()
                print(f"✅ 사전규격정보 조회 성공: {len(data)}건")

                if data:
                    for i, spec in enumerate(data[:3], 1):
                        print(f"\n[{i}] 사전규격 정보")
                        for key in list(spec.keys())[:3]:
                            print(f"   - {key}: {spec.get(key, 'N/A')}")

                return True
            else:
                print(f"❌ 실패: HTTP {response.status}")
                text = await response.text()
                print(f"   오류: {text[:200]}")
                return False


async def test_system_date():
    """시스템 날짜 API 테스트"""
    print("\n" + "=" * 60)
    print("📅 시스템 날짜 API 테스트")
    print("=" * 60)

    async with aiohttp.ClientSession() as session:
        # 현재 날짜 조회
        async with session.get(f"{API_BASE_URL}/api/system/date") as response:
            if response.status == 200:
                data = await response.json()
                print(f"✅ 오늘 날짜: {data['today']}")
                print(f"   - 포맷: {data['formatted']['korean']}")
                print(f"   - 요일: {data['day_of_week']}요일")
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

                # 처리된 문서 통계
                docs = data.get('processed_documents', {})
                print(f"\n📊 처리된 문서:")
                print(f"   - HWP: {docs.get('hwp', 0)}개")
                print(f"   - PDF: {docs.get('pdf', 0)}개")
                print(f"   - DOC: {docs.get('doc', 0)}개")

                return True
            else:
                print(f"❌ 실패: HTTP {response.status}")
                return False


async def main():
    """메인 테스트 실행"""
    print("🚀 Odin-AI 조달청 나라장터 전체 API 테스트 시작\n")
    print(f"📅 테스트 시작 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    tests = [
        ("시스템 날짜", test_system_date),
        ("입찰공고 검색", test_bid_search),
        ("사용자정보", test_user_info),
        ("계약정보", test_contract_info),
        ("낙찰정보", test_bid_success),
        ("사전규격정보", test_pre_specs),
        ("문서 처리 상태", test_document_status),
    ]

    results = []
    for name, test_func in tests:
        try:
            result = await test_func()
            results.append((name, result))
        except Exception as e:
            print(f"❌ {name} 실행 중 오류: {e}")
            results.append((name, False))

        # 각 테스트 간 대기 (Rate limiting 고려)
        await asyncio.sleep(2)

    # 결과 요약
    print(f"\n{'='*60}")
    print("🏁 조달청 나라장터 API 테스트 결과 요약")
    print(f"{'='*60}")

    success_count = 0
    for name, result in results:
        if result:
            print(f"✅ {name}: 성공")
            success_count += 1
        else:
            print(f"❌ {name}: 실패")

    print(f"\n📊 총 {len(results)}개 테스트 중 {success_count}개 성공")
    print(f"⏰ 테스트 완료 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    if success_count == len(results):
        print("\n🎉 모든 조달청 API 테스트 통과!")
        print("\n💡 사용 가능한 서비스:")
        print("   1. 입찰공고정보 서비스")
        print("   2. 사용자정보 서비스")
        print("   3. 계약정보 서비스")
        print("   4. 낙찰정보 서비스")
        print("   5. 사전규격정보 서비스")
        return 0
    else:
        failed = len(results) - success_count
        print(f"\n⚠️ {failed}개 테스트 실패")
        print("\n💡 실패한 API는 다음을 확인하세요:")
        print("   1. 공공데이터포털 API 키 유효성")
        print("   2. 해당 서비스 구독 상태")
        print("   3. API URL 및 파라미터")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)