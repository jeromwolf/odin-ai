import { request } from '@playwright/test';
import { ensureTestUser, ensureAdminToken } from './helpers/auth';
import fs from 'fs';
import path from 'path';

const API_BASE = 'http://localhost:9000';
const SCREENSHOT_DIRS = [
  'auth', 'dashboard', 'search', 'bid-detail', 'bookmarks',
  'notifications', 'subscription', 'profile', 'settings', 'admin', 'navigation'
];

async function globalSetup() {
  console.log('\n=== ODIN-AI E2E Test Global Setup ===\n');

  // 1. Create screenshot directories
  const screenshotBase = path.resolve(__dirname, '../../docs/screenshots');
  for (const dir of SCREENSHOT_DIRS) {
    fs.mkdirSync(path.join(screenshotBase, dir), { recursive: true });
  }
  console.log('[Setup] Screenshot directories created');

  // 2. Check backend health
  const ctx = await request.newContext();
  try {
    const health = await ctx.get(`${API_BASE}/health`, { timeout: 5000 });
    if (health.ok()) {
      console.log('[Setup] Backend is healthy');
    } else {
      console.warn(`[Setup] Backend health check returned ${health.status()}`);
    }
  } catch (e) {
    console.error('[Setup] Backend not reachable. Tests requiring backend will fail.');
  }

  // 3. Ensure test user exists and get token
  try {
    await ensureTestUser(ctx);
    console.log('[Setup] Test user ready');
  } catch (e) {
    console.warn(`[Setup] Test user setup failed: ${e}`);
  }

  // 4. Get admin token
  try {
    await ensureAdminToken(ctx);
    console.log('[Setup] Admin token ready');
  } catch (e) {
    console.warn(`[Setup] Admin token setup failed: ${e}`);
  }

  await ctx.dispose();
  console.log('\n=== Setup Complete ===\n');
}

export default globalSetup;
