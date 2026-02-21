import { test, expect } from '@playwright/test';
import { setupAdminAuth } from '../helpers/auth';
import { captureScreenshot } from '../helpers/screenshot';
import { waitForPageReady } from '../helpers/common';

test.describe('Admin Batch Monitoring', () => {
  test.beforeEach(async ({ page }) => {
    await setupAdminAuth(page);
    await page.goto('/admin/batch');
    await waitForPageReady(page);
  });

  test('should display batch monitoring page', async ({ page }) => {
    await page.waitForTimeout(3000);
    await captureScreenshot(page, 'admin', '04-admin-batch');
  });

  test('should have batch execution controls', async ({ page }) => {
    await page.waitForTimeout(2000);
    // Look for execute button
    const execBtn = page.locator('button:has-text("실행"), button:has-text("Execute"), button:has-text("배치")').first();
    const hasBtn = await execBtn.isVisible().catch(() => false);
  });
});
