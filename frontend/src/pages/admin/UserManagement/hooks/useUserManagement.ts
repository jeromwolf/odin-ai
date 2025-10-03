/**
 * UserManagement 커스텀 훅
 * 사용자 관리 페이지의 state와 handlers를 관리
 */

import { useState, useEffect } from 'react';
import { adminApi } from '../../../../services/admin/adminApi';
import { User, UserDetail } from '../types';

export const useUserManagement = () => {
  // State
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

  // 사용자 목록 로드
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

  // 사용자 통계 로드
  const loadUserStats = async () => {
    try {
      const stats = await adminApi.getUserStatistics();
      setUserStats(stats);
    } catch (err) {
      console.error('사용자 통계 조회 실패:', err);
    }
  };

  // 사용자 상세 정보 보기
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

  // 사용자 활성/비활성 토글
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

  // Effect: 페이지/필터 변경 시 데이터 로드
  useEffect(() => {
    loadUsers();
    loadUserStats();
  }, [page, rowsPerPage, searchQuery, planFilter, statusFilter]);

  return {
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
    loadUserStats,
    handleViewDetail,
    handleToggleUserStatus,
  };
};
