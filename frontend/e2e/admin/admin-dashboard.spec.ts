import { test, expect } from '@playwright/test';
import { setupAdminAuth } from '../helpers/auth';
import { captureScreenshot } from '../helpers/screenshot';
import { waitForPageReady } from '../helpers/common';

test.describe('Admin Dashboard', () => {
  test.beforeEach(async ({ page }) => {
    await setupAdminAuth(page);
    await page.goto('/admin/dashboard');
    await waitForPageReady(page);
  });

  test('should display admin dashboard', async ({ page }) => {
    await page.waitForTimeout(3000);
    const cards = page.locator('.MuiCard-root, .MuiPaper-root');
    const count = await cards.count();
    expect(count).toBeGreaterThan(0);
    await captureScreenshot(page, 'admin', '03-admin-dashboard');
  });
});
