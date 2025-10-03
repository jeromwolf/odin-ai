/**
 * 사용자 필터 컴포넌트
 */

import React from 'react';
import { Paper, Grid, TextField, MenuItem } from '@mui/material';
import { Search as SearchIcon } from '@mui/icons-material';

interface UserFiltersProps {
  searchQuery: string;
  setSearchQuery: (value: string) => void;
  planFilter: string;
  setPlanFilter: (value: string) => void;
  statusFilter: string;
  setStatusFilter: (value: string) => void;
}

export const UserFilters: React.FC<UserFiltersProps> = ({
  searchQuery,
  setSearchQuery,
  planFilter,
  setPlanFilter,
  statusFilter,
  setStatusFilter,
}) => {
  return (
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
  );
};
