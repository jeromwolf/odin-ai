/**
 * RecentSearches component
 * Renders the recent searches section within the suggestions dropdown
 */

import React from 'react';
import {
  Box,
  List,
  ListItemText,
  ListItemIcon,
  IconButton,
  Typography,
  alpha
} from '@mui/material';
import {
  History as HistoryIcon,
  Clear as ClearIcon,
  Close as CloseIcon
} from '@mui/icons-material';
import { styled } from '@mui/material/styles';

const CategoryHeader = styled(Box)(({ theme }) => ({
  padding: theme.spacing(1.5, 2),
  backgroundColor: alpha(theme.palette.primary.main, 0.04),
  borderBottom: `1px solid ${theme.palette.divider}`,
  display: 'flex',
  alignItems: 'center',
  gap: theme.spacing(1)
}));

const SuggestionItem = styled('div')(({ theme }) => ({
  padding: theme.spacing(1.5, 2),
  borderLeft: '3px solid transparent',
  transition: 'all 0.2s ease',
  display: 'flex',
  alignItems: 'center',
  cursor: 'pointer',
  '&:hover': {
    backgroundColor: alpha(theme.palette.primary.main, 0.08),
    borderLeftColor: theme.palette.primary.main,
    paddingLeft: theme.spacing(2.5)
  },
  '&[data-selected="true"]': {
    backgroundColor: alpha(theme.palette.primary.main, 0.12),
    borderLeftColor: theme.palette.primary.main,
    '&:hover': {
      backgroundColor: alpha(theme.palette.primary.main, 0.15)
    }
  }
}));

interface RecentSearchesProps {
  recentSearches: string[];
  selectedIndex: number;
  indexOffset: number;
  onSearch: (text: string) => void;
  onRemove: (text: string) => void;
  onClearAll: () => void;
}

const RecentSearches: React.FC<RecentSearchesProps> = ({
  recentSearches,
  selectedIndex,
  indexOffset,
  onSearch,
  onRemove,
  onClearAll
}) => {
  if (recentSearches.length === 0) return null;

  return (
    <Box>
      <CategoryHeader>
        <HistoryIcon fontSize="small" />
        <Typography variant="subtitle2" fontWeight={600}>
          최근 검색어
        </Typography>
        <IconButton size="small" sx={{ ml: 'auto' }} onClick={onClearAll}>
          <ClearIcon fontSize="small" />
        </IconButton>
      </CategoryHeader>
      <List dense disablePadding>
        {recentSearches.slice(0, 5).map((text, index) => {
          const dataIndex = indexOffset + index;
          return (
            <SuggestionItem
              key={`recent-${index}`}
              data-index={dataIndex}
              data-selected={selectedIndex === dataIndex}
              onClick={() => onSearch(text)}
            >
              <ListItemIcon sx={{ minWidth: 36 }}>
                <HistoryIcon fontSize="small" color="action" />
              </ListItemIcon>
              <ListItemText
                primary={text}
                secondary={
                  <Typography variant="caption" color="text.secondary">
                    최근 검색
                  </Typography>
                }
              />
              <IconButton
                size="small"
                edge="end"
                onClick={(e) => {
                  e.stopPropagation();
                  onRemove(text);
                }}
              >
                <CloseIcon fontSize="small" />
              </IconButton>
            </SuggestionItem>
          );
        })}
      </List>
    </Box>
  );
};

export default RecentSearches;
