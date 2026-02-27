/**
 * React Query hooks for search functionality
 */

import { useQuery, useQueryClient } from '@tanstack/react-query';
import { useState, useCallback, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import {
  SearchParams,
  SearchResponse,
  SuggestResponse,
  FacetGroup,
  SearchType,
  SortOrder,
  SearchFilters,
  SearchState
} from '../types/search.types';
import searchService from '../services/searchService';

// Query keys
const QUERY_KEYS = {
  search: (params: SearchParams) => ['search', params] as const,
  suggestions: (query: string) => ['suggestions', query] as const,
  facets: (searchType: SearchType, filters?: SearchFilters) =>
    ['facets', searchType, filters] as const,
  recentSearches: ['recentSearches'] as const
};

/**
 * 메인 검색 Hook
 */
export function useSearch(initialParams?: Partial<SearchParams>) {
  const queryClient = useQueryClient();
  const [searchParams, setSearchParams] = useSearchParams();

  // URL 파라미터에서 검색 상태 복원
  const [params, setParams] = useState<SearchParams>(() => ({
    query: searchParams.get('q') || initialParams?.query || '',
    type: (searchParams.get('type') as SearchType) || initialParams?.type || SearchType.ALL,
    filters: JSON.parse(searchParams.get('filters') || '{}'),
    sort: (searchParams.get('sort') as SortOrder) || initialParams?.sort || SortOrder.RELEVANCE,
    page: parseInt(searchParams.get('page') || '1'),
    size: parseInt(searchParams.get('size') || '20')
  }));

  // URL 파라미터 동기화
  useEffect(() => {
    const newParams = new URLSearchParams();

    if (params.query) newParams.set('q', params.query);
    if (params.type !== SearchType.ALL) newParams.set('type', params.type);
    if (Object.keys(params.filters || {}).length > 0) {
      newParams.set('filters', JSON.stringify(params.filters));
    }
    if (params.sort !== SortOrder.RELEVANCE) newParams.set('sort', params.sort);
    if (params.page !== 1) newParams.set('page', params.page.toString());
    if (params.size !== 20) newParams.set('size', params.size.toString());

    setSearchParams(newParams, { replace: true });
  }, [params, setSearchParams]);

  // 검색 쿼리
  const searchQuery = useQuery<SearchResponse>({
    queryKey: QUERY_KEYS.search(params),
    queryFn: () => searchService.search(params),
    enabled: !!params.query, // 검색어가 있을 때만 실행
    staleTime: 5 * 60 * 1000, // 5분
    gcTime: 10 * 60 * 1000, // 10분 (이전 cacheTime)
    retry: 2
  });

  // 검색 파라미터 업데이트
  const updateParams = useCallback((newParams: Partial<SearchParams>) => {
    setParams(prev => ({
      ...prev,
      ...newParams,
      // 필터나 검색어가 변경되면 페이지를 1로 리셋
      page: (newParams.query !== undefined && newParams.query !== prev.query) ||
             (newParams.filters !== undefined && JSON.stringify(newParams.filters) !== JSON.stringify(prev.filters)) ||
             (newParams.type !== undefined && newParams.type !== prev.type)
        ? 1
        : newParams.page || prev.page
    }));
  }, []);

  // 검색 실행
  const search = useCallback((query?: string) => {
    if (query !== undefined) {
      updateParams({ query, page: 1 });
    }
    // React Query가 자동으로 재실행
  }, [updateParams]);

  // 필터 변경
  const updateFilters = useCallback((filters: SearchFilters) => {
    updateParams({ filters, page: 1 });
  }, [updateParams]);

  // 정렬 변경
  const updateSort = useCallback((sortOrder: SortOrder) => {
    updateParams({ sort: sortOrder });
  }, [updateParams]);

  // 페이지 변경
  const updatePage = useCallback((page: number) => {
    updateParams({ page });
  }, [updateParams]);

  // 페이지 크기 변경
  const updatePageSize = useCallback((size: number) => {
    updateParams({ size, page: 1 });
  }, [updateParams]);

  // 검색 타입 변경
  const updateSearchType = useCallback((searchType: SearchType) => {
    updateParams({ type: searchType, page: 1 });
  }, [updateParams]);

  // 검색 초기화
  const resetSearch = useCallback(() => {
    setParams({
      query: '',
      type: SearchType.ALL,
      filters: {},
      sort: SortOrder.RELEVANCE,
      page: 1,
      size: 20
    });
    queryClient.removeQueries({ queryKey: ['search'] });
  }, [queryClient]);

  // Prefetch next page
  const prefetchNextPage = useCallback(() => {
    const nextPage = params.page + 1;
    const totalPages = Math.ceil((searchQuery.data?.totalCount || 0) / params.size);

    if (nextPage <= totalPages) {
      queryClient.prefetchQuery({
        queryKey: QUERY_KEYS.search({ ...params, page: nextPage }),
        queryFn: () => searchService.search({ ...params, page: nextPage }),
        staleTime: 5 * 60 * 1000
      });
    }
  }, [params, searchQuery.data, queryClient]);

  return {
    // State
    params,
    results: searchQuery.data?.results || [],
    totalCount: searchQuery.data?.totalCount || 0,
    pageInfo: searchQuery.data?.pageInfo || {
      currentPage: params.page,
      totalPages: 0,
      pageSize: params.size,
      totalItems: 0,
      hasNext: false,
      hasPrev: false
    },
    facets: searchQuery.data?.facets,

    // Status
    isLoading: searchQuery.isLoading,
    isError: searchQuery.isError,
    error: searchQuery.error,
    isFetching: searchQuery.isFetching,

    // Actions
    search,
    updateFilters,
    updateSort,
    updatePage,
    updatePageSize,
    updateSearchType,
    resetSearch,
    prefetchNextPage,
    refetch: searchQuery.refetch
  };
}

/**
 * 자동완성 제안 Hook
 */
export function useSearchSuggestions(query: string, enabled = true) {
  return useQuery<SuggestResponse>({
    queryKey: QUERY_KEYS.suggestions(query),
    queryFn: () => searchService.getSuggestions(query),
    enabled: enabled && query.length >= 2, // 2글자 이상일 때만
    staleTime: 30 * 1000, // 30초
    gcTime: 60 * 1000 // 1분
  });
}

/**
 * 패싯(facets) 정보 Hook
 */
export function useSearchFacets(searchType: SearchType, filters?: SearchFilters) {
  return useQuery<FacetGroup>({
    queryKey: QUERY_KEYS.facets(searchType, filters),
    queryFn: () => searchService.getFacets(searchType, filters),
    staleTime: 5 * 60 * 1000, // 5분
    gcTime: 10 * 60 * 1000 // 10분
  });
}

/**
 * 최근 검색어 Hook
 */
export function useRecentSearches() {
  const queryClient = useQueryClient();

  const query = useQuery<string[]>({
    queryKey: QUERY_KEYS.recentSearches,
    queryFn: () => {
      const saved = localStorage.getItem('recentSearches');
      return saved ? JSON.parse(saved) : [];
    },
    staleTime: Infinity // 항상 캐시 사용
  });

  const addRecentSearch = useCallback((searchTerm: string) => {
    const current = query.data || [];
    const updated = [
      searchTerm,
      ...current.filter(item => item !== searchTerm)
    ].slice(0, 10); // 최대 10개 저장

    localStorage.setItem('recentSearches', JSON.stringify(updated));
    queryClient.setQueryData(QUERY_KEYS.recentSearches, updated);
  }, [query.data, queryClient]);

  const removeRecentSearch = useCallback((searchTerm: string) => {
    const current = query.data || [];
    const updated = current.filter(item => item !== searchTerm);

    localStorage.setItem('recentSearches', JSON.stringify(updated));
    queryClient.setQueryData(QUERY_KEYS.recentSearches, updated);
  }, [query.data, queryClient]);

  const clearRecentSearches = useCallback(() => {
    localStorage.removeItem('recentSearches');
    queryClient.setQueryData(QUERY_KEYS.recentSearches, []);
  }, [queryClient]);

  return {
    recentSearches: query.data || [],
    addRecentSearch,
    removeRecentSearch,
    clearRecentSearches
  };
}

/**
 * 입찰공고 검색 Hook
 */
export function useSearchBids(params: SearchParams) {
  return useQuery<SearchResponse>({
    queryKey: ['searchBids', params],
    queryFn: () => searchService.searchBids(params),
    enabled: !!params.query,
    staleTime: 5 * 60 * 1000
  });
}

/**
 * 문서 검색 Hook
 */
export function useSearchDocuments(params: SearchParams) {
  return useQuery<SearchResponse>({
    queryKey: ['searchDocuments', params],
    queryFn: () => searchService.searchDocuments(params),
    enabled: !!params.query,
    staleTime: 5 * 60 * 1000
  });
}

/**
 * 기업 검색 Hook
 */
export function useSearchCompanies(params: SearchParams) {
  return useQuery<SearchResponse>({
    queryKey: ['searchCompanies', params],
    queryFn: () => searchService.searchCompanies(params),
    enabled: !!params.query,
    staleTime: 5 * 60 * 1000
  });
}

/**
 * 검색 상태 관리 Hook (로컬)
 */
export function useSearchState(initialState?: Partial<SearchState>) {
  const [state, setState] = useState<SearchState>(() => ({
    query: '',
    type: SearchType.ALL,
    filters: {},
    sort: SortOrder.RELEVANCE,
    page: 1,
    size: 20,
    results: [],
    totalCount: 0,
    loading: false,
    error: undefined,
    ...initialState
  }));

  const updateState = useCallback((updates: Partial<SearchState>) => {
    setState(prev => ({ ...prev, ...updates }));
  }, []);

  const resetState = useCallback(() => {
    setState({
      query: '',
      type: SearchType.ALL,
      filters: {},
      sort: SortOrder.RELEVANCE,
      page: 1,
      size: 20,
      results: [],
      totalCount: 0,
      loading: false,
      error: undefined
    });
  }, []);

  return {
    state,
    updateState,
    resetState
  };
}