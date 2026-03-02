-- 낙찰정보 컬럼 추가 마이그레이션
-- 조달청 나라장터 낙찰정보서비스 API 연동용

-- pg_trgm 확장 (유사 입찰 검색용)
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- 낙찰 정보 컬럼 추가
ALTER TABLE bid_announcements ADD COLUMN IF NOT EXISTS winning_company VARCHAR(200);
ALTER TABLE bid_announcements ADD COLUMN IF NOT EXISTS winning_bizno VARCHAR(20);
ALTER TABLE bid_announcements ADD COLUMN IF NOT EXISTS winning_price BIGINT;
ALTER TABLE bid_announcements ADD COLUMN IF NOT EXISTS winning_rate FLOAT;
ALTER TABLE bid_announcements ADD COLUMN IF NOT EXISTS bid_participant_count INTEGER;
ALTER TABLE bid_announcements ADD COLUMN IF NOT EXISTS award_date TIMESTAMP;
ALTER TABLE bid_announcements ADD COLUMN IF NOT EXISTS award_status VARCHAR(20) DEFAULT 'pending';

-- 인덱스 추가
CREATE INDEX IF NOT EXISTS idx_award_company ON bid_announcements(winning_company);
CREATE INDEX IF NOT EXISTS idx_award_status ON bid_announcements(award_status);
CREATE INDEX IF NOT EXISTS idx_award_date ON bid_announcements(award_date);

-- 제목 trigram 인덱스 (유사 입찰 검색 성능)
CREATE INDEX IF NOT EXISTS idx_title_trgm ON bid_announcements USING gin (title gin_trgm_ops);
