-- ============================================================
-- Neo4j Sync Log Table
-- PostgreSQL에서 Neo4j 동기화 이력을 추적하기 위한 테이블
-- ============================================================

CREATE TABLE IF NOT EXISTS neo4j_sync_log (
    id SERIAL PRIMARY KEY,
    sync_type VARCHAR(20) NOT NULL,  -- 'full' or 'incremental'
    started_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP,
    status VARCHAR(20) DEFAULT 'running',  -- running, completed, failed
    nodes_synced INTEGER DEFAULT 0,
    relationships_synced INTEGER DEFAULT 0,
    error_message TEXT,
    details JSONB
);

-- 인덱스: 최근 동기화 이력 조회 최적화
CREATE INDEX IF NOT EXISTS idx_neo4j_sync_log_status
    ON neo4j_sync_log(status);

CREATE INDEX IF NOT EXISTS idx_neo4j_sync_log_started_at
    ON neo4j_sync_log(started_at DESC);
