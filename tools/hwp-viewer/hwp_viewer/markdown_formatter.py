"""
마크다운 포맷터 - 중요한 정보를 자동으로 강조하는 모듈
"""

import re
from typing import List


class MarkdownFormatter:
    """마크다운 형식으로 HWP 내용을 포맷하는 클래스"""

    def __init__(self, use_emoji: bool = False):
        self.use_emoji = use_emoji
        # 강조할 패턴들 정의
        self.important_patterns = {
            # 날짜 패턴
            'dates': [
                r'(\d{4}년\s*\d{1,2}월\s*\d{1,2}일)',
                r'(계약일로부터\s+.*?까지)',
                r'(\d{4}\.\d{1,2}\.\d{1,2})',
                r'(\d{4}-\d{1,2}-\d{1,2})'
            ],
            # 금액 패턴
            'amounts': [
                r'(\d{1,3}(?:,\d{3})*원)',
                r'(\d+억\s*원?)',
                r'(\d+만\s*원?)',
                r'(예정가격.*?\d+)',
                r'(총\s*사업비.*?\d+)'
            ],
            # 중요 키워드
            'keywords': [
                r'(IoT)',
                r'(AI|인공지능)',
                r'(빅데이터|Big\s*Data)',
                r'(클라우드|Cloud)',
                r'(데이터분석|데이터\s*분석)',
                r'(모니터링)',
                r'(시스템\s*구축)',
                r'(플랫폼)',
                r'(디지털\s*전환)',
                r'(스마트)',
            ],
            # 회사명/기관명
            'organizations': [
                r'(한국.*?연구원)',
                r'(.*?공단)',
                r'(.*?청)',
                r'(.*?부)',
                r'(.*?지방자치단체)',
                r'(발주처)',
                r'(수급인)',
                r'(계약자)',
            ],
            # 기술 사양
            'specifications': [
                r'(\d+개소)',
                r'(\d+대)',
                r'(\d+식)',
                r'(\d+년\s*이상\s*경력)',
                r'(기술사)',
                r'(박사)',
                r'(석사)',
                r'([A-Z]{2,}\s*인증)',
                r'(ISO\s*\d+)',
            ],
            # 특이사항 및 조건
            'conditions': [
                r'(필수\s*조건)',
                r'(특이사항)',
                r'(주의사항)',
                r'(제한사항)',
                r'(필수\s*요구사항)',
                r'(의무사항)',
                r'(금지사항)',
                r'(준수사항)',
                r'(※.*?[다\.])(?=\s|$)',  # ※로 시작하는 주의사항
                r'(반드시\s+.*?[다\.])(?=\s|$)',
                r'(단,\s+.*?[다\.])(?=\s|$)',
                r'(다만,\s+.*?[다\.])(?=\s|$)',
                r'(단서조건)',
                r'(별도\s*협의)',
                r'(사전\s*승인)',
                r'(별도\s*지시)',
            ]
        }

    def format_document(self, title: str, content: str, metadata: dict = None) -> str:
        """문서를 마크다운으로 포맷팅"""
        md_content = []

        # 제목
        md_content.append(f"# {title}\n")

        # 메타데이터
        if metadata:
            md_content.append("## 📋 문서 정보\n")
            for key, value in metadata.items():
                if value:
                    md_content.append(f"- **{key}**: {value}")
            md_content.append("\n---\n")

        # 중요 정보 요약 섹션 추가
        summary = self._extract_key_info(content)
        if summary:
            md_content.append("## 🎯 핵심 정보\n")
            md_content.extend(summary)
            md_content.append("\n---\n")

        # 본문 내용
        md_content.append("## 📄 본문 내용\n")
        formatted_content = self._format_content(content)
        md_content.append(formatted_content)

        return "\n".join(md_content)

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
        keywords = self._find_all_patterns(content, self.important_patterns['keywords'])
        if keywords:
            emoji = "🔧 " if self.use_emoji else ""
            key_info.append(f"**{emoji}기술 키워드**: {', '.join(set(keywords[:5]))}")

        # 기관명 추출
        orgs = self._find_all_patterns(content, self.important_patterns['organizations'])
        if orgs:
            emoji = "🏢 " if self.use_emoji else ""
            key_info.append(f"**{emoji}관련 기관**: {', '.join(set(orgs[:3]))}")

        # 기술 사양 추출
        specs = self._find_all_patterns(content, self.important_patterns['specifications'])
        if specs:
            emoji = "📊 " if self.use_emoji else ""
            key_info.append(f"**{emoji}주요 사양**: {', '.join(set(specs[:5]))}")

        # 특이사항 및 조건 추출
        conditions = self._find_all_patterns(content, self.important_patterns['conditions'])
        if conditions:
            emoji = "⚠️ " if self.use_emoji else ""
            key_info.append(f"**{emoji}특이사항**: {', '.join(set(conditions[:3]))}")

        return [item + "\n" for item in key_info]

    def _format_content(self, content: str) -> str:
        """본문 내용 포맷팅 및 강조"""
        lines = content.split('\n')
        formatted_lines = []

        for line in lines:
            if not line.strip():
                formatted_lines.append('')
                continue

            # 제목 형태 감지 및 변환
            if re.match(r'^\d+\.', line.strip()):
                level = line.count('.', 0, 10) + 2  # H2, H3, H4...
                formatted_lines.append(f"{'#' * level} {line.strip()}")
            elif re.match(r'^[가-힣]\)', line.strip()):
                formatted_lines.append(f"### {line.strip()}")
            elif line.strip().startswith('○'):
                formatted_lines.append(f"**{line.strip()}**")
            elif line.strip().startswith('- '):
                # 리스트 아이템
                item_text = line.strip()[2:]
                emphasized_text = self._emphasize_important_text(item_text)
                formatted_lines.append(f"- {emphasized_text}")
            else:
                # 일반 텍스트
                emphasized_text = self._emphasize_important_text(line)
                formatted_lines.append(emphasized_text)

            formatted_lines.append('')  # 줄 간격

        return '\n'.join(formatted_lines)

    def _emphasize_important_text(self, text: str) -> str:
        """중요한 텍스트 강조 처리"""
        # 강조 우선순위: 날짜 > 금액 > 키워드 > 기관명

        # 날짜 강조
        emoji = "🗓️ " if self.use_emoji else ""
        for pattern in self.important_patterns['dates']:
            text = re.sub(pattern, rf'**{emoji}\1**', text, flags=re.IGNORECASE)

        # 금액 강조
        emoji = "💰 " if self.use_emoji else ""
        for pattern in self.important_patterns['amounts']:
            text = re.sub(pattern, rf'**{emoji}\1**', text, flags=re.IGNORECASE)

        # 기술 키워드 강조
        emoji = "🔧 " if self.use_emoji else ""
        for pattern in self.important_patterns['keywords']:
            text = re.sub(pattern, rf'**{emoji}\1**', text, flags=re.IGNORECASE)

        # 기관명 강조
        emoji = "🏢 " if self.use_emoji else ""
        for pattern in self.important_patterns['organizations']:
            text = re.sub(pattern, rf'**{emoji}\1**', text, flags=re.IGNORECASE)

        # 기술 사양 강조
        emoji = "📊 " if self.use_emoji else ""
        for pattern in self.important_patterns['specifications']:
            text = re.sub(pattern, rf'**{emoji}\1**', text, flags=re.IGNORECASE)

        # 특이사항 및 조건 강조
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

    def create_summary_table(self, content: str) -> str:
        """요약 테이블 생성"""
        dates = self._find_all_patterns(content, self.important_patterns['dates'])
        amounts = self._find_all_patterns(content, self.important_patterns['amounts'])
        keywords = self._find_all_patterns(content, self.important_patterns['keywords'])
        conditions = self._find_all_patterns(content, self.important_patterns['conditions'])

        table = "## 📊 정보 요약\n\n"
        table += "| 구분 | 내용 |\n"
        table += "|------|------|\n"

        if dates:
            table += f"| 📅 주요 일정 | {', '.join(set(dates[:3]))} |\n"
        if amounts:
            table += f"| 💰 관련 금액 | {', '.join(set(amounts[:2]))} |\n"
        if keywords:
            table += f"| 🔧 핵심 기술 | {', '.join(set(keywords[:5]))} |\n"
        if conditions:
            table += f"| ⚠️ 특이사항 | {', '.join(set(conditions[:3]))} |\n"

        table += "\n"
        return table