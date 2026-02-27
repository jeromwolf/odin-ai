/**
 * 통합 색상 유틸리티
 * Dashboard, admin/Dashboard, Subscription, admin/Logs 등에서 하드코딩된 색상 통합
 */

/** 차트에 사용하는 8가지 조화로운 색상 팔레트 */
export const CHART_COLORS: string[] = [
  '#3B82F6',
  '#8B5CF6',
  '#06B6D4',
  '#10B981',
  '#F59E0B',
  '#EF4444',
  '#EC4899',
  '#6366F1',
];

/** 통계 카드 타입별 배경/텍스트/아이콘 색상 */
export const STAT_CARD_COLORS = {
  total:   { bg: '#EFF6FF', color: '#2563EB', icon: '#3B82F6' },
  active:  { bg: '#F0FDF4', color: '#059669', icon: '#10B981' },
  warning: { bg: '#FFFBEB', color: '#D97706', icon: '#F59E0B' },
  info:    { bg: '#F5F3FF', color: '#7C3AED', icon: '#8B5CF6' },
  error:   { bg: '#FEF2F2', color: '#DC2626', icon: '#EF4444' },
} as const;

/** 로그 레벨을 MUI Chip color 값으로 매핑 */
export const LOG_LEVEL_COLORS: Record<string, 'error' | 'warning' | 'info' | 'success' | 'default'> = {
  ERROR:    'error',
  WARNING:  'warning',
  INFO:     'info',
  DEBUG:    'default',
  CRITICAL: 'error',
};

/** 구독 플랜명을 hex 색상으로 매핑 */
export const SUBSCRIPTION_PLAN_COLORS: Record<string, string> = {
  free:       '#64748B',
  basic:      '#2563EB',
  pro:        '#7C3AED',
  enterprise: '#059669',
};

/** 입찰 상태별 배경/텍스트 색상 */
export const BID_STATUS_COLORS: Record<string, { bg: string; color: string }> = {
  active:   { bg: '#F0FDF4', color: '#059669' },
  closed:   { bg: '#FEF2F2', color: '#DC2626' },
  upcoming: { bg: '#EFF6FF', color: '#2563EB' },
};

/** GraphExplorer 엔티티 타입별 색상 */
export const ENTITY_TYPE_COLORS: Record<string, string> = {
  organization: '#3B82F6',
  project:      '#8B5CF6',
  location:     '#10B981',
  keyword:      '#F59E0B',
  category:     '#06B6D4',
  default:      '#64748B',
};

/**
 * 인덱스로 차트 색상 순환 반환
 * @example getChartColor(0) → '#3B82F6'
 * @example getChartColor(9) → '#8B5CF6'  (cycles back)
 */
export function getChartColor(index: number): string {
  return CHART_COLORS[index % CHART_COLORS.length];
}

/**
 * hex 색상에 투명도(alpha) 적용하여 rgba 문자열 반환
 * @param hex '#RRGGBB' 형식의 hex 색상
 * @param alpha 0~1 사이의 투명도
 * @example getAlphaColor('#3B82F6', 0.1) → 'rgba(59, 130, 246, 0.1)'
 */
export function getAlphaColor(hex: string, alpha: number): string {
  const clean = hex.replace('#', '');
  const r = parseInt(clean.substring(0, 2), 16);
  const g = parseInt(clean.substring(2, 4), 16);
  const b = parseInt(clean.substring(4, 6), 16);
  return `rgba(${r}, ${g}, ${b}, ${alpha})`;
}
