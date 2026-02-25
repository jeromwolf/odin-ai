/**
 * StatusFilter - 태그 및 추가 옵션 필터 컴포넌트 (고급 옵션)
 */

import React from 'react';
import { Typography, Stack, FormControlLabel, Switch, Collapse, Box } from '@mui/material';
import { LocalOffer as TagIcon } from '@mui/icons-material';
import { FilterSection, TagChip, SearchFilters, AVAILABLE_TAGS } from '../types';

interface StatusFilterProps {
  showAdvanced: boolean;
  localFilters: SearchFilters;
  selectedTags: string[];
  onTagToggle: (tag: string) => void;
  onFilterChange: (field: keyof SearchFilters, value: boolean) => void;
}

const StatusFilter: React.FC<StatusFilterProps> = ({
  showAdvanced,
  localFilters,
  selectedTags,
  onTagToggle,
  onFilterChange
}) => {
  return (
    <Collapse in={showAdvanced}>
      <FilterSection>
        <Typography
          variant="subtitle2"
          gutterBottom
          sx={{ display: 'flex', alignItems: 'center', gap: 1 }}
        >
          <TagIcon />
          태그 필터
        </Typography>
        <Box sx={{ display: 'flex', flexWrap: 'wrap' }}>
          {AVAILABLE_TAGS.map(tag => (
            <TagChip
              key={tag}
              label={tag}
              className={selectedTags.includes(tag) ? 'selected' : ''}
              onClick={() => onTagToggle(tag)}
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
                onChange={(e) => onFilterChange('excludeClosed', e.target.checked)}
              />
            }
            label="마감된 공고 제외"
          />
          <FormControlLabel
            control={
              <Switch
                checked={localFilters.onlyUrgent || false}
                onChange={(e) => onFilterChange('onlyUrgent', e.target.checked)}
              />
            }
            label="긴급 공고만"
          />
          <FormControlLabel
            control={
              <Switch
                checked={localFilters.hasAttachments || false}
                onChange={(e) => onFilterChange('hasAttachments', e.target.checked)}
              />
            }
            label="첨부파일 있는 공고만"
          />
        </Stack>
      </FilterSection>
    </Collapse>
  );
};

export default StatusFilter;
