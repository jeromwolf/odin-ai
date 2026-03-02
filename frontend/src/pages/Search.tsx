import React, { useEffect, useState } from 'react';
import {
  Box,
  Container,
  TextField,
  Button,
  Typography,
  Card,
  CardContent,
  Grid,
  Chip,
  Alert,
  InputAdornment,
  IconButton,
  MenuItem,
  Select,
  FormControl,
  Divider,
  Paper,
  Collapse,
  Pagination as MuiPagination,
  ToggleButtonGroup,
  ToggleButton,
} from '@mui/material';
import {
  Search as SearchIcon,
  Bookmark,
  BookmarkBorder,
  Business,
  LocationOn,
  AccessTime,
  SearchOff,
  TrendingUp,
  Sort,
  FilterList,
  ExpandMore,
  ExpandLess,
  AutoAwesome as AutoAwesomeIcon,
  EmojiEvents,
} from '@mui/icons-material';
import { useLocation, useNavigate } from 'react-router-dom';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import apiClient from '../services/api';
import { FullscreenLoading } from '../components/common';
import { formatKRW, formatKRDate } from '../utils/formatters';

interface SearchResult {
  bid_notice_no: string;
  title: string;
  organization_name: string;
  department_name?: string;
  estimated_price?: number;
  bid_start_date?: string;
  bid_end_date?: string;
  status?: string;
  bid_method?: string;
  contract_method?: string;
  region_restriction?: string;
  remaining_days?: number;
  award_status?: string;
  winning_company?: string;
  winning_price?: number;
  winning_rate?: number;
  participant_count?: number;
  tags?: string[];
  is_bookmarked?: boolean;
  extracted_info?: {
    requirements?: { [key: string]: string };
    contract_details?: { [key: string]: string };
    prices?: { [key: string]: string };
  };
}

/** Returns left-border color and status chip props based on bid status */
const getStatusMeta = (status?: string, remaining_days?: number) => {
  if (status === 'active') {
    if (remaining_days != null && remaining_days <= 3 && remaining_days >= 0) {
      return {
        borderColor: '#FF6B35',
        chipLabel: '마감임박',
        chipColor: 'warning' as const,
      };
    }
    return {
      borderColor: '#1976D2',
      chipLabel: '진행중',
      chipColor: 'success' as const,
    };
  }
  return {
    borderColor: '#BDBDBD',
    chipLabel: '마감',
    chipColor: 'default' as const,
  };
};

const getSortedResults = (data: SearchResult[], sort: string): SearchResult[] => {
  const sorted = [...data];
  switch (sort) {
    case 'date_desc':
      return sorted.sort((a, b) => (b.bid_end_date || '').localeCompare(a.bid_end_date || ''));
    case 'price_desc':
      return sorted.sort((a, b) => (b.estimated_price || 0) - (a.estimated_price || 0));
    case 'price_asc':
      return sorted.sort((a, b) => (a.estimated_price || 0) - (b.estimated_price || 0));
    case 'deadline':
      return sorted.sort((a, b) => (a.remaining_days ?? 999) - (b.remaining_days ?? 999));
    default: // 'relevance' - keep API order
      return sorted;
  }
};

const POPULAR_TAGS = ['데이터분석', '데이터통계', 'AI', '빅데이터', '건설', '물품', '토목', '소프트웨어', '용역', '시스템개발'];

const SORT_OPTIONS = [
  { value: 'relevance', label: '관련도순' },
  { value: 'date_desc', label: '최신순' },
  { value: 'price_desc', label: '금액 높은순' },
  { value: 'price_asc', label: '금액 낮은순' },
  { value: 'deadline', label: '마감임박순' },
];

const ITEMS_PER_PAGE = 20;

const Search: React.FC = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [searchQuery, setSearchQuery] = useState('');
  const [results, setResults] = useState<SearchResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [totalResults, setTotalResults] = useState(0);
  const [totalPages, setTotalPages] = useState(0);
  const [page, setPage] = useState(1);
  const [bookmarkedBids, setBookmarkedBids] = useState<Set<string>>(new Set());
  const [sortBy, setSortBy] = useState('relevance');

  // Search mode state
  const [searchMode, setSearchMode] = useState<'keyword' | 'semantic'>('keyword');
  const [ragResults, setRagResults] = useState<any[]>([]);
  const [ragSearchMode, setRagSearchMode] = useState<string>('');

  // Filter state
  const [showFilters, setShowFilters] = useState(false);
  const [statusFilter, setStatusFilter] = useState('all');
  const [minPrice, setMinPrice] = useState<number | ''>('');
  const [maxPrice, setMaxPrice] = useState<number | ''>('');

  // 북마크 데이터 가져오기
  const { data: bookmarks } = useQuery({
    queryKey: ['bookmarks'],
    queryFn: () => apiClient.getBookmarks(),
    staleTime: 10000,
  });

  // 북마크 데이터가 로드되면 로컬 상태 동기화
  useEffect(() => {
    if (bookmarks && Array.isArray(bookmarks)) {
      const bookmarkSet = new Set(
        bookmarks.map((bookmark: any) => bookmark.bid_notice_no)
      );
      setBookmarkedBids(bookmarkSet);
    }
  }, [bookmarks]);

  // URL 파라미터에서 검색어 가져오기
  useEffect(() => {
    const params = new URLSearchParams(location.search);
    const query = params.get('q');
    if (query) {
      setSearchQuery(query);
      handleSearch(query, 1);
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [location.search]);

  const handleBookmarkToggle = async (result: SearchResult, e: React.MouseEvent) => {
    e.stopPropagation(); // 카드 클릭 이벤트 방지

    const bidId = result.bid_notice_no;
    const isCurrentlyBookmarked = bookmarkedBids.has(bidId);

    try {
      if (isCurrentlyBookmarked) {
        await apiClient.removeBookmark(bidId);
        setBookmarkedBids(prev => {
          const newSet = new Set(prev);
          newSet.delete(bidId);
          return newSet;
        });
        // 검색 결과에서도 북마크 상태 업데이트
        setResults(prev => prev.map(r =>
          r.bid_notice_no === bidId ? { ...r, is_bookmarked: false } : r
        ));
      } else {
        await apiClient.addBookmark(bidId);
        setBookmarkedBids(prev => new Set(prev).add(bidId));
        // 검색 결과에서도 북마크 상태 업데이트
        setResults(prev => prev.map(r =>
          r.bid_notice_no === bidId ? { ...r, is_bookmarked: true } : r
        ));
      }

      // React Query 캐시 무효화
      queryClient.invalidateQueries({ queryKey: ['bookmarks'] });
    } catch (error) {
      console.error('북마크 처리 실패:', error);
    }
  };

  const handleSearch = async (query?: string, pageNum?: number) => {
    const searchTerm = query || searchQuery;
    if (!searchTerm.trim()) return;

    setLoading(true);
    setError(null);

    try {
      if (searchMode === 'semantic') {
        const response = await apiClient.ragSearchBids(searchTerm, 20);
        if (response.success) {
          setRagResults(response.results || []);
          setRagSearchMode(response.search_mode || '');
        } else {
          setRagResults([]);
          setRagSearchMode('');
        }
        return;
      }

      const currentPage = pageNum !== undefined ? pageNum : page;
      const response = await apiClient.searchBids(searchTerm, {
        page: currentPage,
        limit: ITEMS_PER_PAGE,
        status: statusFilter !== 'all' ? statusFilter : undefined,
        min_price: minPrice ? Number(minPrice) * 10000 : undefined,
        max_price: maxPrice ? Number(maxPrice) * 10000 : undefined,
      });
      if (response.success) {
        // 검색 결과에 북마크 상태 추가
        const resultsWithBookmarks = (response.data || []).map((result: SearchResult) => ({
          ...result,
          is_bookmarked: bookmarkedBids.has(result.bid_notice_no)
        }));
        setResults(resultsWithBookmarks);
        setTotalResults(response.total || 0);
        setTotalPages(response.total_pages || 0);
      } else {
        setResults([]);
        setTotalResults(0);
        setTotalPages(0);
      }
    } catch (err: any) {
      console.error('검색 실패:', err);
      setError(err.message || '검색 중 오류가 발생했습니다.');
      setResults([]);
      setTotalResults(0);
      setTotalPages(0);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (searchQuery.trim()) {
      setPage(1);
      navigate(`/search?q=${encodeURIComponent(searchQuery)}`);
      handleSearch(undefined, 1);
    }
  };

  const handlePageChange = (_event: React.ChangeEvent<unknown>, value: number) => {
    setPage(value);
    handleSearch(undefined, value);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const hasSearched = !!searchQuery && !loading;

  const displayedResults = getSortedResults(results, sortBy);

  return (
    <Container maxWidth="lg">
      <Box sx={{ py: 4 }}>

        {/* ─── Page header ─── */}
        <Box sx={{ mb: 4 }}>
          <Typography
            variant="h4"
            sx={{
              fontWeight: 700,
              color: 'text.primary',
              letterSpacing: '-0.5px',
              mb: 0.5,
            }}
          >
            입찰 검색
          </Typography>
          <Typography variant="body2" color="text.secondary">
            공공입찰 공고를 키워드로 빠르게 찾아보세요
          </Typography>
        </Box>

        {/* ─── Search bar ─── */}
        <Box
          component="form"
          onSubmit={handleSubmit}
          sx={{ mb: 3 }}
        >
          <Box
            sx={{
              display: 'flex',
              gap: 1.5,
              alignItems: 'center',
              p: '6px 6px 6px 0',
              borderRadius: 3,
              boxShadow: '0 2px 16px rgba(0,0,0,0.10)',
              border: '1.5px solid',
              borderColor: 'divider',
              bgcolor: 'background.paper',
              transition: 'box-shadow 0.2s, border-color 0.2s',
              '&:focus-within': {
                boxShadow: '0 4px 24px rgba(25,118,210,0.14)',
                borderColor: 'primary.main',
              },
            }}
          >
            <TextField
              fullWidth
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="검색어를 입력하세요 (예: 건설, 물품, 토목 등)"
              variant="standard"
              InputProps={{
                disableUnderline: true,
                startAdornment: (
                  <InputAdornment position="start" sx={{ pl: 2, pr: 0.5 }}>
                    <SearchIcon sx={{ color: 'text.disabled', fontSize: 22 }} />
                  </InputAdornment>
                ),
              }}
              sx={{
                '& .MuiInputBase-input': {
                  fontSize: '1rem',
                  py: 1.2,
                  '&::placeholder': { color: 'text.disabled', opacity: 1 },
                },
              }}
            />
            <Button
              type="submit"
              variant="contained"
              disabled={loading}
              sx={{
                borderRadius: 2.5,
                px: 3.5,
                py: 1.2,
                fontWeight: 700,
                fontSize: '0.95rem',
                whiteSpace: 'nowrap',
                flexShrink: 0,
                boxShadow: 'none',
                '&:hover': { boxShadow: '0 4px 12px rgba(25,118,210,0.3)' },
              }}
            >
              검색
            </Button>
          </Box>
        </Box>

        {/* ─── Search mode toggle ─── */}
        <Box sx={{ display: 'flex', justifyContent: 'center', my: 2 }}>
          <ToggleButtonGroup
            value={searchMode}
            exclusive
            onChange={(_, newMode) => {
              if (newMode) {
                setSearchMode(newMode);
                setRagResults([]);
              }
            }}
            size="small"
          >
            <ToggleButton value="keyword" sx={{ px: 3 }}>
              <SearchIcon sx={{ mr: 1 }} /> 키워드 검색
            </ToggleButton>
            <ToggleButton value="semantic" sx={{ px: 3 }}>
              <AutoAwesomeIcon sx={{ mr: 1 }} /> AI 의미검색
            </ToggleButton>
          </ToggleButtonGroup>
        </Box>

        {/* ─── Popular tags ─── */}
        <Box sx={{ mb: 3 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.75, mb: 1.25 }}>
            <TrendingUp sx={{ fontSize: 15, color: 'text.disabled' }} />
            <Typography variant="caption" color="text.disabled" sx={{ fontWeight: 600, letterSpacing: 0.5 }}>
              인기 태그
            </Typography>
          </Box>
          <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.75 }}>
            {POPULAR_TAGS.map((tag) => (
              <Chip
                key={tag}
                label={`#${tag}`}
                onClick={() => {
                  setPage(1);
                  setSearchQuery(tag);
                  handleSearch(tag, 1);
                  navigate(`/search?q=${encodeURIComponent(tag)}`);
                }}
                variant="outlined"
                size="small"
                sx={{
                  cursor: 'pointer',
                  borderRadius: 1.5,
                  fontWeight: 500,
                  fontSize: '0.8rem',
                  color: 'primary.main',
                  borderColor: 'primary.light',
                  bgcolor: 'transparent',
                  transition: 'all 0.15s',
                  '&:hover': {
                    backgroundColor: 'primary.main',
                    color: 'white',
                    borderColor: 'primary.main',
                    transform: 'translateY(-1px)',
                    boxShadow: '0 2px 8px rgba(25,118,210,0.25)',
                  },
                }}
              />
            ))}
          </Box>
        </Box>

        {/* ─── Collapsible filter panel ─── */}
        <Box sx={{ mb: 2 }}>
          <Button
            size="small"
            startIcon={<FilterList />}
            endIcon={showFilters ? <ExpandLess /> : <ExpandMore />}
            onClick={() => setShowFilters(!showFilters)}
            sx={{ mb: 1, color: 'text.secondary', textTransform: 'none' }}
          >
            상세 필터 {showFilters ? '접기' : '열기'}
          </Button>
          <Collapse in={showFilters}>
            <Paper variant="outlined" sx={{ p: 2, mb: 2, borderRadius: 2 }}>
              <Grid container spacing={2} alignItems="flex-end">
                {/* Status filter */}
                <Grid item xs={12} sm={3}>
                  <Typography variant="caption" color="text.secondary" sx={{ mb: 0.5, display: 'block' }}>
                    상태
                  </Typography>
                  <FormControl fullWidth size="small">
                    <Select
                      value={statusFilter}
                      onChange={(e) => setStatusFilter(e.target.value)}
                    >
                      <MenuItem value="all">전체</MenuItem>
                      <MenuItem value="active">진행중</MenuItem>
                      <MenuItem value="closed">마감</MenuItem>
                    </Select>
                  </FormControl>
                </Grid>
                {/* Min price */}
                <Grid item xs={6} sm={3}>
                  <Typography variant="caption" color="text.secondary" sx={{ mb: 0.5, display: 'block' }}>
                    최소 금액 (만원)
                  </Typography>
                  <TextField
                    size="small"
                    type="number"
                    fullWidth
                    value={minPrice}
                    onChange={(e) => setMinPrice(e.target.value ? Number(e.target.value) : '')}
                    placeholder="0"
                    inputProps={{ min: 0 }}
                  />
                </Grid>
                {/* Max price */}
                <Grid item xs={6} sm={3}>
                  <Typography variant="caption" color="text.secondary" sx={{ mb: 0.5, display: 'block' }}>
                    최대 금액 (만원)
                  </Typography>
                  <TextField
                    size="small"
                    type="number"
                    fullWidth
                    value={maxPrice}
                    onChange={(e) => setMaxPrice(e.target.value ? Number(e.target.value) : '')}
                    placeholder="무제한"
                    inputProps={{ min: 0 }}
                  />
                </Grid>
                {/* Apply button */}
                <Grid item xs={12} sm={3}>
                  <Button
                    variant="contained"
                    size="medium"
                    fullWidth
                    onClick={() => {
                      setPage(1);
                      handleSearch(undefined, 1);
                    }}
                  >
                    필터 적용
                  </Button>
                </Grid>
              </Grid>
            </Paper>
          </Collapse>
        </Box>

        {/* ─── Loading ─── */}
        {loading && <FullscreenLoading />}

        {/* ─── Error ─── */}
        {error && (
          <Alert severity="error" sx={{ mb: 2, borderRadius: 2 }}>
            {error}
          </Alert>
        )}

        {/* ─── Results header (count + sort) ─── */}
        {hasSearched && results.length > 0 && (
          <Box
            sx={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              mb: 2,
              pb: 1.5,
              borderBottom: '1px solid',
              borderColor: 'divider',
            }}
          >
            <Box>
              <Typography variant="body1" sx={{ fontWeight: 600, color: 'text.primary' }}>
                총&nbsp;
                <Box component="span" sx={{ color: 'primary.main' }}>
                  {totalResults.toLocaleString()}
                </Box>
                건의 검색 결과
              </Typography>
              <Typography variant="caption" color="text.secondary">
                "{searchQuery}" 에 대한 결과입니다
              </Typography>
            </Box>

            <FormControl size="small" sx={{ minWidth: 130 }}>
              <Select
                value={sortBy}
                onChange={(e) => setSortBy(e.target.value)}
                startAdornment={
                  <Sort sx={{ fontSize: 16, mr: 0.5, color: 'text.secondary' }} />
                }
                sx={{
                  borderRadius: 2,
                  fontSize: '0.85rem',
                  '& .MuiOutlinedInput-notchedOutline': { borderColor: 'divider' },
                }}
              >
                {SORT_OPTIONS.map((opt) => (
                  <MenuItem key={opt.value} value={opt.value} sx={{ fontSize: '0.85rem' }}>
                    {opt.label}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Box>
        )}

        {/* ─── Result cards ─── */}
        {!loading && displayedResults.length > 0 && (
          <Grid container spacing={2}>
            {displayedResults.map((result) => {
              const { borderColor, chipLabel, chipColor } = getStatusMeta(
                result.status,
                result.remaining_days
              );
              const isBookmarked = bookmarkedBids.has(result.bid_notice_no);

              return (
                <Grid item xs={12} key={result.bid_notice_no}>
                  <Card
                    onClick={() => navigate(`/bids/${result.bid_notice_no}`)}
                    elevation={0}
                    sx={{
                      cursor: 'pointer',
                      borderRadius: 2.5,
                      border: '1px solid',
                      borderColor: 'divider',
                      borderLeft: `4px solid ${borderColor}`,
                      position: 'relative',
                      transition: 'box-shadow 0.2s, transform 0.15s',
                      '&:hover': {
                        boxShadow: '0 6px 24px rgba(0,0,0,0.10)',
                        transform: 'translateY(-2px)',
                        borderColor: 'primary.light',
                        '& .result-title': {
                          color: 'primary.main',
                        },
                      },
                    }}
                  >
                    <CardContent sx={{ p: 2.5, '&:last-child': { pb: 2.5 } }}>

                      {/* ── Top row: title + bookmark ── */}
                      <Box sx={{ display: 'flex', alignItems: 'flex-start', gap: 1, mb: 1.25 }}>
                        <Typography
                          className="result-title"
                          variant="subtitle1"
                          sx={{
                            fontWeight: 700,
                            flex: 1,
                            lineHeight: 1.45,
                            color: 'text.primary',
                            transition: 'color 0.15s',
                            display: '-webkit-box',
                            WebkitLineClamp: 2,
                            WebkitBoxOrient: 'vertical',
                            overflow: 'hidden',
                          }}
                        >
                          {result.title}
                        </Typography>
                        <IconButton
                          size="small"
                          onClick={(e) => handleBookmarkToggle(result, e)}
                          sx={{
                            flexShrink: 0,
                            mt: -0.25,
                            color: isBookmarked ? 'primary.main' : 'text.disabled',
                            '&:hover': {
                              color: 'primary.main',
                              bgcolor: 'primary.50',
                            },
                          }}
                        >
                          {isBookmarked ? (
                            <Bookmark sx={{ fontSize: 20 }} />
                          ) : (
                            <BookmarkBorder sx={{ fontSize: 20 }} />
                          )}
                        </IconButton>
                      </Box>

                      {/* ── Status chips row ── */}
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.75, mb: 1.5, flexWrap: 'wrap' }}>
                        <Chip
                          label={chipLabel}
                          color={chipColor}
                          size="small"
                          sx={{ fontWeight: 600, fontSize: '0.72rem', height: 22 }}
                        />
                        {result.remaining_days != null && result.remaining_days >= 0 && (
                          <Chip
                            label={`D-${result.remaining_days}`}
                            color={result.remaining_days <= 3 ? 'error' : 'primary'}
                            size="small"
                            variant="outlined"
                            sx={{ fontWeight: 700, fontSize: '0.72rem', height: 22 }}
                          />
                        )}
                        {result.bid_method && (
                          <Chip
                            label={result.bid_method}
                            size="small"
                            variant="outlined"
                            sx={{ fontSize: '0.72rem', height: 22, color: 'text.secondary', borderColor: 'divider' }}
                          />
                        )}
                        {result.contract_method && (
                          <Chip
                            label={result.contract_method}
                            size="small"
                            variant="outlined"
                            sx={{ fontSize: '0.72rem', height: 22, color: 'text.secondary', borderColor: 'divider' }}
                          />
                        )}
                        {result.award_status === 'awarded' && (
                          <Chip
                            icon={<EmojiEvents sx={{ fontSize: '14px !important' }} />}
                            label={`낙찰 ${result.winning_company || ''}`}
                            size="small"
                            sx={{
                              fontWeight: 600,
                              fontSize: '0.72rem',
                              height: 22,
                              bgcolor: '#f0fdf4',
                              color: '#15803d',
                              borderColor: '#86efac',
                              border: '1px solid',
                              '& .MuiChip-icon': { color: '#f59e0b' },
                            }}
                          />
                        )}
                      </Box>

                      {/* ── Award summary (낙찰 완료 시) ── */}
                      {result.award_status === 'awarded' && result.winning_price && (
                        <Box
                          sx={{
                            display: 'flex',
                            alignItems: 'center',
                            gap: 2,
                            mb: 1.5,
                            px: 1.5,
                            py: 0.75,
                            bgcolor: '#f0fdf4',
                            borderRadius: 1.5,
                            border: '1px solid #dcfce7',
                          }}
                        >
                          <Typography variant="caption" sx={{ color: '#15803d', fontWeight: 600 }}>
                            낙찰금액 {formatKRW(result.winning_price)}
                          </Typography>
                          {result.winning_rate && (
                            <Typography variant="caption" sx={{ color: '#15803d' }}>
                              낙찰률 {result.winning_rate.toFixed(1)}%
                            </Typography>
                          )}
                          {result.participant_count && (
                            <Typography variant="caption" sx={{ color: '#6b7280' }}>
                              참여 {result.participant_count}개사
                            </Typography>
                          )}
                        </Box>
                      )}

                      {/* ── Meta row: org + region + price ── */}
                      <Box
                        sx={{
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'space-between',
                          flexWrap: 'wrap',
                          gap: 1,
                          mb: 1.5,
                        }}
                      >
                        {/* Left: organization + region */}
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, flexWrap: 'wrap' }}>
                          <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                            <Business sx={{ fontSize: 14, color: 'text.disabled' }} />
                            <Typography variant="body2" color="text.secondary" sx={{ fontWeight: 500 }}>
                              {result.organization_name}
                              {result.department_name && (
                                <Box component="span" sx={{ color: 'text.disabled', fontWeight: 400 }}>
                                  &nbsp;·&nbsp;{result.department_name}
                                </Box>
                              )}
                            </Typography>
                          </Box>
                          {result.region_restriction && (
                            <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                              <LocationOn sx={{ fontSize: 14, color: 'text.disabled' }} />
                              <Typography variant="body2" color="text.secondary">
                                {result.region_restriction}
                              </Typography>
                            </Box>
                          )}
                        </Box>

                        {/* Right: price */}
                        <Typography
                          variant="body1"
                          sx={{
                            fontWeight: 800,
                            color: result.estimated_price ? 'text.primary' : 'text.disabled',
                            fontSize: '1rem',
                            letterSpacing: '-0.3px',
                          }}
                        >
                          {formatKRW(result.estimated_price)}
                        </Typography>
                      </Box>

                      {/* ── Deadline row ── */}
                      {result.bid_end_date && (
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5, mb: 1.25 }}>
                          <AccessTime sx={{ fontSize: 13, color: 'text.disabled' }} />
                          <Typography variant="caption" color="text.secondary">
                            마감&nbsp;{formatKRDate(result.bid_end_date)}
                          </Typography>
                        </Box>
                      )}

                      {/* ── Divider + tags ── */}
                      {result.tags && result.tags.length > 0 && (
                        <>
                          <Divider sx={{ mb: 1.25 }} />
                          <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                            {result.tags.slice(0, 6).map((tag, index) => (
                              <Chip
                                key={index}
                                label={`#${tag}`}
                                size="small"
                                variant="outlined"
                                onClick={(e) => {
                                  e.stopPropagation();
                                  setPage(1);
                                  setSearchQuery(tag);
                                  handleSearch(tag, 1);
                                  navigate(`/search?q=${encodeURIComponent(tag)}`);
                                }}
                                sx={{
                                  fontSize: '0.72rem',
                                  height: 20,
                                  borderRadius: 1,
                                  color: 'text.secondary',
                                  borderColor: 'divider',
                                  bgcolor: 'action.hover',
                                  cursor: 'pointer',
                                  '&:hover': {
                                    borderColor: 'primary.light',
                                    color: 'primary.main',
                                    bgcolor: 'primary.50',
                                  },
                                }}
                              />
                            ))}
                          </Box>
                        </>
                      )}

                      {/* ── Extracted info (requirements / contract_details) ── */}
                      {result.extracted_info && (
                        <Box sx={{ mt: 1.5, p: 1.25, bgcolor: 'action.hover', borderRadius: 1.5 }}>
                          {result.extracted_info.requirements &&
                           Object.keys(result.extracted_info.requirements).length > 0 && (
                            <Typography variant="caption" display="block" sx={{ mb: 0.5, color: 'text.secondary' }}>
                              <Box component="span" sx={{ fontWeight: 700, color: 'text.primary' }}>
                                📋 주요 요구사항:
                              </Box>
                              {' ' + Object.values(result.extracted_info.requirements)[0].substring(0, 100)}...
                            </Typography>
                          )}
                          {result.extracted_info.contract_details &&
                           Object.keys(result.extracted_info.contract_details).length > 0 && (
                            <Typography variant="caption" display="block" sx={{ color: 'text.secondary' }}>
                              <Box component="span" sx={{ fontWeight: 700, color: 'text.primary' }}>
                                📝 계약 조건:
                              </Box>
                              {' ' + Object.values(result.extracted_info.contract_details)[0].substring(0, 100)}...
                            </Typography>
                          )}
                        </Box>
                      )}

                    </CardContent>
                  </Card>
                </Grid>
              );
            })}
          </Grid>
        )}

        {/* ─── RAG / semantic results ─── */}
        {!loading && searchMode === 'semantic' && ragResults.length > 0 && (
          <Box>
            <Box
              sx={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                mb: 2,
                pb: 1.5,
                borderBottom: '1px solid',
                borderColor: 'divider',
              }}
            >
              <Typography variant="body1" sx={{ fontWeight: 600, color: 'text.primary' }}>
                AI 의미검색 결과&nbsp;
                <Box component="span" sx={{ color: 'primary.main' }}>
                  {ragResults.length}
                </Box>
                건
                {ragSearchMode && (
                  <Box component="span" sx={{ color: 'text.secondary', fontWeight: 400, fontSize: '0.85rem', ml: 1 }}>
                    ({ragSearchMode === 'hybrid' ? '하이브리드 검색' : ragSearchMode === 'vector' ? '벡터 검색' : ragSearchMode === 'fts' ? '전문 검색' : ragSearchMode})
                  </Box>
                )}
              </Typography>
            </Box>
            <Grid container spacing={2}>
              {ragResults.map((item: any) => {
                const scoreColor = item.score >= 0.8 ? 'success' : item.score >= 0.5 ? 'warning' : 'default';
                const sectionTypeLabel: { [key: string]: string } = {
                  qualifications: '자격요건',
                  overview: '공사개요',
                  schedule: '일정',
                  price: '가격',
                  requirements: '요구사항',
                  general: '일반',
                };
                return (
                  <Grid item xs={12} key={item.chunk_id}>
                    <Paper
                      elevation={0}
                      sx={{
                        borderRadius: 2.5,
                        border: '1px solid',
                        borderColor: 'divider',
                        borderLeft: '4px solid',
                        borderLeftColor: 'primary.main',
                        p: 2.5,
                        cursor: 'pointer',
                        transition: 'box-shadow 0.2s, transform 0.15s',
                        '&:hover': {
                          boxShadow: '0 6px 24px rgba(0,0,0,0.10)',
                          transform: 'translateY(-2px)',
                        },
                      }}
                      onClick={() => navigate(`/bids/${item.bid_notice_no}`)}
                    >
                      {/* Score + match sources */}
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.75, mb: 1.25, flexWrap: 'wrap' }}>
                        <Chip
                          label={`유사도 ${Math.round(item.score * 100)}%`}
                          color={scoreColor}
                          size="small"
                          sx={{ fontWeight: 700, fontSize: '0.72rem', height: 22 }}
                        />
                        {item.section_type && (
                          <Chip
                            label={sectionTypeLabel[item.section_type] || item.section_type}
                            size="small"
                            variant="outlined"
                            sx={{ fontSize: '0.72rem', height: 22, color: 'text.secondary', borderColor: 'divider' }}
                          />
                        )}
                        {Array.isArray(item.match_sources) && item.match_sources.map((src: string) => (
                          <Chip
                            key={src}
                            label={src === 'vector' ? '벡터' : src === 'fts' ? '전문검색' : src}
                            size="small"
                            variant="outlined"
                            sx={{ fontSize: '0.68rem', height: 20, color: 'primary.main', borderColor: 'primary.light' }}
                          />
                        ))}
                      </Box>

                      {/* Title */}
                      <Typography
                        variant="h6"
                        sx={{
                          fontWeight: 700,
                          fontSize: '1rem',
                          lineHeight: 1.4,
                          color: 'text.primary',
                          mb: 0.75,
                          '&:hover': { color: 'primary.main' },
                        }}
                      >
                        {item.bid_title}
                      </Typography>

                      {/* Org + price */}
                      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 1.25, flexWrap: 'wrap', gap: 1 }}>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                          <Business sx={{ fontSize: 14, color: 'text.disabled' }} />
                          <Typography variant="body2" color="text.secondary" sx={{ fontWeight: 500 }}>
                            {item.organization_name}
                          </Typography>
                        </Box>
                        {item.estimated_price && (
                          <Typography variant="body1" sx={{ fontWeight: 800, fontSize: '1rem', letterSpacing: '-0.3px' }}>
                            {formatKRW(item.estimated_price)}
                          </Typography>
                        )}
                      </Box>

                      {/* Chunk text excerpt */}
                      <Typography
                        variant="body2"
                        color="text.secondary"
                        sx={{
                          display: '-webkit-box',
                          WebkitLineClamp: 3,
                          WebkitBoxOrient: 'vertical',
                          overflow: 'hidden',
                          lineHeight: 1.6,
                          fontSize: '0.85rem',
                        }}
                      >
                        {item.chunk_text}
                      </Typography>
                    </Paper>
                  </Grid>
                );
              })}
            </Grid>
          </Box>
        )}

        {/* ─── Pagination + range info ─── */}
        {!loading && results.length > 0 && totalPages > 0 && (
          <Box
            sx={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              mt: 4,
              mb: 2,
              flexWrap: 'wrap',
              gap: 2,
            }}
          >
            <Typography variant="body2" color="text.secondary">
              {totalResults.toLocaleString()}건 중{' '}
              {((page - 1) * ITEMS_PER_PAGE + 1).toLocaleString()}~
              {Math.min(page * ITEMS_PER_PAGE, totalResults).toLocaleString()}건
            </Typography>
            {totalPages > 1 && (
              <MuiPagination
                count={totalPages}
                page={page}
                onChange={handlePageChange}
                color="primary"
                size="large"
                showFirstButton
                showLastButton
              />
            )}
          </Box>
        )}

        {/* ─── Empty state ─── */}
        {hasSearched && results.length === 0 && (
          <Box
            sx={{
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              justifyContent: 'center',
              py: 10,
              gap: 2,
            }}
          >
            <Box
              sx={{
                width: 80,
                height: 80,
                borderRadius: '50%',
                bgcolor: 'action.hover',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}
            >
              <SearchOff sx={{ fontSize: 38, color: 'text.disabled' }} />
            </Box>
            <Box sx={{ textAlign: 'center' }}>
              <Typography variant="h6" sx={{ fontWeight: 700, color: 'text.primary', mb: 0.5 }}>
                검색 결과가 없습니다
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                "<strong>{searchQuery}</strong>"에 해당하는 공고를 찾을 수 없어요.
              </Typography>
              <Typography variant="caption" color="text.disabled" display="block">
                다른 키워드로 검색하거나 인기 태그를 활용해보세요.
              </Typography>
            </Box>
            <Box sx={{ display: 'flex', gap: 0.75, flexWrap: 'wrap', justifyContent: 'center', mt: 1 }}>
              {POPULAR_TAGS.slice(0, 5).map((tag) => (
                <Chip
                  key={tag}
                  label={`#${tag}`}
                  size="small"
                  onClick={() => {
                    setPage(1);
                    setSearchQuery(tag);
                    handleSearch(tag, 1);
                    navigate(`/search?q=${encodeURIComponent(tag)}`);
                  }}
                  sx={{
                    cursor: 'pointer',
                    borderRadius: 1.5,
                    fontSize: '0.78rem',
                    color: 'primary.main',
                    borderColor: 'primary.light',
                    border: '1px solid',
                    '&:hover': {
                      bgcolor: 'primary.main',
                      color: 'white',
                    },
                  }}
                />
              ))}
            </Box>
          </Box>
        )}

      </Box>
    </Container>
  );
};

export default Search;
