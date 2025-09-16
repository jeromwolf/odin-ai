#!/usr/bin/env python3
"""
API 날짜 형식 최적화 테스트
- 정확한 날짜 형식으로 API 호출
- stdNtceDocUrl 필드 확인
"""

import asyncio
import sys
from datetime import datetime, timedelta

sys.path.append('/Users/blockmeta/Desktop/blockmeta/project/odin-ai')
from backend.services.public_data_client import PublicDataAPIClient

async def test_api_with_correct_date_format():
    """정확한 날짜 형식으로 API 테스트"""
    print("=" * 80)
    print("📅 정확한 날짜 형식으로 API 테스트")
    print("=" * 80)

    try:
        client = PublicDataAPIClient()

        # 현재 날짜 기준으로 정확한 날짜 범위 설정
        now = datetime.now()

        # 다양한 날짜 범위 테스트
        test_cases = [
            {
                "desc": "어제 하루",
                "start": (now - timedelta(days=1)).strftime("%Y%m%d"),
                "end": (now - timedelta(days=1)).strftime("%Y%m%d")
            },
            {
                "desc": "최근 3일",
                "start": (now - timedelta(days=3)).strftime("%Y%m%d"),
                "end": now.strftime("%Y%m%d")
            },
            {
                "desc": "최근 7일",
                "start": (now - timedelta(days=7)).strftime("%Y%m%d"),
                "end": now.strftime("%Y%m%d")
            },
            {
                "desc": "이번 주 (월요일부터)",
                "start": (now - timedelta(days=now.weekday())).strftime("%Y%m%d"),
                "end": now.strftime("%Y%m%d")
            }
        ]

        for case in test_cases:
            try:
                print(f"\n🔍 {case['desc']} 테스트")
                print(f"   날짜 범위: {case['start']} ~ {case['end']}")

                # API 호출 - 파라미터를 정확한 형식으로
                result = await client.get_bid_construction_list(
                    page=1,
                    size=10,
                    inquiry_div="1",  # 전체
                    start_date=case['start'] + "0000",  # YYYYMMDDHHMM 형식
                    end_date=case['end'] + "2359"       # YYYYMMDDHHMM 형식
                )

                if result and result.get('success'):
                    print(f"   ✅ API 호출 성공!")

                    raw_data = result.get('raw_data', {})

                    # 에러 체크
                    if 'nkoneps.com.response.ResponseError' in raw_data:
                        error_info = raw_data['nkoneps.com.response.ResponseError']['header']
                        print(f"   ❌ API 에러: [{error_info['resultCode']}] {error_info['resultMsg']}")
                        continue

                    # 정상 응답에서 items 추출
                    items = []
                    if 'response' in raw_data:
                        response_data = raw_data['response']
                        if 'body' in response_data and 'items' in response_data['body']:
                            items = response_data['body']['items']
                            total_count = response_data['body'].get('totalCount', 0)
                            print(f"   📊 전체 건수: {total_count}")
                            print(f"   📋 반환 건수: {len(items)}")

                            if items:
                                # 첫 번째 항목의 모든 필드 출력
                                first_item = items[0]
                                print(f"\n   📄 첫 번째 공고 정보:")

                                # 중요 필드만 출력
                                important_fields = [
                                    'bidNtceNo', 'bidNm', 'ntceInsttNm',
                                    'bidBeginDt', 'bidClseDt',
                                    'stdNtceDocUrl', 'bidNtceDtlUrl', 'bidNtceUrl'
                                ]

                                for field in important_fields:
                                    if field in first_item:
                                        value = first_item[field]
                                        if value:
                                            if field == 'bidNm':
                                                print(f"     {field}: {value[:60]}...")
                                            elif 'Url' in field:
                                                print(f"     {field}: {value[:80]}...")
                                                print(f"       🔗 URL 필드 발견!")
                                            else:
                                                print(f"     {field}: {value}")

                                # stdNtceDocUrl 특별 체크
                                if 'stdNtceDocUrl' in first_item and first_item['stdNtceDocUrl']:
                                    print(f"\n   🎯 stdNtceDocUrl 발견!")
                                    print(f"      URL: {first_item['stdNtceDocUrl']}")
                                    return first_item['stdNtceDocUrl']  # 성공시 URL 반환

                            else:
                                print(f"   ❌ items 배열이 비어있음")
                    else:
                        print(f"   ❌ response 구조가 예상과 다름")
                        print(f"   raw_data 키: {list(raw_data.keys())}")

                else:
                    print(f"   ❌ API 호출 실패")

            except Exception as e:
                print(f"   ❌ {case['desc']} 테스트 오류: {e}")

        print(f"\n❌ 모든 날짜 범위에서 stdNtceDocUrl을 찾지 못함")
        return None

    except Exception as e:
        print(f"❌ 전체 테스트 오류: {e}")
        import traceback
        traceback.print_exc()
        return None

async def test_multiple_apis():
    """여러 API 서비스로 테스트"""
    print(f"\n{'='*60}")
    print("🔄 여러 API 서비스 테스트")
    print(f"{'='*60}")

    try:
        client = PublicDataAPIClient()

        # 어제 날짜로 고정
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y%m%d")

        # 다른 API 서비스들도 테스트
        api_tests = [
            {
                "name": "입찰공고정보 (공사)",
                "method": "get_bid_construction_list",
                "params": {
                    "page": 1,
                    "size": 5,
                    "inquiry_div": "1",
                    "start_date": yesterday + "0000",
                    "end_date": yesterday + "2359"
                }
            },
            {
                "name": "계약정보",
                "method": "get_contract_info",
                "params": {
                    "page": 1,
                    "size": 5,
                    "inquiry_div": "1",
                    "start_date": yesterday + "0000",
                    "end_date": yesterday + "2359"
                }
            }
        ]

        for api_test in api_tests:
            try:
                print(f"\n📡 {api_test['name']} API 테스트")

                method = getattr(client, api_test['method'])
                result = await method(**api_test['params'])

                if result and result.get('success'):
                    print(f"   ✅ 호출 성공")

                    raw_data = result.get('raw_data', {})

                    # 에러 체크
                    if 'nkoneps.com.response.ResponseError' in raw_data:
                        error_info = raw_data['nkoneps.com.response.ResponseError']['header']
                        print(f"   ❌ 에러: [{error_info['resultCode']}] {error_info['resultMsg']}")
                        continue

                    # items 확인
                    if 'response' in raw_data and 'body' in raw_data['response'] and 'items' in raw_data['response']['body']:
                        items = raw_data['response']['body']['items']
                        print(f"   📋 {len(items)}건 데이터")

                        if items:
                            # URL 필드 찾기
                            url_fields = ['stdNtceDocUrl', 'bidNtceDtlUrl', 'bidNtceUrl']
                            for url_field in url_fields:
                                if url_field in items[0] and items[0][url_field]:
                                    print(f"   🎯 {url_field} 발견: {items[0][url_field][:80]}...")
                                    return items[0][url_field]
                    else:
                        print(f"   ❌ items 없음")
                else:
                    print(f"   ❌ 호출 실패")

            except Exception as e:
                print(f"   ❌ {api_test['name']} 오류: {e}")

    except Exception as e:
        print(f"❌ 다중 API 테스트 오류: {e}")

    return None

async def main():
    """메인 실행"""
    print("🧪 API 날짜 형식 최적화 및 stdNtceDocUrl 확인 테스트")

    # 1. 정확한 날짜 형식으로 테스트
    found_url = await test_api_with_correct_date_format()

    if not found_url:
        # 2. 여러 API로 테스트
        found_url = await test_multiple_apis()

    print(f"\n{'='*80}")
    if found_url:
        print("🎉 성공! stdNtceDocUrl 또는 관련 URL 발견!")
        print(f"URL: {found_url}")
        print("이제 이 URL로 Selenium 테스트를 진행할 수 있습니다.")
    else:
        print("⚠️ URL을 찾지 못했지만, API 날짜 형식은 개선되었습니다.")
        print("실제 서비스에서는 더 넓은 날짜 범위나 다른 조건으로 시도해볼 수 있습니다.")
    print("=" * 80)

if __name__ == "__main__":
    asyncio.run(main())