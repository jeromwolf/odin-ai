"""
나라장터 Selenium 크롤러
실제 문서 다운로드를 위한 Selenium 기반 크롤링
"""

import asyncio
import os
import time
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from pathlib import Path
import logging

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import pandas as pd

logger = logging.getLogger(__name__)


class G2BSeleniumCrawler:
    """나라장터 Selenium 크롤러"""
    
    def __init__(self, download_path: str = "storage/downloads"):
        """
        초기화
        
        Args:
            download_path: 파일 다운로드 경로
        """
        self.download_path = Path(download_path).absolute()
        self.download_path.mkdir(parents=True, exist_ok=True)
        
        # 나라장터 URL
        self.base_url = "https://www.g2b.go.kr"
        self.search_url = "https://www.g2b.go.kr:8101/ep/tbid/tbidFwd.do"
        
        self.driver = None
        
    def setup_driver(self, headless: bool = False):
        """
        Chrome 드라이버 설정
        
        Args:
            headless: 헤드리스 모드 사용 여부
        """
        options = Options()
        
        # 다운로드 설정
        prefs = {
            "download.default_directory": str(self.download_path),
            "download.prompt_for_download": False,  # 다운로드 프롬프트 비활성화
            "download.directory_upgrade": True,
            "safebrowsing.enabled": True,
            "plugins.always_open_pdf_externally": True  # PDF 자동 다운로드
        }
        options.add_experimental_option("prefs", prefs)
        
        # 헤드리스 모드 설정
        if headless:
            options.add_argument('--headless')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            # 헤드리스 모드에서 다운로드 허용
            options.add_experimental_option("excludeSwitches", ["enable-logging"])
            
        # 일반 설정
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument("user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36")
        
        # 드라이버 생성
        try:
            self.driver = webdriver.Chrome(options=options)
            
            # 헤드리스 모드에서 다운로드 허용 (필수)
            if headless:
                self.driver.command_executor._commands["send_command"] = (
                    "POST", 
                    '/session/$sessionId/chromium/send_command'
                )
                params = {
                    'cmd': 'Page.setDownloadBehavior',
                    'params': {
                        'behavior': 'allow',
                        'downloadPath': str(self.download_path)
                    }
                }
                self.driver.execute("send_command", params)
                
            logger.info(f"Chrome 드라이버 설정 완료 (headless={headless})")
            
        except Exception as e:
            logger.error(f"Chrome 드라이버 설정 실패: {e}")
            raise
    
    def search_bids(self, keyword: str = "", start_date: str = None, end_date: str = None) -> List[Dict]:
        """
        입찰공고 검색
        
        Args:
            keyword: 검색 키워드
            start_date: 시작일 (YYYYMMDD)
            end_date: 종료일 (YYYYMMDD)
            
        Returns:
            입찰공고 목록
        """
        if not self.driver:
            self.setup_driver()
            
        try:
            # 검색 페이지로 이동
            self.driver.get(self.search_url)
            
            # 페이지 로드 대기
            wait = WebDriverWait(self.driver, 10)
            
            # 키워드 입력
            if keyword:
                search_input = wait.until(
                    EC.presence_of_element_located((By.ID, "bidNm"))
                )
                search_input.clear()
                search_input.send_keys(keyword)
            
            # 날짜 설정
            if start_date:
                start_input = self.driver.find_element(By.ID, "fromBidDt")
                start_input.clear()
                start_input.send_keys(start_date)
                
            if end_date:
                end_input = self.driver.find_element(By.ID, "toBidDt")
                end_input.clear()
                end_input.send_keys(end_date)
            
            # 검색 버튼 클릭
            search_button = self.driver.find_element(By.CLASS_NAME, "btn_mdl")
            search_button.click()
            
            # 결과 로드 대기
            time.sleep(3)
            
            # 결과 파싱
            results = self.parse_search_results()
            
            logger.info(f"입찰공고 {len(results)}건 검색 완료")
            return results
            
        except Exception as e:
            logger.error(f"입찰공고 검색 실패: {e}")
            return []
    
    def parse_search_results(self) -> List[Dict]:
        """
        검색 결과 파싱
        
        Returns:
            파싱된 입찰공고 정보
        """
        results = []
        
        try:
            # 테이블 찾기
            table = self.driver.find_element(By.CLASS_NAME, "table_list")
            rows = table.find_elements(By.TAG_NAME, "tr")[1:]  # 헤더 제외
            
            for row in rows:
                cols = row.find_elements(By.TAG_NAME, "td")
                
                if len(cols) >= 7:
                    # 공고번호 및 링크 추출
                    bid_no_elem = cols[1].find_element(By.TAG_NAME, "a")
                    bid_no = bid_no_elem.text.strip()
                    bid_link = bid_no_elem.get_attribute("href")
                    
                    result = {
                        "번호": cols[0].text.strip(),
                        "공고번호": bid_no,
                        "공고명": cols[2].text.strip(),
                        "공고기관": cols[3].text.strip(),
                        "입찰방식": cols[4].text.strip(),
                        "마감일시": cols[5].text.strip(),
                        "추정가격": cols[6].text.strip() if len(cols) > 6 else "",
                        "상세링크": bid_link
                    }
                    
                    results.append(result)
                    
        except Exception as e:
            logger.error(f"검색 결과 파싱 실패: {e}")
            
        return results
    
    def download_bid_documents(self, bid_url: str) -> List[str]:
        """
        입찰공고 첨부파일 다운로드
        
        Args:
            bid_url: 입찰공고 상세 URL
            
        Returns:
            다운로드된 파일 경로 리스트
        """
        if not self.driver:
            self.setup_driver()
            
        downloaded_files = []
        
        try:
            # 상세 페이지로 이동
            self.driver.get(bid_url)
            
            # 페이지 로드 대기
            wait = WebDriverWait(self.driver, 10)
            time.sleep(2)
            
            # 첨부파일 영역 찾기
            try:
                # 첨부파일 다운로드 링크 찾기
                file_links = self.driver.find_elements(
                    By.XPATH, 
                    "//a[contains(@onclick, 'download') or contains(@href, '.hwp') or contains(@href, '.pdf')]"
                )
                
                # 기존 파일 목록 저장
                before_download = set(os.listdir(self.download_path))
                
                for link in file_links:
                    try:
                        file_name = link.text.strip()
                        logger.info(f"첨부파일 다운로드 시도: {file_name}")
                        
                        # 다운로드 클릭
                        link.click()
                        time.sleep(2)  # 다운로드 대기
                        
                    except Exception as e:
                        logger.error(f"파일 다운로드 실패: {e}")
                        continue
                
                # 새로 다운로드된 파일 확인
                time.sleep(3)  # 다운로드 완료 대기
                after_download = set(os.listdir(self.download_path))
                new_files = after_download - before_download
                
                for file_name in new_files:
                    file_path = self.download_path / file_name
                    downloaded_files.append(str(file_path))
                    logger.info(f"파일 다운로드 성공: {file_path}")
                    
            except NoSuchElementException:
                logger.warning("첨부파일을 찾을 수 없습니다")
                
        except Exception as e:
            logger.error(f"문서 다운로드 실패: {e}")
            
        return downloaded_files
    
    def export_to_excel(self, results: List[Dict], filename: str = "narajangteo_bids.xlsx"):
        """
        검색 결과를 엑셀 파일로 저장
        
        Args:
            results: 입찰공고 검색 결과
            filename: 저장할 파일명
        """
        if not results:
            logger.warning("저장할 데이터가 없습니다")
            return
            
        try:
            df = pd.DataFrame(results)
            
            # 컨럼 순서 정리
            columns = ["번호", "공고번호", "공고명", "공고기관", 
                      "입찰방식", "마감일시", "추정가격", "상세링크"]
            df = df[columns]
            
            # 엑셀 파일로 저장
            excel_path = self.download_path / filename
            df.to_excel(excel_path, index=False, sheet_name="입찰공고")
            
            logger.info(f"엑셀 파일 저장 완료: {excel_path}")
            
        except Exception as e:
            logger.error(f"엑셀 파일 저장 실패: {e}")
    
    def close(self):
        """드라이버 종료"""
        if self.driver:
            self.driver.quit()
            logger.info("Chrome 드라이버 종료")


# 비동기 래퍼 클래스
class AsyncG2BSeleniumCrawler:
    """비동기 나라장터 크롤러"""
    
    def __init__(self, download_path: str = "storage/downloads"):
        self.crawler = G2BSeleniumCrawler(download_path)
        
    async def search_bids(self, keyword: str = "", start_date: str = None, end_date: str = None) -> List[Dict]:
        """비동기 입찰공고 검색"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.crawler.search_bids, keyword, start_date, end_date)
    
    async def download_bid_documents(self, bid_url: str) -> List[str]:
        """비동기 문서 다운로드"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.crawler.download_bid_documents, bid_url)
    
    async def close(self):
        """비동기 드라이버 종료"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.crawler.close)


# 싱글톤 인스턴스
g2b_selenium_crawler = None

def get_g2b_selenium_crawler():
    """싱글톤 크롤러 인스턴스 반환"""
    global g2b_selenium_crawler
    if g2b_selenium_crawler is None:
        g2b_selenium_crawler = AsyncG2BSeleniumCrawler()
    return g2b_selenium_crawler