"""
Graph Search API
Neo4j 기반 그래프 검색 엔드포인트
"""

from fastapi import APIRouter, HTTPException, Query, Path
from typing import Optional
import logging

logger = logging.getLogger(__name__)

try:
    from services.graph_search_service import get_graph_search_service
    GRAPH_AVAILABLE = True
except ImportError:
    GRAPH_AVAILABLE = False

router = APIRouter(prefix="/api/graph", tags=["Graph Search"])


@router.get("/status")
async def graph_status():
    """Neo4j 그래프 DB 상태 및 통계"""
    if not GRAPH_AVAILABLE:
        return {"available": False, "reason": "neo4j 패키지 미설치"}

    service = get_graph_search_service()
    if not service:
        return {"available": False, "reason": "NEO4J_URL 미설정"}

    status = service.get_status()
    status["available"] = status.get("connected", False)
    return status


@router.get("/related/{bid_notice_no}")
async def graph_related(
    bid_notice_no: str = Path(..., description="입찰공고번호"),
    depth: int = Query(2, ge=1, le=3),
    limit: int = Query(20, ge=1, le=100),
):
    """특정 입찰공고의 관련 입찰 탐색"""
    if not GRAPH_AVAILABLE:
        raise HTTPException(503, "그래프 검색 비활성화")
    service = get_graph_search_service()
    if not service:
        raise HTTPException(503, "Neo4j 미연결")

    try:
        return service.search_related(bid_notice_no, depth=depth, limit=limit)
    except Exception as e:
        logger.error(f"관련 입찰 검색 실패: {e}")
        raise HTTPException(500, "관련 입찰 검색 중 오류가 발생했습니다")


@router.get("/org/{org_name}")
async def graph_org_network(
    org_name: str = Path(..., description="기관명"),
    limit: int = Query(50, ge=1, le=200),
):
    """기관 네트워크 조회"""
    if not GRAPH_AVAILABLE:
        raise HTTPException(503, "그래프 검색 비활성화")
    service = get_graph_search_service()
    if not service:
        raise HTTPException(503, "Neo4j 미연결")

    try:
        return service.get_org_network(org_name, limit=limit)
    except Exception as e:
        logger.error(f"기관 네트워크 조회 실패: {e}")
        raise HTTPException(500, "기관 네트워크 조회 중 오류가 발생했습니다")


@router.get("/tag/{tag_name}")
async def graph_tag_network(
    tag_name: str = Path(..., description="태그명"),
    limit: int = Query(30, ge=1, le=100),
):
    """태그 네트워크 조회"""
    if not GRAPH_AVAILABLE:
        raise HTTPException(503, "그래프 검색 비활성화")
    service = get_graph_search_service()
    if not service:
        raise HTTPException(503, "Neo4j 미연결")

    try:
        return service.get_tag_network(tag_name, limit=limit)
    except Exception as e:
        logger.error(f"태그 네트워크 조회 실패: {e}")
        raise HTTPException(500, "태그 네트워크 조회 중 오류가 발생했습니다")


@router.get("/region/{region_name}")
async def graph_region_bids(
    region_name: str = Path(..., description="지역명"),
    limit: int = Query(30, ge=1, le=100),
):
    """지역별 입찰 조회"""
    if not GRAPH_AVAILABLE:
        raise HTTPException(503, "그래프 검색 비활성화")
    service = get_graph_search_service()
    if not service:
        raise HTTPException(503, "Neo4j 미연결")

    try:
        return service.get_region_bids(region_name, limit=limit)
    except Exception as e:
        logger.error(f"지역별 입찰 조회 실패: {e}")
        raise HTTPException(500, "지역별 입찰 조회 중 오류가 발생했습니다")
