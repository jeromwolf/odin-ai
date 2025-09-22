#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
향상된 정보 추출기: HWP 문서에서 핵심 비즈니스 정보 추출
"""

import re
from typing import Dict, Optional, List, Tuple
from datetime import datetime
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import os

class EnhancedInfoExtractor:
    """HWP 문서에서 API에 없는 중요 정보들을 추출"""

    def __init__(self):
        self.patterns = {
            # 공사 기간 패턴
            'duration': [
                (r'공사기간[:\s]*착공일[로부터\s]*(\d+)일', 'days'),
                (r'공사기간[:\s]*착공일[로부터\s]*(\d+)개월', 'months'),
                (r'착공일[로부터\s]*(\d+)일', 'days'),
                (r'공사기간[:\s]*([^\n]{5,50})', 'text'),
            ],

            # 지역 제한 패턴
            'region': [
                (r'([가-힣]+(?:특별시|광역시|특별자치시|도|특별자치도))\s*지역제한', 'region'),
                (r'지역제한[:\s]*([가-힣]+(?:특별시|광역시|특별자치시|도|특별자치도))', 'region'),
                (r'([가-힣]+(?:시|군|구))\s*소재', 'location'),
                (r'입찰참가지역[:\s]*([^\n]+)', 'region_text'),
            ],

            # 하도급 관련
            'subcontract': [
                (r'하도급[\s]*([가능|불가능|가능함|불가능함|허용|금지])', 'allowed'),
                (r'하도급[\s]*비율[:\s]*(\d+)%', 'ratio'),
                (r'도내업체[\s]*(\d+)%[\s]*이상', 'local_ratio'),
                (r'하도급지킴이[\s]*(?:사용|이용)[\s]*의무', 'system_required'),
            ],

            # 자격 요건
            'qualification': [
                (r'자격요건[:\s]*([^\n]{10,200})', 'text'),
                (r'([가-힣]+공사업)\s*(?:등록|보유)', 'license'),
                (r'기술자[\s]*(\d+)명[\s]*이상', 'technician_count'),
                (r'실적[\s]*(\d+)억[\s]*이상', 'experience_billion'),
            ],

            # 특수 조건
            'special': [
                (r'노무비[\s]*구분관리', 'labor_cost_mgmt'),
                (r'전자대금시스템', 'e_payment'),
                (r'직불제', 'direct_payment'),
                (r'적격심사[\s]*([실시|제외|미실시])', 'qualification_review'),
            ]
        }

    def extract_all_info(self, text: str) -> Dict:
        """텍스트에서 모든 정보 추출"""
        extracted = {
            'duration': self._extract_duration(text),
            'region': self._extract_region(text),
            'subcontract': self._extract_subcontract(text),
            'qualification': self._extract_qualification(text),
            'special_conditions': self._extract_special_conditions(text),
        }
        return extracted

    def _extract_duration(self, text: str) -> Dict:
        """공사 기간 추출"""
        result = {'days': None, 'text': None}

        for pattern, dtype in self.patterns['duration']:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                if dtype == 'days':
                    result['days'] = int(match.group(1))
                    result['text'] = f"착공일로부터 {match.group(1)}일"
                elif dtype == 'months':
                    result['days'] = int(match.group(1)) * 30
                    result['text'] = f"착공일로부터 {match.group(1)}개월"
                elif dtype == 'text':
                    result['text'] = match.group(1).strip()
                    # 텍스트에서 숫자 추출 시도
                    numbers = re.findall(r'\d+', match.group(1))
                    if numbers:
                        result['days'] = int(numbers[0])
                break

        return result

    def _extract_region(self, text: str) -> Dict:
        """지역 제한 추출"""
        result = {'restriction': None, 'location': None}

        for pattern, dtype in self.patterns['region']:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                if dtype in ['region', 'region_text']:
                    result['restriction'] = match.group(1).strip()
                elif dtype == 'location':
                    result['location'] = match.group(1).strip()

        return result

    def _extract_subcontract(self, text: str) -> Dict:
        """하도급 정보 추출"""
        result = {
            'allowed': None,
            'ratio': None,
            'local_ratio': None,
            'system_required': False
        }

        for pattern, dtype in self.patterns['subcontract']:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                if dtype == 'allowed':
                    allowed_text = match.group(1)
                    result['allowed'] = '가능' in allowed_text or '허용' in allowed_text
                elif dtype == 'ratio':
                    result['ratio'] = int(match.group(1))
                elif dtype == 'local_ratio':
                    result['local_ratio'] = int(match.group(1))
                elif dtype == 'system_required':
                    result['system_required'] = True

        # 하도급 관련 키워드가 있으면 기본적으로 허용으로 판단
        if result['allowed'] is None and '하도급' in text:
            result['allowed'] = True

        return result

    def _extract_qualification(self, text: str) -> Dict:
        """자격 요건 추출"""
        result = {
            'summary': None,
            'licenses': [],
            'technician_count': None,
            'experience_amount': None
        }

        for pattern, dtype in self.patterns['qualification']:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                if dtype == 'text' and not result['summary']:
                    result['summary'] = match.group(1).strip()[:200]
                elif dtype == 'license':
                    license = match.group(1).strip()
                    if license not in result['licenses']:
                        result['licenses'].append(license)
                elif dtype == 'technician_count':
                    result['technician_count'] = int(match.group(1))
                elif dtype == 'experience_billion':
                    result['experience_amount'] = int(match.group(1)) * 100000000

        return result

    def _extract_special_conditions(self, text: str) -> List[str]:
        """특수 조건 추출"""
        conditions = []

        for pattern, dtype in self.patterns['special']:
            if re.search(pattern, text, re.IGNORECASE):
                if dtype == 'labor_cost_mgmt':
                    conditions.append('노무비 구분관리제 적용')
                elif dtype == 'e_payment':
                    conditions.append('전자대금시스템 사용 의무')
                elif dtype == 'direct_payment':
                    conditions.append('직불제 적용')
                elif dtype == 'qualification_review':
                    match = re.search(pattern, text, re.IGNORECASE)
                    if match:
                        conditions.append(f'적격심사 {match.group(1)}')

        return conditions

    def save_to_database(self, bid_notice_no: str, extracted_info: Dict,
                         session, bid_announcement=None):
        """추출된 정보를 데이터베이스에 저장"""

        # 1. bid_announcements 테이블 업데이트 (중요 필드만)
        if bid_announcement:
            if extracted_info['duration']['days']:
                bid_announcement.duration_days = extracted_info['duration']['days']
            if extracted_info['duration']['text']:
                bid_announcement.duration_text = extracted_info['duration']['text']
            if extracted_info['region']['restriction']:
                bid_announcement.region_restriction = extracted_info['region']['restriction']
            if extracted_info['subcontract']['allowed'] is not None:
                bid_announcement.subcontract_allowed = extracted_info['subcontract']['allowed']
            if extracted_info['subcontract']['ratio']:
                bid_announcement.subcontract_ratio = extracted_info['subcontract']['ratio']
            if extracted_info['qualification']['summary']:
                bid_announcement.qualification_summary = extracted_info['qualification']['summary']
            if extracted_info['special_conditions']:
                bid_announcement.special_conditions = ', '.join(extracted_info['special_conditions'])

            session.commit()
            print(f"✅ bid_announcements 업데이트: {bid_notice_no}")

        # 2. bid_extracted_info 테이블에 상세 정보 저장
        from src.database.models import BidExtractedInfo

        # 기간 정보
        if extracted_info['duration']['text']:
            info = BidExtractedInfo(
                bid_notice_no=bid_notice_no,
                info_category='contract_details',
                field_name='duration',
                field_value=extracted_info['duration']['text'],
                confidence_score=0.9,
                extraction_method='enhanced_parser'
            )
            session.add(info)

        # 지역 제한
        if extracted_info['region']['restriction']:
            info = BidExtractedInfo(
                bid_notice_no=bid_notice_no,
                info_category='requirements',
                field_name='region_restriction',
                field_value=extracted_info['region']['restriction'],
                confidence_score=0.9,
                extraction_method='enhanced_parser'
            )
            session.add(info)

        # 하도급 정보
        if extracted_info['subcontract']['ratio']:
            info = BidExtractedInfo(
                bid_notice_no=bid_notice_no,
                info_category='contract_details',
                field_name='subcontract_ratio',
                field_value=f"{extracted_info['subcontract']['ratio']}%",
                confidence_score=0.9,
                extraction_method='enhanced_parser'
            )
            session.add(info)

        # 자격 요건
        for license in extracted_info['qualification']['licenses']:
            info = BidExtractedInfo(
                bid_notice_no=bid_notice_no,
                info_category='requirements',
                field_name='required_license',
                field_value=license,
                confidence_score=0.85,
                extraction_method='enhanced_parser'
            )
            session.add(info)

        # 특수 조건
        for condition in extracted_info['special_conditions']:
            info = BidExtractedInfo(
                bid_notice_no=bid_notice_no,
                info_category='special_conditions',
                field_name='condition',
                field_value=condition,
                confidence_score=0.85,
                extraction_method='enhanced_parser'
            )
            session.add(info)

        session.commit()
        print(f"✅ bid_extracted_info 저장: {bid_notice_no}")


if __name__ == "__main__":
    # 테스트
    extractor = EnhancedInfoExtractor()

    # 샘플 텍스트
    sample_text = """
    공사기간: 착공일로부터 90일
    전라남도 지역제한 공사
    하도급 가능, 도내업체 70% 이상 참여
    전기공사업 등록 필요
    노무비 구분관리제 적용
    하도급지킴이 사용 의무
    """

    result = extractor.extract_all_info(sample_text)

    print("📋 추출 결과:")
    print(f"  • 공사기간: {result['duration']}")
    print(f"  • 지역제한: {result['region']}")
    print(f"  • 하도급: {result['subcontract']}")
    print(f"  • 자격요건: {result['qualification']}")
    print(f"  • 특수조건: {result['special_conditions']}")