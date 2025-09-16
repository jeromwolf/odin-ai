"""
HWP 파일 파서 모듈 - pyhwp 라이브러리를 활용한 개선된 버전
"""

import olefile
from typing import Optional, Dict, Any, List
from pathlib import Path
import logging
import tempfile
import zlib

try:
    import hwp5
    from hwp5.hwp5 import Hwp5File
    PYHWP_AVAILABLE = True
except ImportError:
    try:
        # Alternative import path
        from pyhwp import Hwp5File
        PYHWP_AVAILABLE = True
    except ImportError:
        PYHWP_AVAILABLE = False

from .models import HWPDocument, HWPMetadata, HWPParagraph, HWPTable

logger = logging.getLogger(__name__)


class HWPParser:
    """HWP 파일을 파싱하는 메인 클래스"""

    def __init__(self):
        self.document = None
        self.ole_file = None
        self.hwp_file = None

    def parse(self, file_path: str) -> HWPDocument:
        """HWP 파일을 파싱하여 구조화된 문서 객체 반환

        Args:
            file_path: HWP 파일 경로

        Returns:
            HWPDocument: 파싱된 문서 객체
        """
        try:
            path = Path(file_path)
            if not path.exists():
                raise FileNotFoundError(f"파일을 찾을 수 없습니다: {file_path}")

            # pyhwp가 설치된 경우 우선 사용
            if PYHWP_AVAILABLE:
                return self._parse_with_pyhwp(file_path)
            else:
                return self._parse_with_olefile(file_path)

        except Exception as e:
            logger.error(f"HWP 파일 파싱 실패: {e}")
            # Fallback to olefile method
            if PYHWP_AVAILABLE:
                logger.info("pyhwp 파싱 실패, olefile 방식으로 재시도")
                return self._parse_with_olefile(file_path)
            raise

    def _parse_with_pyhwp(self, file_path: str) -> HWPDocument:
        """pyhwp 라이브러리를 사용한 파싱"""
        try:
            self.hwp_file = Hwp5File(file_path)

            # 메타데이터 추출
            metadata = self._extract_metadata_pyhwp()

            # 텍스트 추출
            text = self.hwp_file.get_text()
            paragraphs = [HWPParagraph(text=p.strip()) for p in text.split('\n') if p.strip()]

            # 테이블 추출 (TODO: 구현 필요)
            tables = []

            # 문서 객체 생성
            self.document = HWPDocument(
                metadata=metadata,
                paragraphs=paragraphs,
                tables=tables,
                raw_text=text
            )

            return self.document

        except Exception as e:
            logger.error(f"pyhwp 파싱 실패: {e}")
            raise
        finally:
            if self.hwp_file:
                self.hwp_file.close()

    def _parse_with_olefile(self, file_path: str) -> HWPDocument:
        """olefile을 사용한 기본 파싱"""
        try:
            # OLE 파일로 열기
            self.ole_file = olefile.OleFileIO(file_path)

            # 메타데이터 추출
            metadata = self._extract_metadata_ole()

            # 본문 텍스트 추출
            paragraphs = self._extract_paragraphs_ole()

            # 테이블 추출
            tables = self._extract_tables_ole()

            # 문서 객체 생성
            self.document = HWPDocument(
                metadata=metadata,
                paragraphs=paragraphs,
                tables=tables,
                raw_text=self._get_raw_text(paragraphs)
            )

            return self.document

        finally:
            if self.ole_file:
                self.ole_file.close()

    def extract_text(self, file_path: str) -> str:
        """HWP 파일에서 텍스트만 빠르게 추출

        Args:
            file_path: HWP 파일 경로

        Returns:
            str: 추출된 텍스트
        """
        doc = self.parse(file_path)
        return doc.raw_text

    def _extract_metadata_pyhwp(self) -> HWPMetadata:
        """pyhwp를 사용한 메타데이터 추출"""
        metadata = HWPMetadata()

        try:
            summary = self.hwp_file.get_summary_info()
            if summary:
                metadata.title = summary.get('title', '')
                metadata.author = summary.get('author', '')
                metadata.subject = summary.get('subject', '')
                metadata.keywords = summary.get('keywords', '')
        except Exception as e:
            logger.warning(f"메타데이터 추출 실패: {e}")

        return metadata

    def _extract_metadata_ole(self) -> HWPMetadata:
        """olefile을 사용한 메타데이터 추출"""
        metadata = HWPMetadata()

        try:
            # HwpSummaryInformation 스트림에서 메타데이터 읽기
            if self.ole_file.exists("\x05HwpSummaryInformation"):
                summary = self.ole_file.getproperties(["\x05HwpSummaryInformation"])
                metadata.title = summary.get('title', '')
                metadata.author = summary.get('author', '')
                metadata.created_date = summary.get('create_time', None)
                metadata.modified_date = summary.get('last_saved_time', None)
                metadata.keywords = summary.get('keywords', '')

        except Exception as e:
            logger.warning(f"메타데이터 추출 실패: {e}")

        return metadata

    def _extract_paragraphs_ole(self) -> List[HWPParagraph]:
        """olefile을 사용한 본문 단락 추출"""
        paragraphs = []

        try:
            # BodyText 섹션 찾기
            dirs = self.ole_file.listdir()
            for d in dirs:
                if 'BodyText' in d[0]:
                    # 각 섹션 처리
                    stream = self.ole_file.openstream(d)
                    data = stream.read()

                    # 압축 해제 시도
                    text = self._decode_bodytext(data)
                    if text:
                        # 문단별로 분리
                        for para_text in text.split('\n'):
                            if para_text.strip():
                                para = HWPParagraph(text=para_text.strip())
                                paragraphs.append(para)

        except Exception as e:
            logger.warning(f"단락 추출 실패: {e}")

        return paragraphs

    def _extract_tables_ole(self) -> List[HWPTable]:
        """테이블 추출"""
        tables = []
        # TODO: 테이블 파싱 구현
        # HWP 테이블 구조는 복잡하여 상세 구현 필요
        return tables

    def _decode_bodytext(self, data: bytes) -> str:
        """BodyText 데이터 디코딩 - 압축 해제 포함"""
        try:
            # HWP 5.0 이상은 zlib 압축 사용
            try:
                # 압축 해제 시도
                decompressed = zlib.decompress(data, -zlib.MAX_WBITS)
                data = decompressed
            except zlib.error:
                # 압축되지 않은 데이터인 경우 그대로 사용
                pass

            # 여러 인코딩 시도
            encodings = ['utf-16-le', 'utf-16', 'cp949', 'euc-kr', 'utf-8']

            for encoding in encodings:
                try:
                    text = data.decode(encoding)

                    # 한글이 포함되어 있는지 확인
                    if any('\uac00' <= char <= '\ud7af' for char in text):
                        # 제어 문자 제거 및 정리
                        cleaned_text = []
                        for char in text:
                            if char.isprintable() or char in '\n\r\t ':
                                cleaned_text.append(char)

                        result = ''.join(cleaned_text).strip()
                        if result:
                            logger.info(f"텍스트 디코딩 성공: {encoding}")
                            return result

                except (UnicodeDecodeError, UnicodeError):
                    continue

            # 모든 인코딩 실패 시 기본 처리
            logger.warning("모든 인코딩 시도 실패, ignore 모드로 디코딩")
            text = data.decode('utf-16-le', errors='ignore')

            # 제어 문자 제거
            cleaned_text = []
            for char in text:
                if char.isprintable() or char in '\n\r\t ':
                    cleaned_text.append(char)

            return ''.join(cleaned_text).strip()

        except Exception as e:
            logger.warning(f"텍스트 디코딩 실패: {e}")
            return ""

    def _get_raw_text(self, paragraphs: List[HWPParagraph]) -> str:
        """전체 텍스트 추출"""
        texts = [p.text for p in paragraphs if p.text]
        return '\n\n'.join(texts)