"""
HWP 문서 데이터 모델
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Dict, Any


@dataclass
class HWPMetadata:
    """HWP 문서 메타데이터"""
    title: str = ""
    author: str = ""
    subject: str = ""
    keywords: str = ""
    created_date: Optional[datetime] = None
    modified_date: Optional[datetime] = None
    version: str = ""
    pages: int = 0


@dataclass
class HWPParagraph:
    """HWP 단락"""
    text: str
    style: Optional[str] = None
    level: int = 0  # 제목 레벨 (0=본문)


@dataclass
class HWPTable:
    """HWP 테이블"""
    rows: int = 0
    cols: int = 0
    cells: List[List[str]] = field(default_factory=list)
    title: Optional[str] = None


@dataclass
class HWPImage:
    """HWP 이미지"""
    name: str
    data: bytes
    width: int = 0
    height: int = 0
    format: str = ""


@dataclass
class HWPDocument:
    """HWP 문서 전체 구조"""
    metadata: HWPMetadata
    paragraphs: List[HWPParagraph] = field(default_factory=list)
    tables: List[HWPTable] = field(default_factory=list)
    images: List[HWPImage] = field(default_factory=list)
    raw_text: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """사전 형태로 변환"""
        return {
            "metadata": {
                "title": self.metadata.title,
                "author": self.metadata.author,
                "created_date": self.metadata.created_date.isoformat() if self.metadata.created_date else None,
                "modified_date": self.metadata.modified_date.isoformat() if self.metadata.modified_date else None,
            },
            "content": {
                "paragraphs": [{"text": p.text, "level": p.level} for p in self.paragraphs],
                "tables": [{"rows": t.rows, "cols": t.cols} for t in self.tables],
                "images_count": len(self.images)
            },
            "statistics": {
                "total_paragraphs": len(self.paragraphs),
                "total_tables": len(self.tables),
                "total_images": len(self.images),
                "text_length": len(self.raw_text)
            }
        }