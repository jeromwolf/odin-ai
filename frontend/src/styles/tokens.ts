// Design tokens for ODIN-AI frontend
// Style reference: Vercel/Linear/Notion - wide whitespace, restrained colors, clear hierarchy

// ---------------------------------------------------------------------------
// Spacing scale
// ---------------------------------------------------------------------------
export const spacing = {
  xs: 4,
  sm: 8,
  md: 16,
  lg: 24,
  xl: 32,
  xxl: 48,
} as const;

// ---------------------------------------------------------------------------
// Border radius
// ---------------------------------------------------------------------------
export const borderRadius = {
  xs: 4,
  sm: 8,
  md: 12,
  lg: 16,
  xl: 24,
  full: 9999,
} as const;

// ---------------------------------------------------------------------------
// Shadows – light mode
// ---------------------------------------------------------------------------
export const shadowsLight = {
  subtle: '0 1px 2px 0 rgba(0, 0, 0, 0.05)',
  card: '0 1px 3px 0 rgba(0, 0, 0, 0.08), 0 1px 2px -1px rgba(0, 0, 0, 0.06)',
  elevated: '0 4px 6px -1px rgba(0, 0, 0, 0.07), 0 2px 4px -2px rgba(0, 0, 0, 0.05)',
  dialog: '0 20px 25px -5px rgba(0, 0, 0, 0.10), 0 8px 10px -6px rgba(0, 0, 0, 0.08)',
} as const;

// ---------------------------------------------------------------------------
// Shadows – dark mode
// ---------------------------------------------------------------------------
export const shadowsDark = {
  subtle: '0 1px 2px 0 rgba(0, 0, 0, 0.30)',
  card: '0 1px 3px 0 rgba(0, 0, 0, 0.40), 0 1px 2px -1px rgba(0, 0, 0, 0.30)',
  elevated: '0 4px 6px -1px rgba(0, 0, 0, 0.50), 0 2px 4px -2px rgba(0, 0, 0, 0.40)',
  dialog: '0 20px 25px -5px rgba(0, 0, 0, 0.60), 0 8px 10px -6px rgba(0, 0, 0, 0.50)',
} as const;

// ---------------------------------------------------------------------------
// Transitions
// ---------------------------------------------------------------------------
export const transitions = {
  fast: 'all 150ms cubic-bezier(0.4, 0, 0.2, 1)',
  normal: 'all 200ms cubic-bezier(0.4, 0, 0.2, 1)',
  slow: 'all 300ms cubic-bezier(0.4, 0, 0.2, 1)',
} as const;

export const transitionDuration = {
  fast: 150,
  normal: 200,
  slow: 300,
} as const;

export const transitionEasing = 'cubic-bezier(0.4, 0, 0.2, 1)';

// ---------------------------------------------------------------------------
// Chart color palette – 8 harmonious colors anchored to primary blue
// ---------------------------------------------------------------------------
export const chartColors = [
  '#2563EB', // Blue 600 – primary
  '#7C3AED', // Violet 600 – secondary
  '#059669', // Emerald 600 – success
  '#D97706', // Amber 600 – warning
  '#DC2626', // Red 600 – error
  '#0891B2', // Cyan 600
  '#EA580C', // Orange 600
  '#7E22CE', // Purple 700
] as const;

// ---------------------------------------------------------------------------
// Raw palette (used by semantic tokens below)
// ---------------------------------------------------------------------------
const palette = {
  primary: '#2563EB',
  primaryHover: '#1D4ED8',
  secondary: '#7C3AED',
  success: '#059669',
  warning: '#D97706',
  error: '#DC2626',
} as const;

// ---------------------------------------------------------------------------
// Semantic color tokens – light mode
// ---------------------------------------------------------------------------
export const colorsLight = {
  // Core palette
  primary: palette.primary,
  primaryHover: palette.primaryHover,
  secondary: palette.secondary,
  success: palette.success,
  warning: palette.warning,
  error: palette.error,

  // Surfaces
  background: '#F8FAFC',
  surface: '#FFFFFF',
  surfaceHover: '#F1F5F9',
  surfaceMuted: '#F8FAFC',

  // Text
  textPrimary: '#0F172A',
  textSecondary: '#64748B',
  textDisabled: '#CBD5E1',
  textInverse: '#FFFFFF',

  // Borders
  border: '#E2E8F0',
  borderStrong: '#CBD5E1',
  divider: '#E2E8F0',
} as const;

// ---------------------------------------------------------------------------
// Semantic color tokens – dark mode
// ---------------------------------------------------------------------------
export const colorsDark = {
  // Core palette (same, they work on both backgrounds)
  primary: palette.primary,
  primaryHover: '#3B82F6',
  secondary: '#8B5CF6',
  success: '#10B981',
  warning: '#F59E0B',
  error: '#EF4444',

  // Surfaces
  background: '#0F172A',
  surface: '#1E293B',
  surfaceHover: '#273549',
  surfaceMuted: '#0F172A',

  // Text
  textPrimary: '#F1F5F9',
  textSecondary: '#94A3B8',
  textDisabled: '#475569',
  textInverse: '#0F172A',

  // Borders
  border: '#334155',
  borderStrong: '#475569',
  divider: '#334155',
} as const;

// ---------------------------------------------------------------------------
// Drawer width constants
// ---------------------------------------------------------------------------
export const drawerWidth = {
  full: 240,
  mini: 56,
} as const;

// ---------------------------------------------------------------------------
// Z-index layers
// ---------------------------------------------------------------------------
export const zIndex = {
  drawer: 1200,
  appBar: 1100,
  modal: 1300,
  tooltip: 1500,
  snackbar: 1400,
} as const;
