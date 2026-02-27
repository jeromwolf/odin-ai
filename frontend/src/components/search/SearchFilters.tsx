/**
 * SearchFilters 컴포넌트
 * 검색 필터 UI 제공
 */

import React, { useState, useCallback } from 'react';
import {
  Box,
  Paper,
  Typography,
  TextField,
  Button,
  Chip,
  Stack,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  IconButton,
  Divider,
  Badge
} from '@mui/material';
import {
  ExpandMore as ExpandMoreIcon,
  FilterList as FilterListIcon,
  Clear as ClearIcon,
  DateRange as DateRangeIcon,
  AttachMoney as MoneyIcon,
  Business as BusinessIcon,
  Category as CategoryIcon
} from '@mui/icons-material';
import { DatePicker } from '@mui/x-date-pickers/DatePicker';
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider';
import { AdapterDateFns } from '@mui/x-date-pickers/AdapterDateFns';
import ko from 'date-fns/locale/ko';
import { format } from 'date-fns';
import { SearchFiltersProps, SearchFilters as FilterType } from '../../types/search.types';

// 가격 범위 옵션
const PRICE_RANGES = [
  { label: '전체', min: 0, max: null },
  { label: '1천만원 이하', min: 0, max: 10000000 },
  { label: '1천만원 ~ 5천만원', min: 10000000, max: 50000000 },
  { label: '5천만원 ~ 1억원', min: 50000000, max: 100000000 },
  { label: '1억원 ~ 5억원', min: 100000000, max: 500000000 },
  { label: '5억원 이상', min: 500000000, max: null }
];

// 상태 옵션
const STATUS_OPTIONS = [
  { value: '', label: '전체' },
  { value: 'active', label: '진행중' },
  { value: 'pending', label: '예정' },
  { value: 'closed', label: '마감' },
  { value: 'cancelled', label: '취소' }
];

const SearchFilters: React.FC<SearchFiltersProps> = ({
  filters,
  onFilterChange,
  facets
}) => {
  // 로컬 상태 (임시 필터 값)
  const [localFilters, setLocalFilters] = useState<FilterType>(filters);
  const [expanded, setExpanded] = useState<boolean>(true);

  // 활성 필터 개수 계산
  const activeFilterCount = Object.values(localFilters).filter(
    value => value !== undefined && value !== null && value !== ''
  ).length;

  /**
   * 날짜 변경 처리
   */
  const handleDateChange = (field: 'startDate' | 'endDate', value: Date | null) => {
    const newFilters = { ...localFilters };

    if (value) {
      newFilters[field] = format(value, 'yyyy-MM-dd');
    } else {
      delete newFilters[field];
    }

    setLocalFilters(newFilters);
  };

  /**
   * 가격 범위 변경 처리
   */
  const handlePriceRangeChange = (range: typeof PRICE_RANGES[0]) => {
    const newFilters = { ...localFilters };

    if (range.min === 0 && range.max === null) {
      // 전체 선택 시 가격 필터 제거
      delete newFilters.minPrice;
      delete newFilters.maxPrice;
    } else {
      if (range.min !== null) newFilters.minPrice = range.min;
      if (range.max !== null) newFilters.maxPrice = range.max;
      else delete newFilters.maxPrice;
    }

    setLocalFilters(newFilters);
  };

  /**
   * 커스텀 가격 범위 설정
   */
  const handleCustomPriceChange = (field: 'minPrice' | 'maxPrice', value: string) => {
    const newFilters = { ...localFilters };

    if (value) {
      const numValue = parseInt(value.replace(/[^0-9]/g, ''));
      if (!isNaN(numValue)) {
        newFilters[field] = numValue;
      }
    } else {
      delete newFilters[field];
    }

    setLocalFilters(newFilters);
  };

  /**
   * 일반 필드 변경 처리
   */
  const handleFieldChange = (field: keyof FilterType, value: string) => {
    const newFilters = { ...localFilters };

    if (value) {
      (newFilters as any)[field] = value;
    } else {
      delete newFilters[field];
    }

    setLocalFilters(newFilters);
  };

  /**
   * 필터 적용
   */
  const handleApply = useCallback(() => {
    onFilterChange(localFilters);
  }, [localFilters, onFilterChange]);

  /**
   * 필터 초기화
   */
  const handleReset = () => {
    const emptyFilters: FilterType = {};
    setLocalFilters(emptyFilters);
    onFilterChange(emptyFilters);
  };

  /**
   * 개별 필터 제거
   */
  const handleRemoveFilter = (key: keyof FilterType) => {
    const newFilters = { ...localFilters };
    delete newFilters[key];
    setLocalFilters(newFilters);
    onFilterChange(newFilters);
  };

  /**
   * 금액 포맷팅
   */
  const formatPrice = (price: number): string => {
    if (price >= 100000000) {
      return `${(price / 100000000).toFixed(1)}억원`;
    } else if (price >= 10000000) {
      return `${(price / 10000000).toFixed(1)}천만원`;
    } else if (price >= 10000) {
      return `${(price / 10000).toFixed(0)}만원`;
    }
    return `${price.toLocaleString()}원`;
  };

  /**
   * 활성 필터 칩 렌더링
   */
  const renderActiveFilters = () => {
    const chips: JSX.Element[] = [];

    if (localFilters.startDate) {
      chips.push(
        <Chip
          key="startDate"
          label={`시작일: ${localFilters.startDate}`}
          onDelete={() => handleRemoveFilter('startDate')}
          size="small"
          icon={<DateRangeIcon />}
        />
      );
    }

    if (localFilters.endDate) {
      chips.push(
        <Chip
          key="endDate"
          label={`종료일: ${localFilters.endDate}`}
          onDelete={() => handleRemoveFilter('endDate')}
          size="small"
          icon={<DateRangeIcon />}
        />
      );
    }

    if (localFilters.minPrice !== undefined) {
      chips.push(
        <Chip
          key="minPrice"
          label={`최소: ${formatPrice(localFilters.minPrice)}`}
          onDelete={() => handleRemoveFilter('minPrice')}
          size="small"
          icon={<MoneyIcon />}
        />
      );
    }

    if (localFilters.maxPrice !== undefined) {
      chips.push(
        <Chip
          key="maxPrice"
          label={`최대: ${formatPrice(localFilters.maxPrice)}`}
          onDelete={() => handleRemoveFilter('maxPrice')}
          size="small"
          icon={<MoneyIcon />}
        />
      );
    }

    if (localFilters.organization) {
      chips.push(
        <Chip
          key="organization"
          label={`기관: ${localFilters.organization}`}
          onDelete={() => handleRemoveFilter('organization')}
          size="small"
          icon={<BusinessIcon />}
        />
      );
    }

    if (localFilters.status) {
      const statusLabel = STATUS_OPTIONS.find(opt => opt.value === localFilters.status)?.label;
      chips.push(
        <Chip
          key="status"
          label={`상태: ${statusLabel}`}
          onDelete={() => handleRemoveFilter('status')}
          size="small"
        />
      );
    }

    return chips;
  };

  return (
    <Paper elevation={1} sx={{ p: 2 }}>
      {/* 헤더 */}
      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <Badge badgeContent={activeFilterCount} color="primary">
            <FilterListIcon />
          </Badge>
          <Typography variant="h6">검색 필터</Typography>
        </Box>
        <Box>
          <Button
            size="small"
            onClick={handleReset}
            disabled={activeFilterCount === 0}
            startIcon={<ClearIcon />}
          >
            초기화
          </Button>
          <IconButton
            size="small"
            onClick={() => setExpanded(!expanded)}
            sx={{ ml: 1 }}
          >
            <ExpandMoreIcon
              sx={{
                transform: expanded ? 'rotate(0deg)' : 'rotate(-90deg)',
                transition: 'transform 0.3s'
              }}
            />
          </IconButton>
        </Box>
      </Box>

      {/* 활성 필터 표시 */}
      {activeFilterCount > 0 && (
        <Stack direction="row" spacing={1} flexWrap="wrap" sx={{ mb: 2, gap: 0.5 }}>
          {renderActiveFilters()}
        </Stack>
      )}

      {/* 필터 섹션 */}
      {expanded && (
        <Box sx={{ mt: 2 }}>
          <Stack spacing={3}>
            {/* 날짜 범위 */}
            <Box>
              <Typography variant="subtitle2" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                <DateRangeIcon fontSize="small" />
                날짜 범위
              </Typography>
              <LocalizationProvider dateAdapter={AdapterDateFns} adapterLocale={ko}>
                <Stack direction="row" spacing={2}>
                  <DatePicker
                    label="시작일"
                    value={localFilters.startDate ? new Date(localFilters.startDate) : null}
                    onChange={(value) => handleDateChange('startDate', value)}
                    slotProps={{
                      textField: {
                        size: 'small',
                        fullWidth: true,
                        variant: 'outlined'
                      }
                    }}
                  />
                  <DatePicker
                    label="종료일"
                    value={localFilters.endDate ? new Date(localFilters.endDate) : null}
                    onChange={(value) => handleDateChange('endDate', value)}
                    slotProps={{
                      textField: {
                        size: 'small',
                        fullWidth: true,
                        variant: 'outlined'
                      }
                    }}
                  />
                </Stack>
              </LocalizationProvider>
            </Box>

            <Divider />

            {/* 가격 범위 */}
            <Box>
              <Typography variant="subtitle2" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                <MoneyIcon fontSize="small" />
                가격 범위
              </Typography>
              <Stack spacing={2}>
                <Stack direction="row" spacing={1} flexWrap="wrap">
                  {PRICE_RANGES.map((range, index) => (
                    <Chip
                      key={index}
                      label={range.label}
                      onClick={() => handlePriceRangeChange(range)}
                      color={
                        localFilters.minPrice === range.min &&
                        (localFilters.maxPrice === range.max || (!localFilters.maxPrice && range.max === null))
                          ? 'primary' : 'default'
                      }
                      variant={
                        localFilters.minPrice === range.min &&
                        (localFilters.maxPrice === range.max || (!localFilters.maxPrice && range.max === null))
                          ? 'filled' : 'outlined'
                      }
                      size="small"
                    />
                  ))}
                </Stack>
                <Stack direction="row" spacing={2}>
                  <TextField
                    size="small"
                    label="최소 금액"
                    placeholder="0"
                    value={localFilters.minPrice || ''}
                    onChange={(e) => handleCustomPriceChange('minPrice', e.target.value)}
                    type="number"
                    fullWidth
                  />
                  <TextField
                    size="small"
                    label="최대 금액"
                    placeholder="제한없음"
                    value={localFilters.maxPrice || ''}
                    onChange={(e) => handleCustomPriceChange('maxPrice', e.target.value)}
                    type="number"
                    fullWidth
                  />
                </Stack>
              </Stack>
            </Box>

            <Divider />

            {/* 기관 및 상태 */}
            <Stack direction="row" spacing={2}>
              <TextField
                size="small"
                label="발주기관"
                value={localFilters.organization || ''}
                onChange={(e) => handleFieldChange('organization', e.target.value)}
                placeholder="기관명 입력"
                fullWidth
                InputProps={{
                  startAdornment: <BusinessIcon sx={{ mr: 1, color: 'action.active' }} fontSize="small" />
                }}
              />
              <FormControl size="small" fullWidth>
                <InputLabel>상태</InputLabel>
                <Select
                  value={localFilters.status || ''}
                  onChange={(e) => handleFieldChange('status', e.target.value)}
                  label="상태"
                >
                  {STATUS_OPTIONS.map(option => (
                    <MenuItem key={option.value} value={option.value}>
                      {option.label}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Stack>

            <Divider />

            {/* 추가 필터 */}
            <Stack direction="row" spacing={2}>
              <TextField
                size="small"
                label="산업분야"
                value={localFilters.industry || ''}
                onChange={(e) => handleFieldChange('industry', e.target.value)}
                placeholder="산업분야 입력"
                fullWidth
                InputProps={{
                  startAdornment: <CategoryIcon sx={{ mr: 1, color: 'action.active' }} fontSize="small" />
                }}
              />
              <TextField
                size="small"
                label="지역"
                value={localFilters.region || ''}
                onChange={(e) => handleFieldChange('region', e.target.value)}
                placeholder="지역 입력"
                fullWidth
              />
            </Stack>

            {/* 적용 버튼 */}
            <Box sx={{ display: 'flex', justifyContent: 'flex-end', gap: 1, mt: 2 }}>
              <Button
                variant="outlined"
                onClick={handleReset}
                disabled={activeFilterCount === 0}
              >
                초기화
              </Button>
              <Button
                variant="contained"
                onClick={handleApply}
                disabled={JSON.stringify(filters) === JSON.stringify(localFilters)}
              >
                필터 적용
              </Button>
            </Box>
          </Stack>
        </Box>
      )}

      {/* 패싯 정보 표시 (선택사항) */}
      {facets && expanded && (
        <Box sx={{ mt: 3, pt: 2, borderTop: 1, borderColor: 'divider' }}>
          <Typography variant="subtitle2" gutterBottom>
            빠른 필터
          </Typography>
          <Stack spacing={1}>
            {facets.organizations && facets.organizations.length > 0 && (
              <Box>
                <Typography variant="caption" color="text.secondary">
                  주요 기관
                </Typography>
                <Stack direction="row" spacing={0.5} flexWrap="wrap" sx={{ mt: 0.5 }}>
                  {facets.organizations.slice(0, 5).map((org, index) => (
                    <Chip
                      key={index}
                      label={`${org.name} (${org.count})`}
                      size="small"
                      variant="outlined"
                      onClick={() => handleFieldChange('organization', org.name)}
                    />
                  ))}
                </Stack>
              </Box>
            )}
          </Stack>
        </Box>
      )}
    </Paper>
  );
};

export default SearchFilters;