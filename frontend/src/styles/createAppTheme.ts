import { createTheme, ThemeOptions } from '@mui/material/styles';
import {
  borderRadius,
  colorsLight,
  colorsDark,
  drawerWidth,
  zIndex as zIndexTokens,
} from './tokens';

const fontFamily = [
  'Inter',
  '-apple-system',
  'BlinkMacSystemFont',
  '"Segoe UI"',
  'Roboto',
  'sans-serif',
].join(', ');

export function createAppTheme(mode: 'light' | 'dark') {
  const colors = mode === 'light' ? colorsLight : colorsDark;
  const isDark = mode === 'dark';

  const themeOptions: ThemeOptions = {
    palette: {
      mode,
      primary: {
        main: colors.primary,
        contrastText: colors.textInverse,
      },
      secondary: {
        main: colors.secondary,
        contrastText: '#FFFFFF',
      },
      success: {
        main: colors.success,
      },
      warning: {
        main: colors.warning,
      },
      error: {
        main: colors.error,
      },
      background: {
        default: colors.background,
        paper: colors.surface,
      },
      text: {
        primary: colors.textPrimary,
        secondary: colors.textSecondary,
        disabled: colors.textDisabled,
      },
      divider: colors.divider,
    },

    typography: {
      fontFamily,
      h1: {
        fontWeight: 700,
        fontSize: '2.25rem',
        lineHeight: 1.2,
        letterSpacing: '-0.02em',
      },
      h2: {
        fontWeight: 700,
        fontSize: '1.875rem',
        lineHeight: 1.25,
        letterSpacing: '-0.015em',
      },
      h3: {
        fontWeight: 700,
        fontSize: '1.5rem',
        lineHeight: 1.3,
        letterSpacing: '-0.01em',
      },
      h4: {
        fontWeight: 600,
        fontSize: '1.25rem',
        lineHeight: 1.35,
        letterSpacing: '-0.008em',
      },
      h5: {
        fontWeight: 600,
        fontSize: '1.125rem',
        lineHeight: 1.4,
        letterSpacing: '-0.005em',
      },
      h6: {
        fontWeight: 600,
        fontSize: '1rem',
        lineHeight: 1.5,
        letterSpacing: '-0.003em',
      },
      body1: {
        fontSize: '0.9375rem',
        lineHeight: 1.6,
      },
      body2: {
        fontSize: '0.875rem',
        lineHeight: 1.57,
      },
      caption: {
        fontSize: '0.75rem',
        lineHeight: 1.5,
      },
      overline: {
        fontSize: '0.6875rem',
        fontWeight: 600,
        letterSpacing: '0.08em',
        textTransform: 'uppercase',
      },
      button: {
        fontWeight: 500,
        fontSize: '0.875rem',
      },
    },

    shape: {
      borderRadius: borderRadius.sm,
    },

    zIndex: {
      drawer: zIndexTokens.drawer,
      appBar: zIndexTokens.appBar,
      modal: zIndexTokens.modal,
      tooltip: zIndexTokens.tooltip,
      snackbar: zIndexTokens.snackbar,
    },

    components: {
      // -----------------------------------------------------------------------
      // CssBaseline
      // -----------------------------------------------------------------------
      MuiCssBaseline: {
        styleOverrides: {
          body: {
            backgroundColor: colors.background,
            color: colors.textPrimary,
            WebkitFontSmoothing: 'antialiased',
            MozOsxFontSmoothing: 'grayscale',
            textRendering: 'optimizeLegibility',
          },
        },
      },

      // -----------------------------------------------------------------------
      // Button
      // -----------------------------------------------------------------------
      MuiButton: {
        styleOverrides: {
          root: {
            textTransform: 'none',
            borderRadius: borderRadius.sm,
            fontWeight: 500,
            boxShadow: 'none',
            '&:hover': {
              boxShadow: 'none',
            },
            '&:active': {
              boxShadow: 'none',
            },
          },
          containedPrimary: {
            '&:hover': {
              backgroundColor: colors.primaryHover,
            },
          },
          outlined: {
            borderColor: colors.border,
            '&:hover': {
              borderColor: colors.borderStrong,
              backgroundColor: colors.surfaceHover,
            },
          },
          text: {
            '&:hover': {
              backgroundColor: colors.surfaceHover,
            },
          },
        },
      },

      // -----------------------------------------------------------------------
      // Card
      // -----------------------------------------------------------------------
      MuiCard: {
        styleOverrides: {
          root: {
            borderRadius: borderRadius.md,
            border: `1px solid ${colors.border}`,
            // rootbircks-style: clean card with border, no shadow in light mode
            boxShadow: isDark
              ? '0 1px 3px 0 rgba(0, 0, 0, 0.40), 0 1px 2px -1px rgba(0, 0, 0, 0.30)'
              : 'none',
            backgroundColor: colors.surface,
          },
        },
      },

      MuiCardContent: {
        styleOverrides: {
          root: {
            '&:last-child': {
              paddingBottom: 16,
            },
          },
        },
      },

      // -----------------------------------------------------------------------
      // Paper
      // -----------------------------------------------------------------------
      MuiPaper: {
        styleOverrides: {
          root: {
            backgroundImage: 'none',
          },
          rounded: {
            borderRadius: borderRadius.md,
          },
          elevation0: {
            boxShadow: 'none',
          },
          elevation1: {
            boxShadow: isDark
              ? '0 1px 2px 0 rgba(0, 0, 0, 0.30)'
              : '0 1px 2px 0 rgba(0, 0, 0, 0.05)',
          },
          elevation2: {
            boxShadow: isDark
              ? '0 1px 3px 0 rgba(0, 0, 0, 0.40), 0 1px 2px -1px rgba(0, 0, 0, 0.30)'
              : '0 1px 3px 0 rgba(0, 0, 0, 0.08), 0 1px 2px -1px rgba(0, 0, 0, 0.06)',
          },
          elevation4: {
            boxShadow: isDark
              ? '0 4px 6px -1px rgba(0, 0, 0, 0.50), 0 2px 4px -2px rgba(0, 0, 0, 0.40)'
              : '0 4px 6px -1px rgba(0, 0, 0, 0.07), 0 2px 4px -2px rgba(0, 0, 0, 0.05)',
          },
        },
      },

      // -----------------------------------------------------------------------
      // TextField
      // -----------------------------------------------------------------------
      MuiTextField: {
        defaultProps: {
          variant: 'outlined',
          size: 'small',
        },
      },

      MuiOutlinedInput: {
        styleOverrides: {
          root: {
            borderRadius: borderRadius.sm,
            backgroundColor: colors.surface,
            '& .MuiOutlinedInput-notchedOutline': {
              borderColor: colors.border,
            },
            '&:hover .MuiOutlinedInput-notchedOutline': {
              borderColor: colors.borderStrong,
            },
            '&.Mui-focused .MuiOutlinedInput-notchedOutline': {
              borderColor: colors.primary,
              borderWidth: 1.5,
            },
          },
        },
      },

      // -----------------------------------------------------------------------
      // Chip
      // -----------------------------------------------------------------------
      MuiChip: {
        styleOverrides: {
          root: {
            borderRadius: borderRadius.xs + 2, // 6
            fontWeight: 500,
            fontSize: '0.75rem',
          },
        },
      },

      // -----------------------------------------------------------------------
      // Table
      // -----------------------------------------------------------------------
      MuiTableCell: {
        styleOverrides: {
          root: {
            borderBottom: `1px solid ${colors.divider}`,
            fontSize: '0.875rem',
          },
          head: {
            fontWeight: 600,
            color: colors.textSecondary,
            fontSize: '0.75rem',
            letterSpacing: '0.04em',
            textTransform: 'uppercase',
            backgroundColor: colors.background,
          },
        },
      },

      MuiTableRow: {
        styleOverrides: {
          root: {
            '&:hover': {
              backgroundColor: colors.surfaceHover,
            },
            '&:last-child td': {
              borderBottom: 0,
            },
          },
        },
      },

      // -----------------------------------------------------------------------
      // Drawer
      // -----------------------------------------------------------------------
      MuiDrawer: {
        styleOverrides: {
          paper: {
            backgroundColor: colors.surface,
            borderRight: `1px solid ${colors.border}`,
            boxShadow: 'none',
            width: drawerWidth.full,
          },
        },
      },

      // -----------------------------------------------------------------------
      // AppBar
      // -----------------------------------------------------------------------
      MuiAppBar: {
        styleOverrides: {
          root: {
            backgroundColor: colors.surface,
            color: colors.textPrimary,
            // rootbircks style: border-bottom instead of shadow
            boxShadow: 'none',
            borderBottom: `1px solid ${colors.border}`,
          },
        },
      },

      // -----------------------------------------------------------------------
      // Dialog
      // -----------------------------------------------------------------------
      MuiDialog: {
        styleOverrides: {
          paper: {
            borderRadius: borderRadius.lg,
            backgroundColor: colors.surface,
            border: `1px solid ${colors.border}`,
            boxShadow: isDark
              ? '0 20px 25px -5px rgba(0, 0, 0, 0.60), 0 8px 10px -6px rgba(0, 0, 0, 0.50)'
              : '0 20px 25px -5px rgba(0, 0, 0, 0.10), 0 8px 10px -6px rgba(0, 0, 0, 0.08)',
          },
        },
      },

      MuiDialogTitle: {
        styleOverrides: {
          root: {
            fontWeight: 600,
            fontSize: '1.0625rem',
            padding: '20px 24px 12px',
          },
        },
      },

      MuiDialogContent: {
        styleOverrides: {
          root: {
            padding: '8px 24px 20px',
          },
        },
      },

      MuiDialogActions: {
        styleOverrides: {
          root: {
            padding: '12px 24px 20px',
            gap: 8,
          },
        },
      },

      // -----------------------------------------------------------------------
      // Tooltip
      // -----------------------------------------------------------------------
      MuiTooltip: {
        styleOverrides: {
          tooltip: {
            borderRadius: borderRadius.sm,
            fontSize: 12,
            fontWeight: 500,
            backgroundColor: isDark ? '#334155' : '#1E293B',
            color: '#F8FAFC',
            padding: '6px 10px',
          },
          arrow: {
            color: isDark ? '#334155' : '#1E293B',
          },
        },
      },

      // -----------------------------------------------------------------------
      // List
      // -----------------------------------------------------------------------
      MuiListItemButton: {
        styleOverrides: {
          root: {
            borderRadius: borderRadius.sm,
            '&:hover': {
              backgroundColor: colors.surfaceHover,
            },
            '&.Mui-selected': {
              backgroundColor: isDark
                ? 'rgba(37, 99, 235, 0.15)'
                : 'rgba(37, 99, 235, 0.08)',
              '&:hover': {
                backgroundColor: isDark
                  ? 'rgba(37, 99, 235, 0.22)'
                  : 'rgba(37, 99, 235, 0.12)',
              },
            },
          },
        },
      },

      // -----------------------------------------------------------------------
      // Divider
      // -----------------------------------------------------------------------
      MuiDivider: {
        styleOverrides: {
          root: {
            borderColor: colors.divider,
          },
        },
      },

      // -----------------------------------------------------------------------
      // Alert
      // -----------------------------------------------------------------------
      MuiAlert: {
        styleOverrides: {
          root: {
            borderRadius: borderRadius.sm,
            fontSize: '0.875rem',
          },
        },
      },

      // -----------------------------------------------------------------------
      // Tabs
      // -----------------------------------------------------------------------
      MuiTab: {
        styleOverrides: {
          root: {
            textTransform: 'none',
            fontWeight: 500,
            fontSize: '0.875rem',
          },
        },
      },

      // -----------------------------------------------------------------------
      // Select
      // -----------------------------------------------------------------------
      MuiSelect: {
        styleOverrides: {
          select: {
            borderRadius: borderRadius.sm,
          },
        },
      },

      // -----------------------------------------------------------------------
      // Skeleton
      // -----------------------------------------------------------------------
      MuiSkeleton: {
        styleOverrides: {
          root: {
            backgroundColor: isDark ? '#273549' : '#E2E8F0',
          },
        },
      },
    },
  };

  return createTheme(themeOptions);
}
