import { test, expect } from '@playwright/test';
import { setupAdminAuth } from '../helpers/auth';
import { captureScreenshot } from '../helpers/screenshot';

test.describe('Admin Notification Monitoring', () => {
  test.beforeEach(async ({ page }) => {
    await setupAdminAuth(page);
    await page.goto('/admin/notifications');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(3000);
  });

  test('should display notification monitoring page', async ({ page }) => {
    const url = page.url();
    if (url.includes('/admin/login')) {
      const { adminLoginViaUI } = await import('../helpers/auth');
      await adminLoginViaUI(page);
      await page.goto('/admin/notifications');
      await page.waitForLoadState('networkidle');
      await page.waitForTimeout(3000);
    }
    await captureScreenshot(page, 'admin', '08-admin-notifications');
  });
});
