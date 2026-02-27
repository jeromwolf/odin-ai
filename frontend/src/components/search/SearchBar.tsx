/**
 * SearchBar 컴포넌트
 * 검색 입력 필드와 자동완성 기능을 제공
 */

import React, { useState, useEffect, useRef, useCallback } from 'react';
import {
  TextField,
  InputAdornment,
  IconButton,
  Paper,
  List,
  ListItem,
  ListItemButton,
  ListItemText,
  Box,
  CircularProgress,
  Fade
} from '@mui/material';
import {
  Search as SearchIcon,
  Clear as ClearIcon,
  History as HistoryIcon
} from '@mui/icons-material';
import { styled } from '@mui/material/styles';
import { useDebounce } from '../../hooks/useDebounce';
import { SearchBarProps, SuggestResponse } from '../../types/search.types';
import { getSuggestions } from '../../services/searchService';

// 스타일 컴포넌트
const SearchContainer = styled(Box)(({ theme }) => ({
  position: 'relative',
  width: '100%',
  maxWidth: '600px'
}));

const SuggestionPaper = styled(Paper)(({ theme }) => ({
  position: 'absolute',
  top: '100%',
  left: 0,
  right: 0,
  marginTop: theme.spacing(0.5),
  maxHeight: '400px',
  overflow: 'auto',
  zIndex: 1000,
  boxShadow: theme.shadows[4]
}));

const RecentSearchHeader = styled(Box)(({ theme }) => ({
  padding: theme.spacing(1, 2),
  borderBottom: `1px solid ${theme.palette.divider}`,
  color: theme.palette.text.secondary,
  fontSize: '0.875rem',
  fontWeight: 500
}));

const SearchBar: React.FC<SearchBarProps> = ({
  onSearch,
  initialQuery = '',
  placeholder = '검색어를 입력하세요',
  showSuggestions = true
}) => {
  // 상태 관리
  const [query, setQuery] = useState<string>(initialQuery);
  const [suggestions, setSuggestions] = useState<string[]>([]);
  const [recentSearches, setRecentSearches] = useState<string[]>([]);
  const [showDropdown, setShowDropdown] = useState<boolean>(false);
  const [loading, setLoading] = useState<boolean>(false);
  const [selectedIndex, setSelectedIndex] = useState<number>(-1);

  // Refs
  const inputRef = useRef<HTMLInputElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  // 디바운스된 검색어
  const debouncedQuery = useDebounce(query, 300);

  /**
   * 최근 검색어 로드
   */
  useEffect(() => {
    const saved = localStorage.getItem('recentSearches');
    if (saved) {
      try {
        setRecentSearches(JSON.parse(saved));
      } catch (error) {
        console.error('Failed to load recent searches:', error);
      }
    }
  }, []);

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
          setSuggestions(response.suggestions);
          setShowDropdown(response.suggestions.length > 0 || recentSearches.length > 0);
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
  }, [debouncedQuery, showSuggestions, recentSearches.length]);

  /**
   * 외부 클릭 감지하여 드롭다운 닫기
   */
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
        setShowDropdown(false);
        setSelectedIndex(-1);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, []);

  /**
   * 검색 실행
   */
  const handleSearch = useCallback((searchQuery?: string) => {
    const finalQuery = searchQuery || query;
    if (!finalQuery.trim()) return;

    // 검색 실행
    onSearch(finalQuery);

    // 최근 검색어에 추가
    const newRecentSearches = [
      finalQuery,
      ...recentSearches.filter(item => item !== finalQuery)
    ].slice(0, 5); // 최대 5개 저장

    setRecentSearches(newRecentSearches);
    localStorage.setItem('recentSearches', JSON.stringify(newRecentSearches));

    // 드롭다운 닫기
    setShowDropdown(false);
    setSelectedIndex(-1);
  }, [query, onSearch, recentSearches]);

  /**
   * 입력 값 변경 처리
   */
  const handleInputChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const value = event.target.value;
    setQuery(value);

    if (value.trim() || recentSearches.length > 0) {
      setShowDropdown(true);
    } else {
      setShowDropdown(false);
    }

    setSelectedIndex(-1);
  };

  /**
   * 키보드 이벤트 처리
   */
  const handleKeyDown = (event: React.KeyboardEvent) => {
    const allItems = [...suggestions, ...recentSearches];

    switch (event.key) {
      case 'Enter':
        event.preventDefault();
        if (selectedIndex >= 0 && selectedIndex < allItems.length) {
          handleSearch(allItems[selectedIndex]);
        } else {
          handleSearch();
        }
        break;

      case 'ArrowDown':
        event.preventDefault();
        setSelectedIndex(prev =>
          prev < allItems.length - 1 ? prev + 1 : prev
        );
        break;

      case 'ArrowUp':
        event.preventDefault();
        setSelectedIndex(prev => prev > -1 ? prev - 1 : -1);
        break;

      case 'Escape':
        setShowDropdown(false);
        setSelectedIndex(-1);
        inputRef.current?.blur();
        break;
    }
  };

  /**
   * 검색어 클리어
   */
  const handleClear = () => {
    setQuery('');
    setSuggestions([]);
    setShowDropdown(false);
    setSelectedIndex(-1);
    inputRef.current?.focus();
  };

  /**
   * 최근 검색어 삭제
   */
  const handleRemoveRecentSearch = (item: string, event: React.MouseEvent) => {
    event.stopPropagation();
    const newRecentSearches = recentSearches.filter(search => search !== item);
    setRecentSearches(newRecentSearches);
    localStorage.setItem('recentSearches', JSON.stringify(newRecentSearches));
  };

  /**
   * 드롭다운 아이템 렌더링
   */
  const renderDropdownItems = () => {
    const items = [];

    // 자동완성 제안
    if (suggestions.length > 0) {
      items.push(
        <Box key="suggestions">
          {suggestions.map((suggestion, index) => (
            <ListItem key={`suggestion-${index}`} disablePadding>
              <ListItemButton
                selected={selectedIndex === index}
                onClick={() => handleSearch(suggestion)}
                sx={{ py: 1 }}
              >
                <SearchIcon sx={{ mr: 2, color: 'text.secondary' }} fontSize="small" />
                <ListItemText
                  primary={suggestion}
                  primaryTypographyProps={{
                    sx: {
                      fontWeight: selectedIndex === index ? 600 : 400
                    }
                  }}
                />
              </ListItemButton>
            </ListItem>
          ))}
        </Box>
      );
    }

    // 최근 검색어 (제안이 없거나 검색어가 비어있을 때)
    if (recentSearches.length > 0 && (!query || suggestions.length === 0)) {
      const offset = suggestions.length;

      items.push(
        <Box key="recent">
          <RecentSearchHeader>최근 검색어</RecentSearchHeader>
          {recentSearches.map((item, index) => (
            <ListItem
              key={`recent-${index}`}
              disablePadding
              secondaryAction={
                <IconButton
                  edge="end"
                  size="small"
                  onClick={(e) => handleRemoveRecentSearch(item, e)}
                >
                  <ClearIcon fontSize="small" />
                </IconButton>
              }
            >
              <ListItemButton
                selected={selectedIndex === offset + index}
                onClick={() => handleSearch(item)}
                sx={{ py: 1 }}
              >
                <HistoryIcon sx={{ mr: 2, color: 'text.secondary' }} fontSize="small" />
                <ListItemText primary={item} />
              </ListItemButton>
            </ListItem>
          ))}
        </Box>
      );
    }

    return items;
  };

  return (
    <SearchContainer ref={containerRef}>
      <TextField
        ref={inputRef}
        fullWidth
        variant="outlined"
        placeholder={placeholder}
        value={query}
        onChange={handleInputChange}
        onKeyDown={handleKeyDown}
        onFocus={() => {
          if (query || recentSearches.length > 0) {
            setShowDropdown(true);
          }
        }}
        InputProps={{
          startAdornment: (
            <InputAdornment position="start">
              <SearchIcon color="action" />
            </InputAdornment>
          ),
          endAdornment: (
            <InputAdornment position="end">
              {loading && (
                <CircularProgress size={20} sx={{ mr: 1 }} />
              )}
              {query && !loading && (
                <IconButton
                  size="small"
                  onClick={handleClear}
                  edge="end"
                  sx={{ mr: 0.5 }}
                >
                  <ClearIcon />
                </IconButton>
              )}
              <IconButton
                onClick={() => handleSearch()}
                edge="end"
                color="primary"
                disabled={!query.trim()}
              >
                <SearchIcon />
              </IconButton>
            </InputAdornment>
          )
        }}
        sx={{
          '& .MuiOutlinedInput-root': {
            '&:hover fieldset': {
              borderColor: 'primary.main'
            },
            '&.Mui-focused fieldset': {
              borderColor: 'primary.main'
            }
          }
        }}
      />

      {/* 드롭다운 */}
      <Fade in={showDropdown && (suggestions.length > 0 || recentSearches.length > 0)}>
        <SuggestionPaper elevation={3}>
          <List dense>
            {renderDropdownItems()}
          </List>
        </SuggestionPaper>
      </Fade>
    </SearchContainer>
  );
};

export default SearchBar;