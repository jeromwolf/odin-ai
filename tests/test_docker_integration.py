#!/usr/bin/env python3
"""
Docker 통합 테스트
tools 디렉토리와 odin-ai 서비스 연동 테스트
"""

import asyncio
import sys
from pathlib import Path
import aiohttp
import time

# 프로젝트 루트를 경로에 추가
sys.path.append(str(Path(__file__).parent.parent))

from backend.services.integrated_document_processor import IntegratedDocumentProcessor


async def test_docker_services_health():
    """Docker 서비스 상태 확인"""
    print("=" * 60)
    print("Docker 서비스 헬스체크")
    print("=" * 60)

    processor = IntegratedDocumentProcessor()
    health = await processor.health_check()

    print(f"\n📊 서비스 상태:")
    print(f"   - HWP 서비스: {'✅' if health['hwp_service'] else '❌'}")
    print(f"   - PDF 서비스: {'✅' if health['pdf_service'] else '❌'}")
    print(f"   - 로컬 프로세서: {'✅' if health['local_processor'] else '❌'}")
    print(f"   - 전체 상태: {'✅ 정상' if health['all_services_healthy'] else '⚠️ 일부 서비스 오프라인'}")

    return health['all_services_healthy']


async def test_hwp_processing_with_docker():
    """HWP 서비스를 통한 문서 처리 테스트"""
    print("\n" + "=" * 60)
    print("HWP Docker 서비스 테스트")
    print("=" * 60)

    processor = IntegratedDocumentProcessor()

    # 테스트 HWP 파일 생성
    test_hwp = Path("storage/downloads/hwp/test_docker.txt")
    test_hwp.parent.mkdir(parents=True, exist_ok=True)

    test_content = """
    도커 통합 테스트 문서

    1. 프로젝트명: Odin-AI Docker 통합
    2. 테스트 일시: 2025년 9월 16일
    3. 추정가격: 50,000,000원
    4. 입찰마감: 2025년 10월 1일

    테스트 내용:
    - HWP 서비스 연동 확인
    - 마크다운 변환 확인
    - 중요 정보 강조 확인
    """

    with open(test_hwp, 'w', encoding='utf-8') as f:
        f.write(test_content)

    # Docker 서비스로 처리
    result = await processor.process_document_enhanced(
        file_path=test_hwp,
        use_docker_service=True
    )

    if result['success']:
        print(f"✅ HWP 처리 성공")
        print(f"   - 처리 방식: {result['processed_by']}")
        print(f"   - 처리 시간: {result['processing_time']:.2f}초")
        print(f"   - 텍스트 길이: {result['text_length']:,}자")
        print(f"   - 마크다운 파일: {result['markdown_file']}")

        # 마크다운 내용 확인
        if result['markdown_file']:
            with open(result['markdown_file'], 'r', encoding='utf-8') as f:
                md_content = f.read()
                if "**추정가격" in md_content or "**50,000,000원**" in md_content:
                    print("   ✅ 중요 정보 강조 확인")
                else:
                    print("   ⚠️ 중요 정보 강조 미적용")
    else:
        print(f"❌ HWP 처리 실패: {result.get('error', '알 수 없는 오류')}")

    return result['success']


async def test_pdf_processing_with_docker():
    """PDF 서비스를 통한 문서 처리 테스트"""
    print("\n" + "=" * 60)
    print("PDF Docker 서비스 테스트")
    print("=" * 60)

    processor = IntegratedDocumentProcessor()

    # 테스트 PDF 파일 생성 (텍스트 파일로 시뮬레이션)
    test_pdf = Path("storage/downloads/pdf/test_docker.txt")
    test_pdf.parent.mkdir(parents=True, exist_ok=True)

    test_content = """
    PDF 도커 통합 테스트

    프로젝트 개요:
    - 사업명: AI 기반 입찰 분석 시스템
    - 예정가격: 100,000,000원
    - 계약방법: 협상에 의한 계약
    - 입찰마감일시: 2025년 10월 15일 17:00

    요구사항:
    1. PDF 문서 처리 기능
    2. 표 데이터 추출
    3. 이미지 OCR 처리
    """

    with open(test_pdf, 'w', encoding='utf-8') as f:
        f.write(test_content)

    # Docker 서비스로 처리
    result = await processor.process_document_enhanced(
        file_path=test_pdf,
        use_docker_service=True
    )

    if result['success']:
        print(f"✅ PDF 처리 성공")
        print(f"   - 처리 방식: {result['processed_by']}")
        print(f"   - 처리 시간: {result['processing_time']:.2f}초")
        print(f"   - 텍스트 길이: {result['text_length']:,}자")
        print(f"   - 마크다운 파일: {result['markdown_file']}")
    else:
        print(f"❌ PDF 처리 실패: {result.get('error', '알 수 없는 오류')}")

    return result['success']


async def test_batch_processing():
    """일괄 처리 테스트"""
    print("\n" + "=" * 60)
    print("일괄 처리 테스트 (Docker 서비스 활용)")
    print("=" * 60)

    processor = IntegratedDocumentProcessor()

    # 테스트 파일들 생성
    test_files = []
    for i in range(3):
        # HWP 파일
        hwp_file = Path(f"storage/downloads/hwp/batch_test_{i}.txt")
        hwp_file.parent.mkdir(parents=True, exist_ok=True)
        with open(hwp_file, 'w', encoding='utf-8') as f:
            f.write(f"HWP 테스트 문서 {i}\n입찰마감: 2025년 10월 {i+1}일")
        test_files.append(hwp_file)

        # PDF 파일
        pdf_file = Path(f"storage/downloads/pdf/batch_test_{i}.txt")
        pdf_file.parent.mkdir(parents=True, exist_ok=True)
        with open(pdf_file, 'w', encoding='utf-8') as f:
            f.write(f"PDF 테스트 문서 {i}\n예정가격: {(i+1)*10000000}원")
        test_files.append(pdf_file)

    print(f"📋 처리할 파일: {len(test_files)}개")

    # 일괄 처리 실행
    start_time = time.time()
    results = await processor.batch_process_with_docker(
        file_paths=test_files,
        max_concurrent=3
    )
    total_time = time.time() - start_time

    print(f"\n📊 처리 결과:")
    print(f"   - 성공: {results['successful']}/{results['total']}")
    print(f"   - 실패: {results['failed']}")
    print(f"   - Docker 처리: {results['docker_processed']}")
    print(f"   - 로컬 처리: {results['local_processed']}")
    print(f"   - 총 처리 시간: {total_time:.2f}초")
    print(f"   - 평균 처리 시간: {results['statistics']['avg_processing_time']:.2f}초")
    print(f"   - 성공률: {results['statistics']['success_rate']:.1f}%")
    print(f"   - Docker 서비스 사용률: {results['statistics']['docker_service_rate']:.1f}%")

    return results['successful'] > 0


async def test_fallback_mechanism():
    """Docker 서비스 실패시 로컬 폴백 테스트"""
    print("\n" + "=" * 60)
    print("폴백 메커니즘 테스트")
    print("=" * 60)

    processor = IntegratedDocumentProcessor()

    # 잘못된 서비스 URL로 설정하여 폴백 테스트
    original_hwp_url = processor.hwp_service_url
    processor.hwp_service_url = "http://invalid-service:9999"

    test_file = Path("storage/downloads/hwp/fallback_test.txt")
    test_file.parent.mkdir(parents=True, exist_ok=True)
    with open(test_file, 'w', encoding='utf-8') as f:
        f.write("폴백 테스트 문서\n입찰마감: 2025년 12월 31일")

    # 처리 시도 (폴백으로 로컬 처리 예상)
    result = await processor.process_document_enhanced(
        file_path=test_file,
        use_docker_service=True
    )

    if result['success']:
        print(f"✅ 폴백 처리 성공")
        print(f"   - 처리 방식: {result['processed_by']}")
        if result['processed_by'] == 'local':
            print("   ✅ 로컬 폴백 동작 확인")
        else:
            print("   ⚠️ 예상치 않은 처리 방식")
    else:
        print(f"❌ 폴백 처리 실패: {result.get('error', '알 수 없는 오류')}")

    # 원래 설정 복구
    processor.hwp_service_url = original_hwp_url

    return result['success']


async def main():
    """통합 테스트 메인"""
    print("🚀 Docker 통합 테스트 시작\n")

    tests = [
        ("Docker 서비스 헬스체크", test_docker_services_health),
        ("HWP Docker 서비스", test_hwp_processing_with_docker),
        ("PDF Docker 서비스", test_pdf_processing_with_docker),
        ("일괄 처리", test_batch_processing),
        ("폴백 메커니즘", test_fallback_mechanism),
    ]

    results = []
    for name, test_func in tests:
        try:
            result = await test_func()
            results.append((name, result))
        except Exception as e:
            print(f"❌ {name} 실행 중 오류: {e}")
            results.append((name, False))

    # 결과 요약
    print(f"\n{'='*60}")
    print("🏁 Docker 통합 테스트 결과 요약")
    print(f"{'='*60}")

    success_count = 0
    for name, result in results:
        if result:
            print(f"✅ {name}: 성공")
            success_count += 1
        else:
            print(f"❌ {name}: 실패")

    print(f"\n📊 총 {len(results)}개 테스트 중 {success_count}개 성공")

    if success_count == len(results):
        print("🎉 모든 Docker 통합 테스트 통과!")
        print("\n💡 다음 단계:")
        print("   1. git add -A")
        print("   2. git commit -m 'feat: Docker 통합 완료 - tools 디렉토리 통합'")
        print("   3. git push")
        return 0
    else:
        print(f"⚠️ {len(results) - success_count}개 테스트 실패")
        print("\n💡 Docker 서비스 확인:")
        print("   ./scripts/manage-docker.sh status")
        print("   ./scripts/manage-docker.sh logs hwp-viewer")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)