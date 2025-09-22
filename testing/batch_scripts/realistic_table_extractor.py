#!/usr/bin/env python
"""
현실적인 표 데이터 추출 전략
- hwp5txt 출력을 최대한 활용
- GPT-4 보조 추출
- 패턴 매칭 고도화
"""

import re
import subprocess
import json
from pathlib import Path
from typing import Dict, List, Any
# import openai  # 선택사항


class RealisticTableExtractor:
    """현실적인 표 데이터 추출기"""

    def __init__(self):
        self.openai_api_key = None  # 필요시 설정

    def extract_structured_data(self, hwp_path: Path, bid_notice_no: str) -> Dict:
        """HWP에서 구조화된 데이터 추출"""

        print(f"🔍 구조화된 데이터 추출: {bid_notice_no}")

        # 1. hwp5txt로 원시 텍스트 추출
        raw_text = self.extract_raw_text(hwp_path)
        if not raw_text:
            return {}

        # 2. 다양한 방법으로 정보 추출
        extracted = {
            'bid_notice_no': bid_notice_no,
            'prices': self.extract_price_info(raw_text),
            'dates': self.extract_date_info(raw_text),
            'contract_details': self.extract_contract_details(raw_text),
            'table_structures': self.identify_table_structures(raw_text)
        }

        # 3. GPT-4 보조 추출 (선택사항)
        if self.openai_api_key:
            gpt_extracted = self.extract_with_gpt4(raw_text)
            extracted['gpt4_enhanced'] = gpt_extracted

        return extracted

    def extract_raw_text(self, hwp_path: Path) -> str:
        """hwp5txt로 원시 텍스트 추출"""

        try:
            result = subprocess.run([
                'hwp5txt', str(hwp_path)
            ], capture_output=True, text=True, timeout=30)

            if result.returncode == 0:
                return result.stdout
            else:
                print(f"❌ hwp5txt 실패: {result.stderr}")
                return ""

        except Exception as e:
            print(f"❌ 텍스트 추출 오류: {e}")
            return ""

    def extract_price_info(self, text: str) -> Dict:
        """금액 정보 추출 (고도화된 패턴)"""

        prices = {}

        # 다양한 금액 패턴들
        price_patterns = [
            # 기본 패턴
            (r'추정가격[:\s]*([0-9,]+)\s*원', 'estimated_price'),
            (r'예정가격[:\s]*([0-9,]+)\s*원', 'budget_price'),
            (r'기준가격[:\s]*([0-9,]+)\s*원', 'base_price'),

            # 표 형태 패턴 (항목명과 금액이 분리된 형태)
            (r'추정가격.*?(\d{1,3}(?:,\d{3})*)', 'estimated_price'),
            (r'예가.*?(\d{1,3}(?:,\d{3})*)', 'budget_price'),
            (r'총액.*?(\d{1,3}(?:,\d{3})*)', 'total_amount'),

            # 부가세 관련
            (r'부가가치세[:\s]*([0-9,]+)', 'vat_amount'),
            (r'VAT[:\s]*([0-9,]+)', 'vat_amount'),

            # 금액 범위
            (r'(\d{1,3}(?:,\d{3})*)\s*원?\s*[~\-]\s*(\d{1,3}(?:,\d{3})*)\s*원?', 'price_range'),
        ]

        for pattern, field_name in price_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE | re.MULTILINE)

            if matches:
                if field_name == 'price_range' and len(matches[0]) == 2:
                    # 가격 범위 처리
                    try:
                        min_price = int(matches[0][0].replace(',', ''))
                        max_price = int(matches[0][1].replace(',', ''))
                        prices['min_price'] = min_price
                        prices['max_price'] = max_price
                        print(f"💰 가격 범위: {min_price:,}원 ~ {max_price:,}원")
                    except ValueError:
                        continue
                else:
                    # 단일 금액 처리
                    try:
                        amount_str = matches[0] if isinstance(matches[0], str) else matches[0][0]
                        amount = int(amount_str.replace(',', ''))

                        # 합리적인 금액 범위 체크 (100원 ~ 100억원)
                        if 100 <= amount <= 10_000_000_000:
                            prices[field_name] = amount
                            print(f"💰 {field_name}: {amount:,}원")

                    except (ValueError, IndexError):
                        continue

        return prices

    def extract_date_info(self, text: str) -> Dict:
        """날짜 정보 추출"""

        dates = {}

        # 날짜 패턴들
        date_patterns = [
            # 기본 일정
            (r'공고일[:\s]*(\d{4})[.\-/](\d{1,2})[.\-/](\d{1,2})', 'announcement_date'),
            (r'입찰마감[:\s]*(\d{4})[.\-/](\d{1,2})[.\-/](\d{1,2})', 'submission_deadline'),
            (r'개찰일[:\s]*(\d{4})[.\-/](\d{1,2})[.\-/](\d{1,2})', 'opening_date'),

            # 시간 포함
            (r'(\d{4})[.\-/](\d{1,2})[.\-/](\d{1,2})\s+(\d{1,2}):(\d{2})', 'datetime_full'),

            # 제출 관련
            (r'제출.*?(\d{4})[.\-/](\d{1,2})[.\-/](\d{1,2})', 'submission_date'),
            (r'견적.*?(\d{4})[.\-/](\d{1,2})[.\-/](\d{1,2})', 'quotation_date'),

            # 기간 형태
            (r'(\d{4})[.\-/](\d{1,2})[.\-/](\d{1,2}).*?(\d{4})[.\-/](\d{1,2})[.\-/](\d{1,2})', 'period'),
        ]

        for pattern, field_name in date_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)

            if matches:
                if field_name == 'period' and len(matches[0]) >= 6:
                    # 기간 처리
                    start_date = f"{matches[0][0]}-{matches[0][1].zfill(2)}-{matches[0][2].zfill(2)}"
                    end_date = f"{matches[0][3]}-{matches[0][4].zfill(2)}-{matches[0][5].zfill(2)}"
                    dates['period_start'] = start_date
                    dates['period_end'] = end_date
                    print(f"📅 기간: {start_date} ~ {end_date}")

                elif field_name == 'datetime_full' and len(matches[0]) >= 5:
                    # 날짜+시간 처리
                    datetime_str = f"{matches[0][0]}-{matches[0][1].zfill(2)}-{matches[0][2].zfill(2)} {matches[0][3].zfill(2)}:{matches[0][4]}"
                    dates['datetime'] = datetime_str
                    print(f"📅 일시: {datetime_str}")

                elif len(matches[0]) >= 3:
                    # 일반 날짜 처리
                    date_str = f"{matches[0][0]}-{matches[0][1].zfill(2)}-{matches[0][2].zfill(2)}"
                    dates[field_name] = date_str
                    print(f"📅 {field_name}: {date_str}")

        return dates

    def extract_contract_details(self, text: str) -> Dict:
        """계약 상세 정보 추출"""

        details = {}

        # 계약 관련 패턴들
        detail_patterns = [
            # 기본 정보
            (r'공사명[:\s]*(.+?)(?=\n|$)', 'project_name'),
            (r'공사위치[:\s]*(.+?)(?=\n|$)', 'location'),
            (r'공사기간[:\s]*(.+?)(?=\n|$)', 'duration'),
            (r'계약방법[:\s]*(.+?)(?=\n|$)', 'contract_method'),

            # 자격 요건
            (r'참가자격[:\s]*(.+?)(?=\n|$)', 'qualification'),
            (r'업종[:\s]*(.+?)(?=\n|$)', 'industry_type'),
            (r'지역제한[:\s]*(.+?)(?=\n|$)', 'region_restriction'),

            # 특별 조건
            (r'공동수급[:\s]*(.+?)(?=\n|$)', 'joint_venture'),
            (r'면세여부[:\s]*(.+?)(?=\n|$)', 'tax_exemption'),
        ]

        for pattern, field_name in detail_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE | re.MULTILINE)

            if matches:
                value = matches[0].strip()
                # 너무 길거나 짧은 텍스트 필터링
                if 3 <= len(value) <= 200:
                    details[field_name] = value
                    print(f"📋 {field_name}: {value}")

        return details

    def identify_table_structures(self, text: str) -> List[Dict]:
        """텍스트에서 표 구조 식별"""

        structures = []

        # 표 구조 패턴들
        table_patterns = [
            # 가나다 구조
            {
                'name': 'korean_alphabet',
                'pattern': r'가\.\s*(.+?)\s*나\.\s*(.+?)\s*다\.\s*(.+?)(?=\n|$)',
                'fields': ['항목1', '항목2', '항목3']
            },
            # 123 구조
            {
                'name': 'numbers',
                'pattern': r'1\.\s*(.+?)\s*2\.\s*(.+?)\s*3\.\s*(.+?)(?=\n|$)',
                'fields': ['항목1', '항목2', '항목3']
            },
            # 콜론 구분 구조
            {
                'name': 'colon_separated',
                'pattern': r'(.+?):\s*(.+?)(?=\n|$)',
                'fields': ['키', '값']
            }
        ]

        for table_pattern in table_patterns:
            matches = re.findall(table_pattern['pattern'], text, re.IGNORECASE | re.MULTILINE | re.DOTALL)

            if matches:
                structure = {
                    'type': table_pattern['name'],
                    'matches_count': len(matches),
                    'data': []
                }

                for match in matches[:5]:  # 최대 5개까지만
                    if isinstance(match, tuple):
                        row_data = {}
                        for i, field in enumerate(table_pattern['fields']):
                            if i < len(match):
                                value = match[i].strip()
                                if value and len(value) < 100:  # 너무 긴 텍스트 제외
                                    row_data[field] = value

                        if row_data:
                            structure['data'].append(row_data)

                if structure['data']:
                    structures.append(structure)
                    print(f"📊 표 구조 '{table_pattern['name']}': {len(structure['data'])}개 항목")

        return structures

    def extract_with_gpt4(self, text: str) -> Dict:
        """GPT-4를 활용한 보조 추출"""

        if not self.openai_api_key:
            return {}

        # GPT-4 구현 (필요시)
        return {}


def test_realistic_extraction():
    """현실적인 추출 테스트"""

    extractor = RealisticTableExtractor()

    hwp_path = Path("storage/documents/R25BK00556045/standard.hwp")
    bid_notice_no = "R25BK00556045"

    if hwp_path.exists():
        print("🔍 현실적인 표 데이터 추출 테스트")
        print("=" * 60)

        extracted = extractor.extract_structured_data(hwp_path, bid_notice_no)

        print("\n📊 추출 결과:")
        print("=" * 60)

        for category, data in extracted.items():
            if data and category != 'bid_notice_no':
                print(f"\n📋 {category.upper()}:")

                if isinstance(data, dict):
                    for key, value in data.items():
                        print(f"  {key}: {value}")
                elif isinstance(data, list):
                    for i, item in enumerate(data):
                        print(f"  {i+1}. {item}")

        # 결과를 JSON으로 저장
        output_path = Path(f"extracted_data_{bid_notice_no}.json")
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(extracted, f, ensure_ascii=False, indent=2)

        print(f"\n💾 결과 저장: {output_path}")

    else:
        print(f"❌ 파일 없음: {hwp_path}")


if __name__ == "__main__":
    test_realistic_extraction()