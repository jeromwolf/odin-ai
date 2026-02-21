"""
RAG 의미 검색 API
하이브리드 벡터 + 전문검색 엔드포인트
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional
import logging
import os

logger = logging.getLogger(__name__)

# Services (optional imports)
try:
    from services.hybrid_search import get_hybrid_search_service
    RAG_AVAILABLE = True
except ImportError:
    RAG_AVAILABLE = False
    logger.warning("하이브리드 검색 서비스 로드 실패 - RAG API 비활성화")

# OpenAI for answer synthesis (optional)
try:
    from openai import OpenAI
    LLM_AVAILABLE = True
except ImportError:
    LLM_AVAILABLE = False

router = APIRouter(prefix="/api/rag", tags=["RAG Search"])


@router.get("/search")
async def rag_search(
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
        raise HTTPException(status_code=503, detail="RAG 검색 서비스가 비활성화되어 있습니다")

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
        raise HTTPException(status_code=500, detail="검색 처리 중 오류가 발생했습니다")


@router.get("/ask")
async def rag_ask(
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
        raise HTTPException(status_code=503, detail="RAG 검색 서비스가 비활성화되어 있습니다")

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
        api_key = os.getenv("OPENAI_API_KEY")
        if LLM_AVAILABLE and api_key:
            answer = _synthesize_answer(q, chunks, api_key)
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
        raise HTTPException(status_code=500, detail="질의응답 처리 중 오류가 발생했습니다")


@router.get("/status")
async def rag_status():
    """
    RAG 시스템 상태 및 임베딩 현황
    """
    status = {
        "rag_available": RAG_AVAILABLE,
        "llm_available": LLM_AVAILABLE and bool(os.getenv("OPENAI_API_KEY")),
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

    return status


def _synthesize_answer(query: str, chunks: list, api_key: str) -> str:
    """LLM으로 답변 합성"""
    try:
        client = OpenAI(api_key=api_key)

        # Build context from chunks
        context_parts = []
        for i, chunk in enumerate(chunks[:5], 1):
            bid_title = chunk.get("bid_title", "")
            section = chunk.get("section_type", "")
            text = chunk.get("chunk_text", "")
            context_parts.append(
                f"[문서 {i}] {bid_title} ({section})\n{text}"
            )

        context = "\n\n---\n\n".join(context_parts)

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "당신은 한국 공공입찰 전문가입니다. "
                        "아래 입찰공고 문서를 참고하여 질문에 정확하게 답변하세요. "
                        "답변은 한국어로 작성하고, 근거가 되는 문서 번호를 인용하세요. "
                        "문서에 없는 내용은 추측하지 마세요."
                    ),
                },
                {
                    "role": "user",
                    "content": f"참고 문서:\n{context}\n\n질문: {query}",
                },
            ],
            max_tokens=1000,
            temperature=0.3,
        )

        return response.choices[0].message.content

    except Exception as e:
        logger.error(f"LLM 답변 합성 실패: {e}")
        return f"답변 생성 중 오류가 발생했습니다: {str(e)}"
