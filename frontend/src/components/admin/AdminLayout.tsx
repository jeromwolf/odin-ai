/**
 * 관리자 웹 레이아웃 컴포넌트
 * 사이드바, 헤더, 메인 컨텐츠 영역 포함
 */

import React, { useState } from 'react';
import { useNavigate, useLocation, Outlet } from 'react-router-dom';
import {
  Box,
  Drawer,
  AppBar,
  Toolbar,
  List,
  Typography,
  Divider,
  IconButton,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Menu,
  MenuItem,
  Avatar,
  Chip,
} from '@mui/material';
import {
  Menu as MenuIcon,
  Dashboard,
  Settings,
  Storage,
  People,
  Description,
  BarChart,
  Logout,
  AccountCircle,
  Computer,
  Search,
  Bookmark,
  Notifications,
  Person,
} from '@mui/icons-material';
import { adminApi } from '../../services/admin/adminApi';

const DRAWER_WIDTH = 240;

interface AdminLayoutProps {
  children?: React.ReactNode;
}

const AdminLayout: React.FC<AdminLayoutProps> = ({ children }) => {
  const navigate = useNavigate();
  const location = useLocation();
  const [mobileOpen, setMobileOpen] = useState(false);
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);

  const handleDrawerToggle = () => {
    setMobileOpen(!mobileOpen);
  };

  const handleProfileMenuOpen = (event: React.MouseEvent<HTMLElement>) => {
    setAnchorEl(event.currentTarget);
  };

  const handleProfileMenuClose = () => {
    setAnchorEl(null);
  };

  const handleLogout = async () => {
    try {
      await adminApi.logout();
      navigate('/admin/login');
    } catch (error) {
      console.error('로그아웃 실패:', error);
      // 에러가 발생해도 로그아웃 처리
      adminApi.clearToken();
      navigate('/admin/login');
    }
  };

  // 일반 사용자 메뉴
  const userMenuItems = [
    { text: '대시보드', icon: <Dashboard />, path: '/dashboard' },
    { text: '입찰 검색', icon: <Search />, path: '/search' },
    { text: '북마크', icon: <Bookmark />, path: '/bookmarks' },
    { text: '알림 설정', icon: <Notifications />, path: '/notifications' },
    { text: '프로필', icon: <Person />, path: '/profile' },
    { text: '설정', icon: <Settings />, path: '/settings' },
  ];

  // 관리자 메뉴
  const adminMenuItems = [
    { text: '관리자 대시보드', icon: <Dashboard />, path: '/admin/dashboard' },
    { text: '배치 모니터링', icon: <Storage />, path: '/admin/batch' },
    { text: '시스템 모니터링', icon: <Computer />, path: '/admin/system' },
    { text: '알림 모니터링', icon: <Notifications />, path: '/admin/notifications' },
    { text: '사용자 관리', icon: <People />, path: '/admin/users' },
    { text: '로그 조회', icon: <Description />, path: '/admin/logs' },
    { text: '통계 분석', icon: <BarChart />, path: '/admin/statistics' },
  ];

  const drawer = (
    <div>
      <Toolbar>
        <Typography variant="h6" noWrap component="div">
          ODIN-AI 관리자
        </Typography>
      </Toolbar>
      <Divider />

      {/* 일반 사용자 메뉴 */}
      <Typography
        variant="overline"
        sx={{ px: 2, pt: 2, pb: 1, display: 'block', color: 'text.secondary' }}
      >
        일반 메뉴
      </Typography>
      <List>
        {userMenuItems.map((item) => (
          <ListItem key={item.text} disablePadding>
            <ListItemButton
              selected={location.pathname === item.path}
              onClick={() => navigate(item.path)}
            >
              <ListItemIcon>{item.icon}</ListItemIcon>
              <ListItemText primary={item.text} />
            </ListItemButton>
          </ListItem>
        ))}
      </List>

      <Divider sx={{ my: 1 }} />

      {/* 관리자 메뉴 */}
      <Typography
        variant="overline"
        sx={{ px: 2, pt: 1, pb: 1, display: 'block', color: 'text.secondary' }}
      >
        관리자 메뉴
      </Typography>
      <List>
        {adminMenuItems.map((item) => (
          <ListItem key={item.text} disablePadding>
            <ListItemButton
              selected={location.pathname === item.path}
              onClick={() => navigate(item.path)}
            >
              <ListItemIcon>{item.icon}</ListItemIcon>
              <ListItemText primary={item.text} />
            </ListItemButton>
          </ListItem>
        ))}
      </List>
    </div>
  );

  return (
    <Box sx={{ display: 'flex' }}>
      {/* 상단 AppBar */}
      <AppBar
        position="fixed"
        sx={{
          width: { sm: `calc(100% - ${DRAWER_WIDTH}px)` },
          ml: { sm: `${DRAWER_WIDTH}px` },
        }}
      >
        <Toolbar>
          <IconButton
            color="inherit"
            aria-label="open drawer"
            edge="start"
            onClick={handleDrawerToggle}
            sx={{ mr: 2, display: { sm: 'none' } }}
          >
            <MenuIcon />
          </IconButton>
          <Typography variant="h6" noWrap component="div" sx={{ flexGrow: 1 }}>
            관리자 대시보드
          </Typography>

          {/* 시스템 상태 표시 */}
          <Chip
            label="시스템 정상"
            color="success"
            size="small"
            sx={{ mr: 2 }}
          />

          {/* 프로필 메뉴 */}
          <IconButton
            size="large"
            edge="end"
            aria-label="account of current user"
            aria-controls="profile-menu"
            aria-haspopup="true"
            onClick={handleProfileMenuOpen}
            color="inherit"
          >
            <AccountCircle />
          </IconButton>
          <Menu
            id="profile-menu"
            anchorEl={anchorEl}
            anchorOrigin={{
              vertical: 'bottom',
              horizontal: 'right',
            }}
            keepMounted
            transformOrigin={{
              vertical: 'top',
              horizontal: 'right',
            }}
            open={Boolean(anchorEl)}
            onClose={handleProfileMenuClose}
          >
            <MenuItem onClick={handleProfileMenuClose}>
              <AccountCircle sx={{ mr: 1 }} />
              프로필
            </MenuItem>
            <MenuItem onClick={handleProfileMenuClose}>
              <Settings sx={{ mr: 1 }} />
              설정
            </MenuItem>
            <Divider />
            <MenuItem onClick={handleLogout}>
              <Logout sx={{ mr: 1 }} />
              로그아웃
            </MenuItem>
          </Menu>
        </Toolbar>
      </AppBar>

      {/* 사이드바 Drawer */}
      <Box
        component="nav"
        sx={{ width: { sm: DRAWER_WIDTH }, flexShrink: { sm: 0 } }}
      >
        {/* 모바일 Drawer */}
        <Drawer
          variant="temporary"
          open={mobileOpen}
          onClose={handleDrawerToggle}
          ModalProps={{
            keepMounted: true, // 모바일 성능 향상
          }}
          sx={{
            display: { xs: 'block', sm: 'none' },
            '& .MuiDrawer-paper': {
              boxSizing: 'border-box',
              width: DRAWER_WIDTH,
            },
          }}
        >
          {drawer}
        </Drawer>

        {/* 데스크톱 Drawer */}
        <Drawer
          variant="permanent"
          sx={{
            display: { xs: 'none', sm: 'block' },
            '& .MuiDrawer-paper': {
              boxSizing: 'border-box',
              width: DRAWER_WIDTH,
            },
          }}
          open
        >
          {drawer}
        </Drawer>
      </Box>

      {/* 메인 컨텐츠 영역 */}
      <Box
        component="main"
        sx={{
          flexGrow: 1,
          p: 3,
          width: { sm: `calc(100% - ${DRAWER_WIDTH}px)` },
        }}
      >
        <Toolbar /> {/* AppBar 높이만큼 여백 */}
        {children || <Outlet />}
      </Box>
    </Box>
  );
};

export default AdminLayout;
