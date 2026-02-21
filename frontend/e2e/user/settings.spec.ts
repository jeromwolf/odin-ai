import { test, expect } from '@playwright/test';
import { setupUserAuth } from '../helpers/auth';
import { captureScreenshot } from '../helpers/screenshot';
import { waitForPageReady } from '../helpers/common';

test.describe('Settings', () => {
  test.beforeEach(async ({ page }) => {
    await setupUserAuth(page);
    await page.goto('/settings');
    await waitForPageReady(page);
  });

  test('should display settings page', async ({ page }) => {
    await page.waitForTimeout(2000);
    await captureScreenshot(page, 'settings', '01-settings-page');
  });

  test('should show setting toggles and options', async ({ page }) => {
    await page.waitForTimeout(2000);
    // Look for switches/toggles
    const toggles = page.locator('.MuiSwitch-root, .MuiToggleButton-root, input[type="checkbox"]');
    await captureScreenshot(page, 'settings', '02-settings-notifications');
  });
});
