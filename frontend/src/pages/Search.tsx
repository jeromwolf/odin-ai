/**
 * 통합 검색 페이지
 * 모든 검색 컴포넌트를 통합하여 완전한 검색 경험 제공
 */

import React, { useState, useCallback, useEffect } from 'react';
import {
  Box,
  Container,
  Typography,
  Paper,
  Grid,
  Tabs,
  Tab,
  Badge,
  Chip,
  Stack,
  Alert,
  AlertTitle,
  Fade,
  Grow,
  CircularProgress,
  Button,
  IconButton,
  Tooltip,
  Divider,
  useTheme,
  useMediaQuery
} from '@mui/material';
import {
  Search as SearchIcon,
  FilterList as FilterIcon,
  Sort as SortIcon,
  ViewList as ViewListIcon,
  ViewModule as ViewModuleIcon,
  Refresh as RefreshIcon,
  Download as DownloadIcon,
  Help as HelpIcon,
  TrendingUp as TrendingIcon
} from '@mui/icons-material';
import { styled } from '@mui/material/styles';

// Components
import SearchBar from '../components/search/SearchBar';
import SearchFilters from '../components/search/SearchFilters';
import SearchResults from '../components/search/SearchResults';
import SearchPagination from '../components/search/SearchPagination';

// Hooks
import { useSearch, useSearchFacets, useRecentSearches } from '../hooks/useSearch';

// Types
import {
  SearchType,
  SortOrder,
  SearchFilters as FilterType,
  SearchResult
} from '../types/search.types';

// 스타일 컴포넌트
const PageContainer = styled(Container)(({ theme }) => ({
  paddingTop: theme.spacing(3),
  paddingBottom: theme.spacing(6),
  minHeight: 'calc(100vh - 64px)', // 헤더 높이 제외
  [theme.breakpoints.down('sm')]: {
    paddingTop: theme.spacing(2),
    paddingBottom: theme.spacing(4)
  }
}));

const HeaderSection = styled(Box)(({ theme }) => ({
  marginBottom: theme.spacing(4),
  textAlign: 'center',
  [theme.breakpoints.down('sm')]: {
    marginBottom: theme.spacing(3)
  }
}));

const SearchSection = styled(Paper)(({ theme }) => ({
  padding: theme.spacing(3),
  marginBottom: theme.spacing(3),
  backgroundColor: theme.palette.background.paper,
  borderRadius: theme.shape.borderRadius * 2,
  boxShadow: theme.shadows[2],
  [theme.breakpoints.down('sm')]: {
    padding: theme.spacing(2),
    marginBottom: theme.spacing(2)
  }
}));

const ContentSection = styled(Box)(({ theme }) => ({
  display: 'flex',
  gap: theme.spacing(3),
  [theme.breakpoints.down('md')]: {
    flexDirection: 'column'
  }
}));

const FilterSection = styled(Box)(({ theme }) => ({
  width: '320px',
  flexShrink: 0,
  [theme.breakpoints.down('md')]: {
    width: '100%'
  }
}));

const ResultSection = styled(Box)(({ theme }) => ({
  flex: 1,
  minWidth: 0 // Prevent overflow
}));

const StyledTabs = styled(Tabs)(({ theme }) => ({
  marginBottom: theme.spacing(2),
  borderBottom: `1px solid ${theme.palette.divider}`,
  '& .MuiTab-root': {
    minHeight: 48,
    fontWeight: 500
  }
}));

const SortButton = styled(Button)(({ theme }) => ({
  textTransform: 'none',
  fontWeight: 500
}));

// 정렬 옵션
const SORT_OPTIONS = [
  { value: SortOrder.RELEVANCE, label: '관련도순' },
  { value: SortOrder.DATE_DESC, label: '최신순' },
  { value: SortOrder.DATE_ASC, label: '오래된순' },
  { value: SortOrder.PRICE_DESC, label: '금액 높은순' },
  { value: SortOrder.PRICE_ASC, label: '금액 낮은순' }
];

const Search: React.FC = () => {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));
  const isTablet = useMediaQuery(theme.breakpoints.down('md'));

  // Search state and hooks
  const {
    params,
    results,
    totalCount,
    pageInfo,
    facets,
    isLoading,
    isError,
    error,
    search,
    updateFilters,
    updateSort,
    updatePage,
    updatePageSize,
    updateSearchType,
    resetSearch,
    refetch
  } = useSearch();

  // 추가 hooks
  const { recentSearches, addRecentSearch } = useRecentSearches();
  const facetsQuery = useSearchFacets(params.type, params.filters);

  // Local states
  const [showFilters, setShowFilters] = useState(!isMobile);
  const [viewMode, setViewMode] = useState<'list' | 'grid'>('list');
  const [sortMenuAnchor, setSortMenuAnchor] = useState<HTMLElement | null>(null);
  const [showHelp, setShowHelp] = useState(false);

  // 검색 타입별 결과 개수
  const typeCounts = {
    all: totalCount,
    bid: results.filter((r: any) => r.type === 'bid').length,
    document: results.filter((r: any) => r.type === 'document').length,
    company: results.filter((r: any) => r.type === 'company').length
  };

  /**
   * 검색 실행 핸들러
   */
  const handleSearch = useCallback((query: string) => {
    search(query);
    addRecentSearch(query);
  }, [search, addRecentSearch]);

  /**
   * 필터 변경 핸들러
   */
  const handleFilterChange = useCallback((filters: FilterType) => {
    updateFilters(filters);
  }, [updateFilters]);

  /**
   * 검색 타입 변경 핸들러
   */
  const handleTypeChange = useCallback((event: React.SyntheticEvent, newValue: SearchType) => {
    updateSearchType(newValue);
  }, [updateSearchType]);

  /**
   * 정렬 변경 핸들러
   */
  const handleSortChange = useCallback((sortOrder: SortOrder) => {
    updateSort(sortOrder);
    setSortMenuAnchor(null);
  }, [updateSort]);

  /**
   * 아이템 클릭 핸들러
   */
  const handleItemClick = useCallback((item: SearchResult) => {
    // 상세 페이지로 이동 또는 모달 오픈
    console.log('Item clicked:', item);
    // TODO: Navigate to detail page or open modal
  }, []);

  /**
   * 결과 내보내기
   */
  const handleExport = useCallback(() => {
    // CSV 또는 Excel로 내보내기
    console.log('Export results');
    // TODO: Implement export functionality
  }, []);

  /**
   * 초기 로딩 시 인기 검색어 표시
   */
  const renderWelcomeContent = () => (
    <Grow in={!params.query}>
      <Box sx={{ textAlign: 'center', py: 8 }}>
        <SearchIcon sx={{ fontSize: 80, color: 'text.secondary', mb: 2 }} />
        <Typography variant="h5" gutterBottom color="text.secondary">
          검색어를 입력하세요
        </Typography>

        {recentSearches.length > 0 && (
          <Box sx={{ mt: 4 }}>
            <Typography variant="subtitle2" color="text.secondary" gutterBottom>
              최근 검색어
            </Typography>
            <Stack
              direction="row"
              spacing={1}
              justifyContent="center"
              flexWrap="wrap"
              sx={{ mt: 2, gap: 1 }}
            >
              {recentSearches.slice(0, 5).map((term, index) => (
                <Chip
                  key={index}
                  label={term}
                  onClick={() => handleSearch(term)}
                  variant="outlined"
                  clickable
                />
              ))}
            </Stack>
          </Box>
        )}

        <Box sx={{ mt: 4 }}>
          <Typography variant="subtitle2" color="text.secondary" gutterBottom>
            인기 검색어
          </Typography>
          <Stack
            direction="row"
            spacing={1}
            justifyContent="center"
            flexWrap="wrap"
            sx={{ mt: 2, gap: 1 }}
          >
            {['건설', '소프트웨어', 'SI사업', '장비구매', '용역'].map((term, index) => (
              <Chip
                key={index}
                label={term}
                icon={<TrendingIcon />}
                onClick={() => handleSearch(term)}
                color="primary"
                variant="outlined"
                clickable
              />
            ))}
          </Stack>
        </Box>
      </Box>
    </Grow>
  );

  return (
    <PageContainer maxWidth="xl">
      {/* 헤더 */}
      <HeaderSection>
        <Typography variant="h3" component="h1" gutterBottom fontWeight="bold">
          통합 검색
        </Typography>
        <Typography variant="subtitle1" color="text.secondary">
          입찰공고, 문서, 기업정보를 한 번에 검색하세요
        </Typography>
      </HeaderSection>

      {/* 검색바 섹션 */}
      <SearchSection elevation={2}>
        <Grid container spacing={2} alignItems="center">
          <Grid item xs={12} md={9}>
            <SearchBar
              onSearch={handleSearch}
              initialQuery={params.query}
              placeholder="검색어를 입력하세요 (예: 건설, 소프트웨어, SI사업)"
            />
          </Grid>
          <Grid item xs={12} md={3}>
            <Stack direction="row" spacing={1} justifyContent={isTablet ? 'center' : 'flex-end'}>
              <Tooltip title="필터">
                <IconButton
                  onClick={() => setShowFilters(!showFilters)}
                  color={Object.keys(params.filters || {}).length > 0 ? 'primary' : 'default'}
                >
                  <Badge badgeContent={Object.keys(params.filters || {}).length} color="primary">
                    <FilterIcon />
                  </Badge>
                </IconButton>
              </Tooltip>
              <Tooltip title="새로고침">
                <IconButton onClick={() => refetch()} disabled={isLoading}>
                  <RefreshIcon />
                </IconButton>
              </Tooltip>
              {!isMobile && (
                <Tooltip title="결과 내보내기">
                  <IconButton onClick={handleExport} disabled={results.length === 0}>
                    <DownloadIcon />
                  </IconButton>
                </Tooltip>
              )}
              <Tooltip title="도움말">
                <IconButton onClick={() => setShowHelp(!showHelp)}>
                  <HelpIcon />
                </IconButton>
              </Tooltip>
            </Stack>
          </Grid>
        </Grid>

        {/* 도움말 */}
        {showHelp && (
          <Fade in={showHelp}>
            <Alert severity="info" sx={{ mt: 2 }} onClose={() => setShowHelp(false)}>
              <AlertTitle>검색 도움말</AlertTitle>
              <Typography variant="body2">
                • 띄어쓰기로 여러 단어 검색 (예: 소프트웨어 개발)<br />
                • 따옴표로 정확한 구문 검색 (예: "시스템 구축")<br />
                • 필터를 사용하여 검색 결과 세분화<br />
                • 정렬 옵션으로 원하는 순서로 정렬
              </Typography>
            </Alert>
          </Fade>
        )}
      </SearchSection>

      {/* 검색 결과가 없을 때 */}
      {!params.query && renderWelcomeContent()}

      {/* 검색 결과가 있을 때 */}
      {params.query && (
        <>
          {/* 검색 타입 탭 */}
          <StyledTabs
            value={params.type}
            onChange={handleTypeChange}
            variant={isMobile ? 'scrollable' : 'standard'}
            scrollButtons="auto"
          >
            <Tab
              label={`전체 ${totalCount > 0 ? `(${totalCount})` : ''}`}
              value={SearchType.ALL}
            />
            <Tab
              label={`입찰공고 ${typeCounts.bid > 0 ? `(${typeCounts.bid})` : ''}`}
              value={SearchType.BID}
            />
            <Tab
              label={`문서 ${typeCounts.document > 0 ? `(${typeCounts.document})` : ''}`}
              value={SearchType.DOCUMENT}
            />
            <Tab
              label={`기업 ${typeCounts.company > 0 ? `(${typeCounts.company})` : ''}`}
              value={SearchType.COMPANY}
            />
          </StyledTabs>

          {/* 결과 헤더 */}
          <Box sx={{ mb: 2, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <Typography variant="body2" color="text.secondary">
              {isLoading ? (
                '검색 중...'
              ) : (
                <>
                  "<strong>{params.query}</strong>"에 대한 검색 결과 {totalCount.toLocaleString()}개
                </>
              )}
            </Typography>

            <Stack direction="row" spacing={1} alignItems="center">
              {/* 정렬 */}
              <SortButton
                startIcon={<SortIcon />}
                onClick={(e) => setSortMenuAnchor(e.currentTarget)}
                size="small"
              >
                {SORT_OPTIONS.find(opt => opt.value === params.sort)?.label}
              </SortButton>

              {/* 보기 모드 */}
              {!isMobile && (
                <Stack direction="row" spacing={0}>
                  <Tooltip title="리스트 보기">
                    <IconButton
                      size="small"
                      onClick={() => setViewMode('list')}
                      color={viewMode === 'list' ? 'primary' : 'default'}
                    >
                      <ViewListIcon />
                    </IconButton>
                  </Tooltip>
                  <Tooltip title="그리드 보기">
                    <IconButton
                      size="small"
                      onClick={() => setViewMode('grid')}
                      color={viewMode === 'grid' ? 'primary' : 'default'}
                    >
                      <ViewModuleIcon />
                    </IconButton>
                  </Tooltip>
                </Stack>
              )}
            </Stack>
          </Box>

          {/* 메인 컨텐츠 */}
          <ContentSection>
            {/* 필터 섹션 */}
            {showFilters && (
              <FilterSection>
                <SearchFilters
                  filters={params.filters || {}}
                  onFilterChange={handleFilterChange}
                  facets={facetsQuery.data || facets}
                />
              </FilterSection>
            )}

            {/* 결과 섹션 */}
            <ResultSection>
              {isError ? (
                <Alert severity="error">
                  <AlertTitle>검색 오류</AlertTitle>
                  검색 중 오류가 발생했습니다. 다시 시도해주세요.
                </Alert>
              ) : (
                <>
                  <SearchResults
                    results={results}
                    loading={isLoading}
                    error={error?.message}
                    onItemClick={handleItemClick}
                  />

                  {/* 페이지네이션 */}
                  {totalCount > 0 && (
                    <Box sx={{ mt: 3 }}>
                      <SearchPagination
                        currentPage={pageInfo.currentPage}
                        totalPages={pageInfo.totalPages}
                        pageSize={pageInfo.pageSize}
                        totalItems={pageInfo.totalItems}
                        onPageChange={updatePage}
                        onPageSizeChange={updatePageSize}
                        loading={isLoading}
                        viewMode={viewMode}
                        onViewModeChange={setViewMode}
                      />
                    </Box>
                  )}
                </>
              )}
            </ResultSection>
          </ContentSection>
        </>
      )}

      {/* 정렬 메뉴 (Popover로 구현 가능) */}
      {sortMenuAnchor && (
        <Paper
          sx={{
            position: 'absolute',
            top: sortMenuAnchor.getBoundingClientRect().bottom + 5,
            left: sortMenuAnchor.getBoundingClientRect().left,
            p: 1,
            zIndex: 1000
          }}
          elevation={3}
        >
          {SORT_OPTIONS.map(option => (
            <Box
              key={option.value}
              onClick={() => handleSortChange(option.value)}
              sx={{
                px: 2,
                py: 1,
                cursor: 'pointer',
                '&:hover': { bgcolor: 'action.hover' },
                fontWeight: params.sort === option.value ? 600 : 400,
                color: params.sort === option.value ? 'primary.main' : 'text.primary'
              }}
            >
              {option.label}
            </Box>
          ))}
        </Paper>
      )}
    </PageContainer>
  );
};

export default Search;