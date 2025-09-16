"""
나라장터(G2B) 웹사이트 크롤러
공공데이터포털 API로 부족한 데이터를 보완하는 크롤러
"""

import asyncio
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import json
from urllib.parse import urljoin, urlparse
import random

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from bs4 import BeautifulSoup
import httpx

from backend.core.config import settings
from loguru import logger


class G2BCrawler:
    """나라장터 크롤러"""

    # 나라장터 기본 URL
    BASE_URL = "https://www.g2b.go.kr"

    # 주요 페이지 URL
    URLS = {
        "bid_list": "/koneps/bisns/bidding/seach/bidding.do",
        "bid_detail": "/koneps/bisns/bidding/detail/bidding.do",
        "emergency_list": "/koneps/bisns/bidding/seach/emergency.do",
        "tender_list": "/koneps/bisns/tender/seach/tender.do",
    }

    def __init__(self):
        """크롤러 초기화"""
        self.session = None
        self.driver = None
        self.request_count = 0
        self.last_request_time = 0
        self.min_delay = 2.0  # 최소 2초 딜레이
        self.max_delay = 5.0  # 최대 5초 딜레이

        logger.info("G2BCrawler 초기화 완료")

    async def __aenter__(self):
        """비동기 컨텍스트 매니저 진입"""
        await self.setup_session()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """비동기 컨텍스트 매니저 종료"""
        await self.close_session()

    async def setup_session(self):
        """HTTP 세션 및 Selenium 드라이버 설정"""
        try:
            # HTTP 클라이언트 설정
            self.session = httpx.AsyncClient(
                timeout=30.0,
                headers={
                    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                    'Accept-Language': 'ko-KR,ko;q=0.8,en-US;q=0.5,en;q=0.3',
                    'Accept-Encoding': 'gzip, deflate',
                    'Connection': 'keep-alive',
                    'Upgrade-Insecure-Requests': '1',
                }
            )

            # Selenium 드라이버 설정 (필요시에만)
            self._setup_selenium_driver()

            logger.info("크롤링 세션 설정 완료")

        except Exception as e:
            logger.error(f"세션 설정 실패: {e}")
            raise

    def _setup_selenium_driver(self):
        """Selenium WebDriver 설정"""
        try:
            chrome_options = Options()
            chrome_options.add_argument('--headless')  # 헤드리스 모드
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--window-size=1920,1080')
            chrome_options.add_argument('--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')

            # 이미지 로딩 비활성화 (속도 향상)
            prefs = {
                "profile.managed_default_content_settings.images": 2,
                "profile.default_content_setting_values.notifications": 2
            }
            chrome_options.add_experimental_option("prefs", prefs)

            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.implicitly_wait(10)

            logger.info("Selenium WebDriver 설정 완료")

        except Exception as e:
            logger.warning(f"Selenium 설정 실패 (필요시에만 사용): {e}")
            self.driver = None

    async def close_session(self):
        """세션 정리"""
        if self.session:
            await self.session.aclose()
            logger.info("HTTP 세션 종료")

        if self.driver:
            self.driver.quit()
            logger.info("Selenium 드라이버 종료")

    async def _wait_for_rate_limit(self):
        """Rate limiting 대기"""
        current_time = time.time()
        time_diff = current_time - self.last_request_time

        if time_diff < self.min_delay:
            wait_time = random.uniform(self.min_delay, self.max_delay) - time_diff
            if wait_time > 0:
                logger.debug(f"Rate limiting: {wait_time:.2f}초 대기")
                await asyncio.sleep(wait_time)

        self.last_request_time = time.time()
        self.request_count += 1

    async def fetch_page(self, url: str, params: Dict = None) -> str:
        """페이지 HTML 가져오기"""
        await self._wait_for_rate_limit()

        try:
            full_url = urljoin(self.BASE_URL, url)
            logger.debug(f"페이지 요청: {full_url}")

            response = await self.session.get(full_url, params=params)
            response.raise_for_status()

            return response.text

        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP 오류 [{e.response.status_code}]: {url}")
            raise
        except httpx.RequestError as e:
            logger.error(f"요청 오류: {e}")
            raise

    def parse_html(self, html: str) -> BeautifulSoup:
        """HTML 파싱"""
        return BeautifulSoup(html, 'html.parser')

    async def get_bid_announcements(
        self,
        page: int = 1,
        bid_type: str = "전체",
        region: str = "전체",
        agency: str = "",
        keyword: str = "",
        start_date: str = "",
        end_date: str = "",
        min_amount: int = 0,
        max_amount: int = 0
    ) -> Dict[str, Any]:
        """입찰공고 목록 조회"""

        logger.info(f"입찰공고 목록 조회 (페이지: {page})")

        try:
            # 검색 파라미터 구성
            params = {
                "currentPageNo": page,
                "recordCountPerPage": 10,
                "viewMode": "",
                "searchType": "1",  # 공고명
                "searchKeyword": keyword,
                "searchBgnDt": start_date or datetime.now().strftime("%Y/%m/%d"),
                "searchEndDt": end_date or (datetime.now() + timedelta(days=30)).strftime("%Y/%m/%d"),
                "searchBidNtceOdr": "DESC",
                "searchTotalYn": "Y"
            }

            # 페이지 HTML 가져오기
            html = await self.fetch_page(self.URLS["bid_list"], params)
            soup = self.parse_html(html)

            # 입찰공고 목록 파싱
            bid_items = await self._parse_bid_list(soup)

            # 페이징 정보 파싱
            pagination_info = await self._parse_pagination(soup)

            return {
                "success": True,
                "page": page,
                "total_count": pagination_info.get("total_count", 0),
                "total_pages": pagination_info.get("total_pages", 1),
                "items": bid_items,
                "crawled_at": datetime.now().isoformat(),
                "source": "g2b_crawler"
            }

        except Exception as e:
            logger.error(f"입찰공고 목록 조회 실패: {e}")
            return {
                "success": False,
                "error": str(e),
                "page": page,
                "items": [],
                "source": "g2b_crawler"
            }

    async def _parse_bid_list(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """입찰공고 목록 파싱"""
        bid_items = []

        try:
            # 입찰공고 테이블 찾기
            table = soup.find("table", {"class": "tbl_type"})
            if not table:
                logger.warning("입찰공고 테이블을 찾을 수 없습니다")
                return bid_items

            rows = table.find("tbody").find_all("tr")

            for row in rows:
                try:
                    cols = row.find_all("td")
                    if len(cols) < 7:
                        continue

                    # 공고명에서 링크와 공고번호 추출
                    title_cell = cols[1]
                    title_link = title_cell.find("a")

                    if title_link:
                        bid_title = title_link.get_text(strip=True)
                        # onclick 속성에서 공고번호 추출
                        onclick = title_link.get("onclick", "")
                        bid_no = self._extract_bid_no_from_onclick(onclick)
                    else:
                        bid_title = title_cell.get_text(strip=True)
                        bid_no = ""

                    # 데이터 추출
                    item = {
                        "bid_notice_no": bid_no,
                        "bid_notice_name": bid_title,
                        "agency": cols[2].get_text(strip=True),
                        "bid_method": cols[3].get_text(strip=True),
                        "announcement_date": cols[4].get_text(strip=True),
                        "deadline_date": cols[5].get_text(strip=True),
                        "opening_date": cols[6].get_text(strip=True) if len(cols) > 6 else "",

                        # 메타데이터
                        "crawled_from": "g2b_website",
                        "detail_url": self._build_detail_url(bid_no) if bid_no else "",
                    }

                    bid_items.append(item)

                except Exception as e:
                    logger.warning(f"입찰공고 항목 파싱 오류: {e}")
                    continue

            logger.info(f"입찰공고 {len(bid_items)}건 파싱 완료")

        except Exception as e:
            logger.error(f"입찰공고 목록 파싱 실패: {e}")

        return bid_items

    def _extract_bid_no_from_onclick(self, onclick: str) -> str:
        """onclick 속성에서 입찰공고번호 추출"""
        try:
            # 일반적인 패턴: fn_link_bidDetail('공고번호', '차수')
            import re
            pattern = r"fn_link_bidDetail\(['\"]([^'\"]+)['\"]"
            match = re.search(pattern, onclick)
            if match:
                return match.group(1)
        except Exception as e:
            logger.debug(f"공고번호 추출 실패: {e}")

        return ""

    def _build_detail_url(self, bid_no: str) -> str:
        """상세 페이지 URL 생성"""
        if not bid_no:
            return ""

        return f"{self.BASE_URL}/koneps/bisns/bidding/detail/bidding.do?bidno={bid_no}"

    async def _parse_pagination(self, soup: BeautifulSoup) -> Dict[str, int]:
        """페이징 정보 파싱"""
        pagination_info = {
            "total_count": 0,
            "total_pages": 1,
            "current_page": 1
        }

        try:
            # 전체 건수 찾기
            total_elem = soup.find("span", {"class": "number"})
            if total_elem:
                total_text = total_elem.get_text(strip=True)
                total_count = int(''.join(filter(str.isdigit, total_text)))
                pagination_info["total_count"] = total_count
                pagination_info["total_pages"] = max(1, (total_count + 9) // 10)

        except Exception as e:
            logger.warning(f"페이징 정보 파싱 오류: {e}")

        return pagination_info

    async def get_bid_detail(self, bid_no: str, bid_ord: str = "01") -> Dict[str, Any]:
        """입찰공고 상세 정보 조회"""

        logger.info(f"입찰공고 상세 조회: {bid_no}")

        try:
            params = {
                "bidno": bid_no,
                "bidseq": bid_ord
            }

            html = await self.fetch_page(self.URLS["bid_detail"], params)
            soup = self.parse_html(html)

            # 상세 정보 파싱
            detail_info = await self._parse_bid_detail(soup, bid_no)

            return {
                "success": True,
                "bid_notice_no": bid_no,
                "detail_info": detail_info,
                "crawled_at": datetime.now().isoformat(),
                "source": "g2b_crawler"
            }

        except Exception as e:
            logger.error(f"입찰공고 상세 조회 실패: {e}")
            return {
                "success": False,
                "error": str(e),
                "bid_notice_no": bid_no,
                "source": "g2b_crawler"
            }

    async def _parse_bid_detail(self, soup: BeautifulSoup, bid_no: str) -> Dict[str, Any]:
        """입찰공고 상세 정보 파싱"""
        detail_info = {
            "bid_notice_no": bid_no,
            "parsed_fields": {}
        }

        try:
            # 상세 정보 테이블들 찾기
            detail_tables = soup.find_all("table", {"class": "tbl_type"})

            for table in detail_tables:
                rows = table.find_all("tr")

                for row in rows:
                    try:
                        th = row.find("th")
                        td = row.find("td")

                        if th and td:
                            field_name = th.get_text(strip=True)
                            field_value = td.get_text(strip=True)
                            detail_info["parsed_fields"][field_name] = field_value

                    except Exception as e:
                        logger.debug(f"상세 필드 파싱 오류: {e}")
                        continue

            # 첨부파일 정보 파싱
            attachments = await self._parse_attachments(soup)
            if attachments:
                detail_info["attachments"] = attachments

            logger.info(f"상세 정보 파싱 완료: {len(detail_info['parsed_fields'])}개 필드")

        except Exception as e:
            logger.error(f"상세 정보 파싱 실패: {e}")

        return detail_info

    async def _parse_attachments(self, soup: BeautifulSoup) -> List[Dict[str, str]]:
        """첨부파일 정보 파싱"""
        attachments = []

        try:
            # 첨부파일 링크들 찾기
            file_links = soup.find_all("a", href=True)

            for link in file_links:
                href = link.get("href", "")
                if "download" in href.lower() or "file" in href.lower():
                    attachment = {
                        "filename": link.get_text(strip=True),
                        "url": urljoin(self.BASE_URL, href),
                        "type": self._get_file_type_from_name(link.get_text(strip=True))
                    }
                    attachments.append(attachment)

        except Exception as e:
            logger.warning(f"첨부파일 파싱 오류: {e}")

        return attachments

    def _get_file_type_from_name(self, filename: str) -> str:
        """파일명에서 파일 타입 추출"""
        if not filename:
            return "unknown"

        ext = filename.lower().split(".")[-1] if "." in filename else ""

        type_mapping = {
            "hwp": "hwp",
            "pdf": "pdf",
            "doc": "doc",
            "docx": "doc",
            "xls": "excel",
            "xlsx": "excel",
            "zip": "archive",
            "rar": "archive"
        }

        return type_mapping.get(ext, "unknown")

    async def health_check(self) -> Dict[str, Any]:
        """크롤러 상태 확인"""
        try:
            # 기본 페이지 접근 테스트
            html = await self.fetch_page("/")
            soup = self.parse_html(html)

            title = soup.find("title")
            title_text = title.get_text() if title else "No title"

            return {
                "success": True,
                "status": "healthy",
                "website_title": title_text,
                "request_count": self.request_count,
                "last_request_time": self.last_request_time,
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"크롤러 상태 확인 실패: {e}")
            return {
                "success": False,
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }