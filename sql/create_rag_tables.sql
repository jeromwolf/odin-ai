-- =============================================================================
-- RAG (Retrieval-Augmented Generation) 시스템을 위한 PostgreSQL 스키마
-- pgvector를 사용한 벡터 유사도 검색 + 전문 검색(FTS) 하이브리드 구조
-- =============================================================================

BEGIN;

-- =============================================================================
-- 확장 모듈 설치
-- =============================================================================

-- pgvector: 벡터 임베딩 저장 및 유사도 검색
CREATE EXTENSION IF NOT EXISTS vector;

-- pg_trgm: 트라이그램 기반 ILIKE 폴백 검색
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- =============================================================================
-- rfp_chunks 테이블: RFP 문서의 청크 단위 저장
-- 각 입찰공고 문서를 작은 청크로 분할하여 임베딩과 함께 저장
-- =============================================================================

CREATE TABLE IF NOT EXISTS rfp_chunks (
    chunk_id        BIGSERIAL PRIMARY KEY,
    bid_notice_no   VARCHAR(100) NOT NULL,                         -- 입찰공고번호 (FK)
    document_id     INTEGER,                                       -- bid_documents.id 참조 (optional)
    chunk_index     INTEGER NOT NULL,                              -- 문서 내 청크 순서 (0-based)
    chunk_text      TEXT NOT NULL,                                 -- 청크 원문 텍스트
    chunk_text_tsv  TSVECTOR GENERATED ALWAYS AS                  -- 전문 검색용 tsvector (자동 생성)
                        (to_tsvector('simple', chunk_text)) STORED,
    embedding       vector(1024),                                  -- KURE-v1 차원 (1024)
    embedding_model VARCHAR(50) DEFAULT 'KURE-v1',               -- 사용된 임베딩 모델명
    section_type    VARCHAR(50),                                   -- 섹션 유형: '자격요건', '예정가격', '제출서류' 등
    page_number     INTEGER,                                       -- 원본 문서의 페이지 번호
    token_count     INTEGER,                                       -- 청크의 토큰 수
    created_at      TIMESTAMPTZ DEFAULT NOW(),                     -- 생성 시각

    -- 입찰공고 삭제 시 관련 청크도 함께 삭제 (CASCADE)
    CONSTRAINT fk_rfp_chunks_bid FOREIGN KEY (bid_notice_no)
        REFERENCES bid_announcements(bid_notice_no) ON DELETE CASCADE
);

COMMENT ON TABLE rfp_chunks IS 'RFP 문서를 청크 단위로 분할하여 벡터 임베딩과 함께 저장하는 RAG 핵심 테이블';
COMMENT ON COLUMN rfp_chunks.chunk_index    IS '문서 내 청크 순서 (0부터 시작)';
COMMENT ON COLUMN rfp_chunks.chunk_text_tsv IS 'simple 딕셔너리 기반 전문 검색용 tsvector (자동 생성 컬럼)';
COMMENT ON COLUMN rfp_chunks.embedding      IS 'KURE-v1 모델 기준 1024차원 벡터';
COMMENT ON COLUMN rfp_chunks.section_type   IS '청크가 속한 문서 섹션 유형 (자격요건, 예정가격, 제출서류 등)';

-- =============================================================================
-- rfp_chunks 인덱스
-- =============================================================================

-- HNSW 벡터 인덱스: 코사인 거리 기반 유사도 검색 (ANN, 근사 최근접 이웃)
-- m=16: 각 노드의 최대 연결 수 (메모리 vs 정확도 트레이드오프)
-- ef_construction=128: 인덱스 빌드 시 탐색 범위 (높을수록 정확하지만 느림)
CREATE INDEX IF NOT EXISTS idx_rfp_chunks_embedding_hnsw
    ON rfp_chunks USING hnsw (embedding vector_cosine_ops)
    WITH (m = 16, ef_construction = 128);

-- GIN 인덱스: tsvector 기반 전문 검색 (to_tsquery, plainto_tsquery)
CREATE INDEX IF NOT EXISTS idx_rfp_chunks_tsv_gin
    ON rfp_chunks USING GIN (chunk_text_tsv);

-- GIN 트라이그램 인덱스: ILIKE '%키워드%' 폴백 검색용
CREATE INDEX IF NOT EXISTS idx_rfp_chunks_trgm
    ON rfp_chunks USING GIN (chunk_text gin_trgm_ops);

-- B-tree 인덱스: bid_notice_no 단독 필터링 (특정 공고의 청크 조회)
CREATE INDEX IF NOT EXISTS idx_rfp_chunks_bid_notice_no
    ON rfp_chunks(bid_notice_no);

-- B-tree 인덱스: section_type 필터링 (특정 섹션 유형만 검색)
CREATE INDEX IF NOT EXISTS idx_rfp_chunks_section_type
    ON rfp_chunks(section_type);

-- 복합 B-tree 인덱스: 공고번호 + 청크 순서 (문서 재조합 시 사용)
CREATE INDEX IF NOT EXISTS idx_rfp_chunks_bid_chunk
    ON rfp_chunks(bid_notice_no, chunk_index);

-- =============================================================================
-- bid_announcements 테이블에 임베딩 상태 컬럼 추가
-- 어떤 공고가 이미 임베딩 처리되었는지 빠르게 확인하기 위한 플래그
-- =============================================================================

ALTER TABLE bid_announcements
    ADD COLUMN IF NOT EXISTS has_embedding BOOLEAN DEFAULT FALSE;

COMMENT ON COLUMN bid_announcements.has_embedding IS '해당 공고의 RFP 문서가 벡터 임베딩 처리 완료되었는지 여부';

-- has_embedding 필터링 인덱스: 미처리 공고 배치 선택 시 활용
CREATE INDEX IF NOT EXISTS idx_bid_has_embedding
    ON bid_announcements(has_embedding);

-- =============================================================================
-- fn_hybrid_search 함수: RRF(Reciprocal Rank Fusion) 기반 하이브리드 검색
--
-- 벡터 검색(코사인 유사도)과 전문 검색(FTS)의 결과를 RRF 알고리즘으로 융합.
-- RRF 점수 = SUM(1.0 / (rrf_k + rank)) — 두 검색 방식에서 모두 상위에 오를수록 높은 점수.
-- =============================================================================

CREATE OR REPLACE FUNCTION fn_hybrid_search(
    query_embedding     vector(1024),           -- 검색 쿼리의 벡터 임베딩
    query_text          TEXT,                   -- 검색 쿼리 원문 (FTS용)
    match_count         INT     DEFAULT 10,     -- 최종 반환할 결과 수
    candidate_count     INT     DEFAULT 40,     -- 각 검색 방식에서 수집할 후보 수
    rrf_k               INT     DEFAULT 60,     -- RRF 파라미터 k (낮을수록 상위 랭크에 민감)
    filter_bid_notice_no VARCHAR DEFAULT NULL,  -- 특정 공고로 검색 범위 제한 (NULL=전체)
    filter_section_type  VARCHAR DEFAULT NULL   -- 특정 섹션 유형으로 검색 범위 제한 (NULL=전체)
)
RETURNS TABLE (
    chunk_id     BIGINT,
    chunk_text   TEXT,
    bid_notice_no VARCHAR,
    section_type  VARCHAR,
    chunk_index   INTEGER,
    rrf_score     DOUBLE PRECISION,
    match_sources TEXT[]                        -- 해당 청크가 포함된 검색 방식 목록 ['vector', 'fts']
)
LANGUAGE SQL
STABLE
AS $$
    -- CTE 1: vector_results — 코사인 유사도 기반 벡터 검색 결과
    -- embedding <=> query_embedding: pgvector 코사인 거리 연산자 (낮을수록 유사)
    WITH vector_results AS (
        SELECT
            c.chunk_id,
            ROW_NUMBER() OVER (ORDER BY c.embedding <=> query_embedding) AS rank
        FROM rfp_chunks c
        WHERE
            c.embedding IS NOT NULL
            AND (filter_bid_notice_no IS NULL OR c.bid_notice_no = filter_bid_notice_no)
            AND (filter_section_type  IS NULL OR c.section_type  = filter_section_type)
        ORDER BY c.embedding <=> query_embedding
        LIMIT candidate_count
    ),

    -- CTE 2: fts_results — plainto_tsquery 기반 전문 검색 결과
    -- ts_rank_cd: 문서 밀도(커버리지) 고려 랭킹 함수
    fts_results AS (
        SELECT
            c.chunk_id,
            ROW_NUMBER() OVER (
                ORDER BY ts_rank_cd(c.chunk_text_tsv, plainto_tsquery('simple', query_text)) DESC
            ) AS rank
        FROM rfp_chunks c
        WHERE
            c.chunk_text_tsv @@ plainto_tsquery('simple', query_text)
            AND (filter_bid_notice_no IS NULL OR c.bid_notice_no = filter_bid_notice_no)
            AND (filter_section_type  IS NULL OR c.section_type  = filter_section_type)
        ORDER BY ts_rank_cd(c.chunk_text_tsv, plainto_tsquery('simple', query_text)) DESC
        LIMIT candidate_count
    ),

    -- CTE 3: combined — 두 검색 결과를 RRF 점수와 출처 정보와 함께 합산
    combined AS (
        SELECT chunk_id, 1.0 / (rrf_k + rank) AS rrf_score, 'vector' AS source
        FROM vector_results

        UNION ALL

        SELECT chunk_id, 1.0 / (rrf_k + rank) AS rrf_score, 'fts' AS source
        FROM fts_results
    ),

    -- CTE 4: fused — chunk_id별로 RRF 점수 합산 및 출처 배열 집계
    fused AS (
        SELECT
            chunk_id,
            SUM(rrf_score)         AS total_rrf_score,
            ARRAY_AGG(DISTINCT source ORDER BY source) AS sources
        FROM combined
        GROUP BY chunk_id
    )

    -- 최종 결과: fused 결과를 rfp_chunks와 JOIN하여 상세 정보 반환
    SELECT
        rc.chunk_id,
        rc.chunk_text,
        rc.bid_notice_no,
        rc.section_type,
        rc.chunk_index,
        f.total_rrf_score  AS rrf_score,
        f.sources          AS match_sources
    FROM fused f
    JOIN rfp_chunks rc ON rc.chunk_id = f.chunk_id
    ORDER BY f.total_rrf_score DESC
    LIMIT match_count;
$$;

COMMENT ON FUNCTION fn_hybrid_search IS
    'RRF(Reciprocal Rank Fusion) 알고리즘으로 벡터 검색(코사인 유사도)과 '
    '전문 검색(FTS)을 융합하는 하이브리드 검색 함수. '
    'filter_bid_notice_no로 특정 공고 내 검색, filter_section_type으로 섹션 필터링 가능.';

-- =============================================================================
-- 완료
-- =============================================================================

COMMIT;
