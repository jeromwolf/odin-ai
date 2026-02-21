import { test, expect } from '@playwright/test';
import { setupUserAuth } from '../helpers/auth';
import { captureScreenshot } from '../helpers/screenshot';
import { waitForPageReady } from '../helpers/common';

test.describe('Profile', () => {
  test.beforeEach(async ({ page }) => {
    await setupUserAuth(page);
    await page.goto('/profile');
    await waitForPageReady(page);
  });

  test('should display profile page', async ({ page }) => {
    await page.waitForTimeout(2000);
    // Check for profile form elements
    const inputs = page.locator('input, .MuiTextField-root');
    const count = await inputs.count();
    expect(count).toBeGreaterThan(0);
    await captureScreenshot(page, 'profile', '01-profile-page');
  });

  test('should show activity statistics', async ({ page }) => {
    await page.waitForTimeout(2000);
    await captureScreenshot(page, 'profile', '02-profile-stats');
  });
});
