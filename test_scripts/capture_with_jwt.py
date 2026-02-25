#!/usr/bin/env python3
"""
JWT 토큰을 직접 생성하여 인증된 상태에서 스크린샷 캡처
"""

import asyncio
import os
import sys
import json
from datetime import datetime, timedelta

# JWT 토큰 직접 생성
try:
    from jose import jwt
except ImportError:
    os.system("pip install python-jose[cryptography]")
    from jose import jwt

SECRET_KEY = "odin-secret-key-2025"
ALGORITHM = "HS256"

# user_id=1 로 JWT 생성
token_data = {
    "sub": "1",
    "email": "test@odin.ai",
    "exp": datetime.utcnow() + timedelta(hours=24),
}
ACCESS_TOKEN = jwt.encode(token_data, SECRET_KEY, algorithm=ALGORITHM)
print(f"JWT Token: {ACCESS_TOKEN[:40]}...")

SCREENSHOT_DIR = "/Users/blockmeta/Desktop/workspace/odin-ai/docs/screenshots/phase1_3"
FRONTEND_URL = "http://localhost:3000"
os.makedirs(SCREENSHOT_DIR, exist_ok=True)

async def main():
    from playwright.async_api import async_playwright

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={"width": 1440, "height": 900},
            locale="ko-KR"
        )
        page = await context.new_page()

        # 1. 먼저 로그인 페이지 접속하여 localStorage에 토큰 주입
        await page.goto(f"{FRONTEND_URL}/login", wait_until="networkidle")
        await page.evaluate(f"""() => {{
            localStorage.setItem('odin_ai_token', '{ACCESS_TOKEN}');
            localStorage.setItem('odin_ai_refresh_token', '{ACCESS_TOKEN}');
        }}""")
        print("  JWT 토큰 localStorage에 주입 완료")

        # 2. 대시보드
        await page.goto(f"{FRONTEND_URL}/dashboard", wait_until="networkidle")
        await page.wait_for_timeout(3000)
        url = page.url
        print(f"  대시보드 URL: {url}")
        await page.screenshot(path=os.path.join(SCREENSHOT_DIR, "11_dashboard.png"), full_page=True)
        if "/login" not in url:
            print("  ✅ 대시보드 페이지 캡처 성공")
        else:
            print("  ⚠️ 여전히 로그인 페이지 (인증 실패)")

        # 3. 검색 페이지
        await page.goto(f"{FRONTEND_URL}/search", wait_until="networkidle")
        await page.wait_for_timeout(2000)
        await page.screenshot(path=os.path.join(SCREENSHOT_DIR, "12_search_page.png"), full_page=True)
        url = page.url
        print(f"  ✅ 검색 페이지 ({url})")

        # 4. 지식 그래프 - 빈 상태
        await page.goto(f"{FRONTEND_URL}/graph", wait_until="networkidle")
        await page.wait_for_timeout(3000)
        await page.screenshot(path=os.path.join(SCREENSHOT_DIR, "13_graph_explorer_empty.png"), full_page=True)
        url = page.url
        print(f"  ✅ 지식 그래프 빈 상태 ({url})")

        # 5. 지식 그래프 - 검색 실행
        if "/login" not in page.url:
            try:
                # 검색 입력 필드 찾기 (여러 셀렉터 시도)
                selectors = [
                    'input[placeholder*="질문"]',
                    'input[placeholder*="입찰"]',
                    'input[type="text"]',
                    '.MuiTextField-root input',
                    'input',
                ]
                search_input = None
                for sel in selectors:
                    search_input = await page.query_selector(sel)
                    if search_input:
                        print(f"    검색 필드 발견: {sel}")
                        break

                if search_input:
                    await search_input.fill("충청남도 건설 트렌드")
                    await search_input.press("Enter")
                    print("    검색 실행 중... (최대 45초 대기)")
                    await page.wait_for_timeout(45000)
                    await page.screenshot(path=os.path.join(SCREENSHOT_DIR, "14_graph_explorer_result.png"), full_page=True)
                    print("  ✅ 지식 그래프 검색 결과 캡처")
                else:
                    print("  ⚠️ 검색 필드를 찾을 수 없음")
            except Exception as e:
                print(f"  ⚠️ 검색 캡처 실패: {e}")
                await page.screenshot(path=os.path.join(SCREENSHOT_DIR, "14_graph_explorer_error.png"), full_page=True)

        # 6. 사이드바
        await page.goto(f"{FRONTEND_URL}/graph", wait_until="networkidle")
        await page.wait_for_timeout(2000)
        await page.screenshot(path=os.path.join(SCREENSHOT_DIR, "15_sidebar_navigation.png"),
                            clip={"x": 0, "y": 0, "width": 280, "height": 900})
        print("  ✅ 사이드바 네비게이션 캡처")

        await browser.close()

    # 결과 요약
    files = sorted([f for f in os.listdir(SCREENSHOT_DIR) if f.endswith('.png')])
    print(f"\n📁 PNG 스크린샷 ({len(files)}개):")
    for f in files:
        size = os.path.getsize(os.path.join(SCREENSHOT_DIR, f))
        print(f"  - {f} ({size//1024}KB)")

asyncio.run(main())
