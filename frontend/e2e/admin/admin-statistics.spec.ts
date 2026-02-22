import { test, expect } from '@playwright/test';
import { setupAdminAuth } from '../helpers/auth';
import { captureScreenshot } from '../helpers/screenshot';
import { waitForCharts } from '../helpers/common';

test.describe('Admin Statistics', () => {
  test.beforeEach(async ({ page }) => {
    await setupAdminAuth(page);
    await page.goto('/admin/statistics');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(3000);
  });

  test('should display statistics page with charts', async ({ page }) => {
    const url = page.url();
    if (url.includes('/admin/login')) {
      const { adminLoginViaUI } = await import('../helpers/auth');
      await adminLoginViaUI(page);
      await page.goto('/admin/statistics');
      await page.waitForLoadState('networkidle');
      await page.waitForTimeout(3000);
    }
    await waitForCharts(page);
    await captureScreenshot(page, 'admin', '10-admin-statistics');
  });
});
