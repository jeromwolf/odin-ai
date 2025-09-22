"""
Selenium 기반 웹 수집기
공공데이터포털 API SSL 오류 시 대체 수집 방법
"""

import os
import time
import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from loguru import logger
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException

from shared.config import settings
from shared.database import get_db_context
from shared.models import BidAnnouncement, BidDocument, CollectionLog


class SeleniumCollector:
    """Selenium 기반 나라장터 직접 수집기"""

    def __init__(self):
        self.driver: Optional[webdriver.Chrome] = None
        self.download_dir = os.path.abspath("storage/downloads/selenium")

        # 다운로드 폴더 생성
        if not os.path.exists(self.download_dir):
            os.makedirs(self.download_dir)

    def setup_driver(self):
        """Chrome 드라이버 설정"""
        options = Options()

        # 헤드리스 모드 (운영 환경에서는 헤드리스 사용)
        if settings.selenium_headless:
            options.add_argument('--headless')

        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument("user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36")

        # 자동화 감지 우회
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)

        # 다운로드 설정
        prefs = {
            "download.default_directory": self.download_dir,
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "safebrowsing.enabled": True
        }
        options.add_experimental_option("prefs", prefs)

        try:
            self.driver = webdriver.Chrome(options=options)
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            self.driver.set_window_size(1400, 900)

            logger.info("✅ Selenium Chrome 드라이버 초기화 완료")
            return True

        except Exception as e:
            logger.error(f"❌ Selenium 드라이버 초기화 실패: {e}")
            return False

    def close_driver(self):
        """드라이버 종료"""
        if self.driver:
            try:
                self.driver.quit()
                logger.info("✅ Selenium 드라이버 종료")
            except Exception as e:
                logger.error(f"⚠️ 드라이버 종료 오류: {e}")
            finally:
                self.driver = None

    async def collect_bids_by_date_range(
        self,
        start_date: datetime,
        end_date: datetime,
        max_pages: int = 10
    ) -> List[Dict[str, Any]]:
        """
        날짜 범위로 입찰 공고 수집 (Selenium 방식)

        Args:
            start_date: 시작 날짜
            end_date: 종료 날짜
            max_pages: 최대 페이지 수

        Returns:
            수집된 입찰 데이터 리스트
        """

        # 로그 시작
        with get_db_context() as db:
            log_entry = CollectionLog(
                collection_type="selenium",
                collection_date=datetime.utcnow(),
                status="running",
                start_time=datetime.utcnow(),
                notes=f"Selenium 수집: {start_date.date()} ~ {end_date.date()}"
            )
            db.add(log_entry)
            db.commit()
            log_id = log_entry.id

        collected_bids = []

        try:
            logger.info(f"🚀 Selenium 수집 시작: {start_date.date()} ~ {end_date.date()}")

            if not self.setup_driver():
                raise Exception("Selenium 드라이버 초기화 실패")

            # 나라장터 입찰공고 검색 페이지로 이동
            search_url = "https://www.g2b.go.kr/koneps/bisps/biss/bidd/BiddSearchForm.do"
            self.driver.get(search_url)

            # 페이지 로딩 대기
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )

            logger.info("📄 나라장터 검색 페이지 접속 완료")

            # 날짜 설정
            await self._set_search_dates(start_date, end_date)

            # 검색 실행
            await self._execute_search()

            # 페이지별 데이터 수집
            for page in range(1, max_pages + 1):
                logger.info(f"📖 페이지 {page} 수집 시작...")

                page_bids = await self._collect_page_data(page)
                if not page_bids:
                    logger.info(f"📄 페이지 {page}: 더 이상 데이터 없음. 수집 종료")
                    break

                collected_bids.extend(page_bids)
                logger.info(f"✅ 페이지 {page}: {len(page_bids)}건 수집 완료")

                # 다음 페이지로 이동
                if page < max_pages:
                    next_page_success = await self._go_to_next_page()
                    if not next_page_success:
                        logger.info(f"📄 다음 페이지 없음. 수집 종료")
                        break

                # 요청 간격
                await asyncio.sleep(2)

            # 데이터베이스 저장
            if collected_bids:
                saved_count = await self._save_selenium_bid_data(collected_bids)
                logger.info(f"💾 데이터베이스 저장: {saved_count}건")

            # 로그 업데이트 (성공)
            with get_db_context() as db:
                log_entry = db.query(CollectionLog).filter(
                    CollectionLog.id == log_id
                ).first()

                if log_entry:
                    log_entry.status = "completed"
                    log_entry.end_time = datetime.utcnow()
                    log_entry.total_found = len(collected_bids)
                    log_entry.new_items = len(collected_bids)
                    db.commit()

            logger.info(f"🎉 Selenium 수집 완료: 총 {len(collected_bids)}건")
            return collected_bids

        except Exception as e:
            # 로그 업데이트 (실패)
            with get_db_context() as db:
                log_entry = db.query(CollectionLog).filter(
                    CollectionLog.id == log_id
                ).first()

                if log_entry:
                    log_entry.status = "failed"
                    log_entry.end_time = datetime.utcnow()
                    log_entry.error_message = str(e)
                    db.commit()

            logger.error(f"❌ Selenium 수집 실패: {e}")
            raise

        finally:
            self.close_driver()

    async def _set_search_dates(self, start_date: datetime, end_date: datetime):
        """검색 날짜 설정"""
        try:
            # 공고기간 시작일 설정
            start_input = self.driver.find_element(By.NAME, "fromBidDt")
            start_input.clear()
            start_input.send_keys(start_date.strftime("%Y/%m/%d"))

            # 공고기간 종료일 설정
            end_input = self.driver.find_element(By.NAME, "toBidDt")
            end_input.clear()
            end_input.send_keys(end_date.strftime("%Y/%m/%d"))

            logger.info(f"📅 검색 날짜 설정: {start_date.date()} ~ {end_date.date()}")

        except Exception as e:
            logger.error(f"❌ 날짜 설정 실패: {e}")
            raise

    async def _execute_search(self):
        """검색 실행"""
        try:
            # 검색 버튼 클릭
            search_btn = self.driver.find_element(By.XPATH, "//a[contains(@onclick, 'searchBiddPblList')]")
            search_btn.click()

            # 검색 결과 로딩 대기
            WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.CLASS_NAME, "list_table"))
            )

            logger.info("🔍 검색 실행 완료")

        except TimeoutException:
            logger.error("❌ 검색 결과 로딩 타임아웃")
            raise
        except Exception as e:
            logger.error(f"❌ 검색 실행 실패: {e}")
            raise

    async def _collect_page_data(self, page_num: int) -> List[Dict[str, Any]]:
        """페이지 데이터 수집"""
        page_bids = []

        try:
            # 테이블 행 찾기
            rows = self.driver.find_elements(By.XPATH, "//table[@class='list_table']//tr[position()>1]")

            if not rows:
                logger.warning(f"📄 페이지 {page_num}: 데이터 행 없음")
                return []

            for i, row in enumerate(rows, 1):
                try:
                    cells = row.find_elements(By.TAG_NAME, "td")
                    if len(cells) < 8:  # 최소 필요한 컬럼 수
                        continue

                    # 입찰공고 정보 추출
                    bid_data = {
                        'bidNtceNo': self._extract_bid_notice_no(cells[1]),
                        'bidNtceNm': cells[2].text.strip(),
                        'ntceInsttNm': cells[3].text.strip(),
                        'bidNtceDt': cells[4].text.strip(),
                        'bidClseDt': cells[5].text.strip(),
                        'opengDt': cells[6].text.strip(),
                        'presmptPrce': cells[7].text.strip(),
                        'bidNtceDtlUrl': self._extract_detail_url(cells[1]),
                        'collection_method': 'selenium',
                        'page_number': page_num,
                        'row_number': i
                    }

                    page_bids.append(bid_data)

                except Exception as e:
                    logger.warning(f"⚠️ 행 {i} 처리 오류: {e}")
                    continue

            logger.info(f"📊 페이지 {page_num}: {len(page_bids)}건 추출")
            return page_bids

        except Exception as e:
            logger.error(f"❌ 페이지 {page_num} 데이터 수집 실패: {e}")
            return []

    def _extract_bid_notice_no(self, cell) -> str:
        """입찰공고번호 추출"""
        try:
            link = cell.find_element(By.TAG_NAME, "a")
            onclick = link.get_attribute("onclick")
            # onclick에서 공고번호 추출
            # 예: showBiddPblDetailThng('20241001001', '000');
            import re
            match = re.search(r"'([^']+)'", onclick)
            return match.group(1) if match else ""
        except:
            return ""

    def _extract_detail_url(self, cell) -> str:
        """상세 URL 추출"""
        try:
            link = cell.find_element(By.TAG_NAME, "a")
            onclick = link.get_attribute("onclick")
            # onclick으로부터 실제 URL 구성
            if "showBiddPblDetailThng" in onclick:
                import re
                matches = re.findall(r"'([^']+)'", onclick)
                if len(matches) >= 2:
                    bid_no, bid_ord = matches[0], matches[1]
                    return f"https://www.g2b.go.kr/koneps/bisps/biss/bidd/BiddSearchResultDetailThng.do?bidPbancNo={bid_no}&bidPbancOrd={bid_ord}"
            return ""
        except:
            return ""

    async def _go_to_next_page(self) -> bool:
        """다음 페이지로 이동"""
        try:
            # 다음 페이지 버튼 찾기
            next_btn = self.driver.find_element(By.XPATH, "//a[contains(@onclick, 'goPage') and text()='다음']")
            next_btn.click()

            # 페이지 로딩 대기
            await asyncio.sleep(3)
            return True

        except Exception:
            return False

    async def _save_selenium_bid_data(self, bid_items: List[Dict[str, Any]]) -> int:
        """Selenium으로 수집된 데이터 저장"""
        saved_count = 0

        with get_db_context() as db:
            for item in bid_items:
                try:
                    bid_notice_no = item.get('bidNtceNo', '')
                    if not bid_notice_no:
                        continue

                    # 중복 확인
                    existing = db.query(BidAnnouncement).filter(
                        BidAnnouncement.bid_notice_no == bid_notice_no
                    ).first()

                    if existing:
                        # 기존 데이터 업데이트
                        existing.title = item.get('bidNtceNm', existing.title)
                        existing.organization_name = item.get('ntceInsttNm', existing.organization_name)
                        existing.detail_url = item.get('bidNtceDtlUrl', existing.detail_url)
                        existing.updated_at = datetime.utcnow()
                    else:
                        # 신규 데이터 생성
                        bid_announcement = BidAnnouncement(
                            bid_notice_no=bid_notice_no,
                            title=item.get('bidNtceNm', ''),
                            organization_name=item.get('ntceInsttNm', ''),
                            announcement_date=self._parse_date(item.get('bidNtceDt')),
                            document_submission_end=self._parse_date(item.get('bidClseDt')),
                            opening_date=self._parse_date(item.get('opengDt')),
                            bid_amount=self._parse_amount(item.get('presmptPrce')),
                            detail_url=item.get('bidNtceDtlUrl', ''),
                            status="active",
                            is_processed=False,
                            api_service="selenium"
                        )
                        db.add(bid_announcement)
                        saved_count += 1

                    db.commit()

                except Exception as e:
                    logger.error(f"❌ 데이터 저장 오류: {e}, 아이템: {item}")
                    db.rollback()
                    continue

        return saved_count

    def _parse_date(self, date_str: Optional[str]) -> Optional[datetime]:
        """날짜 문자열 파싱"""
        if not date_str:
            return None

        try:
            # 나라장터 날짜 형식: 2024-10-01 또는 2024/10/01
            formats = ['%Y-%m-%d', '%Y/%m/%d', '%Y.%m.%d']

            for fmt in formats:
                try:
                    return datetime.strptime(date_str.strip(), fmt)
                except ValueError:
                    continue

            logger.warning(f"날짜 파싱 실패: {date_str}")
            return None

        except Exception as e:
            logger.error(f"날짜 파싱 오류: {e}")
            return None

    def _parse_amount(self, amount_str: Optional[str]) -> Optional[int]:
        """금액 문자열 파싱"""
        if not amount_str:
            return None

        try:
            import re
            # 숫자만 추출 (쉼표 제거)
            numbers = re.findall(r'\d+', str(amount_str).replace(',', ''))
            if numbers:
                return int(''.join(numbers))
            return None

        except Exception as e:
            logger.error(f"금액 파싱 오류: {e}")
            return None


# 파일 다운로드 전용 함수
async def download_file_with_selenium(file_url: str, expected_filename: str = None) -> Optional[str]:
    """
    Selenium으로 개별 파일 다운로드

    Args:
        file_url: 다운로드할 파일 URL
        expected_filename: 예상 파일명

    Returns:
        다운로드된 파일 경로 또는 None
    """
    collector = SeleniumCollector()

    try:
        if not collector.setup_driver():
            return None

        # 다운로드 전 파일 목록
        before_files = set(os.listdir(collector.download_dir)) if os.path.exists(collector.download_dir) else set()

        # 파일 URL 직접 접속
        collector.driver.get(file_url)
        time.sleep(5)  # 다운로드 대기

        # 다운로드 후 파일 목록
        after_files = set(os.listdir(collector.download_dir)) if os.path.exists(collector.download_dir) else set()
        new_files = after_files - before_files

        if new_files:
            downloaded_file = list(new_files)[0]  # 첫 번째 파일
            file_path = os.path.join(collector.download_dir, downloaded_file)

            logger.info(f"✅ 파일 다운로드 성공: {downloaded_file}")
            return file_path
        else:
            logger.warning(f"⚠️ 파일 다운로드 실패: {file_url}")
            return None

    except Exception as e:
        logger.error(f"❌ 파일 다운로드 오류: {e}")
        return None

    finally:
        collector.close_driver()