-- PostgreSQL Full-text Search 인덱스 생성
-- 한국어 검색 성능 최적화를 위한 인덱스

-- 1. 한국어 텍스트 검색 설정 생성
CREATE TEXT SEARCH CONFIGURATION korean (COPY = simple);

-- 2. 입찰공고 테이블 전문 검색 인덱스
-- 공고명 검색 인덱스
CREATE INDEX IF NOT EXISTS idx_bid_announcements_title_gin
ON bid_announcements
USING gin(to_tsvector('korean', bid_notice_name));

-- 공고 내용 검색 인덱스 (내용 필드가 있는 경우)
CREATE INDEX IF NOT EXISTS idx_bid_announcements_content_gin
ON bid_announcements
USING gin(to_tsvector('korean', COALESCE(content, '')));

-- 기관명 검색 인덱스
CREATE INDEX IF NOT EXISTS idx_bid_announcements_org_gin
ON bid_announcements
USING gin(to_tsvector('korean', organization_name));

-- 복합 검색 인덱스 (제목 + 기관명)
CREATE INDEX IF NOT EXISTS idx_bid_announcements_combined_gin
ON bid_announcements
USING gin(to_tsvector('korean', bid_notice_name || ' ' || organization_name));

-- 3. 문서 테이블 전문 검색 인덱스
CREATE INDEX IF NOT EXISTS idx_bid_documents_filename_gin
ON bid_documents
USING gin(to_tsvector('korean', file_name));

CREATE INDEX IF NOT EXISTS idx_bid_documents_content_gin
ON bid_documents
USING gin(to_tsvector('korean', COALESCE(extracted_text, '')));

-- 4. 기업 테이블 전문 검색 인덱스
CREATE INDEX IF NOT EXISTS idx_companies_name_gin
ON companies
USING gin(to_tsvector('korean', company_name));

CREATE INDEX IF NOT EXISTS idx_companies_description_gin
ON companies
USING gin(to_tsvector('korean', COALESCE(description, '')));

-- 5. 날짜 인덱스 (범위 검색 최적화)
CREATE INDEX IF NOT EXISTS idx_bid_announcements_dates
ON bid_announcements(announcement_date DESC, closing_date DESC);

-- 6. 가격 인덱스 (범위 검색 최적화)
CREATE INDEX IF NOT EXISTS idx_bid_announcements_price
ON bid_announcements(bid_amount);

-- 7. 상태 인덱스
CREATE INDEX IF NOT EXISTS idx_bid_announcements_status
ON bid_announcements(status);

-- 8. 복합 인덱스 (자주 함께 사용되는 필터)
CREATE INDEX IF NOT EXISTS idx_bid_announcements_status_date
ON bid_announcements(status, announcement_date DESC);

CREATE INDEX IF NOT EXISTS idx_bid_announcements_org_status
ON bid_announcements(organization_name, status);

-- 9. 트리그램 인덱스 (유사 검색 및 오타 허용)
CREATE EXTENSION IF NOT EXISTS pg_trgm;

CREATE INDEX IF NOT EXISTS idx_bid_announcements_title_trgm
ON bid_announcements
USING gin(bid_notice_name gin_trgm_ops);

CREATE INDEX IF NOT EXISTS idx_companies_name_trgm
ON companies
USING gin(company_name gin_trgm_ops);

-- 10. 검색 통계 테이블 (검색어 자동완성용)
CREATE TABLE IF NOT EXISTS search_history (
    id SERIAL PRIMARY KEY,
    search_query VARCHAR(255) NOT NULL,
    search_count INTEGER DEFAULT 1,
    last_searched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(search_query)
);

CREATE INDEX IF NOT EXISTS idx_search_history_query
ON search_history(search_query);

CREATE INDEX IF NOT EXISTS idx_search_history_count
ON search_history(search_count DESC);

-- 11. 검색 성능 모니터링을 위한 통계 수집
ANALYZE bid_announcements;
ANALYZE bid_documents;
ANALYZE companies;

-- 12. 검색 함수 생성 (옵션)
CREATE OR REPLACE FUNCTION search_bids(search_query TEXT)
RETURNS TABLE(
    id INTEGER,
    bid_notice_no VARCHAR,
    bid_notice_name VARCHAR,
    organization_name VARCHAR,
    bid_amount BIGINT,
    rank REAL
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        ba.id,
        ba.bid_notice_no,
        ba.bid_notice_name,
        ba.organization_name,
        ba.bid_amount,
        ts_rank(
            to_tsvector('korean', ba.bid_notice_name || ' ' || ba.organization_name),
            plainto_tsquery('korean', search_query)
        ) AS rank
    FROM bid_announcements ba
    WHERE
        to_tsvector('korean', ba.bid_notice_name || ' ' || ba.organization_name)
        @@ plainto_tsquery('korean', search_query)
    ORDER BY rank DESC
    LIMIT 100;
END;
$$ LANGUAGE plpgsql;

-- 13. 검색어 하이라이팅 함수
CREATE OR REPLACE FUNCTION highlight_search_result(
    text_content TEXT,
    search_query TEXT
) RETURNS TEXT AS $$
BEGIN
    RETURN ts_headline(
        'korean',
        text_content,
        plainto_tsquery('korean', search_query),
        'StartSel=<mark>, StopSel=</mark>, MaxWords=50, MinWords=20'
    );
END;
$$ LANGUAGE plpgsql;

-- 14. 인덱스 유지보수 설정
-- 자동 VACUUM 및 ANALYZE 설정
ALTER TABLE bid_announcements SET (autovacuum_vacuum_scale_factor = 0.1);
ALTER TABLE bid_announcements SET (autovacuum_analyze_scale_factor = 0.05);
ALTER TABLE bid_documents SET (autovacuum_vacuum_scale_factor = 0.1);
ALTER TABLE bid_documents SET (autovacuum_analyze_scale_factor = 0.05);

-- 인덱스 생성 완료 메시지
DO $$
BEGIN
    RAISE NOTICE '검색 인덱스 생성 완료!';
    RAISE NOTICE '생성된 인덱스:';
    RAISE NOTICE '  - Full-text search (GIN) 인덱스';
    RAISE NOTICE '  - 트리그램 (유사 검색) 인덱스';
    RAISE NOTICE '  - 날짜/가격/상태 필터링 인덱스';
    RAISE NOTICE '  - 검색 함수 및 하이라이팅 함수';
END $$;