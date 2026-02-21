#!/usr/bin/env python3
"""
공공데이터포털 API 기능 분석
- 키워드 검색 가능성 확인
- 응답 데이터 구조 분석
- Odin-AI 작업 처리 가능성 검토
"""

import asyncio
import sys
from datetime import datetime, timedelta

sys.path.append('/Users/blockmeta/Desktop/blockmeta/project/odin-ai')
from backend.services.public_data_client import PublicDataAPIClient

def analyze_api_capabilities():
    """API 기능 분석"""
    print("=" * 80)
    print("📊 공공데이터포털 나라장터 API 기능 분석")
    print("=" * 80)

    print("""
🔍 **1. 키워드 검색 기능 분석**

❌ **API 자체적 키워드 검색 불가능**
- API는 '기간 기반 조회'만 지원 (inqryBgnDt ~ inqryEndDt)
- 공고명, 기관명, 내용 등에 대한 직접 키워드 필터 파라미터 없음
- 모든 데이터를 가져온 후 '후처리 필터링' 필요

✅ **대안: 클라이언트 사이드 필터링**
- API로 기간별 전체 데이터 수집
- 응답 데이터에서 bidNm(공고명) 필드로 키워드 필터링
- 예: '데이터분석' 키워드 포함 공고만 추출

📅 **기간 설정 제약**
- 필수 파라미터: inqryBgnDt, inqryEndDt
- 형식: YYYYMMDDHHMM (예: 202501010000)
- 너무 넓은 범위 시 "입력범위값 초과" 에러 발생
- 권장: 최대 30일 이내 범위

💡 **검색 전략**:
1. 기간을 청크 단위로 나누어 순차 조회 (예: 7일씩)
2. 각 응답에서 키워드 매칭 항목 추출
3. 결과를 통합하여 사용자에게 제공
""")

    print("""
🗃️ **2. API 응답 데이터 구조 분석**

**기본 구조:**
```json
{
  "success": true,
  "total_count": 150,
  "items": [
    {
      "bidNtceNo": "20250001001",        // 공고번호
      "bidNm": "데이터분석 시스템 구축",    // 공고명 ⭐ 키워드 검색 대상
      "ntceInsttNm": "서울특별시",         // 공고기관명
      "bidBeginDt": "202501010900",      // 입찰시작일시
      "bidClseDt": "202501101700",       // 입찰마감일시 ⭐ 중요
      "bidNtceUrl": "https://...",       // 공고URL ⭐ 매우 중요!
      "dminsttNm": "서울시청",            // 수요기관명
      "cntrctCnclsMethod": "일반경쟁",     // 계약방법
      "bidQlfctRgstDt": "...",          // 입찰참가자격등록마감일시
      // ... 기타 20여개 필드
    }
  ]
}
```

**핵심 활용 필드:**
- `bidNm`: 공고명 → 키워드 필터링
- `bidNtceUrl`: 공고URL → 상세 문서 다운로드 ⭐
- `bidClseDt`: 마감일시 → 알림 스케줄링
- `ntceInsttNm`: 발주기관 → 기관별 분석
""")

    print("""
🚀 **3. Odin-AI 작업 처리 가능성**

✅ **완전히 가능한 작업들:**

**1) 키워드 기반 공고 검색**
- API로 기간별 데이터 수집 → 클라이언트에서 키워드 필터링
- 예: '데이터분석', 'AI', '인공지능', '시스템' 등

**2) 입찰공고 문서 다운로드**
- bidNtceUrl 필드에서 나라장터 상세 페이지 URL 제공
- Selenium으로 해당 URL 접속 → 첨부파일 다운로드 가능

**3) 마감임박 알림**
- bidClseDt(마감일시) 기준으로 D-3, D-1, D-Day 알림 가능
- 사용자별 관심 키워드 공고 추적

**4) 발주기관 분석**
- ntceInsttNm으로 기관별 입찰 패턴 분석
- 특정 기관의 주요 사업 유형 파악

**5) 경쟁률 예측**
- 과거 유사 공고 데이터로 AI 모델 학습
- 성공 확률 예측 서비스

⚠️ **제약 사항:**

**1) 실시간 검색 불가**
- API 호출 후 필터링이므로 약간의 지연 발생
- Rate Limit: 시간당 800건 → 4.5초당 1건

**2) 전체 문서 내용 검색 불가**
- API는 메타데이터만 제공
- 첨부파일 내용 검색은 다운로드 후 별도 처리

**3) 날짜 범위 제한**
- 한 번에 너무 넓은 범위 조회 시 에러
- 점진적 수집 전략 필요
""")

async def demonstrate_workflow():
    """실제 워크플로우 시연"""
    print("""
🔄 **4. 실제 워크플로우 시연**

**시나리오: '데이터분석' 관련 공고 검색 및 알림**
""")

    try:
        client = PublicDataAPIClient()

        print("1️⃣ 최근 30일 공고 데이터 수집...")

        # 실제로는 7일씩 나누어 호출해야 함
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)  # 일단 7일로 제한

        # 파라미터를 올바른 메서드 시그니처에 맞게 수정
        result = await client.get_bid_construction_list(
            page=1,
            size=10,
            inquiry_div="1",
            start_date=start_date.strftime("%Y%m%d") + "0000",
            end_date=end_date.strftime("%Y%m%d") + "2359"
        )

        if result.get('success'):
            print("✅ API 호출 성공!")

            # raw_data에서 items 추출 시도
            items = []
            if 'items' in result:
                items = result['items']
            elif 'raw_data' in result and 'response' in result['raw_data']:
                response_data = result['raw_data']['response']
                if 'body' in response_data and 'items' in response_data['body']:
                    items = response_data['body']['items']

            if items:
                print(f"2️⃣ {len(items)}건 공고 데이터 수집")

                # 키워드 필터링
                keywords = ['데이터', '분석', 'AI', '인공지능', '시스템']
                matched_items = []

                for item in items:
                    bid_name = item.get('bidNm', '')
                    for keyword in keywords:
                        if keyword in bid_name:
                            matched_items.append((item, keyword))
                            break

                if matched_items:
                    print(f"3️⃣ 키워드 매칭 공고 {len(matched_items)}건 발견!")

                    for i, (item, keyword) in enumerate(matched_items[:3], 1):
                        print(f"\n   [{i}] 키워드: '{keyword}'")
                        print(f"       공고명: {item.get('bidNm', 'N/A')[:80]}...")
                        print(f"       마감일: {item.get('bidClseDt', 'N/A')}")

                        url = item.get('bidNtceUrl', '')
                        if url:
                            print(f"       📎 상세URL: 제공됨 (길이: {len(url)})")
                            print(f"       🔄 → Selenium으로 파일 다운로드 가능")
                        else:
                            print(f"       ❌ 상세URL 없음")

                    print(f"\n4️⃣ 후속 처리 가능:")
                    print(f"   - 각 URL로 Selenium 크롤링하여 첨부파일 다운로드")
                    print(f"   - HWP/PDF 문서 AI 분석")
                    print(f"   - 마감일 기준 알림 스케줄링")
                    print(f"   - 사용자 맞춤 공고 추천")

                else:
                    print("3️⃣ 키워드 매칭 공고 없음")
            else:
                print("2️⃣ items 데이터 없음 - API 응답 구조 확인 필요")
                if 'raw_data' in result:
                    print(f"   raw_data 키: {list(result['raw_data'].keys())}")

        else:
            print("❌ API 호출 실패")

    except Exception as e:
        print(f"❌ 워크플로우 시연 오류: {e}")

async def main():
    """메인 실행"""
    analyze_api_capabilities()
    await demonstrate_workflow()

    print(f"\n{'='*80}")
    print("📋 **결론: API 활용 전략**")
    print("""
✅ **권장 접근법:**
1. 기간별 배치 수집 (매일 또는 주간)
2. 클라이언트 키워드 필터링
3. bidNtceUrl로 Selenium 크롤링
4. 첨부파일 다운로드 및 AI 분석

⚡ **실시간성:**
- API 수집: 준실시간 (시간 지연 있음)
- Selenium 크롤링: 실시간 가능
- 하이브리드 접근으로 최적화

🎯 **Odin-AI 완성도:**
현재 구조로도 충분히 서비스 구현 가능!
""")
    print("=" * 80)

if __name__ == "__main__":
    asyncio.run(main())