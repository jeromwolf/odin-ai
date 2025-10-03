/**
 * 관리자 - 통계 분석 화면
 * 종합 통계 및 분석 대시보드
 */

import React, { useEffect, useState } from 'react';
import {
  Box,
  Typography,
  Paper,
  Grid,
  Card,
  CardContent,
  TextField,
  MenuItem,
  Alert,
  CircularProgress,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
} from '@mui/material';
import {
  TrendingUp,
  TrendingDown,
  People,
  Assignment,
  Notifications,
  AttachMoney,
} from '@mui/icons-material';
import {
  LineChart,
  Line,
  AreaChart,
  Area,
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
import { adminApi } from '../../services/admin/adminApi';

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884D8'];

const Statistics: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [period, setPeriod] = useState<string>('30days');

  // 통계 데이터
  const [userStats, setUserStats] = useState<any>(null);
  const [bidStats, setBidStats] = useState<any>(null);
  const [systemStats, setSystemStats] = useState<any>(null);
  const [growthData, setGrowthData] = useState<any[]>([]);
  const [subscriptionData, setSubscriptionData] = useState<any[]>([]);

  useEffect(() => {
    loadStatistics();
    // 5분마다 자동 새로고침
    const interval = setInterval(loadStatistics, 300000);
    return () => clearInterval(interval);
  }, [period]);

  const loadStatistics = async () => {
    try {
      setLoading(true);
      setError(null);

      const userStatsData = await adminApi.getUserStatistics();

      setUserStats(userStatsData);
      // TODO: API 구현 후 주석 해제
      // setBidStats(bidStatsData);
      // setSystemStats(systemStatsData);

      // 가상 성장 데이터 (실제로는 API에서 받아야 함)
      setGrowthData([
        { date: '1주', users: 120, bids: 450, notifications: 890 },
        { date: '2주', users: 145, bids: 520, notifications: 1020 },
        { date: '3주', users: 168, bids: 610, notifications: 1180 },
        { date: '4주', users: 195, bids: 705, notifications: 1350 },
      ]);

      // 구독 플랜 분포 데이터
      setSubscriptionData([
        { name: '무료', value: userStatsData?.free_users || 0 },
        { name: '베이직', value: userStatsData?.basic_users || 0 },
        { name: '프로', value: userStatsData?.pro_users || 0 },
        { name: '엔터프라이즈', value: userStatsData?.enterprise_users || 0 },
      ]);
    } catch (err: any) {
      console.error('통계 데이터 로드 실패:', err);
      setError(err.response?.data?.detail || '데이터를 불러오는데 실패했습니다.');
    } finally {
      setLoading(false);
    }
  };

  const getTrendIcon = (value: number) => {
    return value >= 0 ? (
      <TrendingUp sx={{ color: '#4caf50' }} />
    ) : (
      <TrendingDown sx={{ color: '#f44336' }} />
    );
  };

  if (loading && !userStats) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Box>
          <Typography variant="h4" gutterBottom>
            통계 분석
          </Typography>
          <Typography variant="body2" color="textSecondary">
            종합 통계 및 분석 대시보드
          </Typography>
        </Box>
        <TextField
          select
          value={period}
          onChange={(e) => setPeriod(e.target.value)}
          size="small"
          sx={{ width: 150 }}
        >
          <MenuItem value="7days">최근 7일</MenuItem>
          <MenuItem value="30days">최근 30일</MenuItem>
          <MenuItem value="90days">최근 90일</MenuItem>
          <MenuItem value="1year">최근 1년</MenuItem>
        </TextField>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {/* 주요 지표 카드 */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box display="flex" justifyContent="space-between" alignItems="center">
                <Box>
                  <Typography variant="body2" color="textSecondary">
                    전체 사용자
                  </Typography>
                  <Typography variant="h4">{userStats?.total_users || 0}</Typography>
                  <Box display="flex" alignItems="center" mt={1}>
                    {getTrendIcon(userStats?.user_growth_rate || 0)}
                    <Typography variant="caption" color="textSecondary" ml={0.5}>
                      {userStats?.user_growth_rate > 0 ? '+' : ''}
                      {userStats?.user_growth_rate || 0}% 전주 대비
                    </Typography>
                  </Box>
                </Box>
                <People sx={{ fontSize: 48, color: '#2196f3', opacity: 0.3 }} />
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box display="flex" justifyContent="space-between" alignItems="center">
                <Box>
                  <Typography variant="body2" color="textSecondary">
                    총 입찰공고
                  </Typography>
                  <Typography variant="h4">{bidStats?.total_bids || 0}</Typography>
                  <Box display="flex" alignItems="center" mt={1}>
                    {getTrendIcon(bidStats?.bid_growth_rate || 0)}
                    <Typography variant="caption" color="textSecondary" ml={0.5}>
                      {bidStats?.bid_growth_rate > 0 ? '+' : ''}
                      {bidStats?.bid_growth_rate || 0}% 전주 대비
                    </Typography>
                  </Box>
                </Box>
                <Assignment sx={{ fontSize: 48, color: '#4caf50', opacity: 0.3 }} />
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box display="flex" justifyContent="space-between" alignItems="center">
                <Box>
                  <Typography variant="body2" color="textSecondary">
                    알림 발송
                  </Typography>
                  <Typography variant="h4">
                    {systemStats?.total_notifications || 0}
                  </Typography>
                  <Box display="flex" alignItems="center" mt={1}>
                    <Typography variant="caption" color="success.main">
                      성공률 {systemStats?.notification_success_rate || 0}%
                    </Typography>
                  </Box>
                </Box>
                <Notifications sx={{ fontSize: 48, color: '#ff9800', opacity: 0.3 }} />
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box display="flex" justifyContent="space-between" alignItems="center">
                <Box>
                  <Typography variant="body2" color="textSecondary">
                    유료 사용자
                  </Typography>
                  <Typography variant="h4">{userStats?.paid_users || 0}</Typography>
                  <Box display="flex" alignItems="center" mt={1}>
                    <Typography variant="caption" color="textSecondary">
                      전체의 {((userStats?.paid_users / userStats?.total_users) * 100 || 0).toFixed(1)}%
                    </Typography>
                  </Box>
                </Box>
                <AttachMoney sx={{ fontSize: 48, color: '#9c27b0', opacity: 0.3 }} />
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      <Grid container spacing={3}>
        {/* 사용자 성장 추이 */}
        <Grid item xs={12} lg={8}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>
              사용자 및 입찰공고 성장 추이
            </Typography>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={growthData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="date" />
                <YAxis />
                <Tooltip />
                <Legend />
                <Line
                  type="monotone"
                  dataKey="users"
                  stroke="#2196f3"
                  name="사용자"
                  strokeWidth={2}
                />
                <Line
                  type="monotone"
                  dataKey="bids"
                  stroke="#4caf50"
                  name="입찰공고"
                  strokeWidth={2}
                />
                <Line
                  type="monotone"
                  dataKey="notifications"
                  stroke="#ff9800"
                  name="알림 발송"
                  strokeWidth={2}
                />
              </LineChart>
            </ResponsiveContainer>
          </Paper>
        </Grid>

        {/* 구독 플랜 분포 */}
        <Grid item xs={12} lg={4}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>
              구독 플랜 분포
            </Typography>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={subscriptionData}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={(entry) => `${entry.name}: ${entry.value}`}
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {subscriptionData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </Paper>
        </Grid>

        {/* 시스템 성능 지표 */}
        <Grid item xs={12} lg={6}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>
              시스템 성능 지표
            </Typography>
            <TableContainer>
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell>지표</TableCell>
                    <TableCell align="right">현재 값</TableCell>
                    <TableCell align="right">상태</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  <TableRow>
                    <TableCell>평균 API 응답 시간</TableCell>
                    <TableCell align="right">
                      {systemStats?.avg_api_response_time || 0} ms
                    </TableCell>
                    <TableCell align="right">
                      <Chip
                        label="정상"
                        color="success"
                        size="small"
                      />
                    </TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell>배치 처리 성공률</TableCell>
                    <TableCell align="right">
                      {systemStats?.batch_success_rate || 0}%
                    </TableCell>
                    <TableCell align="right">
                      <Chip
                        label={systemStats?.batch_success_rate > 90 ? '우수' : '주의'}
                        color={systemStats?.batch_success_rate > 90 ? 'success' : 'warning'}
                        size="small"
                      />
                    </TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell>데이터베이스 연결</TableCell>
                    <TableCell align="right">
                      {systemStats?.db_connection_count || 0}
                    </TableCell>
                    <TableCell align="right">
                      <Chip label="정상" color="success" size="small" />
                    </TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell>오류율</TableCell>
                    <TableCell align="right">{systemStats?.error_rate || 0}%</TableCell>
                    <TableCell align="right">
                      <Chip
                        label={systemStats?.error_rate < 1 ? '정상' : '주의'}
                        color={systemStats?.error_rate < 1 ? 'success' : 'warning'}
                        size="small"
                      />
                    </TableCell>
                  </TableRow>
                </TableBody>
              </Table>
            </TableContainer>
          </Paper>
        </Grid>

        {/* 사용자 활동 통계 */}
        <Grid item xs={12} lg={6}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>
              사용자 활동 통계
            </Typography>
            <TableContainer>
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell>활동</TableCell>
                    <TableCell align="right">전체</TableCell>
                    <TableCell align="right">오늘</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  <TableRow>
                    <TableCell>검색 횟수</TableCell>
                    <TableCell align="right">{userStats?.total_searches || 0}</TableCell>
                    <TableCell align="right">
                      {userStats?.today_searches || 0}
                    </TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell>북마크 생성</TableCell>
                    <TableCell align="right">
                      {userStats?.total_bookmarks || 0}
                    </TableCell>
                    <TableCell align="right">
                      {userStats?.today_bookmarks || 0}
                    </TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell>알림 규칙 등록</TableCell>
                    <TableCell align="right">
                      {userStats?.total_notification_rules || 0}
                    </TableCell>
                    <TableCell align="right">
                      {userStats?.today_notification_rules || 0}
                    </TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell>로그인 횟수</TableCell>
                    <TableCell align="right">{userStats?.total_logins || 0}</TableCell>
                    <TableCell align="right">{userStats?.today_logins || 0}</TableCell>
                  </TableRow>
                </TableBody>
              </Table>
            </TableContainer>
          </Paper>
        </Grid>

        {/* 입찰공고 카테고리 분포 */}
        <Grid item xs={12}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>
              입찰공고 카테고리별 분포
            </Typography>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart
                data={[
                  { category: '건설', count: 1245 },
                  { category: '용역', count: 890 },
                  { category: '물품', count: 756 },
                  { category: 'IT', count: 523 },
                  { category: '유지보수', count: 412 },
                  { category: '기타', count: 289 },
                ]}
              >
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="category" />
                <YAxis />
                <Tooltip />
                <Legend />
                <Bar dataKey="count" fill="#2196f3" name="공고 수" />
              </BarChart>
            </ResponsiveContainer>
          </Paper>
        </Grid>
      </Grid>
    </Box>
  );
};

export default Statistics;
