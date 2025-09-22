"""
해시태그 자동 생성 시스템
"""

import re
from typing import List, Dict, Optional, Set
from datetime import datetime, timedelta
from loguru import logger

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from src.database.models import (
    BidAnnouncement, BidTag, BidTagRelation
)


class TagGenerator:
    """해시태그 자동 생성기"""

    def __init__(self, db_session: Session):
        self.db_session = db_session
        self._init_tag_rules()
        self._load_existing_tags()

    def _init_tag_rules(self):
        """태그 생성 규칙 초기화"""

        # 산업 분야 키워드
        self.industry_keywords = {
            '건설': ['건축', '건설', '토목', '시공', '공사', '건물', '설비'],
            'IT': ['시스템', '소프트웨어', 'SW', '개발', '구축', '프로그램', '전산', 'IT', '정보화'],
            '의료': ['병원', '의료', '보건', '약품', '의료기기', '의약품', '건강'],
            '교육': ['학교', '교육', '대학', '초등', '중학', '고등', '유치원', '어린이집'],
            '전기': ['전기', '전력', '배전', '발전', '변압', '전선', '전등'],
            '기계': ['기계', '설비', '장비', '기기', '장치'],
            '환경': ['환경', '폐기물', '오수', '하수', '정화', '청소'],
            '조경': ['조경', '녹지', '공원', '수목', '잔디', '가로수'],
            '도로': ['도로', '포장', '아스팔트', '보도', '차도', '교통'],
            '통신': ['통신', '네트워크', '인터넷', '전화', 'CCTV', '방송'],
        }

        # 지역 키워드
        self.region_keywords = {
            '서울': ['서울', '서울특별시', '서울시'],
            '부산': ['부산', '부산광역시', '부산시'],
            '대구': ['대구', '대구광역시', '대구시'],
            '인천': ['인천', '인천광역시', '인천시'],
            '광주': ['광주', '광주광역시', '광주시'],
            '대전': ['대전', '대전광역시', '대전시'],
            '울산': ['울산', '울산광역시', '울산시'],
            '세종': ['세종', '세종특별자치시', '세종시'],
            '경기': ['경기도', '경기', '수원', '성남', '용인', '고양', '안양', '부천', '안산', '남양주'],
            '강원': ['강원도', '강원', '강원특별자치도', '춘천', '원주', '강릉'],
            '충북': ['충청북도', '충북', '청주', '충주', '제천'],
            '충남': ['충청남도', '충남', '천안', '공주', '아산', '논산'],
            '전북': ['전라북도', '전북', '전북특별자치도', '전주', '익산', '군산'],
            '전남': ['전라남도', '전남', '목포', '여수', '순천', '광양'],
            '경북': ['경상북도', '경북', '포항', '경주', '안동', '구미'],
            '경남': ['경상남도', '경남', '창원', '김해', '양산', '진주'],
            '제주': ['제주도', '제주', '제주특별자치도', '제주시', '서귀포'],
        }

        # 계약 방법
        self.contract_methods = {
            '수의계약': ['수의계약', '수의', '1인견적'],
            '일반경쟁': ['일반경쟁', '경쟁입찰'],
            '제한경쟁': ['제한경쟁', '제한입찰'],
            '지명경쟁': ['지명경쟁', '지명입찰'],
            '협상계약': ['협상에의한계약', '협상계약'],
        }

        # 특수 태그 규칙
        self.special_rules = {
            '긴급': lambda ann: self._is_urgent(ann),
            '재공고': lambda ann: ann.bid_notice_ord != '000',
            '연간단가': lambda ann: '연간' in ann.title or '단가' in ann.title,
            '다년계약': lambda ann: '다년' in ann.title,
            '공동계약': lambda ann: '공동' in ann.title,
            '장기계속': lambda ann: '장기계속' in ann.title,
        }

    def _load_existing_tags(self):
        """기존 태그 로드"""
        self.existing_tags = {}
        tags = self.db_session.query(BidTag).all()
        for tag in tags:
            self.existing_tags[tag.tag_name] = tag

    def generate_tags(self, announcement: BidAnnouncement) -> List[str]:
        """
        공고에 대한 태그 생성
        Returns: 태그 리스트
        """
        tags = set()

        # 1. 산업 분야 태그
        industry_tags = self._extract_industry_tags(announcement.title)
        tags.update(industry_tags)

        # 2. 지역 태그
        region_tags = self._extract_region_tags(
            announcement.organization_name,
            announcement.title
        )
        tags.update(region_tags)

        # 3. 금액 규모 태그
        if announcement.estimated_price or announcement.assigned_budget:
            price_tag = self._get_price_range_tag(
                announcement.estimated_price or announcement.assigned_budget
            )
            if price_tag:
                tags.add(price_tag)

        # 4. 계약 방법 태그
        if announcement.contract_method:
            contract_tag = self._get_contract_method_tag(announcement.contract_method)
            if contract_tag:
                tags.add(contract_tag)

        # 5. 특수 태그
        special_tags = self._get_special_tags(announcement)
        tags.update(special_tags)

        # 6. 자동 추출 태그 (제목에서 주요 키워드)
        auto_tags = self._extract_auto_tags(announcement.title)
        tags.update(auto_tags)

        # 태그 정규화
        normalized_tags = [self._normalize_tag(tag) for tag in tags]

        return list(set(normalized_tags))

    def _extract_industry_tags(self, title: str) -> Set[str]:
        """산업 분야 태그 추출"""
        tags = set()
        title_lower = title.lower()

        for industry, keywords in self.industry_keywords.items():
            for keyword in keywords:
                if keyword.lower() in title_lower:
                    tags.add(f"#{industry}")
                    break

        return tags

    def _extract_region_tags(
        self,
        org_name: Optional[str],
        title: Optional[str]
    ) -> Set[str]:
        """지역 태그 추출"""
        tags = set()
        text = f"{org_name or ''} {title or ''}".lower()

        for region, keywords in self.region_keywords.items():
            for keyword in keywords:
                if keyword.lower() in text:
                    tags.add(f"#{region}")

                    # 세부 지역 추출 (예: 강남구, 분당구 등)
                    if '구' in text:
                        gu_match = re.search(r'(\w+구)', text)
                        if gu_match:
                            tags.add(f"#{gu_match.group(1)}")
                    break

        return tags

    def _get_price_range_tag(self, price: int) -> Optional[str]:
        """금액 규모 태그 생성"""
        if price < 100_000_000:
            return "#1억미만"
        elif price < 500_000_000:
            return "#1억-5억"
        elif price < 1_000_000_000:
            return "#5억-10억"
        elif price < 5_000_000_000:
            return "#10억-50억"
        else:
            return "#50억이상"

    def _get_contract_method_tag(self, method: str) -> Optional[str]:
        """계약 방법 태그 생성"""
        method_lower = method.lower()

        for tag, keywords in self.contract_methods.items():
            for keyword in keywords:
                if keyword in method_lower:
                    return f"#{tag}"

        # 기본값
        if method:
            return f"#{method[:10]}"  # 최대 10자

        return None

    def _get_special_tags(self, announcement: BidAnnouncement) -> Set[str]:
        """특수 태그 생성"""
        tags = set()

        for tag_name, rule_func in self.special_rules.items():
            if rule_func(announcement):
                tags.add(f"#{tag_name}")

        return tags

    def _is_urgent(self, announcement: BidAnnouncement) -> bool:
        """긴급 공고 여부 확인"""
        if not announcement.bid_start_date or not announcement.bid_end_date:
            return False

        # 입찰 기간이 7일 미만이면 긴급
        delta = announcement.bid_end_date - announcement.bid_start_date
        return delta.days < 7

    def _extract_auto_tags(self, title: str) -> Set[str]:
        """제목에서 자동 태그 추출"""
        tags = set()

        # 주요 키워드 패턴
        patterns = [
            r'(\w+)사업',  # XX사업
            r'(\w+)공사',  # XX공사
            r'(\w+)구매',  # XX구매
            r'(\w+)용역',  # XX용역
            r'(\w+)시스템',  # XX시스템
            r'(\w+)설치',  # XX설치
            r'(\w+)유지보수',  # XX유지보수
        ]

        for pattern in patterns:
            matches = re.findall(pattern, title)
            for match in matches:
                if len(match) >= 2 and len(match) <= 10:
                    tags.add(f"#{match}")

        return tags

    def _normalize_tag(self, tag: str) -> str:
        """태그 정규화"""
        # # 기호 확인
        if not tag.startswith('#'):
            tag = f"#{tag}"

        # 공백 제거
        tag = tag.replace(' ', '')

        # 특수문자 제거 (# 제외)
        tag = re.sub(r'[^\w#가-힣]', '', tag)

        # 길이 제한
        if len(tag) > 20:
            tag = tag[:20]

        return tag

    def save_tags(
        self,
        announcement: BidAnnouncement,
        tags: List[str],
        source: str = 'auto'
    ) -> int:
        """
        태그 저장
        Returns: 저장된 태그 수
        """
        saved_count = 0

        for tag_name in tags:
            try:
                # 태그 마스터 확인/생성
                tag = self._get_or_create_tag(tag_name)

                # 태그 관계 확인 (중복 방지)
                existing_relation = self.db_session.query(BidTagRelation).filter(
                    and_(
                        BidTagRelation.bid_notice_no == announcement.bid_notice_no,
                        BidTagRelation.tag_id == tag.tag_id
                    )
                ).first()

                if not existing_relation:
                    # 새 관계 생성
                    relation = BidTagRelation(
                        bid_notice_no=announcement.bid_notice_no,
                        tag_id=tag.tag_id,
                        relevance_score=1.0,
                        source=source
                    )
                    self.db_session.add(relation)

                    # 태그 사용 횟수 증가
                    tag.usage_count += 1

                    saved_count += 1

            except Exception as e:
                logger.error(f"태그 저장 실패 ({tag_name}): {e}")

        try:
            self.db_session.commit()
            logger.info(f"태그 {saved_count}개 저장: {announcement.bid_notice_no}")
        except Exception as e:
            self.db_session.rollback()
            logger.error(f"태그 저장 실패: {e}")

        return saved_count

    def _get_or_create_tag(self, tag_name: str) -> BidTag:
        """태그 조회 또는 생성"""
        # 캐시에서 확인
        if tag_name in self.existing_tags:
            return self.existing_tags[tag_name]

        # DB에서 확인
        tag = self.db_session.query(BidTag).filter(
            BidTag.tag_name == tag_name
        ).first()

        if not tag:
            # 새 태그 생성
            category = self._categorize_tag(tag_name)
            tag = BidTag(
                tag_name=tag_name,
                tag_category=category,
                usage_count=0
            )
            self.db_session.add(tag)
            self.db_session.flush()  # ID 생성

        # 캐시에 추가
        self.existing_tags[tag_name] = tag

        return tag

    def _categorize_tag(self, tag_name: str) -> str:
        """태그 카테고리 분류"""
        tag_text = tag_name.replace('#', '')

        # 산업 분야
        for industry in self.industry_keywords.keys():
            if industry in tag_text:
                return 'industry'

        # 지역
        for region in self.region_keywords.keys():
            if region in tag_text:
                return 'region'

        # 금액
        if '억' in tag_text:
            return 'price'

        # 계약 방법
        if '계약' in tag_text or '경쟁' in tag_text:
            return 'contract'

        # 특수
        if tag_text in ['긴급', '재공고', '연간단가', '다년계약']:
            return 'special'

        return 'general'

    def process_announcement(self, announcement: BidAnnouncement) -> List[str]:
        """
        공고 처리 (태그 생성 및 저장)
        Returns: 생성된 태그 리스트
        """
        # 태그 생성
        tags = self.generate_tags(announcement)

        # 태그 저장
        if tags:
            self.save_tags(announcement, tags)

        return tags

    def get_popular_tags(self, limit: int = 20) -> List[Dict]:
        """인기 태그 조회"""
        tags = self.db_session.query(BidTag).order_by(
            BidTag.usage_count.desc()
        ).limit(limit).all()

        return [
            {
                'tag_name': tag.tag_name,
                'category': tag.tag_category,
                'count': tag.usage_count
            }
            for tag in tags
        ]

    def search_by_tags(
        self,
        tags: List[str],
        operator: str = 'AND'
    ) -> List[str]:
        """
        태그로 공고 검색
        Returns: bid_notice_no 리스트
        """
        # 태그 ID 조회
        tag_ids = []
        for tag_name in tags:
            tag = self.db_session.query(BidTag).filter(
                BidTag.tag_name == tag_name
            ).first()
            if tag:
                tag_ids.append(tag.tag_id)

        if not tag_ids:
            return []

        # 태그 관계 조회
        query = self.db_session.query(BidTagRelation.bid_notice_no)

        if operator == 'AND':
            # 모든 태그를 가진 공고
            query = query.filter(
                BidTagRelation.tag_id.in_(tag_ids)
            ).group_by(
                BidTagRelation.bid_notice_no
            ).having(
                func.count(BidTagRelation.tag_id) == len(tag_ids)
            )
        else:  # OR
            # 하나 이상의 태그를 가진 공고
            query = query.filter(
                BidTagRelation.tag_id.in_(tag_ids)
            ).distinct()

        results = query.all()
        return [r[0] for r in results]