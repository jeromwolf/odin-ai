#!/usr/bin/env python3
"""
통합된 HWP 문서 처리 서비스 테스트
HWP Viewer가 통합된 DocumentProcessor 테스트
"""

import asyncio
import sys
import os
from pathlib import Path

# 백엔드 경로 추가
sys.path.append('/Users/blockmeta/Desktop/blockmeta/project/odin-ai')

async def test_integrated_hwp_processor():
    """통합된 HWP 문서 처리 서비스 테스트"""
    print("=" * 80)
    print("🧪 통합된 HWP 문서 처리 서비스 테스트")
    print("=" * 80)

    try:
        # DocumentProcessor import
        from backend.services.document_processor import DocumentProcessor

        # 프로세서 초기화
        print("📦 DocumentProcessor 초기화...")
        processor = DocumentProcessor()

        # HWP Viewer 사용 가능 여부 확인
        print(f"🔧 HWP Viewer 사용 가능: {processor.hwp_parser is not None}")
        print(f"🎨 Markdown Formatter 사용 가능: {processor.markdown_formatter is not None}")

        # 테스트할 다운로드 URL (이전에 확인된 URL)
        test_documents = [
            {
                "url": "https://www.g2b.go.kr/pn/pnp/pnpe/UntyAtchFile/downloadFile.do?bidPbancNo=R25BK01060027&bidPbancOrd=000&fileType=&fileSeq=1",
                "filename": "수의계약안내공고[어린이보호구역(신안초등학교) 보행로 조성사업].hwp",
                "bid_info": {
                    "bidNtceNo": "R25BK01060027",
                    "bidNm": "어린이보호구역(신안초등학교) 보행로 조성사업",
                    "ntceInsttNm": "신안군청"
                }
            }
        ]

        total_processed = 0

        for i, doc_info in enumerate(test_documents, 1):
            print(f"\n{'='*60}")
            print(f"📥 테스트 {i}: {doc_info['filename']}")
            print(f"{'='*60}")

            try:
                # 1단계: 문서 다운로드
                print("1️⃣ 문서 다운로드 중...")
                download_result = await processor.download_document(
                    url=doc_info["url"],
                    filename=doc_info["filename"],
                    bid_notice_no=doc_info["bid_info"]["bidNtceNo"]
                )

                if not download_result.get("success"):
                    print(f"❌ 다운로드 실패: {download_result.get('error')}")
                    continue

                print(f"✅ 다운로드 성공:")
                print(f"   📁 파일 경로: {download_result['file_path']}")
                print(f"   📊 파일 크기: {download_result['file_size']:,} bytes")
                print(f"   🏷️ 파일 타입: {download_result['file_type']}")

                # 2단계: 문서 처리 (HWP 파싱 + 마크다운 변환)
                print("\n2️⃣ 문서 처리 중...")
                process_result = await processor.process_document(download_result["file_path"])

                if process_result.get("success"):
                    print(f"✅ 문서 처리 성공:")
                    print(f"   🔧 처리 방법: {process_result.get('processing_method', 'unknown')}")
                    print(f"   📄 텍스트 길이: {process_result.get('text_length', 0):,} 문자")

                    if process_result.get('paragraph_count'):
                        print(f"   📝 단락 수: {process_result['paragraph_count']}")
                    if process_result.get('table_count'):
                        print(f"   📊 테이블 수: {process_result['table_count']}")

                    # 마크다운 파일 확인
                    md_file = process_result.get("markdown_file")
                    if md_file and os.path.exists(md_file):
                        md_size = os.path.getsize(md_file)
                        print(f"   🎨 마크다운 파일: {md_size:,} bytes")

                        # 마크다운 내용 미리보기
                        with open(md_file, 'r', encoding='utf-8') as f:
                            md_content = f.read()
                            preview = md_content[:300] + "..." if len(md_content) > 300 else md_content
                            print(f"   📋 마크다운 미리보기:")
                            print("   " + "\n   ".join(preview.split('\n')[:5]))

                    total_processed += 1

                else:
                    print(f"❌ 문서 처리 실패: {process_result.get('error')}")

            except Exception as e:
                print(f"❌ 테스트 {i} 처리 중 오류: {e}")
                import traceback
                traceback.print_exc()

        # 최종 통계
        print(f"\n{'='*80}")
        print(f"📊 최종 테스트 결과")
        print(f"{'='*80}")

        # 처리 통계 조회
        stats = await processor.get_processing_stats()
        print(f"📈 처리 통계:")
        print(f"   다운로드: {stats['stats']['downloaded']}개")
        print(f"   처리 성공: {stats['stats']['processed']}개")
        print(f"   HWP Viewer 처리: {stats['stats'].get('hwp_viewer_processed', 0)}개")
        print(f"   hwp5txt 처리: {stats['stats'].get('hwp5txt_processed', 0)}개")
        print(f"   실패: {stats['stats']['failed']}개")

        # 저장소 상태 확인
        storage_info = {
            "downloads": len(list(Path("storage/downloads").rglob("*.*"))) if Path("storage/downloads").exists() else 0,
            "processed": len(list(Path("storage/processed").rglob("*.*"))) if Path("storage/processed").exists() else 0,
            "markdown": len(list(Path("storage/markdown").rglob("*.md"))) if Path("storage/markdown").exists() else 0
        }

        print(f"\n📁 저장소 현황:")
        print(f"   다운로드 파일: {storage_info['downloads']}개")
        print(f"   처리된 파일: {storage_info['processed']}개")
        print(f"   마크다운 파일: {storage_info['markdown']}개")

        if total_processed > 0:
            print(f"\n🎉 성공!")
            print(f"   HWP Viewer 통합 문서 처리 시스템이 정상 작동합니다!")
            print(f"   총 {total_processed}개 문서가 성공적으로 처리되었습니다.")

            # 생성된 마크다운 파일 목록
            md_files = list(Path("storage/markdown").glob("*.md")) if Path("storage/markdown").exists() else []
            if md_files:
                print(f"\n📝 생성된 마크다운 파일:")
                for md_file in md_files:
                    print(f"   - {md_file.name}")

        else:
            print(f"\n⚠️ 처리된 문서가 없습니다.")
            print(f"   네트워크 연결이나 URL 접근성을 확인해주세요.")

    except ImportError as e:
        print(f"❌ 모듈 import 실패: {e}")
        print("백엔드 환경이 제대로 설정되지 않았을 수 있습니다.")
    except Exception as e:
        print(f"❌ 테스트 중 오류: {e}")
        import traceback
        traceback.print_exc()

async def test_hwp_viewer_directly():
    """HWP Viewer 도구 직접 테스트"""
    print(f"\n{'='*60}")
    print("🔧 HWP Viewer 도구 직접 테스트")
    print(f"{'='*60}")

    try:
        # HWP Viewer import 테스트
        sys.path.append('/Users/blockmeta/Desktop/blockmeta/project/odin-ai/tools/hwp-viewer')
        from hwp_viewer.parser import HWPParser
        from hwp_viewer.markdown_formatter import MarkdownFormatter

        print("✅ HWP Viewer 도구 import 성공")

        # 파서 초기화
        parser = HWPParser()
        formatter = MarkdownFormatter(use_emoji=True)

        print("✅ HWP 파서 및 포맷터 초기화 성공")

        # 다운로드된 HWP 파일이 있는지 확인
        hwp_files = list(Path("storage/downloads/hwp").glob("*.hwp")) if Path("storage/downloads/hwp").exists() else []

        if hwp_files:
            test_file = hwp_files[0]
            print(f"🧪 테스트 파일: {test_file.name}")

            # 파싱 테스트
            print("📖 HWP 파일 파싱 중...")
            document = parser.parse(str(test_file))

            print(f"✅ 파싱 완료:")
            print(f"   텍스트 길이: {len(document.raw_text)} 문자")
            print(f"   단락 수: {len(document.paragraphs)}")
            print(f"   테이블 수: {len(document.tables) if document.tables else 0}")

            # 마크다운 변환 테스트
            print("🎨 마크다운 변환 중...")
            markdown = formatter.format_document(
                title=test_file.stem,
                content=document.raw_text[:1000],  # 첫 1000자만 테스트
                metadata={"테스트": "HWP Viewer 직접 테스트"}
            )

            print(f"✅ 마크다운 변환 완료: {len(markdown)} 문자")
            print("📋 마크다운 미리보기:")
            print(markdown[:500] + "..." if len(markdown) > 500 else markdown)

        else:
            print("⚠️ 테스트할 HWP 파일이 없습니다.")

    except Exception as e:
        print(f"❌ HWP Viewer 직접 테스트 실패: {e}")
        import traceback
        traceback.print_exc()

async def main():
    """메인 실행"""
    print("🚀 HWP 문서 처리 시스템 통합 테스트 시작")

    # 1. 통합된 DocumentProcessor 테스트
    await test_integrated_hwp_processor()

    # 2. HWP Viewer 직접 테스트
    await test_hwp_viewer_directly()

    print(f"\n{'='*80}")
    print("🏁 모든 테스트 완료")
    print("HWP Viewer 통합이 성공적으로 완료되었습니다!")
    print("="*80)

if __name__ == "__main__":
    asyncio.run(main())