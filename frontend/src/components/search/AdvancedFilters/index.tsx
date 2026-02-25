/**
 * AdvancedFilters 컴포넌트
 * 고급 필터링 기능 (슬라이더, 태그, 프리셋 등)
 */

import React from 'react';
import {
  Box, Typography, Stack, Button, IconButton,
  Divider, TextField, Badge, Alert, Fade, Collapse
} from '@mui/material';
import {
  FilterList as FilterIcon,
  Clear as ClearIcon,
  Save as SaveIcon,
  ExpandMore as ExpandIcon,
  ExpandLess as CollapseIcon,
  AutoAwesome as AutoIcon
} from '@mui/icons-material';
import {
  AdvancedFiltersProps, FilterContainer, FilterSection,
  PresetChip, DEFAULT_PRESETS
} from './types';
import { useAdvancedFilters } from './hooks/useAdvancedFilters';
import PriceFilter from './components/PriceFilter';
import DateFilter from './components/DateFilter';
import StatusFilter from './components/StatusFilter';
import OrgFilter from './components/OrgFilter';

const AdvancedFilters: React.FC<AdvancedFiltersProps> = ({
  filters,
  onFilterChange,
  onPresetSave,
  savedPresets = [],
  suggestions = {},
  showInsights = true
}) => {
  const {
    localFilters, setLocalFilters, expandedSections, selectedPreset,
    showAdvanced, setShowAdvanced, priceRange, setPriceRange,
    selectedTags, customPresetName, setCustomPresetName,
    showPresetDialog, setShowPresetDialog, activeFilterCount,
    toggleSection, handlePriceChange, handlePriceCommit,
    handleDateChange, handleTagToggle, applyPreset,
    handleApply, handleReset, handleSavePreset,
    formatPrice, generateInsights,
    setDateToday, setDateThisWeek, setDateThisMonth
  } = useAdvancedFilters({ filters, onFilterChange, onPresetSave });

  return (
    <FilterContainer elevation={1}>
      {/* 헤더 */}
      <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
        <FilterIcon sx={{ mr: 1 }} />
        <Typography variant="h6" sx={{ flexGrow: 1 }}>고급 필터</Typography>
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

      <PriceFilter
        expanded={expandedSections.has('price')}
        onToggle={() => toggleSection('price')}
        priceRange={priceRange}
        onPriceChange={handlePriceChange}
        onPriceCommit={handlePriceCommit}
        onMinChange={(value) => setPriceRange([value, priceRange[1]])}
        onMaxChange={(value) => setPriceRange([priceRange[0], value])}
        formatPrice={formatPrice}
      />

      <Divider sx={{ my: 2 }} />

      <DateFilter
        expanded={expandedSections.has('date')}
        onToggle={() => toggleSection('date')}
        localFilters={localFilters}
        onDateChange={handleDateChange}
        onSetToday={setDateToday}
        onSetThisWeek={setDateThisWeek}
        onSetThisMonth={setDateThisMonth}
      />

      <Divider sx={{ my: 2 }} />

      <OrgFilter
        expanded={expandedSections.has('organization')}
        onToggle={() => toggleSection('organization')}
        localFilters={localFilters}
        suggestions={suggestions}
        onOrgChange={(value) => setLocalFilters({ ...localFilters, organization: value || undefined })}
        onIndustryChange={(value) => setLocalFilters({ ...localFilters, industry: value || undefined })}
        onRegionChange={(value) => setLocalFilters({ ...localFilters, region: value || undefined })}
      />

      <StatusFilter
        showAdvanced={showAdvanced}
        localFilters={localFilters}
        selectedTags={selectedTags}
        onTagToggle={handleTagToggle}
        onFilterChange={(field, value) => setLocalFilters({ ...localFilters, [field]: value })}
      />

      {/* 인사이트 */}
      {showInsights && activeFilterCount > 0 && (
        <Fade in>
          <Alert severity="info" icon={<AutoIcon />} sx={{ mt: 2 }}>
            <Stack spacing={0.5}>
              {generateInsights().map((insight, index) => (
                <Typography key={index} variant="caption">• {insight}</Typography>
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
        <Box component="div" sx={{ mt: 2, p: 2, bgcolor: 'background.default', borderRadius: 1 }}>
          <Typography variant="subtitle2" gutterBottom>필터 프리셋 저장</Typography>
          <TextField
            size="small"
            label="프리셋 이름"
            value={customPresetName}
            onChange={(e) => setCustomPresetName(e.target.value)}
            fullWidth
            sx={{ mb: 2 }}
          />
          <Stack direction="row" spacing={1}>
            <Button size="small" onClick={() => setShowPresetDialog(false)} fullWidth>취소</Button>
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
        </Box>
      </Collapse>
    </FilterContainer>
  );
};

export default AdvancedFilters;
