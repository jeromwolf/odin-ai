"""
문서 다운로드 및 처리 서비스
HWP, PDF 등 입찰 관련 문서를 다운로드하고 텍스트로 변환
"""

import asyncio
import os
import hashlib
import tempfile
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from urllib.parse import urlparse
import shutil

import httpx
from loguru import logger

from backend.core.config import settings
from backend.models.database import SessionLocal
from backend.models.document_models import Document, DocumentProcessingQueue


class DocumentProcessor:
    """문서 다운로드 및 처리 서비스"""

    def __init__(self):
        """프로세서 초기화"""
        self.base_path = Path("storage")
        self.downloads_path = self.base_path / "downloads"
        self.processed_path = self.base_path / "processed"

        # 디렉토리 생성
        self._ensure_directories()

        # 지원 파일 타입
        self.supported_types = {
            ".hwp": "hwp",
            ".pdf": "pdf",
            ".doc": "doc",
            ".docx": "doc",
            ".xls": "excel",
            ".xlsx": "excel"
        }

        # 처리 통계
        self.stats = {
            "downloaded": 0,
            "processed": 0,
            "failed": 0,
            "skipped": 0
        }

        logger.info("DocumentProcessor 초기화 완료")

    def _ensure_directories(self):
        """필요한 디렉토리 생성"""
        dirs_to_create = [
            self.downloads_path / "hwp",
            self.downloads_path / "pdf",
            self.downloads_path / "doc",
            self.downloads_path / "unknown",
            self.processed_path / "hwp",
            self.processed_path / "pdf",
            self.processed_path / "doc",
            self.processed_path / "unknown"
        ]

        for dir_path in dirs_to_create:
            dir_path.mkdir(parents=True, exist_ok=True)

        logger.debug(f"디렉토리 구조 생성 완료: {self.base_path}")

    def get_file_type(self, filename: str) -> str:
        """파일 확장자로 타입 결정"""
        if not filename:
            return "unknown"

        ext = Path(filename).suffix.lower()
        return self.supported_types.get(ext, "unknown")

    def generate_file_hash(self, file_path: Path) -> str:
        """파일 해시 생성 (중복 방지용)"""
        try:
            hasher = hashlib.sha256()
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hasher.update(chunk)
            return hasher.hexdigest()
        except Exception as e:
            logger.error(f"해시 생성 실패: {e}")
            return ""

    async def download_document(
        self,
        url: str,
        filename: str = None,
        bid_notice_no: str = None
    ) -> Dict[str, Any]:
        """문서 다운로드"""

        if not filename:
            # URL에서 파일명 추출
            parsed_url = urlparse(url)
            filename = Path(parsed_url.path).name
            if not filename:
                filename = f"document_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        file_type = self.get_file_type(filename)
        download_dir = self.downloads_path / file_type

        logger.info(f"문서 다운로드 시작: {filename} (타입: {file_type})")

        try:
            # 안전한 파일명 생성
            safe_filename = self._make_safe_filename(filename, bid_notice_no)
            file_path = download_dir / safe_filename

            # 기존 파일 확인
            if file_path.exists():
                logger.info(f"파일 이미 존재: {safe_filename}")
                return await self._create_download_result(file_path, url, "exists")

            # HTTP 다운로드
            async with httpx.AsyncClient(timeout=60.0, follow_redirects=True) as client:
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
                    'Accept': 'application/octet-stream, application/*, */*'
                }

                response = await client.get(url, headers=headers)
                response.raise_for_status()

                # 파일 저장
                with open(file_path, 'wb') as f:
                    f.write(response.content)

                file_size = file_path.stat().st_size
                logger.info(f"다운로드 완료: {safe_filename} ({file_size:,} bytes)")

                self.stats["downloaded"] += 1
                return await self._create_download_result(file_path, url, "success")

        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP 오류 [{e.response.status_code}]: {url}")
            self.stats["failed"] += 1
            return {
                "success": False,
                "error": f"HTTP {e.response.status_code}",
                "url": url,
                "filename": filename
            }
        except Exception as e:
            logger.error(f"다운로드 실패: {e}")
            self.stats["failed"] += 1
            return {
                "success": False,
                "error": str(e),
                "url": url,
                "filename": filename
            }

    def _make_safe_filename(self, filename: str, bid_notice_no: str = None) -> str:
        """안전한 파일명 생성"""
        # 위험한 문자 제거
        safe_chars = "-_.() abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789가-힣"
        safe_name = ''.join(c for c in filename if c in safe_chars)

        # 길이 제한
        name_part = Path(safe_name).stem[:100]
        ext_part = Path(safe_name).suffix

        # 입찰공고번호 추가
        if bid_notice_no:
            prefix = f"{bid_notice_no}_"
        else:
            prefix = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_"

        return f"{prefix}{name_part}{ext_part}"

    async def _create_download_result(self, file_path: Path, url: str, status: str) -> Dict[str, Any]:
        """다운로드 결과 생성"""
        file_hash = self.generate_file_hash(file_path)
        file_size = file_path.stat().st_size
        file_type = self.get_file_type(file_path.name)

        return {
            "success": True,
            "status": status,
            "file_path": str(file_path),
            "filename": file_path.name,
            "file_type": file_type,
            "file_size": file_size,
            "file_hash": file_hash,
            "url": url,
            "downloaded_at": datetime.now().isoformat()
        }

    async def process_document(self, file_path: str) -> Dict[str, Any]:
        """문서 텍스트 추출 및 마크다운 생성"""

        file_path = Path(file_path)
        if not file_path.exists():
            return {
                "success": False,
                "error": f"파일이 존재하지 않음: {file_path}"
            }

        file_type = self.get_file_type(file_path.name)
        logger.info(f"문서 처리 시작: {file_path.name} (타입: {file_type})")

        try:
            if file_type == "hwp":
                return await self._process_hwp(file_path)
            elif file_type == "pdf":
                return await self._process_pdf(file_path)
            elif file_type == "doc":
                return await self._process_doc(file_path)
            else:
                logger.warning(f"지원하지 않는 파일 타입: {file_type}")
                self.stats["skipped"] += 1
                return {
                    "success": False,
                    "error": f"지원하지 않는 파일 타입: {file_type}",
                    "file_type": file_type
                }

        except Exception as e:
            logger.error(f"문서 처리 실패: {e}")
            self.stats["failed"] += 1
            return {
                "success": False,
                "error": str(e),
                "file_path": str(file_path)
            }

    async def _process_hwp(self, file_path: Path) -> Dict[str, Any]:
        """HWP 파일 처리"""
        processed_dir = self.processed_path / "hwp"
        base_name = file_path.stem

        # 출력 파일 경로
        txt_file = processed_dir / f"{base_name}.txt"
        md_file = processed_dir / f"{base_name}.md"

        try:
            # hwp5txt 명령으로 텍스트 추출
            result = subprocess.run([
                'hwp5txt', str(file_path)
            ], capture_output=True, text=True, encoding='utf-8')

            if result.returncode != 0:
                logger.warning(f"hwp5txt 실패, 오류: {result.stderr}")
                return {
                    "success": False,
                    "error": f"hwp5txt 처리 실패: {result.stderr}"
                }

            extracted_text = result.stdout

            # 텍스트 파일 저장
            with open(txt_file, 'w', encoding='utf-8') as f:
                f.write(extracted_text)

            # 마크다운 파일 생성
            markdown_content = self._convert_text_to_markdown(extracted_text, file_path.name)
            with open(md_file, 'w', encoding='utf-8') as f:
                f.write(markdown_content)

            self.stats["processed"] += 1

            return {
                "success": True,
                "file_type": "hwp",
                "original_file": str(file_path),
                "text_file": str(txt_file),
                "markdown_file": str(md_file),
                "text_length": len(extracted_text),
                "processed_at": datetime.now().isoformat()
            }

        except FileNotFoundError:
            logger.error("hwp5txt 명령을 찾을 수 없습니다. HWP 도구가 설치되지 않음")
            return {
                "success": False,
                "error": "hwp5txt 명령을 찾을 수 없음 (HWP 도구 미설치)"
            }

    async def _process_pdf(self, file_path: Path) -> Dict[str, Any]:
        """PDF 파일 처리"""
        processed_dir = self.processed_path / "pdf"
        base_name = file_path.stem

        # 출력 파일 경로
        txt_file = processed_dir / f"{base_name}.txt"
        md_file = processed_dir / f"{base_name}.md"

        try:
            # pdfplumber로 텍스트 추출 (별도 패키지 필요)
            extracted_text = await self._extract_pdf_text(file_path)

            if not extracted_text:
                return {
                    "success": False,
                    "error": "PDF에서 텍스트를 추출할 수 없음"
                }

            # 텍스트 파일 저장
            with open(txt_file, 'w', encoding='utf-8') as f:
                f.write(extracted_text)

            # 마크다운 파일 생성
            markdown_content = self._convert_text_to_markdown(extracted_text, file_path.name)
            with open(md_file, 'w', encoding='utf-8') as f:
                f.write(markdown_content)

            self.stats["processed"] += 1

            return {
                "success": True,
                "file_type": "pdf",
                "original_file": str(file_path),
                "text_file": str(txt_file),
                "markdown_file": str(md_file),
                "text_length": len(extracted_text),
                "processed_at": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"PDF 처리 실패: {e}")
            return {
                "success": False,
                "error": f"PDF 처리 실패: {e}"
            }

    async def _extract_pdf_text(self, file_path: Path) -> str:
        """PDF에서 텍스트 추출 (pdfplumber 사용)"""
        try:
            import pdfplumber

            text_content = []
            with pdfplumber.open(file_path) as pdf:
                for page_num, page in enumerate(pdf.pages, 1):
                    text = page.extract_text()
                    if text:
                        text_content.append(f"\n--- 페이지 {page_num} ---\n")
                        text_content.append(text)

            return '\n'.join(text_content)

        except ImportError:
            logger.error("pdfplumber가 설치되지 않음")
            return ""
        except Exception as e:
            logger.error(f"PDF 텍스트 추출 실패: {e}")
            return ""

    async def _process_doc(self, file_path: Path) -> Dict[str, Any]:
        """DOC/DOCX 파일 처리"""
        processed_dir = self.processed_path / "doc"
        base_name = file_path.stem

        # 출력 파일 경로
        txt_file = processed_dir / f"{base_name}.txt"
        md_file = processed_dir / f"{base_name}.md"

        try:
            # python-docx로 텍스트 추출 (별도 패키지 필요)
            extracted_text = await self._extract_doc_text(file_path)

            if not extracted_text:
                return {
                    "success": False,
                    "error": "DOC에서 텍스트를 추출할 수 없음"
                }

            # 텍스트 파일 저장
            with open(txt_file, 'w', encoding='utf-8') as f:
                f.write(extracted_text)

            # 마크다운 파일 생성
            markdown_content = self._convert_text_to_markdown(extracted_text, file_path.name)
            with open(md_file, 'w', encoding='utf-8') as f:
                f.write(markdown_content)

            self.stats["processed"] += 1

            return {
                "success": True,
                "file_type": "doc",
                "original_file": str(file_path),
                "text_file": str(txt_file),
                "markdown_file": str(md_file),
                "text_length": len(extracted_text),
                "processed_at": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"DOC 처리 실패: {e}")
            return {
                "success": False,
                "error": f"DOC 처리 실패: {e}"
            }

    async def _extract_doc_text(self, file_path: Path) -> str:
        """DOC/DOCX에서 텍스트 추출"""
        try:
            from docx import Document

            doc = Document(file_path)
            text_content = []

            for paragraph in doc.paragraphs:
                if paragraph.text.strip():
                    text_content.append(paragraph.text)

            return '\n'.join(text_content)

        except ImportError:
            logger.error("python-docx가 설치되지 않음")
            return ""
        except Exception as e:
            logger.error(f"DOC 텍스트 추출 실패: {e}")
            return ""

    def _convert_text_to_markdown(self, text: str, filename: str) -> str:
        """텍스트를 마크다운 형식으로 변환"""
        lines = text.split('\n')
        markdown_lines = [
            f"# {Path(filename).stem}",
            "",
            f"**파일명**: {filename}",
            f"**처리일시**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"**텍스트 길이**: {len(text):,} 문자",
            "",
            "---",
            ""
        ]

        current_section = ""
        for line in lines:
            line = line.strip()
            if not line:
                markdown_lines.append("")
                continue

            # 섹션 헤더 감지 (간단한 패턴)
            if any(keyword in line for keyword in ["1.", "가.", "○", "■", "◦"]):
                if len(line) < 100:  # 헤더는 보통 짧음
                    markdown_lines.append(f"## {line}")
                    current_section = line
                    continue

            # 중요 정보 강조
            if any(keyword in line for keyword in ["예정가격", "추정가격", "입찰마감", "개찰일시", "계약기간"]):
                markdown_lines.append(f"**{line}**")
            else:
                markdown_lines.append(line)

        return '\n'.join(markdown_lines)

    async def download_and_process_batch(
        self,
        document_urls: List[Dict[str, str]],
        bid_notice_no: str = None
    ) -> Dict[str, Any]:
        """문서 일괄 다운로드 및 처리"""

        logger.info(f"일괄 처리 시작: {len(document_urls)}개 문서")

        results = {
            "total_documents": len(document_urls),
            "downloaded": 0,
            "processed": 0,
            "failed": 0,
            "results": [],
            "stats": self.stats.copy()
        }

        for doc_info in document_urls:
            url = doc_info.get("url", "")
            filename = doc_info.get("filename", "")

            if not url:
                continue

            try:
                # 1단계: 다운로드
                download_result = await self.download_document(url, filename, bid_notice_no)

                if download_result.get("success"):
                    results["downloaded"] += 1

                    # 2단계: 처리 (텍스트 추출 + 마크다운 생성)
                    file_path = download_result["file_path"]
                    process_result = await self.process_document(file_path)

                    if process_result.get("success"):
                        results["processed"] += 1

                    # 결과 병합
                    combined_result = {**download_result, **process_result}
                    results["results"].append(combined_result)

                else:
                    results["failed"] += 1
                    results["results"].append(download_result)

            except Exception as e:
                logger.error(f"문서 처리 오류 ({url}): {e}")
                results["failed"] += 1
                results["results"].append({
                    "success": False,
                    "error": str(e),
                    "url": url,
                    "filename": filename
                })

        # 최종 통계 업데이트
        results["final_stats"] = self.stats.copy()

        logger.info(f"일괄 처리 완료: {results['processed']}/{results['total_documents']}개 처리 성공")

        return results

    async def get_processing_stats(self) -> Dict[str, Any]:
        """처리 통계 조회"""
        return {
            "stats": self.stats,
            "directories": {
                "downloads": str(self.downloads_path),
                "processed": str(self.processed_path)
            },
            "supported_types": list(self.supported_types.keys()),
            "timestamp": datetime.now().isoformat()
        }

    async def cleanup_old_files(self, days_old: int = 30) -> Dict[str, Any]:
        """오래된 파일 정리"""
        cutoff_time = datetime.now().timestamp() - (days_old * 24 * 3600)

        removed_files = {"downloads": 0, "processed": 0}

        for category in ["downloads", "processed"]:
            base_dir = self.downloads_path if category == "downloads" else self.processed_path

            for file_path in base_dir.rglob("*"):
                if file_path.is_file() and file_path.stat().st_mtime < cutoff_time:
                    try:
                        file_path.unlink()
                        removed_files[category] += 1
                    except Exception as e:
                        logger.warning(f"파일 삭제 실패: {e}")

        logger.info(f"파일 정리 완료: {sum(removed_files.values())}개 파일 삭제")

        return {
            "removed_files": removed_files,
            "days_old": days_old,
            "cleaned_at": datetime.now().isoformat()
        }