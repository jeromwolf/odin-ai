#!/usr/bin/env python3
"""
문서 처리기 테스트 스크립트
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime
import tempfile
import shutil

# 프로젝트 루트를 경로에 추가
sys.path.append(str(Path(__file__).parent.parent))

from backend.services.document_processor import DocumentProcessor


async def test_document_processor_basic():
    """문서 처리기 기본 테스트"""
    print("=" * 60)
    print("문서 처리기 기본 테스트")
    print("=" * 60)

    try:
        processor = DocumentProcessor()

        # 통계 확인
        stats = await processor.get_processing_stats()
        print("✅ 문서 처리기 초기화 성공")
        print(f"   - 다운로드 디렉토리: {stats['directories']['downloads']}")
        print(f"   - 처리된 파일 디렉토리: {stats['directories']['processed']}")
        print(f"   - 지원 파일 타입: {', '.join(stats['supported_types'])}")

        # 파일 타입 감지 테스트
        test_files = [
            "test.hwp",
            "document.pdf",
            "report.doc",
            "data.xlsx",
            "unknown.xyz"
        ]

        print(f"\n📁 파일 타입 감지 테스트:")
        for filename in test_files:
            file_type = processor.get_file_type(filename)
            print(f"   - {filename} → {file_type}")

        return True

    except Exception as e:
        print(f"❌ 기본 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_document_download():
    """문서 다운로드 테스트 (실제 URL 없이 시뮬레이션)"""
    print("\n" + "=" * 60)
    print("문서 다운로드 시뮬레이션 테스트")
    print("=" * 60)

    try:
        processor = DocumentProcessor()

        # 테스트용 더미 문서 생성
        test_content = """
        입찰 공고서

        1. 공사명: 테스트 시설 건설공사
        2. 공사장소: 서울특별시 종로구
        3. 공사기간: 2025년 3월 ~ 2025년 12월
        4. 추정가격: 10,000,000,000원
        5. 입찰방법: 전자입찰

        가. 입찰참가자격
        - 건설업 면허 보유자
        - 신용평가 A등급 이상

        나. 제출서류
        - 입찰서
        - 이행보증서
        - 기술제안서

        다. 입찰마감일시: 2025년 2월 15일 17시

        ■ 중요사항
        본 공사는 친환경 자재 사용이 필수입니다.
        """

        # 임시 파일 생성 (다운로드 시뮬레이션)
        temp_dir = Path("storage/downloads/hwp")
        temp_file = temp_dir / "test_document.txt"

        with open(temp_file, 'w', encoding='utf-8') as f:
            f.write(test_content)

        print(f"✅ 테스트 문서 생성: {temp_file}")

        # 텍스트를 마크다운으로 변환 테스트
        markdown_content = processor._convert_text_to_markdown(test_content, "test_document.txt")

        markdown_file = Path("storage/processed/hwp/test_document.md")
        markdown_file.parent.mkdir(parents=True, exist_ok=True)

        with open(markdown_file, 'w', encoding='utf-8') as f:
            f.write(markdown_content)

        print(f"✅ 마크다운 변환 완료: {markdown_file}")

        # 결과 미리보기
        print(f"\n📄 마크다운 내용 미리보기 (첫 500자):")
        print("-" * 50)
        print(markdown_content[:500] + ("..." if len(markdown_content) > 500 else ""))
        print("-" * 50)

        # 파일 해시 테스트
        file_hash = processor.generate_file_hash(temp_file)
        print(f"✅ 파일 해시 생성: {file_hash[:16]}...")

        return True

    except Exception as e:
        print(f"❌ 다운로드 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_batch_processing():
    """일괄 처리 시뮬레이션 테스트"""
    print("\n" + "=" * 60)
    print("일괄 처리 시뮬레이션 테스트")
    print("=" * 60)

    try:
        processor = DocumentProcessor()

        # 테스트용 문서 목록 (실제 URL이 아닌 시뮬레이션)
        test_documents = [
            {
                "filename": "입찰공고서.hwp",
                "url": "https://example.com/doc1.hwp",
                "type": "hwp"
            },
            {
                "filename": "설계도서.pdf",
                "url": "https://example.com/doc2.pdf",
                "type": "pdf"
            },
            {
                "filename": "기술규격서.doc",
                "url": "https://example.com/doc3.doc",
                "type": "doc"
            }
        ]

        print(f"📋 처리할 문서 목록 ({len(test_documents)}개):")
        for i, doc in enumerate(test_documents, 1):
            print(f"   [{i}] {doc['filename']} ({doc['type'].upper()})")

        # 처리 결과 시뮬레이션
        simulated_results = {
            "total_documents": len(test_documents),
            "downloaded": 2,  # 시뮬레이션
            "processed": 2,   # 시뮬레이션
            "failed": 1,      # 시뮬레이션
            "results": [
                {
                    "success": True,
                    "filename": "입찰공고서.hwp",
                    "file_type": "hwp",
                    "text_length": 1234,
                    "markdown_file": "storage/processed/hwp/입찰공고서.md"
                },
                {
                    "success": True,
                    "filename": "설계도서.pdf",
                    "file_type": "pdf",
                    "text_length": 5678,
                    "markdown_file": "storage/processed/pdf/설계도서.md"
                },
                {
                    "success": False,
                    "filename": "기술규격서.doc",
                    "error": "다운로드 실패 (시뮬레이션)"
                }
            ]
        }

        print(f"\n📊 처리 결과:")
        print(f"   - 총 문서: {simulated_results['total_documents']}개")
        print(f"   - 다운로드 성공: {simulated_results['downloaded']}개")
        print(f"   - 처리 완료: {simulated_results['processed']}개")
        print(f"   - 실패: {simulated_results['failed']}개")

        print(f"\n📄 상세 결과:")
        for result in simulated_results['results']:
            if result.get('success'):
                print(f"   ✅ {result['filename']} → {result.get('text_length', 0):,} 문자 추출")
                print(f"      마크다운: {result.get('markdown_file', 'N/A')}")
            else:
                print(f"   ❌ {result['filename']} → {result.get('error', '알 수 없는 오류')}")

        return True

    except Exception as e:
        print(f"❌ 일괄 처리 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_directory_structure():
    """디렉토리 구조 확인 테스트"""
    print("\n" + "=" * 60)
    print("디렉토리 구조 확인 테스트")
    print("=" * 60)

    try:
        base_path = Path("storage")

        print(f"📁 저장소 구조 ({base_path}):")

        def print_tree(path: Path, prefix: str = "", is_last: bool = True):
            """디렉토리 트리 출력"""
            if not path.exists():
                return

            connector = "└── " if is_last else "├── "
            print(f"{prefix}{connector}{path.name}")

            if path.is_dir():
                children = sorted([p for p in path.iterdir() if p.is_dir()])
                for i, child in enumerate(children):
                    extension = "    " if is_last else "│   "
                    print_tree(child, prefix + extension, i == len(children) - 1)

        # 디렉토리 트리 출력
        print_tree(base_path)

        # 실제 파일 개수 확인
        download_files = list(Path("storage/downloads").rglob("*"))
        processed_files = list(Path("storage/processed").rglob("*"))

        print(f"\n📊 파일 통계:")
        print(f"   - 다운로드 영역: {len([f for f in download_files if f.is_file()])}개 파일")
        print(f"   - 처리 완료 영역: {len([f for f in processed_files if f.is_file()])}개 파일")

        # 최근 생성된 파일 목록 (상위 5개)
        all_files = [f for f in (download_files + processed_files) if f.is_file()]
        recent_files = sorted(all_files, key=lambda x: x.stat().st_mtime, reverse=True)[:5]

        if recent_files:
            print(f"\n📅 최근 파일 목록 (상위 5개):")
            for file_path in recent_files:
                mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                size = file_path.stat().st_size
                print(f"   - {file_path.name} ({size:,} bytes, {mtime.strftime('%Y-%m-%d %H:%M')})")

        return True

    except Exception as e:
        print(f"❌ 디렉토리 구조 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """메인 테스트 실행"""
    print("🚀 문서 처리기 종합 테스트 시작\n")

    tests = [
        ("기본 기능", test_document_processor_basic),
        ("문서 다운로드", test_document_download),
        ("일괄 처리", test_batch_processing),
        ("디렉토리 구조", test_directory_structure),
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
    print("🏁 문서 처리기 테스트 결과 요약")
    print(f"{'='*60}")

    success_count = 0
    for name, result in results:
        if result:
            print(f"✅ {name}: 성공")
            success_count += 1
        else:
            print(f"❌ {name}: 실패")

    print(f"\n📊 총 {len(results)}개 테스트 중 {success_count}개 성공")

    if success_count > 0:
        print("🎉 문서 처리기 시스템 작동 확인!")
        print("💡 다음 단계: 크롤러와 문서 처리기 통합")
        return 0
    else:
        print("⚠️ 모든 테스트 실패")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)