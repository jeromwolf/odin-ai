/**
 * EnhancedSearchBar 컴포넌트
 * 고급 자동완성 기능과 개선된 UX를 제공하는 검색바
 */

import React, { useState, useEffect, useRef, useCallback, useMemo } from 'react';
import {
  TextField,
  InputAdornment,
  IconButton,
  Paper,
  List,
  ListItem,
  ListItemButton,
  ListItemText,
  ListItemIcon,
  ListItemSecondaryAction,
  Box,
  CircularProgress,
  Chip,
  Fade,
  Popper,
  Typography,
  Divider,
  Avatar,
  Tooltip,
  Badge,
  Stack,
  useTheme,
  alpha
} from '@mui/material';
import {
  Search as SearchIcon,
  Clear as ClearIcon,
  History as HistoryIcon,
  TrendingUp as TrendingIcon,
  Gavel as BidIcon,
  Description as DocumentIcon,
  Business as CompanyIcon,
  ArrowForward as ArrowIcon,
  AutoAwesome as AiIcon,
  QueryStats as StatsIcon,
  Close as CloseIcon
} from '@mui/icons-material';
import { styled, keyframes } from '@mui/material/styles';
import { useDebounce } from '../../hooks/useDebounce';
import { SearchBarProps, SuggestResponse } from '../../types/search.types';
import { getSuggestions } from '../../services/searchService';

// 애니메이션
const pulse = keyframes`
  0% {
    box-shadow: 0 0 0 0 rgba(25, 118, 210, 0.4);
  }
  70% {
    box-shadow: 0 0 0 10px rgba(25, 118, 210, 0);
  }
  100% {
    box-shadow: 0 0 0 0 rgba(25, 118, 210, 0);
  }
`;

// 스타일 컴포넌트
const SearchContainer = styled(Box)(({ theme }) => ({
  position: 'relative',
  width: '100%',
  maxWidth: '800px',
  margin: '0 auto'
}));

const StyledTextField = styled(TextField)(({ theme }) => ({
  '& .MuiOutlinedInput-root': {
    borderRadius: theme.shape.borderRadius * 3,
    backgroundColor: theme.palette.background.paper,
    transition: 'all 0.3s ease',
    '&:hover': {
      backgroundColor: alpha(theme.palette.primary.main, 0.02),
      '& fieldset': {
        borderColor: theme.palette.primary.main,
        borderWidth: 2
      }
    },
    '&.Mui-focused': {
      backgroundColor: theme.palette.background.paper,
      boxShadow: `0 0 0 4px ${alpha(theme.palette.primary.main, 0.1)}`,
      animation: `${pulse} 2s infinite`,
      '& fieldset': {
        borderColor: theme.palette.primary.main,
        borderWidth: 2
      }
    }
  },
  '& .MuiInputBase-input': {
    fontSize: '1.1rem',
    fontWeight: 500,
    '&::placeholder': {
      opacity: 0.6
    }
  }
}));

const SuggestionPaper = styled(Paper)(({ theme }) => ({
  marginTop: theme.spacing(1),
  maxHeight: '500px',
  overflow: 'auto',
  borderRadius: theme.shape.borderRadius * 2,
  boxShadow: theme.shadows[8],
  border: `1px solid ${theme.palette.divider}`,
  '&::-webkit-scrollbar': {
    width: '8px'
  },
  '&::-webkit-scrollbar-track': {
    backgroundColor: theme.palette.background.default
  },
  '&::-webkit-scrollbar-thumb': {
    backgroundColor: theme.palette.action.disabled,
    borderRadius: '4px',
    '&:hover': {
      backgroundColor: theme.palette.action.active
    }
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

const SuggestionItem = styled(ListItemButton)(({ theme }) => ({
  padding: theme.spacing(1.5, 2),
  borderLeft: '3px solid transparent',
  transition: 'all 0.2s ease',
  '&:hover': {
    backgroundColor: alpha(theme.palette.primary.main, 0.08),
    borderLeftColor: theme.palette.primary.main,
    paddingLeft: theme.spacing(2.5)
  },
  '&.Mui-selected': {
    backgroundColor: alpha(theme.palette.primary.main, 0.12),
    borderLeftColor: theme.palette.primary.main,
    '&:hover': {
      backgroundColor: alpha(theme.palette.primary.main, 0.15)
    }
  }
}));

const QuickAction = styled(Chip)(({ theme }) => ({
  margin: theme.spacing(0.5),
  fontWeight: 600,
  '&:hover': {
    backgroundColor: theme.palette.primary.main,
    color: theme.palette.primary.contrastText,
    transform: 'scale(1.05)'
  }
}));

// 제안 타입
interface EnhancedSuggestion {
  id: string;
  text: string;
  type: 'history' | 'suggestion' | 'trending' | 'command';
  category?: 'bid' | 'document' | 'company';
  count?: number;
  metadata?: {
    lastSearched?: Date;
    popularity?: number;
    icon?: React.ReactNode;
  };
}

// Props 인터페이스 확장
interface EnhancedSearchBarProps extends SearchBarProps {
  showQuickActions?: boolean;
  showSearchStats?: boolean;
  enableAiSuggestions?: boolean;
  onCategorySelect?: (category: string) => void;
}

const EnhancedSearchBar: React.FC<EnhancedSearchBarProps> = ({
  onSearch,
  initialQuery = '',
  placeholder = '무엇을 찾고 계신가요?',
  showSuggestions = true,
  showQuickActions = true,
  showSearchStats = true,
  enableAiSuggestions = false,
  onCategorySelect
}) => {
  const theme = useTheme();
  const [query, setQuery] = useState<string>(initialQuery);
  const [suggestions, setSuggestions] = useState<EnhancedSuggestion[]>([]);
  const [recentSearches, setRecentSearches] = useState<string[]>([]);
  const [trendingSearches, setTrendingSearches] = useState<string[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const [selectedIndex, setSelectedIndex] = useState<number>(-1);
  const [anchorEl, setAnchorEl] = useState<HTMLElement | null>(null);
  const [searchStats, setSearchStats] = useState<{ total: number; recent: number } | null>(null);

  const inputRef = useRef<HTMLInputElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const suggestionsRef = useRef<HTMLDivElement>(null);

  const debouncedQuery = useDebounce(query, 300);
  const showDropdown = Boolean(anchorEl) && (suggestions.length > 0 || recentSearches.length > 0);

  /**
   * 초기화
   */
  useEffect(() => {
    // 최근 검색어 로드
    const saved = localStorage.getItem('recentSearches');
    if (saved) {
      try {
        setRecentSearches(JSON.parse(saved));
      } catch (error) {
        console.error('Failed to load recent searches:', error);
      }
    }

    // 인기 검색어 로드 (실제로는 API에서)
    setTrendingSearches(['건설 공사', '소프트웨어 개발', 'SI 구축', '의료 장비', '시설 관리']);

    // 검색 통계 로드 (실제로는 API에서)
    if (showSearchStats) {
      setSearchStats({ total: 15234, recent: 523 });
    }
  }, [showSearchStats]);

  /**
   * 자동완성 제안 가져오기
   */
  useEffect(() => {
    if (!showSuggestions || !debouncedQuery || debouncedQuery.length < 2) {
      setSuggestions([]);
      return;
    }

    let cancelled = false;

    const fetchSuggestions = async () => {
      setLoading(true);
      try {
        const response: SuggestResponse = await getSuggestions(debouncedQuery);

        if (!cancelled) {
          // 제안을 카테고리별로 구성
          const enhancedSuggestions: EnhancedSuggestion[] = response.suggestions.map(
            (text, index) => ({
              id: `suggestion-${index}`,
              text,
              type: 'suggestion',
              category: detectCategory(text),
              metadata: {
                icon: getCategoryIcon(detectCategory(text))
              }
            })
          );

          // AI 제안 추가 (활성화된 경우)
          if (enableAiSuggestions) {
            enhancedSuggestions.push({
              id: 'ai-suggestion',
              text: `"${debouncedQuery}"와 관련된 모든 결과 보기`,
              type: 'command',
              metadata: {
                icon: <AiIcon color="primary" />
              }
            });
          }

          setSuggestions(enhancedSuggestions);
        }
      } catch (error) {
        console.error('Failed to fetch suggestions:', error);
        if (!cancelled) {
          setSuggestions([]);
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    };

    fetchSuggestions();

    return () => {
      cancelled = true;
    };
  }, [debouncedQuery, showSuggestions, enableAiSuggestions]);

  /**
   * 카테고리 감지
   */
  const detectCategory = (text: string): 'bid' | 'document' | 'company' | undefined => {
    const lowerText = text.toLowerCase();
    if (lowerText.includes('공고') || lowerText.includes('입찰')) return 'bid';
    if (lowerText.includes('문서') || lowerText.includes('파일')) return 'document';
    if (lowerText.includes('기업') || lowerText.includes('회사')) return 'company';
    return undefined;
  };

  /**
   * 카테고리 아이콘 가져오기
   */
  const getCategoryIcon = (category?: string): React.ReactNode => {
    switch (category) {
      case 'bid':
        return <BidIcon color="primary" />;
      case 'document':
        return <DocumentIcon color="action" />;
      case 'company':
        return <CompanyIcon color="secondary" />;
      default:
        return <SearchIcon color="action" />;
    }
  };

  /**
   * 검색 실행
   */
  const handleSearch = useCallback(
    (searchQuery?: string) => {
      const finalQuery = searchQuery || query;
      if (!finalQuery.trim()) return;

      onSearch(finalQuery);

      // 최근 검색어에 추가
      const newRecentSearches = [
        finalQuery,
        ...recentSearches.filter(item => item !== finalQuery)
      ].slice(0, 10);

      setRecentSearches(newRecentSearches);
      localStorage.setItem('recentSearches', JSON.stringify(newRecentSearches));

      // 드롭다운 닫기
      setAnchorEl(null);
      setSelectedIndex(-1);

      // 검색 애니메이션
      if (inputRef.current) {
        inputRef.current.blur();
      }
    },
    [query, onSearch, recentSearches]
  );

  /**
   * 키보드 네비게이션
   */
  const handleKeyDown = (event: React.KeyboardEvent) => {
    const allItems = [...suggestions, ...recentSearches.map((text, i) => ({
      id: `recent-${i}`,
      text,
      type: 'history' as const
    }))];

    switch (event.key) {
      case 'Enter':
        event.preventDefault();
        if (selectedIndex >= 0 && selectedIndex < allItems.length) {
          handleSearch(allItems[selectedIndex].text);
        } else {
          handleSearch();
        }
        break;

      case 'ArrowDown':
        event.preventDefault();
        setSelectedIndex(prev => Math.min(prev + 1, allItems.length - 1));
        scrollToSelected();
        break;

      case 'ArrowUp':
        event.preventDefault();
        setSelectedIndex(prev => Math.max(prev - 1, -1));
        scrollToSelected();
        break;

      case 'Escape':
        setAnchorEl(null);
        setSelectedIndex(-1);
        inputRef.current?.blur();
        break;

      case 'Tab':
        // Tab으로 자동완성 수락
        if (selectedIndex >= 0 && allItems[selectedIndex]) {
          event.preventDefault();
          setQuery(allItems[selectedIndex].text);
        }
        break;
    }
  };

  /**
   * 선택된 항목으로 스크롤
   */
  const scrollToSelected = useCallback(() => {
    if (suggestionsRef.current && selectedIndex >= 0) {
      const selectedElement = suggestionsRef.current.querySelector(
        `[data-index="${selectedIndex}"]`
      );
      selectedElement?.scrollIntoView({ block: 'nearest', behavior: 'smooth' });
    }
  }, [selectedIndex]);

  /**
   * 제안 그룹 렌더링
   */
  const renderSuggestionGroups = () => {
    const groups: JSX.Element[] = [];
    let currentIndex = 0;

    // 검색 제안
    if (suggestions.length > 0) {
      groups.push(
        <Box key="suggestions">
          <CategoryHeader>
            <SearchIcon fontSize="small" />
            <Typography variant="subtitle2" fontWeight={600}>
              검색 제안
            </Typography>
            {loading && <CircularProgress size={16} sx={{ ml: 'auto' }} />}
          </CategoryHeader>
          <List dense>
            {suggestions.map((suggestion, index) => (
              <SuggestionItem
                key={suggestion.id}
                data-index={currentIndex++}
                selected={selectedIndex === currentIndex - 1}
                onClick={() => handleSearch(suggestion.text)}
              >
                <ListItemIcon sx={{ minWidth: 36 }}>
                  {suggestion.metadata?.icon || <SearchIcon />}
                </ListItemIcon>
                <ListItemText
                  primary={
                    <Typography variant="body2" fontWeight={500}>
                      {highlightMatch(suggestion.text, query)}
                    </Typography>
                  }
                  secondary={suggestion.category && (
                    <Chip
                      label={suggestion.category}
                      size="small"
                      sx={{ mt: 0.5, height: 20 }}
                    />
                  )}
                />
                <ListItemSecondaryAction>
                  <IconButton size="small" edge="end">
                    <ArrowIcon fontSize="small" />
                  </IconButton>
                </ListItemSecondaryAction>
              </SuggestionItem>
            ))}
          </List>
        </Box>
      );
    }

    // 인기 검색어 (검색어가 없을 때)
    if (!query && trendingSearches.length > 0) {
      groups.push(
        <Box key="trending">
          <CategoryHeader>
            <TrendingIcon fontSize="small" color="error" />
            <Typography variant="subtitle2" fontWeight={600}>
              인기 검색어
            </Typography>
            <Badge badgeContent="실시간" color="error" sx={{ ml: 'auto' }} />
          </CategoryHeader>
          <List dense>
            {trendingSearches.slice(0, 5).map((text, index) => (
              <SuggestionItem
                key={`trending-${index}`}
                data-index={currentIndex++}
                selected={selectedIndex === currentIndex - 1}
                onClick={() => handleSearch(text)}
              >
                <ListItemIcon sx={{ minWidth: 36 }}>
                  <Avatar
                    sx={{
                      width: 24,
                      height: 24,
                      fontSize: '0.875rem',
                      bgcolor: 'primary.main'
                    }}
                  >
                    {index + 1}
                  </Avatar>
                </ListItemIcon>
                <ListItemText primary={text} />
                <Chip
                  label={`${Math.floor(Math.random() * 100) + 20}건`}
                  size="small"
                  variant="outlined"
                />
              </SuggestionItem>
            ))}
          </List>
        </Box>
      );
    }

    // 최근 검색어
    if (recentSearches.length > 0 && (!query || suggestions.length === 0)) {
      groups.push(
        <Box key="recent">
          <CategoryHeader>
            <HistoryIcon fontSize="small" />
            <Typography variant="subtitle2" fontWeight={600}>
              최근 검색어
            </Typography>
            <IconButton
              size="small"
              sx={{ ml: 'auto' }}
              onClick={() => {
                setRecentSearches([]);
                localStorage.removeItem('recentSearches');
              }}
            >
              <ClearIcon fontSize="small" />
            </IconButton>
          </CategoryHeader>
          <List dense>
            {recentSearches.slice(0, 5).map((text, index) => (
              <SuggestionItem
                key={`recent-${index}`}
                data-index={currentIndex++}
                selected={selectedIndex === currentIndex - 1}
                onClick={() => handleSearch(text)}
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
                    const newRecentSearches = recentSearches.filter(s => s !== text);
                    setRecentSearches(newRecentSearches);
                    localStorage.setItem('recentSearches', JSON.stringify(newRecentSearches));
                  }}
                >
                  <CloseIcon fontSize="small" />
                </IconButton>
              </SuggestionItem>
            ))}
          </List>
        </Box>
      );
    }

    return groups;
  };

  /**
   * 매칭 텍스트 하이라이트
   */
  const highlightMatch = (text: string, match: string) => {
    if (!match) return text;

    const parts = text.split(new RegExp(`(${match})`, 'gi'));
    return (
      <>
        {parts.map((part, i) =>
          part.toLowerCase() === match.toLowerCase() ? (
            <Box
              key={i}
              component="span"
              sx={{
                fontWeight: 700,
                color: 'primary.main',
                backgroundColor: alpha(theme.palette.primary.main, 0.1),
                padding: '0 2px',
                borderRadius: '2px'
              }}
            >
              {part}
            </Box>
          ) : (
            part
          )
        )}
      </>
    );
  };

  return (
    <SearchContainer ref={containerRef}>
      {/* 검색 통계 */}
      {showSearchStats && searchStats && (
        <Fade in>
          <Stack direction="row" spacing={2} justifyContent="center" sx={{ mb: 2 }}>
            <Chip
              icon={<StatsIcon />}
              label={`오늘 ${searchStats.recent.toLocaleString()}건`}
              size="small"
              color="primary"
              variant="outlined"
            />
            <Chip
              label={`전체 ${searchStats.total.toLocaleString()}건 검색 가능`}
              size="small"
              variant="outlined"
            />
          </Stack>
        </Fade>
      )}

      {/* 검색 입력 */}
      <StyledTextField
        ref={inputRef}
        fullWidth
        variant="outlined"
        placeholder={placeholder}
        value={query}
        onChange={(e) => {
          setQuery(e.target.value);
          if (!anchorEl) {
            setAnchorEl(e.currentTarget);
          }
        }}
        onFocus={(e) => {
          setAnchorEl(e.currentTarget);
        }}
        onKeyDown={handleKeyDown}
        InputProps={{
          startAdornment: (
            <InputAdornment position="start">
              <SearchIcon color="action" />
            </InputAdornment>
          ),
          endAdornment: (
            <InputAdornment position="end">
              <Stack direction="row" spacing={0.5} alignItems="center">
                {loading && <CircularProgress size={20} />}
                {query && !loading && (
                  <Tooltip title="지우기">
                    <IconButton
                      size="small"
                      onClick={() => {
                        setQuery('');
                        inputRef.current?.focus();
                      }}
                    >
                      <ClearIcon />
                    </IconButton>
                  </Tooltip>
                )}
                <Tooltip title="검색">
                  <IconButton
                    onClick={() => handleSearch()}
                    color="primary"
                    disabled={!query.trim()}
                    sx={{
                      bgcolor: query ? 'primary.main' : 'transparent',
                      color: query ? 'primary.contrastText' : 'action.active',
                      '&:hover': {
                        bgcolor: query ? 'primary.dark' : 'action.hover'
                      }
                    }}
                  >
                    <SearchIcon />
                  </IconButton>
                </Tooltip>
              </Stack>
            </InputAdornment>
          )
        }}
      />

      {/* 빠른 액션 */}
      {showQuickActions && !query && (
        <Fade in>
          <Stack
            direction="row"
            spacing={1}
            justifyContent="center"
            flexWrap="wrap"
            sx={{ mt: 2, gap: 0.5 }}
          >
            <QuickAction
              icon={<BidIcon />}
              label="입찰공고"
              onClick={() => {
                onCategorySelect?.('bid');
                handleSearch('입찰공고');
              }}
              clickable
            />
            <QuickAction
              icon={<DocumentIcon />}
              label="문서검색"
              onClick={() => {
                onCategorySelect?.('document');
                handleSearch('문서');
              }}
              clickable
            />
            <QuickAction
              icon={<CompanyIcon />}
              label="기업정보"
              onClick={() => {
                onCategorySelect?.('company');
                handleSearch('기업');
              }}
              clickable
            />
            {enableAiSuggestions && (
              <QuickAction
                icon={<AiIcon />}
                label="AI 검색"
                color="secondary"
                onClick={() => {
                  // AI 검색 모드 활성화
                }}
                clickable
              />
            )}
          </Stack>
        </Fade>
      )}

      {/* 드롭다운 제안 */}
      <Popper
        open={showDropdown}
        anchorEl={anchorEl}
        placement="bottom-start"
        style={{ width: anchorEl?.clientWidth, zIndex: 1300 }}
        transition
      >
        {({ TransitionProps }) => (
          <Fade {...TransitionProps} timeout={200}>
            <SuggestionPaper ref={suggestionsRef} elevation={8}>
              {renderSuggestionGroups()}
            </SuggestionPaper>
          </Fade>
        )}
      </Popper>
    </SearchContainer>
  );
};

export default EnhancedSearchBar;