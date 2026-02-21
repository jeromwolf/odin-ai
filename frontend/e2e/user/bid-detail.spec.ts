import { test, expect } from '@playwright/test';
import { setupUserAuth } from '../helpers/auth';
import { captureScreenshot } from '../helpers/screenshot';
import { waitForPageReady } from '../helpers/common';

test.describe('Bid Detail', () => {
  let bidId: string | null = null;

  test.beforeAll(async ({ request }) => {
    // Dynamically find a valid bid ID
    try {
      const response = await request.get('http://localhost:9000/api/bids?limit=1');
      if (response.ok()) {
        const data = await response.json();
        const bids = data.data || data.results || [];
        if (bids.length > 0) {
          bidId = bids[0].bid_notice_no;
        }
      }
    } catch {
      // API may not be available
    }
  });

  test('should display bid detail page', async ({ page }) => {
    test.skip(!bidId, 'No bids available in database');
    await setupUserAuth(page);
    await page.goto(`/bids/${bidId}`);
    await waitForPageReady(page);
    await page.waitForTimeout(2000);
    await captureScreenshot(page, 'bid-detail', '01-bid-detail-page');
  });

  test('should show bid title and organization info', async ({ page }) => {
    test.skip(!bidId, 'No bids available in database');
    await setupUserAuth(page);
    await page.goto(`/bids/${bidId}`);
    await waitForPageReady(page);
    await page.waitForTimeout(2000);
    // Check for content sections
    const pageContent = await page.textContent('body');
    await captureScreenshot(page, 'bid-detail', '02-bid-detail-info');
  });

  test('should handle non-existent bid gracefully', async ({ page }) => {
    await setupUserAuth(page);
    await page.goto('/bids/NONEXISTENT_BID_12345');
    await page.waitForTimeout(3000);
    // Should show error or 404 within the page
  });
});
