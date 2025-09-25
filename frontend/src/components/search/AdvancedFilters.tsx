/**
 * AdvancedFilters 컴포넌트
 * 고급 필터링 기능 (슬라이더, 태그, 프리셋 등)
 */

import React, { useState, useCallback, useEffect, useMemo } from 'react';
import {
  Box,
  Paper,
  Typography,
  Slider,
  TextField,
  Chip,
  Stack,
  Button,
  IconButton,
  Collapse,
  Divider,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  FormControlLabel,
  Switch,
  Checkbox,
  Autocomplete,
  ToggleButton,
  ToggleButtonGroup,
  Tooltip,
  Badge,
  Alert,
  Fade,
  Zoom,
  alpha,
  useTheme
} from '@mui/material';
import {
  FilterList as FilterIcon,
  Clear as ClearIcon,
  Save as SaveIcon,
  RestoreOutlined as RestoreIcon,
  ExpandMore as ExpandIcon,
  ExpandLess as CollapseIcon,
  AttachMoney as MoneyIcon,
  DateRange as DateIcon,
  Business as OrgIcon,
  Business as BusinessIcon,
  Category as CategoryIcon,
  LocalOffer as TagIcon,
  Bookmark as BookmarkIcon,
  TrendingUp as TrendingIcon,
  AutoAwesome as AutoIcon,
  Info as InfoIcon
} from '@mui/icons-material';
import { DatePicker } from '@mui/x-date-pickers/DatePicker';
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider';
import { AdapterDateFns } from '@mui/x-date-pickers/AdapterDateFns';
import ko from 'date-fns/locale/ko';
import { styled } from '@mui/material/styles';
import { SearchFilters, FilterPreset } from '../../types/search.types';

// 스타일 컴포넌트
const FilterContainer = styled(Paper)(({ theme }) => ({
  padding: theme.spacing(2),
  borderRadius: theme.shape.borderRadius * 2,
  border: `1px solid ${theme.palette.divider}`,
  background: `linear-gradient(135deg, ${theme.palette.background.paper} 0%, ${alpha(
    theme.palette.primary.main,
    0.02
  )} 100%)`
}));

const FilterSection = styled(Box)(({ theme }) => ({
  marginBottom: theme.spacing(3),
  '&:last-child': {
    marginBottom: 0
  }
}));

const SectionHeader = styled(Box)(({ theme }) => ({
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

const StyledSlider = styled(Slider)(({ theme }) => ({
  '& .MuiSlider-rail': {
    height: 6,
    borderRadius: 3
  },
  '& .MuiSlider-track': {
    height: 6,
    borderRadius: 3
  },
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

const PresetChip = styled(Chip)(({ theme }) => ({
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

const TagChip = styled(Chip)(({ theme }) => ({
  margin: theme.spacing(0.5),
  '&.selected': {
    backgroundColor: theme.palette.primary.main,
    color: theme.palette.primary.contrastText
  }
}));

// Props 인터페이스
interface AdvancedFiltersProps {
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

// 가격 범위 마크
const priceMarks = [
  { value: 0, label: '0' },
  { value: 10000000, label: '1천만' },
  { value: 50000000, label: '5천만' },
  { value: 100000000, label: '1억' },
  { value: 500000000, label: '5억' },
  { value: 1000000000, label: '10억' }
];

// 기본 프리셋
const DEFAULT_PRESETS: FilterPreset[] = [
  {
    id: 'recent-high-value',
    name: '최근 고액 입찰',
    icon: <TrendingIcon />,
    filters: {
      minPrice: 100000000,
      startDate: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
      status: 'active'
    }
  },
  {
    id: 'construction',
    name: '건설/공사',
    icon: <CategoryIcon />,
    filters: {
      tags: ['건설', '공사', '시공'],
      industry: 'construction'
    }
  },
  {
    id: 'it-software',
    name: 'IT/소프트웨어',
    icon: <CategoryIcon />,
    filters: {
      tags: ['소프트웨어', 'SI', '시스템', '개발'],
      industry: 'it'
    }
  },
  {
    id: 'small-business',
    name: '중소기업 적합',
    icon: <BusinessIcon />,
    filters: {
      maxPrice: 50000000,
      tags: ['중소기업']
    }
  }
];

const AdvancedFilters: React.FC<AdvancedFiltersProps> = ({
  filters,
  onFilterChange,
  onPresetSave,
  savedPresets = [],
  suggestions = {},
  showInsights = true
}) => {
  const theme = useTheme();
  const [localFilters, setLocalFilters] = useState<SearchFilters>(filters);
  const [expandedSections, setExpandedSections] = useState<Set<string>>(
    new Set(['price', 'date', 'organization'])
  );
  const [selectedPreset, setSelectedPreset] = useState<string | null>(null);
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [priceRange, setPriceRange] = useState<[number, number]>([
    filters.minPrice || 0,
    filters.maxPrice || 1000000000
  ]);
  const [selectedTags, setSelectedTags] = useState<string[]>(filters.tags || []);
  const [customPresetName, setCustomPresetName] = useState('');
  const [showPresetDialog, setShowPresetDialog] = useState(false);

  // 활성 필터 수 계산
  const activeFilterCount = useMemo(() => {
    let count = 0;
    if (localFilters.minPrice || localFilters.maxPrice) count++;
    if (localFilters.startDate || localFilters.endDate) count++;
    if (localFilters.organization) count++;
    if (localFilters.status) count++;
    if (localFilters.tags?.length) count++;
    if (localFilters.industry) count++;
    if (localFilters.region) count++;
    return count;
  }, [localFilters]);

  // 섹션 토글
  const toggleSection = (section: string) => {
    setExpandedSections(prev => {
      const newSet = new Set(prev);
      if (newSet.has(section)) {
        newSet.delete(section);
      } else {
        newSet.add(section);
      }
      return newSet;
    });
  };

  // 가격 슬라이더 변경
  const handlePriceChange = (event: Event, newValue: number | number[]) => {
    const [min, max] = newValue as number[];
    setPriceRange([min, max]);
  };

  // 가격 슬라이더 커밋
  const handlePriceCommit = () => {
    setLocalFilters({
      ...localFilters,
      minPrice: priceRange[0] > 0 ? priceRange[0] : undefined,
      maxPrice: priceRange[1] < 1000000000 ? priceRange[1] : undefined
    });
  };

  // 날짜 변경
  const handleDateChange = (field: 'startDate' | 'endDate', value: Date | null) => {
    setLocalFilters({
      ...localFilters,
      [field]: value ? value.toISOString().split('T')[0] : undefined
    });
  };

  // 태그 변경
  const handleTagToggle = (tag: string) => {
    const newTags = selectedTags.includes(tag)
      ? selectedTags.filter(t => t !== tag)
      : [...selectedTags, tag];

    setSelectedTags(newTags);
    setLocalFilters({
      ...localFilters,
      tags: newTags.length > 0 ? newTags : undefined
    });
  };

  // 프리셋 적용
  const applyPreset = (preset: FilterPreset) => {
    setLocalFilters({ ...localFilters, ...preset.filters });
    setSelectedPreset(preset.id);

    // 가격 범위 업데이트
    if (preset.filters.minPrice || preset.filters.maxPrice) {
      setPriceRange([
        preset.filters.minPrice || 0,
        preset.filters.maxPrice || 1000000000
      ]);
    }

    // 태그 업데이트
    if (preset.filters.tags) {
      setSelectedTags(preset.filters.tags);
    }
  };

  // 필터 적용
  const handleApply = () => {
    onFilterChange(localFilters);
  };

  // 필터 초기화
  const handleReset = () => {
    const emptyFilters: SearchFilters = {};
    setLocalFilters(emptyFilters);
    setPriceRange([0, 1000000000]);
    setSelectedTags([]);
    setSelectedPreset(null);
    onFilterChange(emptyFilters);
  };

  // 프리셋 저장
  const handleSavePreset = () => {
    if (customPresetName && onPresetSave) {
      onPresetSave({
        id: `custom-${Date.now()}`,
        name: customPresetName,
        filters: localFilters,
        icon: <BookmarkIcon />
      });
      setCustomPresetName('');
      setShowPresetDialog(false);
    }
  };

  // 가격 포맷팅
  const formatPrice = (value: number): string => {
    if (value >= 100000000) {
      return `${(value / 100000000).toFixed(1)}억`;
    } else if (value >= 10000000) {
      return `${(value / 10000000).toFixed(1)}천만`;
    } else if (value >= 10000) {
      return `${(value / 10000).toFixed(0)}만`;
    }
    return value.toLocaleString();
  };

  // 인사이트 생성
  const generateInsights = (): string[] => {
    const insights = [];

    if (localFilters.minPrice && localFilters.minPrice > 100000000) {
      insights.push('대형 프로젝트를 검색 중입니다');
    }

    if (localFilters.startDate && localFilters.endDate) {
      const days = Math.ceil(
        (new Date(localFilters.endDate).getTime() - new Date(localFilters.startDate).getTime()) /
        (1000 * 60 * 60 * 24)
      );
      insights.push(`${days}일 기간의 공고를 검색합니다`);
    }

    if (selectedTags.length > 3) {
      insights.push('다양한 분야를 폭넓게 검색 중입니다');
    }

    return insights;
  };

  return (
    <FilterContainer elevation={1}>
      {/* 헤더 */}
      <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
        <FilterIcon sx={{ mr: 1 }} />
        <Typography variant="h6" sx={{ flexGrow: 1 }}>
          고급 필터
        </Typography>
        <Badge badgeContent={activeFilterCount} color="primary">
          <IconButton size="small" onClick={() => setShowAdvanced(!showAdvanced)}>
            {showAdvanced ? <CollapseIcon /> : <ExpandIcon />}
          </IconButton>
        </Badge>
      </Box>

      {/* 프리셋 */}
      <FilterSection>
        <Typography variant="subtitle2" gutterBottom sx={{ mb: 1 }}>
          빠른 필터 프리셋
        </Typography>
        <Stack direction="row" spacing={1} flexWrap="wrap" sx={{ gap: 0.5 }}>
          {[...DEFAULT_PRESETS, ...savedPresets].map(preset => (
            <PresetChip
              key={preset.id}
              icon={preset.icon as React.ReactElement | undefined}
              label={preset.name}
              className={selectedPreset === preset.id ? 'selected' : ''}
              onClick={() => applyPreset(preset)}
              clickable
            />
          ))}
          <PresetChip
            icon={<SaveIcon />}
            label="현재 필터 저장"
            variant="outlined"
            onClick={() => setShowPresetDialog(true)}
            clickable
          />
        </Stack>
      </FilterSection>

      <Divider sx={{ my: 2 }} />

      {/* 가격 범위 */}
      <FilterSection>
        <SectionHeader onClick={() => toggleSection('price')}>
          <MoneyIcon color="action" />
          <Typography variant="subtitle2" className="section-title">
            가격 범위
          </Typography>
          <Typography variant="caption" color="text.secondary" sx={{ ml: 'auto' }}>
            {formatPrice(priceRange[0])} ~ {formatPrice(priceRange[1])}
          </Typography>
          <IconButton size="small">
            {expandedSections.has('price') ? <CollapseIcon /> : <ExpandIcon />}
          </IconButton>
        </SectionHeader>

        <Collapse in={expandedSections.has('price')}>
          <Box sx={{ px: 2 }}>
            <StyledSlider
              value={priceRange}
              onChange={handlePriceChange}
              onChangeCommitted={handlePriceCommit}
              valueLabelDisplay="auto"
              valueLabelFormat={formatPrice}
              min={0}
              max={1000000000}
              marks={priceMarks}
              sx={{ mt: 4, mb: 2 }}
            />
            <Stack direction="row" spacing={2}>
              <TextField
                size="small"
                label="최소"
                value={priceRange[0]}
                onChange={(e) => setPriceRange([Number(e.target.value), priceRange[1]])}
                type="number"
                fullWidth
              />
              <TextField
                size="small"
                label="최대"
                value={priceRange[1]}
                onChange={(e) => setPriceRange([priceRange[0], Number(e.target.value)])}
                type="number"
                fullWidth
              />
            </Stack>
          </Box>
        </Collapse>
      </FilterSection>

      <Divider sx={{ my: 2 }} />

      {/* 기간 */}
      <FilterSection>
        <SectionHeader onClick={() => toggleSection('date')}>
          <DateIcon color="action" />
          <Typography variant="subtitle2" className="section-title">
            공고 기간
          </Typography>
          {(localFilters.startDate || localFilters.endDate) && (
            <Chip
              size="small"
              label="설정됨"
              color="primary"
              sx={{ ml: 'auto', mr: 1 }}
            />
          )}
          <IconButton size="small">
            {expandedSections.has('date') ? <CollapseIcon /> : <ExpandIcon />}
          </IconButton>
        </SectionHeader>

        <Collapse in={expandedSections.has('date')}>
          <LocalizationProvider dateAdapter={AdapterDateFns} adapterLocale={ko}>
            <Stack spacing={2}>
              <DatePicker
                label="시작일"
                value={localFilters.startDate ? new Date(localFilters.startDate) : null}
                onChange={(value) => handleDateChange('startDate', value)}
                slotProps={{
                  textField: {
                    size: 'small',
                    fullWidth: true
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
                    fullWidth: true
                  }
                }}
              />

              {/* 빠른 날짜 선택 */}
              <Stack direction="row" spacing={1}>
                <Chip
                  label="오늘"
                  size="small"
                  onClick={() => {
                    const today = new Date().toISOString().split('T')[0];
                    setLocalFilters({ ...localFilters, startDate: today, endDate: today });
                  }}
                  clickable
                />
                <Chip
                  label="이번 주"
                  size="small"
                  onClick={() => {
                    const now = new Date();
                    const monday = new Date(now);
                    monday.setDate(now.getDate() - now.getDay() + 1);
                    const sunday = new Date(monday);
                    sunday.setDate(monday.getDate() + 6);
                    setLocalFilters({
                      ...localFilters,
                      startDate: monday.toISOString().split('T')[0],
                      endDate: sunday.toISOString().split('T')[0]
                    });
                  }}
                  clickable
                />
                <Chip
                  label="이번 달"
                  size="small"
                  onClick={() => {
                    const now = new Date();
                    const firstDay = new Date(now.getFullYear(), now.getMonth(), 1);
                    const lastDay = new Date(now.getFullYear(), now.getMonth() + 1, 0);
                    setLocalFilters({
                      ...localFilters,
                      startDate: firstDay.toISOString().split('T')[0],
                      endDate: lastDay.toISOString().split('T')[0]
                    });
                  }}
                  clickable
                />
              </Stack>
            </Stack>
          </LocalizationProvider>
        </Collapse>
      </FilterSection>

      <Divider sx={{ my: 2 }} />

      {/* 기관/분야 */}
      <FilterSection>
        <SectionHeader onClick={() => toggleSection('organization')}>
          <OrgIcon color="action" />
          <Typography variant="subtitle2" className="section-title">
            기관 및 분야
          </Typography>
          <IconButton size="small" sx={{ ml: 'auto' }}>
            {expandedSections.has('organization') ? <CollapseIcon /> : <ExpandIcon />}
          </IconButton>
        </SectionHeader>

        <Collapse in={expandedSections.has('organization')}>
          <Stack spacing={2}>
            <Autocomplete
              size="small"
              options={suggestions.organizations || []}
              value={localFilters.organization || null}
              onChange={(_, value) => setLocalFilters({ ...localFilters, organization: value || undefined })}
              renderInput={(params) => (
                <TextField {...params} label="발주기관" placeholder="기관 선택 또는 입력" />
              )}
              freeSolo
            />

            <FormControl size="small" fullWidth>
              <InputLabel>산업 분야</InputLabel>
              <Select
                value={localFilters.industry || ''}
                onChange={(e) => setLocalFilters({ ...localFilters, industry: e.target.value || undefined })}
                label="산업 분야"
              >
                <MenuItem value="">전체</MenuItem>
                <MenuItem value="construction">건설/토목</MenuItem>
                <MenuItem value="it">IT/소프트웨어</MenuItem>
                <MenuItem value="medical">의료/제약</MenuItem>
                <MenuItem value="education">교육</MenuItem>
                <MenuItem value="environment">환경/에너지</MenuItem>
                <MenuItem value="defense">국방/보안</MenuItem>
              </Select>
            </FormControl>

            <TextField
              size="small"
              label="지역"
              value={localFilters.region || ''}
              onChange={(e) => setLocalFilters({ ...localFilters, region: e.target.value || undefined })}
              placeholder="예: 서울, 경기"
              fullWidth
            />
          </Stack>
        </Collapse>
      </FilterSection>

      {/* 고급 옵션 */}
      <Collapse in={showAdvanced}>
        <Divider sx={{ my: 2 }} />

        <FilterSection>
          <Typography variant="subtitle2" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <TagIcon />
            태그 필터
          </Typography>

          <Box sx={{ display: 'flex', flexWrap: 'wrap' }}>
            {['건설', '소프트웨어', 'SI사업', '장비구매', '용역', '공사', '물품', '연구개발'].map(tag => (
              <TagChip
                key={tag}
                label={tag}
                className={selectedTags.includes(tag) ? 'selected' : ''}
                onClick={() => handleTagToggle(tag)}
                clickable
              />
            ))}
          </Box>
        </FilterSection>

        <FilterSection>
          <Typography variant="subtitle2" gutterBottom>
            추가 옵션
          </Typography>

          <Stack spacing={1}>
            <FormControlLabel
              control={
                <Switch
                  checked={localFilters.excludeClosed || false}
                  onChange={(e) => setLocalFilters({ ...localFilters, excludeClosed: e.target.checked })}
                />
              }
              label="마감된 공고 제외"
            />
            <FormControlLabel
              control={
                <Switch
                  checked={localFilters.onlyUrgent || false}
                  onChange={(e) => setLocalFilters({ ...localFilters, onlyUrgent: e.target.checked })}
                />
              }
              label="긴급 공고만"
            />
            <FormControlLabel
              control={
                <Switch
                  checked={localFilters.hasAttachments || false}
                  onChange={(e) => setLocalFilters({ ...localFilters, hasAttachments: e.target.checked })}
                />
              }
              label="첨부파일 있는 공고만"
            />
          </Stack>
        </FilterSection>
      </Collapse>

      {/* 인사이트 */}
      {showInsights && activeFilterCount > 0 && (
        <Fade in>
          <Alert severity="info" icon={<AutoIcon />} sx={{ mt: 2 }}>
            <Stack spacing={0.5}>
              {generateInsights().map((insight, index) => (
                <Typography key={index} variant="caption">
                  • {insight}
                </Typography>
              ))}
            </Stack>
          </Alert>
        </Fade>
      )}

      {/* 액션 버튼 */}
      <Stack direction="row" spacing={1} sx={{ mt: 3 }}>
        <Button
          variant="outlined"
          startIcon={<ClearIcon />}
          onClick={handleReset}
          disabled={activeFilterCount === 0}
          fullWidth
        >
          초기화
        </Button>
        <Button
          variant="contained"
          startIcon={<FilterIcon />}
          onClick={handleApply}
          fullWidth
          disabled={JSON.stringify(filters) === JSON.stringify(localFilters)}
        >
          필터 적용 {activeFilterCount > 0 && `(${activeFilterCount})`}
        </Button>
      </Stack>

      {/* 프리셋 저장 다이얼로그 */}
      <Collapse in={showPresetDialog}>
        <Paper sx={{ mt: 2, p: 2, bgcolor: 'background.default' }}>
          <Typography variant="subtitle2" gutterBottom>
            필터 프리셋 저장
          </Typography>
          <TextField
            size="small"
            label="프리셋 이름"
            value={customPresetName}
            onChange={(e) => setCustomPresetName(e.target.value)}
            fullWidth
            sx={{ mb: 2 }}
          />
          <Stack direction="row" spacing={1}>
            <Button
              size="small"
              onClick={() => setShowPresetDialog(false)}
              fullWidth
            >
              취소
            </Button>
            <Button
              size="small"
              variant="contained"
              onClick={handleSavePreset}
              disabled={!customPresetName}
              fullWidth
            >
              저장
            </Button>
          </Stack>
        </Paper>
      </Collapse>
    </FilterContainer>
  );
};

export default AdvancedFilters;