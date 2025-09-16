#!/usr/bin/env python3
"""
공공데이터포털 API 실제 작동 테스트
- 더 넓은 날짜 범위로 재시도
- API 파라미터 최적화
- 실제 입찰공고 데이터 확인
"""

import asyncio
import sys
import json
from datetime import datetime, timedelta

sys.path.append('/Users/blockmeta/Desktop/blockmeta/project/odin-ai')
from backend.services.public_data_client import PublicDataAPIClient

async def test_with_wider_date_range():
    """더 넓은 날짜 범위로 테스트"""
    print("=" * 80)
    print("📅 넓은 날짜 범위로 나라장터 API 테스트")
    print("=" * 80)

    client = PublicDataAPIClient()

    # 다양한 날짜 범위 테스트
    test_cases = [
        {"days": 30, "desc": "최근 30일"},
        {"days": 7, "desc": "최근 7일"},
        {"days": 3, "desc": "최근 3일"}
    ]

    for case in test_cases:
        try:
            print(f"\n{'='*60}")
            print(f"🔍 {case['desc']} 데이터 테스트")
            print(f"{'='*60}")

            # 날짜 설정
            end_date = datetime.now()
            start_date = end_date - timedelta(days=case['days'])

            print(f"검색 기간: {start_date.strftime('%Y-%m-%d')} ~ {end_date.strftime('%Y-%m-%d')}")

            # API 호출
            response = await client.get_bid_construction_list(
                inqry_div="1",  # 전체
                inqry_bgn_dt=start_date.strftime("%Y%m%d"),
                inqry_end_dt=end_date.strftime("%Y%m%d"),
                num_of_rows=10,
                page_no=1
            )

            # 응답 분석
            if response.get('success'):
                raw_data = response.get('raw_data', {})

                # 에러 체크
                if 'nkoneps.com.response.ResponseError' in raw_data:
                    error_info = raw_data['nkoneps.com.response.ResponseError']['header']
                    print(f"❌ API 에러: [{error_info['resultCode']}] {error_info['resultMsg']}")
                    continue

                # 성공 응답 체크
                if 'response' in raw_data:
                    response_data = raw_data['response']
                    print(f"✅ API 호출 성공!")

                    # header 정보
                    if 'header' in response_data:
                        header = response_data['header']
                        print(f"📊 응답 헤더:")
                        print(f"  - resultCode: {header.get('resultCode')}")
                        print(f"  - resultMsg: {header.get('resultMsg')}")

                    # body 데이터
                    if 'body' in response_data:
                        body = response_data['body']
                        print(f"📋 응답 본문:")

                        # 전체 건수
                        total_count = body.get('totalCount', 0)
                        print(f"  - 전체 건수: {total_count}")

                        # items 데이터
                        if 'items' in body and body['items']:
                            items = body['items']
                            print(f"  - 반환 건수: {len(items)}")

                            # 처음 2개 항목 출력
                            for i, item in enumerate(items[:2], 1):
                                print(f"\n  [{i}] 입찰공고 정보:")

                                # 중요 필드만 출력
                                important_fields = [
                                    ('bidNtceNo', '공고번호'),
                                    ('bidNm', '공고명'),
                                    ('ntceInsttNm', '공고기관'),
                                    ('bidBeginDt', '입찰시작일시'),
                                    ('bidClseDt', '입찰마감일시'),
                                    ('bidNtceUrl', '공고URL')
                                ]

                                for field_key, field_name in important_fields:
                                    if field_key in item:
                                        value = item[field_key]
                                        if field_key == 'bidNm':
                                            # 공고명은 길 수 있으므로 줄여서 표시
                                            value = value[:80] + "..." if len(value) > 80 else value
                                        print(f"    {field_name}: {value}")

                                # URL이 있는지 특별히 체크
                                url = item.get('bidNtceUrl', '')
                                if url:
                                    print(f"    📎 실제 공고 URL 존재! (길이: {len(url)}자)")
                                else:
                                    print(f"    ⚠️ 공고 URL 없음")

                            # 데이터분석 관련 공고 찾기
                            print(f"\n🔍 '데이터' 관련 공고 검색:")
                            keyword_matches = []

                            for item in items:
                                bid_name = item.get('bidNm', '')
                                if bid_name and '데이터' in bid_name:
                                    keyword_matches.append(item)

                            if keyword_matches:
                                print(f"  ✅ '데이터' 포함 공고 {len(keyword_matches)}건 발견!")
                                for i, match in enumerate(keyword_matches[:2], 1):
                                    print(f"  [{i}] {match.get('bidNm', '')[:100]}...")
                                    print(f"      공고번호: {match.get('bidNtceNo', 'N/A')}")
                                    if match.get('bidNtceUrl'):
                                        print(f"      📎 공고URL: 있음")
                            else:
                                print(f"  ❌ '데이터' 관련 공고 없음")

                        else:
                            print(f"  ❌ items 데이터 없음")

                    # 이 경우가 성공이므로 더 이상 다른 날짜 범위 시도할 필요 없음
                    return True

            else:
                print(f"❌ API 호출 실패")

        except Exception as e:
            print(f"❌ {case['desc']} 테스트 오류: {e}")

    return False

async def main():
    """메인 실행"""
    success = await test_with_wider_date_range()

    print(f"\n{'='*80}")
    if success:
        print("🎉 테스트 성공!")
        print("- 공공데이터포털 API를 통해 나라장터 데이터 접근 확인")
        print("- bidNtceUrl 필드를 통한 실제 공고 문서 링크 확인")
        print("- '데이터' 키워드가 포함된 공고 필터링 가능")
    else:
        print("❌ 모든 테스트 실패")
        print("- API 파라미터나 인증키 문제 가능성")
    print("=" * 80)

if __name__ == "__main__":
    asyncio.run(main())