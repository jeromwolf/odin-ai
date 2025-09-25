"""
알림 매칭 엔진
사용자의 알림 규칙과 새로운 입찰 공고를 매칭
"""

import re
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from loguru import logger


class AlertMatcher:
    """알림 매칭 엔진"""

    def __init__(self, db_url: str):
        """초기화

        Args:
            db_url: 데이터베이스 URL
        """
        self.db_url = db_url
        self.engine = create_engine(db_url)
        Session = sessionmaker(bind=self.engine)
        self.session = Session()

    def match_bids_with_rules(self, bid_ids: List[str], batch_date: datetime = None) -> List[Dict]:
        """입찰 공고와 알림 규칙 매칭

        Args:
            bid_ids: 입찰 공고 ID 리스트
            batch_date: 배치 실행 날짜 (기본: 오늘)

        Returns:
            list: 매칭 결과 리스트
        """
        matches = []
        batch_date = batch_date or datetime.now()

        try:
            # 오늘 이미 처리된 공고 조회 (중복 방지)
            processed_today = self._get_processed_bids_today(batch_date)
            logger.info(f"📅 {batch_date.strftime('%Y-%m-%d')} 기처리 공고: {len(processed_today)}개")

            # 1. 활성화된 모든 알림 규칙 조회
            rules = self._get_active_rules()
            logger.info(f"📋 활성 알림 규칙: {len(rules)}개")

            # 2. 각 입찰 공고에 대해 매칭 확인
            for bid_id in bid_ids:
                # 이미 오늘 처리된 공고는 스킵
                if bid_id in processed_today:
                    logger.debug(f"  ⏭️ 오늘 이미 처리됨: {bid_id}")
                    continue

                bid = self._get_bid_details(bid_id)
                if not bid:
                    continue

                # 각 규칙과 매칭 확인
                for rule in rules:
                    if self._check_match(bid, rule):
                        match = {
                            'rule_id': rule['id'],
                            'user_id': rule['user_id'],
                            'bid_id': bid_id,
                            'bid_title': bid['title'],
                            'match_score': self._calculate_match_score(bid, rule),
                            'rule_name': rule.get('rule_name', '알림 규칙'),
                            'channels': rule.get('notification_channels', ['email']),
                            'matched_at': datetime.now()
                        }
                        matches.append(match)
                        logger.debug(f"✅ 매칭: 규칙 {rule['id']} <-> 공고 {bid_id}")

            logger.info(f"🎯 총 {len(matches)}개 매칭 발견")

            # 3. 매칭 결과를 DB에 저장
            self._save_matches(matches)

            return matches

        except Exception as e:
            logger.error(f"매칭 실패: {e}")
            return []
        finally:
            self.session.close()

    def _get_active_rules(self) -> List[Dict]:
        """활성화된 알림 규칙 조회

        Returns:
            list: 알림 규칙 리스트
        """
        query = """
        SELECT
            id,
            user_id,
            rule_name,
            keywords,
            exclude_keywords,
            min_price,
            max_price,
            organizations,
            regions,
            categories,
            notification_channels,
            notification_timing,
            is_active
        FROM alert_rules
        WHERE is_active = true
        """

        result = self.session.execute(text(query))
        rules = []

        for row in result:
            rules.append({
                'id': row[0],
                'user_id': row[1],
                'rule_name': row[2],
                'keywords': row[3] or [],
                'exclude_keywords': row[4] or [],
                'min_price': row[5],
                'max_price': row[6],
                'organizations': row[7] or [],
                'regions': row[8] or [],
                'categories': row[9] or [],
                'notification_channels': row[10] or ['email'],
                'notification_timing': row[11],
                'is_active': row[12]
            })

        return rules

    def _get_bid_details(self, bid_id: str) -> Optional[Dict]:
        """입찰 공고 상세 조회

        Args:
            bid_id: 입찰 공고 ID

        Returns:
            dict: 입찰 공고 정보
        """
        query = """
        SELECT
            ba.bid_notice_no,
            ba.title,
            ba.organization_name,
            ba.department_name,
            ba.estimated_price,
            ba.bid_method,
            ba.contract_method,
            ba.announcement_date,
            ba.bid_end_date,
            bd.extracted_text,
            bei.extracted_data
        FROM bid_announcements ba
        LEFT JOIN bid_documents bd ON ba.bid_notice_no = bd.bid_notice_no
        LEFT JOIN bid_extracted_info bei ON ba.bid_notice_no = bei.bid_notice_no
        WHERE ba.bid_notice_no = :bid_id
        LIMIT 1
        """

        result = self.session.execute(text(query), {'bid_id': bid_id})
        row = result.first()

        if not row:
            return None

        return {
            'bid_id': row[0],
            'title': row[1],
            'organization': row[2],
            'department': row[3],
            'price': row[4],
            'bid_method': row[5],
            'contract_method': row[6],
            'announcement_date': row[7],
            'bid_end_date': row[8],
            'extracted_text': row[9] or '',
            'extracted_data': row[10] or {}
        }

    def _check_match(self, bid: Dict, rule: Dict) -> bool:
        """입찰 공고와 규칙 매칭 확인

        Args:
            bid: 입찰 공고 정보
            rule: 알림 규칙

        Returns:
            bool: 매칭 여부
        """
        # 1. 키워드 매칭
        if rule['keywords']:
            if not self._check_keywords(bid, rule['keywords']):
                return False

        # 2. 제외 키워드 확인
        if rule['exclude_keywords']:
            if self._check_keywords(bid, rule['exclude_keywords']):
                return False  # 제외 키워드가 있으면 매칭 제외

        # 3. 가격 범위 확인
        if rule['min_price'] or rule['max_price']:
            if not self._check_price_range(bid, rule['min_price'], rule['max_price']):
                return False

        # 4. 기관 확인
        if rule['organizations']:
            if not self._check_organizations(bid, rule['organizations']):
                return False

        # 5. 지역 확인
        if rule['regions']:
            if not self._check_regions(bid, rule['regions']):
                return False

        # 6. 카테고리 확인
        if rule['categories']:
            if not self._check_categories(bid, rule['categories']):
                return False

        return True

    def _check_keywords(self, bid: Dict, keywords: List[str]) -> bool:
        """키워드 매칭 확인

        Args:
            bid: 입찰 공고
            keywords: 키워드 리스트

        Returns:
            bool: 매칭 여부
        """
        # 검색 대상 텍스트 결합
        search_text = f"{bid['title']} {bid.get('extracted_text', '')}".lower()

        for keyword in keywords:
            if keyword.lower() in search_text:
                return True

        return False

    def _check_price_range(self, bid: Dict, min_price: Optional[int], max_price: Optional[int]) -> bool:
        """가격 범위 확인

        Args:
            bid: 입찰 공고
            min_price: 최소 가격
            max_price: 최대 가격

        Returns:
            bool: 범위 내 여부
        """
        price = bid.get('price')
        if not price:
            return True  # 가격 정보가 없으면 통과

        if min_price and price < min_price:
            return False

        if max_price and price > max_price:
            return False

        return True

    def _check_organizations(self, bid: Dict, organizations: List[str]) -> bool:
        """기관 매칭 확인

        Args:
            bid: 입찰 공고
            organizations: 기관명 리스트

        Returns:
            bool: 매칭 여부
        """
        bid_org = bid.get('organization', '').lower()
        bid_dept = bid.get('department', '').lower()

        for org in organizations:
            org_lower = org.lower()
            if org_lower in bid_org or org_lower in bid_dept:
                return True

        return False

    def _check_regions(self, bid: Dict, regions: List[str]) -> bool:
        """지역 매칭 확인

        Args:
            bid: 입찰 공고
            regions: 지역명 리스트

        Returns:
            bool: 매칭 여부
        """
        # 제목, 기관명, 추출 텍스트에서 지역 확인
        search_text = f"{bid['title']} {bid['organization']} {bid.get('extracted_text', '')}".lower()

        for region in regions:
            if region.lower() in search_text:
                return True

        # extracted_data에서 지역 정보 확인
        extracted = bid.get('extracted_data', {})
        if isinstance(extracted, dict):
            region_info = extracted.get('region', '')
            if region_info:
                for region in regions:
                    if region.lower() in region_info.lower():
                        return True

        return False

    def _check_categories(self, bid: Dict, categories: List[str]) -> bool:
        """카테고리 매칭 확인

        Args:
            bid: 입찰 공고
            categories: 카테고리 리스트

        Returns:
            bool: 매칭 여부
        """
        # 계약 방법, 입찰 방법 등에서 카테고리 확인
        bid_method = (bid.get('bid_method', '') or '').lower()
        contract_method = (bid.get('contract_method', '') or '').lower()

        for category in categories:
            cat_lower = category.lower()
            if cat_lower in bid_method or cat_lower in contract_method:
                return True

        return False

    def _get_processed_bids_today(self, batch_date: datetime) -> set:
        """오늘 이미 처리된 공고 ID 조회

        Args:
            batch_date: 배치 실행 날짜

        Returns:
            set: 처리된 공고 ID 집합
        """
        query = """
        SELECT DISTINCT bid_id
        FROM alert_matches
        WHERE DATE(matched_at) = :today
        """

        result = self.session.execute(text(query), {
            'today': batch_date.date()
        })

        return {row[0] for row in result}

    def _calculate_match_score(self, bid: Dict, rule: Dict) -> float:
        """매칭 점수 계산

        Args:
            bid: 입찰 공고
            rule: 알림 규칙

        Returns:
            float: 매칭 점수 (0.0 ~ 1.0)
        """
        score = 0.0
        max_score = 0.0

        # 키워드 매칭 점수
        if rule['keywords']:
            max_score += 40
            matched_keywords = 0
            search_text = f"{bid['title']} {bid.get('extracted_text', '')}".lower()

            for keyword in rule['keywords']:
                if keyword.lower() in search_text:
                    matched_keywords += 1

            if rule['keywords']:
                score += (matched_keywords / len(rule['keywords'])) * 40

        # 가격 매칭 점수
        if rule['min_price'] or rule['max_price']:
            max_score += 20
            if self._check_price_range(bid, rule['min_price'], rule['max_price']):
                score += 20

        # 기관 매칭 점수
        if rule['organizations']:
            max_score += 20
            if self._check_organizations(bid, rule['organizations']):
                score += 20

        # 지역 매칭 점수
        if rule['regions']:
            max_score += 10
            if self._check_regions(bid, rule['regions']):
                score += 10

        # 카테고리 매칭 점수
        if rule['categories']:
            max_score += 10
            if self._check_categories(bid, rule['categories']):
                score += 10

        # 최대 점수가 0이면 완벽 매칭으로 간주
        if max_score == 0:
            return 1.0

        return score / max_score

    def _save_matches(self, matches: List[Dict]):
        """매칭 결과 DB 저장 (중복 체크 강화)

        Args:
            matches: 매칭 결과 리스트
        """
        if not matches:
            return

        saved_count = 0
        duplicate_count = 0

        for match in matches:
            # 중복 체크 (이미 발송된 알림 포함)
            check_query = """
            SELECT id, is_sent, sent_at
            FROM alert_matches
            WHERE rule_id = :rule_id AND bid_id = :bid_id
            """

            existing = self.session.execute(text(check_query), {
                'rule_id': match['rule_id'],
                'bid_id': match['bid_id']
            }).first()

            if existing:
                duplicate_count += 1
                if existing[1]:  # is_sent가 True인 경우
                    logger.debug(f"  ⏭️ 이미 발송됨: rule={match['rule_id']}, bid={match['bid_id']}, sent_at={existing[2]}")
                else:
                    logger.debug(f"  ⏭️ 이미 매칭됨 (미발송): rule={match['rule_id']}, bid={match['bid_id']}")
                continue

            # 새 매칭 저장
            insert_query = """
            INSERT INTO alert_matches (
                rule_id, user_id, bid_id, match_score,
                matched_at, is_sent, match_date
            ) VALUES (
                :rule_id, :user_id, :bid_id, :match_score,
                :matched_at, false, :match_date
            )
            """

            self.session.execute(text(insert_query), {
                'rule_id': match['rule_id'],
                'user_id': match['user_id'],
                'bid_id': match['bid_id'],
                'match_score': match['match_score'],
                'matched_at': match['matched_at'],
                'match_date': datetime.now().date()  # 매칭 일자 추가
            })
            saved_count += 1

        self.session.commit()

        if duplicate_count > 0:
            logger.info(f"💾 {saved_count}개 신규 매칭 저장 (중복 {duplicate_count}개 스킵)")
        else:
            logger.info(f"💾 {saved_count}개 매칭 결과 저장 완료")