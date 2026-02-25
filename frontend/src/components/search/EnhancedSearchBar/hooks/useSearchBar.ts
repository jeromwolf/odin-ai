/**
 * useSearchBar Hook
 * All state management and handlers for EnhancedSearchBar
 */

import { useState, useEffect, useRef, useCallback } from 'react';
import { AutoAwesome as AiIcon } from '@mui/icons-material';
import React from 'react';
import { useDebounce } from '../../../../hooks/useDebounce';
import { SuggestResponse } from '../../../../types/search.types';
import { getSuggestions } from '../../../../services/searchService';
import { EnhancedSuggestion } from '../types';

function detectCategory(text: string): 'bid' | 'document' | 'company' | undefined {
  const t = text.toLowerCase();
  if (t.includes('공고') || t.includes('입찰')) return 'bid';
  if (t.includes('문서') || t.includes('파일')) return 'document';
  if (t.includes('기업') || t.includes('회사')) return 'company';
  return undefined;
}

interface UseSearchBarOptions {
  onSearch: (query: string) => void;
  initialQuery?: string;
  showSuggestions?: boolean;
  showSearchStats?: boolean;
  enableAiSuggestions?: boolean;
}

export function useSearchBar({
  onSearch,
  initialQuery = '',
  showSuggestions = true,
  showSearchStats = true,
  enableAiSuggestions = false
}: UseSearchBarOptions) {
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

  // 초기화
  useEffect(() => {
    const saved = localStorage.getItem('recentSearches');
    if (saved) {
      try { setRecentSearches(JSON.parse(saved)); }
      catch (e) { console.error('Failed to load recent searches:', e); }
    }
    setTrendingSearches(['건설 공사', '소프트웨어 개발', 'SI 구축', '의료 장비', '시설 관리']);
    if (showSearchStats) setSearchStats({ total: 15234, recent: 523 });
  }, [showSearchStats]);

  // 자동완성 제안 가져오기
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
          const enhanced: EnhancedSuggestion[] = response.suggestions.map((text, index) => ({
            id: `suggestion-${index}`,
            text,
            type: 'suggestion' as const,
            category: detectCategory(text),
            metadata: { icon: detectCategory(text) }
          }));
          if (enableAiSuggestions) {
            enhanced.push({
              id: 'ai-suggestion',
              text: `"${debouncedQuery}"와 관련된 모든 결과 보기`,
              type: 'command',
              metadata: { icon: React.createElement(AiIcon, { color: 'primary' }) }
            });
          }
          setSuggestions(enhanced);
        }
      } catch (e) {
        console.error('Failed to fetch suggestions:', e);
        if (!cancelled) setSuggestions([]);
      } finally {
        if (!cancelled) setLoading(false);
      }
    };
    fetchSuggestions();
    return () => { cancelled = true; };
  }, [debouncedQuery, showSuggestions, enableAiSuggestions]);

  const handleSearch = useCallback(
    (searchQuery?: string) => {
      const finalQuery = searchQuery || query;
      if (!finalQuery.trim()) return;
      onSearch(finalQuery);
      const updated = [finalQuery, ...recentSearches.filter(s => s !== finalQuery)].slice(0, 10);
      setRecentSearches(updated);
      localStorage.setItem('recentSearches', JSON.stringify(updated));
      setAnchorEl(null);
      setSelectedIndex(-1);
      inputRef.current?.blur();
    },
    [query, onSearch, recentSearches]
  );

  const scrollToSelected = useCallback(() => {
    if (suggestionsRef.current && selectedIndex >= 0) {
      suggestionsRef.current
        .querySelector(`[data-index="${selectedIndex}"]`)
        ?.scrollIntoView({ block: 'nearest', behavior: 'smooth' });
    }
  }, [selectedIndex]);

  const handleKeyDown = useCallback(
    (event: React.KeyboardEvent) => {
      const allItems = [
        ...suggestions,
        ...recentSearches.map((text, i) => ({ id: `recent-${i}`, text, type: 'history' as const }))
      ];
      switch (event.key) {
        case 'Enter':
          event.preventDefault();
          if (selectedIndex >= 0 && selectedIndex < allItems.length) handleSearch(allItems[selectedIndex].text);
          else handleSearch();
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
          if (selectedIndex >= 0 && allItems[selectedIndex]) {
            event.preventDefault();
            setQuery(allItems[selectedIndex].text);
          }
          break;
      }
    },
    [suggestions, recentSearches, selectedIndex, handleSearch, scrollToSelected]
  );

  const removeRecentSearch = useCallback((text: string) => {
    const updated = recentSearches.filter(s => s !== text);
    setRecentSearches(updated);
    localStorage.setItem('recentSearches', JSON.stringify(updated));
  }, [recentSearches]);

  const clearRecentSearches = useCallback(() => {
    setRecentSearches([]);
    localStorage.removeItem('recentSearches');
  }, []);

  return {
    query, suggestions, recentSearches, trendingSearches, loading,
    selectedIndex, anchorEl, searchStats, showDropdown,
    inputRef, containerRef, suggestionsRef,
    setQuery, setAnchorEl,
    handleSearch, handleKeyDown, removeRecentSearch, clearRecentSearches
  };
}
