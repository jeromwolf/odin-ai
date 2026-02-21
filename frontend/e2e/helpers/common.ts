import { Page } from '@playwright/test';

/** Wait for MUI CircularProgress spinners to disappear */
export async function waitForPageReady(page: Page, timeout = 15000) {
  try {
    await page.waitForLoadState('domcontentloaded');
    await page.waitForFunction(
      () => document.querySelectorAll('[role="progressbar"]').length === 0,
      { timeout }
    );
  } catch {
    // Some pages may not have progressbar at all
  }
  // Extra small wait for React renders
  await page.waitForTimeout(500);
}

/** Wait for recharts SVG to render */
export async function waitForCharts(page: Page, timeout = 10000) {
  try {
    await page.waitForSelector('.recharts-surface, .recharts-wrapper, canvas', { timeout });
  } catch {
    // Charts may not exist on every page
  }
}

/** Wait for a MUI table to have at least one row */
export async function waitForTableData(page: Page, timeout = 10000) {
  try {
    await page.waitForSelector('tbody tr, .MuiDataGrid-row', { timeout });
  } catch {
    // Table may be empty
  }
}

/** Get the count of visible elements */
export async function countElements(page: Page, selector: string): Promise<number> {
  return page.locator(selector).count();
}
