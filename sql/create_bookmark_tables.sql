-- 북마크 시스템 테이블 생성
-- 실행: psql -U blockmeta -d odin_db -f sql/create_bookmark_tables.sql

-- 1. 사용자 북마크 테이블
CREATE TABLE IF NOT EXISTS user_bookmarks (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    bid_id VARCHAR(100) NOT NULL,
    title TEXT,
    organization_name VARCHAR(255),
    estimated_price BIGINT,
    bid_end_date TIMESTAMP,
    notes TEXT,  -- 사용자 메모
    tags TEXT[], -- 사용자 정의 태그
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, bid_id) -- 같은 사용자가 같은 공고를 중복 북마크 방지
);

-- 2. 북마크 폴더 (선택적 기능)
CREATE TABLE IF NOT EXISTS bookmark_folders (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    folder_name VARCHAR(100) NOT NULL,
    description TEXT,
    color VARCHAR(7), -- HEX 색상 코드
    icon VARCHAR(50), -- 아이콘 이름
    is_default BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, folder_name)
);

-- 3. 북마크-폴더 관계
CREATE TABLE IF NOT EXISTS bookmark_folder_relations (
    id SERIAL PRIMARY KEY,
    bookmark_id INTEGER REFERENCES user_bookmarks(id) ON DELETE CASCADE,
    folder_id INTEGER REFERENCES bookmark_folders(id) ON DELETE CASCADE,
    UNIQUE(bookmark_id, folder_id)
);

-- 인덱스 생성
CREATE INDEX IF NOT EXISTS idx_bookmarks_user ON user_bookmarks(user_id);
CREATE INDEX IF NOT EXISTS idx_bookmarks_bid ON user_bookmarks(bid_id);
CREATE INDEX IF NOT EXISTS idx_bookmarks_created ON user_bookmarks(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_bookmarks_end_date ON user_bookmarks(bid_end_date);

-- 뷰: 사용자별 북마크 통계
CREATE OR REPLACE VIEW v_user_bookmark_stats AS
SELECT
    user_id,
    COUNT(*) as total_bookmarks,
    COUNT(CASE WHEN bid_end_date > NOW() THEN 1 END) as active_bookmarks,
    COUNT(CASE WHEN bid_end_date <= NOW() THEN 1 END) as expired_bookmarks,
    MIN(created_at) as first_bookmark,
    MAX(created_at) as last_bookmark
FROM user_bookmarks
GROUP BY user_id;

-- 뷰: 인기 북마크 공고
CREATE OR REPLACE VIEW v_popular_bookmarks AS
SELECT
    bid_id,
    COUNT(DISTINCT user_id) as bookmark_count,
    MIN(title) as title,
    MIN(organization_name) as organization,
    MAX(bid_end_date) as bid_end_date
FROM user_bookmarks
GROUP BY bid_id
HAVING COUNT(DISTINCT user_id) > 1
ORDER BY bookmark_count DESC;

-- 함수: 북마크 토글 (추가/삭제)
CREATE OR REPLACE FUNCTION toggle_bookmark(
    p_user_id INTEGER,
    p_bid_id VARCHAR(100),
    p_title TEXT DEFAULT NULL,
    p_organization VARCHAR(255) DEFAULT NULL,
    p_price BIGINT DEFAULT NULL,
    p_end_date TIMESTAMP DEFAULT NULL
) RETURNS JSON AS $$
DECLARE
    v_bookmark_id INTEGER;
    v_action VARCHAR(10);
BEGIN
    -- 기존 북마크 확인
    SELECT id INTO v_bookmark_id
    FROM user_bookmarks
    WHERE user_id = p_user_id AND bid_id = p_bid_id;

    IF v_bookmark_id IS NOT NULL THEN
        -- 북마크 제거
        DELETE FROM user_bookmarks WHERE id = v_bookmark_id;
        v_action := 'removed';
    ELSE
        -- 북마크 추가
        INSERT INTO user_bookmarks (
            user_id, bid_id, title, organization_name,
            estimated_price, bid_end_date
        ) VALUES (
            p_user_id, p_bid_id, p_title, p_organization,
            p_price, p_end_date
        ) RETURNING id INTO v_bookmark_id;
        v_action := 'added';
    END IF;

    RETURN json_build_object(
        'success', true,
        'action', v_action,
        'bookmark_id', v_bookmark_id,
        'bid_id', p_bid_id
    );
END;
$$ LANGUAGE plpgsql;

-- 권한 설정
GRANT ALL ON ALL TABLES IN SCHEMA public TO blockmeta;
GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO blockmeta;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO blockmeta;

COMMENT ON TABLE user_bookmarks IS '사용자 북마크';
COMMENT ON TABLE bookmark_folders IS '북마크 폴더';
COMMENT ON TABLE bookmark_folder_relations IS '북마크-폴더 관계';