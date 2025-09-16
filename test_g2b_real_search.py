#!/usr/bin/env python3
"""
나라장터 실제 검색 인터페이스 구현
- 공고명 '데이터분석' 검색
- 검색 결과 클릭하여 팝업 열기
- 팝업에서 파일 다운로드
"""

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
import time
import os
from datetime import datetime

def setup_driver():
    """Chrome 드라이버 설정"""
    options = Options()
    # GUI 모드로 실행 (확인용)
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

def search_by_keyword(driver, keyword="데이터분석"):
    """공고명으로 검색"""
    print(f"\n🔍 검색 키워드: '{keyword}'")

    try:
        # 나라장터 메인 페이지 접속
        print("1. 나라장터 접속 중...")
        driver.get("https://www.g2b.go.kr")
        time.sleep(3)

        # 현재 페이지 분석
        print("2. 페이지 구조 분석 중...")

        # 모든 링크 확인
        all_links = driver.find_elements(By.TAG_NAME, "a")
        bid_related = [link for link in all_links if '입찰' in link.text or '공고' in link.text]

        if bid_related:
            print(f"   - 입찰/공고 관련 링크 {len(bid_related)}개 발견")
            for link in bid_related[:5]:
                print(f"     • {link.text}")

        # 입찰정보 검색 페이지로 이동
        print("\n3. 입찰 검색 페이지로 이동 시도...")

        # 여러 URL 패턴 시도
        search_urls = [
            "https://www.g2b.go.kr:8101/ep/tbid/tbidFwd.do",  # 구 시스템
            "https://www.g2b.go.kr/index.jsp",  # 신 시스템 메인
            "https://www.g2b.go.kr/pt/menu/selectSubFrame.do?framesrc=/pt/menu/frameTgong.do"  # 통합검색
        ]

        for url in search_urls:
            print(f"   - URL 시도: {url}")
            driver.get(url)
            time.sleep(3)

            # iframe 체크
            iframes = driver.find_elements(By.TAG_NAME, "iframe")
            if iframes:
                print(f"     • iframe {len(iframes)}개 발견")
                for i, iframe in enumerate(iframes):
                    try:
                        driver.switch_to.frame(iframe)
                        print(f"     • iframe {i+1} 진입")

                        # 입력 필드 찾기
                        text_inputs = driver.find_elements(By.CSS_SELECTOR, "input[type='text']")
                        if text_inputs:
                            print(f"     • 텍스트 입력 필드 {len(text_inputs)}개 발견")
                            break
                        else:
                            driver.switch_to.default_content()
                    except:
                        driver.switch_to.default_content()
                        continue

            # 검색 폼 찾기
            print("\n4. 검색 폼 찾기...")

            # 다양한 선택자 시도
            search_input = None
            selectors = [
                ("input[name*='bidNm']", "공고명 필드 (name)"),
                ("input[id*='bidNm']", "공고명 필드 (id)"),
                ("input[placeholder*='공고']", "공고 placeholder"),
                ("input[title*='공고']", "공고 title"),
                ("input.search", "search 클래스"),
                ("input[type='text']", "일반 텍스트 필드")
            ]

            for selector, desc in selectors:
                try:
                    elements = driver.find_elements(By.CSS_SELECTOR, selector)
                    if elements:
                        search_input = elements[0]
                        print(f"   - {desc} 발견: {len(elements)}개")
                        break
                except:
                    continue

            if search_input:
                break

        if not search_input:
            # 페이지 소스 일부 출력
            print("\n   ❌ 검색 필드를 찾을 수 없음")
            print("   - 페이지 제목:", driver.title)
            print("   - 현재 URL:", driver.current_url)
            return []

        # 키워드 입력
        print(f"4. 키워드 '{keyword}' 입력 중...")
        search_input.clear()
        search_input.send_keys(keyword)
        time.sleep(1)

        # 검색 버튼 클릭 또는 엔터
        search_buttons = [
            "//button[contains(text(), '검색')]",
            "//input[@type='submit']",
            "//button[@type='submit']",
            "//a[contains(text(), '검색')]",
            "//img[@alt='검색']/.."
        ]

        clicked = False
        for xpath in search_buttons:
            try:
                btn = driver.find_element(By.XPATH, xpath)
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
        print("\n5. 검색 결과 확인 중...")

        # 검색 결과 테이블 찾기
        results = driver.find_elements(By.XPATH, "//tr[contains(@onclick, 'javascript')]")
        if not results:
            results = driver.find_elements(By.XPATH, "//a[contains(@href, 'bidDtl')]")
        if not results:
            results = driver.find_elements(By.CSS_SELECTOR, "tbody tr")

        print(f"   - {len(results)}개의 검색 결과 발견")

        return results

    except Exception as e:
        print(f"❌ 검색 중 오류: {e}")
        return []

def download_from_popup(driver, result_element):
    """검색 결과 클릭하여 팝업에서 파일 다운로드"""
    try:
        # 현재 창 저장
        main_window = driver.current_window_handle

        # 결과 클릭
        print("\n📄 공고문 클릭...")
        result_element.click()
        time.sleep(2)

        # 새 창/팝업 확인
        windows = driver.window_handles
        if len(windows) > 1:
            print("   - 팝업 창 열림")
            driver.switch_to.window(windows[-1])
            time.sleep(2)

            # 첨부파일 섹션 찾기
            print("   - 첨부파일 확인 중...")

            file_links = []
            # 여러 가능한 첨부파일 링크 패턴
            file_patterns = [
                "//a[contains(@href, 'download')]",
                "//a[contains(@onclick, 'download')]",
                "//a[contains(text(), '.pdf')]",
                "//a[contains(text(), '.hwp')]",
                "//a[contains(text(), '.doc')]",
                "//a[contains(text(), '.zip')]",
                "//img[@alt='다운로드']/..",
                "//td[contains(text(), '첨부')]/..//a"
            ]

            for pattern in file_patterns:
                links = driver.find_elements(By.XPATH, pattern)
                file_links.extend(links)

            if file_links:
                print(f"   - {len(file_links)}개 파일 발견")

                # 파일 다운로드
                downloaded_files = []
                for i, link in enumerate(file_links[:3], 1):  # 최대 3개만
                    try:
                        file_name = link.text or f"file_{i}"
                        print(f"   - 다운로드 중: {file_name}")
                        link.click()
                        time.sleep(2)
                        downloaded_files.append(file_name)
                    except:
                        continue

                # 팝업 닫기
                driver.close()
                driver.switch_to.window(main_window)

                return downloaded_files
            else:
                print("   - 첨부파일 없음")
                driver.close()
                driver.switch_to.window(main_window)
                return []
        else:
            print("   - 팝업이 열리지 않음 (같은 창에서 열림)")
            return []

    except Exception as e:
        print(f"   ❌ 다운로드 중 오류: {e}")
        # 메인 창으로 복귀
        try:
            driver.switch_to.window(main_window)
        except:
            pass
        return []

def main():
    """메인 실행 함수"""
    print("=" * 60)
    print("나라장터 실제 검색 인터페이스 테스트")
    print("=" * 60)

    driver = None
    try:
        # 드라이버 설정
        driver = setup_driver()
        driver.set_window_size(1280, 800)

        # 키워드로 검색
        results = search_by_keyword(driver, "데이터분석")

        if results:
            # 처음 3개 결과에서 파일 다운로드 시도
            total_downloaded = []
            for i, result in enumerate(results[:3], 1):
                print(f"\n[{i}번째 결과 처리]")
                try:
                    # 결과 텍스트 출력
                    result_text = result.text[:100] if result.text else "제목 없음"
                    print(f"공고: {result_text}...")

                    # 팝업에서 다운로드
                    files = download_from_popup(driver, result)
                    if files:
                        total_downloaded.extend(files)
                        print(f"✅ {len(files)}개 파일 다운로드 완료")

                    time.sleep(2)
                except Exception as e:
                    print(f"❌ 처리 중 오류: {e}")
                    continue

            # 결과 요약
            print("\n" + "=" * 60)
            print("📊 다운로드 결과 요약")
            print(f"총 {len(total_downloaded)}개 파일 다운로드 완료")
            for file in total_downloaded:
                print(f"  - {file}")
        else:
            print("\n⚠️ 검색 결과가 없습니다")
            print("나라장터 시스템이 변경되었을 수 있습니다")

        # 화면 확인을 위해 잠시 대기
        print("\n10초 후 종료됩니다...")
        time.sleep(10)

    except Exception as e:
        print(f"\n❌ 실행 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()

    finally:
        if driver:
            driver.quit()
            print("\n✅ 브라우저 종료")

    print("=" * 60)

if __name__ == "__main__":
    main()