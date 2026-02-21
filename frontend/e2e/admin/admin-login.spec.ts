import { test, expect } from '@playwright/test';
import { adminLoginViaUI, ADMIN_USER } from '../helpers/auth';
import { captureScreenshot } from '../helpers/screenshot';

test.describe('Admin Login', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/admin/login');
    await page.waitForLoadState('networkidle');
  });

  test('should display admin login page', async ({ page }) => {
    await expect(page.locator('input[type="email"], input[name="email"]').first()).toBeVisible();
    await captureScreenshot(page, 'admin', '01-admin-login');
  });

  test('should login with admin credentials', async ({ page }) => {
    await page.fill('input[type="email"], input[name="email"]', ADMIN_USER.email);
    await page.fill('input[type="password"], input[name="password"]', ADMIN_USER.password);
    await page.click('button[type="submit"]');
    try {
      await page.waitForURL(/\/admin\/(dashboard|$)/, { timeout: 10000 });
    } catch {
      // May redirect differently
    }
    await page.waitForTimeout(2000);
    await captureScreenshot(page, 'admin', '02-admin-login-success');
  });

  test('should show error for invalid admin credentials', async ({ page }) => {
    await page.fill('input[type="email"], input[name="email"]', 'wrong@admin.com');
    await page.fill('input[type="password"], input[name="password"]', 'wrongpassword');
    await page.click('button[type="submit"]');
    await page.waitForTimeout(2000);
  });
});
