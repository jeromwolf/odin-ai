"""
GraphRAG 서비스 레이어
커뮤니티 기반 글로벌 질의응답 로직
"""

import json
import logging
import os
from typing import Dict, Any, List, Optional

from database import get_db_connection

logger = logging.getLogger(__name__)

try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False


class GraphRAGService:
    """GraphRAG 커뮤니티 기반 질의응답 서비스"""

    def __init__(self):
        self.ollama_url = os.getenv("OLLAMA_URL", "http://localhost:11434")
        self.ollama_model = os.getenv("OLLAMA_MODEL", "exaone3.5:7.8b")

    def get_stats(self) -> Dict[str, Any]:
        """GraphRAG 통계 조회"""
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM graphrag_entities")
                entity_count = cursor.fetchone()[0]
                cursor.execute("SELECT COUNT(*) FROM graphrag_communities")
                community_count = cursor.fetchone()[0]
                cursor.close()
            return {
                "entities": entity_count,
                "communities": community_count,
                "available": entity_count > 0,
            }
        except Exception:
            return {"available": False}

    def global_ask(self, query: str, top_communities: int = 5) -> Dict[str, Any]:
        """커뮤니티 기반 글로벌 질의응답"""
        with get_db_connection() as conn:
            cursor = conn.cursor()

            # 1. 커뮤니티 요약 조회
            cursor.execute("""
                SELECT community_id, title, summary, findings,
                       entity_count, bid_count
                FROM graphrag_communities
                ORDER BY bid_count DESC
                LIMIT %s
            """, (top_communities,))
            communities = cursor.fetchall()

            if not communities:
                cursor.close()
                return {
                    "query": query,
                    "answer": "GraphRAG 커뮤니티 데이터가 없습니다. 인덱싱을 먼저 실행하세요.",
                    "communities": [],
                    "related_entities": [],
                    "has_llm_answer": False,
                }

            # 2. 커뮤니티 컨텍스트 구성
            community_data = []
            context_parts = []
            for i, (cid, title, summary, findings, e_count, b_count) in enumerate(communities, 1):
                findings_parsed = json.loads(findings) if isinstance(findings, str) else findings
                context_parts.append(
                    f"[커뮤니티 {i}] {title}\n"
                    f"요약: {summary}\n"
                    f"엔티티 {e_count}개, 관련 입찰 {b_count}건"
                )
                community_data.append({
                    "community_id": cid,
                    "title": title,
                    "summary": summary,
                    "entity_count": e_count,
                    "bid_count": b_count,
                    "findings": findings_parsed[:5] if findings_parsed else [],
                })

            # 3. 관련 엔티티 검색 (키워드 매칭)
            cursor.execute("""
                SELECT entity_type, entity_name, description, community_id
                FROM graphrag_entities
                WHERE entity_name ILIKE %s OR description ILIKE %s
                LIMIT 10
            """, (f'%{query}%', f'%{query}%'))
            related_entities = [
                {"type": r[0], "name": r[1], "description": r[2], "community_id": r[3]}
                for r in cursor.fetchall()
            ]
            cursor.close()

        # 4. LLM으로 글로벌 답변 생성
        context = "\n\n---\n\n".join(context_parts)
        answer = self._synthesize_global_answer(query, context, related_entities)

        return {
            "query": query,
            "answer": answer,
            "communities": community_data,
            "related_entities": related_entities,
            "has_llm_answer": self._is_llm_available(),
        }

    def _is_llm_available(self) -> bool:
        return HTTPX_AVAILABLE and bool(self.ollama_url)

    def _synthesize_global_answer(self, query: str, community_context: str, entities: list) -> str:
        """커뮤니티 기반 글로벌 답변 합성 (Ollama)"""
        if not self._is_llm_available():
            return "LLM이 비활성화되어 커뮤니티 요약만 반환합니다."

        try:
            entity_info = ""
            if entities:
                entity_info = "\n관련 엔티티:\n" + "\n".join([
                    f"- [{e['type']}] {e['name']}: {e.get('description', '')}"
                    for e in entities[:5]
                ])

            prompt = (
                "당신은 한국 공공입찰 데이터 분석 전문가입니다. "
                "아래 커뮤니티 분석 데이터를 기반으로 질문에 답변하세요. "
                "전체적인 트렌드, 패턴, 인사이트를 중심으로 답변하세요.\n\n"
                f"커뮤니티 분석 데이터:\n{community_context}\n"
                f"{entity_info}\n\n"
                f"질문: {query}\n\n답변:"
            )

            response = httpx.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": self.ollama_model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {"temperature": 0.3, "num_predict": 1000}
                },
                timeout=60.0
            )
            response.raise_for_status()
            return response.json().get("response", "답변 생성에 실패했습니다.")

        except Exception as e:
            logger.error(f"글로벌 답변 합성 실패: {e}")
            return "답변 생성 중 오류가 발생했습니다. 잠시 후 다시 시도하세요."


# 싱글턴 인스턴스
_graphrag_service: Optional[GraphRAGService] = None


def get_graphrag_service() -> GraphRAGService:
    global _graphrag_service
    if _graphrag_service is None:
        _graphrag_service = GraphRAGService()
    return _graphrag_service
