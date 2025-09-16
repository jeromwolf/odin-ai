#!/usr/bin/env python3
"""
나라장터 입찰공고 검색 테스트
"""

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
from datetime import datetime, timedelta

print("="*60)
print("나라장터 입찰공고 검색 테스트")
print("="*60)

try:
    # Chrome 옵션 설정
    options = Options()
    # options.add_argument('--headless')  # 일단 GUI로 테스트
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_argument("user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36")
    
    print("\n1. Chrome 드라이버 초기화...")
    driver = webdriver.Chrome(options=options)
    driver.set_window_size(1280, 800)
    
    # 나라장터 접속
    print("\n2. 나라장터 메인 페이지 접속...")
    driver.get("https://www.g2b.go.kr")
    time.sleep(3)
    
    print(f"   - 페이지 제목: {driver.title}")
    print(f"   - 현재 URL: {driver.current_url}")
    
    # 입찰공고 검색 페이지로 이동 시도
    print("\n3. 입찰공고 검색 페이지 찾기...")
    
    # 메뉴에서 '입찰정보' 찾기
    try:
        # 새로운 차세대 나라장터 구조 파악
        wait = WebDriverWait(driver, 10)
        
        # 메뉴 찾기 시도
        menu_selectors = [
            "//a[contains(text(), '입찰')]",
            "//span[contains(text(), '입찰')]",
            "//div[contains(text(), '입찰')]",
            "//button[contains(text(), '입찰')]"
        ]
        
        found = False
        for selector in menu_selectors:
            try:
                elements = driver.find_elements(By.XPATH, selector)
                if elements:
                    print(f"   - 입찰 관련 메뉴 {len(elements)}개 발견")
                    for elem in elements[:3]:  # 처음 3개만 출력
                        print(f"     • {elem.text}")
                    found = True
                    break
            except:
                continue
        
        if not found:
            print("   - 메뉴에서 입찰 항목을 찾을 수 없음")
        
        # 페이지 소스 확인
        print("\n4. 페이지 구조 분석...")
        
        # iframe 확인
        iframes = driver.find_elements(By.TAG_NAME, "iframe")
        print(f"   - iframe 개수: {len(iframes)}")
        
        # 주요 링크 확인
        links = driver.find_elements(By.TAG_NAME, "a")
        bid_links = [link for link in links if '입찰' in link.text or '공고' in link.text]
        print(f"   - 입찰/공고 관련 링크: {len(bid_links)}개")
        
        # 직접 URL로 접근 시도 (기존 URL)
        print("\n5. 기존 입찰공고 URL로 직접 접근 시도...")
        old_url = "https://www.g2b.go.kr:8101/ep/tbid/tbidFwd.do"
        driver.get(old_url)
        time.sleep(3)
        
        print(f"   - 현재 URL: {driver.current_url}")
        print(f"   - 페이지 제목: {driver.title}")
        
    except Exception as e:
        print(f"   ❌ 오류: {e}")
    
    # 10초 대기 (화면 확인용)
    print("\n10초 후 종료됩니다...")
    time.sleep(10)
    
    driver.quit()
    print("✅ 테스트 완료!")
    
except Exception as e:
    print(f"\n❌ 오류 발생: {e}")
    import traceback
    traceback.print_exc()
    
print("\n" + "="*60)
print("분석 결과:")
print("- 2025년 차세대 나라장터로 변경됨")
print("- 기존 URL 구조가 변경되어 새로운 접근 방법 필요")
print("- API + Selenium 하이브리드 방식 고려")
print("="*60)