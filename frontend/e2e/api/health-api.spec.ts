import { test, expect } from '@playwright/test';

const API_BASE = 'http://localhost:9000';

test.describe('Health API', () => {
  test('should return healthy status from /health', async ({ request }) => {
    const response = await request.get(`${API_BASE}/health`);
    expect(response.status()).toBe(200);
    const data = await response.json();
    expect(data.status).toBeDefined();
  });

  test('should return API info from root', async ({ request }) => {
    const response = await request.get(`${API_BASE}/`);
    expect(response.status()).toBe(200);
    const data = await response.json();
    expect(data.message || data.version).toBeDefined();
  });
});
