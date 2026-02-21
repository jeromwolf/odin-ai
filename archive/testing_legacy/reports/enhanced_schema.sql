-- 🏗️ 확장된 데이터베이스 스키마 (표 파싱 기능 포함)
-- 작성일: 2025-09-23
-- 목적: 표에서 추출한 구조화된 데이터 저장

-- 기존 테이블 삭제
DROP TABLE IF EXISTS bid_extracted_info CASCADE;
DROP TABLE IF EXISTS bid_schedule CASCADE;
DROP TABLE IF EXISTS bid_attachments CASCADE;
DROP TABLE IF EXISTS bid_documents CASCADE;
DROP TABLE IF EXISTS bid_announcements CASCADE;

-- 1. 확장된 bid_announcements 테이블
CREATE TABLE bid_announcements (
    id SERIAL PRIMARY KEY,
    bid_notice_no VARCHAR(100) UNIQUE NOT NULL,

    -- 기본 정보
    title TEXT,
    organization_name VARCHAR(255),
    demand_institution VARCHAR(255),
    bid_method VARCHAR(100),

    -- 💰 금액 정보 (표에서 추출)
    estimated_price BIGINT,              -- 추정가격
    budget_price BIGINT,                 -- 예가/예정가격
    min_price BIGINT,                    -- 최소 입찰가
    max_price BIGINT,                    -- 최대 입찰가
    vat_amount BIGINT,                   -- 부가가치세
    total_amount BIGINT,                 -- 총액
    price_unit VARCHAR(10) DEFAULT '원', -- 통화 단위

    -- 📅 일정 정보 (표에서 추출)
    announcement_date TIMESTAMP,         -- 공고일
    registration_start_date TIMESTAMP,   -- 참가자격등록 시작
    registration_end_date TIMESTAMP,     -- 참가자격등록 마감
    bid_start_date TIMESTAMP,           -- 입찰 시작일
    bid_end_date TIMESTAMP,             -- 입찰 마감일
    submission_start_date TIMESTAMP,    -- 제출 시작일
    submission_end_date TIMESTAMP,      -- 제출 마감일
    opening_date TIMESTAMP,             -- 개찰일시
    contract_date TIMESTAMP,            -- 계약 예정일

    -- 🏢 자격 및 조건
    industry_type VARCHAR(100),         -- 업종 (전기공사, 건축공사 등)
    region_restriction VARCHAR(100),    -- 지역제한
    qualification_requirements TEXT,    -- 자격요건 상세
    license_required VARCHAR(200),      -- 필요 면허/등록

    -- 📋 계약 조건
    contract_method VARCHAR(50),        -- 계약방식 (경쟁입찰, 수의계약)
    joint_venture_allowed BOOLEAN DEFAULT NULL, -- 공동수급 허용여부
    tax_exemption_applicable BOOLEAN DEFAULT NULL, -- 면세 적용여부
    price_method VARCHAR(100),          -- 예가 방법

    -- 🔍 처리 상태
    collection_status VARCHAR(50) DEFAULT 'pending',
    parsing_status VARCHAR(50) DEFAULT 'pending',    -- 표 파싱 상태
    data_completeness_score FLOAT DEFAULT 0.0,       -- 데이터 완성도 (0-1)
    extraction_confidence FLOAT DEFAULT 0.0,         -- 추출 신뢰도 (0-1)

    -- 📊 메타데이터
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    parsed_at TIMESTAMP,                -- 표 파싱 완료 시간
    last_verified_at TIMESTAMP          -- 마지막 검증 시간
);

-- 2. bid_documents 테이블 (기존 + 확장)
CREATE TABLE bid_documents (
    document_id SERIAL PRIMARY KEY,
    bid_notice_no VARCHAR(100) NOT NULL,

    -- 기본 정보
    document_type VARCHAR(50),
    file_name TEXT,
    file_extension VARCHAR(10),
    file_size BIGINT,
    download_url TEXT,
    file_seq INTEGER,

    -- 저장 경로
    storage_path TEXT,
    markdown_path TEXT,

    -- 처리 상태
    download_status VARCHAR(50) DEFAULT 'pending',
    processing_status VARCHAR(50) DEFAULT 'pending',
    parsing_status VARCHAR(50) DEFAULT 'pending',     -- 표 파싱 상태

    -- 추출된 콘텐츠
    extracted_text TEXT,
    text_length INTEGER,
    extraction_method VARCHAR(255),

    -- 📊 표 파싱 결과
    tables_found INTEGER DEFAULT 0,                   -- 발견된 표 개수
    tables_parsed INTEGER DEFAULT 0,                  -- 파싱 성공한 표 개수
    key_data_extracted BOOLEAN DEFAULT FALSE,         -- 핵심 데이터 추출 여부
    parsing_confidence FLOAT DEFAULT 0.0,             -- 파싱 신뢰도

    -- 시간 정보
    downloaded_at TIMESTAMP,
    processed_at TIMESTAMP,
    parsed_at TIMESTAMP,                -- 표 파싱 완료 시간

    -- 오류 정보
    error_message TEXT,
    parsing_errors TEXT,                -- 표 파싱 오류 메시지

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 3. 📊 bid_extracted_info 테이블 (신규)
CREATE TABLE bid_extracted_info (
    info_id SERIAL PRIMARY KEY,
    bid_notice_no VARCHAR(100) NOT NULL,
    document_id INTEGER REFERENCES bid_documents(document_id),

    -- 분류 정보
    info_category VARCHAR(50) NOT NULL,  -- 'price', 'schedule', 'qualification', 'contract'
    field_name VARCHAR(100) NOT NULL,    -- 구체적 필드명
    field_value TEXT,                    -- 추출된 값
    field_type VARCHAR(20),              -- 'text', 'number', 'date', 'boolean'

    -- 품질 정보
    confidence_score FLOAT DEFAULT 0.0,  -- 추출 신뢰도 (0-1)
    verification_status VARCHAR(20) DEFAULT 'unverified', -- 'verified', 'unverified', 'invalid'

    -- 추출 메타데이터
    extraction_method VARCHAR(50),       -- 'regex', 'table_parsing', 'gpt4', 'manual'
    source_location TEXT,                -- 원본에서의 위치 정보
    raw_text_sample TEXT,                -- 원본 텍스트 샘플

    -- 시간 정보
    extracted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    verified_at TIMESTAMP,

    -- 추가 정보
    notes TEXT,                          -- 추가 설명
    tags VARCHAR(200)                    -- 태그 (쉼표 구분)
);

-- 4. 📅 bid_schedule 테이블 (신규)
CREATE TABLE bid_schedule (
    schedule_id SERIAL PRIMARY KEY,
    bid_notice_no VARCHAR(100) NOT NULL,

    -- 일정 정보
    event_type VARCHAR(50) NOT NULL,     -- 'announcement', 'registration_start', 'registration_end', 'submission_start', 'submission_end', 'opening', 'contract'
    event_date TIMESTAMP,
    event_time TIME,
    event_description TEXT,

    -- 장소 정보
    location VARCHAR(255),
    online_url TEXT,

    -- 상태 정보
    is_confirmed BOOLEAN DEFAULT FALSE,
    is_postponed BOOLEAN DEFAULT FALSE,
    postponed_reason TEXT,
    original_date TIMESTAMP,             -- 연기된 경우 원래 날짜

    -- 알림 정보
    notification_sent BOOLEAN DEFAULT FALSE,
    reminder_sent BOOLEAN DEFAULT FALSE,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 5. bid_attachments 테이블 (기존)
CREATE TABLE bid_attachments (
    attachment_id SERIAL PRIMARY KEY,
    document_id INTEGER REFERENCES bid_documents(document_id),
    bid_notice_no VARCHAR(100),
    file_name TEXT,
    file_path TEXT,
    file_size BIGINT,
    file_extension VARCHAR(10),
    attachment_type VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 🔍 인덱스 생성 (검색 최적화)

-- 기본 인덱스
CREATE INDEX idx_bid_announcements_notice_no ON bid_announcements(bid_notice_no);
CREATE INDEX idx_bid_documents_notice_no ON bid_documents(bid_notice_no);
CREATE INDEX idx_extracted_info_notice_no ON bid_extracted_info(bid_notice_no);
CREATE INDEX idx_schedule_notice_no ON bid_schedule(bid_notice_no);

-- 💰 금액 검색 인덱스
CREATE INDEX idx_announcements_estimated_price ON bid_announcements(estimated_price) WHERE estimated_price IS NOT NULL;
CREATE INDEX idx_announcements_price_range ON bid_announcements(min_price, max_price) WHERE min_price IS NOT NULL OR max_price IS NOT NULL;

-- 📅 날짜 검색 인덱스
CREATE INDEX idx_announcements_announcement_date ON bid_announcements(announcement_date) WHERE announcement_date IS NOT NULL;
CREATE INDEX idx_announcements_submission_end ON bid_announcements(submission_end_date) WHERE submission_end_date IS NOT NULL;
CREATE INDEX idx_announcements_opening_date ON bid_announcements(opening_date) WHERE opening_date IS NOT NULL;

-- 🏢 자격 및 조건 검색 인덱스
CREATE INDEX idx_announcements_industry_type ON bid_announcements(industry_type) WHERE industry_type IS NOT NULL;
CREATE INDEX idx_announcements_region ON bid_announcements(region_restriction) WHERE region_restriction IS NOT NULL;

-- 📊 처리 상태 인덱스
CREATE INDEX idx_announcements_parsing_status ON bid_announcements(parsing_status);
CREATE INDEX idx_documents_parsing_status ON bid_documents(parsing_status);

-- 🔍 복합 인덱스 (자주 사용되는 조합)
CREATE INDEX idx_announcements_active_bids ON bid_announcements(submission_end_date, parsing_status)
    WHERE submission_end_date > CURRENT_TIMESTAMP;

CREATE INDEX idx_announcements_search_combo ON bid_announcements(industry_type, region_restriction, estimated_price)
    WHERE industry_type IS NOT NULL;

-- 📊 추출 정보 인덱스
CREATE INDEX idx_extracted_info_category ON bid_extracted_info(info_category, field_name);
CREATE INDEX idx_extracted_info_confidence ON bid_extracted_info(confidence_score) WHERE confidence_score > 0.7;

-- 📅 일정 인덱스
CREATE INDEX idx_schedule_event_type ON bid_schedule(event_type, event_date);
CREATE INDEX idx_schedule_upcoming ON bid_schedule(event_date) WHERE event_date > CURRENT_TIMESTAMP;

-- 🔧 트리거 생성 (자동 업데이트)

-- updated_at 자동 갱신 함수
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- updated_at 트리거 적용
CREATE TRIGGER update_bid_announcements_updated_at BEFORE UPDATE ON bid_announcements FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_bid_schedule_updated_at BEFORE UPDATE ON bid_schedule FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- 📊 데이터 완성도 계산 함수
CREATE OR REPLACE FUNCTION calculate_data_completeness(notice_no VARCHAR)
RETURNS FLOAT AS $$
DECLARE
    total_fields INTEGER := 10;  -- 중요 필드 총 개수
    filled_fields INTEGER := 0;
    announcement_record RECORD;
BEGIN
    SELECT * INTO announcement_record FROM bid_announcements WHERE bid_notice_no = notice_no;

    IF announcement_record.estimated_price IS NOT NULL THEN filled_fields := filled_fields + 1; END IF;
    IF announcement_record.submission_end_date IS NOT NULL THEN filled_fields := filled_fields + 1; END IF;
    IF announcement_record.opening_date IS NOT NULL THEN filled_fields := filled_fields + 1; END IF;
    IF announcement_record.industry_type IS NOT NULL THEN filled_fields := filled_fields + 1; END IF;
    IF announcement_record.region_restriction IS NOT NULL THEN filled_fields := filled_fields + 1; END IF;
    IF announcement_record.contract_method IS NOT NULL THEN filled_fields := filled_fields + 1; END IF;
    IF announcement_record.qualification_requirements IS NOT NULL THEN filled_fields := filled_fields + 1; END IF;
    IF announcement_record.joint_venture_allowed IS NOT NULL THEN filled_fields := filled_fields + 1; END IF;
    IF announcement_record.tax_exemption_applicable IS NOT NULL THEN filled_fields := filled_fields + 1; END IF;
    IF announcement_record.announcement_date IS NOT NULL THEN filled_fields := filled_fields + 1; END IF;

    RETURN filled_fields::FLOAT / total_fields::FLOAT;
END;
$$ LANGUAGE plpgsql;

-- 💡 편의 뷰 생성

-- 활성 입찰 뷰
CREATE VIEW active_bids AS
SELECT
    bid_notice_no,
    title,
    organization_name,
    estimated_price,
    submission_end_date,
    opening_date,
    industry_type,
    region_restriction,
    data_completeness_score
FROM bid_announcements
WHERE submission_end_date > CURRENT_TIMESTAMP
    AND parsing_status = 'completed'
ORDER BY submission_end_date ASC;

-- 데이터 품질 요약 뷰
CREATE VIEW data_quality_summary AS
SELECT
    COUNT(*) as total_bids,
    COUNT(*) FILTER (WHERE parsing_status = 'completed') as parsed_bids,
    COUNT(*) FILTER (WHERE estimated_price IS NOT NULL) as bids_with_price,
    COUNT(*) FILTER (WHERE submission_end_date IS NOT NULL) as bids_with_deadline,
    COUNT(*) FILTER (WHERE industry_type IS NOT NULL) as bids_with_industry,
    AVG(data_completeness_score) as avg_completeness,
    AVG(extraction_confidence) as avg_confidence
FROM bid_announcements;

-- 📝 코멘트 추가
COMMENT ON TABLE bid_announcements IS '입찰 공고 기본 정보 + 표에서 추출한 구조화된 데이터';
COMMENT ON TABLE bid_extracted_info IS '표 파싱으로 추출한 상세 정보 저장소';
COMMENT ON TABLE bid_schedule IS '입찰 관련 모든 일정 정보';

COMMENT ON COLUMN bid_announcements.estimated_price IS '표에서 추출한 추정가격 (원)';
COMMENT ON COLUMN bid_announcements.data_completeness_score IS '데이터 완성도 점수 (0.0-1.0)';
COMMENT ON COLUMN bid_announcements.extraction_confidence IS '표 파싱 신뢰도 (0.0-1.0)';

-- 스키마 생성 완료 로그
INSERT INTO bid_extracted_info (bid_notice_no, info_category, field_name, field_value, extraction_method)
VALUES ('SYSTEM', 'metadata', 'schema_version', '2.0_enhanced', 'manual')
ON CONFLICT DO NOTHING;