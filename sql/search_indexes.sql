-- ====================================================
-- 검색 성능 최적화를 위한 인덱스 생성
-- Created: 2025-09-24
-- Description: Full-text search 및 필터링 성능 향상
-- ====================================================

-- ====================================================
-- 1. Full-Text Search 설정
-- ====================================================

-- PostgreSQL 한국어 검색 설정 (기본 설정이 없는 경우)
-- CREATE TEXT SEARCH CONFIGURATION korean (COPY = simple);

-- ====================================================
-- 2. bid_announcements 테이블 인덱스
-- ====================================================

-- 제목 Full-text 검색 인덱스
CREATE INDEX IF NOT EXISTS idx_bid_announcements_title_fts
ON bid_announcements
USING gin(to_tsvector('simple', title));

-- 기관명 검색 인덱스
CREATE INDEX IF NOT EXISTS idx_bid_announcements_organization
ON bid_announcements
USING btree(organization);

-- 상태 필터 인덱스
CREATE INDEX IF NOT EXISTS idx_bid_announcements_status
ON bid_announcements
USING btree(status);

-- 날짜 범위 검색 인덱스
CREATE INDEX IF NOT EXISTS idx_bid_announcements_announcement_date
ON bid_announcements
USING btree(announcement_date DESC);

CREATE INDEX IF NOT EXISTS idx_bid_announcements_deadline
ON bid_announcements
USING btree(deadline DESC);

-- 가격 범위 검색 인덱스
CREATE INDEX IF NOT EXISTS idx_bid_announcements_price
ON bid_announcements
USING btree(estimated_price);

-- 복합 인덱스: 상태 + 마감일 (자주 함께 사용되는 필터)
CREATE INDEX IF NOT EXISTS idx_bid_announcements_status_deadline
ON bid_announcements
USING btree(status, deadline DESC)
WHERE status IN ('active', 'pending');

-- 복합 인덱스: 기관 + 날짜
CREATE INDEX IF NOT EXISTS idx_bid_announcements_org_date
ON bid_announcements
USING btree(organization, announcement_date DESC);

-- ====================================================
-- 3. bid_documents 테이블 인덱스
-- ====================================================

-- 문서 내용 Full-text 검색 인덱스
CREATE INDEX IF NOT EXISTS idx_bid_documents_content_fts
ON bid_documents
USING gin(to_tsvector('simple', extracted_text))
WHERE extracted_text IS NOT NULL;

-- 파일 타입 인덱스
CREATE INDEX IF NOT EXISTS idx_bid_documents_file_type
ON bid_documents
USING btree(file_type);

-- 처리 상태 인덱스
CREATE INDEX IF NOT EXISTS idx_bid_documents_processing_status
ON bid_documents
USING btree(processing_status)
WHERE processing_status = 'completed';

-- announcement_id 외래 키 인덱스
CREATE INDEX IF NOT EXISTS idx_bid_documents_announcement_id
ON bid_documents
USING btree(announcement_id);

-- ====================================================
-- 4. bid_extracted_info 테이블 인덱스
-- ====================================================

-- 추출 정보 카테고리 인덱스
CREATE INDEX IF NOT EXISTS idx_bid_extracted_info_category
ON bid_extracted_info
USING btree(category);

-- 추출 정보 내용 검색 인덱스
CREATE INDEX IF NOT EXISTS idx_bid_extracted_info_content_fts
ON bid_extracted_info
USING gin(to_tsvector('simple', content));

-- document_id 외래 키 인덱스
CREATE INDEX IF NOT EXISTS idx_bid_extracted_info_document_id
ON bid_extracted_info
USING btree(document_id);

-- 복합 인덱스: 카테고리 + 신뢰도
CREATE INDEX IF NOT EXISTS idx_bid_extracted_info_category_confidence
ON bid_extracted_info
USING btree(category, confidence DESC)
WHERE confidence >= 0.7;

-- ====================================================
-- 5. bid_tags 테이블 인덱스
-- ====================================================

-- 태그명 유니크 인덱스 (이미 있을 수 있음)
CREATE UNIQUE INDEX IF NOT EXISTS idx_bid_tags_name_unique
ON bid_tags
USING btree(name);

-- 태그 카테고리 인덱스
CREATE INDEX IF NOT EXISTS idx_bid_tags_category
ON bid_tags
USING btree(category);

-- ====================================================
-- 6. bid_tag_relations 테이블 인덱스
-- ====================================================

-- 복합 인덱스: announcement_id + tag_id
CREATE INDEX IF NOT EXISTS idx_bid_tag_relations_announcement_tag
ON bid_tag_relations
USING btree(announcement_id, tag_id);

-- 역방향 인덱스: tag_id로 공고 찾기
CREATE INDEX IF NOT EXISTS idx_bid_tag_relations_tag_announcement
ON bid_tag_relations
USING btree(tag_id, announcement_id);

-- ====================================================
-- 7. bid_schedule 테이블 인덱스
-- ====================================================

-- 일정 이벤트 타입 인덱스
CREATE INDEX IF NOT EXISTS idx_bid_schedule_event_type
ON bid_schedule
USING btree(event_type);

-- 일정 날짜 인덱스
CREATE INDEX IF NOT EXISTS idx_bid_schedule_event_date
ON bid_schedule
USING btree(event_date DESC);

-- announcement_id 외래 키 인덱스
CREATE INDEX IF NOT EXISTS idx_bid_schedule_announcement_id
ON bid_schedule
USING btree(announcement_id);

-- ====================================================
-- 8. 통계 정보 업데이트
-- ====================================================

-- 테이블 통계 정보 업데이트 (쿼리 플래너 최적화)
ANALYZE bid_announcements;
ANALYZE bid_documents;
ANALYZE bid_extracted_info;
ANALYZE bid_tags;
ANALYZE bid_tag_relations;
ANALYZE bid_schedule;

-- ====================================================
-- 9. 성능 모니터링용 뷰
-- ====================================================

-- 인덱스 사용 통계 뷰
CREATE OR REPLACE VIEW v_index_usage_stats AS
SELECT
    schemaname,
    tablename,
    indexname,
    idx_scan as index_scans,
    idx_tup_read as tuples_read,
    idx_tup_fetch as tuples_fetched,
    pg_size_pretty(pg_relation_size(indexrelid)) as index_size
FROM pg_stat_user_indexes
WHERE schemaname = 'public'
ORDER BY idx_scan DESC;

-- 테이블 크기 및 성능 통계 뷰
CREATE OR REPLACE VIEW v_table_stats AS
SELECT
    schemaname,
    tablename,
    n_live_tup as live_rows,
    n_dead_tup as dead_rows,
    last_vacuum,
    last_autovacuum,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as total_size
FROM pg_stat_user_tables
WHERE schemaname = 'public'
ORDER BY n_live_tup DESC;

-- ====================================================
-- 10. 검색 성능 개선 함수
-- ====================================================

-- 통합 검색 함수
CREATE OR REPLACE FUNCTION search_bid_announcements(
    search_query TEXT,
    org_filter TEXT DEFAULT NULL,
    status_filter TEXT DEFAULT NULL,
    min_price NUMERIC DEFAULT NULL,
    max_price NUMERIC DEFAULT NULL,
    start_date DATE DEFAULT NULL,
    end_date DATE DEFAULT NULL,
    limit_count INTEGER DEFAULT 20,
    offset_count INTEGER DEFAULT 0
)
RETURNS TABLE (
    id UUID,
    title TEXT,
    organization TEXT,
    status TEXT,
    estimated_price NUMERIC,
    deadline TIMESTAMP,
    rank REAL
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        a.id,
        a.title,
        a.organization,
        a.status,
        a.estimated_price,
        a.deadline,
        CASE
            WHEN search_query IS NOT NULL AND search_query != '' THEN
                ts_rank(to_tsvector('simple', a.title), plainto_tsquery('simple', search_query))
            ELSE 1.0
        END as rank
    FROM bid_announcements a
    WHERE
        -- Full-text search
        (search_query IS NULL OR search_query = '' OR
         to_tsvector('simple', a.title) @@ plainto_tsquery('simple', search_query))
        -- Organization filter
        AND (org_filter IS NULL OR a.organization = org_filter)
        -- Status filter
        AND (status_filter IS NULL OR a.status = status_filter)
        -- Price range filter
        AND (min_price IS NULL OR a.estimated_price >= min_price)
        AND (max_price IS NULL OR a.estimated_price <= max_price)
        -- Date range filter
        AND (start_date IS NULL OR a.announcement_date >= start_date)
        AND (end_date IS NULL OR a.announcement_date <= end_date)
    ORDER BY
        rank DESC,
        a.announcement_date DESC
    LIMIT limit_count
    OFFSET offset_count;
END;
$$ LANGUAGE plpgsql;

-- 자동완성 제안 함수
CREATE OR REPLACE FUNCTION get_search_suggestions(
    prefix TEXT,
    max_results INTEGER DEFAULT 10
)
RETURNS TABLE (
    suggestion TEXT,
    count BIGINT
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        DISTINCT substring(title from 1 for 50) as suggestion,
        COUNT(*) as count
    FROM bid_announcements
    WHERE
        title ILIKE prefix || '%'
        AND status IN ('active', 'pending')
    GROUP BY substring(title from 1 for 50)
    ORDER BY count DESC
    LIMIT max_results;
END;
$$ LANGUAGE plpgsql;

-- 패싯 정보 가져오기 함수
CREATE OR REPLACE FUNCTION get_search_facets()
RETURNS TABLE (
    facet_type TEXT,
    facet_value TEXT,
    count BIGINT
) AS $$
BEGIN
    -- 기관별 카운트
    RETURN QUERY
    SELECT
        'organization'::TEXT as facet_type,
        organization::TEXT as facet_value,
        COUNT(*) as count
    FROM bid_announcements
    WHERE status IN ('active', 'pending')
    GROUP BY organization
    ORDER BY count DESC
    LIMIT 10;

    -- 상태별 카운트
    RETURN QUERY
    SELECT
        'status'::TEXT as facet_type,
        status::TEXT as facet_value,
        COUNT(*) as count
    FROM bid_announcements
    GROUP BY status;

    -- 가격 범위별 카운트
    RETURN QUERY
    SELECT
        'price_range'::TEXT as facet_type,
        CASE
            WHEN estimated_price < 10000000 THEN '1천만원 미만'
            WHEN estimated_price < 50000000 THEN '1천만원 ~ 5천만원'
            WHEN estimated_price < 100000000 THEN '5천만원 ~ 1억원'
            WHEN estimated_price < 500000000 THEN '1억원 ~ 5억원'
            ELSE '5억원 이상'
        END as facet_value,
        COUNT(*) as count
    FROM bid_announcements
    WHERE estimated_price IS NOT NULL
    GROUP BY facet_value
    ORDER BY
        CASE facet_value
            WHEN '1천만원 미만' THEN 1
            WHEN '1천만원 ~ 5천만원' THEN 2
            WHEN '5천만원 ~ 1억원' THEN 3
            WHEN '1억원 ~ 5억원' THEN 4
            ELSE 5
        END;
END;
$$ LANGUAGE plpgsql;

-- ====================================================
-- 실행 완료 메시지
-- ====================================================
DO $$
BEGIN
    RAISE NOTICE 'Search optimization indexes and functions created successfully';
    RAISE NOTICE 'Run ANALYZE on tables to update statistics';
    RAISE NOTICE 'Monitor performance with v_index_usage_stats and v_table_stats views';
END $$;