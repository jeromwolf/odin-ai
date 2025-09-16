#!/usr/bin/env python3
"""
공공데이터포털 API를 통한 나라장터 데이터 수집 테스트
- 5개 나라장터 관련 API 순차 테스트
- 실제 데이터 수집 및 파일 다운로드 URL 확인
"""

import asyncio
import sys
import os
from datetime import datetime, timedelta

# 백엔드 모듈 import
sys.path.append('/Users/blockmeta/Desktop/blockmeta/project/odin-ai')
from backend.services.public_data_client import PublicDataAPIClient
from backend.services.search_service import SearchService

async def test_all_apis():
    """모든 공공데이터포털 API 테스트"""
    print("=" * 80)
    print("공공데이터포털 나라장터 API 전체 테스트")
    print("=" * 80)

    client = PublicDataAPIClient()

    # 검색 기간 설정 (최근 7일)
    end_date = datetime.now()
    start_date = end_date - timedelta(days=7)

    # 모든 API 순차 테스트 (실제 서비스명 사용)
    services = ["bid_construction", "bid_success", "contract_info", "pre_spec", "user_info"]

    for service in services:
        print(f"\n{'='*60}")
        print(f"📡 {service.upper()} API 테스트")
        print(f"{'='*60}")

        try:
            # 서비스별 파라미터 설정
            params = {
                "numOfRows": 5,  # 처음에는 적은 수로 테스트
                "pageNo": 1
            }

            # 날짜 파라미터가 필요한 서비스들
            if service in ["bid_construction", "bid_success", "contract_info", "pre_spec"]:
                params.update({
                    "inqryBgnDt": start_date.strftime("%Y%m%d"),
                    "inqryEndDt": end_date.strftime("%Y%m%d")
                })

            # 기관구분 파라미터 (일부 서비스)
            if service in ["bid_construction", "contract_info", "pre_spec"]:
                params["inqryDiv"] = "1"  # 전체

            print(f"요청 파라미터: {params}")

            # API 호출
            response = await client.call_api(service, params)

            if response:
                print(f"✅ {service} API 호출 성공")

                # 응답 구조 분석
                if isinstance(response, dict):
                    if 'items' in response:
                        items = response['items']
                        print(f"📊 총 {len(items)}개 항목 수신")

                        # 처음 2개 항목만 상세 출력
                        for i, item in enumerate(items[:2], 1):
                            print(f"\n[{i}] 항목 상세:")

                            # 중요 필드들 출력
                            important_fields = [
                                'bidNtcNo', '공고번호', 'bidNm', '공고명',
                                'ntceInsttNm', '공고기관명', 'bidNtcUrl', '입찰공고URL',
                                'dminsttNm', '수요기관명', 'cntrctCnclsDate', '계약체결일자',
                                'bidClseDate', '입찰마감일시', 'rgstDate', '등록일시'
                            ]

                            for field in important_fields:
                                if field in item:
                                    value = item[field]
                                    if value:
                                        print(f"  {field}: {value}")

                            # bidNtcUrl이나 관련 URL 확인
                            url_fields = [key for key in item.keys() if 'url' in key.lower() or 'link' in key.lower()]
                            if url_fields:
                                print("  📎 URL 관련 필드들:")
                                for url_field in url_fields:
                                    print(f"    {url_field}: {item[url_field]}")

                    # totalCount 정보
                    if 'totalCount' in response:
                        print(f"\n📈 전체 데이터 수: {response['totalCount']}건")

                print(f"\n💡 {service} 테스트 완료")

            else:
                print(f"❌ {service} API 호출 실패 - 응답 없음")

        except Exception as e:
            print(f"❌ {service} API 오류: {e}")
            import traceback
            traceback.print_exc()

        # 다음 API 호출 전 잠시 대기
        await asyncio.sleep(2)

async def test_search_service():
    """검색 서비스 테스트"""
    print(f"\n{'='*60}")
    print("🔍 검색 서비스 테스트")
    print(f"{'='*60}")

    try:
        search_service = SearchService()

        # "데이터분석" 키워드로 검색
        keyword = "데이터분석"
        print(f"검색 키워드: '{keyword}'")

        results = await search_service.search_bids(keyword=keyword, limit=5)

        if results:
            print(f"✅ 검색 성공 - {len(results)}건 발견")

            for i, result in enumerate(results, 1):
                print(f"\n[{i}] 검색 결과:")
                print(f"  공고번호: {result.get('공고번호', 'N/A')}")
                print(f"  공고명: {result.get('공고명', 'N/A')[:100]}...")
                print(f"  공고기관: {result.get('공고기관', 'N/A')}")
                print(f"  입찰마감일시: {result.get('입찰마감일시', 'N/A')}")

                # URL 관련 정보
                url_info = result.get('입찰공고URL') or result.get('bidNtcUrl')
                if url_info:
                    print(f"  📎 공고 URL: {url_info}")
        else:
            print("❌ 검색 결과 없음")

    except Exception as e:
        print(f"❌ 검색 서비스 오류: {e}")
        import traceback
        traceback.print_exc()

async def main():
    """메인 실행 함수"""

    # 1. 모든 API 테스트
    await test_all_apis()

    # 2. 검색 서비스 테스트
    await test_search_service()

    print(f"\n{'='*80}")
    print("📊 테스트 요약")
    print("- 공공데이터포털 API로 나라장터 데이터 접근 테스트 완료")
    print("- bidNtcUrl 필드를 통한 실제 공고 URL 확인 시도")
    print("- 검색 서비스를 통한 키워드 검색 테스트")
    print("=" * 80)

if __name__ == "__main__":
    asyncio.run(main())