#!/usr/bin/env python3
"""
공공데이터포털 API 디버깅 테스트
- 에러 내용 상세 확인
- API 키와 파라미터 검증
"""

import asyncio
import sys
import json
from datetime import datetime, timedelta

sys.path.append('/Users/blockmeta/Desktop/blockmeta/project/odin-ai')
from backend.services.public_data_client import PublicDataAPIClient

async def debug_api_response():
    """API 응답 디버깅"""
    print("=" * 80)
    print("🔧 공공데이터포털 API 디버깅")
    print("=" * 80)

    try:
        client = PublicDataAPIClient()

        # 최근 1일로 범위 축소
        end_date = datetime.now()
        start_date = end_date - timedelta(days=1)

        print(f"API 키 확인: {'*' * 10}{client.api_key[-10:] if client.api_key else 'None'}")
        print(f"검색 기간: {start_date.strftime('%Y%m%d')} ~ {end_date.strftime('%Y%m%d')}")

        # API 호출
        response = await client.get_bid_construction_list(
            inqry_div="1",
            inqry_bgn_dt=start_date.strftime("%Y%m%d"),
            inqry_end_dt=end_date.strftime("%Y%m%d"),
            num_of_rows=1,  # 최소한으로
            page_no=1
        )

        print(f"\n📊 전체 응답 분석:")
        print(f"- success: {response.get('success')}")
        print(f"- service: {response.get('service')}")
        print(f"- timestamp: {response.get('timestamp')}")

        # raw_data 상세 분석
        raw_data = response.get('raw_data', {})
        print(f"\n🔍 raw_data 구조:")

        def print_dict_structure(data, prefix=""):
            for key, value in data.items():
                print(f"{prefix}{key}: {type(value)}")
                if isinstance(value, dict):
                    if len(value) < 20:  # 너무 크지 않으면 하위 구조도 출력
                        print_dict_structure(value, prefix + "  ")
                    else:
                        print(f"{prefix}  (딕셔너리 크기: {len(value)})")
                elif isinstance(value, list):
                    print(f"{prefix}  (리스트 크기: {len(value)})")
                    if len(value) > 0 and isinstance(value[0], dict):
                        print(f"{prefix}  첫 번째 항목:")
                        print_dict_structure(value[0], prefix + "    ")
                elif isinstance(value, str) and len(value) < 200:
                    print(f"{prefix}  내용: {value}")

        print_dict_structure(raw_data)

        # 에러 메시지 확인
        if 'nkoneps.com.response.ResponseError' in raw_data:
            error_data = raw_data['nkoneps.com.response.ResponseError']
            print(f"\n❌ API 에러 발생:")
            print_dict_structure(error_data, "  ")

            # header에 에러 코드가 있는지 확인
            if 'header' in error_data:
                header = error_data['header']
                print(f"\n🏷️ 에러 헤더 정보:")
                for key, value in header.items():
                    print(f"  {key}: {value}")

    except Exception as e:
        print(f"❌ 디버깅 중 오류: {e}")
        import traceback
        traceback.print_exc()

async def test_connection():
    """연결 테스트"""
    print(f"\n{'='*60}")
    print("🔗 연결 테스트")
    print(f"{'='*60}")

    try:
        client = PublicDataAPIClient()
        result = await client.test_connection()

        print(f"연결 테스트 결과:")
        print(f"- success: {result.get('success')}")
        print(f"- message: {result.get('message')}")

        if result.get('raw_data'):
            print(f"- raw_data 구조:")
            for key, value in result['raw_data'].items():
                print(f"  {key}: {type(value)}")

    except Exception as e:
        print(f"❌ 연결 테스트 오류: {e}")

async def main():
    """메인 실행"""
    await debug_api_response()
    await test_connection()

    print(f"\n{'='*80}")
    print("디버깅 완료")
    print("=" * 80)

if __name__ == "__main__":
    asyncio.run(main())