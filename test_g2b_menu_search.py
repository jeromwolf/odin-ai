#!/usr/bin/env python3
"""
나라장터 메뉴 네비게이션을 통한 입찰공고 검색
- 메인 페이지 → 입찰 메뉴 → 입찰공고목록
- 공고명 '데이터분석' 검색
- 결과 클릭하여 팝업에서 파일 다운로드
"""

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
import time
import os
from datetime import datetime

def setup_driver():
    """Chrome 드라이버 설정"""
    options = Options()
    # GUI 모드로 실행
    # options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_argument("user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36")

    # 다운로드 경로 설정
    prefs = {
        "download.default_directory": os.path.abspath("storage/downloads/"),
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "safebrowsing.enabled": True
    }
    options.add_experimental_option("prefs", prefs)

    return webdriver.Chrome(options=options)

def navigate_to_bid_list(driver):
    """나라장터 메인 → 입찰 메뉴 → 입찰공고목록"""
    try:
        print("\n📌 나라장터 메뉴 네비게이션 시작")

        # 1. 나라장터 메인 페이지
        print("1. 나라장터 메인 페이지 접속...")
        driver.get("https://www.g2b.go.kr")
        time.sleep(3)
        print(f"   - 페이지 제목: {driver.title}")

        # 2. 입찰 메뉴 찾기
        print("\n2. '입찰' 메뉴 찾기...")

        # 메인 메뉴에서 입찰 찾기
        menu_patterns = [
            "//a[contains(text(), '입찰')]",
            "//span[contains(text(), '입찰')]",
            "//div[@class='menu' or @class='nav']//a[contains(text(), '입찰')]",
            "//li[contains(@class, 'menu')]//a[contains(text(), '입찰')]"
        ]

        bid_menu = None
        for pattern in menu_patterns:
            try:
                elements = driver.find_elements(By.XPATH, pattern)
                if elements:
                    # 메뉴 중에서 '입찰' 텍스트만 있는 메인 메뉴 찾기
                    for elem in elements:
                        text = elem.text.strip()
                        if text == "입찰" or text == "입찰정보":
                            bid_menu = elem
                            print(f"   - '입찰' 메뉴 발견: {text}")
                            break
                    if bid_menu:
                        break
            except:
                continue

        if bid_menu:
            # 마우스 오버 또는 클릭
            actions = ActionChains(driver)
            actions.move_to_element(bid_menu).perform()
            time.sleep(1)

            # 서브메뉴 확인
            print("\n3. '입찰공고목록' 서브메뉴 찾기...")

            sub_menu_patterns = [
                "//a[contains(text(), '입찰공고목록')]",
                "//a[contains(text(), '입찰공고')]",
                "//ul[@class='sub' or contains(@class, 'submenu')]//a[contains(text(), '공고')]"
            ]

            for pattern in sub_menu_patterns:
                try:
                    sub_menu = driver.find_element(By.XPATH, pattern)
                    print(f"   - '입찰공고목록' 발견: {sub_menu.text}")
                    sub_menu.click()
                    time.sleep(3)
                    return True
                except:
                    continue

            # 서브메뉴가 없으면 메인 메뉴 클릭
            print("   - 서브메뉴가 없어 메인 메뉴 클릭")
            bid_menu.click()
            time.sleep(3)
            return True
        else:
            print("   ❌ 입찰 메뉴를 찾을 수 없음")

            # 대체 방법: 직접 URL 접속
            print("\n4. 직접 URL로 입찰공고 페이지 접속...")
            driver.get("https://www.g2b.go.kr:8081/ep/tbid/tbidList.do")
            time.sleep(3)
            return True

    except Exception as e:
        print(f"   ❌ 네비게이션 오류: {e}")
        return False

def search_by_keyword(driver, keyword="데이터분석"):
    """입찰공고 목록에서 공고명으로 검색"""
    try:
        print(f"\n🔍 공고명 '{keyword}' 검색")

        # iframe 처리
        iframes = driver.find_elements(By.TAG_NAME, "iframe")
        if iframes:
            print(f"   - iframe {len(iframes)}개 발견")
            driver.switch_to.frame(iframes[0])
            time.sleep(1)

        # 검색 입력 필드 찾기
        print("1. 검색 입력 필드 찾기...")

        search_patterns = [
            ("input[name*='bidNm']", "공고명 필드"),
            ("input[id*='bidNm']", "공고명 ID"),
            ("input[placeholder*='공고']", "공고 placeholder"),
            ("input.search", "검색 클래스"),
            ("input[type='text']", "텍스트 필드")
        ]

        search_input = None
        for selector, desc in search_patterns:
            try:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                if elements:
                    # 화면에 보이는 첫 번째 요소 선택
                    for elem in elements:
                        if elem.is_displayed():
                            search_input = elem
                            print(f"   - {desc} 발견")
                            break
                    if search_input:
                        break
            except:
                continue

        if not search_input:
            print("   ❌ 검색 필드를 찾을 수 없음")
            return []

        # 키워드 입력
        print(f"2. 키워드 '{keyword}' 입력...")
        search_input.clear()
        search_input.send_keys(keyword)
        time.sleep(1)

        # 검색 실행
        print("3. 검색 실행...")

        # 검색 버튼 찾기
        search_buttons = [
            "//button[contains(text(), '검색')]",
            "//input[@type='submit' or @type='button'][contains(@value, '검색')]",
            "//a[contains(text(), '검색')]",
            "//img[@alt='검색']/.."
        ]

        clicked = False
        for xpath in search_buttons:
            try:
                btn = driver.find_element(By.XPATH, xpath)
                if btn.is_displayed():
                    btn.click()
                    clicked = True
                    print("   - 검색 버튼 클릭")
                    break
            except:
                continue

        if not clicked:
            # 엔터키로 검색
            search_input.send_keys(Keys.RETURN)
            print("   - 엔터키로 검색")

        time.sleep(3)

        # 검색 결과 확인
        print("\n4. 검색 결과 확인...")

        # 결과 테이블 찾기
        result_patterns = [
            "//tr[contains(@onclick, 'javascript')]",
            "//tbody//tr[@class]",
            "//table[@class='table' or contains(@class, 'list')]//tbody//tr",
            "//a[contains(@href, 'bidDtl')]"
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
                except:
                    pass
        else:
            print("   - 검색 결과 없음")

        return results

    except Exception as e:
        print(f"   ❌ 검색 오류: {e}")
        return []

def download_from_result(driver, result_element):
    """검색 결과 클릭하여 상세 페이지/팝업에서 파일 다운로드"""
    try:
        print("\n📥 파일 다운로드 시도")

        # 현재 창 저장
        main_window = driver.current_window_handle
        initial_windows = len(driver.window_handles)

        # 결과 클릭
        print("1. 검색 결과 클릭...")

        # 클릭 가능한 요소 찾기 (공고번호나 제목 링크)
        clickable = None
        try:
            # tr 내의 링크 찾기
            links = result_element.find_elements(By.TAG_NAME, "a")
            if links:
                clickable = links[0]
            else:
                # tr 자체가 클릭 가능한 경우
                clickable = result_element
        except:
            clickable = result_element

        if clickable:
            clickable.click()
            time.sleep(3)

        # 새 창/팝업 확인
        if len(driver.window_handles) > initial_windows:
            print("2. 팝업 창 열림")
            driver.switch_to.window(driver.window_handles[-1])
            time.sleep(2)
        else:
            print("2. 같은 창에서 상세 페이지 열림")

        # 첨부파일 섹션 찾기
        print("3. 첨부파일 확인...")

        file_patterns = [
            "//a[contains(@href, 'fileDownload')]",
            "//a[contains(@onclick, 'download')]",
            "//a[contains(text(), '.pdf')]",
            "//a[contains(text(), '.hwp')]",
            "//a[contains(text(), '.doc')]",
            "//a[contains(text(), '.zip')]",
            "//span[contains(text(), '첨부')]/..//a",
            "//td[contains(text(), '첨부')]/..//a"
        ]

        file_links = []
        for pattern in file_patterns:
            try:
                links = driver.find_elements(By.XPATH, pattern)
                if links:
                    file_links.extend(links)
            except:
                continue

        if file_links:
            print(f"4. {len(file_links)}개 첨부파일 발견")

            downloaded = []
            for i, link in enumerate(file_links[:3], 1):
                try:
                    file_name = link.text or f"file_{i}"
                    print(f"   - 다운로드: {file_name}")
                    link.click()
                    time.sleep(2)
                    downloaded.append(file_name)
                except Exception as e:
                    print(f"   ❌ 다운로드 실패: {e}")

            # 창 닫기 및 복귀
            if len(driver.window_handles) > initial_windows:
                driver.close()
                driver.switch_to.window(main_window)

            return downloaded
        else:
            print("4. 첨부파일 없음")

            # 창 닫기 및 복귀
            if len(driver.window_handles) > initial_windows:
                driver.close()
                driver.switch_to.window(main_window)

            return []

    except Exception as e:
        print(f"   ❌ 다운로드 오류: {e}")

        # 메인 창으로 복귀 시도
        try:
            driver.switch_to.window(main_window)
        except:
            pass

        return []

def main():
    """메인 실행 함수"""
    print("=" * 60)
    print("나라장터 메뉴 네비게이션 입찰공고 검색")
    print("=" * 60)

    driver = None
    try:
        # 드라이버 설정
        driver = setup_driver()
        driver.set_window_size(1400, 900)

        # 입찰공고 목록 페이지로 이동
        if navigate_to_bid_list(driver):
            print("\n✅ 입찰공고 페이지 도달")

            # 키워드 검색
            results = search_by_keyword(driver, "데이터분석")

            if results:
                # 첫 번째 결과에서 파일 다운로드
                print("\n" + "=" * 40)
                print("첫 번째 검색 결과 처리")
                print("=" * 40)

                files = download_from_result(driver, results[0])

                if files:
                    print(f"\n✅ 총 {len(files)}개 파일 다운로드 완료:")
                    for file in files:
                        print(f"   - {file}")
                else:
                    print("\n⚠️ 다운로드된 파일 없음")
            else:
                print("\n⚠️ 검색 결과 없음")
        else:
            print("\n❌ 입찰공고 페이지 접근 실패")

        # 확인을 위해 대기
        print("\n15초 후 종료됩니다...")
        time.sleep(15)

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