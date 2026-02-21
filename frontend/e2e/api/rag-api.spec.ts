import { test, expect } from '@playwright/test';

const API_BASE = 'http://localhost:9000';

test.describe('RAG Search API', () => {
  test('should respond to RAG search endpoint', async ({ request }) => {
    const response = await request.get(`${API_BASE}/api/rag/search?q=도로공사&limit=5`);
    // RAG may return 200 (results) or 503 (not configured)
    expect([200, 503]).toContain(response.status());
    if (response.status() === 200) {
      const data = await response.json();
      expect(data.results).toBeDefined();
    }
  });

  test('should respond to RAG ask endpoint', async ({ request }) => {
    const response = await request.get(`${API_BASE}/api/rag/ask?q=입찰 자격요건은?&limit=3`);
    expect([200, 503]).toContain(response.status());
  });
});
