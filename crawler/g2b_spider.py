"""
나라장터(G2B) 웹 크롤러
공공데이터포털 API로 수집하지 못하는 추가 정보를 크롤링
"""

import asyncio
import aiohttp
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import json
import random
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import time
from loguru import logger

class G2BSpider:
    """나라장터 크롤러"""

    BASE_URL = "https://www.g2b.go.kr"

    # 입찰공고 목록 URL
    BID_LIST_URL = "https://www.g2b.go.kr/bid/bids"

    # User-Agent 로테이션
    USER_AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15"
    ]

    def __init__(self):
        """크롤러 초기화"""
        self.session = None
        self.request_count = 0
        self.last_request_time = 0
        self.min_delay = 2.0  # 최소 요청 간격 (초)
        self.max_delay = 5.0  # 최대 요청 간격 (초)

        logger.info("G2B 크롤러 초기화")

    async def __aenter__(self):
        """비동기 컨텍스트 진입"""
        headers = {
            "User-Agent": random.choice(self.USER_AGENTS),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "ko-KR,ko;q=0.9,en;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1"
        }

        timeout = aiohttp.ClientTimeout(total=30)
        self.session = aiohttp.ClientSession(
            headers=headers,
            timeout=timeout
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """비동기 컨텍스트 종료"""
        if self.session:
            await self.session.close()

    async def _wait_between_requests(self):
        """요청 간 대기 시간 적용"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time

        if time_since_last < self.min_delay:
            delay = random.uniform(self.min_delay, self.max_delay)
            await asyncio.sleep(delay - time_since_last)

        self.last_request_time = time.time()

    async def _make_request(self, url: str, params: Optional[Dict] = None) -> Optional[str]:
        """HTTP 요청 실행"""
        await self._wait_between_requests()

        try:
            self.request_count += 1

            # User-Agent 로테이션
            if self.request_count % 10 == 0:
                self.session.headers["User-Agent"] = random.choice(self.USER_AGENTS)

            logger.debug(f"요청 #{self.request_count}: {url}")

            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    return await response.text()
                else:
                    logger.warning(f"HTTP {response.status} 응답: {url}")
                    return None

        except asyncio.TimeoutError:
            logger.error(f"요청 타임아웃: {url}")
            return None
        except Exception as e:
            logger.error(f"요청 실패: {e}")
            return None

    def _parse_bid_list(self, html: str) -> List[Dict[str, Any]]:
        """입찰공고 목록 파싱"""
        soup = BeautifulSoup(html, 'html.parser')
        bids = []

        # 테이블 찾기
        bid_table = soup.find('table', {'class': 'table_list'})
        if not bid_table:
            logger.warning("입찰공고 테이블을 찾을 수 없습니다")
            return bids

        # 각 행 파싱
        rows = bid_table.find_all('tr')[1:]  # 헤더 제외
        for row in rows:
            cols = row.find_all('td')
            if len(cols) < 7:
                continue

            try:
                bid_info = {
                    "순번": cols[0].get_text(strip=True),
                    "공고번호": cols[1].get_text(strip=True),
                    "공고명": cols[2].get_text(strip=True),
                    "공고기관": cols[3].get_text(strip=True),
                    "입찰마감일시": cols[4].get_text(strip=True),
                    "예정가격": cols[5].get_text(strip=True),
                    "공고상태": cols[6].get_text(strip=True),
                    "상세URL": None
                }

                # 상세 링크 추출
                link = cols[2].find('a')
                if link and link.get('href'):
                    bid_info["상세URL"] = urljoin(self.BASE_URL, link['href'])

                bids.append(bid_info)

            except Exception as e:
                logger.error(f"행 파싱 실패: {e}")
                continue

        return bids

    def _parse_bid_detail(self, html: str) -> Dict[str, Any]:
        """입찰공고 상세 정보 파싱"""
        soup = BeautifulSoup(html, 'html.parser')
        detail = {}

        # 기본 정보 테이블 파싱
        info_tables = soup.find_all('table', {'class': 'table_info'})

        for table in info_tables:
            rows = table.find_all('tr')
            for row in rows:
                th = row.find('th')
                td = row.find('td')

                if th and td:
                    key = th.get_text(strip=True).replace(':', '')
                    value = td.get_text(strip=True)
                    detail[key] = value

        # 첨부파일 정보
        attachments = []
        file_list = soup.find('div', {'class': 'file_list'})
        if file_list:
            links = file_list.find_all('a')
            for link in links:
                if link.get('href'):
                    attachments.append({
                        "파일명": link.get_text(strip=True),
                        "URL": urljoin(self.BASE_URL, link['href'])
                    })

        detail["첨부파일"] = attachments

        return detail

    async def crawl_bid_list(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        max_pages: int = 5
    ) -> List[Dict[str, Any]]:
        """입찰공고 목록 크롤링

        Args:
            start_date: 시작일 (YYYY-MM-DD)
            end_date: 종료일 (YYYY-MM-DD)
            max_pages: 최대 페이지 수

        Returns:
            입찰공고 목록
        """
        all_bids = []

        # 기본 날짜 설정
        if not end_date:
            end_date = datetime.now().strftime("%Y-%m-%d")
        if not start_date:
            start_date = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")

        for page in range(1, max_pages + 1):
            params = {
                "searchType": "1",
                "bidNm": "",
                "searchDtType": "1",
                "fromBidDt": start_date,
                "toBidDt": end_date,
                "fromOpenBidDt": "",
                "toOpenBidDt": "",
                "currentPageNo": str(page)
            }

            html = await self._make_request(self.BID_LIST_URL, params)
            if not html:
                logger.warning(f"페이지 {page} 크롤링 실패")
                continue

            bids = self._parse_bid_list(html)
            if not bids:
                logger.info(f"페이지 {page}에 더 이상 공고가 없습니다")
                break

            all_bids.extend(bids)
            logger.info(f"페이지 {page}: {len(bids)}건 수집")

            # 과도한 요청 방지
            if page < max_pages:
                await asyncio.sleep(random.uniform(3, 5))

        return all_bids

    async def crawl_bid_detail(self, detail_url: str) -> Optional[Dict[str, Any]]:
        """입찰공고 상세 정보 크롤링

        Args:
            detail_url: 상세 페이지 URL

        Returns:
            상세 정보 딕셔너리
        """
        html = await self._make_request(detail_url)
        if not html:
            return None

        return self._parse_bid_detail(html)

    async def crawl_with_details(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        max_items: int = 10
    ) -> List[Dict[str, Any]]:
        """입찰공고 목록과 상세 정보를 함께 크롤링

        Args:
            start_date: 시작일
            end_date: 종료일
            max_items: 최대 수집 개수

        Returns:
            상세 정보가 포함된 입찰공고 리스트
        """
        # 목록 크롤링
        bids = await self.crawl_bid_list(start_date, end_date, max_pages=3)

        # 상세 정보 수집
        detailed_bids = []
        for i, bid in enumerate(bids[:max_items]):
            if bid.get("상세URL"):
                logger.info(f"상세 정보 수집 중... ({i+1}/{min(len(bids), max_items)})")

                detail = await self.crawl_bid_detail(bid["상세URL"])
                if detail:
                    bid.update(detail)

                detailed_bids.append(bid)

                # 과도한 요청 방지
                if i < min(len(bids), max_items) - 1:
                    await asyncio.sleep(random.uniform(2, 4))

        return detailed_bids


async def test_crawler():
    """크롤러 테스트"""
    async with G2BSpider() as spider:
        # 최근 3일간 입찰공고 크롤링
        start_date = (datetime.now() - timedelta(days=3)).strftime("%Y-%m-%d")
        end_date = datetime.now().strftime("%Y-%m-%d")

        logger.info(f"크롤링 기간: {start_date} ~ {end_date}")

        # 목록만 크롤링
        bids = await spider.crawl_bid_list(
            start_date=start_date,
            end_date=end_date,
            max_pages=2
        )

        logger.info(f"총 {len(bids)}건의 입찰공고 수집")

        if bids:
            logger.info("첫 번째 공고:")
            for key, value in bids[0].items():
                logger.info(f"  {key}: {value}")

        return bids


if __name__ == "__main__":
    # 테스트 실행
    asyncio.run(test_crawler())