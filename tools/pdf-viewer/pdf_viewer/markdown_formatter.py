"""
PDF 마크다운 포맷터 - HWP와 유사한 중요 정보 강조 기능
"""

import re
from typing import List


class PDFMarkdownFormatter:
    """PDF 내용을 마크다운으로 포맷하는 클래스"""

    def __init__(self, use_emoji: bool = False):
        self.use_emoji = use_emoji
        # PDF에서 자주 나타나는 중요 패턴들
        self.important_patterns = {
            # 날짜 패턴
            'dates': [
                r'(\\d{4}년\\s*\\d{1,2}월\\s*\\d{1,2}일)',
                r'(\\d{4}\\.\\d{1,2}\\.\\d{1,2})',
                r'(\\d{4}-\\d{1,2}-\\d{1,2})',
                r'(\\d{2}/\\d{2}/\\d{4})',
                r'(납기.*?\\d{4}년.*?\\d{1,2}월.*?\\d{1,2}일)',
                r'(납품.*?\\d{4}년.*?\\d{1,2}월.*?\\d{1,2}일)',
            ],
            # 금액 패턴
            'amounts': [
                r'(\\d{1,3}(?:,\\d{3})*원)',
                r'(\\d+억\\s*원?)',
                r'(\\d+만\\s*원?)',
                r'(USD\\s*\\d+)',
                r'(\\$\\d+)',
                r'(예정가격.*?\\d+)',
                r'(계약금액.*?\\d+)',
            ],
            # 기술 키워드
            'tech_keywords': [
                r'(GPU|CPU|RAM|SSD|NVMe)',
                r'(AI|인공지능)',
                r'(딥러닝|Deep\\s*Learning)',
                r'(머신러닝|Machine\\s*Learning)',
                r'(CUDA\\s*Cores?)',
                r'(RTX\\s*\\d+)',
                r'(Intel\\s*Xeon)',
                r'(\\d+GB)',
                r'(\\d+TB)',
            ],
            # 사양 및 수량
            'specifications': [
                r'(\\d+대)',
                r'(\\d+개)',
                r'(\\d+식)',
                r'(\\d+개소)',
                r'(\\d+년\\s*보증)',
                r'(H/W\\s*무상보증)',
                r'(\\d+-?[Cc]ores?)',
                r'(\\d+-?[Tt]hreads?)',
                r'(\\d+\\.\\d+GHz)',
            ],
            # 기관 및 회사
            'organizations': [
                r'(.*?대학교)',
                r'(.*?연구원)',
                r'(.*?연구소)',
                r'(.*?주식회사)',
                r'(.*?\\(주\\))',
                r'(발주처)',
                r'(수급인)',
                r'(납품업체)',
            ],
            # 중요 조건
            'conditions': [
                r'(필수\\s*조건)',
                r'(납품\\s*조건)',
                r'(보증\\s*조건)',
                r'(설치\\s*조건)',
                r'(※.*?[다\\.])(?=\\s|$)',
                r'(주의사항)',
                r'(특이사항)',
                r'(별도\\s*협의)',
            ]
        }

    def format_document(self, title: str, content: str, metadata: dict = None,
                       pages: List[dict] = None) -> str:
        """PDF 문서를 마크다운으로 포맷팅"""
        md_content = []

        # 제목
        md_content.append(f"# {title}\\n")

        # 메타데이터
        if metadata:
            md_content.append("## 📋 문서 정보\\n")
            for key, value in metadata.items():
                if value:
                    md_content.append(f"- **{key}**: {value}")
            md_content.append("\\n---\\n")

        # 핵심 정보 요약 섹션
        summary = self._extract_key_info(content)
        if summary:
            md_content.append("## 🎯 핵심 정보\\n")
            md_content.extend(summary)
            md_content.append("\\n---\\n")

        # 페이지별 내용 (있는 경우)
        if pages and len(pages) > 1:
            md_content.append("## 📄 페이지별 내용\\n")
            for page in pages[:3]:  # 처음 3페이지만 표시
                if page.get('text'):
                    md_content.append(f"### 📄 페이지 {page.get('page_num', 'N/A')}\\n")
                    formatted_page = self._format_content(page['text'])
                    md_content.append(formatted_page)
                    md_content.append("\\n")

            if len(pages) > 3:
                md_content.append(f"*... 총 {len(pages)}페이지 중 처음 3페이지만 표시*\\n\\n")

        # 전체 내용
        md_content.append("## 📑 전체 내용\\n")
        formatted_content = self._format_content(content)
        md_content.append(formatted_content)

        # 테이블 정보 (있는 경우)
        if pages:
            tables_count = sum(len(page.get('tables', [])) for page in pages)
            if tables_count > 0:
                md_content.append(f"\\n---\\n\\n## 📊 문서 통계\\n")
                md_content.append(f"- **총 페이지**: {len(pages)}페이지")
                md_content.append(f"- **테이블**: {tables_count}개")
                md_content.append(f"- **텍스트 길이**: {len(content):,}자")

        return "\\n".join(md_content)

    def _extract_key_info(self, content: str) -> List[str]:
        """핵심 정보 자동 추출"""
        key_info = []

        # 날짜 추출
        dates = self._find_all_patterns(content, self.important_patterns['dates'])
        if dates:
            emoji = "📅 " if self.use_emoji else ""
            key_info.append(f"**{emoji}주요 일정**: {', '.join(set(dates[:3]))}")

        # 금액 추출
        amounts = self._find_all_patterns(content, self.important_patterns['amounts'])
        if amounts:
            emoji = "💰 " if self.use_emoji else ""
            key_info.append(f"**{emoji}관련 금액**: {', '.join(set(amounts[:3]))}")

        # 기술 키워드 추출
        tech_keywords = self._find_all_patterns(content, self.important_patterns['tech_keywords'])
        if tech_keywords:
            emoji = "🔧 " if self.use_emoji else ""
            key_info.append(f"**{emoji}기술 키워드**: {', '.join(set(tech_keywords[:5]))}")

        # 사양 추출
        specs = self._find_all_patterns(content, self.important_patterns['specifications'])
        if specs:
            emoji = "📊 " if self.use_emoji else ""
            key_info.append(f"**{emoji}주요 사양**: {', '.join(set(specs[:5]))}")

        # 기관명 추출
        orgs = self._find_all_patterns(content, self.important_patterns['organizations'])
        if orgs:
            emoji = "🏢 " if self.use_emoji else ""
            key_info.append(f"**{emoji}관련 기관**: {', '.join(set(orgs[:3]))}")

        # 조건 추출
        conditions = self._find_all_patterns(content, self.important_patterns['conditions'])
        if conditions:
            emoji = "⚠️ " if self.use_emoji else ""
            key_info.append(f"**{emoji}중요 조건**: {', '.join(set(conditions[:3]))}")

        return [item + "\\n" for item in key_info]

    def _format_content(self, content: str) -> str:
        """본문 내용 포맷팅 및 강조"""
        lines = content.split('\\n')
        formatted_lines = []

        for line in lines:
            if not line.strip():
                formatted_lines.append('')
                continue

            # 제목 형태 감지
            if re.match(r'^[ⅠⅡⅢⅣⅤⅥⅦⅧⅨⅩ]\\.', line.strip()):
                formatted_lines.append(f"## {line.strip()}")
            elif re.match(r'^\\d+\\.', line.strip()):
                level = len(re.match(r'^\\d+', line.strip()).group()) + 2
                formatted_lines.append(f"{'#' * level} {line.strip()}")
            elif re.match(r'^[①-⑳]', line.strip()) or re.match(r'^\\([0-9]+\\)', line.strip()):
                formatted_lines.append(f"### {line.strip()}")
            elif line.strip().startswith('○') or line.strip().startswith('◦'):
                formatted_lines.append(f"**{line.strip()}**")
            else:
                # 일반 텍스트에 강조 적용
                emphasized_text = self._emphasize_important_text(line)
                formatted_lines.append(emphasized_text)

            formatted_lines.append('')  # 줄 간격

        return '\\n'.join(formatted_lines)

    def _emphasize_important_text(self, text: str) -> str:
        """중요한 텍스트 강조 처리"""
        # 날짜 강조
        emoji = "📅 " if self.use_emoji else ""
        for pattern in self.important_patterns['dates']:
            text = re.sub(pattern, rf'**{emoji}\1**', text, flags=re.IGNORECASE)

        # 금액 강조
        emoji = "💰 " if self.use_emoji else ""
        for pattern in self.important_patterns['amounts']:
            text = re.sub(pattern, rf'**{emoji}\1**', text, flags=re.IGNORECASE)

        # 기술 키워드 강조
        emoji = "🔧 " if self.use_emoji else ""
        for pattern in self.important_patterns['tech_keywords']:
            text = re.sub(pattern, rf'**{emoji}\1**', text, flags=re.IGNORECASE)

        # 사양 강조
        emoji = "📊 " if self.use_emoji else ""
        for pattern in self.important_patterns['specifications']:
            text = re.sub(pattern, rf'**{emoji}\1**', text, flags=re.IGNORECASE)

        # 기관명 강조
        emoji = "🏢 " if self.use_emoji else ""
        for pattern in self.important_patterns['organizations']:
            text = re.sub(pattern, rf'**{emoji}\1**', text, flags=re.IGNORECASE)

        # 조건 강조
        emoji = "⚠️ " if self.use_emoji else ""
        for pattern in self.important_patterns['conditions']:
            text = re.sub(pattern, rf'**{emoji}\1**', text, flags=re.IGNORECASE)

        return text

    def _find_all_patterns(self, text: str, patterns: List[str]) -> List[str]:
        """패턴에 매칭되는 모든 텍스트 찾기"""
        matches = []
        for pattern in patterns:
            found = re.findall(pattern, text, flags=re.IGNORECASE)
            matches.extend(found)
        return matches