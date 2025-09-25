import React, { useState, useEffect } from 'react';
import {
  Container,
  Grid,
  Paper,
  Typography,
  Box,
  Chip,
  Card,
  CardContent,
  CardActions,
  Button,
  IconButton,
  Tooltip,
  TextField,
  InputAdornment,
  ToggleButton,
  ToggleButtonGroup,
  Pagination,
  Skeleton,
  Alert,
  Menu,
  MenuItem,
  Divider
} from '@mui/material';
import {
  Search as SearchIcon,
  FilterList as FilterListIcon,
  Sort as SortIcon,
  Delete as DeleteIcon,
  Edit as EditIcon,
  AccessTime as AccessTimeIcon,
  Business as BusinessIcon,
  AttachMoney as AttachMoneyIcon,
  ViewList as ViewListIcon,
  ViewModule as ViewModuleIcon,
  BookmarkBorder as BookmarkBorderIcon,
  Schedule as ScheduleIcon,
  MoreVert as MoreVertIcon
} from '@mui/icons-material';
import { format } from 'date-fns';
import { ko } from 'date-fns/locale';
import { useSnackbar } from 'notistack';
import apiClient from '../services/apiClient';
import BookmarkButton from '../components/BookmarkButton';

interface Bookmark {
  id: number;
  user_id: number;
  bid_id: string;
  title: string;
  organization_name: string;
  estimated_price: number;
  bid_end_date: string;
  notes: string;
  tags: string[];
  created_at: string;
  is_expired: boolean;
}

const Bookmarks: React.FC = () => {
  const [bookmarks, setBookmarks] = useState<Bookmark[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid');
  const [sortBy, setSortBy] = useState('created_at');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc');
  const [filterExpired, setFilterExpired] = useState<boolean | null>(null);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [totalCount, setTotalCount] = useState(0);
  const [stats, setStats] = useState<any>(null);
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const [selectedBookmark, setSelectedBookmark] = useState<Bookmark | null>(null);

  const { enqueueSnackbar } = useSnackbar();

  useEffect(() => {
    loadBookmarks();
    loadStats();
  }, [page, sortBy, sortOrder, filterExpired]);

  const loadBookmarks = async () => {
    setLoading(true);
    try {
      const params: any = {
        page,
        size: 12,
        sort: sortBy,
        order: sortOrder
      };

      if (filterExpired !== null) {
        params.expired = filterExpired;
      }

      const response = await apiClient.get('/bookmarks/', { params });
      setBookmarks(response.data.data);
      setTotalCount(response.data.total);
      setTotalPages(response.data.total_pages);
    } catch (error) {
      console.error('북마크 로드 실패:', error);
      enqueueSnackbar('북마크를 불러올 수 없습니다', { variant: 'error' });
    } finally {
      setLoading(false);
    }
  };

  const loadStats = async () => {
    try {
      const response = await apiClient.get('/bookmarks/stats');
      setStats(response.data.stats);
    } catch (error) {
      console.error('통계 로드 실패:', error);
    }
  };

  const handleDelete = async (bookmark: Bookmark) => {
    try {
      await apiClient.delete(`/bookmarks/${bookmark.bid_id}`);
      enqueueSnackbar('북마크가 삭제되었습니다', { variant: 'success' });
      loadBookmarks();
      loadStats();
    } catch (error) {
      console.error('북마크 삭제 실패:', error);
      enqueueSnackbar('북마크 삭제 실패', { variant: 'error' });
    }
    handleCloseMenu();
  };

  const handleOpenMenu = (event: React.MouseEvent<HTMLElement>, bookmark: Bookmark) => {
    setAnchorEl(event.currentTarget);
    setSelectedBookmark(bookmark);
  };

  const handleCloseMenu = () => {
    setAnchorEl(null);
    setSelectedBookmark(null);
  };

  const formatPrice = (price: number) => {
    return `${(price / 100000000).toFixed(1)}억원`;
  };

  const getDaysRemaining = (endDate: string) => {
    const end = new Date(endDate);
    const now = new Date();
    const diff = Math.ceil((end.getTime() - now.getTime()) / (1000 * 60 * 60 * 24));
    return diff;
  };

  const renderBookmarkCard = (bookmark: Bookmark) => {
    const daysRemaining = getDaysRemaining(bookmark.bid_end_date);

    return (
      <Card
        key={bookmark.id}
        sx={{
          height: '100%',
          display: 'flex',
          flexDirection: 'column',
          opacity: bookmark.is_expired ? 0.6 : 1,
          position: 'relative'
        }}
      >
        {bookmark.is_expired && (
          <Box
            sx={{
              position: 'absolute',
              top: 10,
              right: 10,
              zIndex: 1
            }}
          >
            <Chip label="마감" color="error" size="small" />
          </Box>
        )}

        <CardContent sx={{ flexGrow: 1 }}>
          <Typography
            variant="h6"
            gutterBottom
            sx={{
              overflow: 'hidden',
              textOverflow: 'ellipsis',
              display: '-webkit-box',
              WebkitLineClamp: 2,
              WebkitBoxOrient: 'vertical'
            }}
          >
            {bookmark.title}
          </Typography>

          <Box sx={{ mt: 2, display: 'flex', flexDirection: 'column', gap: 1 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <BusinessIcon fontSize="small" color="action" />
              <Typography variant="body2" color="text.secondary">
                {bookmark.organization_name}
              </Typography>
            </Box>

            {bookmark.estimated_price && (
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <AttachMoneyIcon fontSize="small" color="action" />
                <Typography variant="body2" color="text.secondary">
                  {formatPrice(bookmark.estimated_price)}
                </Typography>
              </Box>
            )}

            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <ScheduleIcon fontSize="small" color="action" />
              <Typography variant="body2" color="text.secondary">
                {format(new Date(bookmark.bid_end_date), 'yyyy-MM-dd', { locale: ko })}
                {!bookmark.is_expired && (
                  <Chip
                    label={`D-${daysRemaining}`}
                    size="small"
                    color={daysRemaining <= 3 ? 'error' : daysRemaining <= 7 ? 'warning' : 'default'}
                    sx={{ ml: 1 }}
                  />
                )}
              </Typography>
            </Box>

            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <AccessTimeIcon fontSize="small" color="action" />
              <Typography variant="body2" color="text.secondary">
                {format(new Date(bookmark.created_at), 'yyyy-MM-dd HH:mm', { locale: ko })}
              </Typography>
            </Box>
          </Box>

          {bookmark.tags && bookmark.tags.length > 0 && (
            <Box sx={{ mt: 2, display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
              {bookmark.tags.map((tag, index) => (
                <Chip key={index} label={tag} size="small" variant="outlined" />
              ))}
            </Box>
          )}

          {bookmark.notes && (
            <Typography variant="body2" sx={{ mt: 2, fontStyle: 'italic' }}>
              {bookmark.notes}
            </Typography>
          )}
        </CardContent>

        <CardActions sx={{ justifyContent: 'space-between', px: 2 }}>
          <Button
            size="small"
            href={`/bids/${bookmark.bid_id}`}
            target="_blank"
          >
            상세보기
          </Button>
          <Box>
            <BookmarkButton
              bidId={bookmark.bid_id}
              size="small"
              onToggle={() => {
                loadBookmarks();
                loadStats();
              }}
            />
            <IconButton
              size="small"
              onClick={(e) => handleOpenMenu(e, bookmark)}
            >
              <MoreVertIcon />
            </IconButton>
          </Box>
        </CardActions>
      </Card>
    );
  };

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      {/* 헤더 */}
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" gutterBottom>
          <BookmarkBorderIcon sx={{ mr: 1, verticalAlign: 'bottom' }} />
          내 북마크
        </Typography>
        <Typography variant="body1" color="text.secondary">
          관심있는 입찰 공고를 저장하고 관리하세요
        </Typography>
      </Box>

      {/* 통계 */}
      {stats && (
        <Grid container spacing={2} sx={{ mb: 4 }}>
          <Grid item xs={6} md={3}>
            <Paper sx={{ p: 2, textAlign: 'center' }}>
              <Typography variant="h4" color="primary">
                {stats.total}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                전체 북마크
              </Typography>
            </Paper>
          </Grid>
          <Grid item xs={6} md={3}>
            <Paper sx={{ p: 2, textAlign: 'center' }}>
              <Typography variant="h4" color="success.main">
                {stats.active}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                진행중
              </Typography>
            </Paper>
          </Grid>
          <Grid item xs={6} md={3}>
            <Paper sx={{ p: 2, textAlign: 'center' }}>
              <Typography variant="h4" color="error.main">
                {stats.expired}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                마감
              </Typography>
            </Paper>
          </Grid>
          <Grid item xs={6} md={3}>
            <Paper sx={{ p: 2, textAlign: 'center' }}>
              <Typography variant="h4" color="info.main">
                {stats.recent}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                최근 7일
              </Typography>
            </Paper>
          </Grid>
        </Grid>
      )}

      {/* 툴바 */}
      <Paper sx={{ p: 2, mb: 3 }}>
        <Box sx={{ display: 'flex', gap: 2, alignItems: 'center', flexWrap: 'wrap' }}>
          <TextField
            size="small"
            placeholder="북마크 검색..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            InputProps={{
              startAdornment: (
                <InputAdornment position="start">
                  <SearchIcon />
                </InputAdornment>
              )
            }}
            sx={{ flexGrow: 1, minWidth: 200 }}
          />

          <ToggleButtonGroup
            value={filterExpired}
            exclusive
            onChange={(e, value) => setFilterExpired(value)}
            size="small"
          >
            <ToggleButton value={null}>전체</ToggleButton>
            <ToggleButton value={false}>진행중</ToggleButton>
            <ToggleButton value={true}>마감</ToggleButton>
          </ToggleButtonGroup>

          <ToggleButtonGroup
            value={viewMode}
            exclusive
            onChange={(e, value) => value && setViewMode(value)}
            size="small"
          >
            <ToggleButton value="grid">
              <ViewModuleIcon />
            </ToggleButton>
            <ToggleButton value="list">
              <ViewListIcon />
            </ToggleButton>
          </ToggleButtonGroup>
        </Box>
      </Paper>

      {/* 북마크 목록 */}
      {loading ? (
        <Grid container spacing={3}>
          {[1, 2, 3, 4, 5, 6].map((i) => (
            <Grid item xs={12} sm={6} md={4} key={i}>
              <Skeleton variant="rectangular" height={300} />
            </Grid>
          ))}
        </Grid>
      ) : bookmarks.length === 0 ? (
        <Alert severity="info">
          북마크가 없습니다. 관심있는 입찰 공고를 북마크해보세요!
        </Alert>
      ) : (
        <>
          <Grid container spacing={3}>
            {bookmarks.map((bookmark) => (
              <Grid item xs={12} sm={6} md={viewMode === 'grid' ? 4 : 12} key={bookmark.id}>
                {renderBookmarkCard(bookmark)}
              </Grid>
            ))}
          </Grid>

          {totalPages > 1 && (
            <Box sx={{ mt: 4, display: 'flex', justifyContent: 'center' }}>
              <Pagination
                count={totalPages}
                page={page}
                onChange={(e, value) => setPage(value)}
                color="primary"
              />
            </Box>
          )}
        </>
      )}

      {/* 메뉴 */}
      <Menu
        anchorEl={anchorEl}
        open={Boolean(anchorEl)}
        onClose={handleCloseMenu}
      >
        <MenuItem onClick={() => selectedBookmark && handleDelete(selectedBookmark)}>
          <DeleteIcon fontSize="small" sx={{ mr: 1 }} />
          삭제
        </MenuItem>
      </Menu>
    </Container>
  );
};

export default Bookmarks;