import React, { useEffect, useState } from 'react';
import { IconButton, Tooltip } from '@mui/material';
import Brightness4Icon from '@mui/icons-material/Brightness4';
import Brightness7Icon from '@mui/icons-material/Brightness7';
import { styled } from '@mui/material/styles';

const StyledIconButton = styled(IconButton)(({ theme }) => ({
  position: 'fixed',
  top: 16,
  right: 16,
  zIndex: 1200,
  backgroundColor: theme.palette.mode === 'dark' ? '#2c2c2c' : '#ffffff',
  border: `1px solid ${theme.palette.mode === 'dark' ? '#404040' : '#e0e0e0'}`,
  boxShadow: theme.shadows[2],
  '&:hover': {
    backgroundColor: theme.palette.mode === 'dark' ? '#404040' : '#f5f5f5',
  },
  transition: 'all 0.3s ease',
  [theme.breakpoints.down('sm')]: {
    top: 8,
    right: 8,
    width: 40,
    height: 40,
  },
}));

interface DarkModeToggleProps {
  onThemeChange?: (isDark: boolean) => void;
}

const DarkModeToggle: React.FC<DarkModeToggleProps> = ({ onThemeChange }) => {
  const [darkMode, setDarkMode] = useState<boolean>(() => {
    // 로컬스토리지에서 테마 설정 불러오기
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme) {
      return savedTheme === 'dark';
    }
    // 시스템 설정 확인
    return window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
  });

  useEffect(() => {
    // HTML 요소에 data-theme 속성 설정
    document.documentElement.setAttribute('data-theme', darkMode ? 'dark' : 'light');
    // 로컬스토리지에 저장
    localStorage.setItem('theme', darkMode ? 'dark' : 'light');
    // 콜백 호출
    if (onThemeChange) {
      onThemeChange(darkMode);
    }

    // MUI 테마도 업데이트하기 위한 이벤트 발생
    window.dispatchEvent(new CustomEvent('themeChange', { detail: { darkMode } }));
  }, [darkMode, onThemeChange]);

  // 시스템 테마 변경 감지
  useEffect(() => {
    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
    const handleChange = (e: MediaQueryListEvent) => {
      if (!localStorage.getItem('theme')) {
        setDarkMode(e.matches);
      }
    };

    if (mediaQuery.addEventListener) {
      mediaQuery.addEventListener('change', handleChange);
      return () => mediaQuery.removeEventListener('change', handleChange);
    }
  }, []);

  const toggleDarkMode = () => {
    setDarkMode(!darkMode);
  };

  return (
    <Tooltip title={darkMode ? '라이트 모드로 전환' : '다크 모드로 전환'}>
      <StyledIconButton
        color="inherit"
        onClick={toggleDarkMode}
        aria-label="toggle dark mode"
      >
        {darkMode ? <Brightness7Icon /> : <Brightness4Icon />}
      </StyledIconButton>
    </Tooltip>
  );
};

export default DarkModeToggle;