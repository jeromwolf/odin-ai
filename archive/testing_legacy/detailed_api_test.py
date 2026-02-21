#!/usr/bin/env python3
"""
API 응답 상세 분석 테스트
모든 API 응답 필드를 자세히 확인
"""

import asyncio
import aiohttp
import json
import urllib.parse
from datetime import datetime
from pathlib import Path

# API 설정
API_KEY = urllib.parse.unquote("6h2l2VPWSfA2vG3xSFr7gf6iwaZT2dmzcoCOzklLnOIJY6sw17lrwHNQ3WxPdKMDIN%2FmMlv2vBTWTIzBDPKVdw%3D%3D")
BASE_URL = "http://apis.data.go.kr/1230000/ad/BidPublicInfoService"


async def test_api():
    """API 응답 상세 테스트"""

    target_date = datetime.now()
    date_str = target_date.strftime('%Y%m%d')

    params = {
        'serviceKey': API_KEY,
        'pageNo': 1,
        'numOfRows': 10,
        'type': 'json',
        'inqryDiv': '1',
        'inqryBgnDt': f'{date_str}0000',
        'inqryEndDt': f'{date_str}2359',
    }

    url = f"{BASE_URL}/getBidPblancListInfoCnstwk"

    print("=" * 80)
    print("📡 API 상세 분석 시작")
    print("=" * 80)
    print(f"요청 날짜: {target_date.strftime('%Y-%m-%d')}")
    print(f"요청 URL: {url}")
    print()

    async with aiohttp.ClientSession() as session:
        async with session.get(url, params=params) as response:
            if response.status == 200:
                data = await response.json()

                if 'response' in data and 'body' in data['response']:
                    items = data['response']['body'].get('items', [])

                    print(f"✅ 총 {len(items)}건 수신")
                    print()

                    # 각 항목 상세 분석
                    for idx, item in enumerate(items, 1):
                        print(f"[{idx}번째 공고]")
                        print(f"  공고명: {item.get('bidNtceNm', 'N/A')}")
                        print(f"  공고번호: {item.get('bidNtceNo', 'N/A')}")
                        print(f"  기관명: {item.get('ntceInsttNm', 'N/A')}")
                        print(f"  공고일: {item.get('bidNtceDate', 'N/A')}")

                        # 문서 URL 분석
                        doc_url = item.get('stdNtceDocUrl', '')
                        if doc_url:
                            print(f"  ✅ 표준문서 URL: {doc_url[:100]}...")

                            # URL 파라미터 분석
                            if '?' in doc_url:
                                params_str = doc_url.split('?')[1]
                                print(f"     URL 파라미터:")
                                for param in params_str.split('&'):
                                    if '=' in param:
                                        key, value = param.split('=', 1)
                                        print(f"       - {key}: {value}")
                        else:
                            print(f"  ❌ 표준문서 URL 없음")

                        # 추가 첨부파일 확인
                        for i in range(1, 11):
                            spec_url = item.get(f'ntceSpecDocUrl{i}', '')
                            spec_name = item.get(f'ntceSpecFileNm{i}', '')
                            if spec_url:
                                print(f"  📎 첨부파일{i}: {spec_name}")
                                print(f"     URL: {spec_url[:80]}...")

                        # 상세페이지 URL
                        detail_url = item.get('bidNtceDtlUrl', '')
                        if detail_url:
                            print(f"  🔗 상세페이지: {detail_url[:80]}...")

                        print()

                    # 통계 요약
                    print("=" * 80)
                    print("📊 통계 요약")
                    print("=" * 80)

                    with_doc_url = sum(1 for item in items if item.get('stdNtceDocUrl'))
                    with_attachments = sum(1 for item in items if any(item.get(f'ntceSpecDocUrl{i}') for i in range(1, 11)))

                    print(f"총 공고: {len(items)}건")
                    print(f"표준문서 URL 있음: {with_doc_url}건 ({with_doc_url/len(items)*100:.1f}%)")
                    print(f"추가 첨부파일 있음: {with_attachments}건 ({with_attachments/len(items)*100:.1f}%)")

                    # 전체 데이터를 JSON으로 저장
                    output_file = f"api_response_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                    with open(output_file, 'w', encoding='utf-8') as f:
                        json.dump(items, f, indent=2, ensure_ascii=False)

                    print(f"\n💾 전체 응답 저장: {output_file}")

                else:
                    print("❌ API 응답에 데이터 없음")
            else:
                print(f"❌ HTTP 오류: {response.status}")


if __name__ == "__main__":
    asyncio.run(test_api())