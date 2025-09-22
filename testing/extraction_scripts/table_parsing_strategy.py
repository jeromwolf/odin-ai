#!/usr/bin/env python
"""
HWP 표 파싱 전략
"""

import re
from pathlib import Path
import subprocess
import tempfile
import pandas as pd
from typing import List, Dict, Any


class HWPTableParser:
    """HWP 파일의 표 파싱을 위한 다층 전략"""

    def __init__(self):
        self.strategies = [
            self.strategy_1_hwp5_xml,      # hwp5 XML 모드
            self.strategy_2_libreoffice,   # LibreOffice 변환
            self.strategy_3_ocr_table,     # OCR 표 인식
            self.strategy_4_regex_fallback # 정규식 폴백
        ]

    def parse_tables_from_hwp(self, hwp_path: Path) -> List[Dict]:
        """HWP 파일에서 표 데이터 추출"""

        results = []

        for i, strategy in enumerate(self.strategies, 1):
            try:
                print(f"🔄 Strategy {i}: {strategy.__name__}")
                tables = strategy(hwp_path)

                if tables:
                    print(f"✅ Strategy {i} 성공: {len(tables)}개 표 발견")
                    results.extend(tables)
                    break
                else:
                    print(f"⚠️ Strategy {i} 실패: 표 없음")

            except Exception as e:
                print(f"❌ Strategy {i} 오류: {e}")
                continue

        return results

    def strategy_1_hwp5_xml(self, hwp_path: Path) -> List[Dict]:
        """Strategy 1: hwp5 XML 모드로 표 구조 파싱"""

        try:
            # hwp5 XML 모드로 실행
            result = subprocess.run([
                'hwp5', 'xml', str(hwp_path)
            ], capture_output=True, text=True, timeout=30)

            if result.returncode != 0:
                return []

            xml_content = result.stdout
            tables = self.parse_xml_tables(xml_content)

            return tables

        except Exception as e:
            print(f"hwp5 XML 오류: {e}")
            return []

    def parse_xml_tables(self, xml_content: str) -> List[Dict]:
        """XML에서 표 구조 파싱"""

        tables = []

        # HWP XML에서 표 찾기
        table_pattern = r'<hp:tbl[^>]*>(.*?)</hp:tbl>'
        table_matches = re.findall(table_pattern, xml_content, re.DOTALL)

        for i, table_xml in enumerate(table_matches):
            table_data = self.extract_table_from_xml(table_xml)
            if table_data:
                tables.append({
                    'table_id': i + 1,
                    'method': 'hwp5_xml',
                    'data': table_data,
                    'confidence': 0.9
                })

        return tables

    def extract_table_from_xml(self, table_xml: str) -> List[List[str]]:
        """XML 표에서 셀 데이터 추출"""

        rows = []

        # 행(row) 찾기
        row_pattern = r'<hp:tr[^>]*>(.*?)</hp:tr>'
        row_matches = re.findall(row_pattern, table_xml, re.DOTALL)

        for row_xml in row_matches:
            cells = []

            # 셀(cell) 찾기
            cell_pattern = r'<hp:tc[^>]*>(.*?)</hp:tc>'
            cell_matches = re.findall(cell_pattern, row_xml, re.DOTALL)

            for cell_xml in cell_matches:
                # 텍스트 추출
                text = self.extract_text_from_cell(cell_xml)
                cells.append(text.strip())

            if cells:  # 빈 행 제외
                rows.append(cells)

        return rows

    def extract_text_from_cell(self, cell_xml: str) -> str:
        """셀에서 순수 텍스트 추출"""

        # HTML 태그 제거
        text = re.sub(r'<[^>]+>', '', cell_xml)

        # 특수 문자 정리
        text = text.replace('&amp;', '&')
        text = text.replace('&lt;', '<')
        text = text.replace('&gt;', '>')
        text = text.replace('&quot;', '"')

        return text

    def strategy_2_libreoffice(self, hwp_path: Path) -> List[Dict]:
        """Strategy 2: LibreOffice로 변환 후 표 추출"""

        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)

                # LibreOffice로 ODS 변환
                result = subprocess.run([
                    '/opt/homebrew/bin/soffice', '--headless', '--convert-to', 'ods',
                    '--outdir', str(temp_path), str(hwp_path)
                ], capture_output=True, timeout=60)

                if result.returncode != 0:
                    return []

                # 변환된 ODS 파일 찾기
                ods_files = list(temp_path.glob('*.ods'))
                if not ods_files:
                    return []

                # pandas로 표 읽기
                tables = []

                try:
                    # ODS 파일의 모든 시트 읽기
                    df_dict = pd.read_excel(ods_files[0], sheet_name=None, engine='odf')

                    for sheet_name, df in df_dict.items():
                        if not df.empty:
                            # DataFrame을 리스트로 변환
                            table_data = df.fillna('').astype(str).values.tolist()

                            # 헤더 추가
                            headers = df.columns.tolist()
                            table_data.insert(0, headers)

                            tables.append({
                                'table_id': len(tables) + 1,
                                'method': 'libreoffice_ods',
                                'sheet_name': sheet_name,
                                'data': table_data,
                                'confidence': 0.8
                            })

                except Exception as e:
                    print(f"ODS 파싱 오류: {e}")
                    return []

                return tables

        except Exception as e:
            print(f"LibreOffice 변환 오류: {e}")
            return []

    def strategy_3_ocr_table(self, hwp_path: Path) -> List[Dict]:
        """Strategy 3: OCR 기반 표 인식"""

        try:
            # HWP를 이미지로 변환 후 OCR 표 인식
            # (복잡하므로 일단 패스, 필요시 구현)
            return []

        except Exception as e:
            print(f"OCR 표 인식 오류: {e}")
            return []

    def strategy_4_regex_fallback(self, hwp_path: Path) -> List[Dict]:
        """Strategy 4: 정규식 폴백 (기존 텍스트에서 패턴 찾기)"""

        try:
            # hwp5txt로 텍스트 추출
            result = subprocess.run([
                'hwp5txt', str(hwp_path)
            ], capture_output=True, text=True, timeout=30)

            if result.returncode != 0:
                return []

            text = result.stdout

            # 텍스트에서 표 형태 패턴 찾기
            tables = self.extract_tables_from_text(text)

            return tables

        except Exception as e:
            print(f"정규식 폴백 오류: {e}")
            return []

    def extract_tables_from_text(self, text: str) -> List[Dict]:
        """텍스트에서 표 형태 패턴 추출"""

        tables = []

        # 금액 표 패턴 찾기
        price_patterns = [
            r'추정가격.*?([0-9,]+).*?원',
            r'예정가격.*?([0-9,]+).*?원',
            r'(\d{1,3}(?:,\d{3})*)\s*원',
        ]

        found_prices = []
        for pattern in price_patterns:
            matches = re.findall(pattern, text, re.MULTILINE | re.DOTALL)
            found_prices.extend(matches)

        if found_prices:
            # 금액 정보를 표 형태로 구성
            price_table = [
                ['항목', '금액'],
                ['추정가격', f"{found_prices[0] if found_prices else ''}원"]
            ]

            tables.append({
                'table_id': 1,
                'method': 'regex_price',
                'data': price_table,
                'confidence': 0.6
            })

        return tables


class TableAnalyzer:
    """추출된 표 데이터 분석"""

    def analyze_price_table(self, table_data: List[List[str]]) -> Dict:
        """금액 관련 표 분석"""

        price_info = {}

        for row in table_data:
            if len(row) >= 2:
                key = row[0].strip()
                value = row[1].strip()

                # 금액 관련 키워드 매칭
                if any(keyword in key for keyword in ['추정가격', '예정가격', '기준가격']):
                    # 숫자 추출
                    numbers = re.findall(r'([0-9,]+)', value)
                    if numbers:
                        price_info['estimated_price'] = int(numbers[0].replace(',', ''))

                elif any(keyword in key for keyword in ['예가', '예산']):
                    numbers = re.findall(r'([0-9,]+)', value)
                    if numbers:
                        price_info['budget_price'] = int(numbers[0].replace(',', ''))

                elif any(keyword in key for keyword in ['부가세', '부가가치세']):
                    numbers = re.findall(r'([0-9,]+)', value)
                    if numbers:
                        price_info['vat_amount'] = int(numbers[0].replace(',', ''))

        return price_info

    def analyze_schedule_table(self, table_data: List[List[str]]) -> Dict:
        """일정 관련 표 분석"""

        schedule_info = {}

        for row in table_data:
            if len(row) >= 2:
                key = row[0].strip()
                value = row[1].strip()

                # 일정 관련 키워드 매칭
                if any(keyword in key for keyword in ['공고일', '공고기간']):
                    schedule_info['announcement_date'] = self.parse_date(value)

                elif any(keyword in key for keyword in ['입찰마감', '제출마감']):
                    schedule_info['submission_deadline'] = self.parse_date(value)

                elif any(keyword in key for keyword in ['개찰일', '개찰시간']):
                    schedule_info['opening_date'] = self.parse_date(value)

        return schedule_info

    def parse_date(self, date_str: str) -> str:
        """날짜 문자열 파싱"""

        # 날짜 패턴 찾기
        date_patterns = [
            r'(\d{4})[/-](\d{1,2})[/-](\d{1,2})',  # YYYY-MM-DD
            r'(\d{4})\.(\d{1,2})\.(\d{1,2})',       # YYYY.MM.DD
            r'(\d{1,2})[/-](\d{1,2})[/-](\d{4})',  # MM/DD/YYYY
        ]

        for pattern in date_patterns:
            match = re.search(pattern, date_str)
            if match:
                return match.group(0)

        return date_str


# 테스트 함수
def test_table_parsing():
    """표 파싱 테스트"""

    parser = HWPTableParser()
    analyzer = TableAnalyzer()

    # 테스트할 HWP 파일 경로
    hwp_path = Path("storage/documents/R25BK00556045/standard.hwp")

    if hwp_path.exists():
        print(f"🔍 표 파싱 테스트: {hwp_path}")

        # 표 추출
        tables = parser.parse_tables_from_hwp(hwp_path)

        print(f"📊 추출된 표: {len(tables)}개")

        for table in tables:
            print(f"\n--- 표 {table['table_id']} ({table['method']}) ---")
            print(f"신뢰도: {table['confidence']}")

            data = table['data']
            for i, row in enumerate(data[:5]):  # 상위 5행만 출력
                print(f"  {i+1}: {row}")

            # 금액 정보 분석
            price_info = analyzer.analyze_price_table(data)
            if price_info:
                print(f"💰 금액 정보: {price_info}")

            # 일정 정보 분석
            schedule_info = analyzer.analyze_schedule_table(data)
            if schedule_info:
                print(f"📅 일정 정보: {schedule_info}")


if __name__ == "__main__":
    test_table_parsing()