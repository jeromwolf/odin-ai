"""
RAG 의미 검색 API
하이브리드 벡터 + 전문검색 엔드포인트
"""

from fastapi import APIRouter, Query, Request
from typing import Optional
import logging
import os

from database import get_db_connection
from middleware.rate_limit import limiter
from errors import ErrorCode, ApiError

logger = logging.getLogger(__name__)

# Services (optional imports)
try:
    from services.hybrid_search import get_hybrid_search_service
    RAG_AVAILABLE = True
except ImportError:
    RAG_AVAILABLE = False
    logger.warning("하이브리드 검색 서비스 로드 실패 - RAG API 비활성화")

try:
    from services.graphrag_service import get_graphrag_service
    GRAPHRAG_SERVICE_AVAILABLE = True
except ImportError:
    GRAPHRAG_SERVICE_AVAILABLE = False

# Ollama LLM for answer synthesis (local)
try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False

router = APIRouter(prefix="/api/rag", tags=["RAG Search"])


@router.get("/search")
@limiter.limit("30/minute")
async def rag_search(
    request: Request,
    q: str = Query(..., min_length=1, max_length=500, description="검색 쿼리"),
    limit: int = Query(10, ge=1, le=50, description="결과 수"),
    section_type: Optional[str] = Query(None, description="섹션 타입 필터 (자격요건, 예정가격 등)"),
    bid_notice_no: Optional[str] = Query(None, description="특정 공고 필터"),
):
    """
    RAG 하이브리드 검색

    벡터 유사도 + 전문 검색을 RRF로 결합하여
    의미적으로 관련된 문서 청크를 반환합니다.
    """
    if not RAG_AVAILABLE:
        raise ApiError(503, ErrorCode.SERVICE_RAG_UNAVAILABLE, "RAG 검색 서비스가 비활성화되어 있습니다")

    try:
        service = get_hybrid_search_service()
        result = service.search(
            query=q,
            limit=limit,
            filter_bid_notice_no=bid_notice_no,
            filter_section_type=section_type,
        )

        return {
            "success": True,
            "query": q,
            "search_mode": result.get("search_mode", "unknown"),
            "total": result.get("total", 0),
            "results": result.get("results", []),
        }

    except Exception as e:
        logger.error(f"RAG 검색 실패: {e}")
        raise ApiError(500, ErrorCode.SEARCH_FAILED, "검색 처리 중 오류가 발생했습니다")


@router.get("/ask")
@limiter.limit("10/minute")
async def rag_ask(
    request: Request,
    q: str = Query(..., min_length=1, max_length=500, description="질문"),
    limit: int = Query(5, ge=1, le=20, description="참조 청크 수"),
    bid_notice_no: Optional[str] = Query(None, description="특정 공고로 한정"),
):
    """
    RAG 질의응답

    관련 문서를 검색한 후 LLM으로 답변을 생성합니다.
    OPENAI_API_KEY가 없으면 검색 결과만 반환합니다.
    """
    if not RAG_AVAILABLE:
        raise ApiError(503, ErrorCode.SERVICE_RAG_UNAVAILABLE, "RAG 검색 서비스가 비활성화되어 있습니다")

    try:
        # 1. Retrieve relevant chunks
        service = get_hybrid_search_service()
        search_result = service.search(
            query=q,
            limit=limit,
            filter_bid_notice_no=bid_notice_no,
        )

        chunks = search_result.get("results", [])

        if not chunks:
            return {
                "success": True,
                "query": q,
                "answer": "관련 문서를 찾을 수 없습니다.",
                "sources": [],
                "has_llm_answer": False,
            }

        # 2. Synthesize answer with LLM (if available)
        ollama_url = os.getenv("OLLAMA_URL", "http://localhost:11434")
        if HTTPX_AVAILABLE and ollama_url:
            answer = await _synthesize_answer(q, chunks)
            has_llm = True
        else:
            # No LLM: return chunks as-is
            answer = "LLM이 비활성화되어 검색 결과만 반환합니다. 아래 관련 문서를 참고하세요."
            has_llm = False

        # 3. Build sources
        sources = []
        seen_bids = set()
        for chunk in chunks:
            bid_no = chunk.get("bid_notice_no")
            if bid_no not in seen_bids:
                sources.append({
                    "bid_notice_no": bid_no,
                    "bid_title": chunk.get("bid_title"),
                    "organization_name": chunk.get("organization_name"),
                    "section_type": chunk.get("section_type"),
                    "score": chunk.get("score"),
                })
                seen_bids.add(bid_no)

        return {
            "success": True,
            "query": q,
            "answer": answer,
            "sources": sources,
            "chunks": chunks,
            "has_llm_answer": has_llm,
            "search_mode": search_result.get("search_mode"),
        }

    except Exception as e:
        logger.error(f"RAG 질의응답 실패: {e}")
        raise ApiError(500, ErrorCode.SEARCH_FAILED, "질의응답 처리 중 오류가 발생했습니다")


@router.get("/status")
async def rag_status():
    """
    RAG 시스템 상태 및 임베딩 현황
    """
    status = {
        "rag_available": RAG_AVAILABLE,
        "llm_available": HTTPX_AVAILABLE and bool(os.getenv("OLLAMA_URL")),
        "embedding_stats": {},
    }

    if RAG_AVAILABLE:
        try:
            service = get_hybrid_search_service()
            status["embedding_stats"] = service.get_embedding_stats()
            status["search_available"] = service.is_available()
        except Exception as e:
            logger.error(f"RAG 상태 조회 실패: {e}")
            status["search_available"] = False

    # GraphRAG 통계 추가
    if GRAPHRAG_SERVICE_AVAILABLE:
        status["graphrag"] = get_graphrag_service().get_stats()
    else:
        status["graphrag"] = {"available": False}

    return status


@router.get("/global-ask")
@limiter.limit("10/minute")
async def rag_global_ask(
    request: Request,
    q: str = Query(..., min_length=1, max_length=500, description="글로벌 질문"),
    top_communities: int = Query(5, ge=1, le=20, description="참조 커뮤니티 수"),
):
    """
    GraphRAG 글로벌 질의응답

    커뮤니티 요약을 기반으로 전체적인 패턴, 트렌드,
    인사이트에 대한 답변을 생성합니다.
    """
    if not GRAPHRAG_SERVICE_AVAILABLE:
        raise ApiError(503, ErrorCode.SERVICE_GRAPH_UNAVAILABLE, "GraphRAG 서비스가 비활성화되어 있습니다")

    try:
        result = get_graphrag_service().global_ask(q, top_communities=top_communities)
        return {"success": True, **result}

    except Exception as e:
        logger.error(f"GraphRAG 글로벌 질의 실패: {e}")
        raise ApiError(500, ErrorCode.SEARCH_FAILED, "글로벌 질의 처리 중 오류가 발생했습니다")


async def _synthesize_answer(query: str, chunks: list) -> str:
    """Ollama EXAONE 3.5로 답변 합성 (로컬 LLM)"""
    ollama_url = os.getenv("OLLAMA_URL", "http://localhost:11434")
    ollama_model = os.getenv("OLLAMA_MODEL", "exaone3.5:7.8b")

    try:
        # Build context from chunks
        context_parts = []
        for i, chunk in enumerate(chunks[:5], 1):
            bid_title = chunk.get("bid_title", "")
            section = chunk.get("section_type", "")
            text = chunk.get("chunk_text", "")
            context_parts.append(f"[문서 {i}] {bid_title} ({section})\n{text}")

        context = "\n\n---\n\n".join(context_parts)

        prompt = (
            "당신은 한국 공공입찰 전문가입니다. "
            "아래 입찰공고 문서를 참고하여 질문에 정확하게 답변하세요. "
            "답변은 한국어로 작성하고, 근거가 되는 문서 번호를 인용하세요. "
            "문서에 없는 내용은 추측하지 마세요.\n\n"
            f"참고 문서:\n{context}\n\n"
            f"질문: {query}\n\n답변:"
        )

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{ollama_url}/api/generate",
                json={
                    "model": ollama_model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {"temperature": 0.3, "num_predict": 1000}
                },
                timeout=60.0
            )
        response.raise_for_status()
        return response.json().get("response", "답변 생성에 실패했습니다.")

    except Exception as e:
        logger.error(f"Ollama LLM 답변 합성 실패: {e}")
        return "답변 생성 중 오류가 발생했습니다. 잠시 후 다시 시도하세요."
