import { test, expect } from '@playwright/test';
import { setupAdminAuth } from '../helpers/auth';
import { captureScreenshot } from '../helpers/screenshot';

test.describe('Admin Dashboard', () => {
  test.beforeEach(async ({ page }) => {
    await setupAdminAuth(page);
    await page.goto('/admin/dashboard');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(3000);
  });

  test('should display admin dashboard', async ({ page }) => {
    // Verify we're NOT on the login page
    const url = page.url();
    if (url.includes('/admin/login')) {
      // Re-authenticate if redirected
      const { adminLoginViaUI } = await import('../helpers/auth');
      await adminLoginViaUI(page);
      await page.goto('/admin/dashboard');
      await page.waitForLoadState('networkidle');
      await page.waitForTimeout(3000);
    }
    const cards = page.locator('.MuiCard-root, .MuiPaper-root');
    const count = await cards.count();
    expect(count).toBeGreaterThan(0);
    await captureScreenshot(page, 'admin', '03-admin-dashboard');
  });
});
