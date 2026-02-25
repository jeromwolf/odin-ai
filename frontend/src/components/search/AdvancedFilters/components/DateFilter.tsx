/**
 * DateFilter - 날짜 범위 필터 컴포넌트
 */

import React from 'react';
import { Typography, Stack, Chip, Collapse, IconButton } from '@mui/material';
import {
  DateRange as DateIcon,
  ExpandMore as ExpandIcon,
  ExpandLess as CollapseIcon
} from '@mui/icons-material';
import { DatePicker } from '@mui/x-date-pickers/DatePicker';
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider';
import { AdapterDateFns } from '@mui/x-date-pickers/AdapterDateFns';
import ko from 'date-fns/locale/ko';
import { FilterSection, SectionHeader, SearchFilters } from '../types';

interface DateFilterProps {
  expanded: boolean;
  onToggle: () => void;
  localFilters: SearchFilters;
  onDateChange: (field: 'startDate' | 'endDate', value: Date | null) => void;
  onSetToday: () => void;
  onSetThisWeek: () => void;
  onSetThisMonth: () => void;
}

const DateFilter: React.FC<DateFilterProps> = ({
  expanded,
  onToggle,
  localFilters,
  onDateChange,
  onSetToday,
  onSetThisWeek,
  onSetThisMonth
}) => {
  return (
    <FilterSection>
      <SectionHeader onClick={onToggle}>
        <DateIcon color="action" />
        <Typography variant="subtitle2" className="section-title">
          공고 기간
        </Typography>
        {(localFilters.startDate || localFilters.endDate) && (
          <Chip size="small" label="설정됨" color="primary" sx={{ ml: 'auto', mr: 1 }} />
        )}
        <IconButton size="small">
          {expanded ? <CollapseIcon /> : <ExpandIcon />}
        </IconButton>
      </SectionHeader>

      <Collapse in={expanded}>
        <LocalizationProvider dateAdapter={AdapterDateFns} adapterLocale={ko}>
          <Stack spacing={2}>
            <DatePicker
              label="시작일"
              value={localFilters.startDate ? new Date(localFilters.startDate) : null}
              onChange={(value) => onDateChange('startDate', value)}
              slotProps={{ textField: { size: 'small', fullWidth: true } }}
            />
            <DatePicker
              label="종료일"
              value={localFilters.endDate ? new Date(localFilters.endDate) : null}
              onChange={(value) => onDateChange('endDate', value)}
              slotProps={{ textField: { size: 'small', fullWidth: true } }}
            />
            <Stack direction="row" spacing={1}>
              <Chip label="오늘" size="small" onClick={onSetToday} clickable />
              <Chip label="이번 주" size="small" onClick={onSetThisWeek} clickable />
              <Chip label="이번 달" size="small" onClick={onSetThisMonth} clickable />
            </Stack>
          </Stack>
        </LocalizationProvider>
      </Collapse>
    </FilterSection>
  );
};

export default DateFilter;
