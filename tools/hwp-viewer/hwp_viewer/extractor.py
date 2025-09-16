"""
HWP 파일에서 특정 요소를 추출하는 모듈
"""

import re
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path

from .parser import HWPParser
from .models import HWPDocument, HWPTable

logger = logging.getLogger(__name__)


class TextExtractor:
    """텍스트 추출 전문 클래스"""

    def __init__(self):
        self.parser = HWPParser()

    def extract_all(self, file_path: str) -> str:
        """모든 텍스트 추출"""
        return self.parser.extract_text(file_path)

    def extract_paragraphs(self, file_path: str) -> List[str]:
        """단락별로 텍스트 추출"""
        doc = self.parser.parse(file_path)
        return [p.text for p in doc.paragraphs if p.text]

    def extract_by_keyword(self, file_path: str, keyword: str) -> List[str]:
        """키워드가 포함된 단락만 추출"""
        doc = self.parser.parse(file_path)
        results = []

        for para in doc.paragraphs:
            if keyword.lower() in para.text.lower():
                results.append(para.text)

        return results

    def extract_by_pattern(self, file_path: str, pattern: str) -> List[str]:
        """정규표현식 패턴에 매칭되는 텍스트 추출"""
        doc = self.parser.parse(file_path)
        results = []
        regex = re.compile(pattern, re.IGNORECASE | re.MULTILINE)

        for para in doc.paragraphs:
            matches = regex.findall(para.text)
            if matches:
                results.extend(matches)

        return results

    def extract_summary(self, file_path: str, max_length: int = 500) -> str:
        """문서 요약 추출 (처음 N자)"""
        text = self.extract_all(file_path)
        if len(text) <= max_length:
            return text
        return text[:max_length] + "..."


class TableExtractor:
    """테이블 추출 전문 클래스"""

    def __init__(self):
        self.parser = HWPParser()

    def extract_all_tables(self, file_path: str) -> List[HWPTable]:
        """모든 테이블 추출"""
        doc = self.parser.parse(file_path)
        return doc.tables

    def extract_tables_as_csv(self, file_path: str) -> List[str]:
        """테이블을 CSV 형식으로 추출"""
        tables = self.extract_all_tables(file_path)
        csv_tables = []

        for table in tables:
            csv_lines = []
            for row in table.cells:
                csv_line = ','.join([f'"{cell}"' for cell in row])
                csv_lines.append(csv_line)
            csv_tables.append('\n'.join(csv_lines))

        return csv_tables

    def extract_tables_as_json(self, file_path: str) -> List[Dict[str, Any]]:
        """테이블을 JSON 형식으로 추출"""
        tables = self.extract_all_tables(file_path)
        json_tables = []

        for table in tables:
            json_table = {
                'rows': table.rows,
                'cols': table.cols,
                'data': table.cells,
                'title': table.title
            }
            json_tables.append(json_table)

        return json_tables


class MetadataExtractor:
    """메타데이터 추출 전문 클래스"""

    def __init__(self):
        self.parser = HWPParser()

    def extract_metadata(self, file_path: str) -> Dict[str, Any]:
        """문서 메타데이터 추출"""
        doc = self.parser.parse(file_path)
        metadata = doc.metadata

        return {
            'title': metadata.title,
            'author': metadata.author,
            'subject': metadata.subject,
            'keywords': metadata.keywords,
            'created_date': metadata.created_date.isoformat() if metadata.created_date else None,
            'modified_date': metadata.modified_date.isoformat() if metadata.modified_date else None,
            'version': metadata.version,
            'pages': metadata.pages
        }

    def extract_statistics(self, file_path: str) -> Dict[str, int]:
        """문서 통계 정보 추출"""
        doc = self.parser.parse(file_path)

        # 텍스트 통계
        text = doc.raw_text
        words = text.split()
        lines = text.split('\n')

        return {
            'total_characters': len(text),
            'total_words': len(words),
            'total_lines': len(lines),
            'total_paragraphs': len(doc.paragraphs),
            'total_tables': len(doc.tables),
            'total_images': len(doc.images)
        }


class ContentSearcher:
    """HWP 파일 내용 검색 클래스"""

    def __init__(self):
        self.parser = HWPParser()

    def search(self, file_path: str, query: str, context_lines: int = 2) -> List[Dict[str, Any]]:
        """텍스트 검색 및 컨텍스트 반환"""
        doc = self.parser.parse(file_path)
        results = []

        for idx, para in enumerate(doc.paragraphs):
            if query.lower() in para.text.lower():
                # 컨텍스트 수집
                context_before = []
                context_after = []

                # 이전 컨텍스트
                for i in range(max(0, idx - context_lines), idx):
                    context_before.append(doc.paragraphs[i].text)

                # 이후 컨텍스트
                for i in range(idx + 1, min(len(doc.paragraphs), idx + context_lines + 1)):
                    context_after.append(doc.paragraphs[i].text)

                results.append({
                    'paragraph_index': idx,
                    'text': para.text,
                    'context_before': context_before,
                    'context_after': context_after,
                    'match_positions': self._find_positions(para.text, query)
                })

        return results

    def _find_positions(self, text: str, query: str) -> List[tuple]:
        """쿼리 문자열의 위치 찾기"""
        positions = []
        text_lower = text.lower()
        query_lower = query.lower()

        start = 0
        while True:
            pos = text_lower.find(query_lower, start)
            if pos == -1:
                break
            positions.append((pos, pos + len(query)))
            start = pos + 1

        return positions