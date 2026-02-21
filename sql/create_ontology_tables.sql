-- ============================================
-- 온톨로지 시스템 테이블
-- ODIN-AI 공공입찰 도메인 지식 구조
-- ============================================
-- 생성일: 2026-02-21
-- 설명: 공공입찰 도메인 개념의 계층 구조 및 관계를 저장하는 온톨로지 스키마
--        Phase 3 (v3.0) 구현 대상 - 선행 조건: Phase 2 완료 및 3,000개 이상 입찰공고 데이터
-- ============================================


-- ============================================
-- 1. 온톨로지 개념 계층 테이블
-- 공공입찰 도메인의 개념(공사, 용역, 물품 등)과 계층 관계를 저장
-- level: 0=root(최상위), 1=대분류, 2=중분류, 3=소분류
-- ============================================
CREATE TABLE IF NOT EXISTS ontology_concepts (
    id SERIAL PRIMARY KEY,
    concept_name VARCHAR(100) NOT NULL,        -- 한국어 개념명 (e.g., "도로공사")
    concept_name_en VARCHAR(100),              -- 영문 개념명 (e.g., "road_construction")
    parent_id INTEGER REFERENCES ontology_concepts(id) ON DELETE SET NULL,
    level INTEGER DEFAULT 0,                    -- 0=root, 1=대분류, 2=중분류, 3=소분류
    description TEXT,                           -- 개념 설명
    keywords TEXT[] DEFAULT '{}',              -- 매칭용 키워드 배열
    synonyms TEXT[] DEFAULT '{}',              -- 동의어/유사어 배열
    is_active BOOLEAN DEFAULT true,
    display_order INTEGER DEFAULT 0,            -- 표시 순서
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- ontology_concepts 인덱스
CREATE INDEX IF NOT EXISTS idx_ontology_concepts_parent_id
    ON ontology_concepts(parent_id);

CREATE INDEX IF NOT EXISTS idx_ontology_concepts_concept_name
    ON ontology_concepts(concept_name);

CREATE INDEX IF NOT EXISTS idx_ontology_concepts_level
    ON ontology_concepts(level);

-- GIN 인덱스: 키워드 배열 검색 최적화
CREATE INDEX IF NOT EXISTS idx_ontology_concepts_keywords
    ON ontology_concepts USING GIN(keywords);

-- GIN 인덱스: 동의어 배열 검색 최적화
CREATE INDEX IF NOT EXISTS idx_ontology_concepts_synonyms
    ON ontology_concepts USING GIN(synonyms);


-- ============================================
-- 2. 개념 간 관계 테이블 (부모-자식 외 추가 관계)
-- 온톨로지 개념들 사이의 비계층적 관계를 정의
-- relation_type:
--   'relatedTo' - 관련 있음
--   'requires'  - 전제 조건 관계 (A는 B를 필요로 함)
--   'similarTo' - 유사한 개념
--   'excludes'  - 상호 배타적 관계
-- ============================================
CREATE TABLE IF NOT EXISTS ontology_relations (
    id SERIAL PRIMARY KEY,
    source_concept_id INTEGER NOT NULL REFERENCES ontology_concepts(id) ON DELETE CASCADE,
    target_concept_id INTEGER NOT NULL REFERENCES ontology_concepts(id) ON DELETE CASCADE,
    relation_type VARCHAR(50) NOT NULL,        -- 'relatedTo', 'requires', 'similarTo', 'excludes'
    weight FLOAT DEFAULT 1.0,                   -- 관계 강도 (0.0-1.0)
    description TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(source_concept_id, target_concept_id, relation_type)
);

-- ontology_relations 인덱스
CREATE INDEX IF NOT EXISTS idx_ontology_relations_source_concept_id
    ON ontology_relations(source_concept_id);

CREATE INDEX IF NOT EXISTS idx_ontology_relations_target_concept_id
    ON ontology_relations(target_concept_id);

CREATE INDEX IF NOT EXISTS idx_ontology_relations_relation_type
    ON ontology_relations(relation_type);


-- ============================================
-- 3. 입찰공고-온톨로지 매핑 테이블
-- 입찰공고와 온톨로지 개념 사이의 자동/수동 매핑을 저장
-- source:
--   'auto'   - 키워드 기반 자동 분류
--   'manual' - 관리자 수동 분류
--   'ai'     - GPT-4 기반 AI 분류 (Phase 3 이후)
-- confidence: 매칭 신뢰도 0.0(낮음) ~ 1.0(높음), 0.8 이상만 활용 권장
-- ============================================
CREATE TABLE IF NOT EXISTS bid_ontology_mappings (
    id SERIAL PRIMARY KEY,
    bid_notice_no VARCHAR(100) NOT NULL,       -- FK to bid_announcements (bid_notice_no)
    concept_id INTEGER NOT NULL REFERENCES ontology_concepts(id) ON DELETE CASCADE,
    confidence FLOAT DEFAULT 0.0,               -- 매칭 신뢰도 (0.0-1.0)
    source VARCHAR(50) DEFAULT 'auto',          -- 'auto', 'manual', 'ai'
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(bid_notice_no, concept_id)
);

-- bid_ontology_mappings 인덱스
CREATE INDEX IF NOT EXISTS idx_bid_ontology_mappings_bid_notice_no
    ON bid_ontology_mappings(bid_notice_no);

CREATE INDEX IF NOT EXISTS idx_bid_ontology_mappings_concept_id
    ON bid_ontology_mappings(concept_id);

CREATE INDEX IF NOT EXISTS idx_bid_ontology_mappings_confidence
    ON bid_ontology_mappings(confidence);


-- ============================================
-- 헬퍼 함수
-- ============================================

-- 재귀적으로 모든 하위 개념 ID를 반환하는 함수
-- 사용 예시: SELECT * FROM fn_get_descendant_concepts(1);
--            → root(1)의 모든 하위 개념(자식, 손자 등)을 계층 경로와 함께 반환
CREATE OR REPLACE FUNCTION fn_get_descendant_concepts(root_id INTEGER)
RETURNS TABLE(concept_id INTEGER, concept_name VARCHAR, level INTEGER, path TEXT) AS $$
WITH RECURSIVE concept_tree AS (
    -- 기준 개념(root) 선택
    SELECT id, concept_name, level, concept_name::TEXT as path
    FROM ontology_concepts
    WHERE id = root_id AND is_active = true

    UNION ALL

    -- 재귀적으로 하위 개념 탐색
    SELECT oc.id, oc.concept_name, oc.level, ct.path || ' > ' || oc.concept_name
    FROM ontology_concepts oc
    JOIN concept_tree ct ON oc.parent_id = ct.id
    WHERE oc.is_active = true
)
SELECT id, concept_name, level, path FROM concept_tree;
$$ LANGUAGE SQL STABLE;


-- 개념의 모든 키워드 (자기 + 하위 개념)를 반환하는 함수
-- 검색 확장에 활용: "도로" 검색 시 교량, 터널 등 하위 개념 키워드 자동 포함
-- 사용 예시: SELECT fn_get_expanded_keywords(1);
--            → 개념(1)과 그 하위 모든 개념의 키워드 + 동의어 배열 반환
CREATE OR REPLACE FUNCTION fn_get_expanded_keywords(root_id INTEGER)
RETURNS TEXT[] AS $$
SELECT ARRAY(
    SELECT DISTINCT unnest(oc.keywords || oc.synonyms)
    FROM ontology_concepts oc
    WHERE oc.id IN (
        SELECT concept_id FROM fn_get_descendant_concepts(root_id)
    )
    AND oc.is_active = true
);
$$ LANGUAGE SQL STABLE;
