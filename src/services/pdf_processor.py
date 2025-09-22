"""
PDF 문서 처리기 - tools/pdf-viewer 통합
"""

import sys
from pathlib import Path
from typing import Dict, Tuple
from loguru import logger

# tools/pdf-viewer 모듈 가져오기
tools_path = Path(__file__).parent.parent.parent / "tools" / "pdf-viewer"
sys.path.insert(0, str(tools_path))

try:
    from pdf_viewer.parser import PDFParser
    from pdf_viewer.markdown_formatter import PDFMarkdownFormatter
    HAS_PDF_PARSER = True
except ImportError as e:
    logger.warning(f"PDF 파서 가져오기 실패: {e}")
    HAS_PDF_PARSER = False


class PDFProcessor:
    """PDF 파일 처리기"""

    def __init__(self):
        self.parser = PDFParser(method="auto") if HAS_PDF_PARSER else None
        self.formatter = PDFMarkdownFormatter() if HAS_PDF_PARSER else None

    async def process(self, file_path: Path) -> Tuple[str, Dict]:
        """
        PDF 파일을 처리하여 마크다운 텍스트 반환

        Returns:
            (markdown_text, metadata)
        """
        if not HAS_PDF_PARSER:
            return "", {"error": "PDF 파서 모듈을 사용할 수 없습니다"}

        try:
            # PDF 파싱
            pdf_doc = self.parser.parse(str(file_path))

            # 마크다운 변환
            title = pdf_doc.metadata.title or file_path.stem
            markdown_text = self.formatter.format_document(
                title=title,
                content=pdf_doc.raw_text,
                metadata={
                    'title': pdf_doc.metadata.title,
                    'author': pdf_doc.metadata.author,
                    'pages': pdf_doc.metadata.pages,
                    'creation_date': pdf_doc.metadata.creation_date
                },
                pages=[{
                    'page_num': page.page_num,
                    'text': page.text,
                    'tables': page.tables
                } for page in pdf_doc.pages]
            )

            # 메타데이터 구성
            metadata = {
                "pages": len(pdf_doc.pages),
                "title": pdf_doc.metadata.title or "제목 없음",
                "author": pdf_doc.metadata.author or "작성자 미상",
                "total_tables": sum(len(page.tables) for page in pdf_doc.pages),
                "text_length": len(pdf_doc.raw_text),
                "processing_method": "tools/pdf-viewer"
            }

            logger.info(f"PDF 처리 완료: {file_path.name} - {len(pdf_doc.pages)}페이지, {len(markdown_text)}자")

            return markdown_text, metadata

        except Exception as e:
            logger.error(f"PDF 처리 실패: {file_path.name} - {e}")
            return "", {"error": str(e), "processing_method": "tools/pdf-viewer"}


async def process_pdf_file(file_path: Path) -> Dict:
    """
    PDF 파일 처리 인터페이스

    Returns:
        {
            'text': str,
            'pages_count': int,
            'tables_count': int,
            'success': bool,
            'metadata': dict
        }
    """
    processor = PDFProcessor()
    text, metadata = await processor.process(file_path)

    return {
        'text': text,
        'pages_count': metadata.get('pages', 0),
        'tables_count': metadata.get('total_tables', 0),
        'success': bool(text and not metadata.get('error')),
        'metadata': metadata
    }