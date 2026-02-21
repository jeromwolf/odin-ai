#!/usr/bin/env python
"""
개선된 표 파싱 (현재 환경에 최적화)
"""

import re
import subprocess
from pathlib import Path
from typing import List, Dict, Any


class CurrentEnvironmentTableParser:
    """현재 환경에서 가능한 최선의 표 파싱"""

    def __init__(self):
        self.bid_notice_no = None

    def parse_hwp_enhanced(self, hwp_path: Path, bid_notice_no: str) -> Dict:
        """현재 환경에서 최대한 정확한 표 파싱"""

        self.bid_notice_no = bid_notice_no

        # hwp5txt로 텍스트 추출
        try:
            result = subprocess.run([
                'hwp5txt', str(hwp_path)
            ], capture_output=True, text=True, timeout=30)

            if result.returncode != 0:
                return {}

            text = result.stdout

            # 다양한 방법으로 정보 추출
            extracted_info = {
                'prices': self.extract_enhanced_prices(text),
                'dates': self.extract_enhanced_dates(text),
                'details': self.extract_contract_details(text),
                'raw_tables': self.identify_table_regions(text)
            }

            return extracted_info

        except Exception as e:
            print(f"HWP 파싱 오류: {e}")
            return {}

    def extract_enhanced_prices(self, text: str) -> Dict:
        """향상된 금액 정보 추출"""

        prices = {}

        # 더 정교한 금액 패턴들
        price_patterns = [
            # 기본 금액 패턴
            (r'추정가격[:\s]*([0-9,]+)\s*원', 'estimated_price'),
            (r'공사추정금액[:\s]*([0-9,]+)\s*원', 'estimated_price'),
            (r'예정가격[:\s]*([0-9,]+)\s*원', 'budget_price'),
            (r'기준가격[:\s]*([0-9,]+)\s*원', 'base_price'),

            # 표 내부 패턴 (콜론이나 공백으로 구분)
            (r'추정가격\s*[:\s]\s*([0-9,]+)', 'estimated_price'),
            (r'예가\s*[:\s]\s*([0-9,]+)', 'budget_price'),
            (r'총액\s*[:\s]\s*([0-9,]+)', 'total_amount'),

            # 부가세 관련
            (r'부가가치세[:\s]*([0-9,]+)\s*원', 'vat_amount'),
            (r'부가세[:\s]*([0-9,]+)\s*원', 'vat_amount'),

            # 복합 패턴 (금액 + 설명)
            (r'([0-9,]+)\s*원.*?추정', 'estimated_price'),
            (r'([0-9,]+)\s*원.*?예정', 'budget_price'),
        ]

        for pattern, field_name in price_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE | re.MULTILINE)

            if matches:
                try:
                    # 가장 큰 금액 선택 (일반적으로 추정가격이 가장 큼)
                    amounts = [int(match.replace(',', '')) for match in matches if match.replace(',', '').isdigit()]
                    if amounts:
                        prices[field_name] = max(amounts)
                        print(f"💰 {field_name}: {max(amounts):,}원 (패턴: {pattern})")
                except ValueError:
                    continue

        # 범위 금액 추출 (예: 1,000,000원 ~ 5,000,000원)
        range_pattern = r'([0-9,]+)\s*원\s*[~\-]\s*([0-9,]+)\s*원'
        range_matches = re.findall(range_pattern, text)

        if range_matches:
            try:
                min_price = int(range_matches[0][0].replace(',', ''))
                max_price = int(range_matches[0][1].replace(',', ''))
                prices['min_price'] = min_price
                prices['max_price'] = max_price
                print(f"💰 가격 범위: {min_price:,}원 ~ {max_price:,}원")
            except ValueError:
                pass

        return prices

    def extract_enhanced_dates(self, text: str) -> Dict:
        """향상된 날짜 정보 추출"""

        dates = {}

        # 날짜 패턴들 (다양한 형식 지원)
        date_patterns = [
            # 기본 일정 패턴
            (r'공고일[:\s]*(\d{4})[.\-/](\d{1,2})[.\-/](\d{1,2})', 'announcement_date'),
            (r'입찰마감[:\s]*(\d{4})[.\-/](\d{1,2})[.\-/](\d{1,2})', 'submission_deadline'),
            (r'개찰일[:\s]*(\d{4})[.\-/](\d{1,2})[.\-/](\d{1,2})', 'opening_date'),

            # 시간 포함 패턴
            (r'(\d{4})[.\-/](\d{1,2})[.\-/](\d{1,2})\s*(\d{1,2}):(\d{2})', 'datetime_pattern'),

            # 제출 기간 패턴
            (r'제출기간[:\s]*(\d{4})[.\-/](\d{1,2})[.\-/](\d{1,2}).*?(\d{4})[.\-/](\d{1,2})[.\-/](\d{1,2})', 'submission_period'),

            # 견적 관련 일정
            (r'견적.*?제출[:\s]*(\d{4})[.\-/](\d{1,2})[.\-/](\d{1,2})', 'quotation_deadline'),
        ]

        for pattern, field_name in date_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)

            if matches:
                if field_name == 'submission_period' and len(matches[0]) >= 6:
                    # 제출 기간 (시작~끝)
                    start_date = f"{matches[0][0]}-{matches[0][1].zfill(2)}-{matches[0][2].zfill(2)}"
                    end_date = f"{matches[0][3]}-{matches[0][4].zfill(2)}-{matches[0][5].zfill(2)}"
                    dates['submission_start'] = start_date
                    dates['submission_end'] = end_date
                    print(f"📅 제출기간: {start_date} ~ {end_date}")

                elif len(matches[0]) >= 3:
                    # 단일 날짜
                    date_str = f"{matches[0][0]}-{matches[0][1].zfill(2)}-{matches[0][2].zfill(2)}"
                    dates[field_name] = date_str
                    print(f"📅 {field_name}: {date_str}")

        return dates

    def extract_contract_details(self, text: str) -> Dict:
        """계약 상세 정보 추출"""

        details = {}

        # 계약 관련 패턴들
        detail_patterns = [
            (r'공사명[:\s]*(.+?)(?:\n|$)', 'project_name'),
            (r'공사위치[:\s]*(.+?)(?:\n|$)', 'location'),
            (r'공사기간[:\s]*(.+?)(?:\n|$)', 'duration'),
            (r'계약방법[:\s]*(.+?)(?:\n|$)', 'contract_method'),
            (r'입찰방법[:\s]*(.+?)(?:\n|$)', 'bidding_method'),

            # 자격 요건
            (r'참가자격[:\s]*(.+?)(?:\n|$)', 'qualification'),
            (r'업종[:\s]*(.+?)(?:\n|$)', 'industry_type'),
            (r'지역제한[:\s]*(.+?)(?:\n|$)', 'region_restriction'),

            # 특별 조건
            (r'공동수급[:\s]*(.+?)(?:\n|$)', 'joint_venture'),
            (r'면세[:\s]*(.+?)(?:\n|$)', 'tax_exemption'),
        ]

        for pattern, field_name in detail_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)

            if matches:
                value = matches[0].strip()
                if value and len(value) < 200:  # 너무 긴 텍스트 제외
                    details[field_name] = value
                    print(f"📋 {field_name}: {value}")

        return details

    def identify_table_regions(self, text: str) -> List[Dict]:
        """텍스트에서 표 영역 식별"""

        table_regions = []

        # 표 영역 패턴들
        table_indicators = [
            r'가\..*?나\..*?다\.',  # 가, 나, 다 구조
            r'1\..*?2\..*?3\.',     # 1, 2, 3 구조
            r'항목.*?금액',         # 항목-금액 구조
            r'구분.*?내용',         # 구분-내용 구조
        ]

        for i, pattern in enumerate(table_indicators):
            matches = re.finditer(pattern, text, re.DOTALL)

            for match in matches:
                region_text = match.group(0)

                # 표 영역에서 구체적 정보 추출
                region_info = self.parse_table_region(region_text)

                if region_info:
                    table_regions.append({
                        'region_id': len(table_regions) + 1,
                        'pattern_type': f'type_{i+1}',
                        'text': region_text[:200],  # 처음 200자만
                        'extracted_data': region_info
                    })

        return table_regions

    def parse_table_region(self, region_text: str) -> Dict:
        """표 영역에서 정보 파싱"""

        region_info = {}

        # 영역 내에서 금액 찾기
        amounts = re.findall(r'([0-9,]+)\s*원', region_text)
        if amounts:
            try:
                numeric_amounts = [int(amt.replace(',', '')) for amt in amounts if amt.replace(',', '').isdigit()]
                if numeric_amounts:
                    region_info['amounts'] = numeric_amounts
            except ValueError:
                pass

        # 영역 내에서 날짜 찾기
        dates = re.findall(r'(\d{4})[.\-/](\d{1,2})[.\-/](\d{1,2})', region_text)
        if dates:
            region_info['dates'] = [f"{d[0]}-{d[1].zfill(2)}-{d[2].zfill(2)}" for d in dates]

        return region_info


def test_enhanced_parsing():
    """개선된 파싱 테스트"""

    parser = CurrentEnvironmentTableParser()

    # 테스트할 HWP 파일
    hwp_path = Path("storage/documents/R25BK00556045/standard.hwp")
    bid_notice_no = "R25BK00556045"

    if hwp_path.exists():
        print(f"🔍 개선된 파싱 테스트: {hwp_path}")
        print("=" * 60)

        # 정보 추출
        info = parser.parse_hwp_enhanced(hwp_path, bid_notice_no)

        print("\n📊 추출 결과:")
        print("=" * 60)

        if info.get('prices'):
            print("💰 금액 정보:")
            for key, value in info['prices'].items():
                print(f"  {key}: {value:,}원")

        if info.get('dates'):
            print("\n📅 날짜 정보:")
            for key, value in info['dates'].items():
                print(f"  {key}: {value}")

        if info.get('details'):
            print("\n📋 계약 상세:")
            for key, value in info['details'].items():
                print(f"  {key}: {value}")

        if info.get('raw_tables'):
            print(f"\n📄 표 영역: {len(info['raw_tables'])}개 발견")

    else:
        print(f"❌ 파일 없음: {hwp_path}")


if __name__ == "__main__":
    test_enhanced_parsing()