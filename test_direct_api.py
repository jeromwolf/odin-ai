#!/usr/bin/env python3
"""
조달청 API 직접 테스트
"""

import asyncio
from backend.services.public_data_client import public_data_client
from datetime import datetime, timedelta

async def test_user_info():
    """사용자정보 API 직접 테스트"""
    print("=" * 60)
    print("사용자정보 서비스 API 직접 테스트")
    print("=" * 60)

    try:
        response = await public_data_client.get_user_info(
            page=1,
            size=2,
            start_date="202501010000",
            end_date="202509162359"
        )

        print(f"✅ 성공!")
        print(f"총 건수: {response.get('total_count', 0)}")

        items = response.get('items', [])
        if items:
            for i, item in enumerate(items[:2], 1):
                print(f"\n[{i}] 업체 정보:")
                print(f"  - 업체명: {item.get('corpNm', 'N/A')}")
                print(f"  - 사업자번호: {item.get('bizno', 'N/A')}")
                print(f"  - 지역: {item.get('rgnNm', 'N/A')}")

    except Exception as e:
        print(f"❌ 실패: {e}")
        import traceback
        traceback.print_exc()


async def test_contract_info():
    """계약정보 API 직접 테스트"""
    print("\n" + "=" * 60)
    print("계약정보 서비스 API 직접 테스트")
    print("=" * 60)

    try:
        response = await public_data_client.get_contract_info(
            page=1,
            size=2,
            start_date="202508010000",
            end_date="202509162359"
        )

        print(f"✅ 성공!")
        print(f"총 건수: {response.get('total_count', 0)}")

        items = response.get('items', [])
        if items:
            for i, item in enumerate(items[:2], 1):
                print(f"\n[{i}] 계약 정보:")
                for key in list(item.keys())[:3]:
                    print(f"  - {key}: {item.get(key, 'N/A')}")

    except Exception as e:
        print(f"❌ 실패: {e}")
        import traceback
        traceback.print_exc()


async def test_bid_success():
    """낙찰정보 API 직접 테스트"""
    print("\n" + "=" * 60)
    print("낙찰정보 서비스 API 직접 테스트")
    print("=" * 60)

    try:
        response = await public_data_client.get_bid_success_info(
            page=1,
            size=2,
            start_date="202508010000",
            end_date="202509162359"
        )

        print(f"✅ 성공!")
        print(f"총 건수: {response.get('total_count', 0)}")

        items = response.get('items', [])
        if items:
            for i, item in enumerate(items[:2], 1):
                print(f"\n[{i}] 낙찰 정보:")
                for key in list(item.keys())[:3]:
                    print(f"  - {key}: {item.get(key, 'N/A')}")

    except Exception as e:
        print(f"❌ 실패: {e}")
        import traceback
        traceback.print_exc()


async def test_pre_spec():
    """사전규격정보 API 직접 테스트"""
    print("\n" + "=" * 60)
    print("사전규격정보 서비스 API 직접 테스트")
    print("=" * 60)

    try:
        response = await public_data_client.get_pre_spec_info(
            page=1,
            size=2,
            start_date="202508010000",
            end_date="202509162359"
        )

        print(f"✅ 성공!")
        print(f"총 건수: {response.get('total_count', 0)}")

        items = response.get('items', [])
        if items:
            for i, item in enumerate(items[:2], 1):
                print(f"\n[{i}] 사전규격 정보:")
                for key in list(item.keys())[:3]:
                    print(f"  - {key}: {item.get(key, 'N/A')}")

    except Exception as e:
        print(f"❌ 실패: {e}")
        import traceback
        traceback.print_exc()


async def main():
    """메인 테스트"""
    print("🚀 조달청 API 직접 테스트 시작\n")

    await test_user_info()
    await asyncio.sleep(2)  # Rate limiting

    await test_contract_info()
    await asyncio.sleep(2)

    await test_bid_success()
    await asyncio.sleep(2)

    await test_pre_spec()

    print("\n✅ 테스트 완료")


if __name__ == "__main__":
    asyncio.run(main())