import React, { useEffect, useState } from 'react';
import {
  Box,
  Grid,
  Typography,
  Chip,
  List,
  ListItem,
  ListItemText,
  Paper,
  Button,
  useTheme,
} from '@mui/material';
import {
  TrendingUp,
  AccessTime,
  Bookmark,
  ArrowForward,
  Business,
  Dashboard as DashboardIcon,
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  Legend,
} from 'recharts';
import { format, parseISO } from 'date-fns';
import apiClient from '../services/api';
import { StatCard, FullscreenLoading, SkeletonCard, PageHeader } from '../components/common';
import { CHART_COLORS, STAT_CARD_COLORS, getChartColor } from '../utils/colors';
// formatTimeRemaining from '../utils/formatters' takes a date string; local version handles hours number from API

const Dashboard: React.FC = () => {
  const navigate = useNavigate();
  const theme = useTheme();
  const [bookmarkedBids, setBookmarkedBids] = useState<Set<string>>(new Set());

  // 대시보드 개요 데이터
  const { data: overview, isLoading: overviewLoading } = useQuery({
    queryKey: ['dashboardOverview'],
    queryFn: () => apiClient.getDashboardOverview(),
    refetchInterval: 60000, // 1분마다 새로고침
  });

  // 입찰 통계 데이터
  const { data: statistics, isLoading: statsLoading } = useQuery({
    queryKey: ['bidStatistics'],
    queryFn: () => apiClient.getBidStatistics('7d'),
  });

  // 마감 임박 입찰
  const { data: deadlines, isLoading: deadlinesLoading } = useQuery({
    queryKey: ['upcomingDeadlines'],
    queryFn: () => apiClient.getUpcomingDeadlines(7),
  });

  // AI 추천 입찰
  const { data: recommendations, isLoading: recommendationsLoading } = useQuery({
    queryKey: ['recommendations'],
    queryFn: () => apiClient.getRecommendedBids(5),
  });

  // 북마크 데이터
  const { data: bookmarks } = useQuery({
    queryKey: ['bookmarks'],
    queryFn: () => apiClient.getBookmarks(),
    staleTime: 10000, // 10초간 캐시 유지 (적절한 밸런스)
    // refetchOnWindowFocus는 전역 설정(true) 사용
    // refetchOnMount는 기본값(true) 사용
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


  const getUrgencyColor = (hours: number) => {
    // NaN 또는 undefined/null 체크
    if (!hours || isNaN(hours)) {
      return 'default';
    }
    if (hours <= 24) return 'error';
    if (hours <= 72) return 'warning';
    return 'info';
  };

  const formatTimeRemaining = (hours: number) => {
    // NaN 또는 undefined/null 체크
    if (!hours || isNaN(hours)) {
      return '시간 정보 없음';
    }

    const days = Math.floor(hours / 24);
    const remainingHours = Math.floor(hours % 24);

    if (days > 0) {
      return `${days}일 ${remainingHours}시간 남음`;
    }
    return `${Math.floor(hours)}시간 남음`;
  };

  const statCardData = [
    { title: '오늘의 신규 입찰', value: overview?.activeBids || 0, change: 5, changeLabel: '전일 대비', icon: <TrendingUp />, iconBg: STAT_CARD_COLORS.total.bg, iconColor: STAT_CARD_COLORS.total.color },
    { title: '마감 임박', value: deadlines?.data?.length || 0, icon: <AccessTime />, iconBg: STAT_CARD_COLORS.warning.bg, iconColor: STAT_CARD_COLORS.warning.color },
    { title: '북마크', value: bookmarkedBids.size || 0, icon: <Bookmark />, iconBg: STAT_CARD_COLORS.total.bg, iconColor: STAT_CARD_COLORS.total.icon },
    { title: 'AI 매칭', value: recommendations?.data?.length || 0, icon: <Business />, iconBg: STAT_CARD_COLORS.info.bg, iconColor: STAT_CARD_COLORS.info.color },
  ];

  if (overviewLoading || statsLoading) {
    return (
      <Box>
        <PageHeader title="대시보드" icon={<DashboardIcon />} />
        <Grid container spacing={3} sx={{ mb: 3 }}>
          {[0, 1, 2, 3].map((i) => (
            <Grid item xs={12} sm={6} md={3} key={i}>
              <SkeletonCard variant="stat" />
            </Grid>
          ))}
        </Grid>
        <Grid container spacing={3}>
          <Grid item xs={12} md={8}>
            <SkeletonCard variant="content" />
          </Grid>
          <Grid item xs={12} md={4}>
            <SkeletonCard variant="content" />
          </Grid>
        </Grid>
      </Box>
    );
  }

  return (
    <Box>
      <PageHeader title="대시보드" icon={<DashboardIcon />} />

      {/* 통계 카드 */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        {statCardData.map((card, index) => (
          <Grid item xs={12} sm={6} md={3} key={index}>
            <StatCard {...card} />
          </Grid>
        ))}
      </Grid>

      <Grid container spacing={3}>
        {/* 주간 입찰 트렌드 차트 */}
        <Grid item xs={12} md={8}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" sx={{ mb: 2 }}>
              주간 입찰 트렌드
            </Typography>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={statistics?.daily_stats || []}>
                <CartesianGrid strokeDasharray="3 3" stroke={theme.palette.divider} />
                <XAxis
                  dataKey="date"
                  tickFormatter={(value) => format(parseISO(value), 'MM/dd')}
                  stroke={theme.palette.text.secondary}
                />
                <YAxis stroke={theme.palette.text.secondary} />
                <Tooltip
                  labelFormatter={(value) => format(parseISO(value as string), 'yyyy-MM-dd')}
                  contentStyle={{
                    backgroundColor: theme.palette.background.paper,
                    border: '1px solid ' + theme.palette.divider,
                    borderRadius: 8,
                  }}
                />
                <Line
                  type="monotone"
                  dataKey="count"
                  stroke={CHART_COLORS[0]}
                  strokeWidth={2}
                  name="입찰 건수"
                />
              </LineChart>
            </ResponsiveContainer>
          </Paper>
        </Grid>

        {/* 카테고리별 분포 */}
        <Grid item xs={12} md={4}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" sx={{ mb: 2 }}>
              카테고리별 분포
            </Typography>
            <ResponsiveContainer width="100%" height={350}>
              <PieChart>
                <Pie
                  data={statistics?.category_distribution?.slice(0, 5) || []}
                  cx="50%"
                  cy="45%"
                  labelLine={false}
                  outerRadius={70}
                  fill={CHART_COLORS[0]}
                  dataKey="count"
                  label={({ percent }) => `${(percent * 100).toFixed(0)}%`}
                  onClick={(data: any, index: number) => {
                    // 클릭한 데이터의 카테고리 이름 가져오기
                    if (data && data.category) {
                      // 카테고리 클릭 시 검색 페이지로 이동
                      navigate(`/search?q=${encodeURIComponent(data.category)}`);
                    }
                  }}
                >
                  {statistics?.category_distribution?.slice(0, 5).map((entry: any, index: number) => (
                    <Cell
                      key={`cell-${index}`}
                      fill={getChartColor(index)}
                      style={{ cursor: 'pointer' }}
                    />
                  ))}
                </Pie>
                <Tooltip
                  formatter={(value: any, name: any, props: any) => [`${value}건`, props.payload.category]}
                  contentStyle={{
                    backgroundColor: theme.palette.background.paper,
                    border: '1px solid ' + theme.palette.divider,
                    borderRadius: 8,
                  }}
                />
                <Legend
                  verticalAlign="bottom"
                  height={36}
                  formatter={(value, entry: any) => `${entry.payload.category} (${entry.payload.count}건)`}
                />
              </PieChart>
            </ResponsiveContainer>
          </Paper>
        </Grid>

        {/* 마감 임박 입찰 */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 3 }}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2 }}>
              <Typography variant="h6">마감 임박 입찰</Typography>
              <Button
                size="small"
                endIcon={<ArrowForward />}
                onClick={() => navigate('/search')}
              >
                전체보기
              </Button>
            </Box>
            {deadlinesLoading ? (
              <FullscreenLoading size={24} />
            ) : (
              <List>
                {(deadlines?.deadlines || []).slice(0, 5).map((bid: any) => (
                  <ListItem
                    key={bid.id || bid.bid_id}
                    button
                    onClick={() => navigate(`/search?q=${encodeURIComponent(bid.title)}`)}
                  >
                    <ListItemText
                      primary={bid.title}
                      secondary={
                        <Box>
                          <Typography variant="caption" display="block">
                            {bid.organization}
                          </Typography>
                          <Chip
                            label={formatTimeRemaining(bid.hours_remaining)}
                            size="small"
                            color={getUrgencyColor(bid.hours_remaining)}
                            sx={{ mt: 0.5 }}
                          />
                        </Box>
                      }
                    />
                  </ListItem>
                ))}
              </List>
            )}
          </Paper>
        </Grid>

        {/* AI 추천 입찰 */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 3 }}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2 }}>
              <Typography variant="h6">AI 추천 입찰</Typography>
              <Chip label="개인화 매칭" color="primary" size="small" />
            </Box>
            {recommendationsLoading ? (
              <FullscreenLoading size={24} />
            ) : (
              <List>
                {(recommendations?.recommendations || []).map((bid: any) => (
                  <ListItem
                    key={bid.id || bid.bid_id}
                    button
                    onClick={() => navigate(`/search?q=${encodeURIComponent(bid.title)}`)}
                  >
                    <ListItemText
                      primary={
                        <Box sx={{ display: 'flex', alignItems: 'center' }}>
                          <Typography variant="body1">{bid.title}</Typography>
                          <Chip
                            label={`${bid.ai_score}%`}
                            size="small"
                            color="success"
                            sx={{ ml: 1 }}
                          />
                        </Box>
                      }
                      secondary={
                        <Box>
                          <Typography variant="caption" display="block">
                            {bid.organization}
                          </Typography>
                          <Typography variant="caption" color="text.secondary">
                            {bid.match_reasons?.join(' • ')}
                          </Typography>
                        </Box>
                      }
                    />
                  </ListItem>
                ))}
              </List>
            )}
          </Paper>
        </Grid>
      </Grid>
    </Box>
  );
};

export default Dashboard;