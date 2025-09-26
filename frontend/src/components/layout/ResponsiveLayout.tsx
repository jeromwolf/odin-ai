import React, { useState } from 'react';
import {
  Box,
  Drawer,
  AppBar,
  Toolbar,
  IconButton,
  Typography,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  ListItemButton,
  Divider,
  useTheme,
  useMediaQuery,
  Container,
  Badge,
  Avatar,
  Menu,
  MenuItem,
} from '@mui/material';
import {
  Menu as MenuIcon,
  Dashboard as DashboardIcon,
  Search as SearchIcon,
  Bookmark as BookmarkIcon,
  TrendingUp as TrendingUpIcon,
  Notifications as NotificationsIcon,
  Settings as SettingsIcon,
  Person as PersonIcon,
  Logout as LogoutIcon,
  ChevronLeft as ChevronLeftIcon,
} from '@mui/icons-material';
import { styled } from '@mui/material/styles';
import { useNavigate, useLocation } from 'react-router-dom';
import DarkModeToggle from '../DarkModeToggle';

const drawerWidth = 280;
const mobileDrawerWidth = 240;

// 스타일 컴포넌트
const Main = styled('main', { shouldForwardProp: (prop) => prop !== 'open' })<{
  open?: boolean;
}>(({ theme, open }) => ({
  flexGrow: 1,
  padding: theme.spacing(3),
  transition: theme.transitions.create('margin', {
    easing: theme.transitions.easing.sharp,
    duration: theme.transitions.duration.leavingScreen,
  }),
  marginLeft: 0,
  [theme.breakpoints.up('md')]: {
    marginLeft: open ? drawerWidth : 0,
  },
  [theme.breakpoints.down('md')]: {
    padding: theme.spacing(2),
  },
  [theme.breakpoints.down('sm')]: {
    padding: theme.spacing(1),
  },
}));

const DrawerHeader = styled('div')(({ theme }) => ({
  display: 'flex',
  alignItems: 'center',
  padding: theme.spacing(0, 1),
  ...theme.mixins.toolbar,
  justifyContent: 'space-between',
}));

const StyledAppBar = styled(AppBar, {
  shouldForwardProp: (prop) => prop !== 'open',
})<{ open?: boolean }>(({ theme, open }) => ({
  transition: theme.transitions.create(['margin', 'width'], {
    easing: theme.transitions.easing.sharp,
    duration: theme.transitions.duration.leavingScreen,
  }),
  [theme.breakpoints.up('md')]: {
    width: open ? `calc(100% - ${drawerWidth}px)` : '100%',
    marginLeft: open ? drawerWidth : 0,
  },
}));

const StyledDrawer = styled(Drawer)(({ theme }) => ({
  '& .MuiDrawer-paper': {
    width: drawerWidth,
    boxSizing: 'border-box',
    background: theme.palette.background.default,
    borderRight: `1px solid ${theme.palette.divider}`,
    [theme.breakpoints.down('md')]: {
      width: mobileDrawerWidth,
    },
  },
}));

// 네비게이션 메뉴 아이템
const menuItems = [
  { text: '대시보드', icon: <DashboardIcon />, path: '/dashboard' },
  { text: '검색', icon: <SearchIcon />, path: '/search' },
  { text: '북마크', icon: <BookmarkIcon />, path: '/bookmarks' },
  { text: 'AI 추천', icon: <TrendingUpIcon />, path: '/recommendations' },
  { text: '알림', icon: <NotificationsIcon />, path: '/notifications' },
  { text: '설정', icon: <SettingsIcon />, path: '/settings' },
];

interface ResponsiveLayoutProps {
  children: React.ReactNode;
  title?: string;
  user?: {
    name: string;
    email: string;
    avatar?: string;
  };
  notifications?: number;
}

const ResponsiveLayout: React.FC<ResponsiveLayoutProps> = ({
  children,
  title = 'ODIN-AI',
  user,
  notifications = 0,
}) => {
  const theme = useTheme();
  const navigate = useNavigate();
  const location = useLocation();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));
  const isTablet = useMediaQuery(theme.breakpoints.between('sm', 'md'));

  const [drawerOpen, setDrawerOpen] = useState(!isMobile);
  const [userMenuAnchor, setUserMenuAnchor] = useState<null | HTMLElement>(null);

  const handleDrawerToggle = () => {
    setDrawerOpen(!drawerOpen);
  };

  const handleUserMenuOpen = (event: React.MouseEvent<HTMLElement>) => {
    setUserMenuAnchor(event.currentTarget);
  };

  const handleUserMenuClose = () => {
    setUserMenuAnchor(null);
  };

  const handleLogout = () => {
    // 로그아웃 처리
    localStorage.removeItem('token');
    navigate('/login');
  };

  const DrawerContent = (
    <>
      <DrawerHeader>
        <Typography variant="h6" fontWeight={700} color="primary">
          ODIN-AI
        </Typography>
        {isMobile && (
          <IconButton onClick={handleDrawerToggle}>
            <ChevronLeftIcon />
          </IconButton>
        )}
      </DrawerHeader>
      <Divider />

      {/* 사용자 프로필 (모바일) */}
      {isMobile && user && (
        <>
          <Box sx={{ p: 2, textAlign: 'center' }}>
            <Avatar
              src={user.avatar}
              sx={{
                width: 64,
                height: 64,
                margin: '0 auto',
                mb: 1,
                bgcolor: theme.palette.primary.main,
              }}
            >
              {user.name[0]}
            </Avatar>
            <Typography variant="subtitle1" fontWeight={600}>
              {user.name}
            </Typography>
            <Typography variant="caption" color="text.secondary">
              {user.email}
            </Typography>
          </Box>
          <Divider />
        </>
      )}

      {/* 네비게이션 메뉴 */}
      <List sx={{ px: 1 }}>
        {menuItems.map((item) => (
          <ListItem key={item.text} disablePadding sx={{ mb: 0.5 }}>
            <ListItemButton
              selected={location.pathname === item.path}
              onClick={() => {
                navigate(item.path);
                if (isMobile) setDrawerOpen(false);
              }}
              sx={{
                borderRadius: 2,
                '&.Mui-selected': {
                  backgroundColor: theme.palette.action.selected,
                  '&:hover': {
                    backgroundColor: theme.palette.action.selected,
                  },
                },
              }}
            >
              <ListItemIcon
                sx={{
                  color: location.pathname === item.path
                    ? theme.palette.primary.main
                    : theme.palette.text.secondary,
                }}
              >
                {item.icon}
              </ListItemIcon>
              <ListItemText
                primary={item.text}
                primaryTypographyProps={{
                  fontSize: isTablet ? '0.875rem' : '1rem',
                }}
              />
              {item.text === '알림' && notifications > 0 && (
                <Badge badgeContent={notifications} color="error" />
              )}
            </ListItemButton>
          </ListItem>
        ))}
      </List>

      {/* 하단 메뉴 (데스크톱) */}
      {!isMobile && (
        <Box sx={{ mt: 'auto', p: 2 }}>
          <Divider sx={{ mb: 2 }} />
          <ListItemButton
            onClick={handleLogout}
            sx={{
              borderRadius: 2,
              color: theme.palette.error.main,
              '&:hover': {
                backgroundColor: theme.palette.error.light + '20',
              },
            }}
          >
            <ListItemIcon sx={{ color: 'inherit' }}>
              <LogoutIcon />
            </ListItemIcon>
            <ListItemText primary="로그아웃" />
          </ListItemButton>
        </Box>
      )}
    </>
  );

  return (
    <Box sx={{ display: 'flex', minHeight: '100vh' }}>
      {/* 앱바 */}
      <StyledAppBar position="fixed" open={!isMobile && drawerOpen}>
        <Toolbar>
          <IconButton
            color="inherit"
            aria-label="open drawer"
            onClick={handleDrawerToggle}
            edge="start"
            sx={{
              mr: 2,
              ...((!isMobile && drawerOpen) && { display: 'none' }),
            }}
          >
            <MenuIcon />
          </IconButton>

          <Typography
            variant="h6"
            noWrap
            component="div"
            sx={{ flexGrow: 1, fontWeight: 600 }}
          >
            {title}
          </Typography>

          {/* 데스크톱 툴바 아이템 */}
          {!isMobile && (
            <>
              <IconButton color="inherit" sx={{ mr: 1 }}>
                <Badge badgeContent={notifications} color="error">
                  <NotificationsIcon />
                </Badge>
              </IconButton>

              {user && (
                <IconButton
                  onClick={handleUserMenuOpen}
                  sx={{ ml: 1 }}
                >
                  <Avatar
                    src={user.avatar}
                    sx={{
                      width: 32,
                      height: 32,
                      bgcolor: theme.palette.primary.main,
                    }}
                  >
                    {user.name[0]}
                  </Avatar>
                </IconButton>
              )}
            </>
          )}
        </Toolbar>
      </StyledAppBar>

      {/* 사용자 메뉴 */}
      <Menu
        anchorEl={userMenuAnchor}
        open={Boolean(userMenuAnchor)}
        onClose={handleUserMenuClose}
        transformOrigin={{ horizontal: 'right', vertical: 'top' }}
        anchorOrigin={{ horizontal: 'right', vertical: 'bottom' }}
      >
        <MenuItem onClick={() => { navigate('/profile'); handleUserMenuClose(); }}>
          <ListItemIcon>
            <PersonIcon fontSize="small" />
          </ListItemIcon>
          프로필
        </MenuItem>
        <MenuItem onClick={() => { navigate('/settings'); handleUserMenuClose(); }}>
          <ListItemIcon>
            <SettingsIcon fontSize="small" />
          </ListItemIcon>
          설정
        </MenuItem>
        <Divider />
        <MenuItem onClick={handleLogout}>
          <ListItemIcon>
            <LogoutIcon fontSize="small" />
          </ListItemIcon>
          로그아웃
        </MenuItem>
      </Menu>

      {/* 사이드바 */}
      <StyledDrawer
        variant={isMobile ? 'temporary' : 'persistent'}
        anchor="left"
        open={drawerOpen}
        onClose={handleDrawerToggle}
        ModalProps={{
          keepMounted: true, // 모바일 성능 향상
        }}
      >
        {DrawerContent}
      </StyledDrawer>

      {/* 메인 콘텐츠 */}
      <Main open={!isMobile && drawerOpen}>
        <DrawerHeader />
        <Container
          maxWidth={false}
          sx={{
            px: { xs: 0, sm: 2, md: 3 },
            py: { xs: 1, sm: 2, md: 3 },
          }}
        >
          {children}
        </Container>
      </Main>

      {/* 다크모드 토글 */}
      <DarkModeToggle />
    </Box>
  );
};

export default ResponsiveLayout;