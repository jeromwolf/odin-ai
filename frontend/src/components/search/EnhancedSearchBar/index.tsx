/**
 * EnhancedSearchBar 컴포넌트
 * 고급 자동완성 기능과 개선된 UX를 제공하는 검색바
 */

import React from 'react';
import {
  Box,
  Chip,
  Fade,
  Stack
} from '@mui/material';
import {
  Gavel as BidIcon,
  Description as DocumentIcon,
  Business as CompanyIcon,
  AutoAwesome as AiIcon,
  QueryStats as StatsIcon
} from '@mui/icons-material';
import { styled } from '@mui/material/styles';
import { EnhancedSearchBarProps } from './types';
import { useSearchBar } from './hooks/useSearchBar';
import SearchInput from './components/SearchInput';
import SearchSuggestions from './components/SearchSuggestions';

const SearchContainer = styled(Box)(() => ({
  position: 'relative',
  width: '100%',
  maxWidth: '800px',
  margin: '0 auto'
}));

const QuickAction = styled(Chip)(({ theme }) => ({
  margin: theme.spacing(0.5),
  fontWeight: 600,
  '&:hover': {
    backgroundColor: theme.palette.primary.main,
    color: theme.palette.primary.contrastText,
    transform: 'scale(1.05)'
  }
}));

const EnhancedSearchBar: React.FC<EnhancedSearchBarProps> = ({
  onSearch,
  initialQuery = '',
  placeholder = '무엇을 찾고 계신가요?',
  showSuggestions = true,
  showQuickActions = true,
  showSearchStats = true,
  enableAiSuggestions = false,
  onCategorySelect
}) => {
  const {
    query,
    suggestions,
    recentSearches,
    trendingSearches,
    loading,
    selectedIndex,
    anchorEl,
    searchStats,
    showDropdown,
    inputRef,
    containerRef,
    suggestionsRef,
    setQuery,
    setAnchorEl,
    handleSearch,
    handleKeyDown,
    removeRecentSearch,
    clearRecentSearches
  } = useSearchBar({
    onSearch,
    initialQuery,
    showSuggestions,
    showSearchStats,
    enableAiSuggestions
  });

  return (
    <SearchContainer ref={containerRef}>
      {/* 검색 통계 */}
      {showSearchStats && searchStats && (
        <Fade in>
          <Stack direction="row" spacing={2} justifyContent="center" sx={{ mb: 2 }}>
            <Chip
              icon={<StatsIcon />}
              label={`오늘 ${searchStats.recent.toLocaleString()}건`}
              size="small"
              color="primary"
              variant="outlined"
            />
            <Chip
              label={`전체 ${searchStats.total.toLocaleString()}건 검색 가능`}
              size="small"
              variant="outlined"
            />
          </Stack>
        </Fade>
      )}

      {/* 검색 입력 */}
      <SearchInput
        inputRef={inputRef}
        query={query}
        loading={loading}
        placeholder={placeholder}
        onQueryChange={(value) => {
          setQuery(value);
          if (!anchorEl && value) {
            // anchorEl will be set via onFocus below
          }
        }}
        onFocus={(e) => {
          setAnchorEl(e.currentTarget);
        }}
        onKeyDown={handleKeyDown}
        onClear={() => {
          setQuery('');
          inputRef.current?.focus();
        }}
        onSearch={() => handleSearch()}
      />

      {/* 빠른 액션 */}
      {showQuickActions && !query && (
        <Fade in>
          <Stack
            direction="row"
            spacing={1}
            justifyContent="center"
            flexWrap="wrap"
            sx={{ mt: 2, gap: 0.5 }}
          >
            <QuickAction
              icon={<BidIcon />}
              label="입찰공고"
              onClick={() => {
                onCategorySelect?.('bid');
                handleSearch('입찰공고');
              }}
              clickable
            />
            <QuickAction
              icon={<DocumentIcon />}
              label="문서검색"
              onClick={() => {
                onCategorySelect?.('document');
                handleSearch('문서');
              }}
              clickable
            />
            <QuickAction
              icon={<CompanyIcon />}
              label="기업정보"
              onClick={() => {
                onCategorySelect?.('company');
                handleSearch('기업');
              }}
              clickable
            />
            {enableAiSuggestions && (
              <QuickAction
                icon={<AiIcon />}
                label="AI 검색"
                color="secondary"
                onClick={() => {
                  // AI 검색 모드 활성화
                }}
                clickable
              />
            )}
          </Stack>
        </Fade>
      )}

      {/* 드롭다운 제안 */}
      <SearchSuggestions
        suggestionsRef={suggestionsRef}
        anchorEl={anchorEl}
        showDropdown={showDropdown}
        suggestions={suggestions}
        recentSearches={recentSearches}
        trendingSearches={trendingSearches}
        loading={loading}
        selectedIndex={selectedIndex}
        query={query}
        onSearch={handleSearch}
        onRemoveRecent={removeRecentSearch}
        onClearRecent={clearRecentSearches}
      />
    </SearchContainer>
  );
};

export default EnhancedSearchBar;
