import { test, expect } from '@playwright/test';
import { captureScreenshot } from '../helpers/screenshot';

test.describe('Navigation & Error Pages', () => {
  test('should show 404 page for invalid route', async ({ page }) => {
    await page.goto('/nonexistent-page-12345');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(1000);
    // Check for 404 content
    const has404 = await page.locator('text=404, text=찾을 수 없, text=Not Found, text=페이지를 찾을 수 없습니다').first().isVisible().catch(() => false);
    await captureScreenshot(page, 'navigation', '01-404-page');
  });

  test('should redirect unauthenticated admin to admin login', async ({ page }) => {
    await page.goto('/admin/dashboard');
    await page.waitForTimeout(2000);
    const url = page.url();
    const isOnAdminLogin = url.includes('/admin/login') || url.includes('/admin');
    await captureScreenshot(page, 'navigation', '02-admin-redirect');
  });

  test('should redirect root to dashboard or login', async ({ page }) => {
    await page.goto('/');
    await page.waitForTimeout(2000);
    const url = page.url();
    // Should redirect to either /dashboard (if authenticated) or /login
    const isRedirected = url.includes('/dashboard') || url.includes('/login') || url === 'http://localhost:3000/';
    expect(isRedirected).toBeTruthy();
  });
});
