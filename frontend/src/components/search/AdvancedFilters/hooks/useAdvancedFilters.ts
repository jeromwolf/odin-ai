/**
 * useAdvancedFilters - 고급 필터 상태 관리 훅
 */

import React, { useState, useCallback, useMemo } from 'react';
import { Bookmark as BookmarkIcon } from '@mui/icons-material';
import { SearchFilters, FilterPreset } from '../types';

interface UseAdvancedFiltersProps {
  filters: SearchFilters;
  onFilterChange: (filters: SearchFilters) => void;
  onPresetSave?: (preset: FilterPreset) => void;
}

export function useAdvancedFilters({
  filters,
  onFilterChange,
  onPresetSave
}: UseAdvancedFiltersProps) {
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

  const toggleSection = useCallback((section: string) => {
    setExpandedSections(prev => {
      const newSet = new Set(prev);
      if (newSet.has(section)) {
        newSet.delete(section);
      } else {
        newSet.add(section);
      }
      return newSet;
    });
  }, []);

  const handlePriceChange = useCallback((_event: Event, newValue: number | number[]) => {
    const [min, max] = newValue as number[];
    setPriceRange([min, max]);
  }, []);

  const handlePriceCommit = useCallback(() => {
    setLocalFilters(prev => ({
      ...prev,
      minPrice: priceRange[0] > 0 ? priceRange[0] : undefined,
      maxPrice: priceRange[1] < 1000000000 ? priceRange[1] : undefined
    }));
  }, [priceRange]);

  const handleDateChange = useCallback((field: 'startDate' | 'endDate', value: Date | null) => {
    setLocalFilters(prev => ({
      ...prev,
      [field]: value ? value.toISOString().split('T')[0] : undefined
    }));
  }, []);

  const handleTagToggle = useCallback((tag: string) => {
    setSelectedTags(prev => {
      const newTags = prev.includes(tag) ? prev.filter(t => t !== tag) : [...prev, tag];
      setLocalFilters(f => ({ ...f, tags: newTags.length > 0 ? newTags : undefined }));
      return newTags;
    });
  }, []);

  const applyPreset = useCallback((preset: FilterPreset) => {
    setLocalFilters(prev => ({ ...prev, ...preset.filters }));
    setSelectedPreset(preset.id);
    if (preset.filters.minPrice || preset.filters.maxPrice) {
      setPriceRange([preset.filters.minPrice || 0, preset.filters.maxPrice || 1000000000]);
    }
    if (preset.filters.tags) {
      setSelectedTags(preset.filters.tags);
    }
  }, []);

  const handleApply = useCallback(() => {
    onFilterChange(localFilters);
  }, [localFilters, onFilterChange]);

  const handleReset = useCallback(() => {
    const emptyFilters: SearchFilters = {};
    setLocalFilters(emptyFilters);
    setPriceRange([0, 1000000000]);
    setSelectedTags([]);
    setSelectedPreset(null);
    onFilterChange(emptyFilters);
  }, [onFilterChange]);

  const handleSavePreset = useCallback(() => {
    if (customPresetName && onPresetSave) {
      onPresetSave({
        id: `custom-${Date.now()}`,
        name: customPresetName,
        filters: localFilters,
        icon: React.createElement(BookmarkIcon)
      });
      setCustomPresetName('');
      setShowPresetDialog(false);
    }
  }, [customPresetName, localFilters, onPresetSave]);

  const formatPrice = useCallback((value: number): string => {
    if (value >= 100000000) return `${(value / 100000000).toFixed(1)}억`;
    if (value >= 10000000) return `${(value / 10000000).toFixed(1)}천만`;
    if (value >= 10000) return `${(value / 10000).toFixed(0)}만`;
    return value.toLocaleString();
  }, []);

  const generateInsights = useCallback((): string[] => {
    const insights: string[] = [];
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
    if (selectedTags.length > 3) insights.push('다양한 분야를 폭넓게 검색 중입니다');
    return insights;
  }, [localFilters, selectedTags]);

  const setDateToday = useCallback(() => {
    const today = new Date().toISOString().split('T')[0];
    setLocalFilters(prev => ({ ...prev, startDate: today, endDate: today }));
  }, []);

  const setDateThisWeek = useCallback(() => {
    const now = new Date();
    const monday = new Date(now);
    monday.setDate(now.getDate() - now.getDay() + 1);
    const sunday = new Date(monday);
    sunday.setDate(monday.getDate() + 6);
    setLocalFilters(prev => ({
      ...prev,
      startDate: monday.toISOString().split('T')[0],
      endDate: sunday.toISOString().split('T')[0]
    }));
  }, []);

  const setDateThisMonth = useCallback(() => {
    const now = new Date();
    const firstDay = new Date(now.getFullYear(), now.getMonth(), 1);
    const lastDay = new Date(now.getFullYear(), now.getMonth() + 1, 0);
    setLocalFilters(prev => ({
      ...prev,
      startDate: firstDay.toISOString().split('T')[0],
      endDate: lastDay.toISOString().split('T')[0]
    }));
  }, []);

  return {
    localFilters, setLocalFilters, expandedSections, selectedPreset,
    showAdvanced, setShowAdvanced, priceRange, setPriceRange,
    selectedTags, customPresetName, setCustomPresetName,
    showPresetDialog, setShowPresetDialog, activeFilterCount,
    toggleSection, handlePriceChange, handlePriceCommit,
    handleDateChange, handleTagToggle, applyPreset,
    handleApply, handleReset, handleSavePreset,
    formatPrice, generateInsights,
    setDateToday, setDateThisWeek, setDateThisMonth
  };
}
