"""
문서 처리 서비스: HWP → 마크다운 변환 + 데이터베이스 저장
"""

import os
import sys
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any
from loguru import logger

# HWP Viewer 도구 추가
hwp_viewer_path = Path(__file__).parent.parent.parent / "tools" / "hwp-viewer"
sys.path.insert(0, str(hwp_viewer_path))

from shared.config import settings, get_storage_path
from shared.database import get_db_context
from shared.models import BidAnnouncement, BidDocument


class DocumentProcessor:
    """문서 처리기: HWP → 마크다운 변환 및 저장"""

    def __init__(self):
        self.markdown_storage = get_storage_path("markdown")
        self.processed_files = set()

        # 마크다운 저장 폴더 생성
        self.markdown_storage.mkdir(parents=True, exist_ok=True)

    async def process_downloaded_files(self, download_dir: Path) -> Dict[str, Any]:
        """
        다운로드된 파일들을 마크다운으로 변환하고 데이터베이스에 저장

        Args:
            download_dir: 다운로드된 파일들이 있는 디렉토리

        Returns:
            처리 결과 딕셔너리
        """

        result = {
            "total_files": 0,
            "processed_files": 0,
            "markdown_files": 0,
            "db_updates": 0,
            "errors": [],
            "processing_details": []
        }

        if not download_dir.exists():
            logger.warning(f"다운로드 디렉토리가 존재하지 않음: {download_dir}")
            return result

        # 다운로드된 HWP/HWPX 파일 목록
        hwp_files = list(download_dir.glob("*.hwp")) + list(download_dir.glob("*.hwpx"))
        result["total_files"] = len(hwp_files)

        logger.info(f"📝 문서 처리 시작: {len(hwp_files)}개 파일")

        for hwp_file in hwp_files:
            try:
                logger.info(f"🔄 처리 중: {hwp_file.name}")

                # 1. HWP → 마크다운 변환
                markdown_result = await self._convert_hwp_to_markdown(hwp_file)

                if markdown_result["success"]:
                    result["processed_files"] += 1
                    result["markdown_files"] += 1

                    # 2. 데이터베이스 업데이트
                    db_result = await self._update_database_with_markdown(
                        hwp_file, markdown_result
                    )

                    if db_result["success"]:
                        result["db_updates"] += 1

                    # 처리 상세 정보 기록
                    detail = {
                        "file_name": hwp_file.name,
                        "file_size": hwp_file.stat().st_size,
                        "markdown_file": markdown_result.get("markdown_file"),
                        "text_length": markdown_result.get("text_length", 0),
                        "db_updated": db_result["success"],
                        "processing_time": markdown_result.get("processing_time", 0)
                    }
                    result["processing_details"].append(detail)

                    logger.info(f"✅ 완료: {hwp_file.name} → {markdown_result.get('text_length', 0):,}자")

                else:
                    error_info = {
                        "file": hwp_file.name,
                        "error": markdown_result.get("error", "변환 실패")
                    }
                    result["errors"].append(error_info)
                    logger.error(f"❌ 변환 실패: {hwp_file.name}")

            except Exception as e:
                error_info = {
                    "file": hwp_file.name,
                    "error": str(e)
                }
                result["errors"].append(error_info)
                logger.error(f"❌ 처리 오류: {hwp_file.name} - {e}")

        logger.info(f"📊 문서 처리 완료: {result['processed_files']}/{result['total_files']} 성공")
        return result

    async def _convert_hwp_to_markdown(self, hwp_file: Path) -> Dict[str, Any]:
        """HWP 파일을 마크다운으로 변환"""

        result = {
            "success": False,
            "markdown_file": None,
            "text_length": 0,
            "processing_time": 0,
            "error": None
        }

        start_time = datetime.now()

        try:
            # HWP 파일에서 텍스트 추출
            from hwp_viewer import TextExtractor

            logger.info(f"🔧 HWP 텍스트 추출: {hwp_file.name}")
            extractor = TextExtractor()
            extracted_text = extractor.extract_all(str(hwp_file))

            if not extracted_text or len(extracted_text.strip()) == 0:
                result["error"] = "텍스트 추출 실패 또는 빈 내용"
                return result

            # 마크다운 파일명 생성 (해시 기반)
            file_hash = hashlib.md5(hwp_file.name.encode()).hexdigest()[:8]
            safe_filename = self._safe_filename(hwp_file.stem)
            markdown_filename = f"{safe_filename}_{file_hash}.md"
            markdown_path = self.markdown_storage / markdown_filename

            # 마크다운 변환 및 저장
            markdown_content = self._convert_to_markdown(extracted_text, hwp_file)

            with open(markdown_path, 'w', encoding='utf-8') as f:
                f.write(markdown_content)

            result.update({
                "success": True,
                "markdown_file": str(markdown_path),
                "text_length": len(extracted_text),
                "processing_time": (datetime.now() - start_time).total_seconds()
            })

            logger.info(f"📄 마크다운 생성: {markdown_filename}")

        except ImportError as e:
            result["error"] = f"HWP 처리 도구 없음: {e}"
            logger.error(f"❌ HWP 도구 없음: {e}")

        except Exception as e:
            result["error"] = str(e)
            logger.error(f"❌ 마크다운 변환 오류: {e}")

        return result

    def _convert_to_markdown(self, text: str, original_file: Path) -> str:
        """텍스트를 구조화된 마크다운으로 변환"""

        # 파일 정보 헤더
        header = f"""# {original_file.stem}

## 문서 정보
- **원본 파일**: `{original_file.name}`
- **변환 일시**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- **파일 크기**: {original_file.stat().st_size:,} bytes
- **텍스트 길이**: {len(text):,} 문자

---

## 문서 내용

"""

        # 텍스트 전처리 및 구조화
        lines = text.split('\n')
        processed_lines = []

        for line in lines:
            line = line.strip()
            if not line:
                processed_lines.append('')
                continue

            # 제목으로 보이는 패턴 (대문자, 번호 등)
            if self._is_likely_title(line):
                processed_lines.append(f'### {line}')
            # 항목 번호가 있는 경우
            elif line.startswith(('1.', '2.', '3.', '가.', '나.', '다.', '-', '•')):
                processed_lines.append(f'- {line}')
            # 일반 텍스트
            else:
                processed_lines.append(line)

        body = '\n'.join(processed_lines)

        # 키워드 하이라이팅
        body = self._highlight_keywords(body)

        return header + body

    def _is_likely_title(self, line: str) -> bool:
        """제목일 가능성이 높은 라인인지 판단"""
        title_indicators = [
            '공고', '입찰', '계약', '사업', '공사', '용역', '구매',
            '제목', '건명', '과업', '업무', '내용'
        ]

        # 짧고 특정 키워드를 포함하는 경우
        if len(line) <= 50 and any(keyword in line for keyword in title_indicators):
            return True

        # 전체가 대문자인 경우 (영어)
        if line.isupper() and len(line.split()) <= 5:
            return True

        return False

    def _highlight_keywords(self, text: str) -> str:
        """중요 키워드 하이라이팅"""
        important_keywords = [
            '입찰', '공고', '계약', '사업비', '예산', '기간', '마감', '제출',
            '참가자격', '선정기준', '평가', '낙찰', '계약조건'
        ]

        for keyword in important_keywords:
            text = text.replace(keyword, f'**{keyword}**')

        return text

    def _safe_filename(self, filename: str) -> str:
        """안전한 파일명 생성"""
        import re

        # 특수문자 제거 및 길이 제한
        safe = re.sub(r'[^\w\s-]', '', filename)
        safe = re.sub(r'[-\s]+', '_', safe)
        return safe[:50]  # 최대 50자

    async def _update_database_with_markdown(
        self,
        hwp_file: Path,
        markdown_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """마크다운 정보로 데이터베이스 업데이트"""

        result = {
            "success": False,
            "error": None
        }

        try:
            with get_db_context() as db:
                # 파일명으로 BidDocument 찾기
                bid_document = db.query(BidDocument).filter(
                    BidDocument.file_name == hwp_file.name
                ).first()

                if bid_document:
                    # 기존 레코드 업데이트
                    bid_document.processing_status = 'completed'
                    bid_document.markdown_file_path = markdown_result["markdown_file"]
                    bid_document.extracted_text_length = markdown_result["text_length"]
                    bid_document.processed_at = datetime.utcnow()

                    # 마크다운 파일 상대 경로 저장
                    relative_path = Path(markdown_result["markdown_file"]).relative_to(Path.cwd())
                    bid_document.markdown_file_path = str(relative_path)

                    db.commit()
                    result["success"] = True
                    logger.info(f"💾 DB 업데이트: {hwp_file.name}")

                else:
                    # 연결된 BidDocument가 없는 경우 새로 생성 (선택사항)
                    logger.warning(f"⚠️ 연결된 BidDocument 없음: {hwp_file.name}")

        except Exception as e:
            result["error"] = str(e)
            logger.error(f"❌ DB 업데이트 실패: {hwp_file.name} - {e}")

        return result

    def get_processing_stats(self) -> Dict[str, Any]:
        """처리 통계 반환"""
        with get_db_context() as db:
            total_documents = db.query(BidDocument).count()
            processed_documents = db.query(BidDocument).filter(
                BidDocument.processing_status == 'completed'
            ).count()

            return {
                "total_documents": total_documents,
                "processed_documents": processed_documents,
                "processing_rate": (processed_documents / total_documents * 100) if total_documents > 0 else 0,
                "markdown_storage_path": str(self.markdown_storage)
            }


# 편의 함수
async def process_downloaded_files(download_dir: str) -> Dict[str, Any]:
    """다운로드된 파일들을 처리하는 편의 함수"""
    processor = DocumentProcessor()
    return await processor.process_downloaded_files(Path(download_dir))