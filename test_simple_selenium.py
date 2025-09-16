#!/usr/bin/env python3
"""
간단한 Selenium 테스트
"""

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time

print("Selenium 테스트 시작...")

try:
    # Chrome 옵션 설정
    options = Options()
    options.add_argument('--headless')  # 헤드리스 모드
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    
    print("Chrome 드라이버 초기화 중...")
    driver = webdriver.Chrome(options=options)
    
    print("나라장터 접속 시도...")
    driver.get("https://www.g2b.go.kr")
    
    time.sleep(2)
    
    print(f"페이지 제목: {driver.title}")
    print(f"현재 URL: {driver.current_url}")
    
    driver.quit()
    print("✅ 테스트 성공!")
    
except Exception as e:
    print(f"❌ 오류 발생: {e}")
    import traceback
    traceback.print_exc()