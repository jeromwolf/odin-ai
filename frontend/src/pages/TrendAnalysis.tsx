import React, { useState, useEffect, useCallback } from 'react';
import {
  Box,
  Paper,
  Typography,
  Tabs,
  Tab,
  Grid,
  CircularProgress,
  Alert,
  alpha,
  Divider,
  useTheme,
} from '@mui/material';
import {
  TrendingUp,
  LocalOffer,
  Category,
  AttachMoney,
  Business,
} from '@mui/icons-material';
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';
import { useNavigate } from 'react-router-dom';
import apiClient from '../services/api';
import { CHART_COLORS, getChartColor } from '../utils/colors';

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------
type PeriodKey = 'day' | 'week' | 'month' | 'year';

interface TrendPoint {
  period: string;
  count: number;
}

interface KeywordStat {
  keyword: string;
  count: number;
}

interface CategoryStat {
  category: string;
  count: number;
  percentage?: number;
}

interface OrgStat {
  organization: string;
  count: number;
  total_price?: number;
}

interface PriceRange {
  range: string;
  count: number;
}

interface TrendsData {
  trends: TrendPoint[];
  top_keywords: KeywordStat[];
  period: string;
  interval: string;
}

interface StatisticsData {
  daily_stats: any[];
  category_distribution: CategoryStat[];
  organization_stats: OrgStat[];
  price_distribution: PriceRange[];
}

// ---------------------------------------------------------------------------
// Sub-components
// ---------------------------------------------------------------------------

/** Consistent section header with icon badge */
interface SectionHeaderProps {
  icon: React.ReactNode;
  title: string;
  subtitle?: string;
}

const SectionHeader: React.FC<SectionHeaderProps> = ({ icon, title, subtitle }) => {
  const theme = useTheme();
  return (
    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.25, mb: 2 }}>
      <Box
        sx={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          width: 32,
          height: 32,
          borderRadius: '8px',
          bgcolor: alpha(theme.palette.primary.main, 0.1),
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
  );
};

/** Centered "no data" placeholder sized to match chart height */
const ChartEmpty: React.FC<{ height?: number }> = ({ height = 350 }) => (
  <Box
    sx={{
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      height,
      color: 'text.disabled',
    }}
  >
    <Typography variant="body2" color="text.disabled">
      데이터가 없습니다
    </Typography>
  </Box>
);

/** Shared Paper wrapper */
const SectionPaper: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <Paper
    elevation={0}
    sx={{
      p: 3,
      border: '1px solid',
      borderColor: 'divider',
      borderRadius: '14px',
      height: '100%',
      boxSizing: 'border-box',
    }}
  >
    {children}
  </Paper>
);

// ---------------------------------------------------------------------------
// Period tab config
// ---------------------------------------------------------------------------
const PERIOD_TABS: { label: string; value: PeriodKey }[] = [
  { label: '일간', value: 'day' },
  { label: '주간', value: 'week' },
  { label: '월간', value: 'month' },
  { label: '연간', value: 'year' },
];

// ---------------------------------------------------------------------------
// Main component
// ---------------------------------------------------------------------------
const TrendAnalysis: React.FC = () => {
  const navigate = useNavigate();
  const theme = useTheme();

  const [period, setPeriod] = useState<PeriodKey>('week');
  const [trendsData, setTrendsData] = useState<TrendsData | null>(null);
  const [statsData, setStatsData] = useState<StatisticsData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchData = useCallback(async (selectedPeriod: PeriodKey) => {
    setLoading(true);
    setError(null);
    try {
      const [trendsRes, statsRes] = await Promise.all([
        apiClient.getBidTrends(selectedPeriod),
        apiClient.getBidStatistics('30d'),
      ]);
      setTrendsData(trendsRes?.data ?? null);
      setStatsData(statsRes?.data ?? null);
    } catch (err: any) {
      setError(err?.message ?? '데이터를 불러오는 중 오류가 발생했습니다.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData(period);
  }, [period, fetchData]);

  const handlePeriodChange = (_: React.SyntheticEvent, newValue: PeriodKey) => {
    setPeriod(newValue);
  };

  // Derived data
  const trendPoints: TrendPoint[] = trendsData?.trends ?? [];
  const topKeywords: KeywordStat[] = (trendsData?.top_keywords ?? []).slice(0, 10);
  const categoryDist: CategoryStat[] = statsData?.category_distribution ?? [];
  const priceDist: PriceRange[] = statsData?.price_distribution ?? [];
  const orgStats: OrgStat[] = (statsData?.organization_stats ?? []).slice(0, 10);

  // ---------------------------------------------------------------------------
  // Render
  // ---------------------------------------------------------------------------
  return (
    <Box>
      {/* ------------------------------------------------------------------ */}
      {/* Page header                                                          */}
      {/* ------------------------------------------------------------------ */}
      <Box sx={{ mb: 3 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, mb: 0.5 }}>
          <Box
            sx={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              width: 40,
              height: 40,
              borderRadius: '10px',
              bgcolor: alpha(theme.palette.primary.main, 0.1),
              color: 'primary.main',
              '& .MuiSvgIcon-root': { fontSize: 22 },
            }}
          >
            <TrendingUp />
          </Box>
          <Typography variant="h5" fontWeight={700} letterSpacing="-0.02em">
            트렌드 분석
          </Typography>
        </Box>
        <Typography variant="body2" color="text.secondary" sx={{ ml: 7 }}>
          입찰 시장 동향을 한눈에 파악하세요
        </Typography>
      </Box>

      {/* ------------------------------------------------------------------ */}
      {/* Period tabs                                                          */}
      {/* ------------------------------------------------------------------ */}
      <Paper
        elevation={0}
        sx={{
          mb: 3,
          border: '1px solid',
          borderColor: 'divider',
          borderRadius: '12px',
          display: 'inline-flex',
        }}
      >
        <Tabs
          value={period}
          onChange={handlePeriodChange}
          sx={{
            minHeight: 44,
            px: 0.75,
            '& .MuiTab-root': {
              minHeight: 44,
              minWidth: 72,
              fontSize: '0.875rem',
              fontWeight: 500,
              textTransform: 'none',
              borderRadius: '8px',
            },
          }}
        >
          {PERIOD_TABS.map((tab) => (
            <Tab key={tab.value} label={tab.label} value={tab.value} />
          ))}
        </Tabs>
      </Paper>

      {/* ------------------------------------------------------------------ */}
      {/* Error state                                                          */}
      {/* ------------------------------------------------------------------ */}
      {error && (
        <Alert severity="error" sx={{ mb: 3, borderRadius: '10px' }}>
          {error}
        </Alert>
      )}

      {/* ------------------------------------------------------------------ */}
      {/* Loading state                                                        */}
      {/* ------------------------------------------------------------------ */}
      {loading ? (
        <Box
          sx={{
            display: 'flex',
            justifyContent: 'center',
            alignItems: 'center',
            height: 400,
          }}
        >
          <CircularProgress />
        </Box>
      ) : (
        <Grid container spacing={3}>
          {/* ---------------------------------------------------------------- */}
          {/* Section 1: 입찰 공고 추이 (Line chart)                           */}
          {/* ---------------------------------------------------------------- */}
          <Grid item xs={12} md={8}>
            <SectionPaper>
              <SectionHeader icon={<TrendingUp />} title="입찰 공고 추이" />
              <Divider sx={{ mb: 2 }} />
              {trendPoints.length === 0 ? (
                <ChartEmpty height={350} />
              ) : (
                <ResponsiveContainer width="100%" height={350}>
                  <LineChart data={trendPoints}>
                    <CartesianGrid
                      strokeDasharray="3 3"
                      stroke={theme.palette.divider}
                    />
                    <XAxis
                      dataKey="period"
                      stroke={theme.palette.text.secondary}
                      tick={{ fontSize: 12 }}
                    />
                    <YAxis
                      stroke={theme.palette.text.secondary}
                      tick={{ fontSize: 12 }}
                      width={40}
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
                      name="입찰 건수"
                      stroke="#1976d2"
                      strokeWidth={2}
                      dot={{ r: 4, fill: '#1976d2', strokeWidth: 2, stroke: '#fff' }}
                      activeDot={{ r: 6 }}
                    />
                  </LineChart>
                </ResponsiveContainer>
              )}
            </SectionPaper>
          </Grid>

          {/* ---------------------------------------------------------------- */}
          {/* Section 2: 인기 키워드 TOP 10 (Horizontal bar chart)             */}
          {/* ---------------------------------------------------------------- */}
          <Grid item xs={12} md={4}>
            <SectionPaper>
              <SectionHeader icon={<LocalOffer />} title="인기 키워드" />
              <Divider sx={{ mb: 2 }} />
              {topKeywords.length === 0 ? (
                <ChartEmpty height={350} />
              ) : (
                <ResponsiveContainer width="100%" height={350}>
                  <BarChart
                    layout="vertical"
                    data={topKeywords}
                    margin={{ top: 0, right: 16, left: 0, bottom: 0 }}
                  >
                    <CartesianGrid
                      strokeDasharray="3 3"
                      horizontal={false}
                      stroke={theme.palette.divider}
                    />
                    <XAxis
                      type="number"
                      stroke={theme.palette.text.secondary}
                      tick={{ fontSize: 11 }}
                    />
                    <YAxis
                      type="category"
                      dataKey="keyword"
                      width={80}
                      stroke={theme.palette.text.secondary}
                      tick={{
                        fontSize: 11,
                        cursor: 'pointer',
                      }}
                      tickFormatter={(value: string) =>
                        value.length > 8 ? value.slice(0, 8) + '…' : value
                      }
                    />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: theme.palette.background.paper,
                        border: '1px solid ' + theme.palette.divider,
                        borderRadius: 8,
                        fontSize: 13,
                      }}
                      formatter={(value: any) => [`${value}건`, '검색 빈도']}
                    />
                    <Bar
                      dataKey="count"
                      name="검색 빈도"
                      fill="#42a5f5"
                      radius={[0, 4, 4, 0]}
                      cursor="pointer"
                      onClick={(data: any) => {
                        if (data?.keyword) {
                          navigate(`/search?q=${encodeURIComponent(data.keyword)}`);
                        }
                      }}
                    />
                  </BarChart>
                </ResponsiveContainer>
              )}
            </SectionPaper>
          </Grid>

          {/* ---------------------------------------------------------------- */}
          {/* Section 3: 카테고리 분포 (Pie chart)                             */}
          {/* ---------------------------------------------------------------- */}
          <Grid item xs={12} md={6}>
            <SectionPaper>
              <SectionHeader icon={<Category />} title="카테고리 분포" />
              <Divider sx={{ mb: 2 }} />
              {categoryDist.length === 0 ? (
                <ChartEmpty height={300} />
              ) : (
                <ResponsiveContainer width="100%" height={300}>
                  <PieChart>
                    <Pie
                      data={categoryDist}
                      dataKey="count"
                      nameKey="category"
                      cx="50%"
                      cy="50%"
                      outerRadius={90}
                      innerRadius={30}
                      labelLine={false}
                      label={({ percent }) => `${(percent * 100).toFixed(0)}%`}
                    >
                      {categoryDist.map((_entry, index) => (
                        <Cell
                          key={`cat-cell-${index}`}
                          fill={CHART_COLORS[index % CHART_COLORS.length]}
                        />
                      ))}
                    </Pie>
                    <Tooltip
                      contentStyle={{
                        backgroundColor: theme.palette.background.paper,
                        border: '1px solid ' + theme.palette.divider,
                        borderRadius: 8,
                        fontSize: 13,
                      }}
                      formatter={(value: any, _name: any, props: any) => [
                        `${value}건${props.payload.percentage != null ? ` (${props.payload.percentage.toFixed(1)}%)` : ''}`,
                        props.payload.category,
                      ]}
                    />
                    <Legend
                      verticalAlign="bottom"
                      height={36}
                      wrapperStyle={{ fontSize: 12 }}
                      formatter={(_value, entry: any) =>
                        `${entry.payload.category} (${entry.payload.count}건)`
                      }
                    />
                  </PieChart>
                </ResponsiveContainer>
              )}
            </SectionPaper>
          </Grid>

          {/* ---------------------------------------------------------------- */}
          {/* Section 4: 가격대 분포 (Bar chart)                               */}
          {/* ---------------------------------------------------------------- */}
          <Grid item xs={12} md={6}>
            <SectionPaper>
              <SectionHeader icon={<AttachMoney />} title="가격대 분포" />
              <Divider sx={{ mb: 2 }} />
              {priceDist.length === 0 ? (
                <ChartEmpty height={300} />
              ) : (
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart
                    data={priceDist}
                    margin={{ top: 0, right: 16, left: 0, bottom: 40 }}
                  >
                    <defs>
                      <linearGradient id="priceGradient" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="0%" stopColor="#1976d2" stopOpacity={1} />
                        <stop offset="100%" stopColor="#42a5f5" stopOpacity={1} />
                      </linearGradient>
                    </defs>
                    <CartesianGrid
                      strokeDasharray="3 3"
                      stroke={theme.palette.divider}
                    />
                    <XAxis
                      dataKey="range"
                      stroke={theme.palette.text.secondary}
                      tick={{ fontSize: 11 }}
                      angle={-30}
                      textAnchor="end"
                      interval={0}
                    />
                    <YAxis
                      stroke={theme.palette.text.secondary}
                      tick={{ fontSize: 11 }}
                      width={40}
                    />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: theme.palette.background.paper,
                        border: '1px solid ' + theme.palette.divider,
                        borderRadius: 8,
                        fontSize: 13,
                      }}
                      formatter={(value: any) => [`${value}건`, '공고 수']}
                    />
                    <Bar
                      dataKey="count"
                      name="공고 수"
                      fill="url(#priceGradient)"
                      radius={[4, 4, 0, 0]}
                    />
                  </BarChart>
                </ResponsiveContainer>
              )}
            </SectionPaper>
          </Grid>

          {/* ---------------------------------------------------------------- */}
          {/* Section 5: 발주기관 TOP 10 (Horizontal bar chart, two bars)      */}
          {/* ---------------------------------------------------------------- */}
          <Grid item xs={12}>
            <SectionPaper>
              <SectionHeader icon={<Business />} title="발주기관 TOP 10" />
              <Divider sx={{ mb: 2 }} />
              {orgStats.length === 0 ? (
                <ChartEmpty height={400} />
              ) : (
                <ResponsiveContainer width="100%" height={400}>
                  <BarChart
                    layout="vertical"
                    data={orgStats.map((org) => ({
                      ...org,
                      // Scale total_price to a comparable range (in 억원 units)
                      total_price_scaled:
                        org.total_price != null
                          ? Math.round(org.total_price / 100_000_000)
                          : 0,
                    }))}
                    margin={{ top: 0, right: 24, left: 0, bottom: 0 }}
                  >
                    <CartesianGrid
                      strokeDasharray="3 3"
                      horizontal={false}
                      stroke={theme.palette.divider}
                    />
                    <XAxis
                      type="number"
                      stroke={theme.palette.text.secondary}
                      tick={{ fontSize: 11 }}
                    />
                    <YAxis
                      type="category"
                      dataKey="organization"
                      width={150}
                      stroke={theme.palette.text.secondary}
                      tick={{ fontSize: 11 }}
                      tickFormatter={(value: string) =>
                        value.length > 14 ? value.slice(0, 14) + '…' : value
                      }
                    />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: theme.palette.background.paper,
                        border: '1px solid ' + theme.palette.divider,
                        borderRadius: 8,
                        fontSize: 13,
                      }}
                      formatter={(value: any, name: string) => {
                        if (name === '총 금액(억원)') return [`${value}억원`, name];
                        return [`${value}건`, name];
                      }}
                    />
                    <Legend
                      verticalAlign="top"
                      height={32}
                      wrapperStyle={{ fontSize: 12 }}
                    />
                    <Bar
                      dataKey="count"
                      name="공고 수(건)"
                      fill="#1976d2"
                      radius={[0, 4, 4, 0]}
                    >
                      {orgStats.map((_entry, index) => (
                        <Cell
                          key={`org-count-cell-${index}`}
                          fill={getChartColor(index)}
                        />
                      ))}
                    </Bar>
                    <Bar
                      dataKey="total_price_scaled"
                      name="총 금액(억원)"
                      fill="#66bb6a"
                      radius={[0, 4, 4, 0]}
                    />
                  </BarChart>
                </ResponsiveContainer>
              )}
            </SectionPaper>
          </Grid>
        </Grid>
      )}
    </Box>
  );
};

export default TrendAnalysis;
