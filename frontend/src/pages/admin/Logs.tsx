/**
 * 관리자 - 로그 조회 화면
 * 시스템 로그, 배치 로그, 사용자 활동 로그 조회
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
  Alert,
  CircularProgress,
  IconButton,
  Tooltip,
  Tabs,
  Tab,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
} from '@mui/material';
import {
  Refresh,
  FilterList,
  Download,
  Visibility,
  Error as ErrorIcon,
  Warning as WarningIcon,
  Info as InfoIcon,
  CheckCircle,
} from '@mui/icons-material';
import { adminApi } from '../../services/admin/adminApi';

interface Log {
  id: number;
  log_level: string;
  category: string;
  message: string;
  details: any;
  created_at: string;
  user_id: number | null;
  ip_address: string | null;
}

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;
  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`log-tabpanel-${index}`}
      aria-labelledby={`log-tab-${index}`}
      {...other}
    >
      {value === index && <Box>{children}</Box>}
    </div>
  );
}

const Logs: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const [logs, setLogs] = useState<Log[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(50);
  const [error, setError] = useState<string | null>(null);

  // 탭
  const [tabValue, setTabValue] = useState(0);

  // 필터
  const [logLevel, setLogLevel] = useState<string>('');
  const [category, setCategory] = useState<string>('');
  const [startDate, setStartDate] = useState<string>('');
  const [endDate, setEndDate] = useState<string>('');
  const [searchQuery, setSearchQuery] = useState<string>('');

  // 상세 모달
  const [detailOpen, setDetailOpen] = useState(false);
  const [selectedLog, setSelectedLog] = useState<Log | null>(null);

  useEffect(() => {
    loadLogs();
  }, [page, rowsPerPage, tabValue, logLevel, category, startDate, endDate]);

  const loadLogs = async () => {
    try {
      setLoading(true);
      setError(null);

      const params: any = {
        page: page + 1,
        limit: rowsPerPage,
      };

      // 탭별 카테고리 설정
      if (tabValue === 0) {
        // 전체 로그
      } else if (tabValue === 1) {
        params.category = 'system';
      } else if (tabValue === 2) {
        params.category = 'batch';
      } else if (tabValue === 3) {
        params.category = 'user_activity';
      }

      // 추가 필터
      if (logLevel) params.log_level = logLevel;
      if (category && tabValue === 0) params.category = category;
      if (startDate) params.start_date = startDate;
      if (endDate) params.end_date = endDate;
      if (searchQuery) params.search = searchQuery;

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

  const handleViewDetail = (log: Log) => {
    setSelectedLog(log);
    setDetailOpen(true);
  };

  const handleExportLogs = async () => {
    try {
      if (!logs || logs.length === 0) {
        setError('내보낼 로그가 없습니다.');
        return;
      }
      const headers = ['시간', '레벨', '메시지', '소스'];
      const csvContent = [
        headers.join(','),
        ...logs.map((log: any) =>
          [
            log.timestamp || log.created_at || '',
            log.level || log.log_level || '',
            `"${(log.message || '').replace(/"/g, '""')}"`,
            log.source || log.module || log.category || '',
          ].join(',')
        ),
      ].join('\n');
      const blob = new Blob(['\uFEFF' + csvContent], { type: 'text/csv;charset=utf-8;' });
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `odin-ai-logs-${new Date().toISOString().split('T')[0]}.csv`;
      link.click();
      URL.revokeObjectURL(url);
    } catch (err: any) {
      console.error('로그 내보내기 실패:', err);
      setError('로그 내보내기에 실패했습니다.');
    }
  };

  const getLevelIcon = (level: string) => {
    switch (level.toUpperCase()) {
      case 'ERROR':
        return <ErrorIcon sx={{ color: '#f44336' }} />;
      case 'WARNING':
        return <WarningIcon sx={{ color: '#ff9800' }} />;
      case 'INFO':
        return <InfoIcon sx={{ color: '#2196f3' }} />;
      case 'DEBUG':
        return <CheckCircle sx={{ color: '#4caf50' }} />;
      default:
        return <InfoIcon />;
    }
  };

  const getLevelChip = (level: string) => {
    const configs: Record<
      string,
      { label: string; color: 'error' | 'warning' | 'info' | 'success' | 'default' }
    > = {
      ERROR: { label: 'ERROR', color: 'error' },
      WARNING: { label: 'WARNING', color: 'warning' },
      INFO: { label: 'INFO', color: 'info' },
      DEBUG: { label: 'DEBUG', color: 'success' },
    };
    const config = configs[level.toUpperCase()] || { label: level, color: 'default' };
    return <Chip label={config.label} color={config.color} size="small" />;
  };

  const getCategoryLabel = (category: string) => {
    const labels: Record<string, string> = {
      system: '시스템',
      batch: '배치',
      user_activity: '사용자 활동',
      api: 'API',
      database: '데이터베이스',
      security: '보안',
    };
    return labels[category] || category;
  };

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Box>
          <Typography variant="h4" gutterBottom>
            로그 조회
          </Typography>
          <Typography variant="body2" color="textSecondary">
            시스템 및 사용자 활동 로그 조회
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
          <Button variant="outlined" startIcon={<Download />} onClick={handleExportLogs}>
            내보내기
          </Button>
        </Box>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {/* 로그 카테고리 탭 */}
      <Paper sx={{ mb: 2 }}>
        <Tabs value={tabValue} onChange={(_, newValue) => setTabValue(newValue)}>
          <Tab label="전체 로그" />
          <Tab label="시스템 로그" />
          <Tab label="배치 로그" />
          <Tab label="사용자 활동" />
        </Tabs>
      </Paper>

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
              <MenuItem value="ERROR">ERROR</MenuItem>
              <MenuItem value="WARNING">WARNING</MenuItem>
              <MenuItem value="INFO">INFO</MenuItem>
              <MenuItem value="DEBUG">DEBUG</MenuItem>
            </TextField>
          </Grid>
          {tabValue === 0 && (
            <Grid item xs={12} sm={3}>
              <TextField
                select
                fullWidth
                label="카테고리"
                value={category}
                onChange={(e) => setCategory(e.target.value)}
                size="small"
              >
                <MenuItem value="">전체</MenuItem>
                <MenuItem value="system">시스템</MenuItem>
                <MenuItem value="batch">배치</MenuItem>
                <MenuItem value="user_activity">사용자 활동</MenuItem>
                <MenuItem value="api">API</MenuItem>
                <MenuItem value="database">데이터베이스</MenuItem>
                <MenuItem value="security">보안</MenuItem>
              </TextField>
            </Grid>
          )}
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
          <Grid item xs={12} sm={tabValue === 0 ? 12 : 3}>
            <TextField
              fullWidth
              placeholder="메시지 검색..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onKeyPress={(e) => {
                if (e.key === 'Enter') {
                  loadLogs();
                }
              }}
              size="small"
            />
          </Grid>
        </Grid>
      </Paper>

      {/* 로그 테이블 */}
      <TabPanel value={tabValue} index={tabValue}>
        <Paper>
          <TableContainer sx={{ maxHeight: 600 }}>
            <Table stickyHeader>
              <TableHead>
                <TableRow>
                  <TableCell>레벨</TableCell>
                  <TableCell>카테고리</TableCell>
                  <TableCell>메시지</TableCell>
                  <TableCell>사용자 ID</TableCell>
                  <TableCell>IP 주소</TableCell>
                  <TableCell>발생 시간</TableCell>
                  <TableCell align="center">작업</TableCell>
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
                    <TableRow key={log.id} hover>
                      <TableCell>
                        <Box display="flex" alignItems="center" gap={1}>
                          {getLevelIcon(log.log_level)}
                          {getLevelChip(log.log_level)}
                        </Box>
                      </TableCell>
                      <TableCell>
                        <Chip label={getCategoryLabel(log.category)} size="small" />
                      </TableCell>
                      <TableCell
                        sx={{
                          maxWidth: 400,
                          overflow: 'hidden',
                          textOverflow: 'ellipsis',
                          whiteSpace: 'nowrap',
                        }}
                      >
                        {log.message}
                      </TableCell>
                      <TableCell>{log.user_id || '-'}</TableCell>
                      <TableCell>{log.ip_address || '-'}</TableCell>
                      <TableCell>
                        {new Date(log.created_at).toLocaleString('ko-KR')}
                      </TableCell>
                      <TableCell align="center">
                        <Tooltip title="상세 보기">
                          <IconButton size="small" onClick={() => handleViewDetail(log)}>
                            <Visibility />
                          </IconButton>
                        </Tooltip>
                      </TableCell>
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
            rowsPerPageOptions={[20, 50, 100]}
          />
        </Paper>
      </TabPanel>

      {/* 로그 상세 모달 */}
      <Dialog open={detailOpen} onClose={() => setDetailOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle>
          로그 상세 정보
          {selectedLog && (
            <Box component="span" sx={{ ml: 2 }}>
              {getLevelChip(selectedLog.log_level)}
            </Box>
          )}
        </DialogTitle>
        <DialogContent>
          {selectedLog && (
            <Box>
              <Grid container spacing={2} sx={{ mb: 2 }}>
                <Grid item xs={6}>
                  <Typography variant="body2" color="textSecondary">
                    로그 ID
                  </Typography>
                  <Typography variant="body1">{selectedLog.id}</Typography>
                </Grid>
                <Grid item xs={6}>
                  <Typography variant="body2" color="textSecondary">
                    카테고리
                  </Typography>
                  <Typography variant="body1">
                    {getCategoryLabel(selectedLog.category)}
                  </Typography>
                </Grid>
                <Grid item xs={6}>
                  <Typography variant="body2" color="textSecondary">
                    사용자 ID
                  </Typography>
                  <Typography variant="body1">{selectedLog.user_id || '-'}</Typography>
                </Grid>
                <Grid item xs={6}>
                  <Typography variant="body2" color="textSecondary">
                    IP 주소
                  </Typography>
                  <Typography variant="body1">{selectedLog.ip_address || '-'}</Typography>
                </Grid>
                <Grid item xs={12}>
                  <Typography variant="body2" color="textSecondary">
                    발생 시간
                  </Typography>
                  <Typography variant="body1">
                    {new Date(selectedLog.created_at).toLocaleString('ko-KR')}
                  </Typography>
                </Grid>
              </Grid>

              <Typography variant="h6" gutterBottom sx={{ mt: 2 }}>
                메시지
              </Typography>
              <Paper variant="outlined" sx={{ p: 2, mb: 2, bgcolor: 'grey.50' }}>
                <Typography variant="body1" sx={{ whiteSpace: 'pre-wrap' }}>
                  {selectedLog.message}
                </Typography>
              </Paper>

              {selectedLog.details && Object.keys(selectedLog.details).length > 0 && (
                <>
                  <Typography variant="h6" gutterBottom>
                    상세 정보
                  </Typography>
                  <Paper variant="outlined" sx={{ p: 2, bgcolor: 'grey.50' }}>
                    <pre
                      style={{
                        margin: 0,
                        fontSize: '0.875rem',
                        overflow: 'auto',
                        maxHeight: '300px',
                      }}
                    >
                      {JSON.stringify(selectedLog.details, null, 2)}
                    </pre>
                  </Paper>
                </>
              )}
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDetailOpen(false)}>닫기</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default Logs;
