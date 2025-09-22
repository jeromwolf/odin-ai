"""
HWP 고급 텍스트 추출기 - 표, OLE 객체 처리 강화
"""

import subprocess
import tempfile
import zipfile
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from loguru import logger

try:
    from bs4 import BeautifulSoup
    HAS_BS4 = True
except ImportError:
    HAS_BS4 = False

try:
    import olefile
    HAS_OLEFILE = True
except ImportError:
    HAS_OLEFILE = False


class HWPAdvancedExtractor:
    """HWP 파일 고급 추출기"""

    def __init__(self):
        self.extraction_methods = [
            ('hwp5html', self._extract_with_html),
            ('hwp5txt_table', self._extract_with_table_mode),
            ('libreoffice', self._extract_with_libreoffice),
            ('ole_extraction', self._extract_ole_objects),
            ('hwpx_xml', self._extract_from_hwpx)
        ]

    async def extract(self, file_path: Path) -> Tuple[str, Dict]:
        """
        HWP 파일에서 텍스트, 표, OLE 객체 추출

        Returns:
            (text_content, metadata)
        """
        results = []
        metadata = {
            'tables_found': 0,
            'ole_objects': [],
            'extraction_methods': []
        }

        for method_name, method in self.extraction_methods:
            try:
                logger.debug(f"시도: {method_name}")
                text, meta = await method(file_path)
                if text:
                    results.append(text)
                    metadata['extraction_methods'].append(method_name)
                    if meta:
                        metadata.update(meta)
            except Exception as e:
                logger.debug(f"{method_name} 실패: {e}")
                continue

        # 결과 병합
        final_text = '\n\n=====\n\n'.join(results) if results else ""
        return final_text, metadata

    async def _extract_with_html(self, file_path: Path) -> Tuple[str, Dict]:
        """hwp5html을 사용한 HTML 변환 후 표 추출"""
        if not HAS_BS4:
            return "", {}

        with tempfile.NamedTemporaryFile(suffix='.html', delete=False) as tmp:
            result = subprocess.run(
                ['hwp5html', '--output', tmp.name, str(file_path)],
                capture_output=True,
                timeout=30
            )

            if result.returncode != 0:
                return "", {}

            with open(tmp.name, 'r', encoding='utf-8') as f:
                html_content = f.read()

        soup = BeautifulSoup(html_content, 'html.parser')

        # 텍스트와 표 추출
        text_parts = []
        table_count = 0

        for element in soup.find_all(['p', 'table', 'h1', 'h2', 'h3', 'ul', 'ol']):
            if element.name == 'table':
                table_count += 1
                table_md = self._html_table_to_markdown(element)
                text_parts.append(f"\n### [표 {table_count}]\n{table_md}\n")
            elif element.name in ['ul', 'ol']:
                items = element.find_all('li')
                for item in items:
                    text_parts.append(f"• {item.get_text(strip=True)}")
            else:
                text = element.get_text(strip=True)
                if text:
                    text_parts.append(text)

        return '\n'.join(text_parts), {'tables_found': table_count}

    async def _extract_with_table_mode(self, file_path: Path) -> Tuple[str, Dict]:
        """hwp5txt의 테이블 모드 사용"""
        result = subprocess.run(
            ['hwp5txt', '--table', str(file_path)],
            capture_output=True,
            text=True,
            encoding='utf-8',
            timeout=30
        )

        if result.returncode == 0 and result.stdout:
            # 표 구분자 찾기
            lines = result.stdout.split('\n')
            table_count = sum(1 for line in lines if '┌' in line or '├' in line)
            return result.stdout, {'tables_with_borders': table_count}

        return "", {}

    async def _extract_with_libreoffice(self, file_path: Path) -> Tuple[str, Dict]:
        """LibreOffice를 사용한 변환"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # HWP -> HTML 변환
            result = subprocess.run(
                [
                    'libreoffice', '--headless', '--convert-to', 'html',
                    '--outdir', tmpdir, str(file_path)
                ],
                capture_output=True,
                timeout=60
            )

            if result.returncode != 0:
                return "", {}

            # HTML 파일 찾기
            html_file = Path(tmpdir) / f"{file_path.stem}.html"
            if not html_file.exists():
                return "", {}

            with open(html_file, 'r', encoding='utf-8') as f:
                html = f.read()

            if HAS_BS4:
                soup = BeautifulSoup(html, 'html.parser')
                return soup.get_text(strip=True), {'libreoffice_conversion': True}
            else:
                # 기본 텍스트 추출
                import re
                text = re.sub('<[^<]+?>', '', html)
                return text, {'libreoffice_conversion': True}

    async def _extract_ole_objects(self, file_path: Path) -> Tuple[str, Dict]:
        """OLE 객체 추출 (Excel, 차트 등)"""
        if not HAS_OLEFILE:
            return "", {}

        ole_objects = []
        text_parts = []

        try:
            ole = olefile.OleFileIO(str(file_path))

            # OLE 스트림 목록
            for entry in ole.listdir():
                stream_path = '/'.join(entry)

                # Excel 객체 찾기
                if 'Excel' in stream_path or 'Workbook' in stream_path:
                    ole_objects.append({
                        'type': 'Excel',
                        'path': stream_path
                    })
                    # Excel 데이터 추출 시도
                    try:
                        data = ole.openstream(entry).read()
                        # 간단한 텍스트 추출
                        text = data.decode('utf-8', errors='ignore')
                        if text:
                            text_parts.append(f"[Excel 객체]\n{text[:500]}")
                    except:
                        pass

                # 차트 객체
                elif 'Chart' in stream_path:
                    ole_objects.append({
                        'type': 'Chart',
                        'path': stream_path
                    })

            ole.close()

        except Exception as e:
            logger.debug(f"OLE 추출 실패: {e}")

        return '\n'.join(text_parts), {'ole_objects': ole_objects}

    async def _extract_from_hwpx(self, file_path: Path) -> Tuple[str, Dict]:
        """HWPX (XML 기반) 파일 처리"""
        if file_path.suffix.lower() != '.hwpx':
            return "", {}

        text_parts = []
        metadata = {}

        try:
            with zipfile.ZipFile(file_path, 'r') as z:
                # 실제 문서 내용이 있는 파일들 처리
                content_files = [f for f in z.namelist()
                               if f.endswith('section0.xml') or 'section' in f and f.endswith('.xml')]

                if not content_files:
                    # section 파일이 없으면 다른 content 파일 찾기
                    content_files = [f for f in z.namelist()
                                   if 'content' in f.lower() and f.endswith('.xml')]

                logger.debug(f"HWPX 분석 파일: {content_files}")

                for filename in content_files:
                    with z.open(filename) as f:
                        content = f.read().decode('utf-8', errors='ignore')

                        # XML에서 텍스트 추출
                        parsed_text = self._parse_hwpx_xml(content)
                        if parsed_text:
                            text_parts.append(f"=== {filename} ===\n{parsed_text}")

                # Preview/PrvText.txt 파일도 확인 (있으면 사용)
                if 'Preview/PrvText.txt' in z.namelist():
                    with z.open('Preview/PrvText.txt') as f:
                        preview_text = f.read().decode('utf-8', errors='ignore')
                        if preview_text and len(preview_text) > 100:
                            text_parts.append(f"=== Preview Text ===\n{preview_text}")

                metadata['hwpx_processed'] = True
                metadata['content_files'] = len(content_files)
                metadata['preview_available'] = 'Preview/PrvText.txt' in z.namelist()
        except Exception as e:
            logger.debug(f"HWPX 처리 실패: {e}")

        return '\n'.join(text_parts), metadata

    def _parse_hwpx_xml(self, xml_content: str) -> str:
        """HWPX XML 내용에서 텍스트 추출"""
        try:
            if HAS_BS4:
                # BeautifulSoup으로 XML 파싱 (lxml 파서 사용)
                soup = BeautifulSoup(xml_content, 'xml')

                # 텍스트 노드들 추출
                text_elements = []

                # HWPX 전용 텍스트 태그들 찾기
                text_tags = soup.find_all(['hp:t'])  # 주요 텍스트 태그
                for tag in text_tags:
                    text = tag.get_text()
                    if text and text.strip() and len(text.strip()) > 1:
                        text_elements.append(text.strip())

                # 추가 텍스트 요소들
                if not text_elements:
                    # 다른 텍스트 포함 가능한 태그들
                    for tag_name in ['hp:p', 'hp:span', 'hp:run', 'text']:
                        tags = soup.find_all(tag_name)
                        for tag in tags:
                            text = tag.get_text()
                            if text and text.strip() and len(text.strip()) > 2:
                                text_elements.append(text.strip())

                # 여전히 없으면 모든 텍스트 추출
                if not text_elements:
                    text_elements = [text.strip() for text in soup.stripped_strings
                                    if text.strip() and len(text.strip()) > 2
                                    and not text.strip().startswith('<?xml')]

                # 중복 제거 및 정리
                unique_texts = []
                seen = set()
                for text in text_elements:
                    if text not in seen and len(text) > 3:
                        unique_texts.append(text)
                        seen.add(text)

                if unique_texts:
                    return '\n'.join(unique_texts)

            # BeautifulSoup 없을 때 정규식으로 기본 추출
            import re

            # hp:t 태그 내용 우선 추출
            text_matches = re.findall(r'<hp:t[^>]*>(.*?)</hp:t>', xml_content, re.DOTALL)
            if text_matches:
                texts = [match.strip() for match in text_matches if match.strip()]
                if texts:
                    return '\n'.join(texts)

            # 전체 XML 태그 제거
            text = re.sub(r'<[^>]+>', '', xml_content)
            text = re.sub(r'\s+', ' ', text)

            # 의미있는 텍스트만 추출
            lines = [line.strip() for line in text.split('\n')
                    if line.strip() and len(line.strip()) > 5
                    and not line.strip().startswith('<?xml')]

            return '\n'.join(lines[:50])  # 처음 50줄만 사용

        except Exception as e:
            logger.debug(f"HWPX XML 파싱 실패: {e}")
            return ""

    def _html_table_to_markdown(self, table_element) -> str:
        """HTML 테이블을 마크다운으로 변환"""
        rows = table_element.find_all('tr')
        if not rows:
            return ""

        md_lines = []
        max_cols = 0

        for i, row in enumerate(rows):
            cells = row.find_all(['td', 'th'])
            max_cols = max(max_cols, len(cells))

            # 셀 텍스트 추출
            cell_texts = []
            for cell in cells:
                text = cell.get_text(strip=True).replace('|', '\\|')
                # 줄바꿈을 공백으로
                text = ' '.join(text.split())
                cell_texts.append(text)

            # 빈 셀 채우기
            while len(cell_texts) < max_cols:
                cell_texts.append('')

            md_lines.append('| ' + ' | '.join(cell_texts) + ' |')

            # 헤더 구분선
            if i == 0:
                md_lines.append('|' + '---|' * max_cols)

        return '\n'.join(md_lines)


async def extract_hwp_advanced(file_path: Path) -> Dict:
    """
    HWP 파일 고급 추출 인터페이스

    Returns:
        {
            'text': str,
            'tables_count': int,
            'ole_objects': list,
            'extraction_methods': list,
            'success': bool
        }
    """
    extractor = HWPAdvancedExtractor()

    try:
        text, metadata = await extractor.extract(file_path)

        return {
            'text': text,
            'tables_count': metadata.get('tables_found', 0),
            'ole_objects': metadata.get('ole_objects', []),
            'extraction_methods': metadata.get('extraction_methods', []),
            'success': bool(text)
        }
    except Exception as e:
        logger.error(f"HWP 고급 추출 실패: {e}")
        return {
            'text': '',
            'tables_count': 0,
            'ole_objects': [],
            'extraction_methods': [],
            'success': False
        }