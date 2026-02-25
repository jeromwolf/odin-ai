-- AI 추천 시스템 테이블 생성
-- 2025-09-25

-- 사용자 선호도 테이블
CREATE TABLE user_preferences (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,

    -- 선호 카테고리 (가중치 포함)
    preferred_categories JSONB DEFAULT '{}',
    /* 예시:
    {
        "건설": 0.8,
        "소프트웨어": 0.6,
        "물품": 0.3
    }
    */

    -- 선호 기관
    preferred_organizations JSONB DEFAULT '[]',

    -- 선호 지역
    preferred_regions JSONB DEFAULT '[]',

    -- 선호 가격대
    preferred_price_min BIGINT,
    preferred_price_max BIGINT,

    -- 선호 키워드 (빈도 포함)
    preferred_keywords JSONB DEFAULT '{}',
    /* 예시:
    {
        "시스템": 15,
        "개발": 12,
        "구축": 8
    }
    */

    -- 비선호 키워드
    excluded_keywords JSONB DEFAULT '[]',

    -- 통계
    total_interactions INTEGER DEFAULT 0,
    total_bookmarks INTEGER DEFAULT 0,
    total_views INTEGER DEFAULT 0,

    -- 업데이트 시간
    last_calculated_at TIMESTAMP DEFAULT NOW(),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    UNIQUE(user_id)
);

-- 사용자 입찰 상호작용 기록
CREATE TABLE user_bid_interactions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    bid_notice_no VARCHAR(20) NOT NULL REFERENCES bid_announcements(bid_notice_no),

    -- 상호작용 유형
    interaction_type VARCHAR(20) NOT NULL, -- view, bookmark, download, click
    interaction_score FLOAT DEFAULT 1.0, -- 가중치 (view=1, click=2, download=3, bookmark=5)

    -- 상호작용 시간
    duration_seconds INTEGER, -- 페이지 체류 시간

    -- 상호작용 컨텍스트
    source VARCHAR(50), -- search, recommendation, direct
    search_query TEXT, -- 검색어 (검색 결과에서 온 경우)

    created_at TIMESTAMP DEFAULT NOW(),

    -- 인덱스를 위한 복합 유니크 제약
    UNIQUE(user_id, bid_notice_no, interaction_type, created_at)
);

-- 입찰 간 유사도 테이블 (사전 계산)
CREATE TABLE bid_similarities (
    id SERIAL PRIMARY KEY,
    bid_notice_no_1 VARCHAR(20) NOT NULL REFERENCES bid_announcements(bid_notice_no),
    bid_notice_no_2 VARCHAR(20) NOT NULL REFERENCES bid_announcements(bid_notice_no),

    -- 유사도 점수
    title_similarity FLOAT, -- 제목 유사도 (0~1)
    category_similarity FLOAT, -- 카테고리 유사도
    organization_similarity FLOAT, -- 기관 유사도
    price_similarity FLOAT, -- 가격대 유사도
    keyword_similarity FLOAT, -- 키워드 유사도

    -- 종합 유사도
    overall_similarity FLOAT NOT NULL, -- 가중 평균

    calculated_at TIMESTAMP DEFAULT NOW(),

    UNIQUE(bid_notice_no_1, bid_notice_no_2),
    CHECK (bid_notice_no_1 < bid_notice_no_2) -- 중복 방지
);

-- 추천 이력
CREATE TABLE recommendation_history (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    bid_notice_no VARCHAR(20) NOT NULL REFERENCES bid_announcements(bid_notice_no),

    -- 추천 정보
    recommendation_type VARCHAR(50) NOT NULL, -- collaborative, content_based, hybrid, trending
    recommendation_score FLOAT NOT NULL, -- 추천 점수 (0~100)

    -- 추천 이유
    recommendation_reasons JSONB,
    /* 예시:
    {
        "similar_to_bookmarks": ["bid-001", "bid-002"],
        "matches_preferences": ["건설", "서울"],
        "trending_in_category": "소프트웨어",
        "users_also_viewed": 15
    }
    */

    -- 추천 컨텍스트
    context VARCHAR(50), -- homepage, search_result, detail_page

    -- 사용자 반응
    was_clicked BOOLEAN DEFAULT false,
    was_bookmarked BOOLEAN DEFAULT false,
    click_position INTEGER, -- 클릭한 경우 순위

    created_at TIMESTAMP DEFAULT NOW()
);

-- 추천 피드백
CREATE TABLE recommendation_feedback (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    recommendation_id INTEGER REFERENCES recommendation_history(id),

    -- 피드백 유형
    feedback_type VARCHAR(20) NOT NULL, -- like, dislike, not_relevant
    feedback_score INTEGER, -- 1~5 별점
    feedback_text TEXT, -- 사용자 코멘트

    -- 피드백 이유
    feedback_reasons JSONB DEFAULT '[]',
    /* 예시:
    ["price_too_high", "wrong_category", "expired"]
    */

    created_at TIMESTAMP DEFAULT NOW()
);

-- 인덱스 생성
CREATE INDEX idx_user_preferences_user_id ON user_preferences(user_id);
CREATE INDEX idx_user_bid_interactions_user_id ON user_bid_interactions(user_id);
CREATE INDEX idx_user_bid_interactions_bid_notice_no ON user_bid_interactions(bid_notice_no);
CREATE INDEX idx_user_bid_interactions_created_at ON user_bid_interactions(created_at);
CREATE INDEX idx_bid_similarities_bid1 ON bid_similarities(bid_notice_no_1);
CREATE INDEX idx_bid_similarities_bid2 ON bid_similarities(bid_notice_no_2);
CREATE INDEX idx_bid_similarities_overall ON bid_similarities(overall_similarity DESC);
CREATE INDEX idx_recommendation_history_user_id ON recommendation_history(user_id);
CREATE INDEX idx_recommendation_history_created_at ON recommendation_history(created_at);
CREATE INDEX idx_recommendation_feedback_user_id ON recommendation_feedback(user_id);

-- 사용자 선호도 업데이트 함수
CREATE OR REPLACE FUNCTION update_user_preferences(
    p_user_id INTEGER
) RETURNS VOID AS $$
DECLARE
    v_category_prefs JSONB;
    v_org_prefs JSONB;
    v_keyword_prefs JSONB;
BEGIN
    -- 북마크 기반 카테고리 선호도 계산
    WITH bookmark_categories AS (
        SELECT
            t.tag_name,
            COUNT(*) as count
        FROM user_bookmarks ub
        JOIN bid_tag_relations btr ON ub.bid_id = btr.bid_notice_no
        JOIN bid_tags t ON btr.tag_id = t.tag_id
        WHERE ub.user_id = p_user_id
        GROUP BY t.tag_name
    )
    SELECT jsonb_object_agg(
        tag_name,
        ROUND(count::numeric / total_count, 2)
    ) INTO v_category_prefs
    FROM bookmark_categories, (SELECT SUM(count) as total_count FROM bookmark_categories) t;

    -- 북마크 기반 기관 선호도
    WITH bookmark_orgs AS (
        SELECT
            b.organization_name,
            COUNT(*) as count
        FROM user_bookmarks ub
        JOIN bid_announcements b ON ub.bid_id = b.bid_notice_no
        WHERE ub.user_id = p_user_id
            AND b.organization_name IS NOT NULL
        GROUP BY b.organization_name
        ORDER BY count DESC
        LIMIT 10
    )
    SELECT jsonb_agg(organization_name) INTO v_org_prefs
    FROM bookmark_orgs;

    -- 상호작용 기반 키워드 추출 (간단한 버전)
    v_keyword_prefs := '{}';

    -- 선호도 업데이트 또는 생성
    INSERT INTO user_preferences (
        user_id,
        preferred_categories,
        preferred_organizations,
        preferred_keywords,
        last_calculated_at
    ) VALUES (
        p_user_id,
        COALESCE(v_category_prefs, '{}'),
        COALESCE(v_org_prefs, '[]'),
        v_keyword_prefs,
        NOW()
    )
    ON CONFLICT (user_id) DO UPDATE SET
        preferred_categories = COALESCE(v_category_prefs, '{}'),
        preferred_organizations = COALESCE(v_org_prefs, '[]'),
        preferred_keywords = v_keyword_prefs,
        last_calculated_at = NOW();
END;
$$ LANGUAGE plpgsql;

-- 추천 점수 계산 함수
CREATE OR REPLACE FUNCTION calculate_recommendation_score(
    p_user_id INTEGER,
    p_bid_notice_no VARCHAR(20)
) RETURNS FLOAT AS $$
DECLARE
    v_score FLOAT := 0;
    v_preferences RECORD;
    v_bid RECORD;
    v_category_match FLOAT := 0;
    v_org_match FLOAT := 0;
    v_similar_bookmarks INTEGER := 0;
BEGIN
    -- 사용자 선호도 조회
    SELECT * INTO v_preferences
    FROM user_preferences
    WHERE user_id = p_user_id;

    IF v_preferences IS NULL THEN
        RETURN 50; -- 기본 점수
    END IF;

    -- 입찰 정보 조회
    SELECT * INTO v_bid
    FROM bid_announcements
    WHERE bid_notice_no = p_bid_notice_no;

    IF v_bid IS NULL THEN
        RETURN 0;
    END IF;

    -- 1. 카테고리 매칭 점수 (30점)
    IF v_preferences.preferred_categories IS NOT NULL THEN
        -- 태그와 선호 카테고리 매칭
        SELECT COALESCE(SUM(
            (v_preferences.preferred_categories->>(t.tag_name))::float
        ), 0) * 30 INTO v_category_match
        FROM bid_tag_relations btr
        JOIN bid_tags t ON btr.tag_id = t.tag_id
        WHERE btr.bid_notice_no = p_bid_notice_no;

        v_score := v_score + LEAST(v_category_match, 30);
    END IF;

    -- 2. 기관 매칭 점수 (20점)
    IF v_preferences.preferred_organizations ? v_bid.organization_name THEN
        v_score := v_score + 20;
    END IF;

    -- 3. 유사 북마크 점수 (30점)
    SELECT COUNT(*) INTO v_similar_bookmarks
    FROM bid_similarities bs
    JOIN user_bookmarks ub ON (
        ub.bid_id = bs.bid_notice_no_1 OR
        ub.bid_id = bs.bid_notice_no_2
    )
    WHERE ub.user_id = p_user_id
        AND (bs.bid_notice_no_1 = p_bid_notice_no OR
             bs.bid_notice_no_2 = p_bid_notice_no)
        AND bs.overall_similarity > 0.7;

    v_score := v_score + LEAST(v_similar_bookmarks * 10, 30);

    -- 4. 신규성 점수 (10점)
    IF v_bid.created_at > NOW() - INTERVAL '7 days' THEN
        v_score := v_score + 10;
    ELSIF v_bid.created_at > NOW() - INTERVAL '14 days' THEN
        v_score := v_score + 5;
    END IF;

    -- 5. 마감 임박 점수 (10점)
    IF v_bid.bid_end_date BETWEEN NOW() AND NOW() + INTERVAL '7 days' THEN
        v_score := v_score + 10;
    END IF;

    RETURN LEAST(v_score, 100);
END;
$$ LANGUAGE plpgsql;

-- 협업 필터링 추천 함수
CREATE OR REPLACE FUNCTION get_collaborative_recommendations(
    p_user_id INTEGER,
    p_limit INTEGER DEFAULT 10
) RETURNS TABLE (
    bid_notice_no VARCHAR(20),
    score FLOAT
) AS $$
BEGIN
    RETURN QUERY
    WITH user_bookmarks_set AS (
        -- 현재 사용자의 북마크
        SELECT bid_id
        FROM user_bookmarks
        WHERE user_id = p_user_id
    ),
    similar_users AS (
        -- 비슷한 북마크를 가진 사용자 찾기
        SELECT
            ub2.user_id,
            COUNT(*) as common_bookmarks
        FROM user_bookmarks ub1
        JOIN user_bookmarks ub2 ON ub1.bid_id = ub2.bid_id
        WHERE ub1.user_id = p_user_id
            AND ub2.user_id != p_user_id
        GROUP BY ub2.user_id
        HAVING COUNT(*) >= 2
        ORDER BY common_bookmarks DESC
        LIMIT 20
    )
    -- 유사 사용자들이 북마크한 입찰 추천
    SELECT
        ub.bid_id,
        COUNT(*)::float / (SELECT MAX(common_bookmarks) FROM similar_users) * 100 as rec_score
    FROM user_bookmarks ub
    JOIN similar_users su ON ub.user_id = su.user_id
    WHERE ub.bid_id NOT IN (SELECT bid_id FROM user_bookmarks_set)
        AND EXISTS (
            SELECT 1 FROM bid_announcements ba
            WHERE ba.bid_notice_no = ub.bid_id
                AND ba.bid_end_date > NOW()
        )
    GROUP BY ub.bid_id
    ORDER BY rec_score DESC
    LIMIT p_limit;
END;
$$ LANGUAGE plpgsql;

-- 트리거: 상호작용 시 선호도 업데이트
CREATE OR REPLACE FUNCTION trigger_update_preferences()
RETURNS TRIGGER AS $$
BEGIN
    -- 10번의 상호작용마다 선호도 재계산
    IF (SELECT COUNT(*) FROM user_bid_interactions
        WHERE user_id = NEW.user_id) % 10 = 0 THEN
        PERFORM update_user_preferences(NEW.user_id);
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_preferences_on_interaction
AFTER INSERT ON user_bid_interactions
FOR EACH ROW EXECUTE FUNCTION trigger_update_preferences();

-- 권한 부여
GRANT ALL ON ALL TABLES IN SCHEMA public TO blockmeta;
GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO blockmeta;