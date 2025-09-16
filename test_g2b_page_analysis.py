#!/usr/bin/env python3
"""
나라장터 페이지 구조 상세 분석
- 실제 페이지 구조 파악
- 입찰공고 검색 경로 찾기
- 사용자가 제공한 스크린샷 기반 UI 매칭
"""

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
import time
import os

def setup_driver():
    """Chrome 드라이버 설정"""
    options = Options()
    # GUI 모드로 실행하여 직접 확인
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

def analyze_main_page(driver):
    """메인 페이지 구조 분석"""
    print("\n🔍 나라장터 메인 페이지 분석")

    try:
        driver.get("https://www.g2b.go.kr")
        time.sleep(5)

        print(f"페이지 제목: {driver.title}")
        print(f"현재 URL: {driver.current_url}")

        # 모든 메뉴 항목 찾기
        print("\n📋 메뉴 구조 분석:")

        # 다양한 메뉴 선택자 시도
        menu_selectors = [
            "nav a",
            ".gnb a",
            ".menu a",
            "[class*='menu'] a",
            "[class*='nav'] a",
            "header a",
            ".top-menu a"
        ]

        all_menus = []
        for selector in menu_selectors:
            try:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                if elements:
                    print(f"\n{selector}로 찾은 메뉴들:")
                    for elem in elements[:10]:  # 처음 10개만
                        try:
                            text = elem.text.strip()
                            href = elem.get_attribute('href')
                            if text and '입찰' in text:
                                print(f"  ★ {text}: {href}")
                                all_menus.append((text, href, elem))
                            elif text:
                                print(f"    {text}: {href}")
                        except:
                            pass
            except:
                continue

        # 입찰 관련 링크 상세 분석
        if all_menus:
            print(f"\n🎯 입찰 관련 메뉴 {len(all_menus)}개 발견")
            for i, (text, href, elem) in enumerate(all_menus, 1):
                print(f"[{i}] {text}")
                print(f"    URL: {href}")
                print(f"    클래스: {elem.get_attribute('class')}")
                print(f"    ID: {elem.get_attribute('id')}")
                print()

        return all_menus

    except Exception as e:
        print(f"❌ 메인 페이지 분석 오류: {e}")
        return []

def try_bid_menu_navigation(driver, menus):
    """입찰 메뉴 네비게이션 시도"""
    print("\n🚀 입찰 메뉴 클릭 테스트")

    for i, (text, href, elem) in enumerate(menus, 1):
        try:
            print(f"\n[{i}] '{text}' 메뉴 클릭 시도...")

            # 메뉴 클릭
            actions = ActionChains(driver)

            # 마우스 오버 먼저
            actions.move_to_element(elem).perform()
            time.sleep(1)

            # 클릭
            elem.click()
            time.sleep(3)

            print(f"  클릭 후 URL: {driver.current_url}")
            print(f"  클릭 후 제목: {driver.title}")

            # 서브메뉴나 변화 확인
            page_source = driver.page_source
            if '입찰공고' in page_source or '공고목록' in page_source:
                print("  ✅ 입찰공고 관련 페이지 감지!")

                # 입찰공고 관련 링크 찾기
                sub_links = driver.find_elements(By.XPATH, "//*[contains(text(), '입찰공고') or contains(text(), '공고목록')]")
                for link in sub_links[:5]:
                    try:
                        print(f"    • {link.text}: {link.get_attribute('href')}")
                    except:
                        pass

                return True

            # iframe 체크
            iframes = driver.find_elements(By.TAG_NAME, "iframe")
            if iframes:
                print(f"  iframe {len(iframes)}개 발견, 첫 번째 확인...")
                driver.switch_to.frame(iframes[0])
                time.sleep(2)

                iframe_source = driver.page_source
                if '공고명' in iframe_source or '검색' in iframe_source:
                    print("  ✅ iframe에서 검색 인터페이스 발견!")
                    return analyze_search_interface(driver)

                driver.switch_to.default_content()

        except Exception as e:
            print(f"  ❌ 클릭 오류: {e}")
            continue

    return False

def analyze_search_interface(driver):
    """검색 인터페이스 분석"""
    print("\n🔍 검색 인터페이스 분석")

    try:
        # 모든 입력 필드 찾기
        inputs = driver.find_elements(By.CSS_SELECTOR, "input[type='text']")
        print(f"텍스트 입력 필드 {len(inputs)}개 발견:")

        for i, inp in enumerate(inputs, 1):
            try:
                name = inp.get_attribute('name')
                placeholder = inp.get_attribute('placeholder')
                title = inp.get_attribute('title')
                print(f"  [{i}] name: {name}, placeholder: {placeholder}, title: {title}")

                # 공고명 필드로 보이는 것 찾기
                if any(keyword in str(attr).lower() for attr in [name, placeholder, title] for keyword in ['bid', '공고', 'nm']):
                    print(f"      ★ 공고명 필드로 추정됨")
                    return test_search_functionality(driver, inp)
            except:
                pass

        return False

    except Exception as e:
        print(f"❌ 검색 인터페이스 분석 오류: {e}")
        return False

def test_search_functionality(driver, search_input):
    """검색 기능 테스트"""
    print("\n⚡ 검색 기능 테스트")

    try:
        # 키워드 입력
        keyword = "데이터분석"
        print(f"1. '{keyword}' 입력...")

        search_input.clear()
        search_input.send_keys(keyword)
        time.sleep(1)

        # 검색 버튼 찾기
        search_buttons = driver.find_elements(By.XPATH, "//*[contains(text(), '검색') or @value='검색'][@type='button' or @type='submit' or name()='button']")

        if search_buttons:
            print("2. 검색 버튼 클릭...")
            search_buttons[0].click()
            time.sleep(3)
        else:
            print("2. 엔터키로 검색...")
            search_input.send_keys("\n")
            time.sleep(3)

        # 결과 확인
        page_source = driver.page_source
        if keyword in page_source or '검색결과' in page_source:
            print("3. ✅ 검색 실행 성공!")

            # 검색 결과 테이블 찾기
            result_tables = driver.find_elements(By.CSS_SELECTOR, "table, tbody, .list, .result")

            for table in result_tables[:3]:
                try:
                    rows = table.find_elements(By.TAG_NAME, "tr")
                    if len(rows) > 1:  # 헤더 제외하고 데이터 있음
                        print(f"4. 검색 결과 테이블 발견: {len(rows)}행")

                        # 첫 번째 결과 클릭 테스트
                        data_rows = rows[1:4]  # 헤더 제외하고 처음 3개
                        for i, row in enumerate(data_rows, 1):
                            try:
                                print(f"\n[{i}] 결과 행 클릭 테스트...")
                                row_text = row.text[:100]
                                print(f"    내용: {row_text}...")

                                # 클릭 시도
                                row.click()
                                time.sleep(2)

                                # 새 창이나 팝업 확인
                                if len(driver.window_handles) > 1:
                                    print("    ✅ 팝업 창 열림!")
                                    driver.switch_to.window(driver.window_handles[-1])
                                    return analyze_detail_popup(driver)
                                else:
                                    print("    - 같은 창에서 변화 확인...")
                                    # 상세 내용이나 첨부파일 찾기
                                    if '첨부' in driver.page_source or 'download' in driver.page_source.lower():
                                        print("    ✅ 상세 페이지에서 첨부파일 감지!")
                                        return find_and_download_files(driver)

                            except Exception as e:
                                print(f"    ❌ 행 클릭 오류: {e}")
                                continue

                        return True
                except:
                    continue

        return False

    except Exception as e:
        print(f"❌ 검색 테스트 오류: {e}")
        return False

def analyze_detail_popup(driver):
    """상세 팝업 분석 및 파일 다운로드"""
    print("\n📄 상세 팝업 분석")

    try:
        print(f"팝업 제목: {driver.title}")
        print(f"팝업 URL: {driver.current_url}")

        # 첨부파일 링크 찾기
        return find_and_download_files(driver)

    except Exception as e:
        print(f"❌ 팝업 분석 오류: {e}")
        return False

def find_and_download_files(driver):
    """첨부파일 찾기 및 다운로드"""
    print("\n📎 첨부파일 찾기")

    try:
        # 다양한 파일 링크 패턴
        file_patterns = [
            "//a[contains(@href, 'download')]",
            "//a[contains(@onclick, 'download')]",
            "//a[contains(text(), '.pdf')]",
            "//a[contains(text(), '.hwp')]",
            "//a[contains(text(), '.doc')]",
            "//a[contains(text(), '.zip')]",
            "//a[contains(text(), '.xlsx')]",
            "//*[contains(text(), '첨부')]/..//a",
            "//*[contains(text(), '파일')]/..//a"
        ]

        file_links = []
        for pattern in file_patterns:
            try:
                links = driver.find_elements(By.XPATH, pattern)
                file_links.extend(links)
            except:
                continue

        if file_links:
            print(f"✅ {len(file_links)}개 첨부파일 발견!")

            downloaded = []
            for i, link in enumerate(file_links[:3], 1):
                try:
                    file_name = link.text or f"file_{i}"
                    href = link.get_attribute('href')
                    print(f"[{i}] {file_name}: {href}")

                    # 다운로드 시도
                    print(f"    다운로드 중...")
                    link.click()
                    time.sleep(2)
                    downloaded.append(file_name)

                except Exception as e:
                    print(f"    ❌ 다운로드 실패: {e}")

            return len(downloaded) > 0
        else:
            print("❌ 첨부파일을 찾을 수 없음")
            return False

    except Exception as e:
        print(f"❌ 파일 찾기 오류: {e}")
        return False

def main():
    """메인 실행 함수"""
    print("=" * 80)
    print("나라장터 페이지 구조 상세 분석")
    print("=" * 80)

    driver = None
    try:
        # 드라이버 설정
        driver = setup_driver()
        driver.set_window_size(1400, 900)

        # 메인 페이지 분석
        menus = analyze_main_page(driver)

        if menus:
            # 입찰 메뉴 네비게이션 시도
            success = try_bid_menu_navigation(driver, menus)

            if success:
                print("\n🎉 성공! 입찰공고 검색 및 다운로드 완료")
            else:
                print("\n⚠️ 입찰공고 검색 인터페이스를 찾지 못함")
        else:
            print("\n❌ 입찰 메뉴를 찾을 수 없음")

        # 브라우저를 열어둬서 직접 확인 가능
        print("\n30초 후 종료됩니다. 브라우저에서 직접 확인해보세요...")
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