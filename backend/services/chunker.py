"""
한국어 공공입찰 문서 청킹 서비스
RFP 문서를 의미 단위로 분할하여 RAG 시스템에 적합한 청크 생성
"""

import re
import logging
from dataclasses import dataclass, field
from typing import List, Tuple, Optional, Dict

logger = logging.getLogger(__name__)


@dataclass
class DocumentChunk:
    """문서 청크 데이터"""
    text: str
    section_type: str  # '자격요건', '예정가격', '일반' etc.
    chunk_index: int
    token_count: int
    metadata: Dict = field(default_factory=dict)


class KoreanProcurementChunker:
    """
    한국어 공공입찰 문서 전용 청킹 엔진

    HWP/PDF에서 변환된 마크다운 텍스트를 의미 단위로 분할합니다.
    섹션 경계를 우선 인식하고, 큰 섹션은 문장 단위로 슬라이딩 윈도우 분할합니다.
    """

    # Korean document section header patterns
    SECTION_PATTERNS = [
        r'^#{1,3}\s+.+$',                           # Markdown headers
        r'^\d+\.\s+[가-힣].+$',                     # "1. 사업개요"
        r'^[가나다라마바사아자차카타파하]\.\s+.+$',     # "가. 자격요건"
        r'^제\d+조[\s(].+$',                         # "제1조 (목적)"
        r'^\d+\)\s+.+$',                            # "1) 개요"
        r'^[①②③④⑤⑥⑦⑧⑨⑩]\s*.+$',                 # Circled numbers
        r'^\[.+\]$',                                 # [Section Title]
        r'^■\s+.+$',                                 # ■ Section marker
        r'^○\s+.+$',                                 # ○ Section marker
        r'^▶\s+.+$',                                 # ▶ Section marker
    ]

    # Section type detection keywords
    SECTION_TYPES = {
        '자격': '자격요건',
        '참가자격': '자격요건',
        '입찰참가': '자격요건',
        '예정가격': '예정가격',
        '추정가격': '예정가격',
        '기초금액': '예정가격',
        '설계금액': '예정가격',
        '제출서류': '제출서류',
        '제출': '제출서류',
        '구비서류': '제출서류',
        '평가': '평가기준',
        '심사': '평가기준',
        '배점': '평가기준',
        '일정': '사업일정',
        '기간': '사업일정',
        '공사기간': '사업일정',
        '납품기한': '사업일정',
        '입찰일': '사업일정',
        '하도급': '하도급',
        '하수급': '하도급',
        '업무범위': '업무범위',
        '과업내용': '업무범위',
        '사업범위': '업무범위',
        '기술': '기술요건',
        '사양': '기술요건',
        '규격': '기술요건',
        '계약': '계약조건',
        '대금지급': '계약조건',
        '지체상금': '계약조건',
        '개요': '사업개요',
        '목적': '사업개요',
        '배경': '사업개요',
    }

    def __init__(
        self,
        target_tokens: int = 400,
        max_tokens: int = 512,
        overlap_tokens: int = 80,
        min_tokens: int = 50,
    ):
        self.target = target_tokens
        self.max_tokens = max_tokens
        self.overlap = overlap_tokens
        self.min_tokens = min_tokens
        self._section_re = re.compile(
            '|'.join(self.SECTION_PATTERNS), re.MULTILINE
        )

    def estimate_tokens(self, text: str) -> int:
        """한국어 텍스트의 토큰 수 추정 (1.3 chars/token)"""
        if not text:
            return 0
        return max(1, int(len(text) / 1.3))

    def detect_section_type(self, text: str) -> str:
        """텍스트에서 섹션 유형 감지"""
        check_text = text[:200]
        for keyword, section_type in self.SECTION_TYPES.items():
            if keyword in check_text:
                return section_type
        return '일반'

    def split_sentences(self, text: str) -> List[str]:
        """한국어 문장 분리"""
        # Split on Korean sentence endings + newlines
        # Korean sentences end with: 다, 요, 오, 까, 니, 음, 죠, 임
        pattern = r'(?<=[다요오까니음죠임])[.\s]+(?=[가-힣A-Z0-9①②③④⑤■○▶\[])'
        parts = re.split(pattern, text)

        # Also split on double newlines and bullet points
        result = []
        for part in parts:
            sub_parts = re.split(r'\n\s*\n', part)
            result.extend(sub_parts)

        return [s.strip() for s in result if s.strip()]

    def split_by_sections(self, text: str) -> List[Tuple[str, str]]:
        """문서를 섹션 단위로 분할 (header, body) 튜플 리스트 반환"""
        matches = list(self._section_re.finditer(text))

        if not matches:
            return [('', text)]

        sections = []

        # Text before first section header
        if matches[0].start() > 0:
            pre_text = text[:matches[0].start()].strip()
            if pre_text:
                sections.append(('', pre_text))

        for i, match in enumerate(matches):
            header = match.group().strip()
            # Body is text from end of this header to start of next header
            start = match.end()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
            body = text[start:end].strip()
            sections.append((header, body))

        return sections

    def _trim_to_overlap(self, sentences: List[str]) -> Tuple[List[str], int]:
        """오버랩을 위해 마지막 N토큰 분량의 문장만 유지"""
        result = []
        total = 0
        for sent in reversed(sentences):
            t = self.estimate_tokens(sent)
            if total + t > self.overlap:
                break
            result.insert(0, sent)
            total += t
        return result, total

    def chunk_document(
        self,
        markdown_text: str,
        bid_notice_no: str,
        document_id: Optional[int] = None,
    ) -> List[DocumentChunk]:
        """
        마크다운 문서를 청크로 분할

        Args:
            markdown_text: 변환된 마크다운 텍스트 (full text)
            bid_notice_no: 입찰공고번호
            document_id: 문서 ID (optional)

        Returns:
            DocumentChunk 리스트
        """
        if not markdown_text or not markdown_text.strip():
            return []

        chunks = []
        chunk_idx = 0

        # Step 1: Split by sections
        sections = self.split_by_sections(markdown_text)

        for header, body in sections:
            combined = f"{header}\n{body}".strip() if header else body.strip()
            if not combined:
                continue

            section_type = self.detect_section_type(combined)
            section_tokens = self.estimate_tokens(combined)

            # Small enough section: keep as single chunk
            if section_tokens <= self.max_tokens:
                if section_tokens >= self.min_tokens:
                    chunks.append(DocumentChunk(
                        text=combined,
                        section_type=section_type,
                        chunk_index=chunk_idx,
                        token_count=section_tokens,
                        metadata={
                            'bid_notice_no': bid_notice_no,
                            'document_id': document_id,
                        }
                    ))
                    chunk_idx += 1
                continue

            # Large section: sliding window over sentences
            sentences = self.split_sentences(body)
            if not sentences:
                # Fallback: split by characters
                sentences = [body[i:i+500] for i in range(0, len(body), 500)]

            window: List[str] = []
            header_tokens = self.estimate_tokens(header) if header else 0
            window_tokens = header_tokens

            for sentence in sentences:
                sent_tokens = self.estimate_tokens(sentence)

                # Would exceed max? Emit current window
                if window_tokens + sent_tokens > self.max_tokens and window:
                    chunk_text = f"{header}\n{' '.join(window)}".strip() if header else ' '.join(window)
                    chunks.append(DocumentChunk(
                        text=chunk_text,
                        section_type=section_type,
                        chunk_index=chunk_idx,
                        token_count=window_tokens,
                        metadata={
                            'bid_notice_no': bid_notice_no,
                            'document_id': document_id,
                        }
                    ))
                    chunk_idx += 1

                    # Keep overlap
                    window, window_tokens = self._trim_to_overlap(window)
                    window_tokens += header_tokens

                window.append(sentence)
                window_tokens += sent_tokens

            # Emit remaining window
            if window and window_tokens >= self.min_tokens:
                chunk_text = f"{header}\n{' '.join(window)}".strip() if header else ' '.join(window)
                chunks.append(DocumentChunk(
                    text=chunk_text,
                    section_type=section_type,
                    chunk_index=chunk_idx,
                    token_count=window_tokens,
                    metadata={
                        'bid_notice_no': bid_notice_no,
                        'document_id': document_id,
                    }
                ))
                chunk_idx += 1

        logger.info(f"문서 청킹 완료: bid={bid_notice_no}, chunks={len(chunks)}, "
                     f"avg_tokens={sum(c.token_count for c in chunks) // max(1, len(chunks))}")

        return chunks


# Module-level convenience instance
_chunker: Optional[KoreanProcurementChunker] = None

def get_chunker() -> KoreanProcurementChunker:
    """청커 싱글턴 인스턴스"""
    global _chunker
    if _chunker is None:
        _chunker = KoreanProcurementChunker()
    return _chunker
