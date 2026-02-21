import { test, expect } from '@playwright/test';

const API_BASE = 'http://localhost:9000';

test.describe('Search API', () => {
  test('should search with Korean keyword', async ({ request }) => {
    const response = await request.get(`${API_BASE}/api/search?q=공사&limit=5`);
    expect(response.status()).toBe(200);
    const data = await response.json();
    expect(data.success).toBeDefined();
  });

  test('should handle empty query', async ({ request }) => {
    const response = await request.get(`${API_BASE}/api/search`);
    expect(response.status()).toBe(200);
  });

  test('should support pagination', async ({ request }) => {
    const response = await request.get(`${API_BASE}/api/search?q=공사&page=1&limit=3`);
    expect(response.status()).toBe(200);
    const data = await response.json();
    expect(data.page || data.total).toBeDefined();
  });

  test('should return bid list', async ({ request }) => {
    const response = await request.get(`${API_BASE}/api/bids?limit=5`);
    expect(response.status()).toBe(200);
    const data = await response.json();
    expect(data.data || data.results).toBeDefined();
  });
});
