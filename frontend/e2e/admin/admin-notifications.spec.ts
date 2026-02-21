import { test, expect } from '@playwright/test';
import { setupAdminAuth } from '../helpers/auth';
import { captureScreenshot } from '../helpers/screenshot';
import { waitForPageReady } from '../helpers/common';

test.describe('Admin Notification Monitoring', () => {
  test.beforeEach(async ({ page }) => {
    await setupAdminAuth(page);
    await page.goto('/admin/notifications');
    await waitForPageReady(page);
  });

  test('should display notification monitoring page', async ({ page }) => {
    await page.waitForTimeout(3000);
    await captureScreenshot(page, 'admin', '08-admin-notifications');
  });
});
