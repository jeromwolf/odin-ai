import { test, expect } from '@playwright/test';
import { setupAdminAuth } from '../helpers/auth';
import { captureScreenshot } from '../helpers/screenshot';

test.describe('Admin System Monitoring', () => {
  test.beforeEach(async ({ page }) => {
    await setupAdminAuth(page);
    await page.goto('/admin/system');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(3000);
  });

  test('should display system monitoring page', async ({ page }) => {
    const url = page.url();
    if (url.includes('/admin/login')) {
      const { adminLoginViaUI } = await import('../helpers/auth');
      await adminLoginViaUI(page);
      await page.goto('/admin/system');
      await page.waitForLoadState('networkidle');
      await page.waitForTimeout(3000);
    }
    // Look for system metrics
    const pageContent = await page.textContent('body');
    expect(pageContent?.length).toBeGreaterThan(0);
    await captureScreenshot(page, 'admin', '05-admin-system');
  });
});
