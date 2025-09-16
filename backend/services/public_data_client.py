"""
공공데이터포털 API 클라이언트
나라장터(G2B) 관련 API 서비스 통합 클라이언트
"""

import asyncio
import httpx
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import json
from backend.core.config import settings
from loguru import logger
import xml.etree.ElementTree as ET


class PublicDataAPIClient:
    """공공데이터포털 API 클라이언트"""

    # API 서비스 URL 매핑 (실제 API URL 기준 수정)
    API_SERVICES = {
        "bid_construction": {
            "name": "조달청 나라장터 입찰공고정보서비스 (공사)",
            "url": "http://apis.data.go.kr/1230000/ad/BidPublicInfoService/getBidPblancListInfoCnstwk",
            "description": "입찰공고 목록 조회 (공사)",
            "required_params": ["inqryDiv", "inqryBgnDt", "inqryEndDt"],
            "keywords": ["나라장터", "입찰", "입찰공고", "공사"]
        },
        "bid_success": {
            "name": "조달청 나라장터 낙찰정보서비스",
            "url": "http://apis.data.go.kr/1230000/as/ScsbidInfoService/getScsbidListSttusCnstwk",
            "description": "낙찰업체 및 계약 정보 조회",
            "required_params": ["inqryDiv", "inqryBgnDt", "inqryEndDt"],
            "keywords": ["나라장터", "낙찰", "정보", "순위", "예가기법", "물품", "공사", "용역"]
        },
        "contract_info": {
            "name": "조달청 나라장터 계약정보서비스",
            "url": "http://apis.data.go.kr/1230000/ao/CntrctInfoService/getCntrctInfoListCnstwk",
            "description": "계약 체결 정보 조회",
            "required_params": ["inqryDiv", "inqryBgnDt", "inqryEndDt"],
            "keywords": ["나라장터", "계약", "정보", "물품", "용역", "공사", "의자"]
        },
        "pre_spec": {
            "name": "조달청 나라장터 사전규격정보서비스",
            "url": "http://apis.data.go.kr/1230000/ao/HrcspSsstndrdInfoService/getPublicPrcureThngInfoServc",
            "description": "사전규격서 정보 조회",
            "required_params": ["inqryDiv", "inqryBgnDt", "inqryEndDt"],
            "keywords": ["사전규격", "정보", "물품", "용역", "의자", "공사", "나라장터"]
        },
        "user_info": {
            "name": "조달청 나라장터 사용자정보 서비스",
            "url": "http://apis.data.go.kr/1230000/ao/UsrInfoService/getPrcrmntCorpBasicInfo",
            "description": "조달업체 및 수요기관 정보 조회",
            "required_params": ["inqryDiv", "inqryBgnDt", "inqryEndDt"],
            "keywords": ["나라장터", "사용자", "정보", "기관", "업체", "업종", "물품", "소관"]
        }
    }

    def __init__(self):
        """클라이언트 초기화"""
        self.api_key = settings.PUBLIC_DATA_API_KEY
        self.base_timeout = 30.0
        self.max_retries = 3
        self.retry_delay = 2.0

        # Rate limiting 설정 (시간당 800건으로 제한)
        self.request_interval = 4.5  # 초 (3600/800 = 4.5초)
        self.last_request_time = 0

        logger.info("PublicDataAPIClient 초기화 완료")

    async def _wait_for_rate_limit(self):
        """Rate limiting 대기"""
        current_time = datetime.now().timestamp()
        time_diff = current_time - self.last_request_time

        if time_diff < self.request_interval:
            wait_time = self.request_interval - time_diff
            logger.debug(f"Rate limiting: {wait_time:.2f}초 대기")
            await asyncio.sleep(wait_time)

        self.last_request_time = datetime.now().timestamp()

    async def _make_request(
        self,
        service_key: str,
        params: Dict[str, Any],
        timeout: Optional[float] = None
    ) -> Dict[str, Any]:
        """API 요청 실행 (재시도 로직 포함)"""

        if service_key not in self.API_SERVICES:
            raise ValueError(f"지원하지 않는 서비스: {service_key}")

        service = self.API_SERVICES[service_key]
        url = service["url"]

        # 기본 매개변수 설정
        default_params = {
            "serviceKey": self.api_key,
            "numOfRows": 100,  # 기본 100건
            "pageNo": 1,
            "type": "json"  # JSON 형식으로 응답
        }

        # 매개변수 병합
        request_params = {**default_params, **params}

        # Rate limiting 적용
        await self._wait_for_rate_limit()

        # 재시도 로직
        last_exception = None
        for attempt in range(self.max_retries):
            try:
                async with httpx.AsyncClient(timeout=timeout or self.base_timeout) as client:
                    logger.debug(f"API 요청: {service['name']} (시도: {attempt + 1})")

                    response = await client.get(url, params=request_params)
                    response.raise_for_status()

                    # 응답 처리
                    result = await self._process_response(response, service_key)

                    logger.info(f"{service['name']} 요청 성공 (시도: {attempt + 1})")
                    return result

            except httpx.HTTPStatusError as e:
                last_exception = e
                logger.warning(f"HTTP 오류 (시도: {attempt + 1}): {e.response.status_code}")

                # 429 (Too Many Requests)인 경우 더 오래 대기
                if e.response.status_code == 429:
                    wait_time = self.retry_delay * (2 ** attempt)  # 지수 백오프
                    logger.warning(f"Rate limit 초과, {wait_time}초 대기 후 재시도")
                    await asyncio.sleep(wait_time)
                    continue

                # 4xx 오류는 재시도 안함
                if 400 <= e.response.status_code < 500:
                    break

            except (httpx.RequestError, httpx.TimeoutException) as e:
                last_exception = e
                logger.warning(f"네트워크 오류 (시도: {attempt + 1}): {e}")

            # 재시도 전 대기
            if attempt < self.max_retries - 1:
                wait_time = self.retry_delay * (attempt + 1)
                await asyncio.sleep(wait_time)

        # 모든 재시도 실패
        logger.error(f"{service['name']} 요청 실패: {last_exception}")
        raise last_exception

    async def _process_response(self, response: httpx.Response, service_key: str) -> Dict[str, Any]:
        """API 응답 처리 및 정규화"""

        content_type = response.headers.get("content-type", "").lower()

        try:
            # JSON 응답 처리
            if "application/json" in content_type:
                data = response.json()
                return self._normalize_json_response(data, service_key)

            # XML 응답 처리 (fallback)
            elif "application/xml" in content_type or "text/xml" in content_type:
                xml_data = response.text
                return self._parse_xml_response(xml_data, service_key)

            # 일반 텍스트 응답 (JSON으로 파싱 시도)
            else:
                try:
                    data = response.json()
                    return self._normalize_json_response(data, service_key)
                except json.JSONDecodeError:
                    # XML로 파싱 시도
                    return self._parse_xml_response(response.text, service_key)

        except Exception as e:
            logger.error(f"응답 처리 오류: {e}")
            logger.debug(f"응답 내용: {response.text[:500]}...")
            raise

    def _normalize_json_response(self, data: Dict[str, Any], service_key: str) -> Dict[str, Any]:
        """JSON 응답 정규화"""

        # 공통 응답 구조 확인
        if "response" in data:
            response_data = data["response"]

            # 헤더 정보
            header = response_data.get("header", {})
            result_code = header.get("resultCode", "")
            result_msg = header.get("resultMsg", "")

            # 오류 처리
            if result_code != "00":
                error_msg = f"API 오류 [{result_code}]: {result_msg}"
                logger.error(error_msg)
                raise Exception(error_msg)

            # 바디 데이터
            body = response_data.get("body", {})
            items = body.get("items", [])
            total_count = body.get("totalCount", 0)

            return {
                "success": True,
                "total_count": total_count,
                "items": items,
                "service": service_key,
                "timestamp": datetime.now().isoformat()
            }

        # 비표준 응답 구조
        return {
            "success": True,
            "raw_data": data,
            "service": service_key,
            "timestamp": datetime.now().isoformat()
        }

    def _parse_xml_response(self, xml_text: str, service_key: str) -> Dict[str, Any]:
        """XML 응답 파싱"""
        try:
            root = ET.fromstring(xml_text)

            # XML을 딕셔너리로 변환
            def xml_to_dict(element):
                result = {}
                for child in element:
                    if len(child) == 0:
                        result[child.tag] = child.text
                    else:
                        result[child.tag] = xml_to_dict(child)
                return result

            data = xml_to_dict(root)
            return {
                "success": True,
                "xml_data": data,
                "service": service_key,
                "timestamp": datetime.now().isoformat()
            }

        except ET.ParseError as e:
            logger.error(f"XML 파싱 오류: {e}")
            return {
                "success": False,
                "error": f"XML 파싱 실패: {e}",
                "raw_text": xml_text[:500],
                "service": service_key,
                "timestamp": datetime.now().isoformat()
            }

    # === 주요 API 메서드 ===

    async def get_bid_construction_list(
        self,
        page: int = 1,
        size: int = 10,
        inquiry_div: str = "1",
        start_date: str = "202001010000",
        end_date: str = "202012312359",
        bid_notice_no: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """입찰공고 목록 조회 (공사)

        Args:
            page: 페이지 번호 (1부터 시작)
            size: 페이지 크기 (최대 999)
            inquiry_div: 조회구분 (1:전체, 2:공고중, 3:마감)
            start_date: 조회시작일시 (YYYYMMDDHHMM)
            end_date: 조회종료일시 (YYYYMMDDHHMM)
            bid_notice_no: 입찰공고번호 (선택)
            **kwargs: 추가 매개변수
        """

        params = {
            "pageNo": page,
            "numOfRows": min(size, 999),
            "inqryDiv": inquiry_div,
            "inqryBgnDt": start_date,
            "inqryEndDt": end_date,
            "type": "json",
            **kwargs
        }

        # 특정 공고번호 조회
        if bid_notice_no:
            params["bidNtceNo"] = bid_notice_no

        return await self._make_request("bid_construction", params)

    async def get_bid_detail(self, bid_notice_no: str, bid_notice_ord: str = "01") -> Dict[str, Any]:
        """입찰공고 상세 정보 조회

        Args:
            bid_notice_no: 입찰공고번호
            bid_notice_ord: 입찰공고차수 (기본값: "01")
        """

        params = {
            "bidNtceNo": bid_notice_no,
            "bidNtceOrd": bid_notice_ord
        }

        return await self._make_request("bid_detail", params)

    async def get_contract_info(
        self,
        page: int = 1,
        size: int = 100,
        inquiry_div: str = "1",
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        contract_no: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """계약 정보 조회

        Args:
            page: 페이지 번호
            size: 페이지 크기
            inquiry_div: 조회구분 (1:전체)
            start_date: 조회시작일시 (YYYYMMDDHHMM)
            end_date: 조회종료일시 (YYYYMMDDHHMM)
            contract_no: 통합계약번호 (선택)
        """

        # 기본 날짜 설정
        if not start_date:
            start_date = (datetime.now() - timedelta(days=30)).strftime("%Y%m%d0000")
        if not end_date:
            end_date = datetime.now().strftime("%Y%m%d2359")

        params = {
            "pageNo": page,
            "numOfRows": min(size, 999),
            "inqryDiv": inquiry_div,
            "inqryBgnDt": start_date,
            "inqryEndDt": end_date,
            **kwargs
        }

        if contract_no:
            params["untyCntrctNo"] = contract_no

        return await self._make_request("contract_info", params)

    async def get_pre_spec_info(
        self,
        page: int = 1,
        size: int = 100,
        inquiry_div: str = "1",
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        spec_reg_no: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """사전규격서 정보 조회

        Args:
            page: 페이지 번호
            size: 페이지 크기
            inquiry_div: 조회구분 (1:전체)
            start_date: 조회시작일시 (YYYYMMDDHHMM)
            end_date: 조회종료일시 (YYYYMMDDHHMM)
            spec_reg_no: 사전규격등록번호 (선택)
        """

        # 기본 날짜 설정
        if not start_date:
            start_date = (datetime.now() - timedelta(days=30)).strftime("%Y%m%d0000")
        if not end_date:
            end_date = datetime.now().strftime("%Y%m%d2359")

        params = {
            "pageNo": page,
            "numOfRows": min(size, 999),
            "inqryDiv": inquiry_div,
            "inqryBgnDt": start_date,
            "inqryEndDt": end_date,
            **kwargs
        }

        if spec_reg_no:
            params["bfSpecRgstNo"] = spec_reg_no

        return await self._make_request("pre_spec", params)

    async def get_bid_success_info(
        self,
        page: int = 1,
        size: int = 100,
        inquiry_div: str = "1",
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        bid_notice_no: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """낙찰정보 조회

        Args:
            page: 페이지 번호
            size: 페이지 크기
            inquiry_div: 조회구분 (1:전체, 2:진행중, 3:완료)
            start_date: 조회시작일시 (YYYYMMDDHHMM)
            end_date: 조회종료일시 (YYYYMMDDHHMM)
            bid_notice_no: 입찰공고번호 (선택)
        """

        # 기본 날짜 설정
        if not start_date:
            start_date = (datetime.now() - timedelta(days=30)).strftime("%Y%m%d0000")
        if not end_date:
            end_date = datetime.now().strftime("%Y%m%d2359")

        params = {
            "pageNo": page,
            "numOfRows": min(size, 999),
            "inqryDiv": inquiry_div,
            "inqryBgnDt": start_date,
            "inqryEndDt": end_date,
            **kwargs
        }

        if bid_notice_no:
            params["bidNtceNo"] = bid_notice_no

        return await self._make_request("bid_success", params)

    async def get_user_info(
        self,
        page: int = 1,
        size: int = 100,
        inquiry_div: str = "1",
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        corp_name: Optional[str] = None,
        biz_no: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """조달업체 및 수요기관 정보 조회

        Args:
            page: 페이지 번호
            size: 페이지 크기
            inquiry_div: 조회구분 (1:전체)
            start_date: 조회시작일시 (YYYYMMDDHHMM)
            end_date: 조회종료일시 (YYYYMMDDHHMM)
            corp_name: 업체명 (선택)
            biz_no: 사업자번호 (선택)
        """

        # 기본 날짜 설정
        if not start_date:
            start_date = (datetime.now() - timedelta(days=365)).strftime("%Y%m%d0000")
        if not end_date:
            end_date = datetime.now().strftime("%Y%m%d2359")

        params = {
            "pageNo": page,
            "numOfRows": min(size, 999),
            "inqryDiv": inquiry_div,
            "inqryBgnDt": start_date,
            "inqryEndDt": end_date,
            **kwargs
        }

        if corp_name:
            params["corpNm"] = corp_name
        if biz_no:
            params["bizno"] = biz_no

        return await self._make_request("user_info", params)

    # === 편의 메서드 ===

    async def search_recent_bids(self, days: int = 7, keywords: Optional[List[str]] = None) -> Dict[str, Any]:
        """최근 며칠간의 입찰공고 검색"""

        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        date_from = start_date.strftime("%Y%m%d")
        date_to = end_date.strftime("%Y%m%d")

        result = await self.get_bid_announcements(
            bid_notice_date_from=date_from,
            bid_notice_date_to=date_to,
            numOfRows=999  # 최대한 많이 가져오기
        )

        # 키워드 필터링 (클라이언트 사이드)
        if keywords and result.get("items"):
            filtered_items = []
            for item in result["items"]:
                bid_name = item.get("bidNtceNm", "").lower()
                if any(keyword.lower() in bid_name for keyword in keywords):
                    filtered_items.append(item)

            result["items"] = filtered_items
            result["filtered_count"] = len(filtered_items)
            result["filter_keywords"] = keywords

        return result

    async def test_connection(self) -> Dict[str, Any]:
        """API 연결 테스트"""

        try:
            # 최소한의 요청으로 연결 테스트
            result = await self.get_bid_announcements(page=1, size=1)

            return {
                "success": True,
                "message": "API 연결 성공",
                "api_key_valid": True,
                "test_result": result
            }

        except Exception as e:
            return {
                "success": False,
                "message": f"API 연결 실패: {e}",
                "api_key_valid": False,
                "error": str(e)
            }


# 싱글톤 인스턴스
public_data_client = PublicDataAPIClient()