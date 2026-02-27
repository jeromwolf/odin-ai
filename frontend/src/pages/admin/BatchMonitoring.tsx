/**
 * 관리자 - 배치 모니터링 화면
 * 배치 실행 이력, 상세 정보, 수동 실행
 */

import React, { useEffect, useState, useCallback } from 'react';
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
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  MenuItem,
  Grid,
  Alert,
  CircularProgress,
  IconButton,
  Tooltip,
  Checkbox,
  FormControlLabel,
  Divider,
  Stepper,
  Step,
  StepLabel,
  LinearProgress,
} from '@mui/material';
import {
  Refresh,
  PlayArrow,
  Visibility,
  Schedule,
} from '@mui/icons-material';
import { adminApi } from '../../services/admin/adminApi';
import { PageHeader } from '../../components/common';
import { useNotification } from '../../contexts/NotificationContext';
import { formatKRDate } from '../../utils/formatters';

interface BatchExecution {
  id: number;
  batch_type: string;
  status: string;
  start_time: string;
  end_time: string | null;
  duration_seconds: number | null;
  total_items: number;
  success_items: number;
  failed_items: number;
  error_message: string | null;
}

const BatchMonitoring: React.FC = () => {
  const { showSuccess, showError } = useNotification();
  const [loading, setLoading] = useState(false);
  const [executions, setExecutions] = useState<BatchExecution[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(20);
  const [error, setError] = useState<string | null>(null);

  // 필터
  const [batchType, setBatchType] = useState<string>('');
  const [status, setStatus] = useState<string>('');
  const [startDate, setStartDate] = useState<string>('');
  const [endDate, setEndDate] = useState<string>('');

  // 상세 모달
  const [detailOpen, setDetailOpen] = useState(false);
  const [selectedExecution, setSelectedExecution] = useState<any>(null);

  // 수동 실행 모달
  const [executeOpen, setExecuteOpen] = useState(false);
  const [executeBatchType, setExecuteBatchType] = useState<string>('production');
  // 한국시간 기준 오늘 날짜 (UTC 변환 문제 방지)
  const getKoreaDateString = () => {
    const now = new Date();
    const koreaOffset = 9 * 60; // KST는 UTC+9
    const koreaTime = new Date(now.getTime() + koreaOffset * 60 * 1000);
    return koreaTime.toISOString().split('T')[0];
  };
  const [executeStartDate, setExecuteStartDate] = useState<string>(getKoreaDateString());
  const [executeEndDate, setExecuteEndDate] = useState<string>(getKoreaDateString());
  const [enableNotification, setEnableNotification] = useState<boolean>(true);
  const [executeLoading, setExecuteLoading] = useState(false);

  // 진행률 표시
  const [progressData, setProgressData] = useState<any>(null);

  // 자동 새로고침 상태
  const [autoRefresh, setAutoRefresh] = useState<boolean>(true);
  const [lastRefreshTime, setLastRefreshTime] = useState<Date>(new Date());

  const loadExecutions = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      const params: any = {
        page: page + 1,
        limit: rowsPerPage,
      };

      if (batchType) params.batch_type = batchType;
      if (status) params.status = status;
      if (startDate) params.start_date = startDate;
      if (endDate) params.end_date = endDate;

      const data = await adminApi.getBatchExecutions(params);
      setExecutions(data.executions || []);
      setTotal(data.total || 0);
    } catch (err: any) {
      console.error('배치 실행 이력 조회 실패:', err);
      setError(err.response?.data?.detail || '데이터를 불러오는데 실패했습니다.');
    } finally {
      setLoading(false);
    }
  }, [page, rowsPerPage, batchType, status, startDate, endDate]);

  // 페이지/필터 변경 시 데이터 로드
  useEffect(() => {
    loadExecutions();
  }, [loadExecutions]);

  // 실행 중인 배치 진행률 조회
  const loadProgress = useCallback(async (executionId: number) => {
    try {
      const data = await adminApi.getBatchProgress(executionId);
      setProgressData(data);
    } catch {
      setProgressData(null);
    }
  }, []);

  // 실행 중인 배치가 있으면 진행률 자동 조회
  useEffect(() => {
    const runningBatch = executions.find((e) => e.status === 'running');
    if (runningBatch) {
      loadProgress(runningBatch.id);
    } else {
      setProgressData(null);
    }
  }, [executions, loadProgress]);

  // 자동 새로고침 (5초마다)
  useEffect(() => {
    if (!autoRefresh) return;

    const intervalId = setInterval(() => {
      loadExecutions();
      setLastRefreshTime(new Date());
    }, 5000); // 5초마다 새로고침

    return () => clearInterval(intervalId);
  }, [autoRefresh, loadExecutions]);

  const handleViewDetail = async (executionId: number) => {
    try {
      const detail = await adminApi.getBatchExecutionDetail(executionId);
      setSelectedExecution(detail);
      setDetailOpen(true);
    } catch (err: any) {
      console.error('배치 상세 정보 조회 실패:', err);
      setError(err.response?.data?.detail || '상세 정보를 불러오는데 실패했습니다.');
    }
  };

  const handleExecuteBatch = async () => {
    try {
      setExecuteLoading(true);
      const result = await adminApi.executeBatchManual({
        batch_type: executeBatchType,
        test_mode: false,
        start_date: executeStartDate,
        end_date: executeEndDate,
        enable_notification: enableNotification,
      });
      showSuccess(`배치 실행 요청 성공! Task ID: ${result.task_id} - ${result.message}`);
      setExecuteOpen(false);
      loadExecutions(); // 목록 새로고침
    } catch (err: any) {
      console.error('배치 수동 실행 실패:', err);
      const errMsg = err.response?.data?.detail || '배치 실행에 실패했습니다.';
      showError(errMsg);
      setError(errMsg);
    } finally {
      setExecuteLoading(false);
    }
  };

  const getStatusChip = (status: string) => {
    const configs: Record<string, { label: string; color: 'success' | 'error' | 'warning' | 'info' }> = {
      success: { label: '성공', color: 'success' },
      failed: { label: '실패', color: 'error' },
      running: { label: '실행중', color: 'info' },
    };
    const config = configs[status] || { label: status, color: 'warning' };
    return <Chip label={config.label} color={config.color} size="small" />;
  };

  const getBatchTypeLabel = (type: string) => {
    const labels: Record<string, string> = {
      production: '전체 배치',
      collector: '데이터 수집',
      downloader: '파일 다운로드',
      processor: '문서 처리',
      notification: '알림만 실행',
    };
    return labels[type] || type;
  };

  return (
    <Box>
      <PageHeader
        title="배치 모니터링"
        subtitle="배치 프로그램 실행 이력 및 상태 확인"
        icon={<Schedule />}
        action={
          <>
            <FormControlLabel
              control={
                <Checkbox
                  checked={autoRefresh}
                  onChange={(e) => setAutoRefresh(e.target.checked)}
                  color="primary"
                />
              }
              label="자동 새로고침 (5초)"
              sx={{ mr: 1 }}
            />
            <Button
              variant="outlined"
              startIcon={<Refresh />}
              onClick={loadExecutions}
              sx={{ mr: 1 }}
            >
              새로고침
            </Button>
            <Button
              variant="contained"
              startIcon={<PlayArrow />}
              onClick={() => setExecuteOpen(true)}
            >
              수동 실행
            </Button>
          </>
        }
      />
      {autoRefresh && (
        <Typography variant="caption" color="textSecondary" sx={{ display: 'block', mt: -2, mb: 2 }}>
          🔄 자동 새로고침 활성화 • 마지막 업데이트: {lastRefreshTime.toLocaleTimeString('ko-KR')}
        </Typography>
      )}

      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {/* 필터 */}
      <Paper sx={{ p: 2, mb: 2 }}>
        <Grid container spacing={2} alignItems="center">
          <Grid item xs={12} sm={3}>
            <TextField
              select
              fullWidth
              label="배치 타입"
              value={batchType}
              onChange={(e) => setBatchType(e.target.value)}
              size="small"
            >
              <MenuItem value="">전체</MenuItem>
              <MenuItem value="collector">데이터 수집</MenuItem>
              <MenuItem value="downloader">파일 다운로드</MenuItem>
              <MenuItem value="processor">문서 처리</MenuItem>
              <MenuItem value="notification">알림 발송</MenuItem>
            </TextField>
          </Grid>
          <Grid item xs={12} sm={3}>
            <TextField
              select
              fullWidth
              label="상태"
              value={status}
              onChange={(e) => setStatus(e.target.value)}
              size="small"
            >
              <MenuItem value="">전체</MenuItem>
              <MenuItem value="success">성공</MenuItem>
              <MenuItem value="failed">실패</MenuItem>
              <MenuItem value="running">실행중</MenuItem>
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
        </Grid>
      </Paper>

      {/* 실행 중인 배치 진행률 */}
      {progressData && (
        <Paper sx={{ p: 3, mb: 2 }}>
          <Typography variant="h6" gutterBottom>
            실행 중인 배치 진행률
          </Typography>
          <Stepper activeStep={progressData.current_phase - 1} alternativeLabel>
            {progressData.phases.map((phase: any) => (
              <Step key={phase.phase} completed={phase.status === 'completed'}>
                <StepLabel error={phase.status === 'failed'}>
                  {phase.name}
                </StepLabel>
              </Step>
            ))}
          </Stepper>
          {progressData.current_message && (
            <Typography variant="body2" color="textSecondary" sx={{ mt: 2, textAlign: 'center' }}>
              {progressData.current_message}
            </Typography>
          )}
          <LinearProgress sx={{ mt: 2 }} />
        </Paper>
      )}

      {/* 배치 실행 이력 테이블 */}
      <Paper>
        <TableContainer>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>ID</TableCell>
                <TableCell>배치 타입</TableCell>
                <TableCell>상태</TableCell>
                <TableCell>실행 시간</TableCell>
                <TableCell align="right">처리 건수</TableCell>
                <TableCell align="right">성공</TableCell>
                <TableCell align="right">실패</TableCell>
                <TableCell align="right">소요 시간</TableCell>
                <TableCell align="center">작업</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {loading ? (
                <TableRow>
                  <TableCell colSpan={9} align="center">
                    <CircularProgress />
                  </TableCell>
                </TableRow>
              ) : executions.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={9} align="center">
                    배치 실행 이력이 없습니다
                  </TableCell>
                </TableRow>
              ) : (
                executions.map((execution) => (
                  <TableRow key={execution.id} hover>
                    <TableCell>{execution.id}</TableCell>
                    <TableCell>{getBatchTypeLabel(execution.batch_type)}</TableCell>
                    <TableCell>{getStatusChip(execution.status)}</TableCell>
                    <TableCell>
                      {formatKRDate(execution.start_time, 'yyyy.MM.dd HH:mm')}
                    </TableCell>
                    <TableCell align="right">{execution.total_items}</TableCell>
                    <TableCell align="right">{execution.success_items}</TableCell>
                    <TableCell align="right">{execution.failed_items}</TableCell>
                    <TableCell align="right">
                      {execution.duration_seconds
                        ? `${execution.duration_seconds}초`
                        : '-'}
                    </TableCell>
                    <TableCell align="center">
                      <Tooltip title="상세 보기">
                        <IconButton
                          size="small"
                          onClick={() => handleViewDetail(execution.id)}
                        >
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
        />
      </Paper>

      {/* 상세 정보 모달 */}
      <Dialog open={detailOpen} onClose={() => setDetailOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle>배치 실행 상세 정보</DialogTitle>
        <DialogContent>
          {selectedExecution && (
            <Box>
              <Grid container spacing={2} sx={{ mb: 2 }}>
                <Grid item xs={6}>
                  <Typography variant="body2" color="textSecondary">
                    배치 타입
                  </Typography>
                  <Typography variant="body1">
                    {getBatchTypeLabel(selectedExecution.execution.batch_type)}
                  </Typography>
                </Grid>
                <Grid item xs={6}>
                  <Typography variant="body2" color="textSecondary">
                    상태
                  </Typography>
                  {getStatusChip(selectedExecution.execution.status)}
                </Grid>
                <Grid item xs={6}>
                  <Typography variant="body2" color="textSecondary">
                    처리 건수
                  </Typography>
                  <Typography variant="body1">
                    {selectedExecution.execution.total_items}건
                  </Typography>
                </Grid>
                <Grid item xs={6}>
                  <Typography variant="body2" color="textSecondary">
                    성공률
                  </Typography>
                  <Typography variant="body1">
                    {selectedExecution.statistics.success_rate.toFixed(1)}%
                  </Typography>
                </Grid>
              </Grid>

              {selectedExecution.execution.error_message && (
                <Alert severity="error" sx={{ mb: 2 }}>
                  {selectedExecution.execution.error_message}
                </Alert>
              )}

              <Typography variant="h6" gutterBottom sx={{ mt: 2 }}>
                상세 로그 (최근 10개)
              </Typography>
              <TableContainer component={Paper} variant="outlined">
                <Table size="small">
                  <TableHead>
                    <TableRow>
                      <TableCell>레벨</TableCell>
                      <TableCell>메시지</TableCell>
                      <TableCell>시간</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {selectedExecution.detail_logs.slice(0, 10).map((log: any) => (
                      <TableRow key={log.id}>
                        <TableCell>
                          <Chip
                            label={log.log_level}
                            size="small"
                            color={
                              log.log_level === 'ERROR'
                                ? 'error'
                                : log.log_level === 'WARNING'
                                ? 'warning'
                                : 'default'
                            }
                          />
                        </TableCell>
                        <TableCell>{log.message}</TableCell>
                        <TableCell>
                          {formatKRDate(log.created_at, 'yyyy.MM.dd HH:mm')}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDetailOpen(false)}>닫기</Button>
        </DialogActions>
      </Dialog>

      {/* 수동 실행 모달 */}
      <Dialog open={executeOpen} onClose={() => setExecuteOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>배치 수동 실행</DialogTitle>
        <DialogContent>
          <Box sx={{ pt: 1 }}>
            <TextField
              select
              fullWidth
              label="배치 타입"
              value={executeBatchType}
              onChange={(e) => setExecuteBatchType(e.target.value)}
              margin="normal"
              helperText="production: 전체 배치(수집+처리), notification: 알림만"
            >
              <MenuItem value="production">전체 배치 (수집 + 처리 + 알림)</MenuItem>
              <MenuItem value="notification">알림만 실행 (수집 안 함)</MenuItem>
              <MenuItem value="collector">데이터 수집만</MenuItem>
              <MenuItem value="downloader">파일 다운로드만</MenuItem>
              <MenuItem value="processor">문서 처리만</MenuItem>
            </TextField>

            <Divider sx={{ my: 2 }} />

            <Typography variant="subtitle2" gutterBottom sx={{ mt: 2 }}>
              수집 기간 설정
            </Typography>
            <Grid container spacing={2}>
              <Grid item xs={6}>
                <TextField
                  fullWidth
                  type="date"
                  label="시작 날짜"
                  value={executeStartDate}
                  onChange={(e) => setExecuteStartDate(e.target.value)}
                  InputLabelProps={{ shrink: true }}
                />
              </Grid>
              <Grid item xs={6}>
                <TextField
                  fullWidth
                  type="date"
                  label="종료 날짜"
                  value={executeEndDate}
                  onChange={(e) => setExecuteEndDate(e.target.value)}
                  InputLabelProps={{ shrink: true }}
                />
              </Grid>
            </Grid>

            <Divider sx={{ my: 2 }} />

            <FormControlLabel
              control={
                <Checkbox
                  checked={enableNotification}
                  onChange={(e) => setEnableNotification(e.target.checked)}
                  color="primary"
                />
              }
              label="알림 실행 (이메일 발송)"
            />

            <Alert severity="info" sx={{ mt: 2 }}>
              💡 <strong>알림 동작 방식:</strong>
              <br />
              • 선택한 기간의 입찰공고를 사용자 알림 규칙과 매칭
              <br />
              • 매칭되면 알림 생성 + 이메일 발송 (설정 시)
              <br />• 중복 알림 자동 방지
            </Alert>

            <Alert severity="warning" sx={{ mt: 1 }}>
              ⚠️ 실행 중인 배치가 있는 경우 충돌이 발생할 수 있습니다.
            </Alert>
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setExecuteOpen(false)}>취소</Button>
          <Button
            onClick={handleExecuteBatch}
            variant="contained"
            disabled={executeLoading}
            startIcon={executeLoading ? <CircularProgress size={20} /> : <PlayArrow />}
          >
            {executeLoading ? '실행 중...' : '배치 실행'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default BatchMonitoring;
