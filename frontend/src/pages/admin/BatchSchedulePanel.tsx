/**
 * 배치 스케줄 관리 패널
 * 알람 스타일의 스케줄 등록/수정/삭제/토글 UI
 */

import React, { useEffect, useState, useCallback } from 'react';
import {
  Box,
  Typography,
  Paper,
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
  Chip,
  Switch,
  FormControlLabel,
  Checkbox,
  FormGroup,
  Divider,
} from '@mui/material';
import {
  Add,
  Edit,
  Delete,
  AccessTime,
  CheckCircle,
  Cancel,
} from '@mui/icons-material';
import { adminApi } from '../../services/admin/adminApi';
import { useNotification } from '../../contexts/NotificationContext';

// ============================================
// 타입 정의
// ============================================

interface BatchSchedule {
  id: number;
  label: string;
  schedule_hour: number;
  schedule_minute: number;
  days_of_week: string | null;
  is_active: boolean;
  options: Record<string, boolean>;
  next_run: string | null;
  created_at: string;
  updated_at: string;
}

interface SchedulerStatus {
  is_running: boolean;
  total_schedules: number;
  active_schedules: number;
  next_run: string | null;
}

interface ScheduleFormData {
  label: string;
  schedule_hour: number;
  schedule_minute: number;
  days_of_week: string[];
  options: Record<string, boolean>;
}

// ============================================
// 상수
// ============================================

const DAYS_OF_WEEK = [
  { key: '0', label: '월' },
  { key: '1', label: '화' },
  { key: '2', label: '수' },
  { key: '3', label: '목' },
  { key: '4', label: '금' },
  { key: '5', label: '토' },
  { key: '6', label: '일' },
];

const OPTION_LABELS: Record<string, string> = {
  enable_notification: '알림 발송',
  enable_embedding: '임베딩 생성',
  enable_graph_sync: '그래프 동기화',
  enable_graphrag: 'GraphRAG',
  enable_award_collection: '낙찰정보 수집',
  enable_daily_digest: '일일 다이제스트',
};

const MINUTE_OPTIONS = [0, 10, 20, 30, 40, 50];

const DEFAULT_FORM: ScheduleFormData = {
  label: '',
  schedule_hour: 7,
  schedule_minute: 0,
  days_of_week: [],
  options: {
    enable_notification: true,
    enable_embedding: false,
    enable_graph_sync: false,
    enable_graphrag: false,
    enable_award_collection: false,
    enable_daily_digest: false,
  },
};

// ============================================
// 헬퍼 함수
// ============================================

const formatTime = (hour: number, minute: number): string => {
  return `${String(hour).padStart(2, '0')}:${String(minute).padStart(2, '0')}`;
};

const parseDaysOfWeek = (daysStr: string | null): string[] => {
  if (!daysStr) return [];
  return daysStr.split(',').map((d) => d.trim()).filter(Boolean);
};

const formatDaysOfWeek = (days: string[]): string => {
  if (days.length === 0 || days.length === 7) return '매일';
  const dayMap: Record<string, string> = {
    '0': '월', '1': '화', '2': '수', '3': '목',
    '4': '금', '5': '토', '6': '일',
    mon: '월', tue: '화', wed: '수', thu: '목',
    fri: '금', sat: '토', sun: '일',
  };
  return days.map((d) => dayMap[d] || d).join(', ');
};

const formatNextRun = (nextRun: string | null): string => {
  if (!nextRun) return '-';
  try {
    const date = new Date(nextRun);
    const now = new Date();
    const diffMs = date.getTime() - now.getTime();

    if (diffMs < 0) return '곧 실행';

    const diffMin = Math.floor(diffMs / 60000);
    if (diffMin < 60) return `${diffMin}분 후`;

    const diffHour = Math.floor(diffMin / 60);
    if (diffHour < 24) return `${diffHour}시간 ${diffMin % 60}분 후`;

    const diffDay = Math.floor(diffHour / 24);
    return `${diffDay}일 ${diffHour % 24}시간 후`;
  } catch {
    return '-';
  }
};

// ============================================
// 메인 컴포넌트
// ============================================

const BatchSchedulePanel: React.FC = () => {
  const { showSuccess, showError } = useNotification();

  // 상태
  const [schedules, setSchedules] = useState<BatchSchedule[]>([]);
  const [schedulerStatus, setSchedulerStatus] = useState<SchedulerStatus | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // 다이얼로그 상태
  const [dialogOpen, setDialogOpen] = useState(false);
  const [dialogMode, setDialogMode] = useState<'create' | 'edit'>('create');
  const [editingId, setEditingId] = useState<number | null>(null);
  const [formData, setFormData] = useState<ScheduleFormData>({ ...DEFAULT_FORM });
  const [saving, setSaving] = useState(false);

  // 삭제 확인 다이얼로그
  const [deleteConfirmOpen, setDeleteConfirmOpen] = useState(false);
  const [deletingId, setDeletingId] = useState<number | null>(null);

  // ============================================
  // 데이터 로딩
  // ============================================

  const loadSchedules = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await adminApi.getBatchSchedules();
      setSchedules(data.schedules || []);
    } catch (err: any) {
      console.error('스케줄 목록 조회 실패:', err);
      setError(err.response?.data?.detail || '스케줄 목록을 불러오는데 실패했습니다.');
    } finally {
      setLoading(false);
    }
  }, []);

  const loadSchedulerStatus = useCallback(async () => {
    try {
      const data = await adminApi.getSchedulerStatus();
      setSchedulerStatus(data);
    } catch (err: any) {
      console.error('스케줄러 상태 조회 실패:', err);
    }
  }, []);

  useEffect(() => {
    loadSchedules();
    loadSchedulerStatus();
  }, [loadSchedules, loadSchedulerStatus]);

  // ============================================
  // 핸들러
  // ============================================

  const handleToggle = async (id: number) => {
    try {
      await adminApi.toggleBatchSchedule(id);
      setSchedules((prev) =>
        prev.map((s) => (s.id === id ? { ...s, is_active: !s.is_active } : s))
      );
      showSuccess('스케줄 상태가 변경되었습니다.');
      loadSchedulerStatus();
    } catch (err: any) {
      console.error('스케줄 토글 실패:', err);
      showError(err.response?.data?.detail || '상태 변경에 실패했습니다.');
    }
  };

  const handleOpenCreate = () => {
    setDialogMode('create');
    setEditingId(null);
    setFormData({ ...DEFAULT_FORM });
    setDialogOpen(true);
  };

  const handleOpenEdit = (schedule: BatchSchedule) => {
    setDialogMode('edit');
    setEditingId(schedule.id);
    setFormData({
      label: schedule.label,
      schedule_hour: schedule.schedule_hour,
      schedule_minute: schedule.schedule_minute,
      days_of_week: parseDaysOfWeek(schedule.days_of_week),
      options: { ...DEFAULT_FORM.options, ...schedule.options },
    });
    setDialogOpen(true);
  };

  const handleSave = async () => {
    if (!formData.label.trim()) {
      showError('스케줄 이름을 입력해주세요.');
      return;
    }

    try {
      setSaving(true);
      const payload = {
        label: formData.label.trim(),
        schedule_hour: formData.schedule_hour,
        schedule_minute: formData.schedule_minute,
        days_of_week: formData.days_of_week.length > 0 && formData.days_of_week.length < 7
          ? formData.days_of_week.join(',')
          : null,
        options: formData.options,
      };

      if (dialogMode === 'create') {
        await adminApi.createBatchSchedule({ ...payload, is_active: true });
        showSuccess('스케줄이 생성되었습니다.');
      } else if (editingId !== null) {
        await adminApi.updateBatchSchedule(editingId, payload);
        showSuccess('스케줄이 수정되었습니다.');
      }

      setDialogOpen(false);
      loadSchedules();
      loadSchedulerStatus();
    } catch (err: any) {
      console.error('스케줄 저장 실패:', err);
      showError(err.response?.data?.detail || '스케줄 저장에 실패했습니다.');
    } finally {
      setSaving(false);
    }
  };

  const handleDeleteConfirm = (id: number) => {
    setDeletingId(id);
    setDeleteConfirmOpen(true);
  };

  const handleDelete = async () => {
    if (deletingId === null) return;

    try {
      await adminApi.deleteBatchSchedule(deletingId);
      showSuccess('스케줄이 삭제되었습니다.');
      setDeleteConfirmOpen(false);
      setDeletingId(null);
      loadSchedules();
      loadSchedulerStatus();
    } catch (err: any) {
      console.error('스케줄 삭제 실패:', err);
      showError(err.response?.data?.detail || '스케줄 삭제에 실패했습니다.');
    }
  };

  const handleDayToggle = (dayKey: string) => {
    setFormData((prev) => {
      const days = prev.days_of_week.includes(dayKey)
        ? prev.days_of_week.filter((d) => d !== dayKey)
        : [...prev.days_of_week, dayKey];
      return { ...prev, days_of_week: days };
    });
  };

  const handleAllDaysToggle = () => {
    setFormData((prev) => {
      const allSelected = prev.days_of_week.length === 7;
      return {
        ...prev,
        days_of_week: allSelected ? [] : DAYS_OF_WEEK.map((d) => d.key),
      };
    });
  };

  const handleOptionToggle = (key: string) => {
    setFormData((prev) => ({
      ...prev,
      options: { ...prev.options, [key]: !prev.options[key] },
    }));
  };

  // ============================================
  // 렌더링
  // ============================================

  return (
    <Paper sx={{ p: 3, mb: 3 }}>
      {/* 헤더 */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <AccessTime color="primary" />
          <Typography variant="h6">배치 스케줄 관리</Typography>
        </Box>
        <Button
          variant="contained"
          size="small"
          startIcon={<Add />}
          onClick={handleOpenCreate}
        >
          추가
        </Button>
      </Box>

      {/* 스케줄러 상태 바 */}
      {schedulerStatus && (
        <Box
          sx={{
            display: 'flex',
            alignItems: 'center',
            gap: 2,
            p: 1.5,
            mb: 2,
            borderRadius: 1,
            bgcolor: schedulerStatus.is_running ? 'success.50' : 'grey.100',
            border: 1,
            borderColor: schedulerStatus.is_running ? 'success.200' : 'grey.300',
          }}
        >
          <Chip
            icon={schedulerStatus.is_running ? <CheckCircle /> : <Cancel />}
            label={schedulerStatus.is_running ? '스케줄러 실행중' : '스케줄러 중지됨'}
            color={schedulerStatus.is_running ? 'success' : 'default'}
            size="small"
            variant="outlined"
          />
          <Typography variant="body2" color="textSecondary">
            전체 {schedulerStatus.total_schedules}개 / 활성 {schedulerStatus.active_schedules}개
          </Typography>
          {schedulerStatus.next_run && (
            <Typography variant="body2" color="textSecondary">
              | 다음 실행: {formatNextRun(schedulerStatus.next_run)}
            </Typography>
          )}
        </Box>
      )}

      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {/* 스케줄 목록 */}
      {loading ? (
        <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
          <CircularProgress />
        </Box>
      ) : schedules.length === 0 ? (
        <Alert severity="info">
          등록된 스케줄이 없습니다. "추가" 버튼을 눌러 새 스케줄을 등록해주세요.
        </Alert>
      ) : (
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1.5 }}>
          {schedules.map((schedule) => (
            <Paper
              key={schedule.id}
              variant="outlined"
              sx={{
                p: 2,
                opacity: schedule.is_active ? 1 : 0.6,
                transition: 'opacity 0.2s',
              }}
            >
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                {/* ON/OFF 토글 */}
                <Switch
                  checked={schedule.is_active}
                  onChange={() => handleToggle(schedule.id)}
                  color="primary"
                />

                {/* 시간 표시 */}
                <Typography
                  variant="h4"
                  sx={{
                    fontWeight: 300,
                    fontVariantNumeric: 'tabular-nums',
                    minWidth: 100,
                    color: schedule.is_active ? 'text.primary' : 'text.disabled',
                  }}
                >
                  {formatTime(schedule.schedule_hour, schedule.schedule_minute)}
                </Typography>

                {/* 정보 영역 */}
                <Box sx={{ flex: 1, minWidth: 0 }}>
                  <Typography
                    variant="subtitle1"
                    sx={{
                      fontWeight: 500,
                      color: schedule.is_active ? 'text.primary' : 'text.disabled',
                    }}
                  >
                    {schedule.label}
                  </Typography>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, flexWrap: 'wrap', mt: 0.5 }}>
                    <Typography variant="body2" color="textSecondary">
                      {formatDaysOfWeek(parseDaysOfWeek(schedule.days_of_week))}
                    </Typography>
                    <Typography variant="body2" color="textSecondary">|</Typography>
                    {Object.entries(schedule.options || {})
                      .filter(([, v]) => v)
                      .map(([key]) => (
                        <Chip
                          key={key}
                          label={OPTION_LABELS[key] || key}
                          size="small"
                          variant="outlined"
                          color="primary"
                          sx={{ height: 22, fontSize: '0.7rem' }}
                        />
                      ))}
                  </Box>
                  {schedule.is_active && schedule.next_run && (
                    <Typography variant="caption" color="textSecondary" sx={{ mt: 0.5, display: 'block' }}>
                      다음 실행: {formatNextRun(schedule.next_run)}
                    </Typography>
                  )}
                </Box>

                {/* 액션 버튼 */}
                <Box sx={{ display: 'flex', gap: 0.5 }}>
                  <Tooltip title="수정">
                    <IconButton size="small" onClick={() => handleOpenEdit(schedule)}>
                      <Edit fontSize="small" />
                    </IconButton>
                  </Tooltip>
                  <Tooltip title="삭제">
                    <IconButton
                      size="small"
                      color="error"
                      onClick={() => handleDeleteConfirm(schedule.id)}
                    >
                      <Delete fontSize="small" />
                    </IconButton>
                  </Tooltip>
                </Box>
              </Box>
            </Paper>
          ))}
        </Box>
      )}

      {/* 생성/수정 다이얼로그 */}
      <Dialog
        open={dialogOpen}
        onClose={() => setDialogOpen(false)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>
          {dialogMode === 'create' ? '스케줄 추가' : '스케줄 수정'}
        </DialogTitle>
        <DialogContent>
          <Box sx={{ pt: 1, display: 'flex', flexDirection: 'column', gap: 2.5 }}>
            {/* 스케줄 이름 */}
            <TextField
              fullWidth
              label="스케줄 이름"
              value={formData.label}
              onChange={(e) => setFormData((prev) => ({ ...prev, label: e.target.value }))}
              placeholder="예: 오전 배치, 점심 배치, 저녁 배치"
            />

            {/* 실행 시간 */}
            <Box>
              <Typography variant="subtitle2" gutterBottom>
                실행 시간
              </Typography>
              <Grid container spacing={2}>
                <Grid item xs={6}>
                  <TextField
                    select
                    fullWidth
                    label="시"
                    value={formData.schedule_hour}
                    onChange={(e) =>
                      setFormData((prev) => ({
                        ...prev,
                        schedule_hour: Number(e.target.value),
                      }))
                    }
                    size="small"
                  >
                    {Array.from({ length: 24 }, (_, i) => (
                      <MenuItem key={i} value={i}>
                        {String(i).padStart(2, '0')}시
                      </MenuItem>
                    ))}
                  </TextField>
                </Grid>
                <Grid item xs={6}>
                  <TextField
                    select
                    fullWidth
                    label="분"
                    value={formData.schedule_minute}
                    onChange={(e) =>
                      setFormData((prev) => ({
                        ...prev,
                        schedule_minute: Number(e.target.value),
                      }))
                    }
                    size="small"
                  >
                    {MINUTE_OPTIONS.map((m) => (
                      <MenuItem key={m} value={m}>
                        {String(m).padStart(2, '0')}분
                      </MenuItem>
                    ))}
                  </TextField>
                </Grid>
              </Grid>
            </Box>

            <Divider />

            {/* 요일 선택 */}
            <Box>
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 1 }}>
                <Typography variant="subtitle2">반복 요일</Typography>
                <FormControlLabel
                  control={
                    <Checkbox
                      checked={formData.days_of_week.length === 7}
                      indeterminate={
                        formData.days_of_week.length > 0 && formData.days_of_week.length < 7
                      }
                      onChange={handleAllDaysToggle}
                      size="small"
                    />
                  }
                  label={
                    <Typography variant="body2">매일</Typography>
                  }
                />
              </Box>
              <Box sx={{ display: 'flex', gap: 0.5, flexWrap: 'wrap' }}>
                {DAYS_OF_WEEK.map((day) => {
                  const selected = formData.days_of_week.includes(day.key);
                  return (
                    <Chip
                      key={day.key}
                      label={day.label}
                      onClick={() => handleDayToggle(day.key)}
                      color={selected ? 'primary' : 'default'}
                      variant={selected ? 'filled' : 'outlined'}
                      sx={{ minWidth: 44 }}
                    />
                  );
                })}
              </Box>
              <Typography variant="caption" color="textSecondary" sx={{ mt: 0.5, display: 'block' }}>
                선택하지 않으면 매일 실행됩니다.
              </Typography>
            </Box>

            <Divider />

            {/* 기능 옵션 */}
            <Box>
              <Typography variant="subtitle2" gutterBottom>
                실행 옵션
              </Typography>
              <FormGroup>
                {Object.entries(OPTION_LABELS).map(([key, label]) => (
                  <FormControlLabel
                    key={key}
                    control={
                      <Checkbox
                        checked={formData.options[key] || false}
                        onChange={() => handleOptionToggle(key)}
                        size="small"
                      />
                    }
                    label={<Typography variant="body2">{label}</Typography>}
                  />
                ))}
              </FormGroup>
            </Box>
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDialogOpen(false)}>취소</Button>
          <Button
            onClick={handleSave}
            variant="contained"
            disabled={saving || !formData.label.trim()}
            startIcon={saving ? <CircularProgress size={18} /> : undefined}
          >
            {saving ? '저장 중...' : dialogMode === 'create' ? '추가' : '수정'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* 삭제 확인 다이얼로그 */}
      <Dialog
        open={deleteConfirmOpen}
        onClose={() => setDeleteConfirmOpen(false)}
        maxWidth="xs"
        fullWidth
      >
        <DialogTitle>스케줄 삭제</DialogTitle>
        <DialogContent>
          <Typography>
            이 스케줄을 삭제하시겠습니까? 삭제된 스케줄은 복구할 수 없습니다.
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDeleteConfirmOpen(false)}>취소</Button>
          <Button onClick={handleDelete} color="error" variant="contained">
            삭제
          </Button>
        </DialogActions>
      </Dialog>
    </Paper>
  );
};

export default BatchSchedulePanel;
