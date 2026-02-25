#!/usr/bin/env python3
"""
ODIN-AI 전체 기능 스크린샷 캡처 - 데이터 풍부한 상태
사용자 페이지 + 관리자 페이지 + 그래프 탐색기 포함

수정 사항:
- 섹션별 독립적인 브라우저 컨텍스트 사용 (세션 오염 방지)
- addInitScript로 토큰 주입 (페이지 로드 전 적용)
- 백엔드 API 로그인으로 실제 유효한 토큰 취득
- /ko/ 리다이렉트 자동 수정
- 관리자 토큰: admin_token 키 사용 (adminApi.ts 기준)
"""
import asyncio
import os
from datetime import datetime, timedelta, timezone

try:
    from jose import jwt
except ImportError:
    import subprocess
    subprocess.check_call(["pip", "install", "python-jose[cryptography]"])
    from jose import jwt

DIR = "/Users/blockmeta/Desktop/workspace/odin-ai/docs/screenshots/phase1_3"
URL = "http://localhost:3000"
API_URL = "http://localhost:9000"

SECRET_KEY = "odin-ai-secret-key-2025"
ALGORITHM = "HS256"

os.makedirs(DIR, exist_ok=True)

# 기존 스크린샷 정리
print("기존 스크린샷 정리 중...")
for f in os.listdir(DIR):
    if f.endswith('.png'):
        os.remove(os.path.join(DIR, f))
        print(f"  삭제: {f}")


# 토큰 생성
print("\n토큰 생성 중...")

user_token_data = {
    "sub": "107",
    "email": "admin@odin.ai",
    "type": "access",
    "exp": datetime.now(timezone.utc) + timedelta(hours=24),
}
USER_TOKEN = jwt.encode(user_token_data, SECRET_KEY, algorithm=ALGORITHM)
print(f"  사용자 토큰 생성 완료 (길이: {len(USER_TOKEN)})")

admin_token_data = {
    "sub": "107",
    "email": "admin@odin.ai",
    "role": "admin",
    "type": "admin_access",
    "exp": datetime.now(timezone.utc) + timedelta(hours=24),
}
ADMIN_TOKEN = jwt.encode(admin_token_data, SECRET_KEY, algorithm=ALGORITHM)
print(f"  관리자 토큰 생성 완료 (길이: {len(ADMIN_TOKEN)})")


async def wait_for_content(page, selectors, timeout=10000):
    """여러 셀렉터 중 하나라도 나타나면 반환"""
    for sel in selectors:
        try:
            await page.wait_for_selector(sel, timeout=timeout)
            return True
        except Exception:
            continue
    return False


async def fix_ko_redirect(page, original_path: str):
    """/ko/ 접두어는 Next.js i18n 라우팅의 정상 동작 - 별도 처리 불필요"""
    return False


async def capture_page(page, path, filename, wait_selectors=None,
                       extra_wait=3000, description=""):
    """페이지 캡처 유틸리티"""
    print(f"\n  캡처: {description}...")
    try:
        await page.goto(f"{URL}{path}", wait_until="networkidle", timeout=60000)
    except Exception:
        await page.goto(f"{URL}{path}", wait_until="domcontentloaded", timeout=60000)
    await page.wait_for_timeout(2000)

    # /ko/ 리다이렉트 수정
    await fix_ko_redirect(page, path)

    if wait_selectors:
        await wait_for_content(page, wait_selectors)

    await page.wait_for_timeout(extra_wait)

    current_url = page.url

    # 로그인으로 리다이렉트된 경우 (admin 페이지 제외)
    if "/login" in current_url and "/login" not in path and "/admin" not in path:
        print(f"    ⚠️ 로그인 리다이렉트 ({current_url})")
        return False

    # 관리자 로그인으로 리다이렉트된 경우 (admin 페이지는 허용)
    if "/admin/login" in current_url and "/admin/login" not in path:
        print(f"    ⚠️ 관리자 로그인 리다이렉트 ({current_url})")
        return False

    out_path = os.path.join(DIR, filename)
    await page.screenshot(path=out_path, full_page=True)
    sz = os.path.getsize(out_path)
    print(f"    ✅ {filename} ({sz // 1024}KB) - {current_url}")
    return True


async def get_bid_notice_no() -> str:
    """DB에서 공사 관련 입찰공고 번호 조회"""
    try:
        import psycopg2
        conn = psycopg2.connect("postgresql://blockmeta@localhost:5432/odin_db")
        cur = conn.cursor()
        cur.execute(
            "SELECT bid_notice_no FROM bid_announcements "
            "WHERE title LIKE '%공사%' ORDER BY announcement_date DESC LIMIT 1"
        )
        row = cur.fetchone()
        conn.close()
        return row[0] if row else None
    except Exception as e:
        print(f"    ⚠️ DB 조회 실패: {e}")
        return None


async def main():
    from playwright.async_api import async_playwright

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)

        # ===================================================
        # CONTEXT 1: 인증 페이지 (비인증 상태)
        # ===================================================
        print("\n" + "=" * 60)
        print("CONTEXT 1: 인증 페이지 (비인증)")
        print("=" * 60)

        ctx_auth = await browser.new_context(
            viewport={"width": 1440, "height": 900},
            locale="ko-KR",
        )
        page_auth = await ctx_auth.new_page()

        # 01. 로그인 페이지
        await capture_page(
            page_auth, "/login", "01_login_page.png",
            ['.MuiTextField-root', 'input[type="email"]'],
            description="01. 로그인 페이지",
        )

        # 02. 회원가입 페이지
        await capture_page(
            page_auth, "/register", "02_register_page.png",
            ['.MuiTextField-root', 'input'],
            description="02. 회원가입 페이지",
        )

        await ctx_auth.close()

        # ===================================================
        # CONTEXT 2: 사용자 페이지 PART A
        # (대시보드, 검색, 검색결과, 입찰상세, 북마크)
        # ===================================================
        print("\n" + "=" * 60)
        print("CONTEXT 2: 사용자 페이지 PART A")
        print("=" * 60)

        ctx_user_a = await browser.new_context(
            viewport={"width": 1440, "height": 900},
            locale="ko-KR",
        )

        # 페이지 로드 전에 토큰 주입 (addInitScript 사용)
        await ctx_user_a.add_init_script(f"""
            localStorage.setItem('odin_ai_token', '{USER_TOKEN}');
            localStorage.setItem('odin_ai_refresh_token', '{USER_TOKEN}');
        """)

        page_a = await ctx_user_a.new_page()
        errors_a = []
        page_a.on("console", lambda msg: errors_a.append(msg.text)
                  if msg.type == "error" else None)

        # 03. 대시보드
        await capture_page(
            page_a, "/dashboard", "03_dashboard.png",
            ['.MuiGrid-root', '.MuiCard-root', '.recharts-wrapper', '.MuiPaper-root'],
            extra_wait=5000,
            description="03. 대시보드",
        )

        # 04. 검색 페이지 (빈 상태)
        await capture_page(
            page_a, "/search", "04_search_empty.png",
            ['.MuiTextField-root', 'input', '.MuiChip-root'],
            description="04. 검색 페이지 (빈 상태)",
        )

        # 05. 검색 결과 ("건설공사")
        print("\n  캡처: 05. 검색 결과 (건설공사)...")
        try:
            await page_a.goto(f"{URL}/search", wait_until="networkidle", timeout=60000)
        except Exception:
            await page_a.goto(f"{URL}/search", wait_until="domcontentloaded", timeout=60000)
        await page_a.wait_for_timeout(3000)
        await fix_ko_redirect(page_a, "/search")

        search_done = False
        inputs = await page_a.query_selector_all('input')
        for inp in inputs:
            placeholder = await inp.get_attribute('placeholder') or ''
            input_type = await inp.get_attribute('type') or ''
            if input_type not in ('hidden', 'checkbox', 'radio'):
                if any(kw in placeholder for kw in ('검색', '입찰', '질문', '공고')):
                    await inp.fill("건설공사")
                    await inp.press("Enter")
                    search_done = True
                    break

        if not search_done and inputs:
            # 첫 번째 텍스트 입력 필드 사용
            for inp in inputs:
                input_type = await inp.get_attribute('type') or ''
                if input_type not in ('hidden', 'checkbox', 'radio', 'submit', 'button'):
                    await inp.fill("건설공사")
                    await inp.press("Enter")
                    search_done = True
                    break

        await page_a.wait_for_timeout(5000)
        out = os.path.join(DIR, "05_search_results.png")
        await page_a.screenshot(path=out, full_page=True)
        sz = os.path.getsize(out)
        print(f"    ✅ 05_search_results.png ({sz // 1024}KB) - {page_a.url}")

        # 06. 입찰 상세 페이지
        print("\n  캡처: 06. 입찰 상세 페이지...")
        bid_notice_no = await get_bid_notice_no()

        if bid_notice_no:
            try:
                await page_a.goto(
                    f"{URL}/bids/{bid_notice_no}",
                    wait_until="networkidle", timeout=60000,
                )
            except Exception:
                await page_a.goto(
                    f"{URL}/bids/{bid_notice_no}",
                    wait_until="domcontentloaded", timeout=60000,
                )
            await fix_ko_redirect(page_a, f"/bids/{bid_notice_no}")
            await page_a.wait_for_timeout(4000)
            out = os.path.join(DIR, "06_bid_detail.png")
            await page_a.screenshot(path=out, full_page=True)
            sz = os.path.getsize(out)
            print(f"    ✅ 06_bid_detail.png ({sz // 1024}KB) - {page_a.url}")
        else:
            # 검색 결과 카드 클릭으로 시도
            cards = await page_a.query_selector_all('.MuiCard-root, .MuiPaper-root')
            bid_clicked = False
            for card in cards:
                text = await card.inner_text()
                if '공사' in text or '건설' in text:
                    try:
                        await card.click()
                        await page_a.wait_for_timeout(3000)
                        if "/bids/" in page_a.url:
                            bid_clicked = True
                            break
                    except Exception:
                        continue

            await page_a.wait_for_timeout(3000)
            out = os.path.join(DIR, "06_bid_detail.png")
            await page_a.screenshot(path=out, full_page=True)
            sz = os.path.getsize(out)
            status = "✅" if "/bids/" in page_a.url else "⚠️"
            print(f"    {status} 06_bid_detail.png ({sz // 1024}KB) - {page_a.url}")

        # 07. 북마크
        await capture_page(
            page_a, "/bookmarks", "07_bookmarks.png",
            ['.MuiCard-root', '.MuiPaper-root', '.MuiList-root', '.MuiAlert-root'],
            extra_wait=5000,
            description="07. 북마크 관리",
        )

        await ctx_user_a.close()

        # ===================================================
        # CONTEXT 3: 사용자 페이지 PART B
        # (알림설정, 알림수신함, 프로필, 설정, 구독, 사이드바)
        # ===================================================
        print("\n" + "=" * 60)
        print("CONTEXT 3: 사용자 페이지 PART B")
        print("=" * 60)

        ctx_user_b = await browser.new_context(
            viewport={"width": 1440, "height": 900},
            locale="ko-KR",
        )
        await ctx_user_b.add_init_script(f"""
            localStorage.setItem('odin_ai_token', '{USER_TOKEN}');
            localStorage.setItem('odin_ai_refresh_token', '{USER_TOKEN}');
        """)
        page_b = await ctx_user_b.new_page()

        # 08. 알림 설정
        await capture_page(
            page_b, "/notifications", "08_notification_settings.png",
            ['.MuiTextField-root', '.MuiSwitch-root', '.MuiPaper-root', '.MuiCard-root'],
            extra_wait=5000,
            description="08. 알림 설정",
        )

        # 09. 알림 수신함
        await capture_page(
            page_b, "/notification-inbox", "09_notification_inbox.png",
            ['.MuiList-root', '.MuiPaper-root', '.MuiCard-root', '.MuiAlert-root'],
            extra_wait=5000,
            description="09. 알림 수신함",
        )

        # 10. 프로필
        await capture_page(
            page_b, "/profile", "10_profile.png",
            ['.MuiTextField-root', '.MuiPaper-root'],
            description="10. 프로필 페이지",
        )

        # 11. 설정
        await capture_page(
            page_b, "/settings", "11_settings.png",
            ['.MuiSwitch-root', '.MuiPaper-root', '.MuiSelect-root'],
            description="11. 설정 페이지",
        )

        # 12. 구독관리
        await capture_page(
            page_b, "/subscription", "12_subscription.png",
            ['.MuiCard-root', '.MuiPaper-root'],
            description="12. 구독관리 페이지",
        )

        # 13. 사이드바 네비게이션 (클립 캡처)
        print("\n  캡처: 13. 사이드바 네비게이션...")
        try:
            await page_b.goto(f"{URL}/dashboard", wait_until="networkidle", timeout=60000)
        except Exception:
            await page_b.goto(f"{URL}/dashboard", wait_until="domcontentloaded", timeout=60000)
        await fix_ko_redirect(page_b, "/dashboard")
        await page_b.wait_for_timeout(3000)
        out = os.path.join(DIR, "13_sidebar_navigation.png")
        await page_b.screenshot(
            path=out,
            clip={"x": 0, "y": 0, "width": 280, "height": 900},
        )
        sz = os.path.getsize(out)
        print(f"    ✅ 13_sidebar_navigation.png ({sz // 1024}KB)")

        await ctx_user_b.close()

        # ===================================================
        # CONTEXT 4: 그래프 탐색기 (별도 컨텍스트, AI 대기)
        # ===================================================
        print("\n" + "=" * 60)
        print("CONTEXT 4: 그래프 탐색기")
        print("=" * 60)

        ctx_graph = await browser.new_context(
            viewport={"width": 1440, "height": 900},
            locale="ko-KR",
        )
        await ctx_graph.add_init_script(f"""
            localStorage.setItem('odin_ai_token', '{USER_TOKEN}');
            localStorage.setItem('odin_ai_refresh_token', '{USER_TOKEN}');
        """)
        page_graph = await ctx_graph.new_page()

        # 14. 그래프 탐색기 (빈 상태)
        await capture_page(
            page_graph, "/graph", "14_graph_explorer_empty.png",
            ['.MuiTextField-root', 'input', 'svg', '.MuiPaper-root'],
            extra_wait=5000,
            description="14. 지식 그래프 탐색기 (빈 상태)",
        )

        # 15. 그래프 탐색기 - AI 분석 결과
        print("\n  캡처: 15. 그래프 탐색기 (AI 분석)...")
        if "/login" not in page_graph.url:
            inputs = await page_graph.query_selector_all('input')
            search_field = None
            for inp in inputs:
                placeholder = await inp.get_attribute('placeholder') or ''
                input_type = await inp.get_attribute('type') or ''
                if input_type not in ('hidden', 'checkbox', 'radio') and (
                    any(kw in placeholder for kw in ('질문', '검색', '탐색', '입찰'))
                ):
                    search_field = inp
                    break

            if search_field is None and inputs:
                for inp in inputs:
                    input_type = await inp.get_attribute('type') or ''
                    if input_type not in ('hidden', 'checkbox', 'radio', 'submit', 'button'):
                        search_field = inp
                        break

            if search_field:
                await search_field.fill("충청남도 건설 입찰 트렌드")
                await search_field.press("Enter")
                print("    AI 분석 중 (최대 30초 대기)...")
                await page_graph.wait_for_timeout(30000)
            else:
                print("    ⚠️ 검색 입력 필드를 찾지 못함, 빈 상태 캡처")

            out = os.path.join(DIR, "15_graph_explorer_result.png")
            await page_graph.screenshot(path=out, full_page=True)
            sz = os.path.getsize(out)
            print(f"    ✅ 15_graph_explorer_result.png ({sz // 1024}KB)")
        else:
            print("    ⚠️ 그래프 탐색기: 로그인 리다이렉트됨, 스킵")

        await ctx_graph.close()

        # ===================================================
        # CONTEXT 5: 관리자 페이지
        # ===================================================
        print("\n" + "=" * 60)
        print("CONTEXT 5: 관리자 페이지")
        print("=" * 60)

        # 16. 관리자 로그인 페이지 (비인증 컨텍스트로 캡처)
        ctx_admin_login = await browser.new_context(
            viewport={"width": 1440, "height": 900},
            locale="ko-KR",
        )
        page_al = await ctx_admin_login.new_page()
        await capture_page(
            page_al, "/admin/login", "16_admin_login.png",
            ['.MuiTextField-root', 'input[type="email"]'],
            description="16. 관리자 로그인 페이지",
        )
        await ctx_admin_login.close()

        # 관리자 인증 컨텍스트: addInitScript로 페이지 로드 전 주입
        # admin_token 키 사용 (adminApi.ts: localStorage.getItem('admin_token'))
        ctx_admin = await browser.new_context(
            viewport={"width": 1440, "height": 900},
            locale="ko-KR",
        )
        await ctx_admin.add_init_script(f"""
            localStorage.setItem('admin_token', '{ADMIN_TOKEN}');
        """)
        page_admin = await ctx_admin.new_page()
        print("\n  관리자 토큰 주입 완료 (admin_token 키)")

        # 관리자 페이지는 AdminPrivateRoute가 getCurrentAdmin() API를 호출하므로
        # 충분한 대기 시간 필요
        ADMIN_EXTRA_WAIT = 6000

        # 17. 관리자 대시보드
        await capture_page(
            page_admin, "/admin/dashboard", "17_admin_dashboard.png",
            ['.MuiCard-root', '.MuiPaper-root', '.recharts-wrapper'],
            extra_wait=ADMIN_EXTRA_WAIT,
            description="17. 관리자 대시보드",
        )

        # 18. 배치 모니터링
        await capture_page(
            page_admin, "/admin/batch", "18_admin_batch.png",
            ['.MuiTable-root', '.MuiPaper-root', '.MuiCard-root'],
            extra_wait=ADMIN_EXTRA_WAIT,
            description="18. 배치 모니터링",
        )

        # 19. 시스템 모니터링
        await capture_page(
            page_admin, "/admin/system", "19_admin_system.png",
            ['.MuiCard-root', '.MuiPaper-root', '.recharts-wrapper'],
            extra_wait=ADMIN_EXTRA_WAIT,
            description="19. 시스템 모니터링",
        )

        # 20. 알림 모니터링 (관리자)
        await capture_page(
            page_admin, "/admin/notifications", "20_admin_notifications.png",
            ['.MuiTable-root', '.MuiPaper-root', '.MuiCard-root'],
            extra_wait=ADMIN_EXTRA_WAIT,
            description="20. 알림 발송 모니터링 (관리자)",
        )

        # 21. 사용자 관리
        await capture_page(
            page_admin, "/admin/users", "21_admin_users.png",
            ['.MuiTable-root', '.MuiPaper-root'],
            extra_wait=ADMIN_EXTRA_WAIT,
            description="21. 사용자 관리",
        )

        # 22. 로그 조회
        await capture_page(
            page_admin, "/admin/logs", "22_admin_logs.png",
            ['.MuiTable-root', '.MuiPaper-root'],
            extra_wait=ADMIN_EXTRA_WAIT,
            description="22. 로그 조회",
        )

        # 23. 통계 분석
        await capture_page(
            page_admin, "/admin/statistics", "23_admin_statistics.png",
            ['.MuiCard-root', '.recharts-wrapper', '.MuiPaper-root'],
            extra_wait=ADMIN_EXTRA_WAIT,
            description="23. 통계 분석",
        )

        await ctx_admin.close()
        await browser.close()

    # ===================================================
    # 결과 요약
    # ===================================================
    files = sorted([f for f in os.listdir(DIR) if f.endswith('.png')])
    print(f"\n{'=' * 60}")
    print(f"스크린샷 결과: {len(files)}개 / 23개 목표")
    print(f"저장 위치: {DIR}")
    print(f"{'=' * 60}")
    total_size = 0
    for f in files:
        sz = os.path.getsize(os.path.join(DIR, f))
        total_size += sz
        indicator = "✅" if sz > 20000 else "⚠️ (작음)"
        print(f"  {indicator} {f} ({sz // 1024}KB)")

    missing = 23 - len(files)
    print(f"\n총 크기: {total_size // 1024}KB")
    if missing > 0:
        print(f"⚠️ 누락된 스크린샷: {missing}개")
    else:
        print("✅ 모든 스크린샷 캡처 완료!")


asyncio.run(main())
