import React from 'react';
import {
  Box,
  Grid,
  Typography,
  Paper,
  Divider,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
  LinearProgress,
  useTheme,
  alpha,
} from '@mui/material';
import {
  Analytics as AnalyticsIcon,
  TrendingUp,
  AttachMoney,
  CheckCircleOutline,
  FiberNew,
  ShowChart,
  BarChart as BarChartIcon,
  Business,
  PieChart as PieChartIcon,
  LocationOn,
} from '@mui/icons-material';
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
  Legend,
} from 'recharts';
import { StatCard, PageHeader, SkeletonCard } from '../components/common';
import apiClient from '../services/api';
import { CHART_COLORS, STAT_CARD_COLORS, getChartColor } from '../utils/colors';

// ---------------------------------------------------------------------------
// Local helpers
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

const ChartEmpty: React.FC<{ message?: string }> = ({ message = '데이터를 불러올 수 없습니다' }) => (
  <Box
    sx={{
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      height: 240,
      color: 'text.disabled',
    }}
  >
    <Typography variant="body2" color="text.disabled">
      {message}
    </Typography>
  </Box>
);

const TableEmpty: React.FC<{ message?: string }> = ({ message = '데이터를 불러올 수 없습니다' }) => (
  <Box sx={{ py: 4, textAlign: 'center' }}>
    <Typography variant="body2" color="text.disabled">
      {message}
    </Typography>
  </Box>
);

/** Format large numbers as Korean currency strings */
const formatKRW = (value: number): string => {
  if (!value || isNaN(value)) return '—';
  if (value >= 1_000_000_000_000) return `${(value / 1_000_000_000_000).toFixed(1)}조`;
  if (value >= 100_000_000) return `${(value / 100_000_000).toFixed(0)}억`;
  if (value >= 10_000) return `${(value / 10_000).toFixed(0)}만`;
  return value.toLocaleString();
};

// ---------------------------------------------------------------------------
// Placeholder data builders (used when API returns empty/error)
// ---------------------------------------------------------------------------

const buildMonthlyPlaceholder = () => [
  { month: '9월', count: 0 },
  { month: '10월', count: 0 },
  { month: '11월', count: 0 },
  { month: '12월', count: 0 },
  { month: '1월', count: 0 },
  { month: '2월', count: 0 },
];

// ---------------------------------------------------------------------------
// Main component
// ---------------------------------------------------------------------------

const Analytics: React.FC = () => {
  const theme = useTheme();

  // Fetch dashboard overview for summary stats
  const { data: overview, isLoading: overviewLoading } = useQuery({
    queryKey: ['analyticsOverview'],
    queryFn: () => apiClient.getDashboardOverview(),
    retry: 1,
  });

  // Fetch 30-day statistics for charts
  const { data: statistics, isLoading: statsLoading } = useQuery({
    queryKey: ['analyticsStatistics30d'],
    queryFn: () => apiClient.getBidStatistics('30d'),
    retry: 1,
  });

  const isLoading = overviewLoading || statsLoading;

  // Derived data with safe fallbacks
  const dailyStats: any[] = React.useMemo(() => statistics?.daily_stats || [], [statistics]);
  const categoryData: any[] = React.useMemo(() => statistics?.category_distribution || [], [statistics]);
  const totalBids: number = overview?.totalBids ?? 0;
  const activeBids: number = overview?.activeBids ?? 0;
  const avgPrice: number = overview?.avgPrice ?? 0;

  // Monthly trend — aggregate daily_stats by month if available, else placeholder
  const monthlyTrend: { month: string; count: number }[] = React.useMemo(() => {
    if (!dailyStats || dailyStats.length === 0) return buildMonthlyPlaceholder();
    const map = new Map<string, number>();
    dailyStats.forEach((d: any) => {
      const dateStr: string = d.date || '';
      if (!dateStr) return;
      // e.g. "2026-01-15" → "1월"
      const parts = dateStr.split('-');
      const monthLabel = parts[1] ? `${parseInt(parts[1], 10)}월` : dateStr;
      map.set(monthLabel, (map.get(monthLabel) || 0) + (d.count || 0));
    });
    return Array.from(map.entries()).map(([month, count]) => ({ month, count }));
  }, [dailyStats]);

  // Category bar chart data (top 8)
  const categoryBarData = categoryData.slice(0, 8).map((c: any) => ({
    name: c.category || c.name || '기타',
    count: c.count || 0,
  }));

  // Top organizations — derived from statistics or synthetic
  const topOrganizations: { org: string; count: number; ratio: number }[] = React.useMemo(() => {
    const orgs: any[] = statistics?.top_organizations || [];
    if (orgs.length === 0) return [];
    const maxCount = orgs[0]?.count || 1;
    return orgs.slice(0, 10).map((o: any) => ({
      org: o.organization || o.org || '—',
      count: o.count || 0,
      ratio: Math.round(((o.count || 0) / maxCount) * 100),
    }));
  }, [statistics]);

  // Price range distribution
  const priceRanges: { label: string; count: number }[] = React.useMemo(() => {
    return statistics?.price_distribution || [];
  }, [statistics]);

  // Regional data
  const regionalData: { region: string; count: number }[] = React.useMemo(() => {
    const regions: any[] = statistics?.regional_distribution || [];
    if (regions.length === 0) return [];
    return regions.slice(0, 10).map((r: any) => ({
      region: r.region || '—',
      count: r.count || 0,
    }));
  }, [statistics]);

  // New this week — approximate from last 7 days of daily_stats
  const newThisWeek = React.useMemo(() => {
    if (!dailyStats || dailyStats.length === 0) return 0;
    const last7 = dailyStats.slice(-7);
    return last7.reduce((sum: number, d: any) => sum + (d.count || 0), 0);
  }, [dailyStats]);

  // ---------- Loading skeleton ----------
  if (isLoading) {
    return (
      <Box>
        <PageHeader
          title="데이터 분석"
          subtitle="입찰 데이터 트렌드와 시장 분석을 확인하세요"
          icon={<AnalyticsIcon />}
        />
        <Grid container spacing={3} sx={{ mb: 3 }}>
          {[0, 1, 2, 3].map((i) => (
            <Grid item xs={12} sm={6} md={3} key={i}>
              <SkeletonCard variant="stat" />
            </Grid>
          ))}
        </Grid>
        <Grid container spacing={3}>
          <Grid item xs={12} md={7}>
            <SkeletonCard variant="content" />
          </Grid>
          <Grid item xs={12} md={5}>
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
        title="데이터 분석"
        subtitle="입찰 데이터 트렌드와 시장 분석을 확인하세요"
        icon={<AnalyticsIcon />}
      />

      {/* ------------------------------------------------------------------ */}
      {/* Section 2: Summary Stat Cards                                        */}
      {/* ------------------------------------------------------------------ */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="총 공고 수"
            value={totalBids.toLocaleString()}
            icon={<TrendingUp />}
            iconBg={STAT_CARD_COLORS.total.bg}
            iconColor={STAT_CARD_COLORS.total.color}
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="평균 예정가격"
            value={formatKRW(avgPrice)}
            icon={<AttachMoney />}
            iconBg={STAT_CARD_COLORS.info.bg}
            iconColor={STAT_CARD_COLORS.info.color}
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="활성 공고"
            value={activeBids.toLocaleString()}
            icon={<CheckCircleOutline />}
            iconBg={STAT_CARD_COLORS.active.bg}
            iconColor={STAT_CARD_COLORS.active.color}
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="이번 주 신규"
            value={newThisWeek.toLocaleString()}
            icon={<FiberNew />}
            iconBg={STAT_CARD_COLORS.warning.bg}
            iconColor={STAT_CARD_COLORS.warning.color}
          />
        </Grid>
      </Grid>

      {/* ------------------------------------------------------------------ */}
      {/* Section 3: Charts Row                                                */}
      {/* ------------------------------------------------------------------ */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        {/* Monthly trend line chart */}
        <Grid item xs={12} md={7}>
          <SectionPaper>
            <SectionHeader
              icon={<ShowChart />}
              title="월별 입찰 추이"
              subtitle="최근 수집된 입찰공고의 월별 건수 현황"
            />
            <Divider sx={{ mb: 3 }} />
            {monthlyTrend.every((d) => d.count === 0) ? (
              <ChartEmpty />
            ) : (
              <ResponsiveContainer width="100%" height={260}>
                <LineChart data={monthlyTrend} margin={{ top: 4, right: 8, bottom: 0, left: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke={theme.palette.divider} />
                  <XAxis
                    dataKey="month"
                    stroke={theme.palette.text.secondary}
                    tick={{ fontSize: 12 }}
                  />
                  <YAxis
                    stroke={theme.palette.text.secondary}
                    tick={{ fontSize: 12 }}
                    width={36}
                  />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: theme.palette.background.paper,
                      border: '1px solid ' + theme.palette.divider,
                      borderRadius: 8,
                      fontSize: 13,
                    }}
                    formatter={(value: any) => [`${value}건`, '입찰 건수']}
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

        {/* Category distribution bar chart */}
        <Grid item xs={12} md={5}>
          <SectionPaper>
            <SectionHeader
              icon={<BarChartIcon />}
              title="카테고리별 분석"
              subtitle="카테고리별 입찰공고 건수 분포"
            />
            <Divider sx={{ mb: 3 }} />
            {categoryBarData.length === 0 ? (
              <ChartEmpty />
            ) : (
              <ResponsiveContainer width="100%" height={260}>
                <BarChart
                  data={categoryBarData}
                  layout="vertical"
                  margin={{ top: 0, right: 8, bottom: 0, left: 8 }}
                >
                  <CartesianGrid strokeDasharray="3 3" stroke={theme.palette.divider} horizontal={false} />
                  <XAxis
                    type="number"
                    stroke={theme.palette.text.secondary}
                    tick={{ fontSize: 11 }}
                  />
                  <YAxis
                    type="category"
                    dataKey="name"
                    stroke={theme.palette.text.secondary}
                    tick={{ fontSize: 11 }}
                    width={56}
                  />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: theme.palette.background.paper,
                      border: '1px solid ' + theme.palette.divider,
                      borderRadius: 8,
                      fontSize: 13,
                    }}
                    formatter={(value: any) => [`${value}건`, '건수']}
                  />
                  <Bar dataKey="count" radius={[0, 4, 4, 0]}>
                    {categoryBarData.map((_: any, index: number) => (
                      <Cell key={`cell-${index}`} fill={getChartColor(index)} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            )}
          </SectionPaper>
        </Grid>
      </Grid>

      {/* ------------------------------------------------------------------ */}
      {/* Section 4: Analysis Tables Row                                       */}
      {/* ------------------------------------------------------------------ */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        {/* Top organizations table */}
        <Grid item xs={12} md={6}>
          <SectionPaper>
            <SectionHeader
              icon={<Business />}
              title="발주기관 TOP 10"
              subtitle="입찰공고 건수 기준 상위 발주기관"
              action={
                <Chip
                  label="최근 30일"
                  size="small"
                  sx={{
                    fontSize: '0.72rem',
                    fontWeight: 600,
                    bgcolor: (t) => alpha(t.palette.primary.main, 0.08),
                    color: 'primary.main',
                  }}
                />
              }
            />
            <Divider sx={{ mb: 1 }} />
            {topOrganizations.length === 0 ? (
              <TableEmpty />
            ) : (
              <TableContainer>
                <Table size="small">
                  <TableHead>
                    <TableRow>
                      <TableCell sx={{ fontWeight: 700, fontSize: '0.75rem', color: 'text.secondary', width: 28 }}>
                        #
                      </TableCell>
                      <TableCell sx={{ fontWeight: 700, fontSize: '0.75rem', color: 'text.secondary' }}>
                        기관명
                      </TableCell>
                      <TableCell align="right" sx={{ fontWeight: 700, fontSize: '0.75rem', color: 'text.secondary', width: 52 }}>
                        건수
                      </TableCell>
                      <TableCell sx={{ fontWeight: 700, fontSize: '0.75rem', color: 'text.secondary', width: 100 }}>
                        비율
                      </TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {topOrganizations.map((row, idx) => (
                      <TableRow key={row.org} sx={{ '&:last-child td': { border: 0 } }}>
                        <TableCell sx={{ fontSize: '0.8rem', color: 'text.disabled', fontWeight: 600 }}>
                          {idx + 1}
                        </TableCell>
                        <TableCell sx={{ fontSize: '0.8rem', fontWeight: 500 }}>
                          {row.org}
                        </TableCell>
                        <TableCell align="right" sx={{ fontSize: '0.8rem', fontWeight: 600 }}>
                          {row.count.toLocaleString()}
                        </TableCell>
                        <TableCell>
                          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                            <LinearProgress
                              variant="determinate"
                              value={row.ratio}
                              sx={{
                                flex: 1,
                                height: 6,
                                borderRadius: 3,
                                bgcolor: (t) => alpha(t.palette.primary.main, 0.1),
                                '& .MuiLinearProgress-bar': {
                                  borderRadius: 3,
                                  bgcolor: getChartColor(idx),
                                },
                              }}
                            />
                            <Typography variant="caption" color="text.secondary" sx={{ width: 32, textAlign: 'right', fontWeight: 500 }}>
                              {row.ratio}%
                            </Typography>
                          </Box>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            )}
          </SectionPaper>
        </Grid>

        {/* Price range distribution */}
        <Grid item xs={12} md={6}>
          <SectionPaper>
            <SectionHeader
              icon={<PieChartIcon />}
              title="가격대 분포"
              subtitle="예정가격 범위별 입찰공고 비율"
              action={
                <Chip
                  label="전체 기간"
                  size="small"
                  sx={{
                    fontSize: '0.72rem',
                    fontWeight: 600,
                    bgcolor: (t) => alpha(t.palette.info.main, 0.08),
                    color: 'info.main',
                  }}
                />
              }
            />
            <Divider sx={{ mb: 3 }} />
            {priceRanges.length === 0 ? (
              <ChartEmpty />
            ) : (
              <ResponsiveContainer width="100%" height={240}>
                <PieChart>
                  <Pie
                    data={priceRanges}
                    cx="50%"
                    cy="44%"
                    outerRadius={82}
                    innerRadius={32}
                    dataKey="count"
                    nameKey="label"
                    labelLine={false}
                    label={({ percent }) => `${(percent * 100).toFixed(0)}%`}
                  >
                    {priceRanges.map((_: any, index: number) => (
                      <Cell key={`price-cell-${index}`} fill={getChartColor(index)} />
                    ))}
                  </Pie>
                  <Tooltip
                    formatter={(value: any, _: any, props: any) => [
                      `${value}건`,
                      props.payload.label,
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
                    formatter={(value: any, entry: any) =>
                      `${entry.payload.label} (${(entry.payload.count || 0).toLocaleString()}건)`
                    }
                    wrapperStyle={{ fontSize: 11 }}
                  />
                </PieChart>
              </ResponsiveContainer>
            )}
          </SectionPaper>
        </Grid>
      </Grid>

      {/* ------------------------------------------------------------------ */}
      {/* Section 5: Regional Analysis                                         */}
      {/* ------------------------------------------------------------------ */}
      <Grid container spacing={3}>
        <Grid item xs={12}>
          <SectionPaper>
            <SectionHeader
              icon={<LocationOn />}
              title="지역별 분석"
              subtitle="지역별 입찰공고 건수 현황"
            />
            <Divider sx={{ mb: 3 }} />
            {regionalData.length === 0 ? (
              <ChartEmpty message="지역별 데이터를 불러올 수 없습니다" />
            ) : (
              <ResponsiveContainer width="100%" height={300}>
                <BarChart
                  data={regionalData}
                  layout="vertical"
                  margin={{ top: 0, right: 16, bottom: 0, left: 16 }}
                >
                  <CartesianGrid strokeDasharray="3 3" stroke={theme.palette.divider} horizontal={false} />
                  <XAxis
                    type="number"
                    stroke={theme.palette.text.secondary}
                    tick={{ fontSize: 12 }}
                  />
                  <YAxis
                    type="category"
                    dataKey="region"
                    stroke={theme.palette.text.secondary}
                    tick={{ fontSize: 12 }}
                    width={72}
                  />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: theme.palette.background.paper,
                      border: '1px solid ' + theme.palette.divider,
                      borderRadius: 8,
                      fontSize: 13,
                    }}
                    formatter={(value: any) => [`${value}건`, '입찰 건수']}
                  />
                  <Bar dataKey="count" radius={[0, 4, 4, 0]} maxBarSize={24}>
                    {regionalData.map((_: any, index: number) => (
                      <Cell key={`region-cell-${index}`} fill={getChartColor(index)} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            )}
          </SectionPaper>
        </Grid>
      </Grid>
    </Box>
  );
};

export default Analytics;
