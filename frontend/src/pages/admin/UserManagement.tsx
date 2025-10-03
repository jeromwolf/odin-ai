/**
 * 관리자 - 사용자 관리 화면
 * 사용자 목록, 상세 정보, 활동 내역, 계정 관리
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
  Switch,
  FormControlLabel,
} from '@mui/material';
import {
  Refresh,
  Visibility,
  Block,
  CheckCircle,
  Search as SearchIcon,
  Person,
  Email,
  Phone,
  Business,
} from '@mui/icons-material';
import { adminApi } from '../../services/admin/adminApi';

interface User {
  id: number;
  email: string;
  username: string;
  full_name: string | null;
  company: string | null;
  phone: string | null;
  subscription_plan: string;
  is_active: boolean;
  email_verified: boolean;
  created_at: string;
  last_login: string | null;
}

interface UserDetail {
  user: User;
  activity_stats: {
    total_searches: number;
    total_bookmarks: number;
    total_notifications: number;
    last_search_date: string | null;
  };
  notification_rules: any[];
  bookmarks: any[];
  recent_activities: any[];
}

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

const TabPanel: React.FC<TabPanelProps> = ({ children, value, index }) => {
  return (
    <div role="tabpanel" hidden={value !== index}>
      {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
    </div>
  );
};

const UserManagement: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const [users, setUsers] = useState<User[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(20);
  const [error, setError] = useState<string | null>(null);

  // 필터
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [planFilter, setPlanFilter] = useState<string>('');
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
  }, [page, rowsPerPage, searchQuery, planFilter, statusFilter]);

  const loadUsers = async () => {
    try {
      setLoading(true);
      setError(null);

      const params: any = {
        page: page + 1,
        limit: rowsPerPage,
      };

      if (searchQuery) params.search = searchQuery;
      if (planFilter) params.plan = planFilter;
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
    } catch (err) {
      console.error('사용자 통계 조회 실패:', err);
    }
  };

  const handleViewDetail = async (userId: number) => {
    try {
      const detail = await adminApi.getUserDetail(userId);
      setSelectedUser(detail);
      setDetailTab(0);
      setDetailOpen(true);
    } catch (err: any) {
      console.error('사용자 상세 정보 조회 실패:', err);
      setError(err.response?.data?.detail || '상세 정보를 불러오는데 실패했습니다.');
    }
  };

  const handleToggleUserStatus = async (userId: number, currentStatus: boolean) => {
    const action = currentStatus ? 'deactivate' : 'activate';
    const confirmMessage = currentStatus
      ? '이 사용자를 비활성화하시겠습니까?'
      : '이 사용자를 활성화하시겠습니까?';

    if (!window.confirm(confirmMessage)) return;

    try {
      await adminApi.updateUser(userId, { is_active: !currentStatus });
      alert(`사용자 ${action === 'activate' ? '활성화' : '비활성화'} 성공!`);
      loadUsers(); // 목록 새로고침
      if (selectedUser && selectedUser.user.id === userId) {
        setDetailOpen(false); // 상세 모달 닫기
      }
    } catch (err: any) {
      console.error('사용자 상태 변경 실패:', err);
      setError(err.response?.data?.detail || '상태 변경에 실패했습니다.');
    }
  };

  const getPlanChip = (plan: string) => {
    const configs: Record<string, { label: string; color: 'default' | 'primary' | 'secondary' | 'success' }> = {
      free: { label: '무료', color: 'default' },
      basic: { label: '베이직', color: 'primary' },
      pro: { label: '프로', color: 'secondary' },
      enterprise: { label: '엔터프라이즈', color: 'success' },
    };
    const config = configs[plan] || { label: plan, color: 'default' };
    return <Chip label={config.label} color={config.color} size="small" />;
  };

  const getStatusChip = (isActive: boolean) => {
    return (
      <Chip
        label={isActive ? '활성' : '비활성'}
        color={isActive ? 'success' : 'error'}
        size="small"
        icon={isActive ? <CheckCircle /> : <Block />}
      />
    );
  };

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Box>
          <Typography variant="h4" gutterBottom>
            사용자 관리
          </Typography>
          <Typography variant="body2" color="textSecondary">
            전체 사용자 조회 및 계정 관리
          </Typography>
        </Box>
        <Button
          variant="outlined"
          startIcon={<Refresh />}
          onClick={loadUsers}
        >
          새로고침
        </Button>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {/* 통계 카드 */}
      {userStats && (
        <Grid container spacing={3} sx={{ mb: 3 }}>
          <Grid item xs={12} md={3}>
            <Card>
              <CardContent>
                <Box display="flex" alignItems="center">
                  <Person sx={{ fontSize: 40, mr: 2, color: '#2196f3' }} />
                  <Box>
                    <Typography variant="body2" color="textSecondary">
                      전체 사용자
                    </Typography>
                    <Typography variant="h5">{userStats.total_users}</Typography>
                  </Box>
                </Box>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} md={3}>
            <Card>
              <CardContent>
                <Box display="flex" alignItems="center">
                  <CheckCircle sx={{ fontSize: 40, mr: 2, color: '#4caf50' }} />
                  <Box>
                    <Typography variant="body2" color="textSecondary">
                      활성 사용자
                    </Typography>
                    <Typography variant="h5">{userStats.active_users}</Typography>
                  </Box>
                </Box>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} md={3}>
            <Card>
              <CardContent>
                <Box display="flex" alignItems="center">
                  <Email sx={{ fontSize: 40, mr: 2, color: '#ff9800' }} />
                  <Box>
                    <Typography variant="body2" color="textSecondary">
                      이메일 인증
                    </Typography>
                    <Typography variant="h5">{userStats.verified_users}</Typography>
                  </Box>
                </Box>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} md={3}>
            <Card>
              <CardContent>
                <Box display="flex" alignItems="center">
                  <Business sx={{ fontSize: 40, mr: 2, color: '#9c27b0' }} />
                  <Box>
                    <Typography variant="body2" color="textSecondary">
                      유료 구독자
                    </Typography>
                    <Typography variant="h5">{userStats.paid_users}</Typography>
                  </Box>
                </Box>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      )}

      {/* 검색 및 필터 */}
      <Paper sx={{ p: 2, mb: 2 }}>
        <Grid container spacing={2} alignItems="center">
          <Grid item xs={12} sm={6}>
            <TextField
              fullWidth
              placeholder="이름, 이메일, 회사명 검색..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              InputProps={{
                startAdornment: <SearchIcon sx={{ mr: 1, color: 'text.secondary' }} />,
              }}
              size="small"
            />
          </Grid>
          <Grid item xs={12} sm={3}>
            <TextField
              select
              fullWidth
              label="구독 플랜"
              value={planFilter}
              onChange={(e) => setPlanFilter(e.target.value)}
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
                <TableCell>인증</TableCell>
                <TableCell>가입일</TableCell>
                <TableCell>최근 로그인</TableCell>
                <TableCell align="center">작업</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {loading ? (
                <TableRow>
                  <TableCell colSpan={10} align="center">
                    <CircularProgress />
                  </TableCell>
                </TableRow>
              ) : users.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={10} align="center">
                    사용자가 없습니다
                  </TableCell>
                </TableRow>
              ) : (
                users.map((user) => (
                  <TableRow key={user.id} hover>
                    <TableCell>{user.id}</TableCell>
                    <TableCell>{user.email}</TableCell>
                    <TableCell>{user.full_name || user.username}</TableCell>
                    <TableCell>{user.company || '-'}</TableCell>
                    <TableCell>{getPlanChip(user.subscription_plan)}</TableCell>
                    <TableCell>{getStatusChip(user.is_active)}</TableCell>
                    <TableCell>
                      {user.email_verified ? (
                        <Chip label="완료" color="success" size="small" />
                      ) : (
                        <Chip label="미완료" color="warning" size="small" />
                      )}
                    </TableCell>
                    <TableCell>
                      {new Date(user.created_at).toLocaleDateString('ko-KR')}
                    </TableCell>
                    <TableCell>
                      {user.last_login
                        ? new Date(user.last_login).toLocaleString('ko-KR')
                        : '-'}
                    </TableCell>
                    <TableCell align="center">
                      <Tooltip title="상세 보기">
                        <IconButton
                          size="small"
                          onClick={() => handleViewDetail(user.id)}
                        >
                          <Visibility />
                        </IconButton>
                      </Tooltip>
                      <Tooltip title={user.is_active ? '비활성화' : '활성화'}>
                        <IconButton
                          size="small"
                          onClick={() => handleToggleUserStatus(user.id, user.is_active)}
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

      {/* 상세 정보 모달 */}
      <Dialog open={detailOpen} onClose={() => setDetailOpen(false)} maxWidth="lg" fullWidth>
        <DialogTitle>사용자 상세 정보</DialogTitle>
        <DialogContent>
          {selectedUser && (
            <Box>
              {/* 기본 정보 */}
              <Paper variant="outlined" sx={{ p: 2, mb: 2 }}>
                <Grid container spacing={2}>
                  <Grid item xs={12} md={6}>
                    <Typography variant="body2" color="textSecondary">
                      이메일
                    </Typography>
                    <Typography variant="body1">{selectedUser.user.email}</Typography>
                  </Grid>
                  <Grid item xs={12} md={6}>
                    <Typography variant="body2" color="textSecondary">
                      이름
                    </Typography>
                    <Typography variant="body1">
                      {selectedUser.user.full_name || selectedUser.user.username}
                    </Typography>
                  </Grid>
                  <Grid item xs={12} md={6}>
                    <Typography variant="body2" color="textSecondary">
                      회사
                    </Typography>
                    <Typography variant="body1">
                      {selectedUser.user.company || '-'}
                    </Typography>
                  </Grid>
                  <Grid item xs={12} md={6}>
                    <Typography variant="body2" color="textSecondary">
                      전화번호
                    </Typography>
                    <Typography variant="body1">
                      {selectedUser.user.phone || '-'}
                    </Typography>
                  </Grid>
                  <Grid item xs={12} md={6}>
                    <Typography variant="body2" color="textSecondary">
                      구독 플랜
                    </Typography>
                    {getPlanChip(selectedUser.user.subscription_plan)}
                  </Grid>
                  <Grid item xs={12} md={6}>
                    <Typography variant="body2" color="textSecondary">
                      계정 상태
                    </Typography>
                    {getStatusChip(selectedUser.user.is_active)}
                  </Grid>
                </Grid>
              </Paper>

              {/* 활동 통계 */}
              <Grid container spacing={2} sx={{ mb: 2 }}>
                <Grid item xs={12} md={4}>
                  <Card variant="outlined">
                    <CardContent>
                      <Typography variant="body2" color="textSecondary">
                        총 검색 횟수
                      </Typography>
                      <Typography variant="h5">
                        {selectedUser.activity_stats.total_searches}
                      </Typography>
                    </CardContent>
                  </Card>
                </Grid>
                <Grid item xs={12} md={4}>
                  <Card variant="outlined">
                    <CardContent>
                      <Typography variant="body2" color="textSecondary">
                        북마크 수
                      </Typography>
                      <Typography variant="h5">
                        {selectedUser.activity_stats.total_bookmarks}
                      </Typography>
                    </CardContent>
                  </Card>
                </Grid>
                <Grid item xs={12} md={4}>
                  <Card variant="outlined">
                    <CardContent>
                      <Typography variant="body2" color="textSecondary">
                        알림 규칙 수
                      </Typography>
                      <Typography variant="h5">
                        {selectedUser.activity_stats.total_notifications}
                      </Typography>
                    </CardContent>
                  </Card>
                </Grid>
              </Grid>

              {/* 탭 */}
              <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
                <Tabs value={detailTab} onChange={(_, v) => setDetailTab(v)}>
                  <Tab label="알림 규칙" />
                  <Tab label="북마크" />
                  <Tab label="최근 활동" />
                </Tabs>
              </Box>

              {/* 알림 규칙 탭 */}
              <TabPanel value={detailTab} index={0}>
                <TableContainer>
                  <Table size="small">
                    <TableHead>
                      <TableRow>
                        <TableCell>키워드</TableCell>
                        <TableCell>알림 유형</TableCell>
                        <TableCell>활성</TableCell>
                        <TableCell>생성일</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {selectedUser.notification_rules.length === 0 ? (
                        <TableRow>
                          <TableCell colSpan={4} align="center">
                            등록된 알림 규칙이 없습니다
                          </TableCell>
                        </TableRow>
                      ) : (
                        selectedUser.notification_rules.map((rule: any) => (
                          <TableRow key={rule.id}>
                            <TableCell>{rule.keywords.join(', ')}</TableCell>
                            <TableCell>
                              {rule.notification_types.join(', ')}
                            </TableCell>
                            <TableCell>
                              {rule.is_active ? (
                                <Chip label="활성" color="success" size="small" />
                              ) : (
                                <Chip label="비활성" color="default" size="small" />
                              )}
                            </TableCell>
                            <TableCell>
                              {new Date(rule.created_at).toLocaleDateString('ko-KR')}
                            </TableCell>
                          </TableRow>
                        ))
                      )}
                    </TableBody>
                  </Table>
                </TableContainer>
              </TabPanel>

              {/* 북마크 탭 */}
              <TabPanel value={detailTab} index={1}>
                <TableContainer>
                  <Table size="small">
                    <TableHead>
                      <TableRow>
                        <TableCell>입찰 제목</TableCell>
                        <TableCell>기관명</TableCell>
                        <TableCell>마감일</TableCell>
                        <TableCell>저장일</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {selectedUser.bookmarks.length === 0 ? (
                        <TableRow>
                          <TableCell colSpan={4} align="center">
                            북마크한 입찰이 없습니다
                          </TableCell>
                        </TableRow>
                      ) : (
                        selectedUser.bookmarks.map((bookmark: any) => (
                          <TableRow key={bookmark.id}>
                            <TableCell>{bookmark.title}</TableCell>
                            <TableCell>{bookmark.agency}</TableCell>
                            <TableCell>
                              {new Date(bookmark.bid_end_date).toLocaleDateString('ko-KR')}
                            </TableCell>
                            <TableCell>
                              {new Date(bookmark.created_at).toLocaleDateString('ko-KR')}
                            </TableCell>
                          </TableRow>
                        ))
                      )}
                    </TableBody>
                  </Table>
                </TableContainer>
              </TabPanel>

              {/* 최근 활동 탭 */}
              <TabPanel value={detailTab} index={2}>
                <TableContainer>
                  <Table size="small">
                    <TableHead>
                      <TableRow>
                        <TableCell>활동 유형</TableCell>
                        <TableCell>상세 내용</TableCell>
                        <TableCell>일시</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {selectedUser.recent_activities.length === 0 ? (
                        <TableRow>
                          <TableCell colSpan={3} align="center">
                            최근 활동 내역이 없습니다
                          </TableCell>
                        </TableRow>
                      ) : (
                        selectedUser.recent_activities.map((activity: any, idx: number) => (
                          <TableRow key={idx}>
                            <TableCell>
                              <Chip label={activity.activity_type} size="small" />
                            </TableCell>
                            <TableCell>{activity.description}</TableCell>
                            <TableCell>
                              {new Date(activity.created_at).toLocaleString('ko-KR')}
                            </TableCell>
                          </TableRow>
                        ))
                      )}
                    </TableBody>
                  </Table>
                </TableContainer>
              </TabPanel>
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDetailOpen(false)}>닫기</Button>
          {selectedUser && (
            <Button
              onClick={() => handleToggleUserStatus(selectedUser.user.id, selectedUser.user.is_active)}
              variant="contained"
              color={selectedUser.user.is_active ? 'error' : 'success'}
            >
              {selectedUser.user.is_active ? '비활성화' : '활성화'}
            </Button>
          )}
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default UserManagement;
