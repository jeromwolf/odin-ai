/**
 * 관리자 - 로그 조회 화면
 * 시스템 로그 검색, 필터링, 다운로드
 */

import React, { useEffect, useState } from 'react';
import {
  Box,
  Typography,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TablePagination,
  Chip,
  Button,
  TextField,
  MenuItem,
  Grid,
  Card,
  CardContent,
  Alert,
  CircularProgress,
  IconButton,
  Tooltip,
} from '@mui/material';
import {
  Refresh,
  Download,
  FilterList,
  Error as ErrorIcon,
  Warning,
  Info,
  CheckCircle,
} from '@mui/icons-material';
import { adminApi } from '../../services/admin/adminApi';

interface LogEntry {
  id: number;
  log_level: string;
  module: string;
  message: string;
  details: any;
  created_at: string;
  user_id: number | null;
  ip_address: string | null;
}

interface LogStats {
  total_logs: number;
  error_count: number;
  warning_count: number;
  info_count: number;
  recent_error_rate: number;
}

const LogViewer: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(50);
  const [error, setError] = useState<string | null>(null);
  const [downloading, setDownloading] = useState(false);

  // 필터
  const [logLevel, setLogLevel] = useState<string>('');
  const [module, setModule] = useState<string>('');
  const [keyword, setKeyword] = useState<string>('');
  const [startDate, setStartDate] = useState<string>('');
  const [endDate, setEndDate] = useState<string>('');

  // 통계
  const [logStats, setLogStats] = useState<LogStats | null>(null);

  // 사용 가능한 모듈 목록
  const availableModules = [
    'auth',
    'search',
    'bookmark',
    'notification',
    'batch',
    'api',
    'system',
  ];

  useEffect(() => {
    loadLogs();
    loadLogStats();
  }, [page, rowsPerPage, logLevel, module, keyword, startDate, endDate]);

  const loadLogs = async () => {
    try {
      setLoading(true);
      setError(null);

      const params: any = {
        page: page + 1,
        limit: rowsPerPage,
      };

      if (logLevel) params.log_level = logLevel;
      if (module) params.module = module;
      if (keyword) params.keyword = keyword;
      if (startDate) params.start_date = startDate;
      if (endDate) params.end_date = endDate;

      const data = await adminApi.getLogs(params);
      setLogs(data.logs || []);
      setTotal(data.total || 0);
    } catch (err: any) {
      console.error('로그 조회 실패:', err);
      setError(err.response?.data?.detail || '데이터를 불러오는데 실패했습니다.');
    } finally {
      setLoading(false);
    }
  };

  const loadLogStats = async () => {
    try {
      const stats = await adminApi.getErrorStatistics({});
      setLogStats(stats);
    } catch (err) {
      console.error('로그 통계 조회 실패:', err);
    }
  };

  const handleDownloadLogs = async () => {
    try {
      setDownloading(true);
      setError(null);

      const params: any = {};
      if (logLevel) params.log_level = logLevel;
      if (module) params.module = module;
      if (keyword) params.keyword = keyword;
      if (startDate) params.start_date = startDate;
      if (endDate) params.end_date = endDate;

      const blob = await adminApi.downloadLogs(params);

      // Blob을 다운로드
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `logs_${new Date().toISOString().split('T')[0]}.zip`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);

      alert('로그 다운로드 성공!');
    } catch (err: any) {
      console.error('로그 다운로드 실패:', err);
      setError(err.response?.data?.detail || '로그 다운로드에 실패했습니다.');
    } finally {
      setDownloading(false);
    }
  };

  const getLevelChip = (level: string) => {
    const configs: Record<string, { icon: React.ReactNode; color: 'error' | 'warning' | 'info' | 'success' | 'default' }> = {
      ERROR: { icon: <ErrorIcon />, color: 'error' },
      WARNING: { icon: <Warning />, color: 'warning' },
      INFO: { icon: <Info />, color: 'info' },
      DEBUG: { icon: <CheckCircle />, color: 'default' },
    };
    const config = configs[level] || { icon: <Info />, color: 'default' };
    return (
      <Chip
        label={level}
        color={config.color}
        size="small"
      />
    );
  };

  const formatDetails = (details: any) => {
    if (!details) return '-';
    if (typeof details === 'string') return details;
    return JSON.stringify(details, null, 2);
  };

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Box>
          <Typography variant="h4" gutterBottom>
            로그 조회
          </Typography>
          <Typography variant="body2" color="textSecondary">
            시스템 로그 검색 및 분석
          </Typography>
        </Box>
        <Box>
          <Button
            variant="outlined"
            startIcon={<Refresh />}
            onClick={loadLogs}
            sx={{ mr: 1 }}
          >
            새로고침
          </Button>
          <Button
            variant="contained"
            startIcon={<Download />}
            onClick={handleDownloadLogs}
            disabled={downloading}
          >
            {downloading ? <CircularProgress size={24} /> : '다운로드 (ZIP)'}
          </Button>
        </Box>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {/* 통계 카드 */}
      {logStats && (
        <Grid container spacing={3} sx={{ mb: 3 }}>
          <Grid item xs={12} md={3}>
            <Card>
              <CardContent>
                <Box display="flex" alignItems="center">
                  <Info sx={{ fontSize: 40, mr: 2, color: '#2196f3' }} />
                  <Box>
                    <Typography variant="body2" color="textSecondary">
                      전체 로그
                    </Typography>
                    <Typography variant="h5">{logStats.total_logs.toLocaleString()}</Typography>
                  </Box>
                </Box>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} md={3}>
            <Card>
              <CardContent>
                <Box display="flex" alignItems="center">
                  <ErrorIcon sx={{ fontSize: 40, mr: 2, color: '#f44336' }} />
                  <Box>
                    <Typography variant="body2" color="textSecondary">
                      에러
                    </Typography>
                    <Typography variant="h5">{logStats.error_count.toLocaleString()}</Typography>
                  </Box>
                </Box>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} md={3}>
            <Card>
              <CardContent>
                <Box display="flex" alignItems="center">
                  <Warning sx={{ fontSize: 40, mr: 2, color: '#ff9800' }} />
                  <Box>
                    <Typography variant="body2" color="textSecondary">
                      경고
                    </Typography>
                    <Typography variant="h5">{logStats.warning_count.toLocaleString()}</Typography>
                  </Box>
                </Box>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} md={3}>
            <Card>
              <CardContent>
                <Box display="flex" alignItems="center">
                  <Info sx={{ fontSize: 40, mr: 2, color: '#4caf50' }} />
                  <Box>
                    <Typography variant="body2" color="textSecondary">
                      정보
                    </Typography>
                    <Typography variant="h5">{logStats.info_count.toLocaleString()}</Typography>
                  </Box>
                </Box>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      )}

      {/* 필터 */}
      <Paper sx={{ p: 2, mb: 2 }}>
        <Grid container spacing={2} alignItems="center">
          <Grid item xs={12} sm={3}>
            <TextField
              select
              fullWidth
              label="로그 레벨"
              value={logLevel}
              onChange={(e) => setLogLevel(e.target.value)}
              size="small"
            >
              <MenuItem value="">전체</MenuItem>
              <MenuItem value="ERROR">에러</MenuItem>
              <MenuItem value="WARNING">경고</MenuItem>
              <MenuItem value="INFO">정보</MenuItem>
              <MenuItem value="DEBUG">디버그</MenuItem>
            </TextField>
          </Grid>
          <Grid item xs={12} sm={3}>
            <TextField
              select
              fullWidth
              label="모듈"
              value={module}
              onChange={(e) => setModule(e.target.value)}
              size="small"
            >
              <MenuItem value="">전체</MenuItem>
              {availableModules.map((mod) => (
                <MenuItem key={mod} value={mod}>
                  {mod}
                </MenuItem>
              ))}
            </TextField>
          </Grid>
          <Grid item xs={12} sm={3}>
            <TextField
              type="date"
              fullWidth
              label="시작 날짜"
              value={startDate}
              onChange={(e) => setStartDate(e.target.value)}
              InputLabelProps={{ shrink: true }}
              size="small"
            />
          </Grid>
          <Grid item xs={12} sm={3}>
            <TextField
              type="date"
              fullWidth
              label="종료 날짜"
              value={endDate}
              onChange={(e) => setEndDate(e.target.value)}
              InputLabelProps={{ shrink: true }}
              size="small"
            />
          </Grid>
          <Grid item xs={12}>
            <TextField
              fullWidth
              placeholder="키워드 검색..."
              value={keyword}
              onChange={(e) => setKeyword(e.target.value)}
              size="small"
              InputProps={{
                startAdornment: <FilterList sx={{ mr: 1, color: 'text.secondary' }} />,
              }}
            />
          </Grid>
        </Grid>
      </Paper>

      {/* 로그 테이블 */}
      <Paper>
        <TableContainer sx={{ maxHeight: 600 }}>
          <Table stickyHeader>
            <TableHead>
              <TableRow>
                <TableCell>시간</TableCell>
                <TableCell>레벨</TableCell>
                <TableCell>모듈</TableCell>
                <TableCell>메시지</TableCell>
                <TableCell>상세</TableCell>
                <TableCell>사용자 ID</TableCell>
                <TableCell>IP 주소</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {loading ? (
                <TableRow>
                  <TableCell colSpan={7} align="center">
                    <CircularProgress />
                  </TableCell>
                </TableRow>
              ) : logs.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={7} align="center">
                    로그가 없습니다
                  </TableCell>
                </TableRow>
              ) : (
                logs.map((log) => (
                  <TableRow
                    key={log.id}
                    hover
                    sx={{
                      backgroundColor:
                        log.log_level === 'ERROR'
                          ? 'rgba(244, 67, 54, 0.05)'
                          : log.log_level === 'WARNING'
                          ? 'rgba(255, 152, 0, 0.05)'
                          : 'transparent',
                    }}
                  >
                    <TableCell sx={{ whiteSpace: 'nowrap' }}>
                      {new Date(log.created_at).toLocaleString('ko-KR')}
                    </TableCell>
                    <TableCell>{getLevelChip(log.log_level)}</TableCell>
                    <TableCell>
                      <Chip label={log.module} size="small" variant="outlined" />
                    </TableCell>
                    <TableCell sx={{ maxWidth: 400 }}>
                      <Typography variant="body2" noWrap>
                        {log.message}
                      </Typography>
                    </TableCell>
                    <TableCell sx={{ maxWidth: 200 }}>
                      <Tooltip title={formatDetails(log.details)} arrow>
                        <Typography
                          variant="caption"
                          noWrap
                          sx={{ cursor: 'pointer', color: 'text.secondary' }}
                        >
                          {formatDetails(log.details)}
                        </Typography>
                      </Tooltip>
                    </TableCell>
                    <TableCell>{log.user_id || '-'}</TableCell>
                    <TableCell>{log.ip_address || '-'}</TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </TableContainer>
        <TablePagination
          component="div"
          count={total}
          page={page}
          onPageChange={(_, newPage) => setPage(newPage)}
          rowsPerPage={rowsPerPage}
          onRowsPerPageChange={(e) => {
            setRowsPerPage(parseInt(e.target.value, 10));
            setPage(0);
          }}
          labelRowsPerPage="페이지당 행 수:"
          rowsPerPageOptions={[50, 100, 200]}
        />
      </Paper>
    </Box>
  );
};

export default LogViewer;
