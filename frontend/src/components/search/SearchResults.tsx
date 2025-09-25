/**
 * SearchResults 컴포넌트
 * 검색 결과를 표시하는 컴포넌트
 */

import React from 'react';
import {
  Box,
  Card,
  CardContent,
  CardActions,
  Typography,
  Chip,
  Stack,
  Button,
  IconButton,
  Skeleton,
  Alert,
  AlertTitle,
  Divider,
  Grid,
  Tooltip,
  Link
} from '@mui/material';
import {
  Description as DocumentIcon,
  Business as BusinessIcon,
  Gavel as GavelIcon,
  AttachMoney as MoneyIcon,
  Schedule as ScheduleIcon,
  LocationOn as LocationIcon,
  Category as CategoryIcon,
  Visibility as ViewIcon,
  BookmarkBorder as BookmarkIcon,
  BookmarkAdded as BookmarkedIcon,
  Share as ShareIcon,
  GetApp as DownloadIcon,
  TrendingUp as TrendingUpIcon,
  Warning as WarningIcon
} from '@mui/icons-material';
import { styled } from '@mui/material/styles';
import {
  SearchResultsProps,
  SearchResult,
  BidResult,
  DocumentResult,
  CompanyResult
} from '../../types/search.types';

// 스타일 컴포넌트
const ResultCard = styled(Card)(({ theme }) => ({
  marginBottom: theme.spacing(2),
  transition: 'all 0.3s ease',
  cursor: 'pointer',
  '&:hover': {
    boxShadow: theme.shadows[4],
    transform: 'translateY(-2px)'
  }
}));

const HighlightText = styled('span')(({ theme }) => ({
  backgroundColor: theme.palette.warning.light,
  padding: '0 4px',
  borderRadius: '2px',
  fontWeight: 600
}));

const StatusChip = styled(Chip)(({ theme }) => ({
  fontWeight: 600,
  borderRadius: '4px'
}));

const SearchResults: React.FC<SearchResultsProps> = ({
  results,
  loading,
  error,
  onItemClick
}) => {
  // 북마크 상태 관리 (실제로는 전역 상태나 API와 연동해야 함)
  const [bookmarkedItems, setBookmarkedItems] = React.useState<Set<string>>(new Set());

  /**
   * 북마크 토글
   */
  const handleBookmarkToggle = (itemId: string, event: React.MouseEvent) => {
    event.stopPropagation();
    setBookmarkedItems(prev => {
      const newSet = new Set(prev);
      if (newSet.has(itemId)) {
        newSet.delete(itemId);
      } else {
        newSet.add(itemId);
      }
      return newSet;
    });
  };

  /**
   * 공유 처리
   */
  const handleShare = (item: SearchResult, event: React.MouseEvent) => {
    event.stopPropagation();
    // 실제로는 공유 기능 구현
    if (navigator.share) {
      const title = 'title' in item ? item.title :
                   'name' in item ? item.name :
                   'Search Result';
      navigator.share({
        title: title || 'Search Result',
        url: window.location.href
      });
    }
  };

  /**
   * 금액 포맷팅
   */
  const formatPrice = (price: number): string => {
    if (price >= 100000000) {
      return `${(price / 100000000).toFixed(1)}억원`;
    } else if (price >= 10000000) {
      return `${(price / 10000000).toFixed(0)}천만원`;
    } else if (price >= 10000) {
      return `${(price / 10000).toFixed(0)}만원`;
    }
    return price.toLocaleString() + '원';
  };

  /**
   * 날짜 포맷팅
   */
  const formatDate = (dateStr: string): string => {
    try {
      const date = new Date(dateStr);
      return new Intl.DateTimeFormat('ko-KR', {
        year: 'numeric',
        month: 'long',
        day: 'numeric'
      }).format(date);
    } catch {
      return dateStr;
    }
  };

  /**
   * 남은 일수 계산
   */
  const getDaysRemaining = (deadline: string): number => {
    const today = new Date();
    const deadlineDate = new Date(deadline);
    const diffTime = deadlineDate.getTime() - today.getTime();
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    return diffDays;
  };

  /**
   * 상태 색상 결정
   */
  const getStatusColor = (status: string): 'success' | 'warning' | 'error' | 'default' => {
    switch (status) {
      case 'active':
      case '진행중':
        return 'success';
      case 'pending':
      case '예정':
        return 'warning';
      case 'closed':
      case '마감':
        return 'error';
      default:
        return 'default';
    }
  };

  /**
   * 입찰공고 결과 렌더링
   */
  const renderBidResult = (item: BidResult) => {
    const daysRemaining = item.deadline ? getDaysRemaining(item.deadline) : null;
    const isBookmarked = bookmarkedItems.has(item.id);

    return (
      <ResultCard onClick={() => onItemClick?.(item)}>
        <CardContent>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
            <Stack direction="row" spacing={1} alignItems="center">
              <GavelIcon color="primary" fontSize="small" />
              <Typography variant="caption" color="text.secondary">
                입찰공고
              </Typography>
              <Typography variant="caption" color="text.secondary">
                {item.bidNoticeNo}
              </Typography>
            </Stack>
            <Stack direction="row" spacing={1}>
              <StatusChip
                label={item.status}
                size="small"
                color={getStatusColor(item.status)}
              />
              {daysRemaining !== null && daysRemaining >= 0 && daysRemaining <= 7 && (
                <StatusChip
                  label={`D-${daysRemaining}`}
                  size="small"
                  color="error"
                  icon={<WarningIcon />}
                />
              )}
            </Stack>
          </Box>

          <Typography variant="h6" gutterBottom>
            {item.highlight ? (
              <div dangerouslySetInnerHTML={{ __html: item.highlight }} />
            ) : (
              item.title
            )}
          </Typography>

          <Grid container spacing={2} sx={{ mb: 2 }}>
            <Grid item xs={12} sm={6}>
              <Stack direction="row" spacing={1} alignItems="center">
                <BusinessIcon fontSize="small" color="action" />
                <Typography variant="body2" color="text.secondary">
                  {item.organization}
                </Typography>
              </Stack>
            </Grid>
            {item.price && (
              <Grid item xs={12} sm={6}>
                <Stack direction="row" spacing={1} alignItems="center">
                  <MoneyIcon fontSize="small" color="action" />
                  <Typography variant="body2" color="text.secondary">
                    예정가격: {formatPrice(item.price)}
                  </Typography>
                </Stack>
              </Grid>
            )}
            {item.deadline && (
              <Grid item xs={12} sm={6}>
                <Stack direction="row" spacing={1} alignItems="center">
                  <ScheduleIcon fontSize="small" color="action" />
                  <Typography variant="body2" color="text.secondary">
                    마감: {formatDate(item.deadline)}
                  </Typography>
                </Stack>
              </Grid>
            )}
          </Grid>

          {item.score && (
            <Box sx={{ mt: 1 }}>
              <Stack direction="row" spacing={1} alignItems="center">
                <TrendingUpIcon fontSize="small" color="success" />
                <Typography variant="caption" color="success.main">
                  관련도: {item.score.toFixed(1)}%
                </Typography>
              </Stack>
            </Box>
          )}
        </CardContent>

        <CardActions sx={{ px: 2, pb: 2 }}>
          <Button size="small" startIcon={<ViewIcon />}>
            상세보기
          </Button>
          <IconButton
            size="small"
            onClick={(e) => handleBookmarkToggle(item.id, e)}
            color={isBookmarked ? 'primary' : 'default'}
          >
            {isBookmarked ? <BookmarkedIcon /> : <BookmarkIcon />}
          </IconButton>
          <IconButton
            size="small"
            onClick={(e) => handleShare(item, e)}
          >
            <ShareIcon />
          </IconButton>
        </CardActions>
      </ResultCard>
    );
  };

  /**
   * 문서 결과 렌더링
   */
  const renderDocumentResult = (item: DocumentResult) => {
    const isBookmarked = bookmarkedItems.has(item.id);

    return (
      <ResultCard onClick={() => onItemClick?.(item)}>
        <CardContent>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
            <Stack direction="row" spacing={1} alignItems="center">
              <DocumentIcon color="primary" fontSize="small" />
              <Typography variant="caption" color="text.secondary">
                문서
              </Typography>
              <Chip label={item.fileType.toUpperCase()} size="small" variant="outlined" />
            </Stack>
          </Box>

          <Typography variant="h6" gutterBottom>
            {item.title}
          </Typography>

          <Typography variant="body2" color="text.secondary" gutterBottom>
            {item.filename}
          </Typography>

          {item.highlight && item.highlight.length > 0 && (
            <Box sx={{ mt: 2, p: 1, bgcolor: 'grey.50', borderRadius: 1 }}>
              <Typography variant="caption" color="text.secondary" display="block" gutterBottom>
                매칭 부분:
              </Typography>
              {item.highlight.map((text, index) => (
                <Typography
                  key={index}
                  variant="body2"
                  paragraph
                  dangerouslySetInnerHTML={{ __html: text }}
                />
              ))}
            </Box>
          )}

          <Stack direction="row" spacing={2} sx={{ mt: 2 }}>
            <Typography variant="caption" color="text.secondary">
              크기: {(item.size / 1024).toFixed(1)} KB
            </Typography>
            <Typography variant="caption" color="text.secondary">
              수정일: {formatDate(item.modified)}
            </Typography>
          </Stack>

          {item.score && (
            <Box sx={{ mt: 1 }}>
              <Typography variant="caption" color="success.main">
                매칭 횟수: {item.score}
              </Typography>
            </Box>
          )}
        </CardContent>

        <CardActions sx={{ px: 2, pb: 2 }}>
          <Button size="small" startIcon={<ViewIcon />}>
            보기
          </Button>
          <Button size="small" startIcon={<DownloadIcon />}>
            다운로드
          </Button>
          <IconButton
            size="small"
            onClick={(e) => handleBookmarkToggle(item.id, e)}
            color={isBookmarked ? 'primary' : 'default'}
          >
            {isBookmarked ? <BookmarkedIcon /> : <BookmarkIcon />}
          </IconButton>
        </CardActions>
      </ResultCard>
    );
  };

  /**
   * 기업 결과 렌더링
   */
  const renderCompanyResult = (item: CompanyResult) => {
    const isBookmarked = bookmarkedItems.has(item.id);

    return (
      <ResultCard onClick={() => onItemClick?.(item)}>
        <CardContent>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
            <Stack direction="row" spacing={1} alignItems="center">
              <BusinessIcon color="primary" fontSize="small" />
              <Typography variant="caption" color="text.secondary">
                기업정보
              </Typography>
            </Stack>
          </Box>

          <Typography variant="h6" gutterBottom>
            {item.name}
          </Typography>

          <Grid container spacing={2}>
            <Grid item xs={12} sm={6}>
              <Typography variant="body2" color="text.secondary">
                사업자번호: {item.businessNumber}
              </Typography>
            </Grid>
            {item.industry && (
              <Grid item xs={12} sm={6}>
                <Stack direction="row" spacing={1} alignItems="center">
                  <CategoryIcon fontSize="small" color="action" />
                  <Typography variant="body2" color="text.secondary">
                    {item.industry}
                  </Typography>
                </Stack>
              </Grid>
            )}
            {item.region && (
              <Grid item xs={12} sm={6}>
                <Stack direction="row" spacing={1} alignItems="center">
                  <LocationIcon fontSize="small" color="action" />
                  <Typography variant="body2" color="text.secondary">
                    {item.region}
                  </Typography>
                </Stack>
              </Grid>
            )}
          </Grid>
        </CardContent>

        <CardActions sx={{ px: 2, pb: 2 }}>
          <Button size="small" startIcon={<ViewIcon />}>
            상세정보
          </Button>
          <IconButton
            size="small"
            onClick={(e) => handleBookmarkToggle(item.id, e)}
            color={isBookmarked ? 'primary' : 'default'}
          >
            {isBookmarked ? <BookmarkedIcon /> : <BookmarkIcon />}
          </IconButton>
        </CardActions>
      </ResultCard>
    );
  };

  /**
   * 로딩 스켈레톤
   */
  const renderSkeleton = () => (
    <>
      {[1, 2, 3].map((index) => (
        <Card key={index} sx={{ mb: 2 }}>
          <CardContent>
            <Skeleton variant="text" width="30%" height={20} sx={{ mb: 1 }} />
            <Skeleton variant="text" width="70%" height={30} sx={{ mb: 2 }} />
            <Skeleton variant="text" width="100%" height={20} />
            <Skeleton variant="text" width="80%" height={20} />
          </CardContent>
          <CardActions>
            <Skeleton variant="rectangular" width={80} height={30} />
            <Skeleton variant="circular" width={30} height={30} sx={{ ml: 1 }} />
          </CardActions>
        </Card>
      ))}
    </>
  );

  // 에러 표시
  if (error) {
    return (
      <Alert severity="error">
        <AlertTitle>검색 오류</AlertTitle>
        {error}
      </Alert>
    );
  }

  // 로딩 중
  if (loading) {
    return renderSkeleton();
  }

  // 결과 없음
  if (!results || results.length === 0) {
    return (
      <Alert severity="info">
        <AlertTitle>검색 결과 없음</AlertTitle>
        검색 조건과 일치하는 결과가 없습니다. 다른 검색어나 필터를 시도해보세요.
      </Alert>
    );
  }

  // 결과 렌더링
  return (
    <Box>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
        {results.length}개의 검색 결과
      </Typography>

      {results.map((item) => {
        switch (item.type) {
          case 'bid':
            return <div key={item.id}>{renderBidResult(item as BidResult)}</div>;
          case 'document':
            return <div key={item.id}>{renderDocumentResult(item as DocumentResult)}</div>;
          case 'company':
            return <div key={item.id}>{renderCompanyResult(item as CompanyResult)}</div>;
          default:
            return null;
        }
      })}
    </Box>
  );
};

export default SearchResults;