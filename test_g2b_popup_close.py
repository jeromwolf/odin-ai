#!/usr/bin/env python3
"""
나라장터 팝업 처리 및 입찰공고 검색
- 모든 팝업 닫기
- 입찰 → 입찰공고목록 클릭
- 공고명 "데이터분석" 검색
- 결과 클릭하여 파일 다운로드
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

def setup_driver():
    """Chrome 드라이버 설정"""
    options = Options()
    # GUI 모드로 실행
    # options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_argument("user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36")

    # 팝업 차단
    options.add_argument('--disable-popup-blocking')

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

def close_all_popups(driver):
    """모든 팝업 창 닫기"""
    print("\n🚪 팝업 창들 닫기")

    try:
        # 현재 열린 창 확인
        initial_windows = len(driver.window_handles)
        print(f"   - 현재 열린 창: {initial_windows}개")

        if initial_windows > 1:
            # 메인 창 제외하고 모든 창 닫기
            main_window = driver.window_handles[0]

            for window in driver.window_handles[1:]:
                try:
                    driver.switch_to.window(window)
                    print(f"   - 팝업 창 닫기: {driver.title}")
                    driver.close()
                except:
                    pass

            # 메인 창으로 복귀
            driver.switch_to.window(main_window)
            time.sleep(1)

        # 페이지 내 팝업/모달 닫기
        print("   - 페이지 내 팝업 확인...")

        close_selectors = [
            "//button[contains(text(), '닫기')]",
            "//button[contains(text(), '확인')]",
            "//a[contains(text(), '닫기')]",
            "//span[contains(text(), '×')]",
            "//div[@class='close' or contains(@class, 'close')]",
            "//button[@class='close' or contains(@class, 'close')]",
            "//*[@alt='닫기']",
            "//*[@title='닫기']"
        ]

        for selector in close_selectors:
            try:
                elements = driver.find_elements(By.XPATH, selector)
                for elem in elements:
                    if elem.is_displayed():
                        print(f"   - 페이지 내 팝업 닫기: {elem.text}")
                        elem.click()
                        time.sleep(0.5)
            except:
                continue

        print("   ✅ 팝업 정리 완료")
        return True

    except Exception as e:
        print(f"   ❌ 팝업 닫기 오류: {e}")
        return False

def navigate_to_bid_announcement(driver):
    """입찰 → 입찰공고목록 네비게이션"""
    print("\n🎯 입찰 → 입찰공고목록 네비게이션")

    try:
        # 나라장터 접속
        print("1. 나라장터 메인 페이지 접속...")
        driver.get("https://www.g2b.go.kr")
        time.sleep(3)

        # 팝업 닫기
        close_all_popups(driver)

        print(f"   - 페이지 제목: {driver.title}")

        # 입찰 메뉴 찾기
        print("\n2. '입찰' 메뉴 찾기...")

        wait = WebDriverWait(driver, 10)

        # 다양한 입찰 메뉴 선택자
        bid_menu_selectors = [
            "//a[text()='입찰']",
            "//span[text()='입찰']/..",
            "//li[contains(@class, 'menu')]//a[text()='입찰']",
            "//*[@id='gnb']//a[text()='입찰']",
            "//nav//a[text()='입찰']"
        ]

        bid_menu = None
        for selector in bid_menu_selectors:
            try:
                elements = driver.find_elements(By.XPATH, selector)
                for elem in elements:
                    if elem.is_displayed():
                        bid_menu = elem
                        print(f"   - 입찰 메뉴 발견: {elem.text}")
                        break
                if bid_menu:
                    break
            except:
                continue

        if not bid_menu:
            print("   ❌ 입찰 메뉴를 찾을 수 없음")
            return False

        # 입찰 메뉴에 마우스 오버
        print("\n3. 입찰 메뉴 호버...")
        actions = ActionChains(driver)
        actions.move_to_element(bid_menu).perform()
        time.sleep(2)

        # 서브메뉴에서 입찰공고목록 찾기
        print("\n4. '입찰공고목록' 서브메뉴 찾기...")

        submenu_selectors = [
            "//a[contains(text(), '입찰공고목록')]",
            "//a[contains(text(), '입찰공고')]",
            "//a[contains(text(), '공고목록')]",
            "//ul[@class='sub' or contains(@class, 'submenu')]//a[contains(text(), '공고')]"
        ]

        submenu_found = False
        for selector in submenu_selectors:
            try:
                elements = driver.find_elements(By.XPATH, selector)
                for elem in elements:
                    if elem.is_displayed():
                        print(f"   - 입찰공고목록 발견: {elem.text}")
                        elem.click()
                        time.sleep(3)
                        submenu_found = True
                        break
                if submenu_found:
                    break
            except:
                continue

        if submenu_found:
            print("   ✅ 입찰공고목록 페이지 접근 성공")
            return True
        else:
            # 서브메뉴가 없다면 메인 입찰 메뉴 클릭
            print("   - 서브메뉴가 없어 메인 입찰 메뉴 클릭")
            bid_menu.click()
            time.sleep(3)
            return True

    except Exception as e:
        print(f"   ❌ 네비게이션 오류: {e}")
        return False

def search_data_analysis(driver):
    """공고명 '데이터분석' 검색"""
    print("\n🔍 공고명 '데이터분석' 검색")

    try:
        # iframe 처리 (나라장터는 iframe을 많이 사용)
        iframes = driver.find_elements(By.TAG_NAME, "iframe")
        if iframes:
            print(f"   - iframe {len(iframes)}개 발견, 메인 iframe으로 전환")
            driver.switch_to.frame(iframes[0])
            time.sleep(2)

        # 공고명 입력 필드 찾기
        print("1. 공고명 입력 필드 찾기...")

        # 공고명 필드 선택자들
        bid_name_selectors = [
            "input[name*='bidNm']",
            "input[name*='BidNm']",
            "input[id*='bidNm']",
            "input[id*='BidNm']",
            "input[placeholder*='공고명']",
            "input[title*='공고명']"
        ]

        bid_name_input = None
        for selector in bid_name_selectors:
            try:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                for elem in elements:
                    if elem.is_displayed():
                        bid_name_input = elem
                        print(f"   - 공고명 필드 발견: {selector}")
                        break
                if bid_name_input:
                    break
            except:
                continue

        if not bid_name_input:
            # 일반 텍스트 입력 필드 중에서 찾기
            print("   - 일반 텍스트 필드에서 공고명 필드 추정...")
            text_inputs = driver.find_elements(By.CSS_SELECTOR, "input[type='text']")

            for i, inp in enumerate(text_inputs):
                try:
                    if inp.is_displayed():
                        # 위치나 속성으로 공고명 필드 추정
                        parent_text = inp.find_element(By.XPATH, "../..").text
                        if '공고' in parent_text or '제목' in parent_text:
                            bid_name_input = inp
                            print(f"   - {i+1}번째 필드를 공고명으로 추정")
                            break
                except:
                    continue

            # 여전히 못 찾았으면 첫 번째 텍스트 필드 사용
            if not bid_name_input and text_inputs:
                bid_name_input = text_inputs[0]
                print("   - 첫 번째 텍스트 필드 사용")

        if not bid_name_input:
            print("   ❌ 공고명 입력 필드를 찾을 수 없음")
            return []

        # 키워드 입력
        keyword = "데이터분석"
        print(f"2. '{keyword}' 입력...")

        bid_name_input.clear()
        bid_name_input.send_keys(keyword)
        time.sleep(1)

        # 검색 버튼 찾기 및 클릭
        print("3. 검색 버튼 클릭...")

        search_btn_selectors = [
            "//button[contains(text(), '검색')]",
            "//input[@type='submit'][contains(@value, '검색')]",
            "//input[@type='button'][contains(@value, '검색')]",
            "//a[contains(text(), '검색')]",
            "//img[@alt='검색']/.."
        ]

        clicked = False
        for selector in search_btn_selectors:
            try:
                btn = driver.find_element(By.XPATH, selector)
                if btn.is_displayed():
                    btn.click()
                    clicked = True
                    print(f"   - 검색 버튼 클릭 성공")
                    break
            except:
                continue

        if not clicked:
            # 엔터키로 검색
            bid_name_input.send_keys(Keys.RETURN)
            print("   - 엔터키로 검색")

        time.sleep(3)

        # 검색 결과 확인
        print("\n4. 검색 결과 확인...")
        return get_search_results(driver)

    except Exception as e:
        print(f"   ❌ 검색 오류: {e}")
        return []

def get_search_results(driver):
    """검색 결과 가져오기"""
    try:
        # 검색 결과 테이블 찾기
        result_selectors = [
            "//table[@class='table' or contains(@class, 'list')]//tbody//tr",
            "//div[@class='list' or contains(@class, 'result')]//tr",
            "//tr[contains(@onclick, 'javascript')]",
            "//tbody//tr[@class or @onclick]"
        ]

        results = []
        for selector in result_selectors:
            try:
                elements = driver.find_elements(By.XPATH, selector)
                if len(elements) > 1:  # 헤더 제외
                    results = elements
                    break
            except:
                continue

        if results:
            print(f"   - {len(results)}개 검색 결과 발견")

            # 처음 3개 결과 정보 출력
            for i, result in enumerate(results[:3], 1):
                try:
                    text = result.text[:150] if result.text else "내용 없음"
                    print(f"\n   [{i}] {text}...")
                except:
                    pass

            return results
        else:
            print("   - 검색 결과 없음")
            return []

    except Exception as e:
        print(f"   ❌ 결과 확인 오류: {e}")
        return []

def download_from_first_result(driver, results):
    """첫 번째 검색 결과에서 파일 다운로드"""
    print("\n📥 첫 번째 결과에서 파일 다운로드")

    try:
        if not results:
            print("   ❌ 검색 결과가 없음")
            return False

        first_result = results[0]

        # 현재 창 상태 저장
        main_window = driver.current_window_handle
        initial_windows = len(driver.window_handles)

        print("1. 첫 번째 결과 클릭...")

        # 클릭 가능한 링크 찾기
        clickable = None
        try:
            # 결과 행 내의 링크 찾기
            links = first_result.find_elements(By.TAG_NAME, "a")
            if links:
                clickable = links[0]  # 첫 번째 링크
                print(f"   - 링크 클릭: {clickable.text[:50]}...")
            else:
                # 행 자체가 클릭 가능한 경우
                clickable = first_result
                print("   - 행 전체 클릭")
        except:
            clickable = first_result

        # 클릭 실행
        clickable.click()
        time.sleep(3)

        # 새 창/팝업 확인
        print("2. 상세 페이지/팝업 확인...")

        if len(driver.window_handles) > initial_windows:
            print("   - 팝업 창 열림")
            driver.switch_to.window(driver.window_handles[-1])
            time.sleep(2)
        else:
            print("   - 같은 창에서 상세 페이지 로드")

        # 첨부파일 찾기 및 다운로드
        print("3. 첨부파일 찾기...")

        file_patterns = [
            "//a[contains(@href, 'fileDownload')]",
            "//a[contains(@href, 'download')]",
            "//a[contains(@onclick, 'download')]",
            "//a[contains(text(), '.pdf')]",
            "//a[contains(text(), '.hwp')]",
            "//a[contains(text(), '.doc')]",
            "//a[contains(text(), '.zip')]",
            "//span[contains(text(), '첨부')]/..//a",
            "//td[contains(text(), '첨부')]/..//a",
            "//div[contains(text(), '첨부')]//a"
        ]

        file_links = []
        for pattern in file_patterns:
            try:
                links = driver.find_elements(By.XPATH, pattern)
                file_links.extend(links)
            except:
                continue

        if file_links:
            print(f"   - {len(file_links)}개 첨부파일 발견")

            downloaded = []
            for i, link in enumerate(file_links[:3], 1):
                try:
                    file_name = link.text or f"file_{i}"
                    href = link.get_attribute('href')
                    print(f"   [{i}] {file_name}: {href}")

                    # 다운로드 시도
                    link.click()
                    time.sleep(2)
                    downloaded.append(file_name)
                    print(f"       ✅ 다운로드 완료")

                except Exception as e:
                    print(f"       ❌ 다운로드 실패: {e}")

            # 팝업이었다면 닫기
            if len(driver.window_handles) > initial_windows:
                driver.close()
                driver.switch_to.window(main_window)

            if downloaded:
                print(f"\n✅ 총 {len(downloaded)}개 파일 다운로드 완료")
                return True
            else:
                print("\n⚠️ 다운로드된 파일 없음")
                return False

        else:
            print("   - 첨부파일 없음")

            # 팝업이었다면 닫기
            if len(driver.window_handles) > initial_windows:
                driver.close()
                driver.switch_to.window(main_window)

            return False

    except Exception as e:
        print(f"   ❌ 다운로드 오류: {e}")

        # 메인 창으로 복귀
        try:
            driver.switch_to.window(main_window)
        except:
            pass

        return False

def main():
    """메인 실행 함수"""
    print("=" * 80)
    print("나라장터 팝업 처리 및 입찰공고 검색")
    print("=" * 80)

    driver = None
    try:
        # 드라이버 설정
        driver = setup_driver()
        driver.set_window_size(1400, 900)

        # 1. 입찰공고목록 페이지로 이동
        if navigate_to_bid_announcement(driver):
            print("\n✅ 입찰공고목록 페이지 접근 성공")

            # 2. 데이터분석 검색
            results = search_data_analysis(driver)

            if results:
                print("\n✅ 검색 결과 발견")

                # 3. 첫 번째 결과에서 파일 다운로드
                success = download_from_first_result(driver, results)

                if success:
                    print("\n🎉 파일 다운로드 성공!")
                else:
                    print("\n⚠️ 파일 다운로드 실패")
            else:
                print("\n❌ 검색 결과 없음")
        else:
            print("\n❌ 입찰공고목록 페이지 접근 실패")

        # 확인을 위해 브라우저를 잠시 유지
        print("\n30초 후 브라우저가 종료됩니다...")
        time.sleep(30)

    except Exception as e:
        print(f"\n❌ 실행 오류: {e}")
        import traceback
        traceback.print_exc()

    finally:
        if driver:
            driver.quit()
            print("\n✅ 브라우저 종료")

    print("=" * 80)

if __name__ == "__main__":
    main()