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
} from '@mui/material';
import { Search as SearchIcon, Bookmark, BookmarkBorder } from '@mui/icons-material';
import { useLocation, useNavigate } from 'react-router-dom';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import apiClient from '../services/api';
import { FullscreenLoading, EmptyState } from '../components/common';
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
  tags?: string[];
  is_bookmarked?: boolean;
  extracted_info?: {
    requirements?: { [key: string]: string };
    contract_details?: { [key: string]: string };
    prices?: { [key: string]: string };
  };
}

const Search: React.FC = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [searchQuery, setSearchQuery] = useState('');
  const [results, setResults] = useState<SearchResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [totalResults, setTotalResults] = useState(0);
  const [bookmarkedBids, setBookmarkedBids] = useState<Set<string>>(new Set());

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
      handleSearch(query);
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

  const handleSearch = async (query?: string) => {
    const searchTerm = query || searchQuery;
    if (!searchTerm.trim()) return;

    setLoading(true);
    setError(null);

    try {
      const response = await apiClient.searchBids(searchTerm);
      if (response.success) {
        // 검색 결과에 북마크 상태 추가
        const resultsWithBookmarks = (response.data || []).map((result: SearchResult) => ({
          ...result,
          is_bookmarked: bookmarkedBids.has(result.bid_notice_no)
        }));
        setResults(resultsWithBookmarks);
        setTotalResults(response.total || 0);
      } else {
        setResults([]);
        setTotalResults(0);
      }
    } catch (err: any) {
      console.error('검색 실패:', err);
      setError(err.message || '검색 중 오류가 발생했습니다.');
      setResults([]);
      setTotalResults(0);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (searchQuery.trim()) {
      // URL 업데이트
      navigate(`/search?q=${encodeURIComponent(searchQuery)}`);
      handleSearch();
    }
  };

  return (
    <Container maxWidth="lg">
      <Box sx={{ py: 4 }}>
        <Typography variant="h4" gutterBottom>
          입찰 검색
        </Typography>

        {/* 검색 바 */}
        <Box component="form" onSubmit={handleSubmit} sx={{ mb: 3 }}>
          <TextField
            fullWidth
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="검색어를 입력하세요 (예: 건설, 물품, 토목 등)"
            variant="outlined"
            InputProps={{
              startAdornment: (
                <InputAdornment position="start">
                  <SearchIcon />
                </InputAdornment>
              ),
              endAdornment: (
                <Button
                  type="submit"
                  variant="contained"
                  disabled={loading}
                  sx={{ ml: 1 }}
                >
                  검색
                </Button>
              ),
            }}
          />
        </Box>

        {/* 인기 태그 */}
        <Box sx={{ mb: 4 }}>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
            인기 태그
          </Typography>
          <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
            {['건설', '물품', '토목', '전기', '소프트웨어', '용역', '긴급', '통신'].map((tag) => (
              <Chip
                key={tag}
                label={`#${tag}`}
                onClick={() => {
                  setSearchQuery(tag);
                  handleSearch(tag);
                  navigate(`/search?q=${encodeURIComponent(tag)}`);
                }}
                variant="outlined"
                color="primary"
                sx={{
                  cursor: 'pointer',
                  '&:hover': {
                    backgroundColor: 'primary.main',
                    color: 'white',
                    borderColor: 'primary.main',
                  },
                }}
              />
            ))}
          </Box>
        </Box>

        {/* 검색 결과 */}
        {loading && <FullscreenLoading />}

        {error && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {error}
          </Alert>
        )}

        {!loading && searchQuery && (
          <Typography variant="body1" sx={{ mb: 2 }}>
            "{searchQuery}" 검색 결과: {totalResults}건
          </Typography>
        )}

        {!loading && results.length > 0 && (
          <Grid container spacing={2}>
            {results.map((result) => (
              <Grid item xs={12} key={result.bid_notice_no}>
                <Card
                  sx={{
                    cursor: 'pointer',
                    '&:hover': {
                      backgroundColor: 'action.hover',
                      boxShadow: 3,
                    },
                    transition: 'all 0.3s',
                  }}
                  onClick={() => navigate(`/bids/${result.bid_notice_no}`)}
                >
                  <CardContent>
                    {/* 헤더 영역 */}
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2 }}>
                      <Box flex={1}>
                        <Typography variant="h6" component="div" sx={{ mb: 1 }}>
                          {result.title}
                        </Typography>
                        <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                          <Chip
                            label={result.status === 'active' ? '진행중' : '마감'}
                            color={result.status === 'active' ? 'success' : 'default'}
                            size="small"
                          />
                          {result.remaining_days !== undefined && result.remaining_days >= 0 && (
                            <Chip
                              label={`D-${result.remaining_days}`}
                              color={result.remaining_days <= 3 ? 'error' : 'primary'}
                              size="small"
                              variant="outlined"
                            />
                          )}
                          {result.bid_method && (
                            <Chip label={result.bid_method} size="small" variant="outlined" />
                          )}
                          {result.contract_method && (
                            <Chip label={result.contract_method} size="small" variant="outlined" />
                          )}
                        </Box>
                      </Box>
                      {/* 북마크 버튼 */}
                      <Box>
                        <IconButton
                          onClick={(e) => handleBookmarkToggle(result, e)}
                          color={result.is_bookmarked ? 'primary' : 'default'}
                          sx={{
                            '&:hover': {
                              backgroundColor: result.is_bookmarked ? 'primary.light' : 'action.hover',
                            },
                          }}
                        >
                          {result.is_bookmarked ? (
                            <Bookmark />
                          ) : (
                            <BookmarkBorder />
                          )}
                        </IconButton>
                      </Box>
                    </Box>

                    {/* 기관 정보 */}
                    <Typography variant="body2" color="text.secondary" gutterBottom>
                      <strong>발주기관:</strong> {result.organization_name}
                      {result.department_name && ` - ${result.department_name}`}
                    </Typography>

                    {/* 지역 제한 */}
                    {result.region_restriction && (
                      <Typography variant="body2" color="text.secondary" gutterBottom>
                        <strong>지역제한:</strong> {result.region_restriction}
                      </Typography>
                    )}

                    {/* 태그 */}
                    {result.tags && result.tags.length > 0 && (
                      <Box sx={{ mt: 1, mb: 1 }}>
                        {result.tags.slice(0, 5).map((tag, index) => (
                          <Chip
                            key={index}
                            label={`#${tag}`}
                            size="small"
                            sx={{ mr: 0.5, mb: 0.5 }}
                            color="info"
                            variant="outlined"
                          />
                        ))}
                      </Box>
                    )}

                    {/* 주요 정보 그리드 */}
                    <Grid container spacing={2} sx={{ mt: 1 }}>
                      <Grid item xs={12} md={6}>
                        <Typography variant="body2">
                          <strong>예정가격:</strong> {formatKRW(result.estimated_price)}
                        </Typography>
                      </Grid>
                      <Grid item xs={12} md={6}>
                        {result.bid_end_date && (
                          <Typography variant="body2">
                            <strong>마감일:</strong> {formatKRDate(result.bid_end_date)}
                          </Typography>
                        )}
                      </Grid>
                    </Grid>

                    {/* 추출된 정보 표시 */}
                    {result.extracted_info && (
                      <Box sx={{ mt: 2, p: 1, bgcolor: 'background.default', borderRadius: 1 }}>
                        {result.extracted_info.requirements &&
                         Object.keys(result.extracted_info.requirements).length > 0 && (
                          <Typography variant="caption" display="block" sx={{ mb: 0.5 }}>
                            <strong>📋 주요 요구사항:</strong>
                            {' ' + Object.values(result.extracted_info.requirements)[0].substring(0, 100)}...
                          </Typography>
                        )}

                        {result.extracted_info.contract_details &&
                         Object.keys(result.extracted_info.contract_details).length > 0 && (
                          <Typography variant="caption" display="block" sx={{ mb: 0.5 }}>
                            <strong>📝 계약 조건:</strong>
                            {' ' + Object.values(result.extracted_info.contract_details)[0].substring(0, 100)}...
                          </Typography>
                        )}
                      </Box>
                    )}
                  </CardContent>
                </Card>
              </Grid>
            ))}
          </Grid>
        )}

        {!loading && searchQuery && results.length === 0 && (
          <EmptyState
            title="검색 결과가 없습니다"
            description="다른 검색어를 시도해보세요"
          />
        )}
      </Box>
    </Container>
  );
};

export default Search;