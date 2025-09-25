/**
 * 검색 관련 TypeScript 타입 정의
 */

// 검색 타입 enum
export enum SearchType {
  ALL = 'all',
  BID = 'bid',
  DOCUMENT = 'document',
  COMPANY = 'company'
}

// 정렬 순서 enum
export enum SortOrder {
  RELEVANCE = 'relevance',
  DATE_DESC = 'date_desc',
  DATE_ASC = 'date_asc',
  PRICE_DESC = 'price_desc',
  PRICE_ASC = 'price_asc'
}

// 검색 필터 인터페이스
export interface SearchFilters {
  startDate?: string;
  endDate?: string;
  minPrice?: number;
  maxPrice?: number;
  organization?: string;
  industry?: string;
  status?: string;
  region?: string;
  tags?: string[];
  excludeClosed?: boolean;
  onlyUrgent?: boolean;
  hasAttachments?: boolean;
}

// 필터 프리셋
export interface FilterPreset {
  id: string;
  name: string;
  filters: SearchFilters;
  icon?: React.ReactNode;
  createdAt?: Date;
}

// 검색 요청 파라미터
export interface SearchParams {
  query: string;
  type: SearchType;
  filters?: SearchFilters;
  sort: SortOrder;
  page: number;
  size: number;
}

// 입찰공고 결과 타입
export interface BidResult {
  type: 'bid';
  id: string;
  bidNoticeNo: string;
  title: string;
  organization: string;
  price?: number;
  deadline?: string;
  status: string;
  score?: number;
  highlight?: string;
}

// 문서 결과 타입
export interface DocumentResult {
  type: 'document';
  id: string;
  filename: string;
  path: string;
  fileType: string;
  score?: number;
  size: number;
  modified: string;
  title: string;
  highlight?: string[];
  metadata?: Record<string, any>;
}

// 기업 결과 타입
export interface CompanyResult {
  type: 'company';
  id: string;
  title?: string;  // ShareIcon에서 사용하기 위해 추가
  name: string;
  businessNumber: string;
  industry?: string;
  region?: string;
  createdAt?: string;
}

// 통합 검색 결과 타입
export type SearchResult = BidResult | DocumentResult | CompanyResult;

// 페이지 정보
export interface PageInfo {
  currentPage: number;
  pageSize: number;
  totalPages: number;
  totalItems: number;
}

// 패싯 정보
export interface Facet {
  name: string;
  count: number;
}

export interface FacetGroup {
  organizations?: Facet[];
  status?: Facet[];
  priceRanges?: Array<{ range: string; count: number }>;
}

// 검색 응답
export interface SearchResponse {
  query: string;
  searchType: string;
  results: SearchResult[];
  totalCount: number;
  pageInfo: PageInfo;
  facets?: FacetGroup;
  error?: string;
}

// 자동완성 응답
export interface SuggestResponse {
  query: string;
  suggestions: string[];
  count: number;
}

// 컴포넌트 Props 타입들
export interface SearchBarProps {
  onSearch: (query: string) => void;
  initialQuery?: string;
  placeholder?: string;
  showSuggestions?: boolean;
}

export interface SearchFiltersProps {
  filters: SearchFilters;
  onFilterChange: (filters: SearchFilters) => void;
  facets?: FacetGroup;
}

export interface SearchResultsProps {
  results: SearchResult[];
  loading: boolean;
  error?: string;
  onItemClick?: (item: SearchResult) => void;
}

export interface SearchPaginationProps {
  currentPage: number;
  totalPages: number;
  pageSize: number;
  totalItems: number;
  onPageChange: (page: number) => void;
  onPageSizeChange?: (size: number) => void;
  loading?: boolean;
  showFirstLast?: boolean;
  showPageSizeSelector?: boolean;
  showItemsInfo?: boolean;
  pageSizeOptions?: number[];
  viewMode?: 'list' | 'grid';
  onViewModeChange?: (mode: 'list' | 'grid') => void;
}

// 검색 상태 관리
export interface SearchState {
  query: string;
  type: SearchType;
  filters: SearchFilters;
  sort: SortOrder;
  page: number;
  size: number;
  results: SearchResult[];
  totalCount: number;
  pageInfo?: PageInfo;
  facets?: FacetGroup;
  loading: boolean;
  error?: string;
}