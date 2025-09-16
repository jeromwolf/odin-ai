#!/usr/bin/env python3
"""
bidNtceDtlUrl 필드 테스트
- API에서 bidNtceDtlUrl 필드 확인
- 실제 첨부파일 다운로드 테스트
"""

import asyncio
import sys
import os
import json
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
    # GUI 모드로 실행
    # options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_argument("user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36")

    # 자동화 감지 우회
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)

    # 다운로드 설정
    download_dir = os.path.abspath("storage/downloads/")
    if not os.path.exists(download_dir):
        os.makedirs(download_dir)

    prefs = {
        "download.default_directory": download_dir,
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "safebrowsing.enabled": True
    }
    options.add_experimental_option("prefs", prefs)

    driver = webdriver.Chrome(options=options)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

    return driver

async def get_bidntcedtlurl_from_api():
    """API에서 bidNtceDtlUrl 필드 확인"""
    print("=" * 80)
    print("📡 API에서 bidNtceDtlUrl 필드 확인")
    print("=" * 80)

    try:
        client = PublicDataAPIClient()

        # 더 넓은 날짜 범위로 시도
        date_ranges = [
            (90, "최근 3개월"),
            (60, "최근 2개월"),
            (30, "최근 1개월"),
            (14, "최근 2주"),
            (7, "최근 1주"),
        ]

        found_urls = []

        for days, desc in date_ranges:
            try:
                print(f"\n🔍 {desc} 데이터 확인...")

                end_date = datetime.now()
                start_date = end_date - timedelta(days=days)

                # 입찰공고정보 API 호출
                result = await client.get_bid_construction_list(
                    page=1,
                    size=50,  # 더 많은 데이터
                    inquiry_div="1",
                    start_date=start_date.strftime("%Y%m%d") + "0000",
                    end_date=end_date.strftime("%Y%m%d") + "2359"
                )

                if result and result.get('success'):
                    print(f"   ✅ API 호출 성공")

                    # raw_data에서 items 추출
                    items = []
                    raw_data = result.get('raw_data', {})

                    # 에러 체크
                    if 'nkoneps.com.response.ResponseError' in raw_data:
                        error_info = raw_data['nkoneps.com.response.ResponseError']['header']
                        print(f"   ❌ API 에러: [{error_info['resultCode']}] {error_info['resultMsg']}")
                        continue

                    # 정상 응답에서 items 추출
                    if 'response' in raw_data:
                        response_data = raw_data['response']
                        if 'body' in response_data and 'items' in response_data['body']:
                            items = response_data['body']['items']
                    elif 'items' in raw_data:
                        items = raw_data['items']

                    if items:
                        print(f"   📋 {len(items)}건 데이터 확인")

                        # 모든 필드명 출력 (첫 번째 항목)
                        if len(items) > 0:
                            print(f"\n   📊 첫 번째 항목의 모든 필드:")
                            first_item = items[0]
                            for i, (key, value) in enumerate(first_item.items(), 1):
                                print(f"      [{i:2d}] {key}: {value}")

                        # URL 필드 검색 (stdNtceDocUrl 추가)
                        url_fields = ['stdNtceDocUrl', 'bidNtceDtlUrl', 'bidNtceUrl', 'bidNtcUrl', 'ntceUrl', 'detailUrl']

                        for item in items:
                            for url_field in url_fields:
                                if url_field in item and item[url_field]:
                                    url = item[url_field].strip()
                                    if url and url.startswith('http'):
                                        bid_info = {
                                            'url': url,
                                            'url_field': url_field,
                                            'bidNm': item.get('bidNm', 'N/A'),
                                            'bidNtceNo': item.get('bidNtceNo', 'N/A'),
                                            'ntceInsttNm': item.get('ntceInsttNm', 'N/A')
                                        }
                                        found_urls.append(bid_info)
                                        print(f"   🎯 {url_field} 발견: {url[:80]}...")

                        # URL이 발견되면 더 이상 시도하지 않음
                        if found_urls:
                            break
                    else:
                        print(f"   ❌ items 데이터 없음")

                else:
                    print(f"   ❌ API 호출 실패")

            except Exception as e:
                print(f"   ❌ {desc} 오류: {e}")

        if found_urls:
            print(f"\n✅ 총 {len(found_urls)}개 URL 발견!")

            # 중복 제거
            unique_urls = []
            seen_urls = set()
            for bid_info in found_urls:
                url = bid_info['url']
                if url not in seen_urls:
                    unique_urls.append(bid_info)
                    seen_urls.add(url)

            print(f"📋 중복 제거 후: {len(unique_urls)}개 고유 URL")

            # 처음 3개 출력
            for i, bid_info in enumerate(unique_urls[:3], 1):
                print(f"\n[{i}] 필드명: {bid_info['url_field']}")
                print(f"    공고명: {bid_info['bidNm'][:80]}...")
                print(f"    공고번호: {bid_info['bidNtceNo']}")
                print(f"    기관: {bid_info['ntceInsttNm']}")
                print(f"    URL: {bid_info['url']}")

            return unique_urls[:2]  # 처음 2개만 테스트
        else:
            print("❌ URL 필드를 찾을 수 없음")
            return []

    except Exception as e:
        print(f"❌ API 확인 오류: {e}")
        import traceback
        traceback.print_exc()
        return []

def test_download_from_bidntcedtlurl(driver, bid_info):
    """bidNtceDtlUrl에서 첨부파일 다운로드 테스트"""
    print(f"\n{'='*80}")
    print(f"📥 bidNtceDtlUrl 첨부파일 다운로드 테스트")
    print(f"{'='*80}")

    url = bid_info['url']
    url_field = bid_info['url_field']

    print(f"📄 공고명: {bid_info['bidNm'][:80]}...")
    print(f"🔗 URL 필드: {url_field}")
    print(f"🔗 URL: {url}")

    try:
        # 다운로드 폴더의 파일 목록 확인 (before)
        download_dir = "storage/downloads"
        before_files = set(os.listdir(download_dir)) if os.path.exists(download_dir) else set()

        print(f"\n1. URL 접속 중...")
        driver.get(url)
        time.sleep(5)  # 페이지 로딩 대기

        print(f"   - 페이지 제목: {driver.title}")
        print(f"   - 현재 URL: {driver.current_url}")

        # 첨부파일 관련 요소 찾기
        print(f"\n2. 첨부파일 요소 검색...")

        attachment_patterns = [
            # 일반적인 첨부파일 패턴
            "//a[contains(@href, 'fileDownload')]",
            "//a[contains(@href, 'download')]",
            "//a[contains(@onclick, 'download')]",
            "//a[contains(@onclick, 'fileDown')]",

            # 파일 확장자 패턴
            "//a[contains(@href, '.pdf')]",
            "//a[contains(@href, '.hwp')]",
            "//a[contains(@href, '.doc')]",
            "//a[contains(@href, '.zip')]",
            "//a[contains(@href, '.xlsx')]",

            # 텍스트 기반 패턴
            "//a[contains(text(), '첨부')]",
            "//a[contains(text(), '파일')]",
            "//a[contains(text(), '다운로드')]",
            "//a[contains(text(), '.pdf')]",
            "//a[contains(text(), '.hwp')]",

            # 상위 요소 패턴
            "//td[contains(text(), '첨부')]//a",
            "//div[contains(text(), '첨부')]//a",
            "//span[contains(text(), '첨부')]//a",

            # 버튼 패턴
            "//button[contains(text(), '다운로드')]",
            "//input[@type='button'][contains(@value, '다운로드')]",
            "//input[@type='button'][contains(@value, '첨부')]",
        ]

        found_elements = []
        for pattern in attachment_patterns:
            try:
                elements = driver.find_elements(By.XPATH, pattern)
                for element in elements:
                    if element.is_displayed():
                        found_elements.append((element, pattern))
            except:
                continue

        if found_elements:
            print(f"   ✅ {len(found_elements)}개 첨부파일 관련 요소 발견!")

            downloaded_files = []
            for i, (element, pattern) in enumerate(found_elements[:3], 1):  # 최대 3개
                try:
                    element_text = element.text.strip() or f"element_{i}"
                    href = element.get_attribute('href') or 'javascript'
                    onclick = element.get_attribute('onclick') or ''

                    print(f"\n   [{i}] 요소 정보:")
                    print(f"       텍스트: {element_text}")
                    print(f"       href: {href[:100]}...")
                    print(f"       onclick: {onclick[:100]}...")
                    print(f"       패턴: {pattern}")

                    print(f"       다운로드 시도...")

                    # 클릭 시도
                    driver.execute_script("arguments[0].click();", element)
                    time.sleep(3)  # 다운로드 시간 대기

                    # 다운로드된 파일 확인
                    after_files = set(os.listdir(download_dir)) if os.path.exists(download_dir) else set()
                    new_files = after_files - before_files

                    if new_files:
                        print(f"       ✅ 다운로드 성공: {', '.join(new_files)}")
                        downloaded_files.extend(new_files)
                        before_files = after_files  # 다음 테스트를 위해 업데이트
                    else:
                        print(f"       ⚠️ 새 파일 감지되지 않음")

                except Exception as e:
                    print(f"       ❌ 다운로드 실패: {e}")

            return downloaded_files

        else:
            print(f"   ❌ 첨부파일 요소를 찾을 수 없음")

            # 페이지 소스에서 첨부파일 관련 키워드 검색
            page_source = driver.page_source.lower()
            file_keywords = ['첨부', '파일', '다운로드', 'download', 'file', 'attachment', '.pdf', '.hwp', '.doc']
            found_keywords = [kw for kw in file_keywords if kw in page_source]

            if found_keywords:
                print(f"   💡 페이지에서 발견된 키워드: {', '.join(found_keywords)}")

            return []

    except Exception as e:
        print(f"   ❌ URL 접속 오류: {e}")
        return []

async def main():
    """메인 실행 함수"""
    print("=" * 80)
    print("🧪 bidNtceDtlUrl 첨부파일 다운로드 테스트")
    print("=" * 80)

    # 1. API에서 bidNtceDtlUrl 확인
    bid_urls = await get_bidntcedtlurl_from_api()

    if not bid_urls:
        print("\n❌ 테스트할 URL이 없습니다")
        return

    # 2. Selenium으로 첨부파일 다운로드 테스트
    driver = None
    total_downloaded = []

    try:
        print(f"\n🚀 Selenium 첨부파일 다운로드 테스트 시작")
        print(f"테스트할 URL: {len(bid_urls)}개")

        driver = setup_driver()
        driver.set_window_size(1400, 900)

        for i, bid_info in enumerate(bid_urls, 1):
            print(f"\n테스트 {i}/{len(bid_urls)}")

            downloaded = test_download_from_bidntcedtlurl(driver, bid_info)
            if downloaded:
                total_downloaded.extend(downloaded)

            time.sleep(3)  # 테스트 간 대기

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
            print(f"   bidNtceDtlUrl을 통한 첨부파일 다운로드 ✅ 가능!")
            print(f"   Odin-AI 문서 수집 시스템 구현 완전히 가능!")
        else:
            print(f"⚠️ 다운로드된 파일 없음")
            print(f"   - URL 필드가 다를 수 있음")
            print(f"   - 첨부파일이 없는 공고일 수 있음")
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