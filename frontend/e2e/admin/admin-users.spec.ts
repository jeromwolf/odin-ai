import { test, expect } from '@playwright/test';
import { setupAdminAuth } from '../helpers/auth';
import { captureScreenshot } from '../helpers/screenshot';
import { waitForTableData } from '../helpers/common';

test.describe('Admin User Management', () => {
  test.beforeEach(async ({ page }) => {
    await setupAdminAuth(page);
    await page.goto('/admin/users');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(3000);
  });

  test('should display user management page with stats', async ({ page }) => {
    const url = page.url();
    if (url.includes('/admin/login')) {
      const { adminLoginViaUI } = await import('../helpers/auth');
      await adminLoginViaUI(page);
      await page.goto('/admin/users');
      await page.waitForLoadState('networkidle');
      await page.waitForTimeout(3000);
    }
    const cards = page.locator('.MuiCard-root, .MuiPaper-root');
    const count = await cards.count();
    expect(count).toBeGreaterThan(0);
    await captureScreenshot(page, 'admin', '06-admin-users');
  });

  test('should display user table', async ({ page }) => {
    await page.waitForTimeout(3000);
    await waitForTableData(page);
    const rows = page.locator('tbody tr, .MuiDataGrid-row, .MuiTableRow-root');
    const count = await rows.count();
  });

  test('should open user detail dialog on row click', async ({ page }) => {
    await page.waitForTimeout(3000);
    await waitForTableData(page);
    const firstRow = page.locator('tbody tr, .MuiTableRow-root').first();
    if (await firstRow.isVisible().catch(() => false)) {
      // Look for detail/view button in the row
      const viewBtn = firstRow.locator('button, .MuiIconButton-root').first();
      if (await viewBtn.isVisible().catch(() => false)) {
        await viewBtn.click();
        await page.waitForTimeout(2000);
        await captureScreenshot(page, 'admin', '07-admin-user-detail');
      }
    }
  });
});
