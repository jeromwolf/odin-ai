import React, { useEffect, useState } from 'react';
import {
  Box,
  Grid,
  Typography,
  Chip,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Paper,
  Button,
  Divider,
  LinearProgress,
  useTheme,
  alpha,
} from '@mui/material';
import {
  TrendingUp,
  AccessTime,
  Bookmark,
  ArrowForward,
  Business,
  Dashboard as DashboardIcon,
  Warning,
  Star,
  Search,
  NotificationsActive,
  BookmarkBorder,
  ErrorOutline,
  ScheduleOutlined,
  AutoAwesome,
  ShowChart,
  DonutLarge,
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

// ---------------------------------------------------------------------------
// Section header component — title + subtitle + optional divider
// ---------------------------------------------------------------------------
interface SectionHeaderProps {
  icon: React.ReactNode;
  title: string;
  subtitle?: string;
  action?: React.ReactNode;
}

const SectionHeader: React.FC<SectionHeaderProps> = ({ icon, title, subtitle, action }) => (
  <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.25 }}>
      <Box
        sx={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          width: 32,
          height: 32,
          borderRadius: '8px',
          bgcolor: (t) => alpha(t.palette.primary.main, 0.1),
          color: 'primary.main',
          flexShrink: 0,
          '& .MuiSvgIcon-root': { fontSize: 18 },
        }}
      >
        {icon}
      </Box>
      <Box>
        <Typography variant="h6" fontWeight={700} lineHeight={1.2}>
          {title}
        </Typography>
        {subtitle && (
          <Typography variant="caption" color="text.secondary" lineHeight={1.4}>
            {subtitle}
          </Typography>
        )}
      </Box>
    </Box>
    {action && <Box>{action}</Box>}
  </Box>
);

// ---------------------------------------------------------------------------
// Empty state for lists (compact variant)
// ---------------------------------------------------------------------------
interface InlineEmptyProps {
  icon: React.ReactNode;
  message: string;
}

const InlineEmpty: React.FC<InlineEmptyProps> = ({ icon, message }) => (
  <Box
    sx={{
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      py: 5,
      color: 'text.disabled',
    }}
  >
    <Box sx={{ '& .MuiSvgIcon-root': { fontSize: 44 } }}>{icon}</Box>
    <Typography variant="body2" color="text.disabled" mt={1.5} fontWeight={500}>
      {message}
    </Typography>
  </Box>
);

// ---------------------------------------------------------------------------
// Empty state for charts (compact variant)
// ---------------------------------------------------------------------------
const ChartEmpty: React.FC<{ message: string }> = ({ message }) => (
  <Box
    sx={{
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      height: 260,
      color: 'text.disabled',
    }}
  >
    <Typography variant="body2" color="text.disabled">
      {message}
    </Typography>
  </Box>
);

// ---------------------------------------------------------------------------
// Paper wrapper with consistent styling
// ---------------------------------------------------------------------------
const SectionPaper: React.FC<{ children: React.ReactNode; sx?: object }> = ({ children, sx }) => (
  <Paper
    elevation={0}
    sx={{
      p: 3,
      border: '1px solid',
      borderColor: 'divider',
      borderRadius: '14px',
      height: '100%',
      boxSizing: 'border-box',
      ...sx,
    }}
  >
    {children}
  </Paper>
);

// ---------------------------------------------------------------------------
// Quick action button
// ---------------------------------------------------------------------------
interface QuickActionProps {
  icon: React.ReactNode;
  label: string;
  onClick: () => void;
  color?: string;
}

const QuickAction: React.FC<QuickActionProps> = ({ icon, label, onClick, color }) => (
  <Button
    variant="outlined"
    startIcon={icon}
    onClick={onClick}
    sx={{
      borderRadius: '10px',
      textTransform: 'none',
      fontWeight: 600,
      fontSize: '0.8125rem',
      py: 1,
      px: 2,
      color: color || 'text.primary',
      borderColor: 'divider',
      '&:hover': {
        borderColor: color || 'primary.main',
        bgcolor: color ? `${color}0D` : (t: any) => alpha(t.palette.primary.main, 0.05),
      },
    }}
  >
    {label}
  </Button>
);

// ---------------------------------------------------------------------------
// Main component
// ---------------------------------------------------------------------------
const Dashboard: React.FC = () => {
  const navigate = useNavigate();
  const theme = useTheme();
  const [bookmarkedBids, setBookmarkedBids] = useState<Set<string>>(new Set());

  // 대시보드 개요 데이터
  const { data: overview, isLoading: overviewLoading } = useQuery({
    queryKey: ['dashboardOverview'],
    queryFn: () => apiClient.getDashboardOverview(),
    refetchInterval: 60000,
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

  const getUrgencyIconColor = (hours: number): string => {
    if (!hours || isNaN(hours)) return theme.palette.text.disabled;
    if (hours <= 24) return theme.palette.error.main;
    if (hours <= 72) return theme.palette.warning.main;
    return theme.palette.info.main;
  };

  const getDDayLabel = (hours: number): string => {
    if (!hours || isNaN(hours)) return '—';
    const days = Math.floor(hours / 24);
    if (days === 0) return 'D-DAY';
    return `D-${days}`;
  };

  const formatTimeRemaining = (hours: number) => {
    if (!hours || isNaN(hours)) return '시간 정보 없음';
    const days = Math.floor(hours / 24);
    const remainingHours = Math.floor(hours % 24);
    if (days > 0) return `${days}일 ${remainingHours}시간 남음`;
    return `${Math.floor(hours)}시간 남음`;
  };

  const statCardData = [
    {
      title: '오늘의 신규 입찰',
      value: overview?.data?.active_bids ?? 0,
      change: overview?.data?.today_new ?? 0,
      changeLabel: '전일 대비',
      icon: <TrendingUp />,
      iconBg: STAT_CARD_COLORS.total.bg,
      iconColor: STAT_CARD_COLORS.total.color,
    },
    {
      title: '마감 임박',
      value: deadlines?.data?.length || 0,
      icon: <AccessTime />,
      iconBg: STAT_CARD_COLORS.warning.bg,
      iconColor: STAT_CARD_COLORS.warning.color,
    },
    {
      title: '북마크',
      value: bookmarkedBids.size || 0,
      icon: <Bookmark />,
      iconBg: STAT_CARD_COLORS.total.bg,
      iconColor: STAT_CARD_COLORS.total.icon,
    },
    {
      title: 'AI 매칭',
      value: recommendations?.data?.length || 0,
      icon: <Business />,
      iconBg: STAT_CARD_COLORS.info.bg,
      iconColor: STAT_CARD_COLORS.info.color,
    },
  ];

  const deadlineList: any[] = (deadlines?.data || []).slice(0, 5);
  const recommendationList: any[] = (recommendations?.data || []);
  const trendData: any[] = statistics?.data?.daily_stats || [];
  const categoryData: any[] = (statistics?.data?.category_distribution?.slice(0, 5) || []);

  // ---------- Loading skeleton ----------
  if (overviewLoading || statsLoading) {
    return (
      <Box>
        <PageHeader
          title="대시보드"
          subtitle="실시간 입찰 현황을 확인하세요"
          icon={<DashboardIcon />}
        />
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
      {/* ------------------------------------------------------------------ */}
      {/* Page header                                                          */}
      {/* ------------------------------------------------------------------ */}
      <PageHeader
        title="대시보드"
        subtitle="실시간 입찰 현황을 확인하세요"
        icon={<DashboardIcon />}
      />

      {/* ------------------------------------------------------------------ */}
      {/* Stat cards                                                           */}
      {/* ------------------------------------------------------------------ */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        {statCardData.map((card, index) => (
          <Grid item xs={12} sm={6} md={3} key={index}>
            <StatCard {...card} />
          </Grid>
        ))}
      </Grid>

      {/* ------------------------------------------------------------------ */}
      {/* Quick actions                                                        */}
      {/* ------------------------------------------------------------------ */}
      <Box
        sx={{
          display: 'flex',
          gap: 1.5,
          flexWrap: 'wrap',
          mb: 4,
          pb: 4,
          borderBottom: '1px solid',
          borderColor: 'divider',
        }}
      >
        <QuickAction
          icon={<Search sx={{ fontSize: 18 }} />}
          label="공고 검색"
          onClick={() => navigate('/search')}
          color={theme.palette.primary.main}
        />
        <QuickAction
          icon={<BookmarkBorder sx={{ fontSize: 18 }} />}
          label="북마크 확인"
          onClick={() => navigate('/bookmarks')}
          color={theme.palette.info.main}
        />
        <QuickAction
          icon={<NotificationsActive sx={{ fontSize: 18 }} />}
          label="알림 설정"
          onClick={() => navigate('/notifications')}
          color={theme.palette.warning.main}
        />
      </Box>

      {/* ------------------------------------------------------------------ */}
      {/* Charts row                                                           */}
      {/* ------------------------------------------------------------------ */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        {/* 주간 입찰 트렌드 */}
        <Grid item xs={12} md={8}>
          <SectionPaper>
            <SectionHeader
              icon={<ShowChart />}
              title="주간 입찰 트렌드"
              subtitle="최근 7일간 신규 입찰공고 수집 현황"
            />
            <Divider sx={{ mb: 3 }} />
            {trendData.length === 0 ? (
              <ChartEmpty message="이번 주 수집된 데이터가 없습니다" />
            ) : (
              <ResponsiveContainer width="100%" height={260}>
                <LineChart data={trendData}>
                  <CartesianGrid strokeDasharray="3 3" stroke={theme.palette.divider} />
                  <XAxis
                    dataKey="date"
                    tickFormatter={(value) => format(parseISO(value), 'MM/dd')}
                    stroke={theme.palette.text.secondary}
                    tick={{ fontSize: 12 }}
                  />
                  <YAxis
                    stroke={theme.palette.text.secondary}
                    tick={{ fontSize: 12 }}
                    width={36}
                  />
                  <Tooltip
                    labelFormatter={(value) => format(parseISO(value as string), 'yyyy-MM-dd')}
                    contentStyle={{
                      backgroundColor: theme.palette.background.paper,
                      border: '1px solid ' + theme.palette.divider,
                      borderRadius: 8,
                      fontSize: 13,
                    }}
                  />
                  <Line
                    type="monotone"
                    dataKey="count"
                    stroke={CHART_COLORS[0]}
                    strokeWidth={2.5}
                    dot={{ r: 4, fill: CHART_COLORS[0], strokeWidth: 2, stroke: '#fff' }}
                    activeDot={{ r: 6 }}
                    name="입찰 건수"
                  />
                </LineChart>
              </ResponsiveContainer>
            )}
          </SectionPaper>
        </Grid>

        {/* 카테고리별 분포 */}
        <Grid item xs={12} md={4}>
          <SectionPaper>
            <SectionHeader
              icon={<DonutLarge />}
              title="카테고리 분포"
              subtitle="클릭하면 해당 카테고리 검색"
            />
            <Divider sx={{ mb: 3 }} />
            {categoryData.length === 0 ? (
              <ChartEmpty message="카테고리 데이터가 없습니다" />
            ) : (
              <ResponsiveContainer width="100%" height={280}>
                <PieChart>
                  <Pie
                    data={categoryData}
                    cx="50%"
                    cy="42%"
                    labelLine={false}
                    outerRadius={72}
                    innerRadius={28}
                    fill={CHART_COLORS[0]}
                    dataKey="count"
                    label={({ percent }) => `${(percent * 100).toFixed(0)}%`}
                    onClick={(data: any) => {
                      if (data && data.category) {
                        navigate(`/search?q=${encodeURIComponent(data.category)}`);
                      }
                    }}
                  >
                    {categoryData.map((entry: any, index: number) => (
                      <Cell
                        key={`cell-${index}`}
                        fill={getChartColor(index)}
                        style={{ cursor: 'pointer' }}
                      />
                    ))}
                  </Pie>
                  <Tooltip
                    formatter={(value: any, name: any, props: any) => [
                      `${value}건`,
                      props.payload.category,
                    ]}
                    contentStyle={{
                      backgroundColor: theme.palette.background.paper,
                      border: '1px solid ' + theme.palette.divider,
                      borderRadius: 8,
                      fontSize: 13,
                    }}
                  />
                  <Legend
                    verticalAlign="bottom"
                    height={36}
                    formatter={(value, entry: any) =>
                      `${entry.payload.category} (${entry.payload.count}건)`
                    }
                    wrapperStyle={{ fontSize: 12 }}
                  />
                </PieChart>
              </ResponsiveContainer>
            )}
          </SectionPaper>
        </Grid>
      </Grid>

      {/* ------------------------------------------------------------------ */}
      {/* Lists row                                                            */}
      {/* ------------------------------------------------------------------ */}
      <Grid container spacing={3}>
        {/* 마감 임박 입찰 */}
        <Grid item xs={12} md={6}>
          <SectionPaper>
            <SectionHeader
              icon={<ScheduleOutlined />}
              title="마감 임박 공고"
              subtitle="7일 이내 마감 예정 입찰"
              action={
                <Button
                  size="small"
                  endIcon={<ArrowForward sx={{ fontSize: 15 }} />}
                  onClick={() => navigate('/search')}
                  sx={{
                    textTransform: 'none',
                    fontWeight: 600,
                    fontSize: '0.8rem',
                    color: 'text.secondary',
                    '&:hover': { color: 'primary.main' },
                  }}
                >
                  더 보기
                </Button>
              }
            />
            <Divider sx={{ mb: 1 }} />

            {deadlinesLoading ? (
              <FullscreenLoading size={24} />
            ) : deadlineList.length === 0 ? (
              <InlineEmpty
                icon={<ErrorOutline />}
                message="마감 임박 입찰이 없습니다"
              />
            ) : (
              <List disablePadding>
                {deadlineList.map((bid: any, idx: number) => {
                  const urgencyColor = getUrgencyIconColor(bid.hours_remaining);
                  const isLast = idx === deadlineList.length - 1;
                  return (
                    <React.Fragment key={bid.bid_id}>
                      <ListItem
                        button
                        onClick={() => navigate(`/search?q=${encodeURIComponent(bid.title)}`)}
                        sx={{
                          borderRadius: '8px',
                          px: 1,
                          py: 1,
                          '&:hover': { bgcolor: 'action.hover' },
                        }}
                      >
                        <ListItemIcon sx={{ minWidth: 36 }}>
                          <Warning sx={{ fontSize: 20, color: urgencyColor }} />
                        </ListItemIcon>
                        <ListItemText
                          primary={
                            <Typography
                              variant="body2"
                              fontWeight={600}
                              noWrap
                              title={bid.title}
                              sx={{ pr: 1 }}
                            >
                              {bid.title}
                            </Typography>
                          }
                          secondary={
                            <Typography
                              variant="caption"
                              color="text.secondary"
                              component="span"
                              noWrap
                            >
                              {bid.organization}
                            </Typography>
                          }
                        />
                        <Box
                          sx={{
                            display: 'flex',
                            flexDirection: 'column',
                            alignItems: 'flex-end',
                            gap: 0.5,
                            flexShrink: 0,
                            ml: 1,
                          }}
                        >
                          <Chip
                            label={getDDayLabel(bid.hours_remaining)}
                            size="small"
                            sx={{
                              fontWeight: 700,
                              fontSize: '0.7rem',
                              height: 20,
                              bgcolor: alpha(urgencyColor, 0.12),
                              color: urgencyColor,
                              border: 'none',
                            }}
                          />
                          <Typography
                            variant="caption"
                            color="text.disabled"
                            sx={{ whiteSpace: 'nowrap', fontSize: '0.68rem' }}
                          >
                            {formatTimeRemaining(bid.hours_remaining)}
                          </Typography>
                        </Box>
                      </ListItem>
                      {!isLast && (
                        <Divider
                          component="li"
                          sx={{ mx: 1, borderColor: 'divider' }}
                        />
                      )}
                    </React.Fragment>
                  );
                })}
              </List>
            )}
          </SectionPaper>
        </Grid>

        {/* AI 추천 입찰 */}
        <Grid item xs={12} md={6}>
          <SectionPaper>
            <SectionHeader
              icon={<AutoAwesome />}
              title="AI 추천 공고"
              subtitle="관심 분야와 매칭된 추천 입찰"
              action={
                <Chip
                  label="개인화 매칭"
                  color="primary"
                  size="small"
                  sx={{ fontWeight: 600, fontSize: '0.72rem' }}
                />
              }
            />
            <Divider sx={{ mb: 1 }} />

            {recommendationsLoading ? (
              <FullscreenLoading size={24} />
            ) : recommendationList.length === 0 ? (
              <InlineEmpty
                icon={<Star />}
                message="추천 입찰이 없습니다"
              />
            ) : (
              <>
                <List disablePadding>
                  {recommendationList.map((bid: any, idx: number) => {
                    const score = bid.score ?? 0;
                    const isLast = idx === recommendationList.length - 1;
                    return (
                      <React.Fragment key={bid.bid_id}>
                        <ListItem
                          button
                          onClick={() => navigate(`/search?q=${encodeURIComponent(bid.title)}`)}
                          sx={{
                            borderRadius: '8px',
                            px: 1,
                            py: 1,
                            '&:hover': { bgcolor: 'action.hover' },
                          }}
                        >
                          <ListItemIcon sx={{ minWidth: 36 }}>
                            <Star
                              sx={{
                                fontSize: 20,
                                color:
                                  score >= 80
                                    ? theme.palette.warning.main
                                    : theme.palette.primary.main,
                              }}
                            />
                          </ListItemIcon>
                          <ListItemText
                            primary={
                              <Typography
                                variant="body2"
                                fontWeight={600}
                                noWrap
                                title={bid.title}
                                sx={{ pr: 1 }}
                              >
                                {bid.title}
                              </Typography>
                            }
                            secondary={
                              <Box component="span">
                                <Typography
                                  variant="caption"
                                  color="text.secondary"
                                  component="span"
                                  display="block"
                                  noWrap
                                >
                                  {bid.organization}
                                </Typography>
                                {bid.reason && (
                                  <Typography
                                    variant="caption"
                                    color="text.disabled"
                                    component="span"
                                    display="block"
                                    noWrap
                                    sx={{ fontSize: '0.68rem' }}
                                  >
                                    {[bid.reason].join(' · ')}
                                  </Typography>
                                )}
                              </Box>
                            }
                          />
                          <Box
                            sx={{
                              display: 'flex',
                              flexDirection: 'column',
                              alignItems: 'flex-end',
                              gap: 0.75,
                              flexShrink: 0,
                              ml: 1,
                              width: 60,
                            }}
                          >
                            <Typography
                              variant="caption"
                              fontWeight={700}
                              sx={{
                                color:
                                  score >= 80
                                    ? theme.palette.success.main
                                    : theme.palette.primary.main,
                                fontSize: '0.75rem',
                              }}
                            >
                              {score}%
                            </Typography>
                            <LinearProgress
                              variant="determinate"
                              value={score}
                              sx={{
                                width: '100%',
                                height: 4,
                                borderRadius: 2,
                                bgcolor: (t) => alpha(t.palette.primary.main, 0.12),
                                '& .MuiLinearProgress-bar': {
                                  borderRadius: 2,
                                  bgcolor:
                                    score >= 80
                                      ? theme.palette.success.main
                                      : theme.palette.primary.main,
                                },
                              }}
                            />
                          </Box>
                        </ListItem>
                        {!isLast && (
                          <Divider
                            component="li"
                            sx={{ mx: 1, borderColor: 'divider' }}
                          />
                        )}
                      </React.Fragment>
                    );
                  })}
                </List>

                {/* See more link */}
                <Box sx={{ mt: 2, pt: 1.5, borderTop: '1px solid', borderColor: 'divider', textAlign: 'right' }}>
                  <Button
                    size="small"
                    endIcon={<ArrowForward sx={{ fontSize: 15 }} />}
                    onClick={() => navigate('/search')}
                    sx={{
                      textTransform: 'none',
                      fontWeight: 600,
                      fontSize: '0.8rem',
                      color: 'text.secondary',
                      '&:hover': { color: 'primary.main' },
                    }}
                  >
                    더 보기
                  </Button>
                </Box>
              </>
            )}
          </SectionPaper>
        </Grid>
      </Grid>
    </Box>
  );
};

export default Dashboard;
