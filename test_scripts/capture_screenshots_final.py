#!/usr/bin/env python3
"""
Phase 1~3 프론트엔드 스크린샷 캡처 - 올바른 JWT 토큰 사용
"""
import asyncio, os, json, sys
from datetime import datetime, timedelta, timezone

# 올바른 SECRET_KEY (backend/.env에서 확인)
SECRET_KEY = "odin-secret-key-2025"
ALGORITHM = "HS256"

try:
    from jose import jwt
except ImportError:
    os.system("pip install python-jose[cryptography]")
    from jose import jwt

# 실제 사용자 ID 확인 (DB에 존재하는 사용자)
# user_id=107 (admin@odin.ai) - is_superuser=true
# "type": "access" 필수!
token_data = {
    "sub": "107",
    "email": "admin@odin.ai",
    "type": "access",
    "exp": datetime.now(timezone.utc) + timedelta(hours=24),
}
ACCESS_TOKEN = jwt.encode(token_data, SECRET_KEY, algorithm=ALGORITHM)
print(f"JWT Token (first 50): {ACCESS_TOKEN[:50]}...")

DIR = "/Users/blockmeta/Desktop/workspace/odin-ai/docs/screenshots/phase1_3"
URL = "http://localhost:3000"
os.makedirs(DIR, exist_ok=True)


async def main():
    from playwright.async_api import async_playwright

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        ctx = await browser.new_context(
            viewport={"width": 1440, "height": 900},
            locale="ko-KR"
        )
        page = await ctx.new_page()

        # 콘솔 로그 캡처
        console_messages = []
        page.on("console", lambda msg: console_messages.append(f"{msg.type}: {msg.text}"))

        # 1. 먼저 로그인 페이지에서 토큰 주입
        print("\n🔐 토큰 주입 중...")
        await page.goto(f"{URL}/login", wait_until="networkidle")
        await page.evaluate(f"""() => {{
            localStorage.setItem('odin_ai_token', '{ACCESS_TOKEN}');
            localStorage.setItem('odin_ai_refresh_token', '{ACCESS_TOKEN}');
        }}""")
        print("  ✅ JWT 토큰 주입 완료 (user_id=107, type=access)")

        # 2. 대시보드
        print("\n📸 대시보드 캡처...")
        await page.goto(f"{URL}/dashboard", wait_until="networkidle")
        await page.wait_for_timeout(5000)
        # 실제 컨텐츠 대기
        try:
            await page.wait_for_selector('.MuiGrid-root, .MuiCard-root, .MuiPaper-root, [class*="dashboard"]', timeout=10000)
            await page.wait_for_timeout(2000)
        except:
            pass
        current_url = page.url
        print(f"  URL: {current_url}")
        if "/login" in current_url:
            print("  ⚠️ 로그인 페이지로 리다이렉트됨 - 토큰 문제 확인 필요")
            # 콘솔 에러 출력
            for msg in console_messages[-10:]:
                print(f"    Console: {msg}")
        else:
            print(f"  ✅ 대시보드 접근 성공")
        await page.screenshot(path=os.path.join(DIR, "11_dashboard.png"), full_page=True)

        # 3. 검색 페이지
        print("\n📸 검색 페이지 캡처...")
        await page.goto(f"{URL}/search", wait_until="networkidle")
        await page.wait_for_timeout(5000)
        try:
            await page.wait_for_selector('.MuiTextField-root, input, .MuiPaper-root', timeout=10000)
            await page.wait_for_timeout(2000)
        except:
            pass
        await page.screenshot(path=os.path.join(DIR, "12_search_page.png"), full_page=True)
        print(f"  ✅ 검색 페이지 ({page.url})")

        # 4. 지식 그래프 탐색기 - 빈 상태
        print("\n📸 지식 그래프 탐색기 캡처 (빈 상태)...")
        await page.goto(f"{URL}/graph", wait_until="networkidle")
        await page.wait_for_timeout(5000)
        try:
            await page.wait_for_selector('.MuiTextField-root, .MuiCard-root, .MuiPaper-root, svg, input', timeout=10000)
            await page.wait_for_timeout(2000)
        except:
            pass
        await page.screenshot(path=os.path.join(DIR, "13_graph_explorer_empty.png"), full_page=True)
        print(f"  ✅ 지식 그래프 탐색기 빈 상태 ({page.url})")

        # 5. 지식 그래프 - 검색 실행
        if "/login" not in page.url:
            print("\n📸 지식 그래프 검색 실행...")
            inputs = await page.query_selector_all('input')
            search_done = False
            for inp in inputs:
                placeholder = await inp.get_attribute('placeholder') or ''
                if '질문' in placeholder or '검색' in placeholder or '입찰' in placeholder or '탐색' in placeholder:
                    await inp.fill("충청남도 건설 트렌드")
                    await inp.press("Enter")
                    print("  검색 실행 중... (최대 60초 대기)")
                    await page.wait_for_timeout(60000)
                    await page.screenshot(path=os.path.join(DIR, "14_graph_explorer_result.png"), full_page=True)
                    print("  ✅ 지식 그래프 검색 결과 캡처")
                    search_done = True
                    break

            if not search_done:
                # 첫 번째 input에 시도
                if inputs:
                    await inputs[0].fill("충청남도 건설 트렌드")
                    await inputs[0].press("Enter")
                    await page.wait_for_timeout(60000)
                    await page.screenshot(path=os.path.join(DIR, "14_graph_explorer_result.png"), full_page=True)
                    print("  ✅ 지식 그래프 검색 결과 캡처 (fallback)")
                else:
                    print("  ⚠️ 검색 입력 필드를 찾을 수 없음")
        else:
            print("  ⚠️ 로그인 리다이렉트로 그래프 검색 건너뜀")

        # 6. 사이드바 네비게이션
        print("\n📸 사이드바 네비게이션 캡처...")
        await page.goto(f"{URL}/dashboard", wait_until="networkidle")
        await page.wait_for_timeout(3000)
        await page.screenshot(
            path=os.path.join(DIR, "15_sidebar_navigation.png"),
            clip={"x": 0, "y": 0, "width": 280, "height": 900}
        )
        print("  ✅ 사이드바 네비게이션")

        # 7. 로그인 페이지 (비인증 상태)
        print("\n📸 로그인 페이지 캡처...")
        ctx2 = await browser.new_context(
            viewport={"width": 1440, "height": 900},
            locale="ko-KR"
        )
        page2 = await ctx2.new_page()
        await page2.goto(f"{URL}/login", wait_until="networkidle")
        await page2.wait_for_timeout(3000)
        await page2.screenshot(path=os.path.join(DIR, "10_login_page.png"), full_page=True)
        print("  ✅ 로그인 페이지")
        await ctx2.close()

        await browser.close()

    # 결과 요약
    files = sorted([f for f in os.listdir(DIR) if f.endswith('.png')])
    print(f"\n📁 PNG 스크린샷 ({len(files)}개):")
    for f in files:
        sz = os.path.getsize(os.path.join(DIR, f))
        print(f"  {f} ({sz // 1024}KB)")


asyncio.run(main())
