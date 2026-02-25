/**
 * EnhancedSearchBar - Type definitions
 */

import React from 'react';
import { SearchBarProps } from '../../../types/search.types';

// 제안 타입
export interface EnhancedSuggestion {
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
export interface EnhancedSearchBarProps extends SearchBarProps {
  showQuickActions?: boolean;
  showSearchStats?: boolean;
  enableAiSuggestions?: boolean;
  onCategorySelect?: (category: string) => void;
}
