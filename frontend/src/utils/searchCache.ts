/**
 * 검색 결과 캐싱 유틸리티
 * localStorage와 메모리를 활용한 2단계 캐싱 전략
 */

import { SearchParams, SearchResponse } from '../types/search.types';

// 캐시 설정
const CACHE_CONFIG = {
  maxMemoryItems: 50,          // 메모리 캐시 최대 항목 수
  maxLocalStorageSize: 5 * 1024 * 1024, // 5MB localStorage 최대 크기
  memoryTTL: 5 * 60 * 1000,    // 5분 메모리 캐시 TTL
  localStorageTTL: 30 * 60 * 1000, // 30분 localStorage TTL
  cacheKeyPrefix: 'search_cache_'
};

// 메모리 캐시 타입
interface CacheEntry<T> {
  data: T;
  timestamp: number;
  hits: number;
}

// 메모리 캐시 스토어
class MemoryCache<T> {
  private cache: Map<string, CacheEntry<T>>;
  private maxSize: number;

  constructor(maxSize: number = CACHE_CONFIG.maxMemoryItems) {
    this.cache = new Map();
    this.maxSize = maxSize;
  }

  get(key: string): T | null {
    const entry = this.cache.get(key);

    if (!entry) return null;

    // TTL 체크
    if (Date.now() - entry.timestamp > CACHE_CONFIG.memoryTTL) {
      this.cache.delete(key);
      return null;
    }

    // 히트 카운트 증가
    entry.hits++;

    // LRU: 최근 사용한 항목을 맨 뒤로 이동
    this.cache.delete(key);
    this.cache.set(key, entry);

    return entry.data;
  }

  set(key: string, data: T): void {
    // 캐시 크기 제한 체크
    if (this.cache.size >= this.maxSize) {
      // LRU: 가장 오래된 항목 제거
      const firstKey = this.cache.keys().next().value;
      if (firstKey) {
        this.cache.delete(firstKey);
      }
    }

    this.cache.set(key, {
      data,
      timestamp: Date.now(),
      hits: 0
    });
  }

  has(key: string): boolean {
    return this.cache.has(key);
  }

  clear(): void {
    this.cache.clear();
  }

  getStats() {
    const entries = Array.from(this.cache.values());
    return {
      size: this.cache.size,
      totalHits: entries.reduce((sum, entry) => sum + entry.hits, 0),
      avgAge: entries.length > 0
        ? entries.reduce((sum, entry) => sum + (Date.now() - entry.timestamp), 0) / entries.length
        : 0
    };
  }
}

// LocalStorage 캐시 유틸리티
class LocalStorageCache {
  private prefix: string;

  constructor(prefix: string = CACHE_CONFIG.cacheKeyPrefix) {
    this.prefix = prefix;
    this.cleanup(); // 초기화 시 만료된 항목 정리
  }

  private getFullKey(key: string): string {
    return `${this.prefix}${key}`;
  }

  get<T>(key: string): T | null {
    try {
      const fullKey = this.getFullKey(key);
      const item = localStorage.getItem(fullKey);

      if (!item) return null;

      const entry = JSON.parse(item) as CacheEntry<T>;

      // TTL 체크
      if (Date.now() - entry.timestamp > CACHE_CONFIG.localStorageTTL) {
        localStorage.removeItem(fullKey);
        return null;
      }

      return entry.data;
    } catch (error) {
      console.error('LocalStorage cache get error:', error);
      return null;
    }
  }

  set<T>(key: string, data: T): boolean {
    try {
      const fullKey = this.getFullKey(key);
      const entry: CacheEntry<T> = {
        data,
        timestamp: Date.now(),
        hits: 0
      };

      const serialized = JSON.stringify(entry);

      // 크기 체크
      if (serialized.length > CACHE_CONFIG.maxLocalStorageSize) {
        return false;
      }

      // 저장 시도
      try {
        localStorage.setItem(fullKey, serialized);
        return true;
      } catch (e) {
        // 용량 초과 시 오래된 항목 삭제 후 재시도
        if (e instanceof DOMException && e.code === 22) {
          this.evictOldest();
          localStorage.setItem(fullKey, serialized);
          return true;
        }
        throw e;
      }
    } catch (error) {
      console.error('LocalStorage cache set error:', error);
      return false;
    }
  }

  private evictOldest(): void {
    const items: Array<{ key: string; timestamp: number }> = [];

    for (let i = 0; i < localStorage.length; i++) {
      const key = localStorage.key(i);
      if (key && key.startsWith(this.prefix)) {
        try {
          const item = localStorage.getItem(key);
          if (item) {
            const entry = JSON.parse(item);
            items.push({ key, timestamp: entry.timestamp || 0 });
          }
        } catch (e) {
          // 파싱 실패한 항목은 삭제
          localStorage.removeItem(key);
        }
      }
    }

    // 가장 오래된 항목 25% 삭제
    items.sort((a, b) => a.timestamp - b.timestamp);
    const toRemove = Math.max(1, Math.floor(items.length * 0.25));

    for (let i = 0; i < toRemove; i++) {
      localStorage.removeItem(items[i].key);
    }
  }

  cleanup(): void {
    const now = Date.now();
    const keysToRemove: string[] = [];

    for (let i = 0; i < localStorage.length; i++) {
      const key = localStorage.key(i);
      if (key && key.startsWith(this.prefix)) {
        try {
          const item = localStorage.getItem(key);
          if (item) {
            const entry = JSON.parse(item);
            if (now - entry.timestamp > CACHE_CONFIG.localStorageTTL) {
              keysToRemove.push(key);
            }
          }
        } catch (e) {
          keysToRemove.push(key);
        }
      }
    }

    keysToRemove.forEach(key => localStorage.removeItem(key));
  }

  clear(): void {
    const keysToRemove: string[] = [];

    for (let i = 0; i < localStorage.length; i++) {
      const key = localStorage.key(i);
      if (key && key.startsWith(this.prefix)) {
        keysToRemove.push(key);
      }
    }

    keysToRemove.forEach(key => localStorage.removeItem(key));
  }
}

// 검색 캐시 매니저
class SearchCacheManager {
  private memoryCache: MemoryCache<SearchResponse>;
  private localStorageCache: LocalStorageCache;

  constructor() {
    this.memoryCache = new MemoryCache();
    this.localStorageCache = new LocalStorageCache();
  }

  /**
   * 캐시 키 생성
   */
  private getCacheKey(params: SearchParams): string {
    // 파라미터를 정렬하여 일관된 키 생성
    const sortedParams = {
      query: params.query || '',
      searchType: params.type || 'ALL',
      filters: params.filters ? JSON.stringify(params.filters) : '{}',
      sortOrder: params.sort || 'RELEVANCE',
      page: params.page || 1,
      size: params.size || 20
    };

    return btoa(JSON.stringify(sortedParams))
      .replace(/[^a-zA-Z0-9]/g, '') // 특수문자 제거
      .substring(0, 50); // 길이 제한
  }

  /**
   * 검색 결과 가져오기 (캐시 우선)
   */
  get(params: SearchParams): SearchResponse | null {
    const key = this.getCacheKey(params);

    // 1. 메모리 캐시 확인
    const memoryResult = this.memoryCache.get(key);
    if (memoryResult) {
      return memoryResult;
    }

    // 2. localStorage 캐시 확인
    const localResult = this.localStorageCache.get<SearchResponse>(key);
    if (localResult) {
      // 메모리 캐시에도 저장
      this.memoryCache.set(key, localResult);
      return localResult;
    }

    return null;
  }

  /**
   * 검색 결과 캐싱
   */
  set(params: SearchParams, response: SearchResponse): void {
    const key = this.getCacheKey(params);

    // 메모리 캐시에 저장
    this.memoryCache.set(key, response);

    // localStorage에도 저장 (실패해도 무시)
    this.localStorageCache.set(key, response);
  }

  /**
   * 특정 검색 타입의 캐시 무효화
   */
  invalidate(searchType?: string): void {
    // 메모리 캐시 클리어
    this.memoryCache.clear();

    // localStorage 캐시 클리어
    if (searchType) {
      // 특정 타입만 클리어하는 로직 구현 가능
    } else {
      this.localStorageCache.clear();
    }
  }

  /**
   * 캐시 통계 정보
   */
  getStats() {
    return {
      memory: this.memoryCache.getStats(),
      localStorage: {
        // localStorage 통계는 간단하게
        itemCount: Object.keys(localStorage).filter(key =>
          key.startsWith(CACHE_CONFIG.cacheKeyPrefix)
        ).length
      }
    };
  }

  /**
   * 캐시 정리
   */
  cleanup(): void {
    this.localStorageCache.cleanup();
  }
}

// 싱글톤 인스턴스
const searchCache = new SearchCacheManager();

// 자동 정리 스케줄링 (10분마다)
if (typeof window !== 'undefined') {
  setInterval(() => {
    searchCache.cleanup();
  }, 10 * 60 * 1000);
}

export default searchCache;

/**
 * React Query와 통합하여 사용하는 캐시 래퍼
 */
export function withSearchCache<T extends (...args: any[]) => Promise<SearchResponse>>(
  searchFn: T
): T {
  return (async (...args: Parameters<T>) => {
    const params = args[0] as SearchParams;

    // 캐시 확인
    const cached = searchCache.get(params);
    if (cached) {
      return cached;
    }

    // 실제 검색 실행
    const result = await searchFn(...args);

    // 결과 캐싱
    if (result && !result.error) {
      searchCache.set(params, result);
    }

    return result;
  }) as T;
}

/**
 * 캐시 프리페칭 유틸리티
 */
export async function prefetchSearchResults(
  params: SearchParams,
  searchFn: (params: SearchParams) => Promise<SearchResponse>
): Promise<void> {
  // 이미 캐시에 있으면 스킵
  if (searchCache.get(params)) {
    return;
  }

  try {
    const result = await searchFn(params);
    if (result && !result.error) {
      searchCache.set(params, result);
    }
  } catch (error) {
    console.error('Prefetch error:', error);
  }
}

/**
 * 관련 검색어 프리페칭
 */
export function prefetchRelatedSearches(
  baseParams: SearchParams,
  relatedQueries: string[],
  searchFn: (params: SearchParams) => Promise<SearchResponse>
): void {
  relatedQueries.forEach(query => {
    const params = { ...baseParams, query, page: 1 };
    prefetchSearchResults(params, searchFn);
  });
}

export { searchCache, SearchCacheManager };