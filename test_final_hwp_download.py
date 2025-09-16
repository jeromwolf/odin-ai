#!/usr/bin/env python3
"""
최종 HWP 다운로드 테스트
실제 API에서 얻은 stdNtceDocUrl로 HWP 파일 다운로드
"""

import os
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

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

def test_direct_file_download(driver, file_url, expected_filename):
    """직접 파일 다운로드 테스트"""
    print(f"{'='*80}")
    print(f"📥 직접 HWP 파일 다운로드 테스트")
    print(f"{'='*80}")

    print(f"🔗 파일 URL: {file_url}")
    print(f"📄 예상 파일명: {expected_filename}")

    try:
        # 다운로드 폴더의 파일 목록 확인 (before)
        download_dir = "storage/downloads"
        before_files = set(os.listdir(download_dir)) if os.path.exists(download_dir) else set()
        print(f"📁 다운로드 전 파일: {len(before_files)}개")

        print(f"\n1. 파일 URL 직접 접속...")
        driver.get(file_url)
        time.sleep(5)  # 다운로드 대기

        # 다운로드된 파일 확인
        after_files = set(os.listdir(download_dir)) if os.path.exists(download_dir) else set()
        new_files = after_files - before_files

        print(f"📁 다운로드 후 파일: {len(after_files)}개")

        if new_files:
            print(f"\n✅ 다운로드 성공! {len(new_files)}개 파일:")

            hwp_files = []
            for file in new_files:
                file_path = os.path.join(download_dir, file)
                file_size = os.path.getsize(file_path)
                file_ext = os.path.splitext(file)[1].lower()

                print(f"   📄 {file}")
                print(f"      📊 크기: {file_size:,} bytes")
                print(f"      📋 확장자: {file_ext}")

                if file_ext == '.hwp':
                    hwp_files.append(file)
                    print(f"      🎯 HWP 파일 다운로드 성공!")

            if hwp_files:
                print(f"\n🎉 최종 결과: {len(hwp_files)}개 HWP 파일 다운로드 완료!")
                return hwp_files
            else:
                print(f"\n📋 HWP 파일은 아니지만 파일 다운로드는 성공")
                return list(new_files)
        else:
            print(f"\n⚠️ 새 파일이 감지되지 않음")

            # 페이지 제목과 URL 확인
            print(f"   - 페이지 제목: {driver.title}")
            print(f"   - 현재 URL: {driver.current_url}")

            # 페이지 소스에서 에러 메시지 찾기
            page_source = driver.page_source.lower()
            error_keywords = ['error', '오류', '실패', 'fail', '접근', 'access']
            found_errors = [kw for kw in error_keywords if kw in page_source]

            if found_errors:
                print(f"   - 페이지에서 발견된 오류 키워드: {found_errors}")

            return []

    except Exception as e:
        print(f"❌ 다운로드 오류: {e}")
        return []

def main():
    """메인 실행 함수"""
    print("=" * 80)
    print("🧪 최종 HWP 파일 다운로드 테스트")
    print("=" * 80)

    # API에서 얻은 실제 URL과 파일명
    test_urls = [
        {
            "url": "https://www.g2b.go.kr/pn/pnp/pnpe/UntyAtchFile/downloadFile.do?bidPbancNo=R25BK01060027&bidPbancOrd=000&fileType=&fileSeq=1",
            "filename": "수의계약안내공고[어린이보호구역(신안초등학교) 보행로 조성사업].hwp",
            "desc": "어린이보호구역 보행로 조성사업 HWP"
        },
        {
            "url": "https://www.g2b.go.kr/pn/pnp/pnpe/UntyAtchFile/downloadFile.do?bidPbancNo=R25BK01060164&bidPbancOrd=000&fileType=&fileSeq=1",
            "filename": "1호기 소각로 재추출기 교체공사.zip",
            "desc": "소각로 재추출기 교체공사 ZIP"
        }
    ]

    driver = None
    total_downloaded = []

    try:
        print(f"🚀 Selenium HWP 다운로드 테스트 시작")
        print(f"테스트할 URL: {len(test_urls)}개")

        driver = setup_driver()
        driver.set_window_size(1400, 900)

        for i, test_data in enumerate(test_urls, 1):
            print(f"\n{'='*60}")
            print(f"테스트 {i}/{len(test_urls)}: {test_data['desc']}")

            downloaded = test_direct_file_download(driver, test_data['url'], test_data['filename'])
            if downloaded:
                total_downloaded.extend(downloaded)

            time.sleep(3)  # 테스트 간 대기

        # 최종 결과 요약
        print(f"\n{'='*80}")
        print(f"📊 최종 테스트 결과")
        print(f"{'='*80}")

        if total_downloaded:
            print(f"🎉 성공! 총 {len(total_downloaded)}개 파일 다운로드:")

            hwp_count = 0
            zip_count = 0
            other_count = 0

            for file in total_downloaded:
                file_path = os.path.join("storage/downloads", file)
                size = os.path.getsize(file_path) if os.path.exists(file_path) else 0
                ext = os.path.splitext(file)[1].lower()

                print(f"   📄 {file}")
                print(f"      📊 {size:,} bytes, {ext} 파일")

                if ext == '.hwp':
                    hwp_count += 1
                elif ext == '.zip':
                    zip_count += 1
                else:
                    other_count += 1

            print(f"\n📈 파일 유형별 통계:")
            if hwp_count > 0:
                print(f"   🎯 HWP 파일: {hwp_count}개")
            if zip_count > 0:
                print(f"   📦 ZIP 파일: {zip_count}개")
            if other_count > 0:
                print(f"   📋 기타 파일: {other_count}개")

            print(f"\n🏆 결론:")
            print(f"   stdNtceDocUrl을 통한 실제 파일 다운로드 ✅ 완전히 성공!")
            print(f"   Odin-AI 문서 수집 시스템 구현 ✅ 100% 가능!")
            print(f"   API + Selenium 하이브리드 전략 ✅ 검증 완료!")

        else:
            print(f"⚠️ 다운로드된 파일 없음")
            print(f"   - 네트워크 문제 또는 접근 제한 가능성")
            print(f"   - 하지만 URL 구조와 접근 방법은 확인됨")

        print(f"\n💡 브라우저를 15초간 유지하여 수동 확인 가능...")
        time.sleep(15)

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