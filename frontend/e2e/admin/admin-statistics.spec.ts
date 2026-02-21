import { test, expect } from '@playwright/test';
import { setupAdminAuth } from '../helpers/auth';
import { captureScreenshot } from '../helpers/screenshot';
import { waitForPageReady, waitForCharts } from '../helpers/common';

test.describe('Admin Statistics', () => {
  test.beforeEach(async ({ page }) => {
    await setupAdminAuth(page);
    await page.goto('/admin/statistics');
    await waitForPageReady(page);
  });

  test('should display statistics page with charts', async ({ page }) => {
    await page.waitForTimeout(3000);
    await waitForCharts(page);
    await captureScreenshot(page, 'admin', '10-admin-statistics');
  });
});
