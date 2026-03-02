import React, { useState, useEffect } from 'react';
import { Outlet, useNavigate, useLocation } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
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
  Avatar,
  Menu,
  MenuItem,
  Badge,
  Tooltip,
  useMediaQuery,
  useTheme,
} from '@mui/material';
import {
  Menu as MenuIcon,
  Dashboard,
  Search,
  Bookmark,
  AccountBalance,
  Person,
  Settings,
  Notifications,
  NotificationsActive,
  Logout,
  ChevronLeft,
  ChevronRight,
  AdminPanelSettings,
  Schedule,
  Computer,
  People,
  Assessment,
  Description,
  Hub,
  DarkMode,
  LightMode,
  Security,
  TrendingUp,
} from '@mui/icons-material';
import { useAuth } from '../../contexts/AuthContext';
import { useAppTheme } from '../../contexts/ThemeContext';

const drawerWidth = 240;

const menuItems = [
  { text: '대시보드', icon: <Dashboard />, path: '/dashboard' },
  { text: '입찰 검색', icon: <Search />, path: '/search' },
  { text: '북마크', icon: <Bookmark />, path: '/bookmarks' },
  { text: '알림 설정', icon: <NotificationsActive />, path: '/notifications' },
  { text: '지식 그래프', icon: <Hub />, path: '/graph' },
  { text: '트렌드 분석', icon: <TrendingUp />, path: '/trends' },
  { text: '프로필', icon: <Person />, path: '/profile' },
  { text: '설정', icon: <Settings />, path: '/settings' },
];

const adminMenuItems = [
  { text: '관리자 대시보드', icon: <AdminPanelSettings />, path: '/admin/dashboard' },
  { text: '배치 모니터링', icon: <Schedule />, path: '/admin/batch' },
  { text: '시스템 모니터링', icon: <Computer />, path: '/admin/system' },
  { text: '사용자 관리', icon: <People />, path: '/admin/users' },
  { text: '로그 조회', icon: <Description />, path: '/admin/logs' },
  { text: '통계 분석', icon: <Assessment />, path: '/admin/statistics' },
  { text: '알림 모니터링', icon: <Notifications />, path: '/admin/notifications' },
];

const MainLayout: React.FC = () => {
  const [open, setOpen] = useState(true);
  const [anchorEl, setAnchorEl] = useState<HTMLElement | null>(null);
  const [unreadCount, setUnreadCount] = useState(0);

  useEffect(() => {
    const fetchUnreadCount = async () => {
      try {
        const token = localStorage.getItem(process.env.REACT_APP_TOKEN_KEY || 'odin_ai_token');
        if (!token) return;
        const response = await fetch(
          `${process.env.REACT_APP_API_URL || 'http://localhost:9000'}/api/notifications/?status=unread&limit=1`,
          { headers: { 'Authorization': `Bearer ${token}` } }
        );
        if (response.ok) {
          const data = await response.json();
          setUnreadCount(data.total || 0);
        }
      } catch {
        // 알림 조회 실패 시 0으로 유지
      }
    };
    fetchUnreadCount();
    const interval = setInterval(fetchUnreadCount, 60000); // 1분마다 갱신
    return () => clearInterval(interval);
  }, []);
  const navigate = useNavigate();
  const location = useLocation();
  const { user, logout } = useAuth();
  const { resolvedMode, toggleTheme } = useAppTheme();

  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));

  const handleDrawerToggle = () => {
    setOpen(!open);
  };

  const handleProfileMenuOpen = (event: React.MouseEvent<HTMLElement>) => {
    setAnchorEl(event.currentTarget);
  };

  const handleMenuClose = () => {
    setAnchorEl(null);
  };

  const handleLogout = async () => {
    try {
      await logout();
    } catch {
      // 로그아웃 실패 시에도 메뉴 닫기
    }
    handleMenuClose();
  };

  const handleNavigation = (path: string) => {
    navigate(path);
    if (isMobile) {
      setOpen(false);
    }
  };

  const drawerContent = (
    <>
      {/* Sidebar header */}
      <Box
        sx={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: open ? 'space-between' : 'center',
          px: open ? 2 : 0,
          height: 64, // matches AppBar Toolbar height
          flexShrink: 0,
        }}
      >
        {open && (
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <Box
              sx={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                width: 32,
                height: 32,
                borderRadius: '8px',
                background: 'linear-gradient(135deg, #2563EB 0%, #7C3AED 100%)',
                flexShrink: 0,
              }}
            >
              <Security sx={{ fontSize: 18, color: '#fff' }} />
            </Box>
            <Box>
              <Typography
                sx={{
                  fontWeight: 700,
                  fontSize: '0.9375rem',
                  letterSpacing: '-0.02em',
                  lineHeight: 1.1,
                  color: 'text.primary',
                }}
              >
                ODIN
                <Box
                  component="span"
                  sx={{ fontWeight: 400, color: 'text.secondary' }}
                >
                  -AI
                </Box>
              </Typography>
              <Typography
                sx={{
                  fontSize: '0.6875rem',
                  color: 'text.secondary',
                  letterSpacing: '0.04em',
                  textTransform: 'uppercase',
                  lineHeight: 1,
                }}
              >
                입찰 인텔리전스
              </Typography>
            </Box>
          </Box>
        )}

        {!open && (
          <Box
            sx={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              width: 32,
              height: 32,
              borderRadius: '8px',
              background: 'linear-gradient(135deg, #2563EB 0%, #7C3AED 100%)',
            }}
          >
            <Security sx={{ fontSize: 18, color: '#fff' }} />
          </Box>
        )}

        <Tooltip title={open ? '사이드바 닫기' : '사이드바 열기'} placement="right">
          <IconButton
            onClick={handleDrawerToggle}
            size="small"
            sx={{
              ml: open ? 0 : 'auto',
              color: 'text.secondary',
              '&:hover': { color: 'text.primary' },
            }}
          >
            {open ? <ChevronLeft fontSize="small" /> : <ChevronRight fontSize="small" />}
          </IconButton>
        </Tooltip>
      </Box>

      <Divider />

      <List sx={{ px: 1, py: 1 }}>
        {menuItems.map((item) => {
          const isActive = location.pathname === item.path;
          return (
            <ListItem key={item.text} disablePadding sx={{ display: 'block', mb: 0.5 }}>
              <Tooltip title={!open ? item.text : ''} placement="right">
                <ListItemButton
                  selected={isActive}
                  onClick={() => handleNavigation(item.path)}
                  sx={{
                    minHeight: 40,
                    justifyContent: open ? 'initial' : 'center',
                    px: open ? 1.5 : 1,
                    borderRadius: '8px',
                    position: 'relative',
                    // Left accent bar for active item
                    '&.Mui-selected::before': {
                      content: '""',
                      position: 'absolute',
                      left: 0,
                      top: '20%',
                      height: '60%',
                      width: 3,
                      borderRadius: '0 3px 3px 0',
                      backgroundColor: 'primary.main',
                    },
                    '&.Mui-selected .MuiListItemIcon-root': {
                      color: 'primary.main',
                    },
                    '&.Mui-selected .MuiListItemText-primary': {
                      fontWeight: 600,
                      color: 'primary.main',
                    },
                  }}
                >
                  <ListItemIcon
                    sx={{
                      minWidth: 0,
                      mr: open ? 1.5 : 'auto',
                      justifyContent: 'center',
                      fontSize: 20,
                      color: isActive ? 'primary.main' : 'text.secondary',
                      transition: 'color 150ms',
                    }}
                  >
                    {item.icon}
                  </ListItemIcon>
                  <ListItemText
                    primary={item.text}
                    sx={{ opacity: open ? 1 : 0 }}
                    primaryTypographyProps={{
                      fontSize: '0.875rem',
                      fontWeight: isActive ? 600 : 400,
                      color: isActive ? 'primary.main' : 'text.primary',
                    }}
                  />
                </ListItemButton>
              </Tooltip>
            </ListItem>
          );
        })}
      </List>

      {/* 관리자 메뉴 - 관리자만 표시 */}
      {user?.role === 'admin' && (
        <>
          <Divider sx={{ mx: 1 }} />
          <List sx={{ px: 1, py: 1 }}>
            {open && (
              <ListItem disablePadding sx={{ display: 'block', mb: 0.5 }}>
                <Typography
                  sx={{
                    px: 1.5,
                    py: 0.5,
                    fontSize: '0.6875rem',
                    fontWeight: 600,
                    letterSpacing: '0.08em',
                    textTransform: 'uppercase',
                    color: 'text.secondary',
                  }}
                >
                  관리자
                </Typography>
              </ListItem>
            )}
            {adminMenuItems.map((item) => {
              const isActive = location.pathname === item.path;
              return (
                <ListItem key={item.text} disablePadding sx={{ display: 'block', mb: 0.5 }}>
                  <Tooltip title={!open ? item.text : ''} placement="right">
                    <ListItemButton
                      selected={isActive}
                      onClick={() => handleNavigation(item.path)}
                      sx={{
                        minHeight: 40,
                        justifyContent: open ? 'initial' : 'center',
                        px: open ? 1.5 : 1,
                        borderRadius: '8px',
                        position: 'relative',
                        '&.Mui-selected::before': {
                          content: '""',
                          position: 'absolute',
                          left: 0,
                          top: '20%',
                          height: '60%',
                          width: 3,
                          borderRadius: '0 3px 3px 0',
                          backgroundColor: 'primary.main',
                        },
                        '&.Mui-selected .MuiListItemIcon-root': {
                          color: 'primary.main',
                        },
                      }}
                    >
                      <ListItemIcon
                        sx={{
                          minWidth: 0,
                          mr: open ? 1.5 : 'auto',
                          justifyContent: 'center',
                          color: isActive ? 'primary.main' : 'text.secondary',
                          transition: 'color 150ms',
                        }}
                      >
                        {item.icon}
                      </ListItemIcon>
                      <ListItemText
                        primary={item.text}
                        sx={{ opacity: open ? 1 : 0 }}
                        primaryTypographyProps={{
                          fontSize: '0.875rem',
                          fontWeight: isActive ? 600 : 400,
                          color: isActive ? 'primary.main' : 'text.primary',
                        }}
                      />
                    </ListItemButton>
                  </Tooltip>
                </ListItem>
              );
            })}
          </List>
        </>
      )}
    </>
  );

  return (
    <Box sx={{ display: 'flex', height: '100vh', overflow: 'hidden' }}>
      <AppBar
        position="fixed"
        sx={{
          zIndex: (theme) => theme.zIndex.drawer + 1,
          transition: (theme) =>
            theme.transitions.create(['width', 'margin'], {
              easing: theme.transitions.easing.sharp,
              duration: theme.transitions.duration.leavingScreen,
            }),
          ...(open && {
            marginLeft: { sm: drawerWidth },
            width: { sm: `calc(100% - ${drawerWidth}px)` },
            transition: (theme: any) =>
              theme.transitions.create(['width', 'margin'], {
                easing: theme.transitions.easing.sharp,
                duration: theme.transitions.duration.enteringScreen,
              }),
          }),
        }}
      >
        <Toolbar>
          <IconButton
            color="inherit"
            aria-label="open drawer"
            onClick={handleDrawerToggle}
            edge="start"
            sx={{
              marginRight: 5,
              ...(!isMobile && open && { display: 'none' }),
            }}
          >
            <MenuIcon />
          </IconButton>
          {/* Brand mark — only visible when sidebar is collapsed */}
          <Box
            sx={{
              flexGrow: 1,
              display: 'flex',
              alignItems: 'center',
              gap: 1,
              // hide when drawer is open on desktop (sidebar already shows brand)
              ...(!isMobile && open && { visibility: 'hidden', width: 0, overflow: 'hidden', flexGrow: 0 }),
            }}
          >
            <Box
              sx={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                width: 28,
                height: 28,
                borderRadius: '7px',
                background: 'linear-gradient(135deg, #2563EB 0%, #7C3AED 100%)',
                flexShrink: 0,
              }}
            >
              <Security sx={{ fontSize: 16, color: '#fff' }} />
            </Box>
            <Typography
              noWrap
              component="div"
              sx={{
                fontWeight: 700,
                fontSize: '0.9375rem',
                letterSpacing: '-0.02em',
                color: 'text.primary',
                lineHeight: 1,
              }}
            >
              ODIN
              <Box
                component="span"
                sx={{ fontWeight: 400, color: 'text.secondary' }}
              >
                -AI
              </Box>
            </Typography>
          </Box>

          {/* Spacer when drawer is open on desktop */}
          {!isMobile && open && <Box sx={{ flexGrow: 1 }} />}

          <Tooltip title={resolvedMode === 'dark' ? '라이트 모드' : '다크 모드'}>
            <IconButton color="inherit" onClick={toggleTheme} sx={{ mr: 1 }}>
              {resolvedMode === 'dark' ? <LightMode /> : <DarkMode />}
            </IconButton>
          </Tooltip>

          <IconButton color="inherit" sx={{ mr: 2 }} onClick={() => navigate('/notification-inbox')}>
            <Badge badgeContent={unreadCount} color="secondary" invisible={unreadCount === 0}>
              <Notifications />
            </Badge>
          </IconButton>

          <IconButton onClick={handleProfileMenuOpen} sx={{ p: 0 }}>
            <Avatar sx={{ bgcolor: 'secondary.main' }}>
              {user?.name?.charAt(0).toUpperCase()}
            </Avatar>
          </IconButton>

          <Menu
            anchorEl={anchorEl}
            open={Boolean(anchorEl)}
            onClose={handleMenuClose}
            anchorOrigin={{
              vertical: 'bottom',
              horizontal: 'right',
            }}
            transformOrigin={{
              vertical: 'top',
              horizontal: 'right',
            }}
            slotProps={{
              paper: {
                sx: {
                  overflow: 'visible',
                  filter: 'drop-shadow(0px 2px 8px rgba(0,0,0,0.32))',
                  mt: 1.5,
                  '&:before': {
                    content: '""',
                    display: 'block',
                    position: 'absolute',
                    top: 0,
                    right: 14,
                    width: 10,
                    height: 10,
                    bgcolor: 'background.paper',
                    transform: 'translateY(-50%) rotate(45deg)',
                    zIndex: 0,
                  },
                },
              }
            }}
          >
            <MenuItem onClick={() => {
              handleNavigation('/profile');
              handleMenuClose();
            }}>
              <ListItemIcon>
                <Person fontSize="small" />
              </ListItemIcon>
              프로필
            </MenuItem>
            <MenuItem onClick={() => {
              handleNavigation('/subscription');
              handleMenuClose();
            }}>
              <ListItemIcon>
                <AccountBalance fontSize="small" />
              </ListItemIcon>
              구독 관리
            </MenuItem>
            <Divider />
            <MenuItem onClick={handleLogout}>
              <ListItemIcon>
                <Logout fontSize="small" />
              </ListItemIcon>
              로그아웃
            </MenuItem>
          </Menu>
        </Toolbar>
      </AppBar>

      {/* Mobile Drawer */}
      <Drawer
        variant="temporary"
        open={open}
        onClose={handleDrawerToggle}
        ModalProps={{ keepMounted: true }}
        sx={{
          display: { xs: 'block', sm: 'none' },
          '& .MuiDrawer-paper': {
            boxSizing: 'border-box',
            width: drawerWidth,
          },
        }}
      >
        {drawerContent}
      </Drawer>

      {/* Desktop Drawer */}
      <Drawer
        variant="permanent"
        open={open}
        sx={{
          display: { xs: 'none', sm: 'block' },
          width: drawerWidth,
          flexShrink: 0,
          whiteSpace: 'nowrap',
          boxSizing: 'border-box',
          ...(open && {
            width: drawerWidth,
            transition: (theme) =>
              theme.transitions.create('width', {
                easing: theme.transitions.easing.sharp,
                duration: theme.transitions.duration.enteringScreen,
              }),
            '& .MuiDrawer-paper': {
              width: drawerWidth,
              transition: (theme) =>
                theme.transitions.create('width', {
                  easing: theme.transitions.easing.sharp,
                  duration: theme.transitions.duration.enteringScreen,
                }),
            },
          }),
          ...(!open && {
            transition: (theme) =>
              theme.transitions.create('width', {
                easing: theme.transitions.easing.sharp,
                duration: theme.transitions.duration.leavingScreen,
              }),
            overflowX: 'hidden',
            width: (theme) => theme.spacing(7),
            '& .MuiDrawer-paper': {
              transition: (theme) =>
                theme.transitions.create('width', {
                  easing: theme.transitions.easing.sharp,
                  duration: theme.transitions.duration.leavingScreen,
                }),
              overflowX: 'hidden',
              width: (theme) => theme.spacing(7),
            },
          }),
        }}
      >
        {drawerContent}
      </Drawer>

      <Box
        component="main"
        sx={{
          flexGrow: 1,
          p: 3,
          width: { sm: `calc(100% - ${open ? drawerWidth : 56}px)` },
          height: '100vh',
          overflow: 'auto',
        }}
      >
        <Toolbar />
        <AnimatePresence mode="wait">
          <motion.div
            key={location.pathname}
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -8 }}
            transition={{ duration: 0.2, ease: 'easeInOut' }}
          >
            <Outlet />
          </motion.div>
        </AnimatePresence>
      </Box>
    </Box>
  );
};

export default MainLayout;