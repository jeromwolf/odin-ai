import { test, expect } from '@playwright/test';
import { setupAdminAuth } from '../helpers/auth';
import { captureScreenshot } from '../helpers/screenshot';
import { waitForPageReady } from '../helpers/common';

test.describe('Admin System Monitoring', () => {
  test.beforeEach(async ({ page }) => {
    await setupAdminAuth(page);
    await page.goto('/admin/system');
    await waitForPageReady(page);
  });

  test('should display system monitoring page', async ({ page }) => {
    await page.waitForTimeout(3000);
    // Look for system metrics
    const pageContent = await page.textContent('body');
    expect(pageContent?.length).toBeGreaterThan(0);
    await captureScreenshot(page, 'admin', '05-admin-system');
  });
});
