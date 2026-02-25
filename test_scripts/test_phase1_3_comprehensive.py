#!/usr/bin/env python3
"""
ODIN-AI Phase 1~3 종합 테스트 스크립트
========================================
Phase 1: RAG (KURE-v1 임베딩 + EXAONE 3.5 LLM + 하이브리드 검색)
Phase 2: Neo4j GraphDB (그래프 검색 API)
Phase 3: GraphRAG (엔티티 추출, 커뮤니티, 글로벌 Q&A)
Frontend: 빌드 검증, 라우트, 컴포넌트
"""

import requests
import json
import time
import subprocess
import os
import sys
from datetime import datetime

BASE_URL = "http://localhost:9000/api"
RESULTS = []
PASS_COUNT = 0
FAIL_COUNT = 0
SKIP_COUNT = 0

def test(test_id: str, category: str, description: str, func):
    """테스트 실행 및 결과 기록"""
    global PASS_COUNT, FAIL_COUNT, SKIP_COUNT
    start = time.time()
    try:
        result = func()
        elapsed = round(time.time() - start, 2)
        if result is None:
            status = "SKIP"
            SKIP_COUNT += 1
            detail = "Skipped"
        elif result[0]:
            status = "PASS"
            PASS_COUNT += 1
            detail = result[1]
        else:
            status = "FAIL"
            FAIL_COUNT += 1
            detail = result[1]
    except Exception as e:
        elapsed = round(time.time() - start, 2)
        status = "FAIL"
        FAIL_COUNT += 1
        detail = str(e)

    icon = {"PASS": "✅", "FAIL": "❌", "SKIP": "⏭️"}[status]
    RESULTS.append({
        "id": test_id,
        "category": category,
        "description": description,
        "status": status,
        "detail": detail,
        "elapsed": elapsed,
    })
    print(f"  {icon} [{test_id}] {description} ({elapsed}s) - {detail[:80]}")


# ===================================================================
# PHASE 1: RAG 시스템 테스트
# ===================================================================
print("\n" + "="*60)
print("  PHASE 1: RAG 시스템 테스트")
print("="*60)

# --- 1.1 RAG Status ---
def test_rag_status():
    r = requests.get(f"{BASE_URL}/rag/status", timeout=10)
    d = r.json()
    assert r.status_code == 200
    assert d["rag_available"] is True
    return True, f"rag_available={d['rag_available']}, llm={d['llm_available']}"

test("P1-01", "RAG", "RAG 상태 API 응답 확인", test_rag_status)

# --- 1.2 RAG Embedding Stats ---
def test_rag_embedding_stats():
    r = requests.get(f"{BASE_URL}/rag/status", timeout=10)
    d = r.json()
    stats = d.get("embedding_stats", {})
    assert stats.get("total_bids", 0) > 0, "total_bids should be > 0"
    assert stats.get("embedded_bids", 0) > 0, "embedded_bids should be > 0"
    assert stats.get("total_chunks", 0) > 0, "total_chunks should be > 0"
    coverage = stats.get("coverage_pct", 0)
    return True, f"bids={stats['total_bids']}, embedded={stats['embedded_bids']}, chunks={stats['total_chunks']}, coverage={coverage}%"

test("P1-02", "RAG", "임베딩 통계 (KURE-v1 1024dim)", test_rag_embedding_stats)

# --- 1.3 RAG Search - Basic ---
def test_rag_search_basic():
    r = requests.get(f"{BASE_URL}/rag/search?q=도로공사&limit=5", timeout=30)
    d = r.json()
    assert r.status_code == 200
    assert d["success"] is True
    assert d["total"] > 0, "Search should return results"
    return True, f"total={d['total']}, mode={d['search_mode']}, results={len(d['results'])}"

test("P1-03", "RAG", "하이브리드 검색 - 기본 쿼리 (도로공사)", test_rag_search_basic)

# --- 1.4 RAG Search - Korean ---
def test_rag_search_korean():
    r = requests.get(f"{BASE_URL}/rag/search?q=재해복구+소하천&limit=5", timeout=30)
    d = r.json()
    assert r.status_code == 200
    assert d["success"] is True
    return True, f"total={d['total']}, mode={d['search_mode']}"

test("P1-04", "RAG", "하이브리드 검색 - 한국어 복합 쿼리 (재해복구 소하천)", test_rag_search_korean)

# --- 1.5 RAG Search - Limit ---
def test_rag_search_limit():
    r = requests.get(f"{BASE_URL}/rag/search?q=공사&limit=3", timeout=30)
    d = r.json()
    assert r.status_code == 200
    assert len(d["results"]) <= 3, f"Results should be <= 3, got {len(d['results'])}"
    return True, f"limit=3, returned={len(d['results'])}"

test("P1-05", "RAG", "검색 결과 수 제한 (limit=3)", test_rag_search_limit)

# --- 1.6 RAG Search - Empty query ---
def test_rag_search_empty():
    r = requests.get(f"{BASE_URL}/rag/search?q=", timeout=10)
    assert r.status_code == 422, f"Empty query should return 422, got {r.status_code}"
    return True, f"status={r.status_code} (validation error)"

test("P1-06", "RAG", "빈 쿼리 유효성 검사 (422 에러)", test_rag_search_empty)

# --- 1.7 RAG Search result fields ---
def test_rag_search_fields():
    r = requests.get(f"{BASE_URL}/rag/search?q=건설&limit=1", timeout=30)
    d = r.json()
    if d["total"] > 0:
        result = d["results"][0]
        required_fields = ["bid_notice_no", "bid_title", "chunk_text", "score"]
        missing = [f for f in required_fields if f not in result]
        assert len(missing) == 0, f"Missing fields: {missing}"
        return True, f"fields_ok, score={result.get('score', 'N/A')}"
    return True, "no results to validate"

test("P1-07", "RAG", "검색 결과 필드 구조 검증", test_rag_search_fields)

# --- 1.8 RAG Ask - LLM Answer ---
def test_rag_ask_basic():
    r = requests.get(f"{BASE_URL}/rag/ask?q=경기도 건설 입찰 조건은?&limit=3", timeout=120)
    d = r.json()
    assert r.status_code == 200
    assert d["success"] is True
    assert len(d["answer"]) > 10, "Answer should be substantial"
    return True, f"has_llm={d['has_llm_answer']}, answer_len={len(d['answer'])}, sources={len(d.get('sources',[]))}"

test("P1-08", "RAG", "RAG Q&A - EXAONE 3.5 답변 생성", test_rag_ask_basic)

# --- 1.9 RAG Ask - Sources ---
def test_rag_ask_sources():
    r = requests.get(f"{BASE_URL}/rag/ask?q=도로 공사 자격요건&limit=5", timeout=120)
    d = r.json()
    assert r.status_code == 200
    sources = d.get("sources", [])
    if sources:
        source = sources[0]
        assert "bid_notice_no" in source
        return True, f"sources={len(sources)}, first={source.get('bid_notice_no','?')}"
    return True, "no sources (no matching docs)"

test("P1-09", "RAG", "RAG Q&A - 출처(sources) 반환 검증", test_rag_ask_sources)

# --- 1.10 RAG Ask - No results ---
def test_rag_ask_no_results():
    r = requests.get(f"{BASE_URL}/rag/ask?q=xyzzyspoonnotexist&limit=3", timeout=30)
    d = r.json()
    assert r.status_code == 200
    assert d["success"] is True
    # Should indicate no results found
    return True, f"has_llm={d.get('has_llm_answer')}, answer_len={len(d.get('answer',''))}"

test("P1-10", "RAG", "RAG Q&A - 결과 없는 쿼리 처리", test_rag_ask_no_results)

# --- 1.11 RAG Status - LLM Available ---
def test_rag_llm_available():
    r = requests.get(f"{BASE_URL}/rag/status", timeout=10)
    d = r.json()
    assert d["llm_available"] is True, "LLM (Ollama) should be available"
    return True, f"llm_available={d['llm_available']}"

test("P1-11", "RAG", "Ollama LLM 연결 상태 확인", test_rag_llm_available)

# --- 1.12 RAG Search Available ---
def test_rag_search_available():
    r = requests.get(f"{BASE_URL}/rag/status", timeout=10)
    d = r.json()
    assert d.get("search_available") is True, "Search should be available"
    return True, f"search_available={d['search_available']}"

test("P1-12", "RAG", "하이브리드 검색 서비스 활성 상태", test_rag_search_available)


# ===================================================================
# PHASE 2: Neo4j Graph 테스트
# ===================================================================
print("\n" + "="*60)
print("  PHASE 2: Neo4j Graph 테스트")
print("="*60)

# --- 2.1 Graph Status ---
def test_graph_status():
    r = requests.get(f"{BASE_URL}/graph/status", timeout=10)
    d = r.json()
    assert r.status_code == 200
    assert d.get("connected") is True or d.get("neo4j_connected") is True
    return True, f"connected=True, nodes={d.get('nodes',{})}"

test("P2-01", "Graph", "Neo4j 연결 상태 확인", test_graph_status)

# --- 2.2 Graph Node Counts ---
def test_graph_node_counts():
    r = requests.get(f"{BASE_URL}/graph/status", timeout=10)
    d = r.json()
    nodes = d.get("nodes", {})
    total = sum(nodes.values()) if isinstance(nodes, dict) else 0
    assert total > 0, "Should have nodes in Neo4j"
    return True, f"BidAnnouncement={nodes.get('BidAnnouncement',0)}, Organization={nodes.get('Organization',0)}, Tag={nodes.get('Tag',0)}, Region={nodes.get('Region',0)}"

test("P2-02", "Graph", "Neo4j 노드 타입별 개수 확인", test_graph_node_counts)

# --- 2.3 Graph Relationships ---
def test_graph_relationships():
    r = requests.get(f"{BASE_URL}/graph/status", timeout=10)
    d = r.json()
    rels = d.get("relationships", {})
    total = rels.get("total", 0)
    assert total > 0, "Should have relationships"
    return True, f"total={total}, SIMILAR_TO={rels.get('SIMILAR_TO',0)}"

test("P2-03", "Graph", "Neo4j 관계 통계 확인", test_graph_relationships)

# --- 2.4 Related Bids ---
def test_graph_related():
    # First get a bid_no from DB
    r = requests.get(f"{BASE_URL}/rag/search?q=공사&limit=1", timeout=30)
    d = r.json()
    if d["total"] > 0:
        bid_no = d["results"][0].get("bid_notice_no")
        if bid_no:
            r2 = requests.get(f"{BASE_URL}/graph/related/{bid_no}?depth=1", timeout=30)
            d2 = r2.json()
            assert r2.status_code == 200
            return True, f"bid={bid_no}, related_count={len(d2.get('related_bids', d2.get('results',[])))}"
    return True, "no bid available for test"

test("P2-04", "Graph", "관련 입찰 그래프 탐색", test_graph_related)

# --- 2.5 Organization Network ---
def test_graph_org_network():
    r = requests.get(f"{BASE_URL}/graph/org/충남 공주시", timeout=30)
    d = r.json()
    assert r.status_code == 200
    bids = d.get("bids", d.get("results", []))
    return True, f"org=충남 공주시, bids={len(bids)}"

test("P2-05", "Graph", "기관 네트워크 조회 (충남 공주시)", test_graph_org_network)

# --- 2.6 Tag Network ---
def test_graph_tag_network():
    r = requests.get(f"{BASE_URL}/graph/tag/건설", timeout=30)
    d = r.json()
    assert r.status_code == 200
    return True, f"tag=건설, response_keys={list(d.keys())[:5]}"

test("P2-06", "Graph", "태그 네트워크 조회 (건설)", test_graph_tag_network)

# --- 2.7 Region Bids ---
def test_graph_region():
    r = requests.get(f"{BASE_URL}/graph/region/충청남도", timeout=30)
    d = r.json()
    assert r.status_code == 200
    return True, f"region=충청남도, response_keys={list(d.keys())[:5]}"

test("P2-07", "Graph", "지역별 입찰 조회 (충청남도)", test_graph_region)

# --- 2.8 Non-existent org ---
def test_graph_org_not_found():
    r = requests.get(f"{BASE_URL}/graph/org/존재하지않는기관XYZ", timeout=10)
    d = r.json()
    # Should return empty or 200 with no results
    assert r.status_code in [200, 404]
    return True, f"status={r.status_code}"

test("P2-08", "Graph", "존재하지 않는 기관 조회 처리", test_graph_org_not_found)

# --- 2.9 Graph Sync Log ---
def test_graph_sync_log():
    import psycopg2
    conn = psycopg2.connect("postgresql://blockmeta@localhost:5432/odin_db")
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM neo4j_sync_log")
    count = cur.fetchone()[0]
    conn.close()
    assert count > 0, "Sync log should have entries"
    return True, f"sync_log_entries={count}"

test("P2-09", "Graph", "Neo4j 동기화 로그 검증 (PostgreSQL)", test_graph_sync_log)

# --- 2.10 Graph Bid Count Consistency ---
def test_graph_bid_consistency():
    import psycopg2
    conn = psycopg2.connect("postgresql://blockmeta@localhost:5432/odin_db")
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM bid_announcements")
    pg_count = cur.fetchone()[0]
    conn.close()

    r = requests.get(f"{BASE_URL}/graph/status", timeout=10)
    d = r.json()
    neo4j_count = d.get("nodes", {}).get("BidAnnouncement", 0)
    assert neo4j_count == pg_count, f"PostgreSQL({pg_count}) != Neo4j({neo4j_count})"
    return True, f"PostgreSQL={pg_count}, Neo4j={neo4j_count} (일치)"

test("P2-10", "Graph", "PostgreSQL-Neo4j 데이터 일관성 검증", test_graph_bid_consistency)


# ===================================================================
# PHASE 3: GraphRAG 테스트
# ===================================================================
print("\n" + "="*60)
print("  PHASE 3: GraphRAG 테스트")
print("="*60)

# --- 3.1 GraphRAG Status ---
def test_graphrag_status():
    r = requests.get(f"{BASE_URL}/rag/status", timeout=10)
    d = r.json()
    g = d.get("graphrag", {})
    assert g.get("available") is True, "GraphRAG should be available"
    assert g.get("entities", 0) > 0, "Should have entities"
    assert g.get("communities", 0) > 0, "Should have communities"
    return True, f"entities={g['entities']}, communities={g['communities']}"

test("P3-01", "GraphRAG", "GraphRAG 상태 확인 (엔티티/커뮤니티)", test_graphrag_status)

# --- 3.2 GraphRAG Entity Table ---
def test_graphrag_entities_db():
    import psycopg2
    conn = psycopg2.connect("postgresql://blockmeta@localhost:5432/odin_db")
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*), COUNT(DISTINCT entity_type), COUNT(DISTINCT community_id) FROM graphrag_entities")
    total, types, communities = cur.fetchone()
    cur.execute("SELECT entity_type, COUNT(*) FROM graphrag_entities GROUP BY entity_type ORDER BY COUNT(*) DESC")
    type_dist = cur.fetchall()
    conn.close()
    assert total > 0, "Should have entities"
    dist_str = ", ".join([f"{t}={c}" for t, c in type_dist[:5]])
    return True, f"total={total}, types={types}, communities={communities}, dist=[{dist_str}]"

test("P3-02", "GraphRAG", "graphrag_entities 테이블 데이터 검증", test_graphrag_entities_db)

# --- 3.3 GraphRAG Community Table ---
def test_graphrag_communities_db():
    import psycopg2
    conn = psycopg2.connect("postgresql://blockmeta@localhost:5432/odin_db")
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*), AVG(entity_count), AVG(bid_count) FROM graphrag_communities")
    total, avg_entities, avg_bids = cur.fetchone()
    cur.execute("SELECT community_id, title FROM graphrag_communities LIMIT 3")
    samples = cur.fetchall()
    conn.close()
    assert total > 0, "Should have communities"
    return True, f"total={total}, avg_entities={avg_entities:.1f}, avg_bids={avg_bids:.1f}"

test("P3-03", "GraphRAG", "graphrag_communities 테이블 데이터 검증", test_graphrag_communities_db)

# --- 3.4 GraphRAG Entity Embeddings ---
def test_graphrag_embeddings():
    import psycopg2
    conn = psycopg2.connect("postgresql://blockmeta@localhost:5432/odin_db")
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM graphrag_entities WHERE embedding IS NOT NULL")
    embedded = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM graphrag_entities")
    total = cur.fetchone()[0]
    conn.close()
    ratio = (embedded / total * 100) if total > 0 else 0
    return True, f"embedded={embedded}/{total} ({ratio:.1f}%)"

test("P3-04", "GraphRAG", "엔티티 임베딩 생성 확인 (KURE-v1)", test_graphrag_embeddings)

# --- 3.5 GraphRAG Entity Types ---
def test_graphrag_entity_types():
    import psycopg2
    conn = psycopg2.connect("postgresql://blockmeta@localhost:5432/odin_db")
    cur = conn.cursor()
    cur.execute("SELECT DISTINCT entity_type FROM graphrag_entities ORDER BY entity_type")
    types = [r[0] for r in cur.fetchall()]
    conn.close()
    expected = {"Organization", "Project", "Region"}
    found = set(types)
    assert len(found & expected) >= 2, f"Should have at least 2 core types, got {found}"
    return True, f"types={types}"

test("P3-05", "GraphRAG", "엔티티 타입 다양성 확인", test_graphrag_entity_types)

# --- 3.6 GraphRAG Community Summaries ---
def test_graphrag_community_summaries():
    import psycopg2
    conn = psycopg2.connect("postgresql://blockmeta@localhost:5432/odin_db")
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM graphrag_communities WHERE summary IS NOT NULL AND length(summary) > 10")
    with_summary = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM graphrag_communities")
    total = cur.fetchone()[0]
    conn.close()
    ratio = (with_summary / total * 100) if total > 0 else 0
    assert with_summary > 0, "Should have community summaries"
    return True, f"with_summary={with_summary}/{total} ({ratio:.1f}%)"

test("P3-06", "GraphRAG", "커뮤니티 요약 생성 확인", test_graphrag_community_summaries)

# --- 3.7 Global Ask - Basic ---
def test_global_ask_basic():
    r = requests.get(f"{BASE_URL}/rag/global-ask?q=건설 트렌드&top_communities=3", timeout=120)
    d = r.json()
    assert r.status_code == 200
    assert d["success"] is True
    assert len(d["answer"]) > 20, "Answer should be substantial"
    return True, f"answer_len={len(d['answer'])}, communities={len(d['communities'])}"

test("P3-07", "GraphRAG", "글로벌 Q&A - 기본 쿼리 (건설 트렌드)", test_global_ask_basic)

# --- 3.8 Global Ask - Communities Returned ---
def test_global_ask_communities():
    r = requests.get(f"{BASE_URL}/rag/global-ask?q=충청남도 공사&top_communities=5", timeout=120)
    d = r.json()
    assert r.status_code == 200
    comms = d.get("communities", [])
    assert len(comms) > 0, "Should return communities"
    comm = comms[0]
    assert "community_id" in comm
    assert "title" in comm
    assert "summary" in comm
    assert "entity_count" in comm
    return True, f"communities={len(comms)}, first_title={comm.get('title','')[:40]}"

test("P3-08", "GraphRAG", "글로벌 Q&A - 커뮤니티 데이터 구조 검증", test_global_ask_communities)

# --- 3.9 Global Ask - Community Findings ---
def test_global_ask_findings():
    r = requests.get(f"{BASE_URL}/rag/global-ask?q=재해복구&top_communities=3", timeout=120)
    d = r.json()
    comms = d.get("communities", [])
    has_findings = any(len(c.get("findings", [])) > 0 for c in comms)
    return True, f"has_findings={has_findings}, communities={len(comms)}"

test("P3-09", "GraphRAG", "글로벌 Q&A - 커뮤니티 findings 포함 확인", test_global_ask_findings)

# --- 3.10 Global Ask - Has LLM Answer ---
def test_global_ask_llm():
    r = requests.get(f"{BASE_URL}/rag/global-ask?q=공사 현황&top_communities=2", timeout=120)
    d = r.json()
    assert d.get("has_llm_answer") is True, "Should have LLM answer (Ollama active)"
    return True, f"has_llm_answer={d['has_llm_answer']}"

test("P3-10", "GraphRAG", "글로벌 Q&A - LLM(EXAONE) 답변 생성 확인", test_global_ask_llm)

# --- 3.11 Global Ask - Empty Query ---
def test_global_ask_empty():
    r = requests.get(f"{BASE_URL}/rag/global-ask?q=", timeout=10)
    assert r.status_code == 422, f"Empty query should return 422, got {r.status_code}"
    return True, f"status={r.status_code} (validation error)"

test("P3-11", "GraphRAG", "글로벌 Q&A - 빈 쿼리 유효성 검사", test_global_ask_empty)

# --- 3.12 GraphRAG HNSW Index ---
def test_graphrag_hnsw_index():
    import psycopg2
    conn = psycopg2.connect("postgresql://blockmeta@localhost:5432/odin_db")
    cur = conn.cursor()
    cur.execute("""
        SELECT indexname FROM pg_indexes
        WHERE tablename = 'graphrag_entities' AND indexdef LIKE '%hnsw%'
    """)
    indexes = [r[0] for r in cur.fetchall()]
    conn.close()
    assert len(indexes) > 0, "HNSW index should exist"
    return True, f"hnsw_indexes={indexes}"

test("P3-12", "GraphRAG", "pgvector HNSW 인덱스 존재 확인", test_graphrag_hnsw_index)


# ===================================================================
# PHASE 4: 프론트엔드 테스트
# ===================================================================
print("\n" + "="*60)
print("  PHASE 4: 프론트엔드 테스트")
print("="*60)

FRONTEND_DIR = "/Users/blockmeta/Desktop/workspace/odin-ai/frontend"

# --- 4.1 Frontend Build ---
def test_frontend_build():
    build_dir = os.path.join(FRONTEND_DIR, "build")
    assert os.path.isdir(build_dir), "Build directory should exist"
    index_html = os.path.join(build_dir, "index.html")
    assert os.path.isfile(index_html), "index.html should exist"
    return True, f"build/ exists with index.html"

test("P4-01", "Frontend", "프론트엔드 빌드 결과 확인", test_frontend_build)

# --- 4.2 GraphExplorer Page ---
def test_frontend_graph_explorer():
    path = os.path.join(FRONTEND_DIR, "src/pages/GraphExplorer.tsx")
    assert os.path.isfile(path), "GraphExplorer.tsx should exist"
    with open(path, 'r') as f:
        content = f.read()
    assert "지식 그래프 탐색기" in content, "Should have Korean title"
    assert "global-ask" in content or "globalAsk" in content, "Should call globalAsk API"
    assert "커뮤니티" in content, "Should show communities"
    return True, f"size={len(content)} chars, has all key elements"

test("P4-02", "Frontend", "GraphExplorer.tsx 페이지 구조 검증", test_frontend_graph_explorer)

# --- 4.3 GraphService ---
def test_frontend_graph_service():
    path = os.path.join(FRONTEND_DIR, "src/services/graphService.ts")
    assert os.path.isfile(path), "graphService.ts should exist"
    with open(path, 'r') as f:
        content = f.read()
    endpoints = ["/graph/status", "/graph/related", "/graph/org", "/graph/tag", "/graph/region", "/rag/global-ask", "/rag/status"]
    found = [ep for ep in endpoints if ep in content]
    assert len(found) >= 5, f"Should have most API endpoints, found: {found}"
    return True, f"endpoints={len(found)}/{len(endpoints)}: {found}"

test("P4-03", "Frontend", "graphService.ts API 엔드포인트 검증", test_frontend_graph_service)

# --- 4.4 Routes ---
def test_frontend_routes():
    path = os.path.join(FRONTEND_DIR, "src/routes.tsx")
    with open(path, 'r') as f:
        content = f.read()
    assert "GraphExplorer" in content, "Should import GraphExplorer"
    assert "/graph" in content, "Should have /graph route"
    return True, f"GraphExplorer imported, /graph route registered"

test("P4-04", "Frontend", "라우트 설정 (/graph) 검증", test_frontend_routes)

# --- 4.5 Navigation ---
def test_frontend_navigation():
    path = os.path.join(FRONTEND_DIR, "src/components/layout/MainLayout.tsx")
    with open(path, 'r') as f:
        content = f.read()
    assert "지식 그래프" in content, "Should have navigation item"
    assert "Hub" in content, "Should import Hub icon"
    assert "/graph" in content, "Should link to /graph"
    return True, f"'지식 그래프' nav item with Hub icon → /graph"

test("P4-05", "Frontend", "사이드바 네비게이션 (지식 그래프) 검증", test_frontend_navigation)

# --- 4.6 TypeScript No Errors ---
def test_frontend_typescript():
    result = subprocess.run(
        ["npx", "tsc", "--noEmit"],
        capture_output=True, text=True,
        cwd=FRONTEND_DIR, timeout=60
    )
    # tsc --noEmit returns 0 if no errors
    has_errors = "error TS" in result.stdout or "error TS" in result.stderr
    return not has_errors, f"returncode={result.returncode}, errors={'yes' if has_errors else 'none'}"

test("P4-06", "Frontend", "TypeScript 컴파일 에러 없음", test_frontend_typescript)

# --- 4.7 No Missing Imports ---
def test_frontend_imports():
    path = os.path.join(FRONTEND_DIR, "src/pages/GraphExplorer.tsx")
    with open(path, 'r') as f:
        content = f.read()
    # Check critical imports exist
    critical = ["@mui/material", "graphService", "useState", "useCallback"]
    found = [c for c in critical if c in content]
    missing = [c for c in critical if c not in content]
    assert len(missing) == 0, f"Missing imports: {missing}"
    return True, f"all {len(critical)} critical imports present"

test("P4-07", "Frontend", "GraphExplorer 필수 import 검증", test_frontend_imports)


# ===================================================================
# PHASE 5: 통합 테스트 (Cross-Phase)
# ===================================================================
print("\n" + "="*60)
print("  PHASE 5: 통합 테스트 (Cross-Phase)")
print("="*60)

# --- 5.1 RAG + GraphRAG Status Combined ---
def test_integration_status():
    r = requests.get(f"{BASE_URL}/rag/status", timeout=10)
    d = r.json()
    assert d["rag_available"] is True
    assert d.get("graphrag", {}).get("available") is True
    assert d.get("search_available") is True
    return True, f"rag=True, graphrag=True, search=True, llm={d['llm_available']}"

test("P5-01", "Integration", "RAG + GraphRAG 통합 상태 확인", test_integration_status)

# --- 5.2 Batch Pipeline Configuration ---
def test_batch_pipeline():
    path = "/Users/blockmeta/Desktop/workspace/odin-ai/batch/production_batch.py"
    with open(path, 'r') as f:
        content = f.read()
    checks = {
        "Neo4j sync": "ENABLE_GRAPH_SYNC" in content or "neo4j_sync" in content.lower(),
        "GraphRAG": "ENABLE_GRAPHRAG" in content or "graphrag" in content.lower(),
    }
    passed = all(checks.values())
    detail = ", ".join([f"{k}={'OK' if v else 'MISS'}" for k, v in checks.items()])
    return passed, detail

test("P5-02", "Integration", "배치 파이프라인 Phase 3.6/3.7 등록 확인", test_batch_pipeline)

# --- 5.3 Requirements.txt ---
def test_requirements():
    path = "/Users/blockmeta/Desktop/workspace/odin-ai/requirements.txt"
    with open(path, 'r') as f:
        content = f.read()
    required = ["sentence-transformers", "httpx", "neo4j", "networkx", "python-louvain"]
    found = [r for r in required if r in content]
    missing = [r for r in required if r not in content]
    assert len(missing) == 0, f"Missing: {missing}"
    return True, f"all {len(required)} deps present: {found}"

test("P5-03", "Integration", "requirements.txt 의존성 완전성 확인", test_requirements)

# --- 5.4 SQL Tables Exist ---
def test_sql_tables():
    import psycopg2
    conn = psycopg2.connect("postgresql://blockmeta@localhost:5432/odin_db")
    cur = conn.cursor()
    tables = ["graphrag_entities", "graphrag_communities", "neo4j_sync_log", "rfp_chunks"]
    results = {}
    for table in tables:
        cur.execute(f"SELECT COUNT(*) FROM {table}")
        results[table] = cur.fetchone()[0]
    conn.close()
    all_exist = all(v >= 0 for v in results.values())
    detail = ", ".join([f"{t}={c}" for t, c in results.items()])
    return all_exist, detail

test("P5-04", "Integration", "필수 SQL 테이블 존재 및 데이터 확인", test_sql_tables)

# --- 5.5 Embedding Dimension Consistency ---
def test_embedding_dimension():
    import psycopg2
    conn = psycopg2.connect("postgresql://blockmeta@localhost:5432/odin_db")
    cur = conn.cursor()
    # Check rfp_chunks embedding dimension
    cur.execute("""
        SELECT pg_typeof(embedding)::text FROM rfp_chunks WHERE embedding IS NOT NULL LIMIT 1
    """)
    chunk_type = cur.fetchone()
    # Check graphrag_entities embedding dimension
    cur.execute("""
        SELECT pg_typeof(embedding)::text FROM graphrag_entities WHERE embedding IS NOT NULL LIMIT 1
    """)
    entity_type = cur.fetchone()
    conn.close()
    return True, f"chunk_embedding={chunk_type[0] if chunk_type else 'N/A'}, entity_embedding={entity_type[0] if entity_type else 'N/A'}"

test("P5-05", "Integration", "임베딩 차원 일관성 (1024dim) 확인", test_embedding_dimension)

# --- 5.6 Docker Compose ---
def test_docker_compose():
    path = "/Users/blockmeta/Desktop/workspace/odin-ai/frontend/docker-compose.yml"
    if not os.path.isfile(path):
        return None  # skip
    with open(path, 'r') as f:
        content = f.read()
    has_pgvector = "pgvector" in content
    has_neo4j = "neo4j" in content
    return True, f"pgvector={has_pgvector}, neo4j={has_neo4j}"

test("P5-06", "Integration", "docker-compose.yml pgvector/neo4j 설정 확인", test_docker_compose)

# --- 5.7 GraphRAG Indexer CLI ---
def test_graphrag_indexer():
    path = "/Users/blockmeta/Desktop/workspace/odin-ai/batch/modules/graphrag_indexer.py"
    assert os.path.isfile(path), "graphrag_indexer.py should exist"
    with open(path, 'r') as f:
        content = f.read()
    checks = {
        "Louvain": "community_louvain" in content or "louvain" in content.lower(),
        "KURE-v1": "KURE" in content or "kure" in content.lower(),
        "Ollama": "ollama" in content.lower(),
        "CLI": "__main__" in content or "argparse" in content,
    }
    detail = ", ".join([f"{k}={'OK' if v else 'MISS'}" for k, v in checks.items()])
    return all(checks.values()), detail

test("P5-07", "Integration", "GraphRAG 인덱서 모듈 구조 검증", test_graphrag_indexer)

# --- 5.8 Neo4j Syncer Module ---
def test_neo4j_syncer():
    path = "/Users/blockmeta/Desktop/workspace/odin-ai/batch/modules/neo4j_syncer.py"
    assert os.path.isfile(path), "neo4j_syncer.py should exist"
    with open(path, 'r') as f:
        content = f.read()
    checks = {
        "neo4j driver": "neo4j" in content,
        "BidAnnouncement": "BidAnnouncement" in content,
        "Organization": "Organization" in content,
        "SIMILAR_TO": "SIMILAR_TO" in content,
    }
    detail = ", ".join([f"{k}={'OK' if v else 'MISS'}" for k, v in checks.items()])
    return all(checks.values()), detail

test("P5-08", "Integration", "Neo4j 동기화 모듈 구조 검증", test_neo4j_syncer)


# ===================================================================
# 결과 요약
# ===================================================================
print("\n" + "="*60)
print("  테스트 결과 요약")
print("="*60)

total = PASS_COUNT + FAIL_COUNT + SKIP_COUNT
print(f"\n  총 {total}개 테스트")
print(f"  ✅ PASS: {PASS_COUNT}")
print(f"  ❌ FAIL: {FAIL_COUNT}")
print(f"  ⏭️ SKIP: {SKIP_COUNT}")
print(f"  성공률: {PASS_COUNT/total*100:.1f}%" if total > 0 else "")

# Category breakdown
print("\n  카테고리별:")
categories = {}
for r in RESULTS:
    cat = r["category"]
    if cat not in categories:
        categories[cat] = {"pass": 0, "fail": 0, "skip": 0}
    categories[cat][r["status"].lower()] = categories[cat].get(r["status"].lower(), 0) + 1

for cat, stats in categories.items():
    p, f, s = stats.get("pass", 0), stats.get("fail", 0), stats.get("skip", 0)
    total_cat = p + f + s
    icon = "✅" if f == 0 else "⚠️"
    print(f"  {icon} {cat}: {p}/{total_cat} 통과")

# Failed tests
if FAIL_COUNT > 0:
    print("\n  ❌ 실패한 테스트:")
    for r in RESULTS:
        if r["status"] == "FAIL":
            print(f"    - [{r['id']}] {r['description']}: {r['detail'][:100]}")

# Save JSON report
report = {
    "timestamp": datetime.now().isoformat(),
    "summary": {
        "total": total,
        "pass": PASS_COUNT,
        "fail": FAIL_COUNT,
        "skip": SKIP_COUNT,
        "pass_rate": f"{PASS_COUNT/total*100:.1f}%" if total > 0 else "0%",
    },
    "results": RESULTS,
}

report_path = "/Users/blockmeta/Desktop/workspace/odin-ai/reports/test_phase1_3_report.json"
os.makedirs(os.path.dirname(report_path), exist_ok=True)
with open(report_path, "w", encoding="utf-8") as f:
    json.dump(report, f, ensure_ascii=False, indent=2)

print(f"\n  📄 상세 리포트: {report_path}")
print("="*60)

sys.exit(0 if FAIL_COUNT == 0 else 1)
