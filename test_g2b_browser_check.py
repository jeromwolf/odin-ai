#!/usr/bin/env python3
"""
나라장터 브라우저 체크 우회 및 입찰공고 검색
- 브라우저 호환성 체크 우회
- 입찰공고목록 직접 접근
- 공고명 "데이터분석" 검색
"""

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
import time
import os

def setup_driver():
    """Chrome 드라이버 설정 (나라장터 호환성 최적화)"""
    options = Options()

    # 헤드리스 모드 해제 (브라우저 체크 우회용)
    # options.add_argument('--headless')

    # 나라장터 호환성 설정
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_argument('--disable-web-security')
    options.add_argument('--allow-running-insecure-content')

    # User-Agent 설정 (실제 브라우저처럼)
    options.add_argument("user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.7339.133 Safari/537.36")

    # JavaScript 활성화
    options.add_argument('--enable-javascript')

    # 다운로드 설정
    prefs = {
        "download.default_directory": os.path.abspath("storage/downloads/"),
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "safebrowsing.enabled": True
    }
    options.add_experimental_option("prefs", prefs)

    # 자동화 감지 우회
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)

    driver = webdriver.Chrome(options=options)

    # 자동화 감지 스크립트 제거
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

    return driver

def handle_browser_check(driver):
    """브라우저 호환성 체크 처리"""
    try:
        print("\n🔍 브라우저 호환성 체크 처리")

        # 현재 페이지 확인
        print(f"   - 페이지 제목: {driver.title}")

        # 브라우저 안내 페이지인 경우 처리
        if "접근 가능 브라우저" in driver.title or "브라우저" in driver.page_source:
            print("   - 브라우저 안내 페이지 감지")

            # '계속하기' 또는 '확인' 버튼 찾기
            continue_buttons = [
                "//button[contains(text(), '계속')]",
                "//button[contains(text(), '확인')]",
                "//a[contains(text(), '계속')]",
                "//a[contains(text(), '바로가기')]",
                "//input[@type='button'][contains(@value, '확인')]"
            ]

            for xpath in continue_buttons:
                try:
                    btn = driver.find_element(By.XPATH, xpath)
                    print(f"   - '{btn.text}' 버튼 클릭")
                    btn.click()
                    time.sleep(2)
                    return True
                except:
                    continue

        return False

    except Exception as e:
        print(f"   ❌ 브라우저 체크 처리 오류: {e}")
        return False

def access_bid_list_directly(driver):
    """입찰공고목록 직접 접근"""
    try:
        print("\n📋 입찰공고목록 직접 접근")

        # 2025년 신 시스템 URL들 시도
        urls_to_try = [
            "https://www.g2b.go.kr",
            "https://www.g2b.go.kr/index.jsp",
            "https://www.g2b.go.kr/main.do"
        ]

        for url in urls_to_try:
            print(f"1. URL 접근 시도: {url}")
            driver.get(url)
            time.sleep(3)

            # 브라우저 체크 처리
            handle_browser_check(driver)

            print(f"   - 현재 URL: {driver.current_url}")
            print(f"   - 페이지 제목: {driver.title}")

            # 페이지가 정상적으로 로드되었는지 확인
            if "나라장터" in driver.title and "접근 가능" not in driver.title:
                print("   ✅ 나라장터 메인 페이지 접근 성공")
                return True

        return False

    except Exception as e:
        print(f"   ❌ 접근 오류: {e}")
        return False

def find_and_search(driver, keyword="데이터분석"):
    """입찰공고 검색 기능 찾기 및 실행"""
    try:
        print(f"\n🔍 '{keyword}' 검색 실행")

        # 메인 페이지에서 검색창 찾기
        print("1. 메인 페이지 검색창 찾기...")

        # 다양한 검색창 패턴
        search_patterns = [
            ("input[name*='search']", "일반 검색"),
            ("input[placeholder*='검색']", "검색 placeholder"),
            ("input[name*='keyword']", "키워드 검색"),
            ("input.search-input", "검색 클래스"),
            ("input[type='text']", "텍스트 입력")
        ]

        main_search = None
        for selector, desc in search_patterns:
            try:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                for elem in elements:
                    if elem.is_displayed():
                        main_search = elem
                        print(f"   - {desc} 필드 발견")
                        break
                if main_search:
                    break
            except:
                continue

        if main_search:
            # 메인 검색창에 키워드 입력
            print(f"2. 메인 검색창에 '{keyword}' 입력...")
            main_search.clear()
            main_search.send_keys(keyword)

            # 검색 버튼 찾기
            search_btn_patterns = [
                "//button[contains(text(), '검색')]",
                "//input[@type='submit']",
                "//img[@alt='검색']/.."
            ]

            for xpath in search_btn_patterns:
                try:
                    btn = driver.find_element(By.XPATH, xpath)
                    if btn.is_displayed():
                        btn.click()
                        print("   - 검색 버튼 클릭")
                        time.sleep(3)
                        return True
                except:
                    continue

            # 엔터키로 검색
            main_search.send_keys(Keys.RETURN)
            print("   - 엔터키로 검색")
            time.sleep(3)
            return True

        # 입찰 메뉴 찾기
        print("3. 입찰 메뉴 찾기...")

        menu_patterns = [
            "//a[text()='입찰']",
            "//span[text()='입찰']",
            "//li[contains(@class, 'menu')]//a[contains(text(), '입찰')]"
        ]

        for xpath in menu_patterns:
            try:
                menu = driver.find_element(By.XPATH, xpath)
                print(f"   - 입찰 메뉴 발견: {menu.text}")
                menu.click()
                time.sleep(2)

                # 서브메뉴에서 입찰공고 찾기
                sub_patterns = [
                    "//a[contains(text(), '입찰공고')]",
                    "//a[contains(text(), '공고목록')]"
                ]

                for sub_xpath in sub_patterns:
                    try:
                        sub_menu = driver.find_element(By.XPATH, sub_xpath)
                        print(f"   - 입찰공고 메뉴 클릭: {sub_menu.text}")
                        sub_menu.click()
                        time.sleep(3)
                        return True
                    except:
                        continue

                return True
            except:
                continue

        print("   ❌ 검색 기능을 찾을 수 없음")
        return False

    except Exception as e:
        print(f"   ❌ 검색 오류: {e}")
        return False

def analyze_search_results(driver):
    """검색 결과 분석 및 파일 다운로드"""
    try:
        print("\n📊 검색 결과 분석")

        # iframe 처리
        iframes = driver.find_elements(By.TAG_NAME, "iframe")
        if iframes:
            print(f"   - iframe {len(iframes)}개 발견, 첫 번째로 전환")
            driver.switch_to.frame(iframes[0])
            time.sleep(1)

        # 검색 결과 테이블 찾기
        result_patterns = [
            "//table[@class='table' or contains(@class, 'list')]//tbody//tr",
            "//tr[contains(@onclick, 'javascript')]",
            "//div[@class='result' or contains(@class, 'list')]//a"
        ]

        results = []
        for pattern in result_patterns:
            try:
                elements = driver.find_elements(By.XPATH, pattern)
                if elements:
                    results = elements
                    break
            except:
                continue

        if results:
            print(f"   - {len(results)}개 검색 결과 발견")

            # 처음 3개 결과 출력
            for i, result in enumerate(results[:3], 1):
                try:
                    text = result.text[:100] if result.text else "내용 없음"
                    print(f"\n   [{i}] {text}...")

                    # 결과 클릭해서 상세 보기
                    if i == 1:  # 첫 번째 결과만 클릭
                        try:
                            result.click()
                            time.sleep(3)

                            # 새 창이 열렸는지 확인
                            if len(driver.window_handles) > 1:
                                driver.switch_to.window(driver.window_handles[-1])
                                print("   - 상세 팝업 열림")

                                # 첨부파일 찾기
                                file_links = driver.find_elements(By.XPATH, "//a[contains(@href, 'download') or contains(text(), '.pdf') or contains(text(), '.hwp')]")

                                if file_links:
                                    print(f"   - {len(file_links)}개 첨부파일 발견")
                                    for link in file_links[:2]:
                                        try:
                                            print(f"   - 다운로드: {link.text}")
                                            link.click()
                                            time.sleep(2)
                                        except:
                                            pass
                                else:
                                    print("   - 첨부파일 없음")

                                # 팝업 닫기
                                driver.close()
                                driver.switch_to.window(driver.window_handles[0])
                            else:
                                print("   - 같은 창에서 상세 보기")
                        except Exception as e:
                            print(f"   ❌ 결과 클릭 오류: {e}")
                except:
                    pass
        else:
            print("   - 검색 결과 없음")

        return len(results) > 0

    except Exception as e:
        print(f"   ❌ 결과 분석 오류: {e}")
        return False

def main():
    """메인 실행 함수"""
    print("=" * 60)
    print("나라장터 브라우저 체크 우회 검색 테스트")
    print("=" * 60)

    driver = None
    try:
        # 드라이버 설정
        driver = setup_driver()
        driver.set_window_size(1400, 900)

        # 나라장터 접근
        if access_bid_list_directly(driver):
            print("\n✅ 나라장터 접근 성공")

            # 검색 실행
            if find_and_search(driver, "데이터분석"):
                print("\n✅ 검색 실행 성공")

                # 결과 분석
                analyze_search_results(driver)
            else:
                print("\n❌ 검색 실행 실패")
        else:
            print("\n❌ 나라장터 접근 실패")

        # 확인을 위해 대기
        print("\n20초 후 종료됩니다...")
        time.sleep(20)

    except Exception as e:
        print(f"\n❌ 실행 오류: {e}")
        import traceback
        traceback.print_exc()

    finally:
        if driver:
            driver.quit()
            print("\n✅ 브라우저 종료")

    print("=" * 60)

if __name__ == "__main__":
    main()