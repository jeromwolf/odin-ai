-- PostgreSQL 초기화 스크립트
-- 데이터베이스 및 사용자 설정

-- 데이터베이스 기본 설정
ALTER DATABASE odin_ai SET timezone TO 'Asia/Seoul';

-- 확장 기능 설치
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";  -- 텍스트 검색 성능 향상
CREATE EXTENSION IF NOT EXISTS "btree_gin";  -- 복합 인덱스 성능 향상
CREATE EXTENSION IF NOT EXISTS "unaccent";  -- 검색 정규화

-- 전문 검색을 위한 설정
CREATE TEXT SEARCH CONFIGURATION korean (COPY = simple);

-- 인덱스 성능 튜닝 (pg_stat_statements 제거)
ALTER SYSTEM SET track_activity_query_size = 2048;

-- 로그 설정
ALTER SYSTEM SET log_statement = 'ddl';
ALTER SYSTEM SET log_min_duration_statement = 1000;  -- 1초 이상 쿼리 로깅

-- 메모리 설정 (Docker 환경 기준 최적화)
ALTER SYSTEM SET shared_buffers = '256MB';
ALTER SYSTEM SET effective_cache_size = '1GB';
ALTER SYSTEM SET work_mem = '16MB';
ALTER SYSTEM SET maintenance_work_mem = '64MB';

-- 테이블스페이스 설정
-- CREATE TABLESPACE documents_space LOCATION '/var/lib/postgresql/data/documents';

COMMENT ON DATABASE odin_ai IS 'Odin-AI 공공조달 플랫폼 데이터베이스';