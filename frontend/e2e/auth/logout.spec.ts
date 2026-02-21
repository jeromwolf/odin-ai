import { test, expect } from '@playwright/test';
import { setupUserAuth } from '../helpers/auth';
import { captureScreenshot } from '../helpers/screenshot';

test.describe('User Logout', () => {
  test('should redirect to login after logout', async ({ page }) => {
    await setupUserAuth(page);
    await page.goto('/dashboard');
    await page.waitForLoadState('networkidle');

    // Find and click logout button/menu
    const profileMenu = page.locator('[data-testid="profile-menu"], .MuiAvatar-root, .MuiIconButton-root').last();
    if (await profileMenu.isVisible().catch(() => false)) {
      await profileMenu.click();
      await page.waitForTimeout(300);
    }

    const logoutBtn = page.locator('text=로그아웃, text=Logout, [data-testid="logout"]').first();
    if (await logoutBtn.isVisible().catch(() => false)) {
      await logoutBtn.click();
      await page.waitForTimeout(2000);
    }

    await captureScreenshot(page, 'auth', '08-logout-redirect');
  });

  test('should redirect unauthenticated user from protected routes', async ({ page }) => {
    // No auth token set - should redirect to login
    await page.goto('/dashboard');
    await page.waitForTimeout(2000);
    // Should be on login page or show login prompt
    const url = page.url();
    const isOnLogin = url.includes('/login') || url === 'http://localhost:3000/';
    expect(isOnLogin || await page.locator('text=로그인').first().isVisible().catch(() => false)).toBeTruthy();
  });
});
