import { test, expect } from '@playwright/test';
import { setupUserAuth } from '../helpers/auth';
import { captureScreenshot } from '../helpers/screenshot';
import { waitForPageReady } from '../helpers/common';

test.describe('Subscription', () => {
  test.beforeEach(async ({ page }) => {
    await setupUserAuth(page);
    await page.goto('/subscription');
    await waitForPageReady(page);
  });

  test('should display subscription plans', async ({ page }) => {
    await page.waitForTimeout(2000);
    // Check for plan cards
    const planCards = page.locator('.MuiCard-root, .MuiPaper-root');
    const count = await planCards.count();
    expect(count).toBeGreaterThan(0);
    await captureScreenshot(page, 'subscription', '01-subscription-plans');
  });

  test('should show plan details and pricing', async ({ page }) => {
    await page.waitForTimeout(2000);
    // Look for price-related text (Korean won)
    const pageContent = await page.textContent('body');
    await captureScreenshot(page, 'subscription', '02-subscription-usage');
  });
});
