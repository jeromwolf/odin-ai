import React, { useEffect, useState } from 'react';
import {
  Box,
  Typography,
  Paper,
  Grid,
  Divider,
  Chip,
  Button,
  CircularProgress,
  Alert,
  Card,
  CardContent,
  IconButton,
  Tooltip,
} from '@mui/material';
import {
  ArrowBack,
  Bookmark,
  BookmarkBorder,
  OpenInNew,
  CalendarToday,
  Business,
  AttachMoney,
  Person,
  Phone,
  Email,
} from '@mui/icons-material';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import apiClient from '../services/api';

interface BidDetailData {
  bid_notice_no: string;
  title: string;
  organization_name: string;
  department_name: string;
  estimated_price: number;
  bid_start_date: string;
  bid_end_date: string;
  announcement_date: string;
  bid_method: string;
  contract_method: string;
  officer_name: string;
  officer_phone: string;
  officer_email: string;
  detail_page_url: string;
  created_at: string;
  updated_at: string;
}

const BidDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [isBookmarked, setIsBookmarked] = useState(false);

  // 입찰 상세 정보 조회
  const { data, isLoading, error } = useQuery({
    queryKey: ['bidDetail', id],
    queryFn: async () => {
      if (!id) throw new Error('ID가 없습니다');
      const response = await apiClient.getBidDetail(id);
      return response.data as BidDetailData;
    },
    enabled: !!id,
  });

  // 북마크 상태 조회
  useEffect(() => {
    const checkBookmark = async () => {
      try {
        const response = await apiClient.getBookmarks();
        const bookmarks = response.data;
        const isInBookmarks = bookmarks.some(
          (bookmark: any) => bookmark.bid_notice_no === id
        );
        setIsBookmarked(isInBookmarks);
      } catch (error) {
        console.error('북마크 확인 실패:', error);
      }
    };
    if (id) {
      checkBookmark();
    }
  }, [id]);

  // 북마크 토글
  const handleBookmarkToggle = async () => {
    try {
      if (isBookmarked) {
        await apiClient.removeBookmark(id!);
        setIsBookmarked(false);
      } else {
        await apiClient.addBookmark(id!);
        setIsBookmarked(true);
      }
    } catch (error) {
      console.error('북마크 처리 실패:', error);
    }
  };

  // 날짜 포맷 함수
  const formatDate = (dateString: string | null) => {
    if (!dateString) return '-';
    const date = new Date(dateString);
    return date.toLocaleDateString('ko-KR', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  // 금액 포맷 함수
  const formatPrice = (price: number | null) => {
    if (!price) return '-';
    return `${price.toLocaleString()}원`;
  };

  // 남은 시간 계산
  const getRemainingTime = (endDate: string) => {
    const now = new Date();
    const end = new Date(endDate);
    const diff = end.getTime() - now.getTime();

    if (diff < 0) return '마감';

    const days = Math.floor(diff / (1000 * 60 * 60 * 24));
    const hours = Math.floor((diff % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));

    return `${days}일 ${hours}시간 남음`;
  };

  if (isLoading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="60vh">
        <CircularProgress />
      </Box>
    );
  }

  if (error || !data) {
    return (
      <Box p={3}>
        <Alert severity="error">
          입찰 정보를 불러오는 중 오류가 발생했습니다.
        </Alert>
        <Button
          startIcon={<ArrowBack />}
          onClick={() => navigate('/search')}
          sx={{ mt: 2 }}
        >
          검색으로 돌아가기
        </Button>
      </Box>
    );
  }

  return (
    <Box sx={{ p: 3 }}>
      {/* 헤더 */}
      <Box display="flex" alignItems="center" justifyContent="space-between" mb={3}>
        <Box display="flex" alignItems="center" gap={2}>
          <IconButton onClick={() => navigate('/search')}>
            <ArrowBack />
          </IconButton>
          <Typography variant="h5" fontWeight="bold">
            입찰 공고 상세
          </Typography>
        </Box>
        <Box display="flex" gap={1}>
          <Tooltip title={isBookmarked ? '북마크 제거' : '북마크 추가'}>
            <IconButton onClick={handleBookmarkToggle} color="primary">
              {isBookmarked ? <Bookmark /> : <BookmarkBorder />}
            </IconButton>
          </Tooltip>
          {data.detail_page_url && (
            <Button
              variant="outlined"
              startIcon={<OpenInNew />}
              href={data.detail_page_url}
              target="_blank"
              rel="noopener noreferrer"
            >
              원문 보기
            </Button>
          )}
        </Box>
      </Box>

      {/* 공고 제목 & 기본 정보 */}
      <Paper elevation={2} sx={{ p: 3, mb: 3 }}>
        <Typography variant="h6" fontWeight="bold" gutterBottom>
          {data.title}
        </Typography>

        <Box display="flex" gap={1} flexWrap="wrap" mt={2} mb={3}>
          <Chip
            icon={<CalendarToday fontSize="small" />}
            label={getRemainingTime(data.bid_end_date)}
            color={new Date(data.bid_end_date) < new Date() ? 'default' : 'warning'}
          />
          <Chip label={data.bid_method || '입찰방식 미표시'} />
          <Chip label={data.contract_method || '계약방법 미표시'} />
        </Box>

        <Divider sx={{ my: 2 }} />

        <Grid container spacing={2}>
          <Grid item xs={12} md={6}>
            <Box display="flex" alignItems="center" gap={1} mb={1.5}>
              <Business fontSize="small" color="action" />
              <Typography variant="body2" color="text.secondary" sx={{ minWidth: 80 }}>
                발주기관
              </Typography>
              <Typography variant="body1" fontWeight="medium">
                {data.organization_name}
              </Typography>
            </Box>
            {data.department_name && (
              <Box display="flex" alignItems="center" gap={1} mb={1.5} pl={4}>
                <Typography variant="body2" color="text.secondary" sx={{ minWidth: 80 }}>
                  담당부서
                </Typography>
                <Typography variant="body2">
                  {data.department_name}
                </Typography>
              </Box>
            )}
          </Grid>

          <Grid item xs={12} md={6}>
            <Box display="flex" alignItems="center" gap={1} mb={1.5}>
              <AttachMoney fontSize="small" color="action" />
              <Typography variant="body2" color="text.secondary" sx={{ minWidth: 80 }}>
                예정가격
              </Typography>
              <Typography variant="body1" fontWeight="medium" color="primary">
                {formatPrice(data.estimated_price)}
              </Typography>
            </Box>
          </Grid>
        </Grid>
      </Paper>

      {/* 일정 정보 */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom fontWeight="bold">
            일정 정보
          </Typography>
          <Divider sx={{ mb: 2 }} />
          <Grid container spacing={2}>
            <Grid item xs={12} md={4}>
              <Typography variant="body2" color="text.secondary" gutterBottom>
                공고일
              </Typography>
              <Typography variant="body1">
                {formatDate(data.announcement_date)}
              </Typography>
            </Grid>
            <Grid item xs={12} md={4}>
              <Typography variant="body2" color="text.secondary" gutterBottom>
                입찰시작
              </Typography>
              <Typography variant="body1">
                {formatDate(data.bid_start_date)}
              </Typography>
            </Grid>
            <Grid item xs={12} md={4}>
              <Typography variant="body2" color="text.secondary" gutterBottom>
                입찰마감
              </Typography>
              <Typography variant="body1" color="error">
                {formatDate(data.bid_end_date)}
              </Typography>
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      {/* 담당자 정보 */}
      {(data.officer_name || data.officer_phone || data.officer_email) && (
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Typography variant="h6" gutterBottom fontWeight="bold">
              담당자 정보
            </Typography>
            <Divider sx={{ mb: 2 }} />
            <Grid container spacing={2}>
              {data.officer_name && (
                <Grid item xs={12} md={4}>
                  <Box display="flex" alignItems="center" gap={1}>
                    <Person fontSize="small" color="action" />
                    <Typography variant="body2" color="text.secondary">
                      이름
                    </Typography>
                  </Box>
                  <Typography variant="body1" sx={{ ml: 3, mt: 0.5 }}>
                    {data.officer_name}
                  </Typography>
                </Grid>
              )}
              {data.officer_phone && (
                <Grid item xs={12} md={4}>
                  <Box display="flex" alignItems="center" gap={1}>
                    <Phone fontSize="small" color="action" />
                    <Typography variant="body2" color="text.secondary">
                      전화번호
                    </Typography>
                  </Box>
                  <Typography variant="body1" sx={{ ml: 3, mt: 0.5 }}>
                    {data.officer_phone}
                  </Typography>
                </Grid>
              )}
              {data.officer_email && (
                <Grid item xs={12} md={4}>
                  <Box display="flex" alignItems="center" gap={1}>
                    <Email fontSize="small" color="action" />
                    <Typography variant="body2" color="text.secondary">
                      이메일
                    </Typography>
                  </Box>
                  <Typography
                    variant="body1"
                    sx={{ ml: 3, mt: 0.5 }}
                    component="a"
                    href={`mailto:${data.officer_email}`}
                    style={{ textDecoration: 'none', color: 'inherit' }}
                  >
                    {data.officer_email}
                  </Typography>
                </Grid>
              )}
            </Grid>
          </CardContent>
        </Card>
      )}

      {/* 기타 정보 */}
      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom fontWeight="bold">
            기타 정보
          </Typography>
          <Divider sx={{ mb: 2 }} />
          <Grid container spacing={2}>
            <Grid item xs={12} md={6}>
              <Typography variant="body2" color="text.secondary" gutterBottom>
                공고번호
              </Typography>
              <Typography variant="body1">
                {data.bid_notice_no}
              </Typography>
            </Grid>
            <Grid item xs={12} md={6}>
              <Typography variant="body2" color="text.secondary" gutterBottom>
                최종 업데이트
              </Typography>
              <Typography variant="body2">
                {formatDate(data.updated_at)}
              </Typography>
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      {/* 하단 버튼 */}
      <Box display="flex" justifyContent="space-between" mt={4}>
        <Button
          variant="outlined"
          startIcon={<ArrowBack />}
          onClick={() => navigate('/search')}
        >
          목록으로
        </Button>
        {data.detail_page_url && (
          <Button
            variant="contained"
            endIcon={<OpenInNew />}
            href={data.detail_page_url}
            target="_blank"
            rel="noopener noreferrer"
          >
            나라장터에서 보기
          </Button>
        )}
      </Box>
    </Box>
  );
};

export default BidDetail;
