import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Card,
  CardContent,
  Grid,
  IconButton,
  Chip,
  Button,
  TextField,
  InputAdornment,
  Menu,
  MenuItem,
  Divider,
  Alert,
  CircularProgress,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
  Tooltip,
  Paper,
} from '@mui/material';
import {
  Bookmark,
  BookmarkBorder,
  Search,
  FilterList,
  Sort,
  Delete,
  Share,
  Download,
  FolderOpen,
  Label,
  CalendarToday,
  Business,
  AttachMoney,
  MoreVert,
  CheckBox,
  CheckBoxOutlineBlank,
  DeleteForever,
} from '@mui/icons-material';
import apiClient from '../services/api';
import { useNavigate } from 'react-router-dom';

interface BookmarkItem {
  id: string;
  bid_notice_no: string;
  title: string;
  organization: string;
  bid_end_date: string;
  estimated_price: number;
  category: string;
  tags: string[];
  created_at: string;
  note?: string;
}

const Bookmarks: React.FC = () => {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [bookmarks, setBookmarks] = useState<BookmarkItem[]>([]);
  const [filteredBookmarks, setFilteredBookmarks] = useState<BookmarkItem[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [sortBy, setSortBy] = useState('recent');
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const [selectedBookmarks, setSelectedBookmarks] = useState<string[]>([]);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [noteDialogOpen, setNoteDialogOpen] = useState(false);
  const [selectedBookmark, setSelectedBookmark] = useState<BookmarkItem | null>(null);
  const [noteText, setNoteText] = useState('');

  // 카테고리 목록
  const categories = ['all', '건설', '소프트웨어', '토목', '전기', '통신', '용역', '물품', '기계'];

  useEffect(() => {
    loadBookmarks();
  }, []);

  useEffect(() => {
    filterAndSortBookmarks();
  }, [bookmarks, searchQuery, selectedCategory, sortBy]);

  const loadBookmarks = async () => {
    try {
      setLoading(true);
      const data = await apiClient.getBookmarks();
      if (data && Array.isArray(data)) {
        // 백엔드에서 받은 데이터를 프론트엔드 형식으로 변환
        const formattedBookmarks = data.map((item: any) => ({
          id: item.id || item.bid_notice_no,
          bid_notice_no: item.bid_notice_no,
          title: item.title || '제목 없음',
          organization: item.organization || item.org_name || '기관명 없음',
          bid_end_date: item.bid_end_date || item.bid_close_date,
          estimated_price: item.estimated_price || item.presume_price || 0,
          category: item.category || '기타',
          tags: item.tags || [],
          created_at: item.created_at || new Date().toISOString(),
          note: item.note || '',
        }));
        setBookmarks(formattedBookmarks);
      }
    } catch (error) {
      console.error('북마크 로드 실패:', error);
    } finally {
      setLoading(false);
    }
  };

  const filterAndSortBookmarks = () => {
    let filtered = [...bookmarks];

    // 검색 필터
    if (searchQuery) {
      filtered = filtered.filter(
        (item) =>
          item.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
          item.organization.toLowerCase().includes(searchQuery.toLowerCase()) ||
          item.tags.some(tag => tag.toLowerCase().includes(searchQuery.toLowerCase()))
      );
    }

    // 카테고리 필터
    if (selectedCategory !== 'all') {
      filtered = filtered.filter((item) => item.category === selectedCategory);
    }

    // 정렬
    switch (sortBy) {
      case 'recent':
        filtered.sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime());
        break;
      case 'deadline':
        filtered.sort((a, b) => new Date(a.bid_end_date).getTime() - new Date(b.bid_end_date).getTime());
        break;
      case 'price':
        filtered.sort((a, b) => b.estimated_price - a.estimated_price);
        break;
      case 'title':
        filtered.sort((a, b) => a.title.localeCompare(b.title));
        break;
    }

    setFilteredBookmarks(filtered);
  };

  const handleDeleteBookmark = async (bookmarkId: string) => {
    try {
      await apiClient.removeBookmark(bookmarkId);
      setBookmarks((prev) => prev.filter((item) => item.bid_notice_no !== bookmarkId));
      setSelectedBookmarks([]);
    } catch (error) {
      console.error('북마크 삭제 실패:', error);
      alert('북마크 삭제에 실패했습니다.');
    }
  };

  const handleDeleteSelected = async () => {
    try {
      for (const id of selectedBookmarks) {
        await apiClient.removeBookmark(id);
      }
      setBookmarks((prev) => prev.filter((item) => !selectedBookmarks.includes(item.bid_notice_no)));
      setSelectedBookmarks([]);
      setDeleteDialogOpen(false);
    } catch (error) {
      console.error('북마크 삭제 실패:', error);
      alert('북마크 삭제에 실패했습니다.');
    }
  };

  const handleToggleSelect = (bookmarkId: string) => {
    setSelectedBookmarks((prev) =>
      prev.includes(bookmarkId)
        ? prev.filter((id) => id !== bookmarkId)
        : [...prev, bookmarkId]
    );
  };

  const handleSelectAll = () => {
    if (selectedBookmarks.length === filteredBookmarks.length) {
      setSelectedBookmarks([]);
    } else {
      setSelectedBookmarks(filteredBookmarks.map((item) => item.bid_notice_no));
    }
  };

  const handleViewDetail = (bid_notice_no: string) => {
    navigate(`/bid/${bid_notice_no}`);
  };

  const handleAddNote = (bookmark: BookmarkItem) => {
    setSelectedBookmark(bookmark);
    setNoteText(bookmark.note || '');
    setNoteDialogOpen(true);
  };

  const handleSaveNote = async () => {
    if (selectedBookmark) {
      try {
        await apiClient.updateBookmarkNote(selectedBookmark.bid_notice_no, noteText);
        setBookmarks((prev) =>
          prev.map((item) =>
            item.id === selectedBookmark.id ? { ...item, note: noteText } : item
          )
        );
      } catch (error) {
        console.error('메모 저장 실패:', error);
      }
    }
    setNoteDialogOpen(false);
    setSelectedBookmark(null);
    setNoteText('');
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('ko-KR');
  };

  const formatPrice = (price: number) => {
    return new Intl.NumberFormat('ko-KR').format(price) + '원';
  };

  const getDaysRemaining = (endDate: string) => {
    const now = new Date();
    const end = new Date(endDate);
    const diff = Math.ceil((end.getTime() - now.getTime()) / (1000 * 60 * 60 * 24));

    if (diff < 0) return '마감';
    if (diff === 0) return '오늘 마감';
    if (diff === 1) return '1일 남음';
    return `${diff}일 남음`;
  };

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }}>
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" sx={{ display: 'flex', alignItems: 'center' }}>
          <Bookmark sx={{ mr: 1 }} />
          북마크
        </Typography>
        {selectedBookmarks.length > 0 && (
          <Box sx={{ display: 'flex', gap: 2 }}>
            <Button
              variant="outlined"
              color="error"
              startIcon={<Delete />}
              onClick={() => setDeleteDialogOpen(true)}
            >
              선택 삭제 ({selectedBookmarks.length})
            </Button>
          </Box>
        )}
      </Box>

      {/* 검색 및 필터 */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Grid container spacing={2} alignItems="center">
            <Grid item xs={12} md={5}>
              <TextField
                fullWidth
                placeholder="북마크 검색..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                InputProps={{
                  startAdornment: (
                    <InputAdornment position="start">
                      <Search />
                    </InputAdornment>
                  ),
                }}
              />
            </Grid>
            <Grid item xs={12} md={4}>
              <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                {categories.map((category) => (
                  <Chip
                    key={category}
                    label={category === 'all' ? '전체' : category}
                    onClick={() => setSelectedCategory(category)}
                    color={selectedCategory === category ? 'primary' : 'default'}
                    variant={selectedCategory === category ? 'filled' : 'outlined'}
                  />
                ))}
              </Box>
            </Grid>
            <Grid item xs={12} md={3}>
              <Button
                fullWidth
                variant="outlined"
                startIcon={<Sort />}
                onClick={(e) => setAnchorEl(e.currentTarget)}
              >
                정렬: {
                  sortBy === 'recent' ? '최신순' :
                  sortBy === 'deadline' ? '마감임박순' :
                  sortBy === 'price' ? '가격순' :
                  '제목순'
                }
              </Button>
              <Menu
                anchorEl={anchorEl}
                open={Boolean(anchorEl)}
                onClose={() => setAnchorEl(null)}
              >
                <MenuItem onClick={() => { setSortBy('recent'); setAnchorEl(null); }}>최신순</MenuItem>
                <MenuItem onClick={() => { setSortBy('deadline'); setAnchorEl(null); }}>마감임박순</MenuItem>
                <MenuItem onClick={() => { setSortBy('price'); setAnchorEl(null); }}>가격순</MenuItem>
                <MenuItem onClick={() => { setSortBy('title'); setAnchorEl(null); }}>제목순</MenuItem>
              </Menu>
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      {/* 북마크 통계 */}
      <Grid container spacing={2} sx={{ mb: 3 }}>
        <Grid item xs={12} md={3}>
          <Paper sx={{ p: 2, textAlign: 'center' }}>
            <Typography variant="h4" color="primary">
              {bookmarks.length}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              전체 북마크
            </Typography>
          </Paper>
        </Grid>
        <Grid item xs={12} md={3}>
          <Paper sx={{ p: 2, textAlign: 'center' }}>
            <Typography variant="h4" color="warning.main">
              {bookmarks.filter(b => {
                const days = Math.ceil((new Date(b.bid_end_date).getTime() - new Date().getTime()) / (1000 * 60 * 60 * 24));
                return days >= 0 && days <= 3;
              }).length}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              3일 이내 마감
            </Typography>
          </Paper>
        </Grid>
        <Grid item xs={12} md={3}>
          <Paper sx={{ p: 2, textAlign: 'center' }}>
            <Typography variant="h4" color="success.main">
              {bookmarks.filter(b => b.tags.length > 0).length}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              태그된 북마크
            </Typography>
          </Paper>
        </Grid>
        <Grid item xs={12} md={3}>
          <Paper sx={{ p: 2, textAlign: 'center' }}>
            <Typography variant="h4" color="info.main">
              {bookmarks.filter(b => b.note).length}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              메모 있음
            </Typography>
          </Paper>
        </Grid>
      </Grid>

      {/* 전체 선택 */}
      {filteredBookmarks.length > 0 && (
        <Box sx={{ mb: 2, display: 'flex', alignItems: 'center' }}>
          <IconButton onClick={handleSelectAll}>
            {selectedBookmarks.length === filteredBookmarks.length ? (
              <CheckBox color="primary" />
            ) : (
              <CheckBoxOutlineBlank />
            )}
          </IconButton>
          <Typography variant="body2" color="text.secondary">
            전체 선택 ({filteredBookmarks.length}개)
          </Typography>
        </Box>
      )}

      {/* 북마크 목록 */}
      {filteredBookmarks.length === 0 ? (
        <Alert severity="info">
          {searchQuery || selectedCategory !== 'all'
            ? '검색 결과가 없습니다.'
            : '저장된 북마크가 없습니다. 입찰 검색에서 관심 있는 공고를 북마크해보세요!'}
        </Alert>
      ) : (
        <Grid container spacing={2}>
          {filteredBookmarks.map((bookmark) => (
            <Grid item xs={12} key={bookmark.id}>
              <Card
                sx={{
                  position: 'relative',
                  '&:hover': { boxShadow: 3 },
                  border: selectedBookmarks.includes(bookmark.bid_notice_no) ? 2 : 1,
                  borderColor: selectedBookmarks.includes(bookmark.bid_notice_no) ? 'primary.main' : 'divider',
                }}
              >
                <CardContent>
                  <Box sx={{ display: 'flex', alignItems: 'flex-start' }}>
                    <IconButton
                      onClick={() => handleToggleSelect(bookmark.bid_notice_no)}
                      sx={{ mr: 2 }}
                    >
                      {selectedBookmarks.includes(bookmark.bid_notice_no) ? (
                        <CheckBox color="primary" />
                      ) : (
                        <CheckBoxOutlineBlank />
                      )}
                    </IconButton>

                    <Box sx={{ flexGrow: 1 }}>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 1 }}>
                        <Box>
                          <Typography
                            variant="h6"
                            sx={{
                              cursor: 'pointer',
                              '&:hover': { color: 'primary.main' },
                              mb: 0.5,
                            }}
                            onClick={() => handleViewDetail(bookmark.bid_notice_no)}
                          >
                            {bookmark.title}
                          </Typography>
                          <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap', mb: 1 }}>
                            <Chip label={bookmark.category} size="small" color="primary" />
                            {bookmark.tags.map((tag, index) => (
                              <Chip key={index} label={tag} size="small" variant="outlined" />
                            ))}
                            <Chip
                              label={getDaysRemaining(bookmark.bid_end_date)}
                              size="small"
                              color={
                                getDaysRemaining(bookmark.bid_end_date) === '마감' ? 'default' :
                                getDaysRemaining(bookmark.bid_end_date) === '오늘 마감' ? 'error' :
                                getDaysRemaining(bookmark.bid_end_date) === '1일 남음' ? 'warning' :
                                'success'
                              }
                            />
                          </Box>
                        </Box>
                        <Box sx={{ display: 'flex', gap: 1 }}>
                          <Tooltip title="메모 추가">
                            <IconButton size="small" onClick={() => handleAddNote(bookmark)}>
                              <Label />
                            </IconButton>
                          </Tooltip>
                          <Tooltip title="공유">
                            <IconButton size="small">
                              <Share />
                            </IconButton>
                          </Tooltip>
                          <Tooltip title="삭제">
                            <IconButton
                              size="small"
                              color="error"
                              onClick={() => handleDeleteBookmark(bookmark.bid_notice_no)}
                            >
                              <Delete />
                            </IconButton>
                          </Tooltip>
                        </Box>
                      </Box>

                      <Grid container spacing={2}>
                        <Grid item xs={12} md={3}>
                          <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                            <Business fontSize="small" color="action" />
                            <Typography variant="body2" color="text.secondary">
                              {bookmark.organization}
                            </Typography>
                          </Box>
                        </Grid>
                        <Grid item xs={12} md={3}>
                          <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                            <CalendarToday fontSize="small" color="action" />
                            <Typography variant="body2" color="text.secondary">
                              마감: {formatDate(bookmark.bid_end_date)}
                            </Typography>
                          </Box>
                        </Grid>
                        <Grid item xs={12} md={3}>
                          <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                            <AttachMoney fontSize="small" color="action" />
                            <Typography variant="body2" color="text.secondary">
                              예정가격: {formatPrice(bookmark.estimated_price)}
                            </Typography>
                          </Box>
                        </Grid>
                        <Grid item xs={12} md={3}>
                          <Typography variant="caption" color="text.secondary">
                            저장일: {formatDate(bookmark.created_at)}
                          </Typography>
                        </Grid>
                      </Grid>

                      {bookmark.note && (
                        <Alert severity="info" sx={{ mt: 2 }} icon={<Label />}>
                          {bookmark.note}
                        </Alert>
                      )}
                    </Box>
                  </Box>
                </CardContent>
              </Card>
            </Grid>
          ))}
        </Grid>
      )}

      {/* 삭제 확인 다이얼로그 */}
      <Dialog open={deleteDialogOpen} onClose={() => setDeleteDialogOpen(false)}>
        <DialogTitle>북마크 삭제</DialogTitle>
        <DialogContent>
          <Alert severity="warning">
            선택한 {selectedBookmarks.length}개의 북마크를 삭제하시겠습니까?
            <br />이 작업은 되돌릴 수 없습니다.
          </Alert>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDeleteDialogOpen(false)}>취소</Button>
          <Button onClick={handleDeleteSelected} color="error" variant="contained">
            삭제
          </Button>
        </DialogActions>
      </Dialog>

      {/* 메모 추가/수정 다이얼로그 */}
      <Dialog open={noteDialogOpen} onClose={() => setNoteDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>메모 {selectedBookmark?.note ? '수정' : '추가'}</DialogTitle>
        <DialogContent>
          {selectedBookmark && (
            <Box>
              <Typography variant="subtitle1" sx={{ mb: 2 }}>
                {selectedBookmark.title}
              </Typography>
              <TextField
                fullWidth
                multiline
                rows={4}
                value={noteText}
                onChange={(e) => setNoteText(e.target.value)}
                placeholder="이 입찰에 대한 메모를 작성하세요..."
                variant="outlined"
              />
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setNoteDialogOpen(false)}>취소</Button>
          <Button onClick={handleSaveNote} variant="contained">
            저장
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default Bookmarks;