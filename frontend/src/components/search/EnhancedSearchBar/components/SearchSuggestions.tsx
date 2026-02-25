/**
 * SearchSuggestions component
 * Renders the autocomplete dropdown with suggestion groups and trending searches
 */

import React from 'react';
import {
  Box, Paper, List, ListItemText, ListItemIcon, ListItemSecondaryAction,
  IconButton, CircularProgress, Chip, Fade, Popper, Typography, Badge, Avatar, alpha
} from '@mui/material';
import {
  Search as SearchIcon, TrendingUp as TrendingIcon, Gavel as BidIcon,
  Description as DocumentIcon, Business as CompanyIcon, ArrowForward as ArrowIcon
} from '@mui/icons-material';
import { styled, useTheme } from '@mui/material/styles';
import { EnhancedSuggestion } from '../types';
import RecentSearches from './RecentSearches';

const SuggestionPaper = styled(Paper)(({ theme }) => ({
  marginTop: theme.spacing(1),
  maxHeight: '500px',
  overflow: 'auto',
  borderRadius: theme.shape.borderRadius * 2,
  boxShadow: theme.shadows[8],
  border: `1px solid ${theme.palette.divider}`,
  '&::-webkit-scrollbar': { width: '8px' },
  '&::-webkit-scrollbar-track': { backgroundColor: theme.palette.background.default },
  '&::-webkit-scrollbar-thumb': {
    backgroundColor: theme.palette.action.disabled,
    borderRadius: '4px',
    '&:hover': { backgroundColor: theme.palette.action.active }
  }
}));

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
    borderLeftColor: theme.palette.primary.main
  }
}));

function getCategoryIcon(category?: string): React.ReactNode {
  if (category === 'bid') return <BidIcon color="primary" />;
  if (category === 'document') return <DocumentIcon color="action" />;
  if (category === 'company') return <CompanyIcon color="secondary" />;
  return <SearchIcon color="action" />;
}

interface SearchSuggestionsProps {
  suggestionsRef: React.RefObject<HTMLDivElement>;
  anchorEl: HTMLElement | null;
  showDropdown: boolean;
  suggestions: EnhancedSuggestion[];
  recentSearches: string[];
  trendingSearches: string[];
  loading: boolean;
  selectedIndex: number;
  query: string;
  onSearch: (text: string) => void;
  onRemoveRecent: (text: string) => void;
  onClearRecent: () => void;
}

const SearchSuggestions: React.FC<SearchSuggestionsProps> = ({
  suggestionsRef, anchorEl, showDropdown, suggestions, recentSearches,
  trendingSearches, loading, selectedIndex, query, onSearch, onRemoveRecent, onClearRecent
}) => {
  const theme = useTheme();
  let currentIndex = 0;

  const highlightMatch = (text: string, match: string) => {
    if (!match) return <>{text}</>;
    const parts = text.split(new RegExp(`(${match})`, 'gi'));
    return (
      <>
        {parts.map((part, i) =>
          part.toLowerCase() === match.toLowerCase() ? (
            <Box key={i} component="span" sx={{
              fontWeight: 700, color: 'primary.main',
              backgroundColor: alpha(theme.palette.primary.main, 0.1),
              padding: '0 2px', borderRadius: '2px'
            }}>{part}</Box>
          ) : part
        )}
      </>
    );
  };

  return (
    <Popper open={showDropdown} anchorEl={anchorEl} placement="bottom-start"
      style={{ width: anchorEl?.clientWidth, zIndex: 1300 }} transition>
      {({ TransitionProps }) => (
        <Fade {...TransitionProps} timeout={200}>
          <SuggestionPaper ref={suggestionsRef} elevation={8}>

            {suggestions.length > 0 && (
              <Box>
                <CategoryHeader>
                  <SearchIcon fontSize="small" />
                  <Typography variant="subtitle2" fontWeight={600}>검색 제안</Typography>
                  {loading && <CircularProgress size={16} sx={{ ml: 'auto' }} />}
                </CategoryHeader>
                <List dense disablePadding>
                  {suggestions.map((s) => {
                    const idx = currentIndex++;
                    return (
                      <SuggestionItem key={s.id} data-index={idx}
                        data-selected={selectedIndex === idx} onClick={() => onSearch(s.text)}>
                        <ListItemIcon sx={{ minWidth: 36 }}>{getCategoryIcon(s.category)}</ListItemIcon>
                        <ListItemText
                          primary={<Typography variant="body2" fontWeight={500}>{highlightMatch(s.text, query)}</Typography>}
                          secondary={s.category && <Chip label={s.category} size="small" sx={{ mt: 0.5, height: 20 }} />}
                        />
                        <ListItemSecondaryAction>
                          <IconButton size="small" edge="end"><ArrowIcon fontSize="small" /></IconButton>
                        </ListItemSecondaryAction>
                      </SuggestionItem>
                    );
                  })}
                </List>
              </Box>
            )}

            {!query && trendingSearches.length > 0 && (
              <Box>
                <CategoryHeader>
                  <TrendingIcon fontSize="small" color="error" />
                  <Typography variant="subtitle2" fontWeight={600}>인기 검색어</Typography>
                  <Badge badgeContent="실시간" color="error" sx={{ ml: 'auto' }} />
                </CategoryHeader>
                <List dense disablePadding>
                  {trendingSearches.slice(0, 5).map((text, i) => {
                    const idx = currentIndex++;
                    return (
                      <SuggestionItem key={`trending-${i}`} data-index={idx}
                        data-selected={selectedIndex === idx} onClick={() => onSearch(text)}>
                        <ListItemIcon sx={{ minWidth: 36 }}>
                          <Avatar sx={{ width: 24, height: 24, fontSize: '0.875rem', bgcolor: 'primary.main' }}>
                            {i + 1}
                          </Avatar>
                        </ListItemIcon>
                        <ListItemText primary={text} />
                        <Chip label={`${Math.floor(Math.random() * 100) + 20}건`} size="small" variant="outlined" />
                      </SuggestionItem>
                    );
                  })}
                </List>
              </Box>
            )}

            {recentSearches.length > 0 && (!query || suggestions.length === 0) && (
              <RecentSearches
                recentSearches={recentSearches}
                selectedIndex={selectedIndex}
                indexOffset={currentIndex}
                onSearch={onSearch}
                onRemove={onRemoveRecent}
                onClearAll={onClearRecent}
              />
            )}

          </SuggestionPaper>
        </Fade>
      )}
    </Popper>
  );
};

export default SearchSuggestions;
