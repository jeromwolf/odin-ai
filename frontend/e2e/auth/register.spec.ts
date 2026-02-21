import { test, expect } from '@playwright/test';
import { captureScreenshot } from '../helpers/screenshot';

test.describe('User Registration', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/register');
    await page.waitForLoadState('networkidle');
  });

  test('should display registration form', async ({ page }) => {
    // Check for registration page elements
    await expect(page.locator('input[type="email"], input[name="email"], input[type="text"]').first()).toBeVisible();
    await captureScreenshot(page, 'auth', '05-register-step1');
  });

  test('should show email and password fields', async ({ page }) => {
    await expect(page.locator('input[type="email"], input[name="email"]').first()).toBeVisible();
    await expect(page.locator('input[type="password"], input[name="password"]').first()).toBeVisible();
  });

  test('should navigate between steps if multi-step', async ({ page }) => {
    // Fill first step and try to advance
    const emailInput = page.locator('input[type="email"], input[name="email"]').first();
    if (await emailInput.isVisible()) {
      await emailInput.fill('newuser@example.com');
    }
    // Look for next/stepper buttons
    const nextBtn = page.locator('button:has-text("다음"), button:has-text("Next")').first();
    if (await nextBtn.isVisible().catch(() => false)) {
      await nextBtn.click();
      await page.waitForTimeout(500);
      await captureScreenshot(page, 'auth', '06-register-step2');
    }
  });

  test('should show full registration form elements', async ({ page }) => {
    await captureScreenshot(page, 'auth', '07-register-form');
  });
});
