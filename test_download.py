#!/usr/bin/env python3
"""
실제 입찰공고 문서 다운로드 테스트
"""

import asyncio
from backend.services.public_data_client import public_data_client
from backend.services.document_processor import DocumentProcessor
from datetime import datetime, timedelta

async def test_real_download():
    """실제 문서 다운로드 테스트"""

    print("=" * 60)
    print("실제 입찰공고 문서 다운로드 테스트")
    print("=" * 60)

    # 1. 최근 입찰공고 조회
    print("\n1. 최근 입찰공고 조회 중...")

    try:
        # 최근 7일간 입찰공고 검색
        response = await public_data_client.get_bid_construction_list(
            page=1,
            size=5,
            inquiry_div="1",
            start_date="202509100000",
            end_date="202509162359"
        )

        if response.get("items"):
            print(f"✅ {len(response['items'])}건의 입찰공고 발견")

            # 첫 번째 공고 정보 출력
            for i, item in enumerate(response['items'][:3], 1):
                print(f"\n[{i}] 공고명: {item.get('bidNtceNm', 'N/A')}")
                print(f"    공고번호: {item.get('bidNtceNo', 'N/A')}")
                print(f"    기관: {item.get('ntceInsttNm', 'N/A')}")

                # 문서 URL이 있는지 확인 (실제 API 응답에는 없을 수 있음)
                if item.get('bidNtceUrl'):
                    print(f"    문서 URL: {item['bidNtceUrl']}")
        else:
            print("❌ 입찰공고를 찾을 수 없습니다")

    except Exception as e:
        print(f"❌ API 호출 실패: {e}")

    # 2. 샘플 문서 다운로드 테스트
    print("\n" + "=" * 60)
    print("2. 샘플 문서 다운로드 테스트")
    print("=" * 60)

    # 공공기관 샘플 문서 URL (실제 접근 가능한 예시)
    sample_urls = [
        # 예시: 국가계약법령집 PDF
        "https://www.law.go.kr/fileDownload.do?seq=33953&gubun=lsfile",
        # 더 많은 공개 문서 URL을 추가할 수 있습니다
    ]

    processor = DocumentProcessor()

    for url in sample_urls[:1]:  # 첫 번째 URL만 테스트
        print(f"\n다운로드 시도: {url[:50]}...")

        try:
            result = await processor.download_document(url)

            if result["success"]:
                print(f"✅ 다운로드 성공!")
                print(f"   - 파일명: {result.get('filename', 'N/A')}")
                print(f"   - 파일 타입: {result.get('file_type', 'N/A')}")
                print(f"   - 저장 경로: {result.get('save_path', 'N/A')}")

                # 텍스트 추출 시도
                if result.get('text_length', 0) > 0:
                    print(f"   - 추출된 텍스트: {result['text_length']}자")
            else:
                print(f"❌ 다운로드 실패: {result.get('error', '알 수 없는 오류')}")

        except Exception as e:
            print(f"❌ 처리 중 오류: {e}")

    # 3. 나라장터 공개 문서 확인
    print("\n" + "=" * 60)
    print("3. 다운로드 가능한 문서 유형")
    print("=" * 60)

    print("""
    현재 다운로드 가능한 문서:
    1. 공개된 입찰공고 첨부파일
    2. 사전규격 공개 문서
    3. 낙찰 결과 공개 문서

    주의사항:
    - 로그인이 필요한 문서는 다운로드 불가
    - robots.txt 및 이용약관 준수 필요
    - 과도한 요청 방지를 위한 딜레이 적용
    """)

    # 4. 현재 저장된 파일 통계
    print("\n" + "=" * 60)
    print("4. 현재 저장된 파일 통계")
    print("=" * 60)

    from pathlib import Path

    storage_path = Path("storage/downloads")
    for file_type in ["hwp", "pdf", "doc"]:
        type_path = storage_path / file_type
        if type_path.exists():
            files = list(type_path.glob("*"))
            print(f"   - {file_type.upper()}: {len(files)}개")

    processed_path = Path("storage/processed")
    for file_type in ["hwp", "pdf", "doc"]:
        type_path = processed_path / file_type
        if type_path.exists():
            files = list(type_path.glob("*.md"))
            print(f"   - {file_type.upper()} (처리됨): {len(files)}개")

if __name__ == "__main__":
    asyncio.run(test_real_download())