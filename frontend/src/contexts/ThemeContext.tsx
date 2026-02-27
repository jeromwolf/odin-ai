import React, {
  createContext,
  useContext,
  useState,
  useEffect,
  useMemo,
  ReactNode,
} from 'react';
import { ThemeProvider as MuiThemeProvider, CssBaseline } from '@mui/material';
import { createAppTheme } from '../styles/createAppTheme';

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export type ThemeMode = 'light' | 'dark' | 'system';
export type ResolvedThemeMode = 'light' | 'dark';

interface ThemeContextValue {
  /** The user-chosen preference: 'light' | 'dark' | 'system' */
  mode: ThemeMode;
  /** The actual rendered mode after resolving 'system' */
  resolvedMode: ResolvedThemeMode;
  /** Set the preference explicitly */
  setTheme: (mode: ThemeMode) => void;
  /** Toggle between light and dark (bypasses system) */
  toggleTheme: () => void;
}

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const STORAGE_KEY = 'odin-theme-mode';
const DARK_MEDIA_QUERY = '(prefers-color-scheme: dark)';

// ---------------------------------------------------------------------------
// Context
// ---------------------------------------------------------------------------

export const ThemeContext = createContext<ThemeContextValue>({
  mode: 'system',
  resolvedMode: 'light',
  setTheme: () => undefined,
  toggleTheme: () => undefined,
});

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function readStoredMode(): ThemeMode {
  try {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (stored === 'light' || stored === 'dark' || stored === 'system') {
      return stored;
    }
  } catch {
    // localStorage may be unavailable (SSR, incognito restrictions, etc.)
  }
  return 'system';
}

function getSystemPreference(): ResolvedThemeMode {
  try {
    if (window.matchMedia && window.matchMedia(DARK_MEDIA_QUERY).matches) {
      return 'dark';
    }
  } catch {
    // matchMedia unavailable
  }
  return 'light';
}

function resolveMode(mode: ThemeMode, systemPref: ResolvedThemeMode): ResolvedThemeMode {
  if (mode === 'system') return systemPref;
  return mode;
}

// ---------------------------------------------------------------------------
// Provider
// ---------------------------------------------------------------------------

interface AppThemeProviderProps {
  children: ReactNode;
}

export function AppThemeProvider({ children }: AppThemeProviderProps) {
  const [mode, setMode] = useState<ThemeMode>(readStoredMode);
  const [systemPref, setSystemPref] = useState<ResolvedThemeMode>(getSystemPreference);

  // Listen for OS-level preference changes
  useEffect(() => {
    const mediaQuery = window.matchMedia?.(DARK_MEDIA_QUERY);
    if (!mediaQuery) return;

    const handler = (e: MediaQueryListEvent) => {
      setSystemPref(e.matches ? 'dark' : 'light');
    };

    // Modern API
    if (typeof mediaQuery.addEventListener === 'function') {
      mediaQuery.addEventListener('change', handler);
      return () => mediaQuery.removeEventListener('change', handler);
    }

    // Legacy fallback
    if (typeof mediaQuery.addListener === 'function') {
      mediaQuery.addListener(handler);
      return () => mediaQuery.removeListener(handler);
    }
  }, []);

  // Persist preference to localStorage whenever it changes
  useEffect(() => {
    try {
      localStorage.setItem(STORAGE_KEY, mode);
    } catch {
      // ignore write errors
    }
  }, [mode]);

  const resolvedMode = useMemo<ResolvedThemeMode>(
    () => resolveMode(mode, systemPref),
    [mode, systemPref]
  );

  const muiTheme = useMemo(() => createAppTheme(resolvedMode), [resolvedMode]);

  const setTheme = (newMode: ThemeMode) => {
    setMode(newMode);
  };

  const toggleTheme = () => {
    setMode((prev) => {
      // If currently resolved to dark, switch to light, and vice-versa.
      // This bypasses 'system' and pins an explicit choice.
      const currentResolved = resolveMode(prev, systemPref);
      return currentResolved === 'dark' ? 'light' : 'dark';
    });
  };

  const contextValue = useMemo<ThemeContextValue>(
    () => ({ mode, resolvedMode, setTheme, toggleTheme }),
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [mode, resolvedMode]
  );

  return (
    <ThemeContext.Provider value={contextValue}>
      <MuiThemeProvider theme={muiTheme}>
        <CssBaseline />
        {children}
      </MuiThemeProvider>
    </ThemeContext.Provider>
  );
}

// ---------------------------------------------------------------------------
// Hook
// ---------------------------------------------------------------------------

export function useAppTheme(): ThemeContextValue {
  const ctx = useContext(ThemeContext);
  if (!ctx) {
    throw new Error('useAppTheme must be used within an AppThemeProvider');
  }
  return ctx;
}
