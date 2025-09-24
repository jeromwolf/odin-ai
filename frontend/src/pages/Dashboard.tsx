import React, { useEffect, useState } from 'react';
import {
  Box,
  Grid,
  Card,
  CardContent,
  Typography,
  CircularProgress,
  Alert,
  Chip,
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
  IconButton,
  Paper,
  Button,
} from '@mui/material';
import {
  TrendingUp,
  TrendingDown,
  AccessTime,
  BookmarkBorder,
  Bookmark,
  ArrowForward,
  CalendarToday,
  Business,
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
} from 'recharts';
import { format, parseISO } from 'date-fns';
import apiClient from '../services/api';

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884D8'];

interface StatCard {
  title: string;
  value: number | string;
  trend?: number;
  icon: React.ReactNode;
  color: string;
}

const Dashboard: React.FC = () => {
  const navigate = useNavigate();
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

  const handleBookmarkToggle = async (bidId: string) => {
    try {
      if (bookmarkedBids.has(bidId)) {
        await apiClient.removeBookmark(bidId);
        setBookmarkedBids((prev) => {
          const newSet = new Set(prev);
          newSet.delete(bidId);
          return newSet;
        });
      } else {
        await apiClient.addBookmark(bidId);
        setBookmarkedBids((prev) => new Set(prev).add(bidId));
      }
    } catch (error) {
      console.error('북마크 처리 실패:', error);
    }
  };

  const getUrgencyColor = (hours: number) => {
    if (hours <= 24) return 'error';
    if (hours <= 72) return 'warning';
    return 'info';
  };

  const statCards: StatCard[] = [
    {
      title: '오늘의 신규 입찰',
      value: overview?.today_stats?.new_bids || 0,
      trend: overview?.weekly_trend?.trend_percentage,
      icon: <TrendingUp />,
      color: '#4caf50',
    },
    {
      title: '마감 임박',
      value: overview?.today_stats?.upcoming_deadlines || 0,
      icon: <AccessTime />,
      color: '#ff9800',
    },
    {
      title: '북마크',
      value: overview?.today_stats?.bookmarks || 0,
      icon: <Bookmark />,
      color: '#2196f3',
    },
    {
      title: 'AI 매칭',
      value: overview?.today_stats?.matched_bids || 0,
      icon: <Business />,
      color: '#9c27b0',
    },
  ];

  if (overviewLoading || statsLoading) {
    return (
      <Box
        sx={{
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          height: '80vh',
        }}
      >
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box>
      <Typography variant="h4" sx={{ mb: 3 }}>
        대시보드
      </Typography>

      {/* 통계 카드 */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        {statCards.map((card, index) => (
          <Grid item xs={12} sm={6} md={3} key={index}>
            <Card>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                  <Box
                    sx={{
                      p: 1,
                      borderRadius: 1,
                      backgroundColor: `${card.color}20`,
                      color: card.color,
                      mr: 2,
                    }}
                  >
                    {card.icon}
                  </Box>
                  <Typography variant="body2" color="text.secondary">
                    {card.title}
                  </Typography>
                </Box>
                <Typography variant="h4">{card.value}</Typography>
                {card.trend && (
                  <Box sx={{ display: 'flex', alignItems: 'center', mt: 1 }}>
                    {card.trend > 0 ? (
                      <TrendingUp color="success" fontSize="small" />
                    ) : (
                      <TrendingDown color="error" fontSize="small" />
                    )}
                    <Typography
                      variant="body2"
                      color={card.trend > 0 ? 'success.main' : 'error.main'}
                      sx={{ ml: 0.5 }}
                    >
                      {Math.abs(card.trend)}%
                    </Typography>
                  </Box>
                )}
              </CardContent>
            </Card>
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
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis
                  dataKey="date"
                  tickFormatter={(value) => format(parseISO(value), 'MM/dd')}
                />
                <YAxis />
                <Tooltip
                  labelFormatter={(value) => format(parseISO(value as string), 'yyyy-MM-dd')}
                />
                <Line
                  type="monotone"
                  dataKey="count"
                  stroke="#8884d8"
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
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={statistics?.category_distribution?.slice(0, 5) || []}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="count"
                  label={({ category, percentage }) => `${category} (${percentage}%)`}
                >
                  {statistics?.category_distribution?.slice(0, 5).map((entry: any, index: number) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
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
                onClick={() => navigate('/bids')}
              >
                전체보기
              </Button>
            </Box>
            {deadlinesLoading ? (
              <CircularProgress />
            ) : (
              <List>
                {(deadlines?.deadlines || []).slice(0, 5).map((bid: any) => (
                  <ListItem
                    key={bid.id || bid.bid_id}
                    button
                    onClick={() => navigate(`/bids/${bid.id || bid.bid_id}`)}
                  >
                    <ListItemText
                      primary={bid.title}
                      secondary={
                        <Box>
                          <Typography variant="caption" display="block">
                            {bid.organization}
                          </Typography>
                          <Chip
                            label={`${bid.hours_remaining}시간 남음`}
                            size="small"
                            color={getUrgencyColor(bid.hours_remaining)}
                            sx={{ mt: 0.5 }}
                          />
                        </Box>
                      }
                    />
                    <ListItemSecondaryAction>
                      <IconButton
                        edge="end"
                        onClick={(e) => {
                          e.stopPropagation();
                          handleBookmarkToggle(bid.bid_id);
                        }}
                      >
                        {bid.is_bookmarked || bookmarkedBids.has(bid.bid_id) ? (
                          <Bookmark color="primary" />
                        ) : (
                          <BookmarkBorder />
                        )}
                      </IconButton>
                    </ListItemSecondaryAction>
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
              <CircularProgress />
            ) : (
              <List>
                {(recommendations?.recommendations || []).map((bid: any) => (
                  <ListItem
                    key={bid.id || bid.bid_id}
                    button
                    onClick={() => navigate(`/bids/${bid.id || bid.bid_id}`)}
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
                    <ListItemSecondaryAction>
                      <IconButton
                        edge="end"
                        onClick={(e) => {
                          e.stopPropagation();
                          handleBookmarkToggle(bid.bid_id);
                        }}
                      >
                        {bid.is_bookmarked || bookmarkedBids.has(bid.bid_id) ? (
                          <Bookmark color="primary" />
                        ) : (
                          <BookmarkBorder />
                        )}
                      </IconButton>
                    </ListItemSecondaryAction>
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