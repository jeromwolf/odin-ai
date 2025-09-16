"""
PDF 문서 모델 정의
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional


@dataclass
class PDFTable:
    """PDF 테이블"""
    page_num: int
    rows: int
    cols: int
    cells: List[List[str]]
    bbox: tuple = None  # (x0, y0, x1, y1)


@dataclass
class PDFPage:
    """PDF 페이지"""
    page_num: int
    text: str
    tables: List[PDFTable] = field(default_factory=list)
    images: List[Dict[str, Any]] = field(default_factory=list)
    bbox: tuple = None  # (width, height)


@dataclass
class PDFMetadata:
    """PDF 메타데이터"""
    title: Optional[str] = None
    author: Optional[str] = None
    creator: Optional[str] = None
    producer: Optional[str] = None
    subject: Optional[str] = None
    keywords: Optional[str] = None
    creation_date: Optional[str] = None
    modification_date: Optional[str] = None
    pages: int = 0


@dataclass
class PDFDocument:
    """PDF 문서"""
    metadata: PDFMetadata
    pages: List[PDFPage] = field(default_factory=list)
    raw_text: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return {
            "metadata": {
                "title": self.metadata.title,
                "author": self.metadata.author,
                "creator": self.metadata.creator,
                "producer": self.metadata.producer,
                "subject": self.metadata.subject,
                "keywords": self.metadata.keywords,
                "creation_date": self.metadata.creation_date,
                "modification_date": self.metadata.modification_date,
                "pages": self.metadata.pages,
            },
            "content": {
                "raw_text": self.raw_text,
                "pages": len(self.pages),
                "tables": sum(len(page.tables) for page in self.pages),
                "total_text_length": len(self.raw_text),
            },
            "statistics": {
                "total_pages": len(self.pages),
                "total_tables": sum(len(page.tables) for page in self.pages),
                "total_images": sum(len(page.images) for page in self.pages),
                "average_text_per_page": len(self.raw_text) // max(len(self.pages), 1),
            }
        }