import { Page } from '@playwright/test';
import fs from 'fs';
import path from 'path';

const SCREENSHOT_BASE = path.resolve(__dirname, '../../../docs/screenshots');

export async function captureScreenshot(page: Page, category: string, name: string) {
  const dir = path.join(SCREENSHOT_BASE, category);
  fs.mkdirSync(dir, { recursive: true });
  await page.screenshot({
    path: path.join(dir, `${name}.png`),
    fullPage: false,
  });
}

export async function captureFullPage(page: Page, category: string, name: string) {
  const dir = path.join(SCREENSHOT_BASE, category);
  fs.mkdirSync(dir, { recursive: true });
  await page.screenshot({
    path: path.join(dir, `${name}.png`),
    fullPage: true,
  });
}
