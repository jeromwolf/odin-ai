/**
 * 관리자 - 시스템 모니터링 화면
 * 실시간 시스템 리소스, API 성능, 알림 현황
 */

import React, { useEffect, useState } from 'react';
import {
  Box,
  Typography,
  Paper,
  Grid,
  Card,
  CardContent,
  LinearProgress,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
  Alert,
  CircularProgress,
} from '@mui/material';
import {
  Computer,
  Memory,
  Storage as StorageIcon,
  Speed,
  CheckCircle,
  Error as ErrorIcon,
} from '@mui/icons-material';
import {
  LineChart,
  Line,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  BarChart,
  Bar,
} from 'recharts';
import { adminApi } from '../../services/admin/adminApi';

interface SystemStatus {
  cpu_percent: number;
  memory_percent: number;
  disk_percent: number;
  memory_used_gb: number;
  memory_total_gb: number;
  disk_used_gb: number;
  disk_total_gb: number;
  db_status: string;
  db_connections: number;
}

const SystemMonitoring: React.FC = () => {
  const [loading, setLoading] = useState(true);
  const [systemStatus, setSystemStatus] = useState<SystemStatus | null>(null);
  const [apiPerformance, setApiPerformance] = useState<any[]>([]);
  const [notificationStatus, setNotificationStatus] = useState<any>(null);
  const [metricsHistory, setMetricsHistory] = useState<any[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadSystemData();
    // 10초마다 자동 새로고침
    const interval = setInterval(loadSystemData, 10000);
    return () => clearInterval(interval);
  }, []);

  const loadSystemData = async () => {
    try {
      setLoading(true);
      setError(null);

      const [statusData, apiData, notifData, metricsData] = await Promise.all([
        adminApi.getSystemStatus(),
        adminApi.getApiPerformance({}),
        adminApi.getNotificationStatus({}),
        adminApi.getSystemMetrics({ limit: 30 }),
      ]);

      setSystemStatus(statusData);
      setApiPerformance(apiData.endpoints || []);
      setNotificationStatus(notifData);

      // 메트릭 이력 차트 데이터 변환
      if (metricsData.metrics) {
        const grouped: Record<string, any> = {};
        metricsData.metrics.forEach((metric: any) => {
          const time = new Date(metric.recorded_at).toLocaleTimeString('ko-KR', {
            hour: '2-digit',
            minute: '2-digit',
          });
          if (!grouped[time]) {
            grouped[time] = { time };
          }
          grouped[time][metric.metric_type] = metric.metric_value;
        });
        setMetricsHistory(Object.values(grouped).reverse());
      }
    } catch (err: any) {
      console.error('시스템 데이터 로드 실패:', err);
      setError(err.response?.data?.detail || '데이터를 불러오는데 실패했습니다.');
    } finally {
      setLoading(false);
    }
  };

  const getProgressColor = (value: number) => {
    if (value < 50) return 'success';
    if (value < 80) return 'warning';
    return 'error';
  };

  if (loading && !systemStatus) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        시스템 모니터링
      </Typography>
      <Typography variant="body2" color="textSecondary" gutterBottom>
        실시간 시스템 리소스 및 성능 모니터링
      </Typography>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {/* 시스템 리소스 상태 */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" mb={2}>
                <Computer sx={{ fontSize: 40, mr: 2, color: '#2196f3' }} />
                <Box flexGrow={1}>
                  <Typography variant="body2" color="textSecondary">
                    CPU 사용률
                  </Typography>
                  <Typography variant="h5">
                    {systemStatus?.cpu_percent.toFixed(1)}%
                  </Typography>
                </Box>
              </Box>
              <LinearProgress
                variant="determinate"
                value={systemStatus?.cpu_percent || 0}
                color={getProgressColor(systemStatus?.cpu_percent || 0)}
              />
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" mb={2}>
                <Memory sx={{ fontSize: 40, mr: 2, color: '#4caf50' }} />
                <Box flexGrow={1}>
                  <Typography variant="body2" color="textSecondary">
                    메모리 사용률
                  </Typography>
                  <Typography variant="h5">
                    {systemStatus?.memory_percent.toFixed(1)}%
                  </Typography>
                  <Typography variant="caption" color="textSecondary">
                    {systemStatus?.memory_used_gb.toFixed(1)} /{' '}
                    {systemStatus?.memory_total_gb.toFixed(1)} GB
                  </Typography>
                </Box>
              </Box>
              <LinearProgress
                variant="determinate"
                value={systemStatus?.memory_percent || 0}
                color={getProgressColor(systemStatus?.memory_percent || 0)}
              />
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" mb={2}>
                <StorageIcon sx={{ fontSize: 40, mr: 2, color: '#ff9800' }} />
                <Box flexGrow={1}>
                  <Typography variant="body2" color="textSecondary">
                    디스크 사용률
                  </Typography>
                  <Typography variant="h5">
                    {systemStatus?.disk_percent.toFixed(1)}%
                  </Typography>
                  <Typography variant="caption" color="textSecondary">
                    {systemStatus?.disk_used_gb.toFixed(1)} /{' '}
                    {systemStatus?.disk_total_gb.toFixed(1)} GB
                  </Typography>
                </Box>
              </Box>
              <LinearProgress
                variant="determinate"
                value={systemStatus?.disk_percent || 0}
                color={getProgressColor(systemStatus?.disk_percent || 0)}
              />
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      <Grid container spacing={3}>
        {/* 시스템 리소스 추이 */}
        <Grid item xs={12} lg={8}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>
              시스템 리소스 추이 (최근 30분)
            </Typography>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={metricsHistory}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="time" />
                <YAxis domain={[0, 100]} />
                <Tooltip />
                <Legend />
                <Line
                  type="monotone"
                  dataKey="cpu"
                  stroke="#2196f3"
                  name="CPU (%)"
                  dot={false}
                />
                <Line
                  type="monotone"
                  dataKey="memory"
                  stroke="#4caf50"
                  name="메모리 (%)"
                  dot={false}
                />
                <Line
                  type="monotone"
                  dataKey="disk"
                  stroke="#ff9800"
                  name="디스크 (%)"
                  dot={false}
                />
              </LineChart>
            </ResponsiveContainer>
          </Paper>
        </Grid>

        {/* 데이터베이스 상태 */}
        <Grid item xs={12} lg={4}>
          <Paper sx={{ p: 2, height: '100%' }}>
            <Typography variant="h6" gutterBottom>
              데이터베이스 상태
            </Typography>
            <Box sx={{ mt: 3 }}>
              <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
                <Typography variant="body2">상태</Typography>
                <Chip
                  label={systemStatus?.db_status === 'healthy' ? '정상' : '에러'}
                  color={systemStatus?.db_status === 'healthy' ? 'success' : 'error'}
                  icon={
                    systemStatus?.db_status === 'healthy' ? (
                      <CheckCircle />
                    ) : (
                      <ErrorIcon />
                    )
                  }
                />
              </Box>
              <Box display="flex" justifyContent="space-between" mb={2}>
                <Typography variant="body2">활성 연결</Typography>
                <Typography variant="body1" fontWeight="bold">
                  {systemStatus?.db_connections || 0}개
                </Typography>
              </Box>
            </Box>
          </Paper>
        </Grid>

        {/* API 성능 통계 */}
        <Grid item xs={12}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>
              API 성능 통계 (최근 1시간)
            </Typography>
            <TableContainer>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>엔드포인트</TableCell>
                    <TableCell align="right">평균 응답 시간</TableCell>
                    <TableCell align="right">최대 응답 시간</TableCell>
                    <TableCell align="right">요청 횟수</TableCell>
                    <TableCell align="right">에러 횟수</TableCell>
                    <TableCell align="right">에러율</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {apiPerformance.length === 0 ? (
                    <TableRow>
                      <TableCell colSpan={6} align="center">
                        API 성능 데이터가 없습니다
                      </TableCell>
                    </TableRow>
                  ) : (
                    apiPerformance.map((api, index) => (
                      <TableRow key={index}>
                        <TableCell>{api.endpoint}</TableCell>
                        <TableCell align="right">{api.avg_response_time.toFixed(2)} ms</TableCell>
                        <TableCell align="right">{api.max_response_time.toFixed(2)} ms</TableCell>
                        <TableCell align="right">{api.request_count}</TableCell>
                        <TableCell align="right">{api.error_count}</TableCell>
                        <TableCell align="right">
                          <Chip
                            label={`${api.error_rate.toFixed(2)}%`}
                            color={api.error_rate > 5 ? 'error' : 'success'}
                            size="small"
                          />
                        </TableCell>
                      </TableRow>
                    ))
                  )}
                </TableBody>
              </Table>
            </TableContainer>
          </Paper>
        </Grid>

        {/* 알림 발송 현황 */}
        <Grid item xs={12}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>
              알림 발송 현황 (오늘)
            </Typography>
            <Grid container spacing={3}>
              <Grid item xs={12} md={3}>
                <Card variant="outlined">
                  <CardContent>
                    <Typography variant="body2" color="textSecondary">
                      총 발송
                    </Typography>
                    <Typography variant="h4">
                      {notificationStatus?.total_sent || 0}
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>
              <Grid item xs={12} md={3}>
                <Card variant="outlined">
                  <CardContent>
                    <Typography variant="body2" color="textSecondary">
                      성공
                    </Typography>
                    <Typography variant="h4" color="success.main">
                      {notificationStatus?.success_count || 0}
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>
              <Grid item xs={12} md={3}>
                <Card variant="outlined">
                  <CardContent>
                    <Typography variant="body2" color="textSecondary">
                      실패
                    </Typography>
                    <Typography variant="h4" color="error.main">
                      {notificationStatus?.failed_count || 0}
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>
              <Grid item xs={12} md={3}>
                <Card variant="outlined">
                  <CardContent>
                    <Typography variant="body2" color="textSecondary">
                      성공률
                    </Typography>
                    <Typography variant="h4" color="primary.main">
                      {notificationStatus?.success_rate.toFixed(1) || 0}%
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>
            </Grid>
          </Paper>
        </Grid>
      </Grid>
    </Box>
  );
};

export default SystemMonitoring;
