"""
올바른 하이브리드 데이터 수집기
API (메타데이터) + Selenium (파일 다운로드) 방식
"""

import asyncio
import os
import time
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from loguru import logger
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

from .api_collector import APICollector
from shared.config import settings
from shared.database import get_db_context
from shared.models import CollectionLog, BidAnnouncement, BidDocument


class CorrectHybridCollector:
    """
    올바른 하이브리드 수집기

    1단계: API로 메타데이터 + stdNtceDocUrl 수집
    2단계: Selenium으로 stdNtceDocUrl에서 파일 직접 다운로드
    """

    def __init__(self):
        self.api_collector = APICollector()
        self.download_dir = os.path.abspath("storage/downloads/hybrid")

        # 다운로드 폴더 생성
        if not os.path.exists(self.download_dir):
            os.makedirs(self.download_dir)

    def setup_selenium_driver(self):
        """Selenium 드라이버 설정 (파일 다운로드용)"""
        options = Options()

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
            driver = webdriver.Chrome(options=options)
            driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            driver.set_window_size(1400, 900)
            return driver

        except Exception as e:
            logger.error(f"❌ Selenium 드라이버 초기화 실패: {e}")
            return None

    async def collect_monthly_data_correct(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """
        올바른 월간 데이터 수집

        Args:
            start_date: 시작 날짜
            end_date: 종료 날짜

        Returns:
            수집 결과 딕셔너리
        """

        # 로그 시작
        with get_db_context() as db:
            log_entry = CollectionLog(
                collection_type="correct_hybrid",
                collection_date=datetime.utcnow(),
                status="running",
                start_time=datetime.utcnow(),
                notes=f"올바른 하이브리드 수집: {start_date.date()} ~ {end_date.date()}"
            )
            db.add(log_entry)
            db.commit()
            log_id = log_entry.id

        collection_results = {
            'start_date': start_date,
            'end_date': end_date,
            'total_days': (end_date - start_date).days + 1,
            'api_metadata_success': 0,
            'api_metadata_failure': 0,
            'file_download_success': 0,
            'file_download_failure': 0,
            'total_collected': 0,
            'total_files_downloaded': 0,
            'daily_results': {},
            'error_log': [],
            'downloaded_files': []
        }

        try:
            logger.info(f"🚀 올바른 하이브리드 수집 시작: {start_date.date()} ~ {end_date.date()}")

            # 일자별 수집
            current_date = start_date
            while current_date <= end_date:
                logger.info(f"📅 {current_date.strftime('%Y-%m-%d')} 수집 시작...")

                daily_result = await self._collect_daily_data_correct(current_date)
                collection_results['daily_results'][current_date.strftime('%Y-%m-%d')] = daily_result

                # 통계 업데이트
                if daily_result['api_success']:
                    collection_results['api_metadata_success'] += 1
                    collection_results['total_collected'] += daily_result['metadata_count']
                else:
                    collection_results['api_metadata_failure'] += 1

                if daily_result['files_downloaded'] > 0:
                    collection_results['file_download_success'] += 1
                    collection_results['total_files_downloaded'] += daily_result['files_downloaded']
                    collection_results['downloaded_files'].extend(daily_result['downloaded_file_list'])

                if daily_result.get('errors'):
                    collection_results['error_log'].extend(daily_result['errors'])

                # 다음 날짜로
                current_date += timedelta(days=1)

                # 요청 간격
                await asyncio.sleep(3)

            # 로그 업데이트 (성공)
            with get_db_context() as db:
                log_entry = db.query(CollectionLog).filter(
                    CollectionLog.id == log_id
                ).first()

                if log_entry:
                    log_entry.status = "completed"
                    log_entry.end_time = datetime.utcnow()
                    log_entry.total_found = collection_results['total_collected']
                    log_entry.new_items = collection_results['total_files_downloaded']
                    log_entry.notes = f"메타데이터: {collection_results['total_collected']}, 파일: {collection_results['total_files_downloaded']}"
                    db.commit()

            # 결과 요약
            self._log_correct_collection_summary(collection_results)

            return collection_results

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

            logger.error(f"❌ 올바른 하이브리드 수집 실패: {e}")
            collection_results['error_log'].append({
                'timestamp': datetime.utcnow().isoformat(),
                'error': str(e),
                'type': 'correct_hybrid_collector_error'
            })

            return collection_results

    async def _collect_daily_data_correct(self, target_date: datetime) -> Dict[str, Any]:
        """
        일별 데이터 올바른 하이브리드 수집

        Args:
            target_date: 대상 날짜

        Returns:
            일별 수집 결과
        """

        daily_result = {
            'date': target_date.strftime('%Y-%m-%d'),
            'api_success': False,
            'metadata_count': 0,
            'files_downloaded': 0,
            'downloaded_file_list': [],
            'processing_time': 0,
            'errors': []
        }

        start_time = datetime.utcnow()

        try:
            # 1단계: API로 메타데이터 수집
            logger.info(f"🔄 1단계: API 메타데이터 수집 - {target_date.strftime('%Y-%m-%d')}")

            try:
                # API 수집 (성공한 메서드 사용)
                api_data = await self.api_collector.collect_bids_by_date(target_date)

                if api_data:
                    daily_result['api_success'] = True
                    daily_result['metadata_count'] = len(api_data)

                    logger.info(f"✅ API 메타데이터 수집 성공: {len(api_data)}건")

                    # 2단계: stdNtceDocUrl이 있는 항목들의 파일 다운로드
                    logger.info(f"🔄 2단계: 파일 다운로드 시작...")

                    download_urls = []
                    for item in api_data:
                        bid_notice_no = item.get('bidNtceNo', '')

                        # ntceSpecDocUrl1~10 모든 첨부파일 URL 확인
                        for i in range(1, 11):
                            doc_url_field = f'ntceSpecDocUrl{i}'
                            file_name_field = f'ntceSpecFileNm{i}'

                            doc_url = item.get(doc_url_field, '').strip()
                            file_name = item.get(file_name_field, '').strip()

                            if doc_url and file_name:  # URL과 파일명이 모두 있을 때만
                                download_urls.append({
                                    'url': doc_url,
                                    'bid_notice_no': bid_notice_no,
                                    'filename': file_name,
                                    'sequence': i
                                })

                    logger.info(f"📄 다운로드 대상 파일: {len(download_urls)}개 (모든 첨부파일 포함)")

                    if download_urls:
                        downloaded_files = await self._download_files_with_selenium(download_urls)
                        daily_result['files_downloaded'] = len(downloaded_files)
                        daily_result['downloaded_file_list'] = downloaded_files

                        logger.info(f"✅ 파일 다운로드 완료: {len(downloaded_files)}개")
                    else:
                        logger.info(f"📄 다운로드할 파일 URL 없음")

                else:
                    logger.warning(f"⚠️ API 메타데이터 수집 결과 없음")

            except Exception as api_error:
                logger.warning(f"⚠️ API 메타데이터 수집 실패: {api_error}")
                daily_result['errors'].append({
                    'timestamp': datetime.utcnow().isoformat(),
                    'step': 'api_metadata',
                    'error': str(api_error)
                })

            return daily_result

        finally:
            # 처리 시간 계산
            end_time = datetime.utcnow()
            daily_result['processing_time'] = (end_time - start_time).total_seconds()

    async def _download_files_with_selenium(self, download_urls: List[Dict[str, str]]) -> List[str]:
        """
        Selenium으로 파일들 다운로드 (성공한 방식 사용)

        Args:
            download_urls: 다운로드할 URL 리스트

        Returns:
            다운로드된 파일명 리스트
        """
        downloaded_files = []
        driver = None

        try:
            driver = self.setup_selenium_driver()
            if not driver:
                logger.error("❌ Selenium 드라이버 초기화 실패")
                return []

            for url_info in download_urls:
                try:
                    logger.info(f"📥 파일 다운로드 시도: {url_info['filename']}")

                    # 다운로드 전 파일 목록
                    before_files = set(os.listdir(self.download_dir)) if os.path.exists(self.download_dir) else set()

                    # 파일 URL 직접 접속 (성공한 방식)
                    driver.get(url_info['url'])
                    time.sleep(5)  # 다운로드 대기

                    # 다운로드 후 파일 목록
                    after_files = set(os.listdir(self.download_dir)) if os.path.exists(self.download_dir) else set()
                    new_files = after_files - before_files

                    if new_files:
                        downloaded_file = list(new_files)[0]  # 첫 번째 파일
                        file_path = os.path.join(self.download_dir, downloaded_file)
                        file_size = os.path.getsize(file_path)

                        downloaded_files.append(downloaded_file)

                        logger.info(f"✅ 파일 다운로드 성공: {downloaded_file} ({file_size:,} bytes)")

                        # 데이터베이스에 문서 정보 저장
                        await self._save_document_info(url_info, downloaded_file, file_size)

                    else:
                        logger.warning(f"⚠️ 파일 다운로드 실패: {url_info['filename']}")

                    # 다운로드 간격
                    await asyncio.sleep(2)

                except Exception as e:
                    logger.error(f"❌ 파일 다운로드 오류: {e}")
                    continue

        except Exception as e:
            logger.error(f"❌ Selenium 파일 다운로드 실패: {e}")

        finally:
            if driver:
                try:
                    driver.quit()
                    logger.info("✅ Selenium 드라이버 종료")
                except:
                    pass

        return downloaded_files

    async def _save_document_info(self, url_info: Dict[str, str], downloaded_file: str, file_size: int):
        """다운로드된 문서 정보를 데이터베이스에 저장"""
        try:
            with get_db_context() as db:
                # 해당 입찰공고 찾기
                bid_announcement = db.query(BidAnnouncement).filter(
                    BidAnnouncement.bid_notice_no == url_info['bid_notice_no']
                ).first()

                if bid_announcement:
                    # 문서 레코드 생성 또는 업데이트
                    existing_doc = db.query(BidDocument).filter(
                        BidDocument.bid_announcement_id == bid_announcement.id
                    ).first()

                    if existing_doc:
                        # 기존 문서 업데이트
                        existing_doc.file_name = downloaded_file
                        existing_doc.download_status = 'completed'
                        existing_doc.file_size = file_size
                        existing_doc.updated_at = datetime.utcnow()
                    else:
                        # 새 문서 레코드 생성
                        document = BidDocument(
                            bid_announcement_id=bid_announcement.id,
                            file_name=downloaded_file,
                            download_url=url_info['url'],
                            file_type=os.path.splitext(downloaded_file)[1][1:],  # 확장자 (점 제거)
                            download_status='completed',
                            processing_status='pending',
                            file_size=file_size
                        )
                        db.add(document)

                    db.commit()
                    logger.info(f"💾 문서 정보 저장: {downloaded_file}")

        except Exception as e:
            logger.error(f"❌ 문서 정보 저장 실패: {e}")

    def _log_correct_collection_summary(self, results: Dict[str, Any]):
        """올바른 수집 결과 요약 로깅"""

        logger.info("=" * 80)
        logger.info("📊 올바른 하이브리드 수집 완료 - 결과 요약")
        logger.info("=" * 80)

        logger.info(f"📅 수집 기간: {results['start_date'].date()} ~ {results['end_date'].date()}")
        logger.info(f"📊 총 수집일: {results['total_days']}일")
        logger.info(f"📈 총 메타데이터: {results['total_collected']}건")
        logger.info(f"📥 총 다운로드 파일: {results['total_files_downloaded']}개")

        logger.info("\n🔍 수집 단계별 성공률:")
        api_success_rate = (results['api_metadata_success'] / results['total_days']) * 100 if results['total_days'] > 0 else 0
        file_success_rate = (results['file_download_success'] / results['total_days']) * 100 if results['total_days'] > 0 else 0

        logger.info(f"   📡 API 메타데이터 성공률: {api_success_rate:.1f}%")
        logger.info(f"   📥 파일 다운로드 성공률: {file_success_rate:.1f}%")

        if results['downloaded_files']:
            logger.info(f"\n📄 다운로드된 파일들:")
            for file in results['downloaded_files'][:5]:  # 최대 5개만 표시
                logger.info(f"   - {file}")

            if len(results['downloaded_files']) > 5:
                logger.info(f"   ... 외 {len(results['downloaded_files']) - 5}개")

        logger.info("=" * 80)


# 편의 함수
async def collect_recent_bids_correct(days_back: int = 7) -> Dict[str, Any]:
    """
    최근 며칠간의 입찰 데이터를 올바른 하이브리드 방식으로 수집

    Args:
        days_back: 과거 며칠까지

    Returns:
        수집 결과
    """
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days_back)

    collector = CorrectHybridCollector()
    return await collector.collect_monthly_data_correct(start_date, end_date)