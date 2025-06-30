// @ts-nocheck
// eslint-disable
import { test, expect } from '@playwright/test';

// API base URL (FastAPI dev server)
const BASE_URL = 'http://localhost:8000';

test.describe('Papers API E2E 테스트', () => {
  test('GET /papers - 논문 목록을 성공적으로 가져온다', async ({ request }) => {
    const response = await request.get(`${BASE_URL}/papers`);
    
    // 1. 응답 상태 코드 검증
    expect(response.status()).toBe(200);

    // 2. 응답 본문이 JSON 배열인지 검증
    const body = await response.json();
    expect(Array.isArray(body)).toBeTruthy();

    // 3. (데이터가 있다면) 첫 번째 항목의 데이터 구조 검증
    if (body.length > 0) {
      const firstPaper = body[0];
      expect(firstPaper).toHaveProperty('id');
      expect(firstPaper).toHaveProperty('title');
      expect(firstPaper).toHaveProperty('author');
      expect(firstPaper).toHaveProperty('publisher');
    }
  });

  test('POST /search - 키워드로 논문을 성공적으로 검색한다', async ({ request }) => {
    const searchQuery = '건축'; // 테스트용 검색어
    const response = await request.post(`${BASE_URL}/search?query=${encodeURIComponent(searchQuery)}`);

    // 1. 응답 상태 코드 검증
    expect(response.status()).toBe(200);

    // 2. 응답 본문이 JSON 배열인지 검증
    const body = await response.json();
    expect(Array.isArray(body)).toBeTruthy();

    // 3. (검색 결과가 있다면) 첫 번째 결과의 데이터 구조 검증
    if (body.length > 0) {
      const firstResult = body[0];
      expect(firstResult).toHaveProperty('paper_title');
      expect(firstResult).toHaveProperty('chunk_text');
      expect(firstResult).toHaveProperty('page_number');
    }
  });

  test('GET /health - 헬스 체크가 성공한다', async ({ request }) => {
    const response = await request.get(`${BASE_URL}/health`);
    expect(response.status()).toBe(200);
    const body = await response.json();
    expect(body).toEqual({ status: 'ok' });
  });
}); 