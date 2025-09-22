-- PostgreSQL 전체 텍스트 검색을 위한 테이블 및 인덱스 생성

-- 한국어 검색 설정 (없으면 기본 설정 사용)
-- CREATE TEXT SEARCH CONFIGURATION korean (COPY = simple);

-- BidDocument 테이블에 새로운 컬럼 추가
ALTER TABLE bid_documents
ADD COLUMN IF NOT EXISTS markdown_file_path TEXT,
ADD COLUMN IF NOT EXISTS extracted_text_length INTEGER,
ADD COLUMN IF NOT EXISTS processed_at TIMESTAMP;

-- 기존 processed_text, processed_markdown 컬럼 제거 (선택사항)
-- ALTER TABLE bid_documents DROP COLUMN IF EXISTS processed_text;
-- ALTER TABLE bid_documents DROP COLUMN IF EXISTS processed_markdown;

-- 검색 최적화 테이블 생성
CREATE TABLE IF NOT EXISTS bid_document_search (
    id SERIAL PRIMARY KEY,
    bid_announcement_id INTEGER NOT NULL REFERENCES bid_announcements(id),
    bid_document_id INTEGER NOT NULL REFERENCES bid_documents(id),

    -- 빠른 검색을 위한 주요 필드
    bid_notice_no VARCHAR(50) NOT NULL,
    title TEXT NOT NULL,
    organization_name VARCHAR(200) NOT NULL,
    announcement_date TIMESTAMP NOT NULL,
    bid_amount NUMERIC(15, 0),

    -- 문서 요약 정보
    summary TEXT,
    keywords TEXT,
    important_dates TEXT,
    requirements TEXT,

    -- 전체 텍스트 검색 벡터
    search_vector tsvector,

    -- 마크다운 파일 경로
    markdown_file_path TEXT,

    -- 타임스탬프
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 인덱스 생성
CREATE INDEX IF NOT EXISTS idx_bid_document_search_announcement_id
ON bid_document_search(bid_announcement_id);

CREATE INDEX IF NOT EXISTS idx_bid_document_search_document_id
ON bid_document_search(bid_document_id);

CREATE INDEX IF NOT EXISTS idx_bid_document_search_notice_no
ON bid_document_search(bid_notice_no);

CREATE INDEX IF NOT EXISTS idx_bid_document_search_org
ON bid_document_search(organization_name);

CREATE INDEX IF NOT EXISTS idx_bid_document_search_date
ON bid_document_search(announcement_date);

CREATE INDEX IF NOT EXISTS idx_bid_document_search_amount
ON bid_document_search(bid_amount);

-- 복합 인덱스
CREATE INDEX IF NOT EXISTS idx_bid_document_search_org_date
ON bid_document_search(organization_name, announcement_date);

-- 전체 텍스트 검색을 위한 GIN 인덱스
CREATE INDEX IF NOT EXISTS idx_bid_document_search_vector
ON bid_document_search USING gin(search_vector);

-- 검색 키워드 통계 테이블
CREATE TABLE IF NOT EXISTS search_keywords (
    id SERIAL PRIMARY KEY,
    keyword VARCHAR(100) NOT NULL UNIQUE,
    search_count INTEGER DEFAULT 1,
    last_searched TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_search_keywords_keyword
ON search_keywords(keyword);

-- 전체 텍스트 검색 벡터 업데이트 트리거 함수
CREATE OR REPLACE FUNCTION update_search_vector() RETURNS trigger AS $$
BEGIN
    NEW.search_vector :=
        setweight(to_tsvector('simple', coalesce(NEW.title, '')), 'A') ||
        setweight(to_tsvector('simple', coalesce(NEW.organization_name, '')), 'B') ||
        setweight(to_tsvector('simple', coalesce(NEW.keywords, '')), 'B') ||
        setweight(to_tsvector('simple', coalesce(NEW.summary, '')), 'C') ||
        setweight(to_tsvector('simple', coalesce(NEW.requirements, '')), 'D');
    RETURN NEW;
END
$$ LANGUAGE plpgsql;

-- 트리거 생성
DROP TRIGGER IF EXISTS update_bid_document_search_vector ON bid_document_search;
CREATE TRIGGER update_bid_document_search_vector
BEFORE INSERT OR UPDATE ON bid_document_search
FOR EACH ROW EXECUTE FUNCTION update_search_vector();

-- 기존 데이터 마이그레이션을 위한 함수
CREATE OR REPLACE FUNCTION migrate_existing_data() RETURNS void AS $$
DECLARE
    rec RECORD;
BEGIN
    -- BidAnnouncement와 BidDocument 조인하여 검색 테이블 채우기
    FOR rec IN
        SELECT
            ba.id as bid_announcement_id,
            bd.id as bid_document_id,
            ba.bid_notice_no,
            ba.title,
            ba.organization_name,
            ba.announcement_date,
            ba.bid_amount,
            bd.markdown_file_path
        FROM bid_announcements ba
        LEFT JOIN bid_documents bd ON bd.bid_announcement_id = ba.id
        WHERE NOT EXISTS (
            SELECT 1 FROM bid_document_search bds
            WHERE bds.bid_announcement_id = ba.id
        )
    LOOP
        INSERT INTO bid_document_search (
            bid_announcement_id,
            bid_document_id,
            bid_notice_no,
            title,
            organization_name,
            announcement_date,
            bid_amount,
            markdown_file_path
        ) VALUES (
            rec.bid_announcement_id,
            rec.bid_document_id,
            rec.bid_notice_no,
            rec.title,
            rec.organization_name,
            rec.announcement_date,
            rec.bid_amount,
            rec.markdown_file_path
        );
    END LOOP;
END;
$$ LANGUAGE plpgsql;

-- 마이그레이션 실행 (선택사항)
-- SELECT migrate_existing_data();