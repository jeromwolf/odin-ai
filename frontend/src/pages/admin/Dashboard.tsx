/**
 * 관리자 대시보드 메인 화면
 * 시스템 상태, 최근 배치 실행 이력, 실시간 메트릭 차트
 */

import React, { useEffect, useState } from 'react';
import {
  Grid,
  Paper,
  Typography,
  Box,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
  Alert,
  useTheme,
} from '@mui/material';
import {
  TrendingUp,
  Storage,
  People,
  CheckCircle,
} from '@mui/icons-material';
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';
import { adminApi } from '../../services/admin/adminApi';
import { StatCard, FullscreenLoading } from '../../components/common';
import { getChartColor, STAT_CARD_COLORS } from '../../utils/colors';
import { formatKRDate } from '../../utils/formatters';

const AdminDashboard: React.FC = () => {
  const theme = useTheme();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [systemStatus, setSystemStatus] = useState<any>(null);
  const [batchExecutions, setBatchExecutions] = useState<any[]>([]);
  const [userStats, setUserStats] = useState<any>(null);
  const [metricsData, setMetricsData] = useState<any[]>([]);

  useEffect(() => {
    loadDashboardData();
    // 30초마다 자동 새로고침
    const interval = setInterval(loadDashboardData, 30000);
    return () => clearInterval(interval);
  }, []);

  const loadDashboardData = async () => {
    try {
      setLoading(true);
      setError(null);

      // 병렬로 데이터 로드
      const [statusData, batchData, userStatsData, metricsData] =
        await Promise.all([
          adminApi.getSystemStatus(),
          adminApi.getBatchExecutions({ limit: 10, page: 1 }),
          adminApi.getUserStatistics(),
          adminApi.getSystemMetrics({ limit: 20 }),
        ]);

      setSystemStatus(statusData);
      setBatchExecutions(batchData.executions || []);
      setUserStats(userStatsData);

      // 메트릭 데이터 차트용으로 변환
      if (metricsData.metrics) {
        const chartData = metricsData.metrics
          .reverse()
          .map((metric: any) => ({
            time: new Date(metric.recorded_at).toLocaleTimeString('ko-KR', {
              hour: '2-digit',
              minute: '2-digit',
            }),
            value: metric.metric_value,
            type: metric.metric_type,
          }));
        setMetricsData(chartData);
      }
    } catch (err: any) {
      console.error('대시보드 데이터 로드 실패:', err);
      setError(err.response?.data?.detail || '데이터를 불러오는데 실패했습니다.');
    } finally {
      setLoading(false);
    }
  };

  const getStatusChip = (status: string) => {
    const statusConfig: Record<
      string,
      { label: string; color: 'success' | 'error' | 'warning' | 'info' }
    > = {
      success: { label: '성공', color: 'success' },
      failed: { label: '실패', color: 'error' },
      running: { label: '실행중', color: 'info' },
    };

    const config = statusConfig[status] || { label: status, color: 'info' };
    return <Chip label={config.label} color={config.color} size="small" />;
  };

  if (loading && !systemStatus) {
    return <FullscreenLoading />;
  }

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        관리자 대시보드
      </Typography>
      <Typography variant="body2" color="textSecondary" gutterBottom>
        시스템 현황 및 모니터링
      </Typography>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      {/* 시스템 상태 카드 */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="배치 실행 상태"
            value={batchExecutions.filter((b) => b.status === 'success').length}
            changeLabel={`전체 ${batchExecutions.length}건`}
            icon={<CheckCircle />}
            iconBg={STAT_CARD_COLORS.active.bg}
            iconColor={STAT_CARD_COLORS.active.icon}
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="활성 사용자"
            value={userStats?.active_users || 0}
            changeLabel={`전체 ${userStats?.total_users || 0}명`}
            icon={<People />}
            iconBg={STAT_CARD_COLORS.total.bg}
            iconColor={STAT_CARD_COLORS.total.icon}
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="CPU 사용률"
            value={`${systemStatus?.cpu_percent || 0}%`}
            changeLabel="실시간"
            icon={<TrendingUp />}
            iconBg={STAT_CARD_COLORS.warning.bg}
            iconColor={STAT_CARD_COLORS.warning.icon}
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="DB 상태"
            value={systemStatus?.db_status === 'healthy' ? '정상' : '에러'}
            changeLabel={`연결: ${systemStatus?.db_connections || 0}개`}
            icon={<Storage />}
            iconBg={STAT_CARD_COLORS.info.bg}
            iconColor={STAT_CARD_COLORS.info.icon}
          />
        </Grid>
      </Grid>

      <Grid container spacing={3}>
        {/* 시스템 리소스 차트 */}
        <Grid item xs={12} lg={8}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>
              시스템 리소스 추이
            </Typography>
            <ResponsiveContainer width="100%" height={300}>
              <AreaChart data={metricsData}>
                <CartesianGrid
                  strokeDasharray="3 3"
                  stroke={theme.palette.divider}
                />
                <XAxis
                  dataKey="time"
                  tick={{ fill: theme.palette.text.secondary, fontSize: 12 }}
                />
                <YAxis
                  tick={{ fill: theme.palette.text.secondary, fontSize: 12 }}
                />
                <Tooltip
                  contentStyle={{
                    backgroundColor: theme.palette.background.paper,
                    border: `1px solid ${theme.palette.divider}`,
                    borderRadius: 8,
                  }}
                />
                <Legend />
                <Area
                  type="monotone"
                  dataKey="value"
                  stroke={getChartColor(0)}
                  fill={getChartColor(0)}
                  fillOpacity={0.2}
                />
              </AreaChart>
            </ResponsiveContainer>
          </Paper>
        </Grid>

        {/* 시스템 상태 요약 */}
        <Grid item xs={12} lg={4}>
          <Paper sx={{ p: 2, height: '100%' }}>
            <Typography variant="h6" gutterBottom>
              시스템 상태 요약
            </Typography>
            <Box sx={{ mt: 2 }}>
              <Box display="flex" justifyContent="space-between" mb={2}>
                <Typography variant="body2">CPU</Typography>
                <Typography variant="body2" fontWeight="bold">
                  {systemStatus?.cpu_percent || 0}%
                </Typography>
              </Box>
              <Box display="flex" justifyContent="space-between" mb={2}>
                <Typography variant="body2">메모리</Typography>
                <Typography variant="body2" fontWeight="bold">
                  {systemStatus?.memory_percent || 0}%
                </Typography>
              </Box>
              <Box display="flex" justifyContent="space-between" mb={2}>
                <Typography variant="body2">디스크</Typography>
                <Typography variant="body2" fontWeight="bold">
                  {systemStatus?.disk_percent || 0}%
                </Typography>
              </Box>
              <Box display="flex" justifyContent="space-between" mb={2}>
                <Typography variant="body2">메모리 사용량</Typography>
                <Typography variant="body2" fontWeight="bold">
                  {systemStatus?.memory_used_gb || 0} /{' '}
                  {systemStatus?.memory_total_gb || 0} GB
                </Typography>
              </Box>
              <Box display="flex" justifyContent="space-between">
                <Typography variant="body2">디스크 사용량</Typography>
                <Typography variant="body2" fontWeight="bold">
                  {systemStatus?.disk_used_gb || 0} /{' '}
                  {systemStatus?.disk_total_gb || 0} GB
                </Typography>
              </Box>
            </Box>
          </Paper>
        </Grid>

        {/* 최근 배치 실행 이력 */}
        <Grid item xs={12}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>
              최근 배치 실행 이력
            </Typography>
            <TableContainer>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>배치 타입</TableCell>
                    <TableCell>실행 시간</TableCell>
                    <TableCell>상태</TableCell>
                    <TableCell align="right">처리 건수</TableCell>
                    <TableCell align="right">성공</TableCell>
                    <TableCell align="right">실패</TableCell>
                    <TableCell align="right">소요 시간</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {batchExecutions.length === 0 ? (
                    <TableRow>
                      <TableCell colSpan={7} align="center">
                        배치 실행 이력이 없습니다
                      </TableCell>
                    </TableRow>
                  ) : (
                    batchExecutions.map((execution) => (
                      <TableRow key={execution.id}>
                        <TableCell>{execution.batch_type}</TableCell>
                        <TableCell>
                          {formatKRDate(execution.start_time, 'yyyy.MM.dd HH:mm')}
                        </TableCell>
                        <TableCell>{getStatusChip(execution.status)}</TableCell>
                        <TableCell align="right">
                          {execution.total_items}
                        </TableCell>
                        <TableCell align="right">
                          {execution.success_items}
                        </TableCell>
                        <TableCell align="right">
                          {execution.failed_items}
                        </TableCell>
                        <TableCell align="right">
                          {execution.duration_seconds
                            ? `${execution.duration_seconds}초`
                            : '-'}
                        </TableCell>
                      </TableRow>
                    ))
                  )}
                </TableBody>
              </Table>
            </TableContainer>
          </Paper>
        </Grid>
      </Grid>
    </Box>
  );
};

export default AdminDashboard;
