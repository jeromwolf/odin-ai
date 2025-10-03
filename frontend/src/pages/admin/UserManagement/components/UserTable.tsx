/**
 * 사용자 테이블 컴포넌트
 * 사용자 목록 테이블 및 페이지네이션
 */

import React from 'react';
import {
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TablePagination,
  Chip,
  CircularProgress,
  IconButton,
  Tooltip,
} from '@mui/material';
import {
  Visibility,
  Block,
  CheckCircle,
} from '@mui/icons-material';
import { User } from '../types';
import { getPlanChip, getStatusChip } from '../utils';

interface UserTableProps {
  loading: boolean;
  users: User[];
  page: number;
  rowsPerPage: number;
  total: number;
  onPageChange: (newPage: number) => void;
  onRowsPerPageChange: (newRowsPerPage: number) => void;
  onViewDetail: (userId: number) => void;
  onToggleStatus: (userId: number, currentStatus: boolean) => void;
}

const UserTable: React.FC<UserTableProps> = ({
  loading,
  users,
  page,
  rowsPerPage,
  total,
  onPageChange,
  onRowsPerPageChange,
  onViewDetail,
  onToggleStatus,
}) => {
  return (
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
                        onClick={() => onViewDetail(user.id)}
                      >
                        <Visibility />
                      </IconButton>
                    </Tooltip>
                    <Tooltip title={user.is_active ? '비활성화' : '활성화'}>
                      <IconButton
                        size="small"
                        onClick={() => onToggleStatus(user.id, user.is_active)}
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
        onPageChange={(_, newPage) => onPageChange(newPage)}
        rowsPerPage={rowsPerPage}
        onRowsPerPageChange={(e) => {
          onRowsPerPageChange(parseInt(e.target.value, 10));
        }}
        labelRowsPerPage="페이지당 행 수:"
      />
    </Paper>
  );
};

export default UserTable;
