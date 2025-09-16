#!/usr/bin/env python3
"""
직접 HWP 다운로드 테스트
사용자가 확인한 stdNtceDocUrl에서 HWP 파일 다운로드 테스트
"""

import os
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

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

def test_hwp_download_from_url(driver, test_url):
    """특정 URL에서 HWP 파일 다운로드 테스트"""
    print(f"{'='*80}")
    print(f"📥 HWP 파일 다운로드 테스트")
    print(f"{'='*80}")

    print(f"🔗 테스트 URL: {test_url}")

    try:
        # 다운로드 폴더의 파일 목록 확인 (before)
        download_dir = "storage/downloads"
        before_files = set(os.listdir(download_dir)) if os.path.exists(download_dir) else set()

        print(f"\n1. URL 접속 중...")
        driver.get(test_url)
        time.sleep(5)  # 페이지 로딩 대기

        print(f"   - 페이지 제목: {driver.title}")
        print(f"   - 현재 URL: {driver.current_url}")

        # HWP 파일 관련 요소 찾기
        print(f"\n2. HWP 파일 요소 검색...")

        hwp_patterns = [
            # HWP 파일 직접 링크
            "//a[contains(@href, '.hwp')]",
            "//a[contains(@href, '.HWP')]",

            # 다운로드 링크 패턴
            "//a[contains(@href, 'fileDownload')]",
            "//a[contains(@href, 'download')]",
            "//a[contains(@onclick, 'download')]",
            "//a[contains(@onclick, 'fileDown')]",

            # 텍스트 기반 패턴
            "//a[contains(text(), '.hwp')]",
            "//a[contains(text(), '.HWP')]",
            "//a[contains(text(), '첨부')]",
            "//a[contains(text(), '파일')]",
            "//a[contains(text(), '다운로드')]",

            # 상위 요소 패턴
            "//td[contains(text(), '첨부')]//a",
            "//div[contains(text(), '첨부')]//a",
            "//span[contains(text(), '첨부')]//a",
            "//td[contains(text(), '.hwp')]//a",

            # 버튼 패턴
            "//button[contains(text(), '다운로드')]",
            "//input[@type='button'][contains(@value, '다운로드')]",
            "//input[@type='button'][contains(@value, '첨부')]",
        ]

        found_elements = []
        for pattern in hwp_patterns:
            try:
                elements = driver.find_elements(By.XPATH, pattern)
                for element in elements:
                    if element.is_displayed():
                        found_elements.append((element, pattern))
            except:
                continue

        if found_elements:
            print(f"   ✅ {len(found_elements)}개 파일 관련 요소 발견!")

            downloaded_files = []
            for i, (element, pattern) in enumerate(found_elements[:5], 1):  # 최대 5개
                try:
                    element_text = element.text.strip() or f"element_{i}"
                    href = element.get_attribute('href') or 'javascript'
                    onclick = element.get_attribute('onclick') or ''

                    print(f"\n   [{i}] 요소 정보:")
                    print(f"       텍스트: {element_text}")
                    print(f"       href: {href[:100]}...")
                    if onclick:
                        print(f"       onclick: {onclick[:100]}...")
                    print(f"       패턴: {pattern}")

                    # HWP 관련인지 확인
                    is_hwp_related = (
                        '.hwp' in href.lower() or
                        '.hwp' in element_text.lower() or
                        '첨부' in element_text or
                        '파일' in element_text or
                        'download' in href.lower()
                    )

                    if is_hwp_related:
                        print(f"       📄 HWP 관련 요소로 판단됨")
                        print(f"       다운로드 시도...")

                        # 클릭 시도
                        driver.execute_script("arguments[0].click();", element)
                        time.sleep(5)  # 다운로드 시간 대기

                        # 다운로드된 파일 확인
                        after_files = set(os.listdir(download_dir)) if os.path.exists(download_dir) else set()
                        new_files = after_files - before_files

                        if new_files:
                            print(f"       ✅ 다운로드 성공: {', '.join(new_files)}")

                            # 파일 정보 확인
                            for new_file in new_files:
                                file_path = os.path.join(download_dir, new_file)
                                file_size = os.path.getsize(file_path)
                                file_ext = os.path.splitext(new_file)[1].lower()

                                print(f"          📁 파일명: {new_file}")
                                print(f"          📊 크기: {file_size} bytes")
                                print(f"          📋 확장자: {file_ext}")

                                if file_ext == '.hwp':
                                    print(f"          🎯 HWP 파일 다운로드 성공!")

                            downloaded_files.extend(new_files)
                            before_files = after_files  # 다음 테스트를 위해 업데이트
                        else:
                            print(f"       ⚠️ 새 파일 감지되지 않음")
                    else:
                        print(f"       ⏭️ HWP 관련 아님, 건너뛰기")

                except Exception as e:
                    print(f"       ❌ 처리 실패: {e}")

            return downloaded_files

        else:
            print(f"   ❌ 파일 관련 요소를 찾을 수 없음")

            # 페이지 소스에서 HWP 관련 키워드 검색
            page_source = driver.page_source.lower()
            hwp_keywords = ['.hwp', '첨부', '파일', '다운로드', 'download', 'file', 'attachment']
            found_keywords = [kw for kw in hwp_keywords if kw in page_source]

            if found_keywords:
                print(f"   💡 페이지에서 발견된 키워드: {', '.join(found_keywords)}")

                # .hwp가 페이지에 있다면 더 자세히 검색
                if '.hwp' in page_source:
                    print(f"   🔍 HWP 파일 언급 발견! 페이지 구조 분석 필요")

            return []

    except Exception as e:
        print(f"   ❌ URL 접속 오류: {e}")
        return []

def main():
    """메인 실행 함수"""
    print("=" * 80)
    print("🧪 직접 HWP 파일 다운로드 테스트")
    print("=" * 80)

    # 사용자가 확인한 URL 또는 테스트 URL을 입력받기
    print("사용자가 확인한 stdNtceDocUrl을 입력하거나")
    print("나라장터에서 직접 찾은 공고 URL을 입력해주세요:")
    print("(또는 Enter를 눌러 나라장터 메인 페이지로 이동)")

    test_url = input("URL: ").strip()

    if not test_url:
        test_url = "https://www.g2b.go.kr/index.jsp"
        print(f"기본 URL 사용: {test_url}")
        print("브라우저에서 수동으로 공고를 찾아 테스트할 수 있습니다.")

    driver = None
    try:
        print(f"\n🚀 Selenium HWP 다운로드 테스트 시작")

        driver = setup_driver()
        driver.set_window_size(1400, 900)

        downloaded = test_hwp_download_from_url(driver, test_url)

        # 결과 요약
        print(f"\n{'='*80}")
        print(f"📊 테스트 결과 요약")
        print(f"{'='*80}")

        if downloaded:
            print(f"✅ 성공! 총 {len(downloaded)}개 파일 다운로드:")
            hwp_count = 0
            for file in downloaded:
                file_path = os.path.join("storage/downloads", file)
                size = os.path.getsize(file_path) if os.path.exists(file_path) else 0
                ext = os.path.splitext(file)[1].lower()
                print(f"   - {file} ({size} bytes, {ext})")
                if ext == '.hwp':
                    hwp_count += 1

            if hwp_count > 0:
                print(f"\n🎯 결론:")
                print(f"   HWP 파일 다운로드 ✅ 성공! ({hwp_count}개)")
                print(f"   Odin-AI HWP 문서 수집 시스템 구현 완전히 가능!")
            else:
                print(f"\n📋 HWP 파일은 다운로드되지 않았지만, 파일 다운로드 메커니즘은 작동함")
        else:
            print(f"⚠️ 다운로드된 파일 없음")
            print(f"   - 수동으로 브라우저에서 공고를 찾아보세요")
            print(f"   - 첨부파일이 있는 공고를 찾아 클릭해보세요")

        print(f"\n💡 브라우저를 30초간 유지하여 수동 테스트 가능...")
        time.sleep(30)

    except Exception as e:
        print(f"\n❌ 테스트 중 오류: {e}")
        import traceback
        traceback.print_exc()

    finally:
        if driver:
            driver.quit()
            print(f"\n✅ 브라우저 종료")

if __name__ == "__main__":
    main()