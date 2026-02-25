#!/usr/bin/env python3
"""최종 스크린샷 캡처 - 충분한 대기시간"""
import asyncio, os, json
from datetime import datetime, timedelta, timezone
from jose import jwt

SECRET_KEY = "odin-secret-key-2025"
token_data = {
    "sub": "1",
    "email": "test@odin.ai",
    "exp": datetime.now(timezone.utc) + timedelta(hours=24),
}
ACCESS_TOKEN = jwt.encode(token_data, SECRET_KEY, algorithm="HS256")

DIR = "/Users/blockmeta/Desktop/workspace/odin-ai/docs/screenshots/phase1_3"
URL = "http://localhost:3000"
os.makedirs(DIR, exist_ok=True)

async def main():
    from playwright.async_api import async_playwright
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        ctx = await browser.new_context(viewport={"width": 1440, "height": 900}, locale="ko-KR")
        page = await ctx.new_page()

        # Inject token
        await page.goto(f"{URL}/login", wait_until="networkidle")
        await page.evaluate(f"""() => {{
            localStorage.setItem('odin_ai_token', '{ACCESS_TOKEN}');
            localStorage.setItem('odin_ai_refresh_token', '{ACCESS_TOKEN}');
        }}""")

        # Dashboard - wait for content
        await page.goto(f"{URL}/dashboard", wait_until="networkidle")
        await page.wait_for_timeout(8000)
        # Try to wait for actual content
        try:
            await page.wait_for_selector('.MuiGrid-root, .MuiCard-root, .MuiPaper-root', timeout=10000)
        except:
            pass
        await page.wait_for_timeout(2000)
        await page.screenshot(path=os.path.join(DIR, "11_dashboard.png"), full_page=True)
        print(f"  ✅ 대시보드: {page.url}")

        # Search
        await page.goto(f"{URL}/search", wait_until="networkidle")
        await page.wait_for_timeout(5000)
        try:
            await page.wait_for_selector('.MuiTextField-root, input', timeout=10000)
        except:
            pass
        await page.wait_for_timeout(2000)
        await page.screenshot(path=os.path.join(DIR, "12_search_page.png"), full_page=True)
        print(f"  ✅ 검색: {page.url}")

        # Graph Explorer - empty
        await page.goto(f"{URL}/graph", wait_until="networkidle")
        await page.wait_for_timeout(5000)
        try:
            await page.wait_for_selector('.MuiTextField-root, .MuiCard-root, .MuiPaper-root, svg', timeout=10000)
        except:
            pass
        await page.wait_for_timeout(2000)
        await page.screenshot(path=os.path.join(DIR, "13_graph_explorer_empty.png"), full_page=True)
        print(f"  ✅ 그래프 탐색기 (빈 상태): {page.url}")

        # Graph Explorer - with search
        if "/login" not in page.url:
            inputs = await page.query_selector_all('input')
            for inp in inputs:
                placeholder = await inp.get_attribute('placeholder') or ''
                if '질문' in placeholder or '입찰' in placeholder or '검색' in placeholder:
                    await inp.fill("충청남도 건설 트렌드")
                    await inp.press("Enter")
                    print("    검색 실행 중 (45초 대기)...")
                    await page.wait_for_timeout(45000)
                    await page.screenshot(path=os.path.join(DIR, "14_graph_explorer_result.png"), full_page=True)
                    print("  ✅ 그래프 탐색기 (검색 결과)")
                    break
            else:
                # Try clicking any input and typing
                if inputs:
                    await inputs[0].fill("충청남도 건설 트렌드")
                    await inputs[0].press("Enter")
                    await page.wait_for_timeout(45000)
                    await page.screenshot(path=os.path.join(DIR, "14_graph_explorer_result.png"), full_page=True)
                    print("  ✅ 그래프 탐색기 (검색 결과 - fallback)")

        # Sidebar
        await page.goto(f"{URL}/graph", wait_until="networkidle")
        await page.wait_for_timeout(5000)
        await page.screenshot(path=os.path.join(DIR, "15_sidebar_navigation.png"),
                            clip={"x": 0, "y": 0, "width": 280, "height": 900})
        print("  ✅ 사이드바 네비게이션")

        await browser.close()

    files = sorted([f for f in os.listdir(DIR) if f.endswith('.png')])
    print(f"\n📁 PNG ({len(files)}개):")
    for f in files:
        sz = os.path.getsize(os.path.join(DIR, f))
        print(f"  {f} ({sz//1024}KB)")

asyncio.run(main())
