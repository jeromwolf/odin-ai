import { Page, APIRequestContext } from '@playwright/test';
import fs from 'fs';
import path from 'path';

const API_BASE = 'http://localhost:9000';
const AUTH_DIR = path.resolve(__dirname, '../../.auth');

export const TEST_USER = {
  email: 'e2e-test@odin-ai.com',
  password: 'TestPass123!',
  username: 'e2e-tester',
  full_name: 'E2E Test User',
};

export const ADMIN_USER = {
  email: 'admin@odin.ai',
  password: 'admin123',
};

function getStoredToken(type: 'user' | 'admin'): string | null {
  const file = path.join(AUTH_DIR, `${type}.json`);
  try {
    const data = JSON.parse(fs.readFileSync(file, 'utf-8'));
    return data.token || null;
  } catch {
    return null;
  }
}

export function storeToken(type: 'user' | 'admin', token: string) {
  fs.mkdirSync(AUTH_DIR, { recursive: true });
  const file = path.join(AUTH_DIR, `${type}.json`);
  fs.writeFileSync(file, JSON.stringify({ token, stored_at: new Date().toISOString() }));
}

/** Inject user JWT token into localStorage (fast, no UI) */
export async function setupUserAuth(page: Page) {
  const token = getStoredToken('user');
  if (!token) throw new Error('No user token stored. Run global-setup first.');
  await page.addInitScript((t) => {
    localStorage.setItem('odin_ai_token', t);
  }, token);
}

/** Inject admin JWT token into localStorage (fast, no UI) */
export async function setupAdminAuth(page: Page) {
  const token = getStoredToken('admin');
  if (!token) throw new Error('No admin token stored. Run global-setup first.');
  await page.addInitScript((t) => {
    localStorage.setItem('admin_token', t);
  }, token);
}

/** Login via UI - for auth test specs only */
export async function loginViaUI(page: Page, email?: string, password?: string) {
  await page.goto('/login');
  await page.fill('input[type="email"], input[name="email"]', email || TEST_USER.email);
  await page.fill('input[type="password"], input[name="password"]', password || TEST_USER.password);
  await page.click('button[type="submit"]');
  await page.waitForURL(/\/(dashboard|search|$)/, { timeout: 10000 });
}

/** Admin login via UI */
export async function adminLoginViaUI(page: Page, email?: string, password?: string) {
  await page.goto('/admin/login');
  await page.fill('input[type="email"], input[name="email"]', email || ADMIN_USER.email);
  await page.fill('input[type="password"], input[name="password"]', password || ADMIN_USER.password);
  await page.click('button[type="submit"]');
  await page.waitForURL(/\/admin\/(dashboard|$)/, { timeout: 10000 });
}

/** Register test user via API (if not exists) */
export async function ensureTestUser(request: APIRequestContext): Promise<string> {
  // Try login first
  const loginRes = await request.post(`${API_BASE}/api/auth/login`, {
    data: { email: TEST_USER.email, password: TEST_USER.password },
  });

  if (loginRes.ok()) {
    const data = await loginRes.json();
    const token = data.access_token || data.token;
    storeToken('user', token);
    return token;
  }

  // Register if login failed
  const regRes = await request.post(`${API_BASE}/api/auth/register`, {
    data: {
      email: TEST_USER.email,
      password: TEST_USER.password,
      username: TEST_USER.username,
      full_name: TEST_USER.full_name,
    },
  });

  if (!regRes.ok()) {
    console.warn(`Registration failed (${regRes.status()}), trying login again...`);
  }

  // Login after registration
  const retryLogin = await request.post(`${API_BASE}/api/auth/login`, {
    data: { email: TEST_USER.email, password: TEST_USER.password },
  });

  if (retryLogin.ok()) {
    const data = await retryLogin.json();
    const token = data.access_token || data.token;
    storeToken('user', token);
    return token;
  }

  throw new Error('Failed to create/login test user');
}

/** Get admin token via API */
export async function ensureAdminToken(request: APIRequestContext): Promise<string> {
  const res = await request.post(`${API_BASE}/api/admin/auth/login`, {
    data: { email: ADMIN_USER.email, password: ADMIN_USER.password },
  });

  if (res.ok()) {
    const data = await res.json();
    const token = data.access_token || data.token;
    storeToken('admin', token);
    return token;
  }

  throw new Error(`Admin login failed: ${res.status()}`);
}
