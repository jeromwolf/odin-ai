/**
 * AdvancedFilters 컴포넌트 타입 및 공유 상수
 */

import React from 'react';
import { Paper, Box, Chip, Slider } from '@mui/material';
import {
  TrendingUp as TrendingIcon,
  Category as CategoryIcon,
  Business as BusinessIcon
} from '@mui/icons-material';
import { styled, alpha } from '@mui/material/styles';
import { SearchFilters, FilterPreset } from '../../../types/search.types';

export interface AdvancedFiltersProps {
  filters: SearchFilters;
  onFilterChange: (filters: SearchFilters) => void;
  onPresetSave?: (preset: FilterPreset) => void;
  savedPresets?: FilterPreset[];
  suggestions?: {
    organizations?: string[];
    categories?: string[];
    tags?: string[];
  };
  showInsights?: boolean;
}

export type { SearchFilters, FilterPreset };

// 공유 스타일 컴포넌트
export const FilterContainer = styled(Paper)(({ theme }) => ({
  padding: theme.spacing(2),
  borderRadius: theme.shape.borderRadius * 2,
  border: `1px solid ${theme.palette.divider}`,
  background: `linear-gradient(135deg, ${theme.palette.background.paper} 0%, ${alpha(
    theme.palette.primary.main,
    0.02
  )} 100%)`
}));

export const FilterSection = styled(Box)(({ theme }) => ({
  marginBottom: theme.spacing(3),
  '&:last-child': {
    marginBottom: 0
  }
}));

export const SectionHeader = styled(Box)(({ theme }) => ({
  display: 'flex',
  alignItems: 'center',
  marginBottom: theme.spacing(2),
  gap: theme.spacing(1),
  cursor: 'pointer',
  '&:hover': {
    '& .section-title': {
      color: theme.palette.primary.main
    }
  }
}));

export const StyledSlider = styled(Slider)(({ theme }) => ({
  '& .MuiSlider-rail': { height: 6, borderRadius: 3 },
  '& .MuiSlider-track': { height: 6, borderRadius: 3 },
  '& .MuiSlider-thumb': {
    width: 20,
    height: 20,
    '&:hover, &.Mui-focusVisible': {
      boxShadow: `0 0 0 8px ${alpha(theme.palette.primary.main, 0.16)}`
    }
  },
  '& .MuiSlider-valueLabel': {
    borderRadius: theme.shape.borderRadius,
    backgroundColor: theme.palette.primary.main
  }
}));

export const PresetChip = styled(Chip)(({ theme }) => ({
  fontWeight: 600,
  transition: 'all 0.3s ease',
  '&:hover': {
    transform: 'translateY(-2px)',
    boxShadow: theme.shadows[4]
  },
  '&.selected': {
    backgroundColor: theme.palette.primary.main,
    color: theme.palette.primary.contrastText
  }
}));

export const TagChip = styled(Chip)(({ theme }) => ({
  margin: theme.spacing(0.5),
  '&.selected': {
    backgroundColor: theme.palette.primary.main,
    color: theme.palette.primary.contrastText
  }
}));

// 기본 프리셋
export const DEFAULT_PRESETS: FilterPreset[] = [
  {
    id: 'recent-high-value',
    name: '최근 고액 입찰',
    icon: React.createElement(TrendingIcon),
    filters: {
      minPrice: 100000000,
      startDate: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
      status: 'active'
    }
  },
  {
    id: 'construction',
    name: '건설/공사',
    icon: React.createElement(CategoryIcon),
    filters: {
      tags: ['건설', '공사', '시공'],
      industry: 'construction'
    }
  },
  {
    id: 'it-software',
    name: 'IT/소프트웨어',
    icon: React.createElement(CategoryIcon),
    filters: {
      tags: ['소프트웨어', 'SI', '시스템', '개발'],
      industry: 'it'
    }
  },
  {
    id: 'small-business',
    name: '중소기업 적합',
    icon: React.createElement(BusinessIcon),
    filters: {
      maxPrice: 50000000,
      tags: ['중소기업']
    }
  }
];

export const AVAILABLE_TAGS = ['건설', '소프트웨어', 'SI사업', '장비구매', '용역', '공사', '물품', '연구개발'];

export const PRICE_MARKS = [
  { value: 0, label: '0' },
  { value: 10000000, label: '1천만' },
  { value: 50000000, label: '5천만' },
  { value: 100000000, label: '1억' },
  { value: 500000000, label: '5억' },
  { value: 1000000000, label: '10억' }
];
