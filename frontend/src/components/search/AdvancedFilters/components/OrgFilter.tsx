/**
 * OrgFilter - 기관 및 분야 필터 컴포넌트
 */

import React from 'react';
import {
  Typography,
  TextField,
  Stack,
  Collapse,
  IconButton,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Autocomplete
} from '@mui/material';
import {
  Business as OrgIcon,
  ExpandMore as ExpandIcon,
  ExpandLess as CollapseIcon
} from '@mui/icons-material';
import { FilterSection, SectionHeader, SearchFilters } from '../types';

interface OrgFilterProps {
  expanded: boolean;
  onToggle: () => void;
  localFilters: SearchFilters;
  suggestions: {
    organizations?: string[];
  };
  onOrgChange: (value: string | null) => void;
  onIndustryChange: (value: string) => void;
  onRegionChange: (value: string) => void;
}

const OrgFilter: React.FC<OrgFilterProps> = ({
  expanded,
  onToggle,
  localFilters,
  suggestions,
  onOrgChange,
  onIndustryChange,
  onRegionChange
}) => {
  return (
    <FilterSection>
      <SectionHeader onClick={onToggle}>
        <OrgIcon color="action" />
        <Typography variant="subtitle2" className="section-title">
          기관 및 분야
        </Typography>
        <IconButton size="small" sx={{ ml: 'auto' }}>
          {expanded ? <CollapseIcon /> : <ExpandIcon />}
        </IconButton>
      </SectionHeader>

      <Collapse in={expanded}>
        <Stack spacing={2}>
          <Autocomplete
            size="small"
            options={suggestions.organizations || []}
            value={localFilters.organization || null}
            onChange={(_, value) => onOrgChange(value)}
            renderInput={(params) => (
              <TextField {...params} label="발주기관" placeholder="기관 선택 또는 입력" />
            )}
            freeSolo
          />

          <FormControl size="small" fullWidth>
            <InputLabel>산업 분야</InputLabel>
            <Select
              value={localFilters.industry || ''}
              onChange={(e) => onIndustryChange(e.target.value)}
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
            onChange={(e) => onRegionChange(e.target.value)}
            placeholder="예: 서울, 경기"
            fullWidth
          />
        </Stack>
      </Collapse>
    </FilterSection>
  );
};

export default OrgFilter;
