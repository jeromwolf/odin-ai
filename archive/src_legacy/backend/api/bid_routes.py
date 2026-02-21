"""
입찰공고 관련 API 엔드포인트
"""

from fastapi import APIRouter, Query, HTTPException, BackgroundTasks
from typing import Optional, List
from datetime import datetime, timedelta
from pydantic import BaseModel, Field

from backend.services.public_data_client import public_data_client

router = APIRouter(prefix="/api/bids", tags=["입찰공고"])


class BidSearchParams(BaseModel):
    """입찰공고 검색 파라미터"""
    keyword: Optional[str] = Field(None, description="검색 키워드")
    inst_name: Optional[str] = Field(None, description="기관명")
    start_date: Optional[str] = Field(None, description="시작일 (YYYYMMDD)")
    end_date: Optional[str] = Field(None, description="종료일 (YYYYMMDD)")
    min_price: Optional[int] = Field(None, description="최소 가격")
    max_price: Optional[int] = Field(None, description="최대 가격")
    page: int = Field(1, ge=1, description="페이지 번호")
    size: int = Field(20, ge=1, le=100, description="페이지 크기")


class BidResponse(BaseModel):
    """입찰공고 응답 모델"""
    bid_notice_no: str
    bid_notice_name: str
    notice_inst_name: str
    bid_method: Optional[str]
    contract_type: Optional[str]
    bid_close_date_time: Optional[str]
    bid_open_date_time: Optional[str]
    pre_price: Optional[int]
    bid_notice_date: Optional[str]
    documents_count: int = 0
    created_at: datetime


class CollectionRequest(BaseModel):
    """데이터 수집 요청 모델"""
    source: str = Field("api", description="데이터 소스 (api/web/both)")
    max_items: int = Field(100, ge=1, le=500, description="최대 수집 개수")
    start_date: Optional[str] = Field(None, description="시작일 (YYYYMMDD)")
    end_date: Optional[str] = Field(None, description="종료일 (YYYYMMDD)")


@router.get("/search", response_model=List[BidResponse])
async def search_bids(
    keyword: Optional[str] = Query(None, description="검색 키워드"),
    inst_name: Optional[str] = Query(None, description="기관명"),
    start_date: Optional[str] = Query(None, description="시작일 (YYYYMMDD)"),
    end_date: Optional[str] = Query(None, description="종료일 (YYYYMMDD)"),
    min_price: Optional[int] = Query(None, description="최소 가격"),
    max_price: Optional[int] = Query(None, description="최대 가격"),
    page: int = Query(1, ge=1, description="페이지 번호"),
    size: int = Query(20, ge=1, le=100, description="페이지 크기")
):
    """
    입찰공고 검색

    - keyword: 공고명 또는 내용 검색
    - inst_name: 발주기관명
    - start_date, end_date: 공고일 범위
    - min_price, max_price: 예정가격 범위
    """
    try:
        # 날짜 기본값 설정
        if not start_date:
            start_date = (datetime.now() - timedelta(days=30)).strftime("%Y%m%d")
        if not end_date:
            end_date = datetime.now().strftime("%Y%m%d")

        # API 호출
        params = {
            "numOfRows": size,
            "pageNo": page,
            "inqryBgnDt": start_date + "0000",
            "inqryEndDt": end_date + "2359",
            "type": "json"
        }

        # 기관명 필터
        if inst_name:
            params["dminsttNm"] = inst_name

        # API 호출 (여러 타입 시도)
        all_results = []

        for service_type in ["공사", "용역", "물품"]:
            try:
                response = await public_data_client.get_bid_announcements(
                    service_type=service_type,
                    **params
                )

                if response.get("items"):
                    items = response["items"]

                    # 키워드 필터링
                    if keyword:
                        items = [
                            item for item in items
                            if keyword.lower() in item.get("bidNtceNm", "").lower()
                            or keyword.lower() in item.get("ntceInsttNm", "").lower()
                        ]

                    # 가격 필터링
                    if min_price or max_price:
                        filtered_items = []
                        for item in items:
                            try:
                                price = int(item.get("presmptPrce", 0))
                                if min_price and price < min_price:
                                    continue
                                if max_price and price > max_price:
                                    continue
                                filtered_items.append(item)
                            except (ValueError, TypeError):
                                continue
                        items = filtered_items

                    all_results.extend(items)

            except Exception as e:
                print(f"{service_type} 조회 실패: {e}")
                continue

        # 응답 변환
        bid_responses = []
        for item in all_results[:size]:  # 페이지 크기만큼만 반환
            try:
                bid_responses.append(BidResponse(
                    bid_notice_no=item.get("bidNtceNo", ""),
                    bid_notice_name=item.get("bidNtceNm", ""),
                    notice_inst_name=item.get("ntceInsttNm", ""),
                    bid_method=item.get("bidMethdNm", ""),
                    contract_type=item.get("cntrctCnclsMthdNm", ""),
                    bid_close_date_time=item.get("bidClseDt", ""),
                    bid_open_date_time=item.get("bidOpenDt", ""),
                    pre_price=int(item.get("presmptPrce", 0)) if item.get("presmptPrce") else None,
                    bid_notice_date=item.get("bidNtceDt", ""),
                    documents_count=len(item.get("documents", [])) if item.get("documents") else 0,
                    created_at=datetime.now()
                ))
            except Exception as e:
                print(f"항목 변환 실패: {e}")
                continue

        return bid_responses

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"검색 실패: {str(e)}")


@router.post("/collect")
async def collect_bid_data(
    request: CollectionRequest,
    background_tasks: BackgroundTasks
):
    """
    입찰공고 데이터 수집 요청

    실제 수집은 별도의 collector 프로그램에서 처리됩니다.
    이 API는 수집 요청을 받아 collector 서비스에 전달하는 역할만 합니다.
    """
    try:
        # TODO: collector 서비스와 통신하여 수집 작업 요청
        # 예: HTTP API 호출 또는 메시지 큐를 통한 작업 전달

        return {
            "message": "데이터 수집 요청이 collector 서비스에 전달되었습니다.",
            "source": request.source,
            "max_items": request.max_items,
            "status": "requested",
            "note": "실제 수집은 별도의 collector 프로그램에서 처리됩니다."
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"수집 요청 실패: {str(e)}")


@router.get("/{bid_notice_no}")
async def get_bid_detail(bid_notice_no: str):
    """
    입찰공고 상세 조회

    - bid_notice_no: 입찰공고번호
    """
    try:
        # TODO: 데이터베이스에서 조회
        # 임시로 API에서 직접 조회
        params = {
            "numOfRows": 100,
            "pageNo": 1,
            "type": "json"
        }

        for service_type in ["공사", "용역", "물품"]:
            try:
                response = await public_data_client.get_bid_announcements(
                    service_type=service_type,
                    **params
                )

                if response.get("items"):
                    for item in response["items"]:
                        if item.get("bidNtceNo") == bid_notice_no:
                            return {
                                "bid_notice_no": item.get("bidNtceNo", ""),
                                "bid_notice_name": item.get("bidNtceNm", ""),
                                "notice_inst_name": item.get("ntceInsttNm", ""),
                                "bid_method": item.get("bidMethdNm", ""),
                                "contract_type": item.get("cntrctCnclsMthdNm", ""),
                                "bid_close_date_time": item.get("bidClseDt", ""),
                                "bid_open_date_time": item.get("bidOpenDt", ""),
                                "pre_price": int(item.get("presmptPrce", 0)) if item.get("presmptPrce") else None,
                                "bid_notice_date": item.get("bidNtceDt", ""),
                                "raw_data": item  # 원본 데이터 포함
                            }
            except:
                continue

        raise HTTPException(status_code=404, detail="입찰공고를 찾을 수 없습니다.")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"조회 실패: {str(e)}")


@router.get("/stats/summary")
async def get_bid_statistics():
    """
    입찰공고 통계 요약

    최근 30일간 입찰공고 통계 정보 제공
    """
    try:
        # 최근 30일 데이터
        start_date = (datetime.now() - timedelta(days=30)).strftime("%Y%m%d")
        end_date = datetime.now().strftime("%Y%m%d")

        stats = {
            "period": {
                "start_date": start_date,
                "end_date": end_date
            },
            "total_count": 0,
            "by_type": {},
            "by_method": {},
            "price_ranges": {
                "under_10m": 0,
                "10m_50m": 0,
                "50m_100m": 0,
                "100m_500m": 0,
                "over_500m": 0
            }
        }

        # 각 서비스 타입별 통계
        for service_type in ["공사", "용역", "물품"]:
            try:
                response = await public_data_client.get_bid_announcements(
                    service_type=service_type,
                    numOfRows=100,
                    pageNo=1,
                    inqryBgnDt=start_date + "0000",
                    inqryEndDt=end_date + "2359",
                    type="json"
                )

                if response.get("totalCount"):
                    count = response["totalCount"]
                    stats["total_count"] += count
                    stats["by_type"][service_type] = count

                    # 입찰 방법별 통계
                    if response.get("items"):
                        for item in response["items"]:
                            method = item.get("bidMethdNm", "기타")
                            stats["by_method"][method] = stats["by_method"].get(method, 0) + 1

                            # 가격대별 통계
                            try:
                                price = int(item.get("presmptPrce", 0))
                                if price < 10000000:
                                    stats["price_ranges"]["under_10m"] += 1
                                elif price < 50000000:
                                    stats["price_ranges"]["10m_50m"] += 1
                                elif price < 100000000:
                                    stats["price_ranges"]["50m_100m"] += 1
                                elif price < 500000000:
                                    stats["price_ranges"]["100m_500m"] += 1
                                else:
                                    stats["price_ranges"]["over_500m"] += 1
                            except:
                                pass

            except Exception as e:
                print(f"{service_type} 통계 실패: {e}")
                continue

        return stats

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"통계 조회 실패: {str(e)}")


@router.get("/users")
async def search_users(
    page: int = Query(1, ge=1, description="페이지 번호"),
    size: int = Query(20, ge=1, le=100, description="페이지 크기")
):
    """
    조달업체 및 수요기관 정보 조회

    - 등록된 업체 정보 조회
    - 수요기관 정보 확인
    """
    try:
        from loguru import logger

        response = await public_data_client.get_user_info(
            page=page,
            size=size
        )

        return response.get("items", [])

    except Exception as e:
        logger.error(f"사용자 정보 조회 실패: {e}")
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


@router.get("/contracts")
async def search_contracts(
    start_date: str = Query(None, description="계약시작일 (YYYYMMDD)"),
    end_date: str = Query(None, description="계약종료일 (YYYYMMDD)"),
    page: int = Query(1, ge=1, description="페이지 번호"),
    size: int = Query(20, ge=1, le=100, description="페이지 크기")
):
    """
    계약정보 조회

    - 체결된 계약 정보
    - 계약금액, 업체 정보 등
    """
    try:
        from loguru import logger

        # 기본 날짜 설정 (최근 30일)
        if not end_date:
            end_date = datetime.now().strftime("%Y%m%d")
        if not start_date:
            start_date = (datetime.now() - timedelta(days=30)).strftime("%Y%m%d")

        response = await public_data_client.get_contract_info(
            page=page,
            size=size,
            start_date=start_date + "0000",
            end_date=end_date + "2359"
        )

        return response.get("items", [])

    except Exception as e:
        logger.error(f"계약정보 조회 실패: {e}")
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


@router.get("/success")
async def search_bid_success(
    start_date: str = Query(None, description="낙찰시작일 (YYYYMMDD)"),
    end_date: str = Query(None, description="낙찰종료일 (YYYYMMDD)"),
    page: int = Query(1, ge=1, description="페이지 번호"),
    size: int = Query(20, ge=1, le=100, description="페이지 크기")
):
    """
    낙찰정보 조회

    - 낙찰 결과 정보
    - 낙찰업체, 낙찰금액 등
    """
    try:
        from loguru import logger

        # 기본 날짜 설정 (최근 30일)
        if not end_date:
            end_date = datetime.now().strftime("%Y%m%d")
        if not start_date:
            start_date = (datetime.now() - timedelta(days=30)).strftime("%Y%m%d")

        response = await public_data_client.get_bid_success_info(
            page=page,
            size=size,
            start_date=start_date + "0000",
            end_date=end_date + "2359"
        )

        return response.get("items", [])

    except Exception as e:
        logger.error(f"낙찰정보 조회 실패: {e}")
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


@router.get("/pre-specs")
async def search_pre_specs(
    page: int = Query(1, ge=1, description="페이지 번호"),
    size: int = Query(20, ge=1, le=100, description="페이지 크기")
):
    """
    사전규격정보 조회

    - 사전규격서 정보
    - 규격 공개 전 사전 검토 가능
    """
    try:
        from loguru import logger

        response = await public_data_client.get_pre_spec_info(
            page=page,
            size=size
        )

        return response.get("items", [])

    except Exception as e:
        logger.error(f"사전규격정보 조회 실패: {e}")
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )