/**
 * PriceFilter - 가격 범위 필터 컴포넌트
 */

import React from 'react';
import { Box, Typography, TextField, Stack, Collapse, IconButton } from '@mui/material';
import {
  AttachMoney as MoneyIcon,
  ExpandMore as ExpandIcon,
  ExpandLess as CollapseIcon
} from '@mui/icons-material';
import { FilterSection, SectionHeader, StyledSlider, PRICE_MARKS } from '../types';

interface PriceFilterProps {
  expanded: boolean;
  onToggle: () => void;
  priceRange: [number, number];
  onPriceChange: (event: Event, newValue: number | number[]) => void;
  onPriceCommit: () => void;
  onMinChange: (value: number) => void;
  onMaxChange: (value: number) => void;
  formatPrice: (value: number) => string;
}

const PriceFilter: React.FC<PriceFilterProps> = ({
  expanded,
  onToggle,
  priceRange,
  onPriceChange,
  onPriceCommit,
  onMinChange,
  onMaxChange,
  formatPrice
}) => {
  return (
    <FilterSection>
      <SectionHeader onClick={onToggle}>
        <MoneyIcon color="action" />
        <Typography variant="subtitle2" className="section-title">
          가격 범위
        </Typography>
        <Typography variant="caption" color="text.secondary" sx={{ ml: 'auto' }}>
          {formatPrice(priceRange[0])} ~ {formatPrice(priceRange[1])}
        </Typography>
        <IconButton size="small">
          {expanded ? <CollapseIcon /> : <ExpandIcon />}
        </IconButton>
      </SectionHeader>

      <Collapse in={expanded}>
        <Box sx={{ px: 2 }}>
          <StyledSlider
            value={priceRange}
            onChange={onPriceChange}
            onChangeCommitted={onPriceCommit}
            valueLabelDisplay="auto"
            valueLabelFormat={formatPrice}
            min={0}
            max={1000000000}
            marks={PRICE_MARKS}
            sx={{ mt: 4, mb: 2 }}
          />
          <Stack direction="row" spacing={2}>
            <TextField
              size="small"
              label="최소"
              value={priceRange[0]}
              onChange={(e) => onMinChange(Number(e.target.value))}
              type="number"
              fullWidth
            />
            <TextField
              size="small"
              label="최대"
              value={priceRange[1]}
              onChange={(e) => onMaxChange(Number(e.target.value))}
              type="number"
              fullWidth
            />
          </Stack>
        </Box>
      </Collapse>
    </FilterSection>
  );
};

export default PriceFilter;
