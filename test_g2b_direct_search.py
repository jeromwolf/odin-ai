#!/usr/bin/env python3
"""
나라장터 입찰공고 직접 검색
- 입찰공고목록 URL 직접 접근
- 스크린샷에서 본 검색 인터페이스 매칭
- 공고명 "데이터분석" 검색 및 파일 다운로드
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
    """Chrome 드라이버 설정"""
    options = Options()
    # GUI 모드로 실행 (사용자 확인용)
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

def try_direct_bid_search_urls(driver):
    """다양한 입찰공고 검색 URL 직접 시도"""
    print("\n🔗 입찰공고 검색 페이지 직접 접근")

    # 나라장터 입찰공고 관련 URL들
    urls_to_try = [
        # 2025년 신 시스템 예상 URL들
        "https://www.g2b.go.kr/pt/menu/selectSubFrame.do?framesrc=/pt/menu/frameTgong.do",
        "https://www.g2b.go.kr/index.jsp?menuNo=137",
        "https://www.g2b.go.kr/pt/menu/selectSubFrame.do",

        # 기존 시스템 URL들 (8101, 8081 포트)
        "https://www.g2b.go.kr:8101/ep/tbid/tbidList.do",
        "https://www.g2b.go.kr:8081/ep/tbid/tbidList.do",
        "https://www.g2b.go.kr:8080/ep/tbid/tbidList.do",

        # 통합검색 페이지들
        "https://www.g2b.go.kr/pt/menu/selectSubFrame.do?framesrc=/pt/menu/frameGnrl.do",
        "https://www.g2b.go.kr/pt/menu/selectSubFrame.do?framesrc=/pt/menu/frameTgong.do?menuNo=137"
    ]

    for i, url in enumerate(urls_to_try, 1):
        try:
            print(f"\n[{i}] URL 시도: {url}")
            driver.get(url)
            time.sleep(3)

            current_url = driver.current_url
            page_title = driver.title

            print(f"    현재 URL: {current_url}")
            print(f"    페이지 제목: {page_title}")

            # 브라우저 안내 페이지인지 확인
            if "접근 가능 브라우저" in page_title or "브라우저 안내" in page_title:
                print("    ❌ 브라우저 안내 페이지")
                continue

            # 입찰공고 검색 페이지인지 확인
            page_source = driver.page_source.lower()
            if any(keyword in page_source for keyword in ['공고명', 'bidnm', '입찰공고', '검색']):
                print("    ✅ 입찰공고 검색 페이지 접근 성공!")
                return True

            # iframe이 있는지 확인
            iframes = driver.find_elements(By.TAG_NAME, "iframe")
            if iframes:
                print(f"    iframe {len(iframes)}개 발견, 첫 번째 확인...")
                try:
                    driver.switch_to.frame(iframes[0])
                    time.sleep(2)

                    iframe_source = driver.page_source.lower()
                    if any(keyword in iframe_source for keyword in ['공고명', 'bidnm', '입찰공고', '검색']):
                        print("    ✅ iframe에서 입찰공고 검색 인터페이스 발견!")
                        return True

                    driver.switch_to.default_content()
                except:
                    pass

        except Exception as e:
            print(f"    ❌ 접근 실패: {e}")
            continue

    return False

def analyze_search_form(driver):
    """검색 폼 분석 및 공고명 필드 찾기"""
    print("\n🔍 검색 폼 분석")

    try:
        # 모든 input 필드 찾기
        all_inputs = driver.find_elements(By.CSS_SELECTOR, "input")
        text_inputs = [inp for inp in all_inputs if inp.get_attribute('type') in ['text', None] and inp.is_displayed()]

        print(f"   - 화면에 보이는 텍스트 입력 필드: {len(text_inputs)}개")

        # 각 필드 정보 출력
        for i, inp in enumerate(text_inputs, 1):
            try:
                name = inp.get_attribute('name') or ''
                id_attr = inp.get_attribute('id') or ''
                placeholder = inp.get_attribute('placeholder') or ''
                title = inp.get_attribute('title') or ''

                print(f"   [{i}] name: {name}, id: {id_attr}")
                print(f"       placeholder: {placeholder}, title: {title}")

                # 공고명 필드 추정
                if any(keyword in attr.lower() for attr in [name, id_attr, placeholder, title]
                       for keyword in ['bid', '공고', 'nm', 'name', '제목']):
                    print(f"       ★ 공고명 필드로 추정됨")
                    return inp

            except Exception as e:
                print(f"       오류: {e}")

        # 첫 번째 텍스트 필드 반환 (fallback)
        if text_inputs:
            print("   - 첫 번째 텍스트 필드를 공고명 필드로 사용")
            return text_inputs[0]

        return None

    except Exception as e:
        print(f"   ❌ 폼 분석 오류: {e}")
        return None

def perform_search(driver, keyword="데이터분석"):
    """검색 실행"""
    print(f"\n⚡ '{keyword}' 검색 실행")

    try:
        # 공고명 입력 필드 찾기
        bid_name_field = analyze_search_form(driver)

        if not bid_name_field:
            print("   ❌ 공고명 입력 필드를 찾을 수 없음")
            return False

        # 키워드 입력
        print("1. 키워드 입력...")
        bid_name_field.clear()
        bid_name_field.send_keys(keyword)
        time.sleep(1)

        # 검색 버튼 찾기
        print("2. 검색 버튼 찾기...")

        search_selectors = [
            "//button[contains(text(), '검색')]",
            "//input[@type='submit' or @type='button'][contains(@value, '검색')]",
            "//a[contains(text(), '검색')]",
            "//img[@alt='검색']/..",
            "//*[@onclick and contains(., '검색')]"
        ]

        search_btn = None
        for selector in search_selectors:
            try:
                btn = driver.find_element(By.XPATH, selector)
                if btn.is_displayed():
                    search_btn = btn
                    print(f"   - 검색 버튼 발견: {btn.text or btn.get_attribute('value')}")
                    break
            except:
                continue

        # 검색 실행
        if search_btn:
            print("3. 검색 버튼 클릭...")
            search_btn.click()
        else:
            print("3. 엔터키로 검색...")
            bid_name_field.send_keys(Keys.RETURN)

        time.sleep(3)
        return True

    except Exception as e:
        print(f"   ❌ 검색 실행 오류: {e}")
        return False

def get_and_click_results(driver):
    """검색 결과 가져오기 및 첫 번째 결과 클릭"""
    print("\n📋 검색 결과 처리")

    try:
        # 검색 결과 테이블 찾기
        result_selectors = [
            "//table//tbody//tr[position()>1]",  # 테이블의 데이터 행들
            "//tr[contains(@onclick, 'javascript')]",  # 클릭 가능한 행들
            "//div[@class='list' or contains(@class, 'result')]//tr",
            "//tbody//tr[@class or @onclick]"
        ]

        results = []
        for selector in result_selectors:
            try:
                elements = driver.find_elements(By.XPATH, selector)
                if elements:
                    # 실제 데이터가 있는 행인지 확인
                    valid_results = []
                    for elem in elements:
                        if elem.text.strip() and len(elem.text.strip()) > 10:  # 의미있는 데이터가 있는 행
                            valid_results.append(elem)

                    if valid_results:
                        results = valid_results
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

            # 첫 번째 결과 클릭
            print("\n1. 첫 번째 검색 결과 클릭...")
            return click_result_and_download(driver, results[0])

        else:
            print("   - 검색 결과 없음")
            return False

    except Exception as e:
        print(f"   ❌ 결과 처리 오류: {e}")
        return False

def click_result_and_download(driver, result_element):
    """검색 결과 클릭하여 상세 페이지에서 파일 다운로드"""
    print("\n📥 검색 결과 클릭 및 파일 다운로드")

    try:
        # 현재 창 정보 저장
        main_window = driver.current_window_handle
        initial_windows = len(driver.window_handles)

        # 결과 클릭
        print("1. 검색 결과 클릭...")

        # 클릭 가능한 요소 찾기
        clickable = None
        try:
            # 결과 행 내의 링크 찾기
            links = result_element.find_elements(By.TAG_NAME, "a")
            if links:
                # 공고번호나 제목 링크 우선
                for link in links:
                    link_text = link.text.strip()
                    if link_text and len(link_text) > 3:  # 의미있는 텍스트가 있는 링크
                        clickable = link
                        print(f"   - 링크 클릭: {link_text[:50]}...")
                        break

                if not clickable:
                    clickable = links[0]
            else:
                # 행 자체가 클릭 가능한 경우
                clickable = result_element
                print("   - 행 전체 클릭")
        except:
            clickable = result_element

        # 클릭 실행
        if clickable:
            clickable.click()
            time.sleep(3)

        # 새 창/팝업 확인
        print("2. 상세 페이지 확인...")

        popup_opened = len(driver.window_handles) > initial_windows
        if popup_opened:
            print("   - 팝업 창 열림")
            driver.switch_to.window(driver.window_handles[-1])
            time.sleep(2)
        else:
            print("   - 같은 창에서 상세 페이지 로드")

        # 첨부파일 찾기
        print("3. 첨부파일 검색...")

        file_patterns = [
            "//a[contains(@href, 'fileDownload') or contains(@href, 'download')]",
            "//a[contains(@onclick, 'download') or contains(@onclick, 'file')]",
            "//a[contains(text(), '.pdf') or contains(text(), '.hwp') or contains(text(), '.doc')]",
            "//span[contains(text(), '첨부')]/..//a",
            "//td[contains(text(), '첨부') or contains(text(), '파일')]/..//a",
            "//div[contains(@class, 'attach') or contains(@class, 'file')]//a"
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
        seen_hrefs = set()
        for link in file_links:
            href = link.get_attribute('href')
            if href and href not in seen_hrefs:
                unique_files.append(link)
                seen_hrefs.add(href)

        if unique_files:
            print(f"   - {len(unique_files)}개 첨부파일 발견")

            downloaded = []
            for i, link in enumerate(unique_files[:3], 1):
                try:
                    file_name = link.text.strip() or f"file_{i}"
                    href = link.get_attribute('href')
                    print(f"\n   [{i}] {file_name}")
                    print(f"       URL: {href}")

                    # 다운로드 시도
                    print(f"       다운로드 중...")
                    link.click()
                    time.sleep(2)
                    downloaded.append(file_name)
                    print(f"       ✅ 다운로드 완료")

                except Exception as e:
                    print(f"       ❌ 다운로드 실패: {e}")

            # 팝업 닫기
            if popup_opened:
                driver.close()
                driver.switch_to.window(main_window)

            if downloaded:
                print(f"\n🎉 총 {len(downloaded)}개 파일 다운로드 성공!")
                for file in downloaded:
                    print(f"   - {file}")
                return True
            else:
                print("\n⚠️ 파일을 다운로드하지 못함")
                return False

        else:
            print("   - 첨부파일 없음")

            # 팝업 닫기
            if popup_opened:
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
    print("나라장터 입찰공고 직접 검색 및 파일 다운로드")
    print("=" * 80)

    driver = None
    try:
        # 드라이버 설정
        driver = setup_driver()
        driver.set_window_size(1400, 900)

        # 1. 입찰공고 검색 페이지 직접 접근
        if try_direct_bid_search_urls(driver):
            print("\n✅ 입찰공고 검색 페이지 접근 성공")

            # 2. 데이터분석 검색
            if perform_search(driver, "데이터분석"):
                print("\n✅ 검색 실행 성공")

                # 3. 검색 결과에서 파일 다운로드
                success = get_and_click_results(driver)

                if success:
                    print("\n🎉 전체 프로세스 성공!")
                else:
                    print("\n⚠️ 파일 다운로드 실패")
            else:
                print("\n❌ 검색 실행 실패")
        else:
            print("\n❌ 입찰공고 검색 페이지 접근 실패")

        # 다운로드된 파일 확인
        print("\n📁 다운로드 폴더 확인:")
        download_dir = "storage/downloads"
        if os.path.exists(download_dir):
            files = os.listdir(download_dir)
            for file in files:
                file_path = os.path.join(download_dir, file)
                size = os.path.getsize(file_path)
                print(f"   - {file} ({size} bytes)")

        # 브라우저를 잠시 유지하여 결과 확인
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