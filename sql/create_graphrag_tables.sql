-- ============================================================
-- GraphRAG Tables
-- 엔티티 추출 + 커뮤니티 감지 결과 저장
-- ============================================================

-- GraphRAG 엔티티 테이블
CREATE TABLE IF NOT EXISTS graphrag_entities (
    id SERIAL PRIMARY KEY,
    entity_id VARCHAR(100) UNIQUE NOT NULL,
    entity_type VARCHAR(50) NOT NULL,
    entity_name TEXT NOT NULL,
    description TEXT,
    community_id INTEGER,
    embedding vector(1024),
    source_bid_notice_no VARCHAR(100),
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- GraphRAG 커뮤니티 테이블
CREATE TABLE IF NOT EXISTS graphrag_communities (
    id SERIAL PRIMARY KEY,
    community_id INTEGER UNIQUE NOT NULL,
    title TEXT,
    summary TEXT,
    level INTEGER DEFAULT 0,
    findings JSONB DEFAULT '[]',
    entity_count INTEGER DEFAULT 0,
    bid_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- 인덱스
CREATE INDEX IF NOT EXISTS idx_graphrag_entities_type ON graphrag_entities(entity_type);
CREATE INDEX IF NOT EXISTS idx_graphrag_entities_community ON graphrag_entities(community_id);
CREATE INDEX IF NOT EXISTS idx_graphrag_entities_source ON graphrag_entities(source_bid_notice_no);
CREATE INDEX IF NOT EXISTS idx_graphrag_communities_level ON graphrag_communities(level);

-- HNSW 벡터 인덱스 (엔티티 임베딩 검색)
CREATE INDEX IF NOT EXISTS idx_graphrag_entities_embedding
    ON graphrag_entities USING hnsw (embedding vector_cosine_ops)
    WITH (m = 16, ef_construction = 64);
