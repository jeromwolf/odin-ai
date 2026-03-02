/**
 * ODIN-AI 최신 화면 스크린샷 캡처 스크립트
 * 사업계획서 문서용 전체 화면 캡처
 *
 * 실행: npx playwright test e2e/capture-screenshots.ts --project=chromium
 */
import { test, expect } from '@playwright/test';
import path from 'path';
import fs from 'fs';

const SCREENSHOT_DIR = path.resolve(__dirname, '../../docs/screenshots/phase1_3');
const BASE_URL = 'http://localhost:3000';
const API_BASE = 'http://localhost:9000';

// Ensure screenshot directory exists
fs.mkdirSync(SCREENSHOT_DIR, { recursive: true });

async function saveScreenshot(page: any, filename: string) {
  await page.screenshot({
    path: path.join(SCREENSHOT_DIR, filename),
    fullPage: false,
  });
  console.log(`  Saved: ${filename}`);
}

async function saveFullScreenshot(page: any, filename: string) {
  await page.screenshot({
    path: path.join(SCREENSHOT_DIR, filename),
    fullPage: true,
  });
  console.log(`  Saved: ${filename}`);
}

// Get tokens
async function getTokens(request: any) {
  // User login
  const userRes = await request.post(`${API_BASE}/api/auth/login`, {
    data: { email: 'admin@odin.ai', password: 'admin123' },
  });
  const userData = await userRes.json();
  const userToken = userData.access_token || userData.token;

  // Admin login
  const adminRes = await request.post(`${API_BASE}/api/admin/auth/login`, {
    data: { email: 'admin@odin.ai', password: 'admin123' },
  });
  const adminData = await adminRes.json();
  const adminToken = adminData.access_token || adminData.token;

  return { userToken, adminToken };
}

test.describe('ODIN-AI Screenshot Capture', () => {
  test.describe.configure({ mode: 'serial' });

  // ===========================
  // 1. Authentication Pages
  // ===========================
  test('01 - Login Page', async ({ page }) => {
    await page.goto('/login');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(1000);
    await saveScreenshot(page, '01_login_page.png');
  });

  test('02 - Register Page', async ({ page }) => {
    await page.goto('/register');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(1000);
    await saveScreenshot(page, '02_register_page.png');
  });

  // ===========================
  // 2. User Pages (Authenticated)
  // ===========================
  test('03 - Dashboard', async ({ page, request }) => {
    const { userToken } = await getTokens(request);
    await page.addInitScript((token: string) => {
      localStorage.setItem('odin_ai_token', token);
    }, userToken);
    await page.goto('/dashboard');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(2000);
    await saveScreenshot(page, '03_dashboard.png');
  });

  test('04 - Search Empty', async ({ page, request }) => {
    const { userToken } = await getTokens(request);
    await page.addInitScript((token: string) => {
      localStorage.setItem('odin_ai_token', token);
    }, userToken);
    await page.goto('/search');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(1000);
    await saveScreenshot(page, '04_search_empty.png');
  });

  test('05 - Search Results', async ({ page, request }) => {
    const { userToken } = await getTokens(request);
    await page.addInitScript((token: string) => {
      localStorage.setItem('odin_ai_token', token);
    }, userToken);
    await page.goto('/search?q=%EA%B3%B5%EC%82%AC');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(3000);
    await saveScreenshot(page, '05_search_results.png');
  });

  test('06 - Bid Detail', async ({ page, request }) => {
    const { userToken } = await getTokens(request);
    await page.addInitScript((token: string) => {
      localStorage.setItem('odin_ai_token', token);
    }, userToken);
    // Search first to find a bid
    await page.goto('/search?q=%EA%B3%B5%EC%82%AC');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(2000);
    // Click first result
    const firstResult = page.locator('.MuiCard-root, .MuiPaper-root, [class*="result"]').first();
    if (await firstResult.isVisible()) {
      await firstResult.click();
      await page.waitForTimeout(2000);
    }
    await saveScreenshot(page, '06_bid_detail.png');
  });

  test('07 - Bookmarks', async ({ page, request }) => {
    const { userToken } = await getTokens(request);
    await page.addInitScript((token: string) => {
      localStorage.setItem('odin_ai_token', token);
    }, userToken);
    await page.goto('/bookmarks');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(1500);
    await saveScreenshot(page, '07_bookmarks.png');
  });

  test('08 - Notification Settings', async ({ page, request }) => {
    const { userToken } = await getTokens(request);
    await page.addInitScript((token: string) => {
      localStorage.setItem('odin_ai_token', token);
    }, userToken);
    await page.goto('/notifications');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(1500);
    await saveScreenshot(page, '08_notification_settings.png');
  });

  test('09 - Notification Inbox', async ({ page, request }) => {
    const { userToken } = await getTokens(request);
    await page.addInitScript((token: string) => {
      localStorage.setItem('odin_ai_token', token);
    }, userToken);
    await page.goto('/notification-inbox');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(1500);
    await saveScreenshot(page, '09_notification_inbox.png');
  });

  test('10 - Profile', async ({ page, request }) => {
    const { userToken } = await getTokens(request);
    await page.addInitScript((token: string) => {
      localStorage.setItem('odin_ai_token', token);
    }, userToken);
    await page.goto('/profile');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(1500);
    await saveScreenshot(page, '10_profile.png');
  });

  test('11 - Settings', async ({ page, request }) => {
    const { userToken } = await getTokens(request);
    await page.addInitScript((token: string) => {
      localStorage.setItem('odin_ai_token', token);
    }, userToken);
    await page.goto('/settings');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(1500);
    await saveScreenshot(page, '11_settings.png');
  });

  test('12 - Subscription', async ({ page, request }) => {
    const { userToken } = await getTokens(request);
    await page.addInitScript((token: string) => {
      localStorage.setItem('odin_ai_token', token);
    }, userToken);
    await page.goto('/subscription');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(1500);
    await saveScreenshot(page, '12_subscription.png');
  });

  test('13 - Sidebar Navigation', async ({ page, request }) => {
    const { userToken } = await getTokens(request);
    await page.addInitScript((token: string) => {
      localStorage.setItem('odin_ai_token', token);
    }, userToken);
    await page.goto('/dashboard');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(1000);
    // Capture just the sidebar area (left 280px)
    await page.screenshot({
      path: path.join(SCREENSHOT_DIR, '13_sidebar_navigation.png'),
      clip: { x: 0, y: 0, width: 280, height: 800 },
    });
    console.log('  Saved: 13_sidebar_navigation.png');
  });

  // ===========================
  // 3. Graph Explorer
  // ===========================
  test('14 - Graph Explorer Empty', async ({ page, request }) => {
    const { userToken } = await getTokens(request);
    await page.addInitScript((token: string) => {
      localStorage.setItem('odin_ai_token', token);
    }, userToken);
    await page.goto('/graph-explorer');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(2000);
    await saveScreenshot(page, '14_graph_explorer_empty.png');
  });

  test('15 - Graph Explorer Result', async ({ page, request }) => {
    const { userToken } = await getTokens(request);
    await page.addInitScript((token: string) => {
      localStorage.setItem('odin_ai_token', token);
    }, userToken);
    await page.goto('/graph-explorer');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(1000);
    // Type a search query and submit
    const searchInput = page.locator('input[type="text"], input[placeholder*="검색"], input[placeholder*="search"]').first();
    if (await searchInput.isVisible()) {
      await searchInput.fill('도로공사');
      // Click search button
      const searchBtn = page.locator('button').filter({ hasText: /검색|search|분석/i }).first();
      if (await searchBtn.isVisible()) {
        await searchBtn.click();
        await page.waitForTimeout(5000); // Wait for graph to render
      }
    }
    await saveScreenshot(page, '15_graph_explorer_result.png');
  });

  // ===========================
  // 4. Admin Pages
  // ===========================
  test('16 - Admin Login', async ({ page }) => {
    await page.goto('/admin/login');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(1000);
    await saveScreenshot(page, '16_admin_login.png');
  });

  test('17 - Admin Dashboard', async ({ page, request }) => {
    const { adminToken } = await getTokens(request);
    await page.addInitScript((token: string) => {
      localStorage.setItem('admin_token', token);
    }, adminToken);
    await page.goto('/admin/dashboard');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(2000);
    await saveScreenshot(page, '17_admin_dashboard.png');
  });

  test('18 - Admin Batch', async ({ page, request }) => {
    const { adminToken } = await getTokens(request);
    await page.addInitScript((token: string) => {
      localStorage.setItem('admin_token', token);
    }, adminToken);
    await page.goto('/admin/batch');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(2000);
    await saveScreenshot(page, '18_admin_batch.png');
  });

  test('19 - Admin System', async ({ page, request }) => {
    const { adminToken } = await getTokens(request);
    await page.addInitScript((token: string) => {
      localStorage.setItem('admin_token', token);
    }, adminToken);
    await page.goto('/admin/system');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(2000);
    await saveScreenshot(page, '19_admin_system.png');
  });

  test('20 - Admin Notifications', async ({ page, request }) => {
    const { adminToken } = await getTokens(request);
    await page.addInitScript((token: string) => {
      localStorage.setItem('admin_token', token);
    }, adminToken);
    await page.goto('/admin/notifications');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(2000);
    await saveScreenshot(page, '20_admin_notifications.png');
  });

  test('21 - Admin Users', async ({ page, request }) => {
    const { adminToken } = await getTokens(request);
    await page.addInitScript((token: string) => {
      localStorage.setItem('admin_token', token);
    }, adminToken);
    await page.goto('/admin/users');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(2000);
    await saveScreenshot(page, '21_admin_users.png');
  });

  test('22 - Admin Logs', async ({ page, request }) => {
    const { adminToken } = await getTokens(request);
    await page.addInitScript((token: string) => {
      localStorage.setItem('admin_token', token);
    }, adminToken);
    await page.goto('/admin/logs');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(2000);
    await saveScreenshot(page, '22_admin_logs.png');
  });

  test('23 - Admin Statistics', async ({ page, request }) => {
    const { adminToken } = await getTokens(request);
    await page.addInitScript((token: string) => {
      localStorage.setItem('admin_token', token);
    }, adminToken);
    await page.goto('/admin/statistics');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(2000);
    await saveScreenshot(page, '23_admin_statistics.png');
  });
});
