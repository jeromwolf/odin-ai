"""
검색 관련 API 엔드포인트
"""

from fastapi import APIRouter, Query, HTTPException, Depends
from typing import Optional, List
from enum import Enum

from backend.services.search_service import SearchService, SearchType, SortOrder
from backend.models.database import get_db
from sqlalchemy.orm import Session

router = APIRouter(prefix="/api/search", tags=["검색"])


@router.get("/")
async def search(
    q: str = Query(..., description="검색어", min_length=1),
    type: str = Query("all", description="검색 타입 (all/bid/document/company)"),
    sort: str = Query("relevance", description="정렬 순서"),
    page: int = Query(1, ge=1, description="페이지 번호"),
    size: int = Query(20, ge=1, le=100, description="페이지 크기"),
    start_date: Optional[str] = Query(None, description="시작일 (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="종료일 (YYYY-MM-DD)"),
    min_price: Optional[int] = Query(None, description="최소 가격"),
    max_price: Optional[int] = Query(None, description="최대 가격"),
    organization: Optional[str] = Query(None, description="기관명"),
    industry: Optional[str] = Query(None, description="산업 분야"),
    status: Optional[str] = Query(None, description="상태"),
    db: Session = Depends(get_db)
):
    """
    통합 검색

    - 입찰공고, 문서, 기업 정보를 통합 검색
    - 다양한 필터 옵션 제공
    - 관련도순, 날짜순, 가격순 정렬 지원
    """
    try:
        # 검색 타입 변환
        search_type_map = {
            "all": SearchType.ALL,
            "bid": SearchType.BID,
            "document": SearchType.DOCUMENT,
            "company": SearchType.COMPANY
        }
        search_type = search_type_map.get(type.lower(), SearchType.ALL)

        # 정렬 순서 변환
        sort_order_map = {
            "relevance": SortOrder.RELEVANCE,
            "date_desc": SortOrder.DATE_DESC,
            "date_asc": SortOrder.DATE_ASC,
            "price_desc": SortOrder.PRICE_DESC,
            "price_asc": SortOrder.PRICE_ASC
        }
        sort_order = sort_order_map.get(sort.lower(), SortOrder.RELEVANCE)

        # 필터 구성
        filters = {}
        if start_date:
            filters["start_date"] = start_date
        if end_date:
            filters["end_date"] = end_date
        if min_price is not None:
            filters["min_price"] = min_price
        if max_price is not None:
            filters["max_price"] = max_price
        if organization:
            filters["organization"] = organization
        if industry:
            filters["industry"] = industry
        if status:
            filters["status"] = status

        # 검색 서비스 호출
        search_service = SearchService(db)
        results = await search_service.search(
            query=q,
            search_type=search_type,
            filters=filters,
            sort_order=sort_order,
            page=page,
            page_size=size
        )

        return results

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"검색 실패: {str(e)}")
    finally:
        if 'search_service' in locals():
            search_service.close()


@router.get("/bids")
async def search_bids(
    q: Optional[str] = Query(None, description="검색어"),
    start_date: Optional[str] = Query(None, description="시작일"),
    end_date: Optional[str] = Query(None, description="종료일"),
    min_price: Optional[int] = Query(None, description="최소 가격"),
    max_price: Optional[int] = Query(None, description="최대 가격"),
    organization: Optional[str] = Query(None, description="기관명"),
    status: Optional[str] = Query(None, description="상태"),
    sort: str = Query("date_desc", description="정렬 순서"),
    page: int = Query(1, ge=1, description="페이지 번호"),
    size: int = Query(20, ge=1, le=100, description="페이지 크기"),
    db: Session = Depends(get_db)
):
    """
    입찰공고 검색

    - 입찰공고만 검색
    - 상세 필터 옵션 제공
    """
    try:
        # 정렬 순서 변환
        sort_order_map = {
            "relevance": SortOrder.RELEVANCE,
            "date_desc": SortOrder.DATE_DESC,
            "date_asc": SortOrder.DATE_ASC,
            "price_desc": SortOrder.PRICE_DESC,
            "price_asc": SortOrder.PRICE_ASC
        }
        sort_order = sort_order_map.get(sort.lower(), SortOrder.DATE_DESC)

        # 필터 구성
        filters = {}
        if start_date:
            filters["start_date"] = start_date
        if end_date:
            filters["end_date"] = end_date
        if min_price is not None:
            filters["min_price"] = min_price
        if max_price is not None:
            filters["max_price"] = max_price
        if organization:
            filters["organization"] = organization
        if status:
            filters["status"] = status

        # 검색 서비스 호출
        search_service = SearchService(db)
        results = await search_service.search(
            query=q or "",
            search_type=SearchType.BID,
            filters=filters,
            sort_order=sort_order,
            page=page,
            page_size=size
        )

        return results.get("bid_results", {})

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"입찰공고 검색 실패: {str(e)}")
    finally:
        if 'search_service' in locals():
            search_service.close()


@router.get("/documents")
async def search_documents(
    q: str = Query(..., description="검색어", min_length=1),
    file_type: Optional[str] = Query(None, description="파일 타입 (hwp/pdf/doc)"),
    sort: str = Query("relevance", description="정렬 순서"),
    page: int = Query(1, ge=1, description="페이지 번호"),
    size: int = Query(20, ge=1, le=100, description="페이지 크기"),
    db: Session = Depends(get_db)
):
    """
    문서 검색

    - 처리된 문서(MD 파일) 검색
    - 파일 타입별 필터링 가능
    """
    try:
        # 정렬 순서 변환
        sort_order_map = {
            "relevance": SortOrder.RELEVANCE,
            "date_desc": SortOrder.DATE_DESC,
            "date_asc": SortOrder.DATE_ASC
        }
        sort_order = sort_order_map.get(sort.lower(), SortOrder.RELEVANCE)

        # 필터 구성
        filters = {}
        if file_type:
            filters["file_type"] = file_type

        # 검색 서비스 호출
        search_service = SearchService(db)
        results = await search_service.search(
            query=q,
            search_type=SearchType.DOCUMENT,
            filters=filters,
            sort_order=sort_order,
            page=page,
            page_size=size
        )

        return results.get("document_results", {})

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"문서 검색 실패: {str(e)}")
    finally:
        if 'search_service' in locals():
            search_service.close()


@router.get("/companies")
async def search_companies(
    q: str = Query(..., description="검색어", min_length=1),
    industry: Optional[str] = Query(None, description="산업 분야"),
    region: Optional[str] = Query(None, description="지역"),
    page: int = Query(1, ge=1, description="페이지 번호"),
    size: int = Query(20, ge=1, le=100, description="페이지 크기"),
    db: Session = Depends(get_db)
):
    """
    기업 정보 검색

    - 등록된 기업 정보 검색
    - 산업 분야 및 지역별 필터링
    """
    try:
        # 필터 구성
        filters = {}
        if industry:
            filters["industry"] = industry
        if region:
            filters["region"] = region

        # 검색 서비스 호출
        search_service = SearchService(db)
        results = await search_service.search(
            query=q,
            search_type=SearchType.COMPANY,
            filters=filters,
            sort_order=SortOrder.RELEVANCE,
            page=page,
            page_size=size
        )

        return results.get("company_results", {})

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"기업 검색 실패: {str(e)}")
    finally:
        if 'search_service' in locals():
            search_service.close()


@router.get("/suggest")
async def suggest(
    q: str = Query(..., description="검색어", min_length=2),
    limit: int = Query(10, ge=1, le=20, description="제안 개수"),
    db: Session = Depends(get_db)
):
    """
    검색어 자동완성

    - 입력한 검색어에 대한 자동완성 제안
    - 최대 20개까지 제안
    """
    try:
        search_service = SearchService(db)
        suggestions = await search_service.suggest(q, limit)

        return {
            "query": q,
            "suggestions": suggestions,
            "count": len(suggestions)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"자동완성 실패: {str(e)}")
    finally:
        if 'search_service' in locals():
            search_service.close()


@router.get("/facets")
async def get_facets(
    q: Optional[str] = Query(None, description="검색어"),
    db: Session = Depends(get_db)
):
    """
    검색 패싯(필터 옵션) 조회

    - 기관별, 상태별, 가격대별 분포
    - 검색 결과 필터링을 위한 옵션 제공
    """
    try:
        search_service = SearchService(db)

        # 패싯 정보만 가져오기
        results = await search_service.search(
            query=q or "",
            search_type=SearchType.BID,
            page=1,
            page_size=1  # 패싯만 필요하므로 최소 결과
        )

        return {
            "query": q,
            "facets": results.get("facets", {})
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"패싯 조회 실패: {str(e)}")
    finally:
        if 'search_service' in locals():
            search_service.close()