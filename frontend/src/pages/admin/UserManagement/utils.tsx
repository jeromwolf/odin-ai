/**
 * UserManagement 유틸리티 함수들
 */

import React from 'react';
import { Chip } from '@mui/material';
import { CheckCircle, Block } from '@mui/icons-material';

/**
 * 구독 플랜에 따른 칩 컴포넌트 반환
 */
export const getPlanChip = (plan: string) => {
  const configs: Record<string, { label: string; color: 'default' | 'primary' | 'secondary' | 'success' }> = {
    free: { label: '무료', color: 'default' },
    basic: { label: '베이직', color: 'primary' },
    pro: { label: '프로', color: 'secondary' },
    enterprise: { label: '엔터프라이즈', color: 'success' },
  };
  const config = configs[plan] || { label: plan, color: 'default' };
  return <Chip label={config.label} color={config.color} size="small" />;
};

/**
 * 사용자 활성 상태에 따른 칩 컴포넌트 반환
 */
export const getStatusChip = (isActive: boolean) => {
  return (
    <Chip
      label={isActive ? '활성' : '비활성'}
      color={isActive ? 'success' : 'error'}
      size="small"
      icon={isActive ? <CheckCircle /> : <Block />}
    />
  );
};
