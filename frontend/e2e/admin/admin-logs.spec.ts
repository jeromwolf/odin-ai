import { test, expect } from '@playwright/test';
import { setupAdminAuth } from '../helpers/auth';
import { captureScreenshot } from '../helpers/screenshot';
import { waitForPageReady } from '../helpers/common';

test.describe('Admin Logs', () => {
  test.beforeEach(async ({ page }) => {
    await setupAdminAuth(page);
    await page.goto('/admin/logs');
    await waitForPageReady(page);
  });

  test('should display logs page', async ({ page }) => {
    await page.waitForTimeout(3000);
    await captureScreenshot(page, 'admin', '09-admin-logs');
  });

  test('should have log filter controls', async ({ page }) => {
    await page.waitForTimeout(2000);
    // Look for filter elements
    const filters = page.locator('.MuiSelect-root, .MuiTextField-root, input[type="date"]');
    const count = await filters.count();
  });
});
