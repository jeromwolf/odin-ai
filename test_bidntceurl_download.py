#!/usr/bin/env python3
"""
bidNtceUrl을 통한 실제 문서 다운로드 테스트
1. API에서 bidNtceUrl 추출
2. Selenium으로 해당 URL 접속
3. 첨부파일 다운로드 시도
"""

import asyncio
import sys
import os
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

sys.path.append('/Users/blockmeta/Desktop/blockmeta/project/odin-ai')
from backend.services.public_data_client import PublicDataAPIClient

def setup_driver():
    """Chrome 드라이버 설정"""
    options = Options()
    # GUI 모드로 실행하여 과정 확인
    # options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_argument("user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36")

    # 자동화 감지 우회
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)

    # 다운로드 설정
    prefs = {
        "download.default_directory": os.path.abspath("storage/downloads/"),
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "safebrowsing.enabled": True
    }
    options.add_experimental_option("prefs", prefs)

    driver = webdriver.Chrome(options=options)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

    return driver

async def get_bid_urls_from_api():
    """API에서 bidNtceUrl 추출"""
    print("=" * 80)
    print("📡 API에서 bidNtceUrl 수집")
    print("=" * 80)

    try:
        client = PublicDataAPIClient()

        # 여러 날짜 범위로 시도하여 데이터 확보
        date_ranges = [
            (30, "최근 30일"),
            (7, "최근 7일"),
            (3, "최근 3일"),
            (1, "어제")
        ]

        all_urls = []

        for days, desc in date_ranges:
            try:
                print(f"\n🔍 {desc} 데이터 수집 시도...")

                end_date = datetime.now()
                start_date = end_date - timedelta(days=days)

                # 여러 서비스 API 시도
                services = [
                    ("bid_construction", "입찰공고정보"),
                    ("contract_info", "계약정보"),
                    ("bid_success", "낙찰정보")
                ]

                for service_key, service_name in services:
                    try:
                        print(f"   📋 {service_name} API 호출...")

                        if service_key == "bid_construction":
                            result = await client.get_bid_construction_list(
                                page=1,
                                size=20,
                                inquiry_div="1",
                                start_date=start_date.strftime("%Y%m%d") + "0000",
                                end_date=end_date.strftime("%Y%m%d") + "2359"
                            )
                        elif service_key == "contract_info":
                            result = await client.get_contract_info(
                                page=1,
                                size=20,
                                inquiry_div="1",
                                start_date=start_date.strftime("%Y%m%d") + "0000",
                                end_date=end_date.strftime("%Y%m%d") + "2359"
                            )
                        elif service_key == "bid_success":
                            result = await client.get_bid_success_info(
                                page=1,
                                size=20,
                                inquiry_div="1",
                                start_date=start_date.strftime("%Y%m%d") + "0000",
                                end_date=end_date.strftime("%Y%m%d") + "2359"
                            )

                        if result and result.get('success'):
                            # 데이터 추출
                            items = []

                            if 'items' in result:
                                items = result['items']
                            elif 'raw_data' in result:
                                raw_data = result['raw_data']
                                if 'response' in raw_data and 'body' in raw_data['response']:
                                    body = raw_data['response']['body']
                                    if 'items' in body:
                                        items = body['items']

                            if items:
                                print(f"      ✅ {len(items)}건 데이터 수집")

                                # URL 추출
                                url_fields = ['bidNtceUrl', 'bidNtcUrl', 'ntceUrl', 'url']

                                for item in items:
                                    for url_field in url_fields:
                                        if url_field in item and item[url_field]:
                                            url = item[url_field].strip()
                                            if url and url.startswith('http'):
                                                bid_info = {
                                                    'url': url,
                                                    'bidNm': item.get('bidNm', item.get('bidNtceNm', 'N/A')),
                                                    'bidNtceNo': item.get('bidNtceNo', 'N/A'),
                                                    'ntceInsttNm': item.get('ntceInsttNm', 'N/A'),
                                                    'service': service_name
                                                }
                                                all_urls.append(bid_info)
                                                print(f"         📎 URL 발견: {url[:80]}...")

                            else:
                                print(f"      ❌ {service_name}: items 데이터 없음")
                        else:
                            print(f"      ❌ {service_name}: API 호출 실패")

                    except Exception as e:
                        print(f"      ❌ {service_name} 오류: {e}")

                # URL을 찾았으면 더 이상 다른 날짜 범위 시도하지 않음
                if all_urls:
                    break

            except Exception as e:
                print(f"   ❌ {desc} 시도 오류: {e}")

        if all_urls:
            print(f"\n✅ 총 {len(all_urls)}개 URL 수집 완료!")

            # 중복 제거
            unique_urls = []
            seen_urls = set()
            for bid_info in all_urls:
                url = bid_info['url']
                if url not in seen_urls:
                    unique_urls.append(bid_info)
                    seen_urls.add(url)

            print(f"📋 중복 제거 후: {len(unique_urls)}개 고유 URL")

            # 처음 5개 URL 출력
            for i, bid_info in enumerate(unique_urls[:5], 1):
                print(f"\n[{i}] {bid_info['service']}")
                print(f"    공고명: {bid_info['bidNm'][:80]}...")
                print(f"    공고번호: {bid_info['bidNtceNo']}")
                print(f"    기관: {bid_info['ntceInsttNm']}")
                print(f"    URL: {bid_info['url']}")

            return unique_urls[:3]  # 처음 3개만 테스트
        else:
            print("❌ bidNtceUrl을 찾을 수 없음")
            return []

    except Exception as e:
        print(f"❌ API 수집 오류: {e}")
        import traceback
        traceback.print_exc()
        return []

def test_download_from_url(driver, bid_info):
    """특정 URL에서 파일 다운로드 테스트"""
    print(f"\n{'='*60}")
    print(f"📥 파일 다운로드 테스트")
    print(f"{'='*60}")

    url = bid_info['url']
    print(f"📄 공고명: {bid_info['bidNm'][:80]}...")
    print(f"🔗 URL: {url}")

    try:
        # 현재 창 저장
        main_window = driver.current_window_handle
        initial_windows = len(driver.window_handles)

        print(f"\n1. URL 접속 중...")
        driver.get(url)
        time.sleep(3)

        print(f"   - 페이지 제목: {driver.title}")
        print(f"   - 현재 URL: {driver.current_url}")

        # 새 창이 열렸는지 확인
        if len(driver.window_handles) > initial_windows:
            print("   - 팝업 창 감지, 새 창으로 전환")
            driver.switch_to.window(driver.window_handles[-1])
            time.sleep(2)

        # 첨부파일 링크 찾기
        print(f"\n2. 첨부파일 검색 중...")

        file_patterns = [
            "//a[contains(@href, 'fileDownload')]",
            "//a[contains(@href, 'download')]",
            "//a[contains(@onclick, 'download')]",
            "//a[contains(text(), '.pdf')]",
            "//a[contains(text(), '.hwp')]",
            "//a[contains(text(), '.doc')]",
            "//a[contains(text(), '.zip')]",
            "//a[contains(text(), '.xlsx')]",
            "//span[contains(text(), '첨부')]/..//a",
            "//td[contains(text(), '첨부')]/..//a",
            "//div[contains(text(), '첨부')]//a",
            "//button[contains(text(), '다운로드')]",
            "//input[@type='button'][contains(@value, '다운로드')]"
        ]

        file_links = []
        for pattern in file_patterns:
            try:
                links = driver.find_elements(By.XPATH, pattern)
                for link in links:
                    if link.is_displayed():
                        file_links.append(link)
            except:
                continue

        # 중복 제거
        unique_files = []
        seen_texts = set()
        for link in file_links:
            try:
                link_text = link.text.strip()
                href = link.get_attribute('href') or ''
                if link_text and link_text not in seen_texts:
                    unique_files.append(link)
                    seen_texts.add(link_text)
            except:
                continue

        if unique_files:
            print(f"   ✅ {len(unique_files)}개 첨부파일/다운로드 링크 발견!")

            downloaded_files = []
            for i, link in enumerate(unique_files[:3], 1):  # 최대 3개만
                try:
                    file_name = link.text.strip() or f"file_{i}"
                    href = link.get_attribute('href') or 'javascript'

                    print(f"\n   [{i}] 파일: {file_name}")
                    print(f"       링크: {href[:100]}...")

                    # 다운로드 시도
                    print(f"       다운로드 시도...")

                    # 클릭 전 파일 목록 확인
                    download_dir = "storage/downloads"
                    before_files = set(os.listdir(download_dir)) if os.path.exists(download_dir) else set()

                    link.click()
                    time.sleep(3)  # 다운로드 완료 대기

                    # 클릭 후 파일 목록 확인
                    after_files = set(os.listdir(download_dir)) if os.path.exists(download_dir) else set()
                    new_files = after_files - before_files

                    if new_files:
                        print(f"       ✅ 다운로드 완료: {', '.join(new_files)}")
                        downloaded_files.extend(new_files)
                    else:
                        print(f"       ⚠️ 새 파일이 감지되지 않음 (팝업이나 다른 처리 방식일 수 있음)")

                except Exception as e:
                    print(f"       ❌ 다운로드 실패: {e}")

            # 창 정리
            if len(driver.window_handles) > 1:
                driver.close()
                driver.switch_to.window(main_window)

            return downloaded_files

        else:
            print(f"   ❌ 첨부파일 링크를 찾을 수 없음")

            # 페이지 소스에서 파일 관련 키워드 검색
            page_source = driver.page_source.lower()
            file_keywords = ['첨부', '파일', '다운로드', 'download', 'file', 'attachment']
            found_keywords = [kw for kw in file_keywords if kw in page_source]

            if found_keywords:
                print(f"   💡 페이지에서 발견된 파일 관련 키워드: {', '.join(found_keywords)}")
                print(f"   🔍 수동 확인이 필요할 수 있습니다")

            return []

    except Exception as e:
        print(f"   ❌ URL 접속 오류: {e}")

        # 메인 창으로 복귀
        try:
            driver.switch_to.window(main_window)
        except:
            pass

        return []

async def main():
    """메인 실행 함수"""
    print("=" * 80)
    print("🧪 bidNtceUrl을 통한 실제 문서 다운로드 테스트")
    print("=" * 80)

    # 1. API에서 URL 수집
    bid_urls = await get_bid_urls_from_api()

    if not bid_urls:
        print("\n❌ 테스트할 URL이 없습니다")
        return

    # 2. Selenium으로 파일 다운로드 테스트
    driver = None
    total_downloaded = []

    try:
        print(f"\n🚀 Selenium 다운로드 테스트 시작")
        print(f"테스트할 URL: {len(bid_urls)}개")

        driver = setup_driver()
        driver.set_window_size(1400, 900)

        for i, bid_info in enumerate(bid_urls, 1):
            print(f"\n테스트 {i}/{len(bid_urls)}")

            downloaded = test_download_from_url(driver, bid_info)
            if downloaded:
                total_downloaded.extend(downloaded)

            # 각 테스트 사이에 잠시 대기
            time.sleep(2)

        # 결과 요약
        print(f"\n{'='*80}")
        print(f"📊 테스트 결과 요약")
        print(f"{'='*80}")

        if total_downloaded:
            print(f"✅ 성공! 총 {len(total_downloaded)}개 파일 다운로드:")
            for file in total_downloaded:
                file_path = os.path.join("storage/downloads", file)
                size = os.path.getsize(file_path) if os.path.exists(file_path) else 0
                print(f"   - {file} ({size} bytes)")

            print(f"\n🎯 결론:")
            print(f"   bidNtceUrl을 통한 실제 파일 다운로드 ✅ 가능!")
            print(f"   Odin-AI의 문서 수집 기능 구현 가능!")
        else:
            print(f"⚠️ 다운로드된 파일 없음")
            print(f"   - API URL이 유효하지 않거나")
            print(f"   - 나라장터 사이트 구조 변경")
            print(f"   - 접근 권한 문제 가능성")

        print(f"\n💡 브라우저를 10초간 유지하여 확인 가능...")
        time.sleep(10)

    except Exception as e:
        print(f"\n❌ 테스트 중 오류: {e}")
        import traceback
        traceback.print_exc()

    finally:
        if driver:
            driver.quit()
            print(f"\n✅ 브라우저 종료")

if __name__ == "__main__":
    asyncio.run(main())