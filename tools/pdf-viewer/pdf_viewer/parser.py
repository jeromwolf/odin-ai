"""
PDF 파일 파서 모듈 - 다양한 PDF 라이브러리를 활용한 통합 파서
"""

import PyPDF2
import pdfplumber
import fitz  # pymupdf
from pathlib import Path
from typing import List, Optional
import logging

from .models import PDFDocument, PDFMetadata, PDFPage, PDFTable

logger = logging.getLogger(__name__)


class PDFParser:
    """PDF 파일을 파싱하는 메인 클래스"""

    def __init__(self, method: str = "auto"):
        """
        Args:
            method: 파싱 방법 ("auto", "pypdf2", "pdfplumber", "pymupdf")
        """
        self.method = method
        self.doc = None

    def parse(self, file_path: str) -> PDFDocument:
        """PDF 파일을 파싱하여 구조화된 문서 객체 반환

        Args:
            file_path: PDF 파일 경로

        Returns:
            PDFDocument: 파싱된 문서 객체
        """
        try:
            path = Path(file_path)
            if not path.exists():
                raise FileNotFoundError(f"파일을 찾을 수 없습니다: {file_path}")

            if not path.suffix.lower() == '.pdf':
                raise ValueError("PDF 파일만 처리할 수 있습니다.")

            # 파싱 방법에 따라 다른 처리
            if self.method == "auto":
                return self._parse_auto(file_path)
            elif self.method == "pypdf2":
                return self._parse_pypdf2(file_path)
            elif self.method == "pdfplumber":
                return self._parse_pdfplumber(file_path)
            elif self.method == "pymupdf":
                return self._parse_pymupdf(file_path)
            else:
                raise ValueError(f"지원하지 않는 파싱 방법: {self.method}")

        except Exception as e:
            logger.error(f"PDF 파싱 실패: {e}")
            # 빈 문서 반환
            return PDFDocument(
                metadata=PDFMetadata(),
                pages=[],
                raw_text=f"파싱 오류: {str(e)}"
            )

    def _parse_auto(self, file_path: str) -> PDFDocument:
        """자동으로 가장 적합한 파서 선택"""
        try:
            # 1순위: pdfplumber (테이블 추출 우수)
            return self._parse_pdfplumber(file_path)
        except Exception as e1:
            logger.warning(f"pdfplumber 파싱 실패, pymupdf 시도: {e1}")
            try:
                # 2순위: pymupdf (빠르고 안정적)
                return self._parse_pymupdf(file_path)
            except Exception as e2:
                logger.warning(f"pymupdf 파싱 실패, pypdf2 시도: {e2}")
                try:
                    # 3순위: pypdf2 (기본적)
                    return self._parse_pypdf2(file_path)
                except Exception as e3:
                    logger.error(f"모든 파서 실패: {e3}")
                    raise e3

    def _parse_pypdf2(self, file_path: str) -> PDFDocument:
        """PyPDF2를 사용한 파싱"""
        with open(file_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)

            # 메타데이터 추출
            metadata = self._extract_metadata_pypdf2(reader)

            # 페이지별 텍스트 추출
            pages = []
            all_text = []

            for i, page in enumerate(reader.pages):
                text = page.extract_text()
                all_text.append(text)

                pdf_page = PDFPage(
                    page_num=i + 1,
                    text=text,
                    tables=[],  # PyPDF2는 테이블 추출 제한적
                    images=[]
                )
                pages.append(pdf_page)

            return PDFDocument(
                metadata=metadata,
                pages=pages,
                raw_text="\\n".join(all_text)
            )

    def _parse_pdfplumber(self, file_path: str) -> PDFDocument:
        """pdfplumber를 사용한 파싱"""
        with pdfplumber.open(file_path) as pdf:
            # 메타데이터 추출
            metadata = self._extract_metadata_pdfplumber(pdf)

            # 페이지별 처리
            pages = []
            all_text = []

            for i, page in enumerate(pdf.pages):
                # 텍스트 추출
                text = page.extract_text() or ""
                all_text.append(text)

                # 테이블 추출
                tables = []
                try:
                    page_tables = page.extract_tables()
                    for j, table_data in enumerate(page_tables or []):
                        if table_data:
                            table = PDFTable(
                                page_num=i + 1,
                                rows=len(table_data),
                                cols=len(table_data[0]) if table_data else 0,
                                cells=table_data,
                                bbox=page.bbox
                            )
                            tables.append(table)
                except Exception as e:
                    logger.warning(f"페이지 {i+1} 테이블 추출 실패: {e}")

                pdf_page = PDFPage(
                    page_num=i + 1,
                    text=text,
                    tables=tables,
                    images=[],
                    bbox=page.bbox
                )
                pages.append(pdf_page)

            return PDFDocument(
                metadata=metadata,
                pages=pages,
                raw_text="\\n".join(all_text)
            )

    def _parse_pymupdf(self, file_path: str) -> PDFDocument:
        """PyMuPDF를 사용한 파싱"""
        doc = fitz.open(file_path)

        # 메타데이터 추출
        metadata = self._extract_metadata_pymupdf(doc)

        # 페이지별 처리
        pages = []
        all_text = []

        for i, page in enumerate(doc):
            # 텍스트 추출
            text = page.get_text()
            all_text.append(text)

            # 테이블 추출 (PyMuPDF 1.23+에서 지원)
            tables = []
            try:
                page_tables = page.find_tables()
                for j, table in enumerate(page_tables or []):
                    table_data = table.extract()
                    if table_data:
                        pdf_table = PDFTable(
                            page_num=i + 1,
                            rows=len(table_data),
                            cols=len(table_data[0]) if table_data else 0,
                            cells=table_data,
                            bbox=table.bbox if hasattr(table, 'bbox') else None
                        )
                        tables.append(pdf_table)
            except Exception as e:
                logger.warning(f"페이지 {i+1} 테이블 추출 실패: {e}")

            pdf_page = PDFPage(
                page_num=i + 1,
                text=text,
                tables=tables,
                images=[],
                bbox=(page.rect.width, page.rect.height)
            )
            pages.append(pdf_page)

        doc.close()

        return PDFDocument(
            metadata=metadata,
            pages=pages,
            raw_text="\\n".join(all_text)
        )

    def _extract_metadata_pypdf2(self, reader) -> PDFMetadata:
        """PyPDF2로 메타데이터 추출"""
        try:
            info = reader.metadata or {}
            return PDFMetadata(
                title=info.get('/Title'),
                author=info.get('/Author'),
                creator=info.get('/Creator'),
                producer=info.get('/Producer'),
                subject=info.get('/Subject'),
                keywords=info.get('/Keywords'),
                creation_date=str(info.get('/CreationDate', '')),
                modification_date=str(info.get('/ModDate', '')),
                pages=len(reader.pages)
            )
        except Exception as e:
            logger.warning(f"메타데이터 추출 실패: {e}")
            return PDFMetadata(pages=len(reader.pages))

    def _extract_metadata_pdfplumber(self, pdf) -> PDFMetadata:
        """pdfplumber로 메타데이터 추출"""
        try:
            info = pdf.metadata or {}
            return PDFMetadata(
                title=info.get('Title'),
                author=info.get('Author'),
                creator=info.get('Creator'),
                producer=info.get('Producer'),
                subject=info.get('Subject'),
                keywords=info.get('Keywords'),
                creation_date=str(info.get('CreationDate', '')),
                modification_date=str(info.get('ModDate', '')),
                pages=len(pdf.pages)
            )
        except Exception as e:
            logger.warning(f"메타데이터 추출 실패: {e}")
            return PDFMetadata(pages=len(pdf.pages))

    def _extract_metadata_pymupdf(self, doc) -> PDFMetadata:
        """PyMuPDF로 메타데이터 추출"""
        try:
            info = doc.metadata or {}
            return PDFMetadata(
                title=info.get('title'),
                author=info.get('author'),
                creator=info.get('creator'),
                producer=info.get('producer'),
                subject=info.get('subject'),
                keywords=info.get('keywords'),
                creation_date=info.get('creationDate', ''),
                modification_date=info.get('modDate', ''),
                pages=doc.page_count
            )
        except Exception as e:
            logger.warning(f"메타데이터 추출 실패: {e}")
            return PDFMetadata(pages=doc.page_count)