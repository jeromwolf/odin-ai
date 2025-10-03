/**
 * 사용자 상세 정보 다이얼로그 컴포넌트
 */

import React from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
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
  Tabs,
  Tab,
  Button,
  Chip,
} from '@mui/material';
import { UserDetail } from '../types';
import { TabPanel } from './TabPanel';
import { getPlanChip, getStatusChip } from '../utils';

interface UserDetailDialogProps {
  open: boolean;
  onClose: () => void;
  userDetail: UserDetail | null;
  detailTab: number;
  onTabChange: (newValue: number) => void;
  onToggleStatus: (userId: number, currentStatus: boolean) => void;
}

export const UserDetailDialog: React.FC<UserDetailDialogProps> = ({
  open,
  onClose,
  userDetail,
  detailTab,
  onTabChange,
  onToggleStatus,
}) => {
  return (
    <Dialog open={open} onClose={onClose} maxWidth="lg" fullWidth>
      <DialogTitle>사용자 상세 정보</DialogTitle>
      <DialogContent>
        {userDetail && (
          <Box>
            {/* 기본 정보 */}
            <Paper variant="outlined" sx={{ p: 2, mb: 2 }}>
              <Grid container spacing={2}>
                <Grid item xs={12} md={6}>
                  <Typography variant="body2" color="textSecondary">
                    이메일
                  </Typography>
                  <Typography variant="body1">{userDetail.user.email}</Typography>
                </Grid>
                <Grid item xs={12} md={6}>
                  <Typography variant="body2" color="textSecondary">
                    이름
                  </Typography>
                  <Typography variant="body1">
                    {userDetail.user.full_name || userDetail.user.username}
                  </Typography>
                </Grid>
                <Grid item xs={12} md={6}>
                  <Typography variant="body2" color="textSecondary">
                    회사
                  </Typography>
                  <Typography variant="body1">
                    {userDetail.user.company || '-'}
                  </Typography>
                </Grid>
                <Grid item xs={12} md={6}>
                  <Typography variant="body2" color="textSecondary">
                    전화번호
                  </Typography>
                  <Typography variant="body1">
                    {userDetail.user.phone || '-'}
                  </Typography>
                </Grid>
                <Grid item xs={12} md={6}>
                  <Typography variant="body2" color="textSecondary">
                    구독 플랜
                  </Typography>
                  {getPlanChip(userDetail.user.subscription_plan)}
                </Grid>
                <Grid item xs={12} md={6}>
                  <Typography variant="body2" color="textSecondary">
                    계정 상태
                  </Typography>
                  {getStatusChip(userDetail.user.is_active)}
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
                      {userDetail.activity_stats.total_searches}
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
                      {userDetail.activity_stats.total_bookmarks}
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
                      {userDetail.activity_stats.total_notifications}
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>
            </Grid>

            {/* 탭 */}
            <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
              <Tabs value={detailTab} onChange={(_, v) => onTabChange(v)}>
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
                    {userDetail.notification_rules.length === 0 ? (
                      <TableRow>
                        <TableCell colSpan={4} align="center">
                          등록된 알림 규칙이 없습니다
                        </TableCell>
                      </TableRow>
                    ) : (
                      userDetail.notification_rules.map((rule: any) => (
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
                    {userDetail.bookmarks.length === 0 ? (
                      <TableRow>
                        <TableCell colSpan={4} align="center">
                          북마크한 입찰이 없습니다
                        </TableCell>
                      </TableRow>
                    ) : (
                      userDetail.bookmarks.map((bookmark: any) => (
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
                    {userDetail.recent_activities.length === 0 ? (
                      <TableRow>
                        <TableCell colSpan={3} align="center">
                          최근 활동 내역이 없습니다
                        </TableCell>
                      </TableRow>
                    ) : (
                      userDetail.recent_activities.map((activity: any, idx: number) => (
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
        <Button onClick={onClose}>닫기</Button>
        {userDetail && (
          <Button
            onClick={() => onToggleStatus(userDetail.user.id, userDetail.user.is_active)}
            variant="contained"
            color={userDetail.user.is_active ? 'error' : 'success'}
          >
            {userDetail.user.is_active ? '비활성화' : '활성화'}
          </Button>
        )}
      </DialogActions>
    </Dialog>
  );
};
