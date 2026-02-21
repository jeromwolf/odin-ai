/**
 * 관리자 - 알림 모니터링 화면
 * 알림 발송 현황, 통계, 이메일 로그
 */

import React, { useEffect, useState } from 'react';
import {
  Box,
  Typography,
  Paper,
  Grid,
  Card,
  CardContent,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
  Alert,
  CircularProgress,
  Pagination,
  TextField,
  MenuItem,
} from '@mui/material';
import {
  Mail,
  MailOutline,
  Error as ErrorIcon,
  CheckCircle,
  Warning as WarningIcon,
} from '@mui/icons-material';
import {
  LineChart,
  Line,
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

interface NotificationStats {
  total_notifications: number;
  total_sent: number;
  success_count: number;
  failed_count: number;
  pending_count: number;
}

interface EmailLog {
  id: number;
  user_id: number;
  email_to: string;
  status: 'sent' | 'failed' | 'pending';
  notification_count: number;
  sent_at: string;
  error_message?: string;
}

const NotificationMonitoring: React.FC = () => {
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState<NotificationStats | null>(null);
  const [notificationsList, setNotificationsList] = useState<any[]>([]);
  const [emailLogs, setEmailLogs] = useState<EmailLog[]>([]);
  const [notificationPage, setNotificationPage] = useState(1);
  const [emailLogsPage, setEmailLogsPage] = useState(1);
  const [chartData, setChartData] = useState<any[]>([]);
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadNotificationData();
    // 30초마다 자동 새로고침
    const interval = setInterval(loadNotificationData, 30000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    loadNotificationsList();
  }, [notificationPage]);

  useEffect(() => {
    loadEmailLogs();
  }, [emailLogsPage]);

  const loadNotificationData = async () => {
    try {
      setLoading(true);
      setError(null);

      const [statsData, chartData] = await Promise.all([
        adminApi.getNotificationsStats(),
        adminApi.getNotificationStats({}),
      ]);

      setStats(statsData);

      // 차트 데이터 변환
      if (chartData && Array.isArray(chartData)) {
        setChartData(
          chartData.map((item: any) => ({
            date: new Date(item.date || item.timestamp).toLocaleDateString('ko-KR'),
            notifications: item.total || 0,
            sent: item.sent || 0,
            failed: item.failed || 0,
          }))
        );
      }
    } catch (err: any) {
      setError('알림 통계를 불러오는데 실패했습니다: ' + (err.message || ''));
    } finally {
      setLoading(false);
    }
  };

  const loadNotificationsList = async () => {
    try {
      const response = await adminApi.getNotificationsList({
        page: notificationPage,
        limit: 10,
      });
      setNotificationsList(response.notifications || []);
    } catch (err: any) {
      console.error('알림 목록 로드 실패:', err);
    }
  };

  const loadEmailLogs = async () => {
    try {
      const response = await adminApi.getEmailSendLogs({
        page: emailLogsPage,
        limit: 10,
        status: statusFilter === 'all' ? undefined : statusFilter,
      });
      setEmailLogs(response.logs || []);
    } catch (err: any) {
      console.error('이메일 로그 로드 실패:', err);
    }
  };

  const getStatusChip = (status: string) => {
    switch (status) {
      case 'sent':
        return <Chip icon={<CheckCircle />} label="발송완료" color="success" size="small" />;
      case 'failed':
        return <Chip icon={<ErrorIcon />} label="발송실패" color="error" size="small" />;
      case 'pending':
        return <Chip icon={<WarningIcon />} label="대기중" color="warning" size="small" />;
      default:
        return <Chip label={status} size="small" />;
    }
  };

  if (loading && !stats) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box>
      <Typography variant="h5" gutterBottom fontWeight="bold">
        알림 모니터링
      </Typography>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      {/* 통계 카드 */}
      <Grid container spacing={2} sx={{ mb: 3 }}>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" gap={1}>
                <Mail color="primary" />
                <Box>
                  <Typography variant="body2" color="text.secondary">
                    총 알림
                  </Typography>
                  <Typography variant="h6">{stats?.total_notifications || 0}</Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" gap={1}>
                <CheckCircle sx={{ color: 'success.main' }} />
                <Box>
                  <Typography variant="body2" color="text.secondary">
                    발송완료
                  </Typography>
                  <Typography variant="h6">{stats?.success_count || 0}</Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" gap={1}>
                <ErrorIcon sx={{ color: 'error.main' }} />
                <Box>
                  <Typography variant="body2" color="text.secondary">
                    발송실패
                  </Typography>
                  <Typography variant="h6">{stats?.failed_count || 0}</Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" gap={1}>
                <WarningIcon sx={{ color: 'warning.main' }} />
                <Box>
                  <Typography variant="body2" color="text.secondary">
                    대기중
                  </Typography>
                  <Typography variant="h6">{stats?.pending_count || 0}</Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* 차트 */}
      {chartData.length > 0 && (
        <Paper sx={{ p: 2, mb: 3 }}>
          <Typography variant="h6" gutterBottom>
            알림 발송 현황 (최근 30일)
          </Typography>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Line type="monotone" dataKey="notifications" stroke="#8884d8" name="생성된 알림" />
              <Line type="monotone" dataKey="sent" stroke="#82ca9d" name="발송완료" />
              <Line type="monotone" dataKey="failed" stroke="#ffc658" name="발송실패" />
            </LineChart>
          </ResponsiveContainer>
        </Paper>
      )}

      {/* 이메일 발송 로그 */}
      <Paper sx={{ p: 2, mb: 3 }}>
        <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
          <Typography variant="h6">이메일 발송 로그</Typography>
          <TextField
            select
            size="small"
            label="상태"
            value={statusFilter}
            onChange={(e) => {
              setStatusFilter(e.target.value);
              setEmailLogsPage(1);
              loadEmailLogs();
            }}
            sx={{ width: 150 }}
          >
            <MenuItem value="all">모두</MenuItem>
            <MenuItem value="sent">발송완료</MenuItem>
            <MenuItem value="failed">발송실패</MenuItem>
            <MenuItem value="pending">대기중</MenuItem>
          </TextField>
        </Box>

        <TableContainer>
          <Table>
            <TableHead>
              <TableRow sx={{ backgroundColor: '#f5f5f5' }}>
                <TableCell>ID</TableCell>
                <TableCell>수신자</TableCell>
                <TableCell>알림 개수</TableCell>
                <TableCell>상태</TableCell>
                <TableCell>발송 시간</TableCell>
                <TableCell>비고</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {emailLogs.length > 0 ? (
                emailLogs.map((log) => (
                  <TableRow key={log.id}>
                    <TableCell>{log.id}</TableCell>
                    <TableCell>{log.email_to}</TableCell>
                    <TableCell>{log.notification_count}</TableCell>
                    <TableCell>{getStatusChip(log.status)}</TableCell>
                    <TableCell>
                      {new Date(log.sent_at).toLocaleString('ko-KR')}
                    </TableCell>
                    <TableCell>
                      {log.error_message ? (
                        <Typography variant="caption" color="error">
                          {log.error_message}
                        </Typography>
                      ) : (
                        '-'
                      )}
                    </TableCell>
                  </TableRow>
                ))
              ) : (
                <TableRow>
                  <TableCell colSpan={6} align="center" sx={{ py: 3 }}>
                    <Typography color="text.secondary">데이터 없음</Typography>
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </TableContainer>

        {/* 페이지네이션 */}
        <Box display="flex" justifyContent="center" mt={2}>
          <Pagination
            count={10}
            page={emailLogsPage}
            onChange={(e, newPage) => setEmailLogsPage(newPage)}
          />
        </Box>
      </Paper>

      {/* 알림 목록 */}
      <Paper sx={{ p: 2 }}>
        <Typography variant="h6" gutterBottom>
          최근 알림
        </Typography>

        <TableContainer>
          <Table>
            <TableHead>
              <TableRow sx={{ backgroundColor: '#f5f5f5' }}>
                <TableCell>ID</TableCell>
                <TableCell>사용자 ID</TableCell>
                <TableCell>제목</TableCell>
                <TableCell>가격</TableCell>
                <TableCell>생성 시간</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {notificationsList.length > 0 ? (
                notificationsList.map((notif) => (
                  <TableRow key={notif.id}>
                    <TableCell>{notif.id}</TableCell>
                    <TableCell>{notif.user_id}</TableCell>
                    <TableCell sx={{ maxWidth: 300, overflow: 'hidden', textOverflow: 'ellipsis' }}>
                      {notif.title}
                    </TableCell>
                    <TableCell>
                      {notif.price ? `${notif.price.toLocaleString()}원` : '-'}
                    </TableCell>
                    <TableCell>
                      {new Date(notif.created_at).toLocaleString('ko-KR')}
                    </TableCell>
                  </TableRow>
                ))
              ) : (
                <TableRow>
                  <TableCell colSpan={5} align="center" sx={{ py: 3 }}>
                    <Typography color="text.secondary">데이터 없음</Typography>
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </TableContainer>

        {/* 페이지네이션 */}
        <Box display="flex" justifyContent="center" mt={2}>
          <Pagination
            count={10}
            page={notificationPage}
            onChange={(e, newPage) => setNotificationPage(newPage)}
          />
        </Box>
      </Paper>
    </Box>
  );
};

export default NotificationMonitoring;
