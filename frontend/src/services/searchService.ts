/**
 * 검색 API 서비스
 */

import axios, { AxiosInstance } from 'axios';
import {
  SearchParams,
  SearchResponse,
  SuggestResponse,
  SearchFilters,
  SearchType,
  SortOrder,
  FacetGroup
} from '../types/search.types';

// API 베이스 URL (환경변수 또는 proxy 설정 사용)
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:9000';

class SearchService {
  private api: AxiosInstance;

  constructor() {
    this.api = axios.create({
      baseURL: `${API_BASE_URL}/api/search`,
      timeout: 10000,
      headers: {
        'Content-Type': 'application/json'
      }
    });

    // Request 인터셉터
    this.api.interceptors.request.use(
      (config) => {
        // 토큰이 있다면 추가 (추후 인증 구현 시)
        const token = localStorage.getItem('token');
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
      },
      (error) => {
        return Promise.reject(error);
      }
    );

    // Response 인터셉터
    this.api.interceptors.response.use(
      (response) => response.data,
      (error) => {
        // 에러 처리
        if (error.response) {
          // 서버 응답이 있는 경우
          const errorMessage = error.response.data?.detail || '서버 오류가 발생했습니다.';
          console.error('API Error:', errorMessage);
          throw new Error(errorMessage);
        } else if (error.request) {
          // 요청은 보냈지만 응답이 없는 경우
          console.error('No response:', error.request);
          throw new Error('서버에 연결할 수 없습니다.');
        } else {
          // 요청 설정 중 오류 발생
          console.error('Request error:', error.message);
          throw new Error('요청 중 오류가 발생했습니다.');
        }
      }
    );
  }

  /**
   * 통합 검색
   */
  async search(params: SearchParams): Promise<SearchResponse> {
    const queryParams = this.buildQueryParams(params);

    try {
      const response = await this.api.get<SearchResponse>('/', {
        params: queryParams
      });
      return response as unknown as SearchResponse;
    } catch (error) {
      console.error('Search failed:', error);
      throw error;
    }
  }

  /**
   * 입찰공고 검색
   */
  async searchBids(params: Partial<SearchParams>): Promise<SearchResponse> {
    const queryParams = this.buildQueryParams({
      ...params,
      type: SearchType.BID
    } as SearchParams);

    try {
      const response = await this.api.get<SearchResponse>('/bids', {
        params: queryParams
      });
      return response as unknown as SearchResponse;
    } catch (error) {
      console.error('Bid search failed:', error);
      throw error;
    }
  }

  /**
   * 문서 검색
   */
  async searchDocuments(params: Partial<SearchParams>): Promise<SearchResponse> {
    const queryParams = {
      q: params.query || '',
      file_type: (params.filters as any)?.fileType,
      sort: params.sort || SortOrder.RELEVANCE,
      page: params.page || 1,
      size: params.size || 20
    };

    try {
      const response = await this.api.get<SearchResponse>('/documents', {
        params: queryParams
      });
      return response as unknown as SearchResponse;
    } catch (error) {
      console.error('Document search failed:', error);
      throw error;
    }
  }

  /**
   * 기업 검색
   */
  async searchCompanies(params: Partial<SearchParams>): Promise<SearchResponse> {
    const queryParams = {
      q: params.query || '',
      industry: params.filters?.industry,
      region: params.filters?.region,
      page: params.page || 1,
      size: params.size || 20
    };

    try {
      const response = await this.api.get<SearchResponse>('/companies', {
        params: queryParams
      });
      return response as unknown as SearchResponse;
    } catch (error) {
      console.error('Company search failed:', error);
      throw error;
    }
  }

  /**
   * 검색어 자동완성
   */
  async getSuggestions(query: string, limit: number = 10): Promise<SuggestResponse> {
    if (!query || query.length < 2) {
      return {
        query,
        suggestions: [],
        count: 0
      };
    }

    try {
      const response = await this.api.get<SuggestResponse>('/suggest', {
        params: { q: query, limit }
      });
      return response as unknown as SuggestResponse;
    } catch (error) {
      console.error('Get suggestions failed:', error);
      // 에러 시 빈 결과 반환
      return {
        query,
        suggestions: [],
        count: 0
      };
    }
  }

  /**
   * 패싯 정보 조회
   */
  async getFacets(searchType?: SearchType, filters?: SearchFilters): Promise<FacetGroup> {
    try {
      const params: any = {};
      if (searchType) params.type = searchType;
      if (filters) {
        Object.entries(filters).forEach(([key, value]) => {
          if (value !== undefined && value !== null && value !== '') {
            params[key] = value;
          }
        });
      }

      const response = await this.api.get<{ facets: FacetGroup }>('/facets', {
        params
      });
      return (response as any).facets || {};
    } catch (error) {
      console.error('Get facets failed:', error);
      return {};
    }
  }

  /**
   * 쿼리 파라미터 빌드
   */
  private buildQueryParams(params: SearchParams): Record<string, any> {
    const queryParams: Record<string, any> = {
      q: params.query,
      type: params.type,
      sort: params.sort,
      page: params.page,
      size: params.size
    };

    // 필터 추가
    if (params.filters) {
      const filters = params.filters;

      if (filters.startDate) {
        queryParams.start_date = filters.startDate;
      }
      if (filters.endDate) {
        queryParams.end_date = filters.endDate;
      }
      if (filters.minPrice !== undefined) {
        queryParams.min_price = filters.minPrice;
      }
      if (filters.maxPrice !== undefined) {
        queryParams.max_price = filters.maxPrice;
      }
      if (filters.organization) {
        queryParams.organization = filters.organization;
      }
      if (filters.industry) {
        queryParams.industry = filters.industry;
      }
      if (filters.status) {
        queryParams.status = filters.status;
      }
      if (filters.region) {
        queryParams.region = filters.region;
      }
    }

    return queryParams;
  }

  /**
   * 검색 URL 생성 (브라우저 URL 동기화용)
   */
  static buildSearchUrl(params: SearchParams): string {
    const searchParams = new URLSearchParams();

    searchParams.set('q', params.query);
    searchParams.set('type', params.type);
    searchParams.set('sort', params.sort);
    searchParams.set('page', params.page.toString());
    searchParams.set('size', params.size.toString());

    // 필터 추가
    if (params.filters) {
      Object.entries(params.filters).forEach(([key, value]) => {
        if (value !== undefined && value !== null && value !== '') {
          searchParams.set(key, value.toString());
        }
      });
    }

    return searchParams.toString();
  }

  /**
   * URL에서 검색 파라미터 파싱
   */
  static parseSearchUrl(urlSearch: string): Partial<SearchParams> {
    const searchParams = new URLSearchParams(urlSearch);

    const params: Partial<SearchParams> = {
      query: searchParams.get('q') || '',
      type: (searchParams.get('type') as SearchType) || SearchType.ALL,
      sort: (searchParams.get('sort') as SortOrder) || SortOrder.RELEVANCE,
      page: parseInt(searchParams.get('page') || '1'),
      size: parseInt(searchParams.get('size') || '20')
    };

    // 필터 파싱
    const filters: SearchFilters = {};

    const startDate = searchParams.get('startDate');
    if (startDate) filters.startDate = startDate;

    const endDate = searchParams.get('endDate');
    if (endDate) filters.endDate = endDate;

    const minPrice = searchParams.get('minPrice');
    if (minPrice) filters.minPrice = parseInt(minPrice);

    const maxPrice = searchParams.get('maxPrice');
    if (maxPrice) filters.maxPrice = parseInt(maxPrice);

    const organization = searchParams.get('organization');
    if (organization) filters.organization = organization;

    const industry = searchParams.get('industry');
    if (industry) filters.industry = industry;

    const status = searchParams.get('status');
    if (status) filters.status = status;

    const region = searchParams.get('region');
    if (region) filters.region = region;

    if (Object.keys(filters).length > 0) {
      params.filters = filters;
    }

    return params;
  }
}

// 싱글톤 인스턴스 export
export const searchService = new SearchService();

// 개별 함수로도 export (편의성)
export const search = (params: SearchParams) => searchService.search(params);
export const searchBids = (params: Partial<SearchParams>) => searchService.searchBids(params);
export const searchDocuments = (params: Partial<SearchParams>) => searchService.searchDocuments(params);
export const searchCompanies = (params: Partial<SearchParams>) => searchService.searchCompanies(params);
export const getSuggestions = (query: string, limit?: number) => searchService.getSuggestions(query, limit);
export const getFacets = (searchType?: SearchType, filters?: SearchFilters) => searchService.getFacets(searchType, filters);

export default searchService;