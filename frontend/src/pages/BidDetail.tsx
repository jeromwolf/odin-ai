import React, { useEffect, useState } from 'react';
import {
  Box,
  Typography,
  Paper,
  Grid,
  Divider,
  Chip,
  Button,
  Alert,
  Card,
  CardContent,
  IconButton,
  Tooltip,
  CircularProgress,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
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
  EmojiEvents,
  History,
  Groups,
} from '@mui/icons-material';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import apiClient from '../services/api';
import { FullscreenLoading } from '../components/common';
import { formatKRW, formatKRDate, formatTimeRemaining } from '../utils/formatters';

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
  extracted_info?: {
    requirements?: Record<string, string>;
    contract_details?: Record<string, string>;
    prices?: Record<string, string>;
    schedule?: Record<string, string>;
    work_type?: Record<string, string>;
    region?: Record<string, string>;
  };
  award_info?: {
    winning_company: string | null;
    winning_bizno: string | null;
    winning_price: number | null;
    winning_rate: number | null;
    participant_count: number | null;
    award_date: string | null;
    status: string;
  };
  tags?: string[];
  documents?: Array<{
    document_id: number;
    document_type: string;
    file_name: string;
    file_size: number;
    download_status: string;
    processing_status: string;
  }>;
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

  // 유사 낙찰 히스토리 조회
  const { data: similarAwardsData, isLoading: similarLoading } = useQuery({
    queryKey: ['similarAwards', id],
    queryFn: async () => {
      if (!id) return { data: [] };
      return apiClient.getSimilarAwards(id);
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


  if (isLoading) {
    return <FullscreenLoading message="공고 정보 로딩 중..." />;
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

        <Box display="flex" gap={1} flexWrap="wrap" mt={2} mb={1}>
          <Chip
            icon={<CalendarToday fontSize="small" />}
            label={formatTimeRemaining(data.bid_end_date)}
            color={new Date(data.bid_end_date) < new Date() ? 'default' : 'warning'}
          />
          <Chip label={data.bid_method || '입찰방식 미표시'} />
          <Chip label={data.contract_method || '계약방법 미표시'} />
        </Box>

        {data.tags && data.tags.length > 0 && (
          <Box sx={{ display: 'flex', gap: 0.75, flexWrap: 'wrap', mt: 1, mb: 2 }}>
            {data.tags.map((tag, i) => (
              <Chip
                key={i}
                label={`#${tag}`}
                size="small"
                variant="outlined"
                onClick={() => navigate(`/search?q=${encodeURIComponent(tag)}`)}
                sx={{
                  cursor: 'pointer',
                  fontSize: '0.78rem',
                  color: 'primary.main',
                  borderColor: 'primary.light',
                  '&:hover': { bgcolor: 'primary.main', color: 'white', borderColor: 'primary.main' },
                }}
              />
            ))}
          </Box>
        )}

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
                {formatKRW(data.estimated_price)}
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
                {formatKRDate(data.announcement_date, 'yyyy년 MM월 dd일 HH:mm')}
              </Typography>
            </Grid>
            <Grid item xs={12} md={4}>
              <Typography variant="body2" color="text.secondary" gutterBottom>
                입찰시작
              </Typography>
              <Typography variant="body1">
                {formatKRDate(data.bid_start_date, 'yyyy년 MM월 dd일 HH:mm')}
              </Typography>
            </Grid>
            <Grid item xs={12} md={4}>
              <Typography variant="body2" color="text.secondary" gutterBottom>
                입찰마감
              </Typography>
              <Typography variant="body1" color="error">
                {formatKRDate(data.bid_end_date, 'yyyy년 MM월 dd일 HH:mm')}
              </Typography>
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      {/* 추출된 정보 */}
      {data.extracted_info && Object.keys(data.extracted_info).length > 0 && (
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Typography variant="h6" gutterBottom fontWeight="bold">
              추출된 정보
            </Typography>
            <Divider sx={{ mb: 2 }} />

            {data.extracted_info.requirements && Object.keys(data.extracted_info.requirements).length > 0 && (
              <Box sx={{ mb: 2 }}>
                <Typography variant="subtitle2" color="primary" gutterBottom sx={{ fontWeight: 700 }}>
                  자격요건
                </Typography>
                {Object.entries(data.extracted_info.requirements).map(([key, value]) => (
                  <Box key={key} sx={{ mb: 1, pl: 1 }}>
                    <Typography variant="caption" color="text.secondary" sx={{ fontWeight: 600 }}>
                      {key}
                    </Typography>
                    <Typography variant="body2" sx={{ whiteSpace: 'pre-wrap', mt: 0.25 }}>
                      {value}
                    </Typography>
                  </Box>
                ))}
              </Box>
            )}

            {data.extracted_info.contract_details && Object.keys(data.extracted_info.contract_details).length > 0 && (
              <Box sx={{ mb: 2 }}>
                <Typography variant="subtitle2" color="primary" gutterBottom sx={{ fontWeight: 700 }}>
                  계약 조건
                </Typography>
                {Object.entries(data.extracted_info.contract_details).map(([key, value]) => (
                  <Box key={key} sx={{ mb: 1, pl: 1 }}>
                    <Typography variant="caption" color="text.secondary" sx={{ fontWeight: 600 }}>
                      {key}
                    </Typography>
                    <Typography variant="body2" sx={{ whiteSpace: 'pre-wrap', mt: 0.25 }}>
                      {value}
                    </Typography>
                  </Box>
                ))}
              </Box>
            )}

            {data.extracted_info.prices && Object.keys(data.extracted_info.prices).length > 0 && (
              <Box sx={{ mb: 2 }}>
                <Typography variant="subtitle2" color="primary" gutterBottom sx={{ fontWeight: 700 }}>
                  가격 정보
                </Typography>
                {Object.entries(data.extracted_info.prices).map(([key, value]) => (
                  <Box key={key} sx={{ mb: 1, pl: 1 }}>
                    <Typography variant="caption" color="text.secondary" sx={{ fontWeight: 600 }}>
                      {key}
                    </Typography>
                    <Typography variant="body2" sx={{ mt: 0.25 }}>
                      {value}
                    </Typography>
                  </Box>
                ))}
              </Box>
            )}

            {data.extracted_info.schedule && Object.keys(data.extracted_info.schedule).length > 0 && (
              <Box sx={{ mb: 2 }}>
                <Typography variant="subtitle2" color="primary" gutterBottom sx={{ fontWeight: 700 }}>
                  일정
                </Typography>
                {Object.entries(data.extracted_info.schedule).map(([key, value]) => (
                  <Box key={key} sx={{ mb: 1, pl: 1 }}>
                    <Typography variant="caption" color="text.secondary" sx={{ fontWeight: 600 }}>
                      {key}
                    </Typography>
                    <Typography variant="body2" sx={{ mt: 0.25 }}>
                      {value}
                    </Typography>
                  </Box>
                ))}
              </Box>
            )}

            {data.extracted_info.work_type && Object.keys(data.extracted_info.work_type).length > 0 && (
              <Box sx={{ mb: 2 }}>
                <Typography variant="subtitle2" color="primary" gutterBottom sx={{ fontWeight: 700 }}>
                  공사 유형
                </Typography>
                {Object.entries(data.extracted_info.work_type).map(([key, value]) => (
                  <Box key={key} sx={{ mb: 1, pl: 1 }}>
                    <Typography variant="caption" color="text.secondary" sx={{ fontWeight: 600 }}>
                      {key}
                    </Typography>
                    <Typography variant="body2" sx={{ mt: 0.25 }}>
                      {value}
                    </Typography>
                  </Box>
                ))}
              </Box>
            )}

            {data.extracted_info.region && Object.keys(data.extracted_info.region).length > 0 && (
              <Box sx={{ mb: 2 }}>
                <Typography variant="subtitle2" color="primary" gutterBottom sx={{ fontWeight: 700 }}>
                  지역
                </Typography>
                {Object.entries(data.extracted_info.region).map(([key, value]) => (
                  <Box key={key} sx={{ mb: 1, pl: 1 }}>
                    <Typography variant="caption" color="text.secondary" sx={{ fontWeight: 600 }}>
                      {key}
                    </Typography>
                    <Typography variant="body2" sx={{ mt: 0.25 }}>
                      {value}
                    </Typography>
                  </Box>
                ))}
              </Box>
            )}
          </CardContent>
        </Card>
      )}

      {/* 낙찰 정보 */}
      {data?.award_info && data.award_info.status === 'awarded' && (
        <Paper sx={{ p: 3, mb: 3, bgcolor: '#f0fdf4', border: '1px solid #86efac' }}>
          <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
            <EmojiEvents sx={{ color: '#f59e0b', mr: 1, fontSize: 28 }} />
            <Typography variant="h6" sx={{ fontWeight: 600 }}>
              낙찰 정보
            </Typography>
            <Chip label="낙찰 완료" color="success" size="small" sx={{ ml: 2 }} />
          </Box>
          <Grid container spacing={2}>
            <Grid item xs={12} sm={6} md={3}>
              <Typography variant="body2" color="text.secondary">낙찰업체</Typography>
              <Typography variant="h6" sx={{ fontWeight: 600 }}>
                {data.award_info.winning_company || '-'}
              </Typography>
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <Typography variant="body2" color="text.secondary">낙찰금액</Typography>
              <Typography variant="h6" sx={{ fontWeight: 600, color: '#059669' }}>
                {data.award_info.winning_price
                  ? formatKRW(data.award_info.winning_price)
                  : '-'}
              </Typography>
            </Grid>
            <Grid item xs={12} sm={6} md={2}>
              <Typography variant="body2" color="text.secondary">낙찰률</Typography>
              <Typography variant="h6" sx={{ fontWeight: 600 }}>
                {data.award_info.winning_rate
                  ? `${data.award_info.winning_rate.toFixed(2)}%`
                  : '-'}
              </Typography>
            </Grid>
            <Grid item xs={12} sm={6} md={2}>
              <Typography variant="body2" color="text.secondary">참여업체 수</Typography>
              <Box sx={{ display: 'flex', alignItems: 'center' }}>
                <Groups sx={{ color: '#6b7280', mr: 0.5, fontSize: 20 }} />
                <Typography variant="h6" sx={{ fontWeight: 600 }}>
                  {data.award_info.participant_count || '-'}
                </Typography>
              </Box>
            </Grid>
            <Grid item xs={12} sm={6} md={2}>
              <Typography variant="body2" color="text.secondary">낙찰일</Typography>
              <Typography variant="h6" sx={{ fontWeight: 600 }}>
                {data.award_info.award_date
                  ? formatKRDate(data.award_info.award_date)
                  : '-'}
              </Typography>
            </Grid>
          </Grid>
        </Paper>
      )}

      {data?.award_info && data.award_info.status === 'pending' && (
        <Paper sx={{ p: 2, mb: 3, bgcolor: '#fffbeb', border: '1px solid #fcd34d' }}>
          <Box sx={{ display: 'flex', alignItems: 'center' }}>
            <EmojiEvents sx={{ color: '#d97706', mr: 1 }} />
            <Typography variant="body1" color="text.secondary">
              낙찰 대기중 — 아직 낙찰 결과가 공개되지 않았습니다.
            </Typography>
          </Box>
        </Paper>
      )}

      {/* 유사 입찰 낙찰 히스토리 */}
      <Paper sx={{ p: 3, mb: 3 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
          <History sx={{ color: '#6366f1', mr: 1 }} />
          <Typography variant="h6" sx={{ fontWeight: 600 }}>
            유사 입찰 낙찰 히스토리
          </Typography>
        </Box>

        {similarLoading ? (
          <Box sx={{ display: 'flex', justifyContent: 'center', py: 3 }}>
            <CircularProgress size={30} />
          </Box>
        ) : similarAwardsData?.data && similarAwardsData.data.length > 0 ? (
          <TableContainer>
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell>유사도</TableCell>
                  <TableCell>공고명</TableCell>
                  <TableCell>발주기관</TableCell>
                  <TableCell>낙찰업체</TableCell>
                  <TableCell align="right">낙찰금액</TableCell>
                  <TableCell align="right">낙찰률</TableCell>
                  <TableCell align="center">참여사</TableCell>
                  <TableCell>낙찰일</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {similarAwardsData.data.map((award: any) => (
                  <TableRow
                    key={award.bid_notice_no}
                    hover
                    sx={{ cursor: 'pointer' }}
                    onClick={() => navigate(`/bids/${award.bid_notice_no}`)}
                  >
                    <TableCell>
                      <Chip
                        label={`${award.title_similarity}%`}
                        size="small"
                        color={award.title_similarity >= 70 ? 'success' : award.title_similarity >= 50 ? 'warning' : 'default'}
                      />
                    </TableCell>
                    <TableCell>
                      <Typography variant="body2" noWrap sx={{ maxWidth: 250 }}>
                        {award.title}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <Typography variant="body2" noWrap sx={{ maxWidth: 120 }}>
                        {award.organization_name}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <Typography variant="body2" sx={{ fontWeight: 600 }}>
                        {award.winning_company}
                      </Typography>
                    </TableCell>
                    <TableCell align="right">
                      <Typography variant="body2">
                        {award.winning_price ? formatKRW(award.winning_price) : '-'}
                      </Typography>
                    </TableCell>
                    <TableCell align="right">
                      <Typography variant="body2">
                        {award.winning_rate ? `${award.winning_rate.toFixed(2)}%` : '-'}
                      </Typography>
                    </TableCell>
                    <TableCell align="center">
                      {award.participant_count || '-'}
                    </TableCell>
                    <TableCell>
                      <Typography variant="body2">
                        {award.award_date ? formatKRDate(award.award_date) : '-'}
                      </Typography>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        ) : (
          <Alert severity="info">유사한 과거 낙찰 이력이 없습니다.</Alert>
        )}
      </Paper>

      {/* 첨부 문서 */}
      {data.documents && data.documents.length > 0 && (
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Typography variant="h6" gutterBottom fontWeight="bold">
              첨부 문서
            </Typography>
            <Divider sx={{ mb: 2 }} />
            {data.documents.map((doc) => (
              <Box
                key={doc.document_id}
                sx={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  p: 1.5,
                  mb: 1,
                  border: '1px solid',
                  borderColor: 'divider',
                  borderRadius: 1.5,
                }}
              >
                <Box>
                  <Typography variant="body2" fontWeight={600}>
                    {doc.file_name}
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    {doc.document_type?.toUpperCase()} · {doc.file_size ? `${(doc.file_size / 1024).toFixed(0)} KB` : '크기 미확인'}
                  </Typography>
                </Box>
                <Box sx={{ display: 'flex', gap: 0.5 }}>
                  <Chip
                    size="small"
                    label={doc.download_status === 'completed' ? '다운로드 완료' : doc.download_status}
                    color={doc.download_status === 'completed' ? 'success' : 'default'}
                    variant="outlined"
                    sx={{ fontSize: '0.7rem' }}
                  />
                  <Chip
                    size="small"
                    label={doc.processing_status === 'completed' ? '처리 완료' : doc.processing_status}
                    color={doc.processing_status === 'completed' ? 'info' : 'default'}
                    variant="outlined"
                    sx={{ fontSize: '0.7rem' }}
                  />
                </Box>
              </Box>
            ))}
          </CardContent>
        </Card>
      )}

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
                {formatKRDate(data.updated_at, 'yyyy년 MM월 dd일 HH:mm')}
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
