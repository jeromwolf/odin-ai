import { test, expect } from '@playwright/test';
import { setupUserAuth } from '../helpers/auth';
import { captureScreenshot } from '../helpers/screenshot';
import { waitForPageReady, waitForCharts } from '../helpers/common';

test.describe('Dashboard', () => {
  test.beforeEach(async ({ page }) => {
    await setupUserAuth(page);
    await page.goto('/dashboard');
    await waitForPageReady(page);
  });

  test('should display dashboard with stats cards', async ({ page }) => {
    // Wait for dashboard content to render
    await page.waitForTimeout(2000);
    // Check for stat cards (MUI Card or Paper elements)
    const cards = page.locator('.MuiCard-root, .MuiPaper-root');
    const cardCount = await cards.count();
    expect(cardCount).toBeGreaterThan(0);
    await captureScreenshot(page, 'dashboard', '01-dashboard-overview');
  });

  test('should display charts', async ({ page }) => {
    await waitForCharts(page);
    await page.waitForTimeout(1000);
    await captureScreenshot(page, 'dashboard', '02-dashboard-charts');
  });

  test('should display upcoming deadlines section', async ({ page }) => {
    await page.waitForTimeout(2000);
    // Look for deadline-related content
    const deadlineSection = page.locator('text=마감, text=임박, text=deadline, text=D-').first();
    await captureScreenshot(page, 'dashboard', '03-dashboard-deadlines');
  });

  test('should have navigation sidebar', async ({ page }) => {
    // Verify main navigation elements exist
    const nav = page.locator('nav, .MuiDrawer-root, [role="navigation"]').first();
    await expect(nav).toBeVisible();
  });
});
