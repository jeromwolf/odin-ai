"""
하이브리드 검색 서비스
pgvector 벡터 유사도 + PostgreSQL FTS를 RRF로 결합
"""

import logging
from typing import List, Dict, Optional
from database import get_db_connection
from psycopg2.extras import RealDictCursor

logger = logging.getLogger(__name__)

# Optional imports
try:
    from services.embedding_service import get_embedding_provider
    EMBEDDING_AVAILABLE = True
except ImportError:
    EMBEDDING_AVAILABLE = False

try:
    from services.ontology_service import expand_search_terms
    ONTOLOGY_AVAILABLE = True
except ImportError:
    ONTOLOGY_AVAILABLE = False


class HybridSearchService:
    """
    하이브리드 검색 서비스

    검색 전략:
    1. 벡터 유사도 검색 (pgvector cosine distance)
    2. 전문 검색 (PostgreSQL tsvector + plainto_tsquery)
    3. RRF (Reciprocal Rank Fusion)로 두 결과 통합
    4. 온톨로지 확장으로 FTS 쿼리 보강
    """

    def __init__(self):
        self._embedder = None
        self._pgvector_available = None  # Lazy check

    @property
    def embedder(self):
        if self._embedder is None and EMBEDDING_AVAILABLE:
            self._embedder = get_embedding_provider()
        return self._embedder

    def is_available(self) -> bool:
        """RAG 검색 가능 여부 확인"""
        if self._pgvector_available is None:
            self._pgvector_available = self._check_pgvector()
        return self._pgvector_available and self.embedder is not None

    def _check_pgvector(self) -> bool:
        """pgvector 확장 설치 여부 확인"""
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor(cursor_factory=RealDictCursor)
                cursor.execute("SELECT 1 FROM pg_extension WHERE extname = 'vector'")
                result = cursor.fetchone()
                return result is not None
        except Exception:
            return False

    def search(
        self,
        query: str,
        limit: int = 10,
        rrf_k: int = 60,
        candidate_count: int = 40,
        filter_bid_notice_no: Optional[str] = None,
        filter_section_type: Optional[str] = None,
    ) -> Dict:
        """
        하이브리드 검색 실행

        Args:
            query: 검색 쿼리 (한국어 텍스트)
            limit: 최종 반환 결과 수
            rrf_k: RRF 상수 (높을수록 균등 가중치, 기본 60)
            candidate_count: 각 검색에서 가져올 후보 수
            filter_bid_notice_no: 특정 공고로 필터링
            filter_section_type: 특정 섹션 타입으로 필터링

        Returns:
            {
                "results": [...],
                "total": int,
                "search_mode": "hybrid" | "fts_only" | "vector_only"
            }
        """
        # Determine search mode based on available services (use cached pgvector check)
        if self._pgvector_available is None:
            self._pgvector_available = self._check_pgvector()
        has_vector = self.embedder is not None and self._pgvector_available

        if has_vector:
            return self._hybrid_search(
                query, limit, rrf_k, candidate_count,
                filter_bid_notice_no, filter_section_type
            )
        else:
            return self._fts_only_search(
                query, limit, filter_bid_notice_no, filter_section_type
            )

    def _hybrid_search(
        self, query, limit, rrf_k, candidate_count,
        filter_bid_notice_no, filter_section_type
    ) -> Dict:
        """벡터 + FTS 하이브리드 검색 (RRF)"""

        # 1. Generate query embedding
        query_embedding = self.embedder.embed_query(query)
        if query_embedding is None:
            logger.warning("쿼리 임베딩 실패 - FTS만 사용")
            return self._fts_only_search(
                query, limit, filter_bid_notice_no, filter_section_type
            )

        # 2. Expand query via ontology for FTS
        fts_query = query
        use_tsquery = False  # Track if we need to_tsquery vs plainto_tsquery
        if ONTOLOGY_AVAILABLE:
            try:
                expanded = expand_search_terms(query)
                if expanded:
                    fts_query = ' | '.join(expanded[:10])  # OR terms for tsquery
                    use_tsquery = True
            except Exception:
                pass

        # 3. Build and execute hybrid search SQL
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor(cursor_factory=RealDictCursor)

                # Set HNSW search parameter
                cursor.execute("SET hnsw.ef_search = 100")

                # Build filter conditions
                filters = []
                params = []

                if filter_bid_notice_no:
                    filters.append(f"rc.bid_notice_no = %s")
                    params.append(filter_bid_notice_no)
                if filter_section_type:
                    filters.append(f"rc.section_type = %s")
                    params.append(filter_section_type)

                filter_sql = " AND " + " AND ".join(filters) if filters else ""

                # Hybrid RRF query
                sql = f"""
                    WITH
                    vector_results AS (
                        SELECT
                            rc.chunk_id,
                            ROW_NUMBER() OVER (
                                ORDER BY rc.embedding <=> %s::vector
                            ) AS rank
                        FROM rfp_chunks rc
                        WHERE rc.embedding IS NOT NULL
                        {filter_sql}
                        ORDER BY rc.embedding <=> %s::vector
                        LIMIT %s
                    ),
                    fts_results AS (
                        SELECT
                            rc.chunk_id,
                            ROW_NUMBER() OVER (
                                ORDER BY ts_rank_cd(rc.chunk_text_tsv, query, 32) DESC
                            ) AS rank
                        FROM rfp_chunks rc,
                             {'to_tsquery' if use_tsquery else 'plainto_tsquery'}('simple', %s) query
                        WHERE rc.chunk_text_tsv @@ query
                        {filter_sql}
                        LIMIT %s
                    ),
                    combined AS (
                        SELECT chunk_id, 1.0 / (%s + rank) AS rrf_score, 'vector' AS source
                        FROM vector_results
                        UNION ALL
                        SELECT chunk_id, 1.0 / (%s + rank) AS rrf_score, 'fts' AS source
                        FROM fts_results
                    ),
                    fused AS (
                        SELECT
                            chunk_id,
                            SUM(rrf_score) AS final_score,
                            ARRAY_AGG(DISTINCT source) AS match_sources
                        FROM combined
                        GROUP BY chunk_id
                        ORDER BY final_score DESC
                        LIMIT %s
                    )
                    SELECT
                        rc.chunk_id,
                        rc.chunk_text,
                        rc.bid_notice_no,
                        rc.section_type,
                        rc.chunk_index,
                        rc.token_count,
                        f.final_score,
                        f.match_sources,
                        ba.title AS bid_title,
                        ba.organization_name,
                        ba.estimated_price,
                        ba.bid_end_date
                    FROM fused f
                    JOIN rfp_chunks rc ON rc.chunk_id = f.chunk_id
                    JOIN bid_announcements ba ON ba.bid_notice_no = rc.bid_notice_no
                    ORDER BY f.final_score DESC
                """

                # Build parameter list
                embedding_str = "[" + ",".join(f"{x:.8g}" for x in query_embedding) + "]"
                query_params = [embedding_str]  # vector_results embedding
                query_params.extend(params)      # vector_results filters
                query_params.append(embedding_str)  # vector_results ORDER BY
                query_params.append(candidate_count) # vector_results LIMIT
                query_params.append(fts_query)   # fts_results query text
                query_params.extend(params)      # fts_results filters
                query_params.append(candidate_count)  # fts_results LIMIT
                query_params.append(rrf_k)       # RRF k for vector
                query_params.append(rrf_k)       # RRF k for fts
                query_params.append(limit)       # fused LIMIT

                cursor.execute(sql, query_params)
                rows = cursor.fetchall()

                results = []
                for row in rows:
                    results.append({
                        "chunk_id": row["chunk_id"],
                        "chunk_text": row["chunk_text"],
                        "bid_notice_no": row["bid_notice_no"],
                        "section_type": row["section_type"],
                        "chunk_index": row["chunk_index"],
                        "token_count": row["token_count"],
                        "score": round(float(row["final_score"]), 6),
                        "match_sources": row["match_sources"],
                        "bid_title": row["bid_title"],
                        "organization_name": row["organization_name"],
                        "estimated_price": row["estimated_price"],
                        "bid_end_date": row["bid_end_date"].isoformat() if row["bid_end_date"] else None,
                    })

                return {
                    "results": results,
                    "total": len(results),
                    "search_mode": "hybrid",
                }

        except Exception as e:
            logger.error(f"하이브리드 검색 실패: {e}")
            # Fallback to FTS
            return self._fts_only_search(
                query, limit, filter_bid_notice_no, filter_section_type
            )

    def _fts_only_search(
        self, query, limit, filter_bid_notice_no, filter_section_type
    ) -> Dict:
        """FTS 전용 검색 (pgvector 없을 때 폴백)"""
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor(cursor_factory=RealDictCursor)

                filters = []
                params = []

                if filter_bid_notice_no:
                    filters.append("rc.bid_notice_no = %s")
                    params.append(filter_bid_notice_no)
                if filter_section_type:
                    filters.append("rc.section_type = %s")
                    params.append(filter_section_type)

                filter_sql = " AND " + " AND ".join(filters) if filters else ""

                # Expand with ontology
                fts_query = query
                use_tsquery = False  # Track if we need to_tsquery vs plainto_tsquery
                if ONTOLOGY_AVAILABLE:
                    try:
                        expanded = expand_search_terms(query)
                        if expanded:
                            fts_query = ' | '.join(expanded[:10])
                            use_tsquery = True
                    except Exception:
                        pass

                sql = f"""
                    SELECT
                        rc.chunk_id,
                        rc.chunk_text,
                        rc.bid_notice_no,
                        rc.section_type,
                        rc.chunk_index,
                        rc.token_count,
                        ts_rank_cd(rc.chunk_text_tsv, query, 32) AS score,
                        ba.title AS bid_title,
                        ba.organization_name,
                        ba.estimated_price,
                        ba.bid_end_date
                    FROM rfp_chunks rc
                    CROSS JOIN {'to_tsquery' if use_tsquery else 'plainto_tsquery'}('simple', %s) query
                    JOIN bid_announcements ba ON ba.bid_notice_no = rc.bid_notice_no
                    WHERE rc.chunk_text_tsv @@ query
                    {filter_sql}
                    ORDER BY score DESC
                    LIMIT %s
                """

                cursor.execute(sql, [fts_query] + params + [limit])
                rows = cursor.fetchall()

                results = []
                for row in rows:
                    results.append({
                        "chunk_id": row["chunk_id"],
                        "chunk_text": row["chunk_text"],
                        "bid_notice_no": row["bid_notice_no"],
                        "section_type": row["section_type"],
                        "chunk_index": row["chunk_index"],
                        "token_count": row["token_count"],
                        "score": round(float(row["score"]), 6),
                        "match_sources": ["fts"],
                        "bid_title": row["bid_title"],
                        "organization_name": row["organization_name"],
                        "estimated_price": row["estimated_price"],
                        "bid_end_date": row["bid_end_date"].isoformat() if row["bid_end_date"] else None,
                    })

                return {
                    "results": results,
                    "total": len(results),
                    "search_mode": "fts_only",
                }

        except Exception as e:
            logger.error(f"FTS 검색 실패: {e}")
            return {"results": [], "total": 0, "search_mode": "error"}

    def get_embedding_stats(self) -> Dict:
        """임베딩 현황 통계"""
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor(cursor_factory=RealDictCursor)

                cursor.execute("""
                    SELECT
                        (SELECT COUNT(*) FROM bid_announcements) as total_bids,
                        (SELECT COUNT(*) FROM bid_announcements WHERE has_embedding = TRUE) as embedded_bids,
                        (SELECT COUNT(*) FROM rfp_chunks) as total_chunks,
                        (SELECT COUNT(*) FROM rfp_chunks WHERE embedding IS NOT NULL) as embedded_chunks
                """)
                row = cursor.fetchone()

                total_bids = row["total_bids"] or 0
                embedded_bids = row["embedded_bids"] or 0

                return {
                    "total_bids": total_bids,
                    "embedded_bids": embedded_bids,
                    "total_chunks": row["total_chunks"] or 0,
                    "embedded_chunks": row["embedded_chunks"] or 0,
                    "coverage_pct": round(
                        (embedded_bids / total_bids * 100) if total_bids > 0 else 0, 1
                    ),
                }
        except Exception as e:
            logger.error(f"임베딩 통계 조회 실패: {e}")
            return {
                "total_bids": 0, "embedded_bids": 0,
                "total_chunks": 0, "embedded_chunks": 0,
                "coverage_pct": 0
            }


# Singleton
_search_service: Optional[HybridSearchService] = None

def get_hybrid_search_service() -> HybridSearchService:
    """하이브리드 검색 서비스 싱글턴"""
    global _search_service
    if _search_service is None:
        _search_service = HybridSearchService()
    return _search_service
