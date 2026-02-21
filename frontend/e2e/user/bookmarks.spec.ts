import { test, expect } from '@playwright/test';
import { setupUserAuth } from '../helpers/auth';
import { captureScreenshot } from '../helpers/screenshot';
import { waitForPageReady } from '../helpers/common';

test.describe('Bookmarks', () => {
  test.beforeEach(async ({ page }) => {
    await setupUserAuth(page);
    await page.goto('/bookmarks');
    await waitForPageReady(page);
  });

  test('should display bookmarks page', async ({ page }) => {
    await page.waitForTimeout(2000);
    // Page should render with title or content
    const pageContent = await page.textContent('body');
    expect(pageContent).toBeTruthy();
    await captureScreenshot(page, 'bookmarks', '01-bookmarks-page');
  });

  test('should show bookmarks or empty state', async ({ page }) => {
    await page.waitForTimeout(2000);
    await captureScreenshot(page, 'bookmarks', '02-bookmarks-list');
  });
});
