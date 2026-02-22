/**
 * 관리자 - 사용자 관리 화면
 * 사용자 목록, 상세 정보, 계정 활성화/비활성화
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
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  MenuItem,
  Grid,
  Card,
  CardContent,
  Alert,
  CircularProgress,
  IconButton,
  Tooltip,
  Tabs,
  Tab,
  List,
  ListItem,
  ListItemText,
} from '@mui/material';
import {
  Visibility,
  Block,
  CheckCircle,
  Search,
  Refresh,
} from '@mui/icons-material';
import { adminApi } from '../../services/admin/adminApi';

interface User {
  id: number;
  email: string;
  username: string;
  full_name: string | null;
  company: string | null;
  is_active: boolean;
  is_admin: boolean;
  subscription_plan: string;
  created_at: string;
  last_login: string | null;
}

interface UserDetail {
  user: User;
  activity_summary?: {
    total_searches: number;
    total_bookmarks: number;
    total_notifications: number;
    last_activity: string | null;
  };
  statistics?: {
    bookmarks: number;
    notification_rules: number;
  };
  notification_rules?: any[];
  bookmarks?: any[];
  recent_activity?: any[];
  recent_activities?: any[];
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
      id={`user-tabpanel-${index}`}
      aria-labelledby={`user-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
    </div>
  );
}

const Users: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const [users, setUsers] = useState<User[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(20);
  const [error, setError] = useState<string | null>(null);

  // 필터
  const [searchQuery, setSearchQuery] = useState('');
  const [subscriptionFilter, setSubscriptionFilter] = useState<string>('');
  const [statusFilter, setStatusFilter] = useState<string>('');

  // 상세 모달
  const [detailOpen, setDetailOpen] = useState(false);
  const [selectedUser, setSelectedUser] = useState<UserDetail | null>(null);
  const [detailTab, setDetailTab] = useState(0);

  // 통계
  const [userStats, setUserStats] = useState<any>(null);

  useEffect(() => {
    loadUsers();
    loadUserStats();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [page, rowsPerPage, searchQuery, subscriptionFilter, statusFilter]);

  const loadUsers = async () => {
    try {
      setLoading(true);
      setError(null);

      const params: any = {
        page: page + 1,
        limit: rowsPerPage,
      };

      if (searchQuery) params.search = searchQuery;
      if (subscriptionFilter) params.subscription = subscriptionFilter;
      if (statusFilter) params.is_active = statusFilter === 'active';

      const data = await adminApi.getUsers(params);
      setUsers(data.users || []);
      setTotal(data.total || 0);
    } catch (err: any) {
      console.error('사용자 목록 조회 실패:', err);
      setError(err.response?.data?.detail || '데이터를 불러오는데 실패했습니다.');
    } finally {
      setLoading(false);
    }
  };

  const loadUserStats = async () => {
    try {
      const stats = await adminApi.getUserStatistics();
      setUserStats(stats);
    } catch (err: any) {
      console.error('사용자 통계 조회 실패:', err);
    }
  };

  const handleViewDetail = async (userId: number) => {
    try {
      const detail = await adminApi.getUserDetail(userId);
      setSelectedUser(detail);
      setDetailOpen(true);
      setDetailTab(0);
    } catch (err: any) {
      console.error('사용자 상세 정보 조회 실패:', err);
      setError(err.response?.data?.detail || '상세 정보를 불러오는데 실패했습니다.');
    }
  };

  const handleToggleActive = async (userId: number, currentStatus: boolean) => {
    const action = currentStatus ? '비활성화' : '활성화';
    if (!window.confirm(`이 사용자를 ${action}하시겠습니까?`)) {
      return;
    }

    try {
      await adminApi.updateUser(userId, { is_active: !currentStatus });
      alert(`사용자가 ${action}되었습니다.`);
      loadUsers(); // 목록 새로고침
      if (selectedUser && selectedUser.user.id === userId) {
        setDetailOpen(false); // 상세 모달이 열려있으면 닫기
      }
    } catch (err: any) {
      console.error('사용자 상태 변경 실패:', err);
      setError(err.response?.data?.detail || '상태 변경에 실패했습니다.');
    }
  };

  const getStatusChip = (isActive: boolean) => {
    return isActive ? (
      <Chip label="활성" color="success" size="small" icon={<CheckCircle />} />
    ) : (
      <Chip label="비활성" color="error" size="small" icon={<Block />} />
    );
  };

  const getSubscriptionChip = (plan: string) => {
    const configs: Record<string, { label: string; color: 'default' | 'primary' | 'secondary' | 'success' }> = {
      free: { label: '무료', color: 'default' },
      basic: { label: '베이직', color: 'primary' },
      pro: { label: '프로', color: 'secondary' },
      enterprise: { label: '엔터프라이즈', color: 'success' },
    };
    const config = configs[plan] || { label: plan, color: 'default' };
    return <Chip label={config.label} color={config.color} size="small" />;
  };

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Box>
          <Typography variant="h4" gutterBottom>
            사용자 관리
          </Typography>
          <Typography variant="body2" color="textSecondary">
            전체 사용자 계정 관리 및 모니터링
          </Typography>
        </Box>
        <Box>
          <Button
            variant="outlined"
            startIcon={<Refresh />}
            onClick={loadUsers}
            sx={{ mr: 1 }}
          >
            새로고침
          </Button>
        </Box>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {/* 통계 카드 */}
      {userStats && (
        <Grid container spacing={3} sx={{ mb: 3 }}>
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Typography variant="body2" color="textSecondary">
                  전체 사용자
                </Typography>
                <Typography variant="h4">{userStats.total_users}</Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Typography variant="body2" color="textSecondary">
                  활성 사용자
                </Typography>
                <Typography variant="h4" color="success.main">
                  {userStats.active_users}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Typography variant="body2" color="textSecondary">
                  유료 사용자
                </Typography>
                <Typography variant="h4" color="primary.main">
                  {userStats.paid_users}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Typography variant="body2" color="textSecondary">
                  금일 가입자
                </Typography>
                <Typography variant="h4">{userStats.new_users_today}</Typography>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      )}

      {/* 필터 */}
      <Paper sx={{ p: 2, mb: 2 }}>
        <Grid container spacing={2} alignItems="center">
          <Grid item xs={12} sm={6}>
            <TextField
              fullWidth
              placeholder="이메일 또는 이름으로 검색..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              InputProps={{
                startAdornment: <Search sx={{ mr: 1, color: 'text.secondary' }} />,
              }}
              size="small"
            />
          </Grid>
          <Grid item xs={12} sm={3}>
            <TextField
              select
              fullWidth
              label="구독 플랜"
              value={subscriptionFilter}
              onChange={(e) => setSubscriptionFilter(e.target.value)}
              size="small"
            >
              <MenuItem value="">전체</MenuItem>
              <MenuItem value="free">무료</MenuItem>
              <MenuItem value="basic">베이직</MenuItem>
              <MenuItem value="pro">프로</MenuItem>
              <MenuItem value="enterprise">엔터프라이즈</MenuItem>
            </TextField>
          </Grid>
          <Grid item xs={12} sm={3}>
            <TextField
              select
              fullWidth
              label="상태"
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              size="small"
            >
              <MenuItem value="">전체</MenuItem>
              <MenuItem value="active">활성</MenuItem>
              <MenuItem value="inactive">비활성</MenuItem>
            </TextField>
          </Grid>
        </Grid>
      </Paper>

      {/* 사용자 목록 테이블 */}
      <Paper>
        <TableContainer>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>ID</TableCell>
                <TableCell>이메일</TableCell>
                <TableCell>이름</TableCell>
                <TableCell>회사</TableCell>
                <TableCell>구독 플랜</TableCell>
                <TableCell>상태</TableCell>
                <TableCell>가입일</TableCell>
                <TableCell>최근 로그인</TableCell>
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
              ) : users.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={9} align="center">
                    사용자가 없습니다
                  </TableCell>
                </TableRow>
              ) : (
                users.map((user) => (
                  <TableRow key={user.id} hover>
                    <TableCell>{user.id}</TableCell>
                    <TableCell>{user.email}</TableCell>
                    <TableCell>{user.username || '-'}</TableCell>
                    <TableCell>{user.company || '-'}</TableCell>
                    <TableCell>{getSubscriptionChip(user.subscription_plan)}</TableCell>
                    <TableCell>{getStatusChip(user.is_active)}</TableCell>
                    <TableCell>
                      {new Date(user.created_at).toLocaleDateString('ko-KR')}
                    </TableCell>
                    <TableCell>
                      {user.last_login
                        ? new Date(user.last_login).toLocaleString('ko-KR')
                        : '로그인 기록 없음'}
                    </TableCell>
                    <TableCell align="center">
                      <Tooltip title="상세 보기">
                        <IconButton
                          size="small"
                          onClick={() => handleViewDetail(user.id)}
                          sx={{ mr: 1 }}
                        >
                          <Visibility />
                        </IconButton>
                      </Tooltip>
                      <Tooltip title={user.is_active ? '비활성화' : '활성화'}>
                        <IconButton
                          size="small"
                          onClick={() => handleToggleActive(user.id, user.is_active)}
                          color={user.is_active ? 'error' : 'success'}
                        >
                          {user.is_active ? <Block /> : <CheckCircle />}
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

      {/* 사용자 상세 정보 모달 */}
      <Dialog
        open={detailOpen}
        onClose={() => setDetailOpen(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>
          사용자 상세 정보
          {selectedUser && (
            <Box component="span" sx={{ ml: 2 }}>
              {getStatusChip(selectedUser.user.is_active)}
              {selectedUser.user.is_admin && (
                <Chip label="관리자" color="warning" size="small" sx={{ ml: 1 }} />
              )}
            </Box>
          )}
        </DialogTitle>
        <DialogContent>
          {selectedUser && (
            <Box>
              <Tabs value={detailTab} onChange={(_, newValue) => setDetailTab(newValue)}>
                <Tab label="기본 정보" />
                <Tab label="활동 내역" />
                <Tab label="알림 규칙" />
                <Tab label="북마크" />
              </Tabs>

              <TabPanel value={detailTab} index={0}>
                <Grid container spacing={2}>
                  <Grid item xs={6}>
                    <Typography variant="body2" color="textSecondary">
                      ID
                    </Typography>
                    <Typography variant="body1">{selectedUser.user.id}</Typography>
                  </Grid>
                  <Grid item xs={6}>
                    <Typography variant="body2" color="textSecondary">
                      이메일
                    </Typography>
                    <Typography variant="body1">{selectedUser.user.email}</Typography>
                  </Grid>
                  <Grid item xs={6}>
                    <Typography variant="body2" color="textSecondary">
                      이름
                    </Typography>
                    <Typography variant="body1">
                      {selectedUser.user.username || '-'}
                    </Typography>
                  </Grid>
                  <Grid item xs={6}>
                    <Typography variant="body2" color="textSecondary">
                      회사
                    </Typography>
                    <Typography variant="body1">
                      {selectedUser.user.company || '-'}
                    </Typography>
                  </Grid>
                  <Grid item xs={6}>
                    <Typography variant="body2" color="textSecondary">
                      구독 플랜
                    </Typography>
                    {getSubscriptionChip(selectedUser.user.subscription_plan)}
                  </Grid>
                  <Grid item xs={6}>
                    <Typography variant="body2" color="textSecondary">
                      가입일
                    </Typography>
                    <Typography variant="body1">
                      {new Date(selectedUser.user.created_at).toLocaleString('ko-KR')}
                    </Typography>
                  </Grid>
                  <Grid item xs={6}>
                    <Typography variant="body2" color="textSecondary">
                      최근 로그인
                    </Typography>
                    <Typography variant="body1">
                      {selectedUser.user.last_login
                        ? new Date(selectedUser.user.last_login).toLocaleString('ko-KR')
                        : '로그인 기록 없음'}
                    </Typography>
                  </Grid>
                  <Grid item xs={6}>
                    <Typography variant="body2" color="textSecondary">
                      최근 활동
                    </Typography>
                    <Typography variant="body1">
                      {selectedUser.activity_summary?.last_activity
                        ? new Date(
                            selectedUser.activity_summary.last_activity
                          ).toLocaleString('ko-KR')
                        : '활동 기록 없음'}
                    </Typography>
                  </Grid>
                </Grid>

                <Box sx={{ mt: 3 }}>
                  <Typography variant="h6" gutterBottom>
                    활동 요약
                  </Typography>
                  <Grid container spacing={2}>
                    <Grid item xs={4}>
                      <Card variant="outlined">
                        <CardContent>
                          <Typography variant="body2" color="textSecondary">
                            검색 횟수
                          </Typography>
                          <Typography variant="h5">
                            {selectedUser.activity_summary?.total_searches || 0}
                          </Typography>
                        </CardContent>
                      </Card>
                    </Grid>
                    <Grid item xs={4}>
                      <Card variant="outlined">
                        <CardContent>
                          <Typography variant="body2" color="textSecondary">
                            북마크 수
                          </Typography>
                          <Typography variant="h5">
                            {selectedUser.activity_summary?.total_bookmarks || 0}
                          </Typography>
                        </CardContent>
                      </Card>
                    </Grid>
                    <Grid item xs={4}>
                      <Card variant="outlined">
                        <CardContent>
                          <Typography variant="body2" color="textSecondary">
                            알림 수신
                          </Typography>
                          <Typography variant="h5">
                            {selectedUser.activity_summary?.total_notifications || 0}
                          </Typography>
                        </CardContent>
                      </Card>
                    </Grid>
                  </Grid>
                </Box>
              </TabPanel>

              <TabPanel value={detailTab} index={1}>
                <Typography variant="body2" color="textSecondary" gutterBottom>
                  최근 활동 내역 (최근 20개)
                </Typography>
                {(!selectedUser.recent_activities && !selectedUser.recent_activity) ||
                 (selectedUser.recent_activities?.length === 0 && selectedUser.recent_activity?.length === 0) ? (
                  <Alert severity="info">활동 내역이 없습니다</Alert>
                ) : (
                  <List>
                    {(selectedUser.recent_activities || selectedUser.recent_activity || []).map((activity: any, index: number) => (
                      <ListItem key={index} divider>
                        <ListItemText
                          primary={activity.description}
                          secondary={new Date(activity.created_at).toLocaleString('ko-KR')}
                        />
                      </ListItem>
                    ))}
                  </List>
                )}
              </TabPanel>

              <TabPanel value={detailTab} index={2}>
                <Typography variant="body2" color="textSecondary" gutterBottom>
                  등록된 알림 규칙
                </Typography>
                {!selectedUser.notification_rules || selectedUser.notification_rules.length === 0 ? (
                  <Alert severity="info">등록된 알림 규칙이 없습니다</Alert>
                ) : (
                  <List>
                    {(selectedUser.notification_rules || []).map((rule: any) => (
                      <ListItem key={rule.id} divider>
                        <ListItemText
                          primary={rule.keywords.join(', ')}
                          secondary={`가격: ${rule.min_price || 0}~${
                            rule.max_price || '무제한'
                          } | ${rule.is_active ? '활성' : '비활성'}`}
                        />
                      </ListItem>
                    ))}
                  </List>
                )}
              </TabPanel>

              <TabPanel value={detailTab} index={3}>
                <Typography variant="body2" color="textSecondary" gutterBottom>
                  북마크한 입찰공고
                </Typography>
                {!selectedUser.bookmarks || selectedUser.bookmarks.length === 0 ? (
                  <Alert severity="info">북마크한 공고가 없습니다</Alert>
                ) : (
                  <List>
                    {(selectedUser.bookmarks || []).map((bookmark: any) => (
                      <ListItem key={bookmark.id} divider>
                        <ListItemText
                          primary={bookmark.title || bookmark.bid_notice_no}
                          secondary={`등록일: ${new Date(bookmark.created_at).toLocaleDateString(
                            'ko-KR'
                          )}`}
                        />
                      </ListItem>
                    ))}
                  </List>
                )}
              </TabPanel>
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

export default Users;
