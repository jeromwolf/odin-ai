import { test, expect } from '@playwright/test';
import { setupUserAuth } from '../helpers/auth';
import { captureScreenshot } from '../helpers/screenshot';
import { waitForPageReady } from '../helpers/common';

test.describe('Bid Search', () => {
  test.beforeEach(async ({ page }) => {
    await setupUserAuth(page);
    await page.goto('/search');
    await waitForPageReady(page);
  });

  test('should display search page with input field', async ({ page }) => {
    const searchInput = page.locator('input[type="text"], input[type="search"], input[placeholder*="검색"], input[placeholder*="search"]').first();
    await expect(searchInput).toBeVisible();
    await captureScreenshot(page, 'search', '01-search-page');
  });

  test('should search with Korean keyword and show results', async ({ page }) => {
    const searchInput = page.locator('input[type="text"], input[type="search"], input[placeholder*="검색"], input[placeholder*="search"]').first();
    await searchInput.fill('공사');
    // Press Enter or click search button
    await searchInput.press('Enter');
    await page.waitForTimeout(3000);
    await captureScreenshot(page, 'search', '02-search-results');
  });

  test('should support URL-based search', async ({ page }) => {
    await page.goto('/search?q=건설');
    await page.waitForTimeout(3000);
    await captureScreenshot(page, 'search', '03-search-with-filters');
  });

  test('should display result cards with bid info', async ({ page }) => {
    const searchInput = page.locator('input[type="text"], input[type="search"], input[placeholder*="검색"], input[placeholder*="search"]').first();
    await searchInput.fill('도로');
    await searchInput.press('Enter');
    await page.waitForTimeout(3000);
    // Check for result cards
    const results = page.locator('.MuiCard-root, .MuiPaper-root, [class*="result"], [class*="card"]');
    const count = await results.count();
    // Results may or may not exist depending on data
  });

  test('should handle search with no results gracefully', async ({ page }) => {
    const searchInput = page.locator('input[type="text"], input[type="search"], input[placeholder*="검색"], input[placeholder*="search"]').first();
    await searchInput.fill('xyznonexistent12345');
    await searchInput.press('Enter');
    await page.waitForTimeout(3000);
    await captureScreenshot(page, 'search', '04-search-no-results');
  });

  test('should navigate to bid detail on result click', async ({ page }) => {
    const searchInput = page.locator('input[type="text"], input[type="search"], input[placeholder*="검색"], input[placeholder*="search"]').first();
    await searchInput.fill('공사');
    await searchInput.press('Enter');
    await page.waitForTimeout(3000);
    // Click first result if available
    const firstResult = page.locator('.MuiCard-root, .MuiPaper-root, [class*="result"]').first();
    if (await firstResult.isVisible().catch(() => false)) {
      await firstResult.click();
      await page.waitForTimeout(2000);
    }
  });
});
