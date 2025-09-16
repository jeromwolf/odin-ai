#!/usr/bin/env python3
"""
API 실제 응답 구조 분석
raw_data가 비어있는 이유 확인
"""

import asyncio
import sys
import json
from datetime import datetime, timedelta

sys.path.append('/Users/blockmeta/Desktop/blockmeta/project/odin-ai')
from backend.services.public_data_client import PublicDataAPIClient

async def debug_api_response():
    """API 응답 구조 상세 분석"""
    print("=" * 80)
    print("🔍 API 응답 구조 상세 분석")
    print("=" * 80)

    try:
        client = PublicDataAPIClient()

        # 어제 날짜 사용
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y%m%d")

        print(f"📅 테스트 날짜: {yesterday}")
        print(f"🔑 API 키: {'*' * 10}{client.api_key[-10:] if client.api_key else 'None'}")

        # API 호출
        result = await client.get_bid_construction_list(
            page=1,
            size=3,
            inquiry_div="1",
            start_date=yesterday + "0000",
            end_date=yesterday + "2359"
        )

        print(f"\n📊 전체 응답 분석:")
        print(f"- type(result): {type(result)}")
        print(f"- result 내용: {result}")

        if result:
            print(f"\n📋 응답 키 구조:")
            for key, value in result.items():
                print(f"  {key}: {type(value)}")
                if isinstance(value, dict):
                    print(f"    └── 딕셔너리 크기: {len(value)}")
                    if len(value) <= 10:  # 작은 딕셔너리만 내용 출력
                        for sub_key, sub_value in value.items():
                            print(f"        {sub_key}: {type(sub_value)}")

        # raw_data 상세 분석
        if 'raw_data' in result:
            raw_data = result['raw_data']
            print(f"\n🔍 raw_data 상세 분석:")
            print(f"- type: {type(raw_data)}")
            print(f"- len: {len(raw_data) if isinstance(raw_data, (dict, list)) else 'N/A'}")

            if isinstance(raw_data, dict):
                print(f"- keys: {list(raw_data.keys())}")
                for key, value in raw_data.items():
                    print(f"  {key}: {type(value)}")
                    if isinstance(value, str) and len(value) < 200:
                        print(f"    내용: {value}")
                    elif isinstance(value, dict) and len(value) < 10:
                        print(f"    서브키: {list(value.keys())}")

        print(f"\n🧪 다른 파라미터로 재시도...")

        # 더 넓은 날짜 범위로 시도
        start_date = (datetime.now() - timedelta(days=7)).strftime("%Y%m%d")
        end_date = datetime.now().strftime("%Y%m%d")

        result2 = await client.get_bid_construction_list(
            page=1,
            size=1,
            inquiry_div="1",
            start_date=start_date + "0000",
            end_date=end_date + "2359"
        )

        print(f"📊 두 번째 시도 (7일 범위):")
        print(f"- 날짜 범위: {start_date} ~ {end_date}")
        print(f"- success: {result2.get('success') if result2 else 'None'}")

        if result2 and 'raw_data' in result2:
            raw_data2 = result2['raw_data']
            print(f"- raw_data 타입: {type(raw_data2)}")
            print(f"- raw_data 키: {list(raw_data2.keys()) if isinstance(raw_data2, dict) else 'N/A'}")

    except Exception as e:
        print(f"❌ 분석 중 오류: {e}")
        import traceback
        traceback.print_exc()

async def test_different_services():
    """다른 API 서비스들 테스트"""
    print(f"\n{'='*60}")
    print("🔄 다른 API 서비스들 테스트")
    print(f"{'='*60}")

    try:
        client = PublicDataAPIClient()
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y%m%d")

        # 사용자정보서비스 테스트
        print(f"\n📡 사용자정보서비스 테스트")
        try:
            result = await client.get_user_info(
                page=1,
                size=3,
                start_date=yesterday + "0000",
                end_date=yesterday + "2359"
            )
            print(f"- success: {result.get('success') if result else False}")
            if result and 'raw_data' in result:
                print(f"- raw_data 키: {list(result['raw_data'].keys()) if isinstance(result['raw_data'], dict) else 'N/A'}")
        except Exception as e:
            print(f"- 오류: {e}")

        # 낙찰정보서비스 테스트
        print(f"\n📡 낙찰정보서비스 테스트")
        try:
            result = await client.get_bid_success_info(
                page=1,
                size=3,
                inquiry_div="1",
                start_date=yesterday + "0000",
                end_date=yesterday + "2359"
            )
            print(f"- success: {result.get('success') if result else False}")
            if result and 'raw_data' in result:
                print(f"- raw_data 키: {list(result['raw_data'].keys()) if isinstance(result['raw_data'], dict) else 'N/A'}")
        except Exception as e:
            print(f"- 오류: {e}")

    except Exception as e:
        print(f"❌ 다른 서비스 테스트 오류: {e}")

async def main():
    """메인 실행"""
    await debug_api_response()
    await test_different_services()

    print(f"\n{'='*80}")
    print("📋 분석 완료")
    print("- API 응답 구조 파악")
    print("- raw_data가 비어있는 이유 확인")
    print("- stdNtceDocUrl 필드 존재 여부 확인")
    print("=" * 80)

if __name__ == "__main__":
    asyncio.run(main())