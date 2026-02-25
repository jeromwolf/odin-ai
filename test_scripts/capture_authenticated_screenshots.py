#!/usr/bin/env python3
"""
인증된 상태에서 프론트엔드 스크린샷 캡처
Playwright Python API 사용
"""

import asyncio
import os
import sys

SCREENSHOT_DIR = "/Users/blockmeta/Desktop/workspace/odin-ai/docs/screenshots/phase1_3"
FRONTEND_URL = "http://localhost:3000"

# 테스트 계정
TEST_EMAIL = "test1@example.com"
TEST_PASSWORD = "testpassword123"

os.makedirs(SCREENSHOT_DIR, exist_ok=True)

async def main():
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        print("Playwright not installed. Installing...")
        os.system("pip install playwright && playwright install chromium")
        from playwright.async_api import async_playwright

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={"width": 1440, "height": 900},
            locale="ko-KR"
        )
        page = await context.new_page()

        # 1. 로그인
        print("\n🔐 로그인 시도...")
        await page.goto(f"{FRONTEND_URL}/login", wait_until="networkidle")
        await page.screenshot(path=os.path.join(SCREENSHOT_DIR, "10_login_page.png"))
        print("  ✅ 로그인 페이지 캡처")

        # 이메일/비밀번호 입력
        await page.fill('input[type="email"], input[name="email"], input:first-of-type', TEST_EMAIL)
        await page.fill('input[type="password"], input[name="password"]', TEST_PASSWORD)
        await page.click('button[type="submit"]')
        await page.wait_for_timeout(3000)

        # 로그인 성공 확인
        current_url = page.url
        if "/login" not in current_url:
            print(f"  ✅ 로그인 성공 → {current_url}")
        else:
            # 토큰 직접 설정
            print("  ⚠️ 로그인 실패, JWT 토큰 직접 설정...")
            import requests
            try:
                r = requests.post(f"http://localhost:9000/api/auth/login",
                                json={"email": TEST_EMAIL, "password": TEST_PASSWORD},
                                timeout=10)
                if r.status_code == 200:
                    token = r.json().get("access_token")
                    if token:
                        await page.evaluate(f"""() => {{
                            localStorage.setItem('odin_ai_token', '{token}');
                        }}""")
                        print(f"  ✅ JWT 토큰 설정 완료")
                else:
                    # 다른 계정 시도
                    r = requests.post(f"http://localhost:9000/api/auth/login",
                                    json={"email": "admin@odin.ai", "password": "admin123"},
                                    timeout=10)
                    if r.status_code == 200:
                        token = r.json().get("access_token")
                        if token:
                            await page.evaluate(f"""() => {{
                                localStorage.setItem('odin_ai_token', '{token}');
                            }}""")
                            print(f"  ✅ 관리자 JWT 토큰 설정 완료")
            except Exception as e:
                print(f"  ⚠️ 토큰 설정 실패: {e}")

        # 2. 대시보드
        print("\n📸 페이지 캡처 시작...")
        await page.goto(f"{FRONTEND_URL}/dashboard", wait_until="networkidle")
        await page.wait_for_timeout(2000)
        await page.screenshot(path=os.path.join(SCREENSHOT_DIR, "11_dashboard.png"), full_page=True)
        print("  ✅ 대시보드 페이지")

        # 3. 검색 페이지
        await page.goto(f"{FRONTEND_URL}/search", wait_until="networkidle")
        await page.wait_for_timeout(2000)
        await page.screenshot(path=os.path.join(SCREENSHOT_DIR, "12_search_page.png"), full_page=True)
        print("  ✅ 검색 페이지")

        # 4. 지식 그래프 탐색기 - 빈 상태
        await page.goto(f"{FRONTEND_URL}/graph", wait_until="networkidle")
        await page.wait_for_timeout(3000)
        await page.screenshot(path=os.path.join(SCREENSHOT_DIR, "13_graph_explorer_empty.png"), full_page=True)
        print("  ✅ 지식 그래프 탐색기 (빈 상태)")

        # 5. 지식 그래프 - 검색 실행
        try:
            search_input = await page.query_selector('input[placeholder*="질문"]')
            if search_input:
                await search_input.fill("충청남도 건설 트렌드")
                # Send 버튼 클릭 또는 Enter
                send_btn = await page.query_selector('button[aria-label*="send"], button svg')
                if send_btn:
                    await send_btn.click()
                else:
                    await search_input.press("Enter")
                # 답변 대기 (최대 60초)
                await page.wait_for_timeout(30000)
                await page.screenshot(path=os.path.join(SCREENSHOT_DIR, "14_graph_explorer_result.png"), full_page=True)
                print("  ✅ 지식 그래프 탐색기 (검색 결과)")
            else:
                print("  ⚠️ 검색 입력 필드를 찾을 수 없음")
        except Exception as e:
            print(f"  ⚠️ 그래프 검색 캡처 실패: {e}")
            await page.screenshot(path=os.path.join(SCREENSHOT_DIR, "14_graph_explorer_result.png"), full_page=True)

        # 6. 사이드바 네비게이션 (지식 그래프 메뉴 표시)
        await page.goto(f"{FRONTEND_URL}/graph", wait_until="networkidle")
        await page.wait_for_timeout(2000)
        await page.screenshot(path=os.path.join(SCREENSHOT_DIR, "15_sidebar_navigation.png"),
                            clip={"x": 0, "y": 0, "width": 300, "height": 900})
        print("  ✅ 사이드바 네비게이션")

        await browser.close()

    # 결과 요약
    files = sorted([f for f in os.listdir(SCREENSHOT_DIR) if f.endswith('.png')])
    print(f"\n📁 PNG 스크린샷 ({len(files)}개):")
    for f in files:
        size = os.path.getsize(os.path.join(SCREENSHOT_DIR, f))
        print(f"  - {f} ({size//1024}KB)")

asyncio.run(main())
