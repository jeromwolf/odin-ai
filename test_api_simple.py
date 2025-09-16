#!/usr/bin/env python3
"""
공공데이터포털 API 간단 테스트
- 직접 API 호출로 나라장터 데이터 확인
- bidNtcUrl 필드를 통한 실제 공고 파일 접근
"""

import asyncio
import sys
from datetime import datetime, timedelta

# 백엔드 모듈 import
sys.path.append('/Users/blockmeta/Desktop/blockmeta/project/odin-ai')
from backend.services.public_data_client import PublicDataAPIClient

async def test_bid_construction_api():
    """입찰공고정보 API 테스트"""
    print("=" * 80)
    print("📡 조달청 나라장터 입찰공고정보 API 테스트")
    print("=" * 80)

    try:
        client = PublicDataAPIClient()

        # 검색 기간 설정 (최근 3일)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=3)

        params = {
            "inqryDiv": "1",  # 전체
            "inqryBgnDt": start_date.strftime("%Y%m%d"),
            "inqryEndDt": end_date.strftime("%Y%m%d"),
            "numOfRows": 10,
            "pageNo": 1
        }

        print(f"요청 파라미터:")
        for key, value in params.items():
            print(f"  {key}: {value}")

        print(f"\n🔄 API 호출 중...")

        # API 호출
        response = await client.get_bid_construction_list(
            inqry_div=params["inqryDiv"],
            inqry_bgn_dt=params["inqryBgnDt"],
            inqry_end_dt=params["inqryEndDt"],
            num_of_rows=params["numOfRows"],
            page_no=params["pageNo"]
        )

        if response and isinstance(response, dict):
            print(f"✅ API 호출 성공!")

            # 응답 구조 확인
            print(f"\n📊 응답 구조:")
            for key in response.keys():
                print(f"  - {key}: {type(response[key])}")

            # raw_data에서 items 확인
            raw_data = response.get('raw_data', {})
            if 'items' in raw_data:
                items = raw_data['items']
            elif 'body' in raw_data and 'items' in raw_data['body']:
                items = raw_data['body']['items']
            else:
                print(f"📋 raw_data 구조 확인:")
                for key, value in raw_data.items():
                    print(f"  - {key}: {type(value)}")
                    if isinstance(value, dict) and len(value) < 10:
                        for k, v in value.items():
                            print(f"    - {k}: {type(v)}")
                items = None

            if items:
                print(f"\n📋 총 {len(items)}개 입찰공고 항목")

                # 처음 3개 항목 상세 출력
                for i, item in enumerate(items[:3], 1):
                    print(f"\n{'='*60}")
                    print(f"[{i}] 입찰공고 상세 정보")
                    print(f"{'='*60}")

                    # 모든 필드 출력 (키워드 검색 포함)
                    keyword_found = False
                    for field, value in item.items():
                        print(f"{field}: {value}")

                        # "데이터" 키워드가 포함된 항목 체크
                        if value and isinstance(value, str) and '데이터' in value:
                            print(f"  🔍 '데이터' 키워드 발견!")
                            keyword_found = True

                    if keyword_found:
                        print(f"  ⭐ 이 공고는 '데이터' 관련 공고입니다!")

                    # bidNtcUrl 필드 확인
                    if 'bidNtceUrl' in item or 'bidNtcUrl' in item:
                        url = item.get('bidNtceUrl') or item.get('bidNtcUrl')
                        if url:
                            print(f"  📎 공고 URL: {url}")
                        else:
                            print(f"  ⚠️ 공고 URL이 비어있음")
                    else:
                        print(f"  ❌ 공고 URL 필드 없음")

            # 전체 개수 정보
            if 'totalCount' in response:
                print(f"\n📈 전체 입찰공고 수: {response['totalCount']}건")

        else:
            print(f"❌ API 호출 실패 - 응답이 없거나 형식이 올바르지 않음")
            print(f"응답 타입: {type(response)}")
            if response:
                print(f"응답 내용: {response}")

    except Exception as e:
        print(f"❌ API 테스트 오류: {e}")
        import traceback
        traceback.print_exc()

async def test_with_keyword_search():
    """키워드로 데이터 필터링 테스트"""
    print(f"\n{'='*80}")
    print("🔍 '데이터' 키워드 포함 공고 검색 테스트")
    print(f"{'='*80}")

    try:
        client = PublicDataAPIClient()

        # 검색 기간을 더 넓게 (최근 30일)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)

        params = {
            "inqryDiv": "1",
            "inqryBgnDt": start_date.strftime("%Y%m%d"),
            "inqryEndDt": end_date.strftime("%Y%m%d"),
            "numOfRows": 100,  # 더 많은 데이터 가져오기
            "pageNo": 1
        }

        print(f"🔄 더 많은 데이터로 키워드 검색 중...")
        print(f"검색 기간: {start_date.strftime('%Y-%m-%d')} ~ {end_date.strftime('%Y-%m-%d')}")

        response = await client.get_bid_construction_list(
            inqry_div=params["inqryDiv"],
            inqry_bgn_dt=params["inqryBgnDt"],
            inqry_end_dt=params["inqryEndDt"],
            num_of_rows=params["numOfRows"],
            page_no=params["pageNo"]
        )

        if response:
            raw_data = response.get('raw_data', {})
            if 'items' in raw_data:
                items = raw_data['items']
            elif 'body' in raw_data and 'items' in raw_data['body']:
                items = raw_data['body']['items']
            else:
                items = None
            if items:
                print(f"📋 총 {len(items)}개 공고 검색됨")
            else:
                print("❌ items 데이터가 없음")
                return

            # 키워드 필터링
            keywords = ['데이터', '분석', 'AI', '인공지능', '시스템']
            matching_items = []

            for item in items:
                for field_name, field_value in item.items():
                    if field_value and isinstance(field_value, str):
                        for keyword in keywords:
                            if keyword in field_value:
                                matching_items.append((item, keyword, field_name))
                                break

            if matching_items:
                print(f"✅ 키워드 매칭 공고 {len(matching_items)}건 발견!")

                for i, (item, keyword, field) in enumerate(matching_items[:3], 1):
                    print(f"\n[{i}] 키워드 '{keyword}' 매칭 ({field} 필드)")
                    print(f"  공고번호: {item.get('bidNtceNo', 'N/A')}")
                    print(f"  공고명: {item.get('bidNm', 'N/A')}")
                    print(f"  공고기관: {item.get('ntceInsttNm', 'N/A')}")

                    # URL 확인
                    url_field = item.get('bidNtceUrl') or item.get('bidNtcUrl')
                    if url_field:
                        print(f"  📎 공고 URL: {url_field}")
                    else:
                        print(f"  ⚠️ 공고 URL 없음")

            else:
                print("❌ 키워드 매칭 공고 없음")

        else:
            print("❌ API 응답 없음")

    except Exception as e:
        print(f"❌ 키워드 검색 오류: {e}")

async def main():
    """메인 실행 함수"""

    # 1. 기본 API 테스트
    await test_bid_construction_api()

    # 2. 키워드 검색 테스트
    await test_with_keyword_search()

    print(f"\n{'='*80}")
    print("📊 테스트 완료")
    print("- 공공데이터포털 API를 통한 나라장터 데이터 접근 테스트")
    print("- bidNtceUrl 필드를 통한 실제 공고 문서 접근 가능 여부 확인")
    print("- '데이터' 관련 키워드 검색으로 관련 공고 필터링")
    print("=" * 80)

if __name__ == "__main__":
    asyncio.run(main())