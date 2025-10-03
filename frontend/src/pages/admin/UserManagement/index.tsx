/**
 * 관리자 - 사용자 관리 화면 (리팩토링 완료)
 * 사용자 목록, 상세 정보, 활동 내역, 계정 관리
 */

import React from 'react';
import { Box, Typography, Button, Alert } from '@mui/material';
import { Refresh } from '@mui/icons-material';
import { useUserManagement } from './hooks/useUserManagement';
import { UserStats } from './components/UserStats';
import { UserFilters } from './components/UserFilters';
import UserTable from './components/UserTable';
import { UserDetailDialog } from './components/UserDetailDialog';

const UserManagement: React.FC = () => {
  const {
    // State
    loading,
    users,
    total,
    page,
    rowsPerPage,
    error,
    searchQuery,
    planFilter,
    statusFilter,
    detailOpen,
    selectedUser,
    detailTab,
    userStats,

    // Setters
    setPage,
    setRowsPerPage,
    setError,
    setSearchQuery,
    setPlanFilter,
    setStatusFilter,
    setDetailOpen,
    setDetailTab,

    // Handlers
    loadUsers,
    handleViewDetail,
    handleToggleUserStatus,
  } = useUserManagement();

  return (
    <Box>
      {/* 페이지 헤더 */}
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

      {/* 에러 알림 */}
      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {/* 통계 카드 */}
      <UserStats userStats={userStats} />

      {/* 필터 섹션 */}
      <UserFilters
        searchQuery={searchQuery}
        setSearchQuery={setSearchQuery}
        planFilter={planFilter}
        setPlanFilter={setPlanFilter}
        statusFilter={statusFilter}
        setStatusFilter={setStatusFilter}
      />

      {/* 사용자 테이블 */}
      <UserTable
        loading={loading}
        users={users}
        page={page}
        rowsPerPage={rowsPerPage}
        total={total}
        onPageChange={setPage}
        onRowsPerPageChange={setRowsPerPage}
        onViewDetail={handleViewDetail}
        onToggleStatus={handleToggleUserStatus}
      />

      {/* 상세 정보 다이얼로그 */}
      <UserDetailDialog
        open={detailOpen}
        onClose={() => setDetailOpen(false)}
        userDetail={selectedUser}
        detailTab={detailTab}
        onTabChange={setDetailTab}
        onToggleStatus={handleToggleUserStatus}
      />
    </Box>
  );
};

export default UserManagement;
