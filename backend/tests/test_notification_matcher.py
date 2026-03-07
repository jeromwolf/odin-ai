"""notification_matcher 단위 테스트 - 매칭 로직 검증

DB 연결 없이 _is_bid_matching_rule 메서드의 순수 매칭 로직만 테스트한다.
"""
import sys
import os
import pytest

# batch/modules를 path에 추가
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'batch', 'modules'))


def _make_matcher():
    """DB 없이 매칭 로직만 테스트하기 위한 인스턴스 생성.

    __init__을 우회하여 DB 커넥션 풀 생성을 건너뛴다.
    """
    from notification_matcher import NotificationMatcher
    instance = object.__new__(NotificationMatcher)
    instance.db_url = None
    instance._pool = None
    instance.processed_count = 0
    instance.notification_count = 0
    instance.email_sent_count = 0
    instance.frontend_url = "http://localhost:3000"
    return instance


def _make_bid(**overrides):
    """테스트용 입찰공고 데이터 생성 (기본값 포함)."""
    bid = {
        'bid_notice_no': 'TEST001',
        'title': '서울시 도로 포장공사',
        'organization_name': '서울특별시',
        'estimated_price': 150_000_000,  # 1.5억
        'region_restriction': '서울특별시',
        'tags': ['건설', '도로', '포장'],
        'work_types': ['종합공사'],
        'bid_method': '일반경쟁',
        'bid_start_date': None,
        'bid_end_date': None,
    }
    bid.update(overrides)
    return bid


def _make_rule(conditions: dict = None, **overrides):
    """테스트용 알림 규칙 생성 (기본값 포함)."""
    rule = {
        'id': 1,
        'user_id': 100,
        'rule_name': '테스트 규칙',
        'conditions': conditions if conditions is not None else {},
        'notification_channels': ['email'],
        'notification_timing': 'immediate',
        'email': 'test@example.com',
        'full_name': '테스트 사용자',
    }
    rule.update(overrides)
    return rule


@pytest.fixture
def matcher():
    return _make_matcher()


# ---------------------------------------------------------------------------
# 1. 키워드 매칭 (conditions['keywords'])
# ---------------------------------------------------------------------------

class TestKeywordMatching:
    def test_keyword_found_in_title(self, matcher):
        bid = _make_bid(title='서울시 도로 포장공사', organization_name='서울특별시')
        rule = _make_rule({'keywords': ['도로']})
        assert matcher._is_bid_matching_rule(bid, rule) is True

    def test_keyword_found_in_organization_name(self, matcher):
        bid = _make_bid(title='포장공사', organization_name='한국도로공사')
        rule = _make_rule({'keywords': ['도로공사']})
        assert matcher._is_bid_matching_rule(bid, rule) is True

    def test_keyword_not_found(self, matcher):
        bid = _make_bid(title='건물 신축 공사', organization_name='경기도청')
        rule = _make_rule({'keywords': ['터널']})
        assert matcher._is_bid_matching_rule(bid, rule) is False

    def test_keyword_case_insensitive(self, matcher):
        """대소문자 구분 없이 매칭되어야 한다."""
        bid = _make_bid(title='IT 시스템 구축', organization_name='서울시')
        rule = _make_rule({'keywords': ['it']})
        assert matcher._is_bid_matching_rule(bid, rule) is True

    def test_keyword_case_insensitive_upper(self, matcher):
        bid = _make_bid(title='it 시스템', organization_name='서울시')
        rule = _make_rule({'keywords': ['IT']})
        assert matcher._is_bid_matching_rule(bid, rule) is True

    def test_keyword_any_one_of_multiple_matches(self, matcher):
        """여러 키워드 중 하나라도 매칭되면 통과."""
        bid = _make_bid(title='도로 포장공사', organization_name='서울시')
        rule = _make_rule({'keywords': ['터널', '교량', '포장']})
        assert matcher._is_bid_matching_rule(bid, rule) is True

    def test_keyword_none_of_multiple_matches(self, matcher):
        bid = _make_bid(title='도로 포장공사', organization_name='서울시')
        rule = _make_rule({'keywords': ['터널', '교량', '댐']})
        assert matcher._is_bid_matching_rule(bid, rule) is False

    def test_empty_keywords_list_passes(self, matcher):
        """keywords가 빈 리스트면 키워드 조건 없음 → 통과."""
        bid = _make_bid()
        rule = _make_rule({'keywords': []})
        assert matcher._is_bid_matching_rule(bid, rule) is True

    def test_no_keywords_key_passes(self, matcher):
        """conditions에 keywords 키 자체가 없으면 통과."""
        bid = _make_bid()
        rule = _make_rule({})
        assert matcher._is_bid_matching_rule(bid, rule) is True

    def test_keyword_partial_match_in_title(self, matcher):
        """부분 문자열 매칭을 지원한다."""
        bid = _make_bid(title='소하천 재해복구공사')
        rule = _make_rule({'keywords': ['재해복구']})
        assert matcher._is_bid_matching_rule(bid, rule) is True


# ---------------------------------------------------------------------------
# 2. 가격 범위 매칭 - min_price 형식
# ---------------------------------------------------------------------------

class TestPriceMinFormat:
    def test_below_min_price_rejected(self, matcher):
        bid = _make_bid(estimated_price=40_000_000)  # 4천만
        rule = _make_rule({'min_price': 50_000_000})   # 5천만 이상
        assert matcher._is_bid_matching_rule(bid, rule) is False

    def test_exactly_at_min_price_accepted(self, matcher):
        bid = _make_bid(estimated_price=50_000_000)
        rule = _make_rule({'min_price': 50_000_000})
        assert matcher._is_bid_matching_rule(bid, rule) is True

    def test_above_min_price_accepted(self, matcher):
        bid = _make_bid(estimated_price=200_000_000)
        rule = _make_rule({'min_price': 50_000_000})
        assert matcher._is_bid_matching_rule(bid, rule) is True


# ---------------------------------------------------------------------------
# 3. 가격 범위 매칭 - price_min (구형식) 형식
# ---------------------------------------------------------------------------

class TestPriceMinLegacyFormat:
    def test_below_price_min_rejected(self, matcher):
        bid = _make_bid(estimated_price=9_000_000)
        rule = _make_rule({'price_min': 10_000_000})
        assert matcher._is_bid_matching_rule(bid, rule) is False

    def test_exactly_at_price_min_accepted(self, matcher):
        bid = _make_bid(estimated_price=10_000_000)
        rule = _make_rule({'price_min': 10_000_000})
        assert matcher._is_bid_matching_rule(bid, rule) is True

    def test_above_price_min_accepted(self, matcher):
        bid = _make_bid(estimated_price=100_000_000)
        rule = _make_rule({'price_min': 10_000_000})
        assert matcher._is_bid_matching_rule(bid, rule) is True


# ---------------------------------------------------------------------------
# 4. 가격 범위 매칭 - max_price 형식
# ---------------------------------------------------------------------------

class TestPriceMaxFormat:
    def test_above_max_price_rejected(self, matcher):
        bid = _make_bid(estimated_price=300_000_000)  # 3억
        rule = _make_rule({'max_price': 200_000_000})   # 최대 2억
        assert matcher._is_bid_matching_rule(bid, rule) is False

    def test_exactly_at_max_price_accepted(self, matcher):
        bid = _make_bid(estimated_price=200_000_000)
        rule = _make_rule({'max_price': 200_000_000})
        assert matcher._is_bid_matching_rule(bid, rule) is True

    def test_below_max_price_accepted(self, matcher):
        bid = _make_bid(estimated_price=100_000_000)
        rule = _make_rule({'max_price': 200_000_000})
        assert matcher._is_bid_matching_rule(bid, rule) is True


# ---------------------------------------------------------------------------
# 5. 가격 범위 매칭 - price_max (구형식) 형식
# ---------------------------------------------------------------------------

class TestPriceMaxLegacyFormat:
    def test_above_price_max_rejected(self, matcher):
        bid = _make_bid(estimated_price=10_000_000_001)
        rule = _make_rule({'price_max': 10_000_000_000})
        assert matcher._is_bid_matching_rule(bid, rule) is False

    def test_exactly_at_price_max_accepted(self, matcher):
        bid = _make_bid(estimated_price=10_000_000_000)
        rule = _make_rule({'price_max': 10_000_000_000})
        assert matcher._is_bid_matching_rule(bid, rule) is True

    def test_below_price_max_accepted(self, matcher):
        bid = _make_bid(estimated_price=1_000_000)
        rule = _make_rule({'price_max': 10_000_000_000})
        assert matcher._is_bid_matching_rule(bid, rule) is True


# ---------------------------------------------------------------------------
# 6. 가격 범위 매칭 - min + max 동시 적용
# ---------------------------------------------------------------------------

class TestPriceMinAndMax:
    def test_price_in_range_accepted(self, matcher):
        bid = _make_bid(estimated_price=100_000_000)  # 1억 (범위 내)
        rule = _make_rule({'min_price': 50_000_000, 'max_price': 200_000_000})
        assert matcher._is_bid_matching_rule(bid, rule) is True

    def test_price_below_range_rejected(self, matcher):
        bid = _make_bid(estimated_price=10_000_000)   # 1천만 (범위 하한 미만)
        rule = _make_rule({'min_price': 50_000_000, 'max_price': 200_000_000})
        assert matcher._is_bid_matching_rule(bid, rule) is False

    def test_price_above_range_rejected(self, matcher):
        bid = _make_bid(estimated_price=500_000_000)  # 5억 (범위 상한 초과)
        rule = _make_rule({'min_price': 50_000_000, 'max_price': 200_000_000})
        assert matcher._is_bid_matching_rule(bid, rule) is False

    def test_legacy_format_price_in_range_accepted(self, matcher):
        bid = _make_bid(estimated_price=100_000_000)
        rule = _make_rule({'price_min': 50_000_000, 'price_max': 200_000_000})
        assert matcher._is_bid_matching_rule(bid, rule) is True

    def test_legacy_format_price_out_of_range_rejected(self, matcher):
        bid = _make_bid(estimated_price=400_000_000)
        rule = _make_rule({'price_min': 50_000_000, 'price_max': 200_000_000})
        assert matcher._is_bid_matching_rule(bid, rule) is False


# ---------------------------------------------------------------------------
# 7. 가격이 없는 입찰 (estimated_price = None) → 가격 체크 스킵
# ---------------------------------------------------------------------------

class TestNoBidPrice:
    def test_none_price_skips_min_check(self, matcher):
        """estimated_price가 None이면 가격 필터를 건너뛴다."""
        bid = _make_bid(estimated_price=None)
        rule = _make_rule({'min_price': 50_000_000})
        assert matcher._is_bid_matching_rule(bid, rule) is True

    def test_none_price_skips_max_check(self, matcher):
        bid = _make_bid(estimated_price=None)
        rule = _make_rule({'max_price': 10_000_000})
        assert matcher._is_bid_matching_rule(bid, rule) is True

    def test_none_price_skips_both_checks(self, matcher):
        bid = _make_bid(estimated_price=None)
        rule = _make_rule({'min_price': 50_000_000, 'max_price': 200_000_000})
        assert matcher._is_bid_matching_rule(bid, rule) is True

    def test_zero_price_skips_price_check(self, matcher):
        """estimated_price=0은 falsy → 가격 체크 스킵."""
        bid = _make_bid(estimated_price=0)
        rule = _make_rule({'min_price': 50_000_000})
        assert matcher._is_bid_matching_rule(bid, rule) is True


# ---------------------------------------------------------------------------
# 8. 기관 매칭 (conditions['organizations'])
# ---------------------------------------------------------------------------

class TestOrganizationMatching:
    def test_organization_partial_match_accepted(self, matcher):
        """부분 문자열 매칭을 지원한다."""
        bid = _make_bid(organization_name='한국도로공사 서울지사')
        rule = _make_rule({'organizations': ['한국도로공사']})
        assert matcher._is_bid_matching_rule(bid, rule) is True

    def test_organization_exact_match_accepted(self, matcher):
        bid = _make_bid(organization_name='서울특별시')
        rule = _make_rule({'organizations': ['서울특별시']})
        assert matcher._is_bid_matching_rule(bid, rule) is True

    def test_organization_no_match_rejected(self, matcher):
        bid = _make_bid(organization_name='부산광역시')
        rule = _make_rule({'organizations': ['서울특별시']})
        assert matcher._is_bid_matching_rule(bid, rule) is False

    def test_organization_any_one_of_multiple_matches(self, matcher):
        bid = _make_bid(organization_name='경기도청')
        rule = _make_rule({'organizations': ['서울특별시', '경기도', '인천광역시']})
        assert matcher._is_bid_matching_rule(bid, rule) is True

    def test_empty_organizations_list_passes(self, matcher):
        bid = _make_bid()
        rule = _make_rule({'organizations': []})
        assert matcher._is_bid_matching_rule(bid, rule) is True

    def test_no_organizations_key_passes(self, matcher):
        bid = _make_bid()
        rule = _make_rule({})
        assert matcher._is_bid_matching_rule(bid, rule) is True


# ---------------------------------------------------------------------------
# 9. 카테고리/태그 매칭 (conditions['categories'])
# ---------------------------------------------------------------------------

class TestCategoryTagMatching:
    def test_category_match_found_accepted(self, matcher):
        bid = _make_bid(tags=['건설', '도로', '포장'])
        rule = _make_rule({'categories': ['도로']})
        assert matcher._is_bid_matching_rule(bid, rule) is True

    def test_category_no_match_rejected(self, matcher):
        bid = _make_bid(tags=['건설', '도로'])
        rule = _make_rule({'categories': ['소프트웨어']})
        assert matcher._is_bid_matching_rule(bid, rule) is False

    def test_empty_categories_list_passes(self, matcher):
        bid = _make_bid(tags=['건설'])
        rule = _make_rule({'categories': []})
        assert matcher._is_bid_matching_rule(bid, rule) is True

    def test_no_categories_key_passes(self, matcher):
        bid = _make_bid()
        rule = _make_rule({})
        assert matcher._is_bid_matching_rule(bid, rule) is True

    def test_empty_bid_tags_with_category_condition_rejected(self, matcher):
        """입찰에 태그가 없는데 카테고리 조건이 있으면 거부."""
        bid = _make_bid(tags=[])
        rule = _make_rule({'categories': ['건설']})
        assert matcher._is_bid_matching_rule(bid, rule) is False

    def test_bid_tags_missing_key_with_category_condition_rejected(self, matcher):
        """tags 키 자체가 없어도 빈 리스트로 처리 → 거부."""
        bid = _make_bid()
        del bid['tags']
        rule = _make_rule({'categories': ['건설']})
        assert matcher._is_bid_matching_rule(bid, rule) is False

    def test_any_one_of_multiple_categories_matches(self, matcher):
        bid = _make_bid(tags=['조경'])
        rule = _make_rule({'categories': ['건설', '조경', '전기']})
        assert matcher._is_bid_matching_rule(bid, rule) is True


# ---------------------------------------------------------------------------
# 10. 지역 매칭 (conditions['regions'])
# ---------------------------------------------------------------------------

class TestRegionMatching:
    def test_region_partial_match_accepted(self, matcher):
        bid = _make_bid(region_restriction='서울특별시 강남구')
        rule = _make_rule({'regions': ['서울특별시']})
        assert matcher._is_bid_matching_rule(bid, rule) is True

    def test_region_exact_match_accepted(self, matcher):
        bid = _make_bid(region_restriction='경기도')
        rule = _make_rule({'regions': ['경기도']})
        assert matcher._is_bid_matching_rule(bid, rule) is True

    def test_region_no_match_rejected(self, matcher):
        bid = _make_bid(region_restriction='부산광역시')
        rule = _make_rule({'regions': ['서울특별시']})
        assert matcher._is_bid_matching_rule(bid, rule) is False

    def test_empty_regions_list_passes(self, matcher):
        bid = _make_bid(region_restriction='제주도')
        rule = _make_rule({'regions': []})
        assert matcher._is_bid_matching_rule(bid, rule) is True

    def test_no_regions_key_passes(self, matcher):
        bid = _make_bid()
        rule = _make_rule({})
        assert matcher._is_bid_matching_rule(bid, rule) is True

    def test_no_region_restriction_on_bid_passes(self, matcher):
        """입찰에 region_restriction이 없으면(None) 지역 조건 스킵 → 통과."""
        bid = _make_bid(region_restriction=None)
        rule = _make_rule({'regions': ['서울특별시']})
        assert matcher._is_bid_matching_rule(bid, rule) is True

    def test_any_one_of_multiple_regions_matches(self, matcher):
        bid = _make_bid(region_restriction='인천광역시')
        rule = _make_rule({'regions': ['서울특별시', '인천광역시', '경기도']})
        assert matcher._is_bid_matching_rule(bid, rule) is True


# ---------------------------------------------------------------------------
# 11. 업종 매칭 (conditions['work_types'])
# ---------------------------------------------------------------------------

class TestWorkTypeMatching:
    def test_work_type_match_accepted(self, matcher):
        bid = _make_bid(work_types=['종합공사'])
        rule = _make_rule({'work_types': ['종합공사']})
        assert matcher._is_bid_matching_rule(bid, rule) is True

    def test_work_type_partial_match_accepted(self, matcher):
        """부분 문자열 매칭: joined list 내에 부분 포함."""
        bid = _make_bid(work_types=['전문공사(실내건축공사업)'])
        rule = _make_rule({'work_types': ['실내건축공사업']})
        assert matcher._is_bid_matching_rule(bid, rule) is True

    def test_work_type_no_match_rejected(self, matcher):
        bid = _make_bid(work_types=['종합공사'])
        rule = _make_rule({'work_types': ['전기공사업']})
        assert matcher._is_bid_matching_rule(bid, rule) is False

    def test_empty_work_types_condition_passes(self, matcher):
        bid = _make_bid(work_types=['종합공사'])
        rule = _make_rule({'work_types': []})
        assert matcher._is_bid_matching_rule(bid, rule) is True

    def test_no_work_types_key_passes(self, matcher):
        bid = _make_bid()
        rule = _make_rule({})
        assert matcher._is_bid_matching_rule(bid, rule) is True

    def test_empty_bid_work_types_skips_check(self, matcher):
        """입찰의 work_types가 빈 리스트이면 업종 체크 스킵 → 통과.

        구현 코드: `if bid_work_types:` 조건으로 스킵.
        """
        bid = _make_bid(work_types=[])
        rule = _make_rule({'work_types': ['종합공사']})
        assert matcher._is_bid_matching_rule(bid, rule) is True

    def test_multiple_work_types_in_bid_any_match(self, matcher):
        bid = _make_bid(work_types=['종합공사', '전기공사'])
        rule = _make_rule({'work_types': ['전기공사']})
        assert matcher._is_bid_matching_rule(bid, rule) is True


# ---------------------------------------------------------------------------
# 12. 복합 조건 (여러 조건 동시 적용)
# ---------------------------------------------------------------------------

class TestCombinedConditions:
    def test_all_conditions_met_accepted(self, matcher):
        bid = _make_bid(
            title='서울시 도로 포장공사',
            organization_name='서울특별시',
            estimated_price=100_000_000,
            region_restriction='서울특별시',
            tags=['건설', '도로'],
            work_types=['종합공사'],
        )
        rule = _make_rule({
            'keywords': ['도로'],
            'min_price': 50_000_000,
            'max_price': 200_000_000,
            'organizations': ['서울특별시'],
            'categories': ['도로'],
            'regions': ['서울특별시'],
            'work_types': ['종합공사'],
        })
        assert matcher._is_bid_matching_rule(bid, rule) is True

    def test_keyword_fails_rejects_even_if_rest_pass(self, matcher):
        bid = _make_bid(title='건물 신축 공사', organization_name='서울특별시')
        rule = _make_rule({
            'keywords': ['도로'],           # 이 조건만 실패
            'organizations': ['서울특별시'],
        })
        assert matcher._is_bid_matching_rule(bid, rule) is False

    def test_price_fails_rejects_even_if_keyword_passes(self, matcher):
        bid = _make_bid(title='도로 공사', estimated_price=10_000_000)
        rule = _make_rule({
            'keywords': ['도로'],
            'min_price': 50_000_000,  # 이 조건만 실패
        })
        assert matcher._is_bid_matching_rule(bid, rule) is False

    def test_organization_fails_rejects_even_if_keyword_passes(self, matcher):
        bid = _make_bid(title='도로 공사', organization_name='부산광역시')
        rule = _make_rule({
            'keywords': ['도로'],
            'organizations': ['서울특별시'],  # 이 조건만 실패
        })
        assert matcher._is_bid_matching_rule(bid, rule) is False

    def test_category_fails_rejects_even_if_rest_pass(self, matcher):
        bid = _make_bid(title='도로 공사', tags=['IT'])
        rule = _make_rule({
            'keywords': ['도로'],
            'categories': ['건설'],  # 이 조건만 실패
        })
        assert matcher._is_bid_matching_rule(bid, rule) is False

    def test_region_fails_rejects_even_if_rest_pass(self, matcher):
        bid = _make_bid(title='도로 공사', region_restriction='제주도')
        rule = _make_rule({
            'keywords': ['도로'],
            'regions': ['서울특별시'],  # 이 조건만 실패
        })
        assert matcher._is_bid_matching_rule(bid, rule) is False


# ---------------------------------------------------------------------------
# 13. 빈 conditions → 모든 입찰 통과
# ---------------------------------------------------------------------------

class TestEmptyConditions:
    def test_empty_conditions_always_passes(self, matcher):
        bid = _make_bid()
        rule = _make_rule({})
        assert matcher._is_bid_matching_rule(bid, rule) is True

    def test_empty_conditions_with_minimal_bid(self, matcher):
        """최소한의 입찰 데이터로도 빈 조건 통과."""
        bid = {
            'bid_notice_no': 'MIN001',
            'title': '최소 데이터',
            'organization_name': '기관명',
            'estimated_price': None,
            'region_restriction': None,
            'tags': [],
            'work_types': [],
        }
        rule = _make_rule({})
        assert matcher._is_bid_matching_rule(bid, rule) is True


# ---------------------------------------------------------------------------
# 14. 가격 범위 - 형식 혼용 (min_price가 있으면 price_min 무시)
# ---------------------------------------------------------------------------

class TestPriceFormatPriority:
    def test_min_price_takes_priority_over_price_min(self, matcher):
        """conditions.get('min_price') or conditions.get('price_min') 순서 확인.

        min_price=0 (falsy)이면 price_min으로 폴백된다.
        min_price가 truthy이면 그것을 사용한다.
        """
        bid = _make_bid(estimated_price=100_000_000)
        # min_price가 있으면 그것을 먼저 사용 (100억)
        rule = _make_rule({'min_price': 10_000_000_000, 'price_min': 50_000_000})
        # 100만 < 100억 → 거부 (min_price 사용)
        assert matcher._is_bid_matching_rule(bid, rule) is False

    def test_price_min_fallback_when_min_price_absent(self, matcher):
        """min_price가 없으면 price_min 사용."""
        bid = _make_bid(estimated_price=100_000_000)
        rule = _make_rule({'price_min': 50_000_000})
        assert matcher._is_bid_matching_rule(bid, rule) is True


# ---------------------------------------------------------------------------
# 15. 엣지 케이스
# ---------------------------------------------------------------------------

class TestEdgeCases:
    def test_keyword_matches_both_title_and_org(self, matcher):
        """제목과 기관명이 이어진 문자열에서 매칭된다."""
        bid = _make_bid(title='소하천 정비', organization_name='공주시')
        # '소하천 정비 공주시'.lower() 에 '정비 공주'가 포함된다
        rule = _make_rule({'keywords': ['정비 공주']})
        assert matcher._is_bid_matching_rule(bid, rule) is True

    def test_unicode_keyword_matching(self, matcher):
        bid = _make_bid(title='강교 보수 공사')
        rule = _make_rule({'keywords': ['강교']})
        assert matcher._is_bid_matching_rule(bid, rule) is True

    def test_work_types_joined_partial_match(self, matcher):
        """work_types 리스트를 join한 문자열에서 부분 매칭."""
        bid = _make_bid(work_types=['종합공사', '전문공사(실내건축공사업)'])
        rule = _make_rule({'work_types': ['실내건축']})
        assert matcher._is_bid_matching_rule(bid, rule) is True

    def test_single_char_keyword(self, matcher):
        """단일 문자 키워드도 매칭된다."""
        bid = _make_bid(title='A형 배관공사')
        rule = _make_rule({'keywords': ['A']})
        assert matcher._is_bid_matching_rule(bid, rule) is True

    def test_price_exactly_at_boundaries_accepted(self, matcher):
        """경계값은 허용 범위 내."""
        bid_min = _make_bid(estimated_price=50_000_000)
        bid_max = _make_bid(estimated_price=200_000_000)
        rule = _make_rule({'min_price': 50_000_000, 'max_price': 200_000_000})
        assert matcher._is_bid_matching_rule(bid_min, rule) is True
        assert matcher._is_bid_matching_rule(bid_max, rule) is True
