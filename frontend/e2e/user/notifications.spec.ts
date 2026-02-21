import { test, expect } from '@playwright/test';
import { setupUserAuth } from '../helpers/auth';
import { captureScreenshot } from '../helpers/screenshot';
import { waitForPageReady } from '../helpers/common';

test.describe('Notifications', () => {
  test.beforeEach(async ({ page }) => {
    await setupUserAuth(page);
    await page.goto('/notifications');
    await waitForPageReady(page);
  });

  test('should display notifications page', async ({ page }) => {
    await page.waitForTimeout(2000);
    await captureScreenshot(page, 'notifications', '01-notifications-page');
  });

  test('should show notification settings section', async ({ page }) => {
    await page.waitForTimeout(2000);
    // Look for settings-related elements
    const settingsElements = page.locator('text=설정, text=알림, text=이메일, .MuiSwitch-root, .MuiToggleButton-root');
    await captureScreenshot(page, 'notifications', '02-notification-settings');
  });
});
