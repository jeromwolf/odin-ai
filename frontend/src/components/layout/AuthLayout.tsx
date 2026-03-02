import React from 'react';
import { Outlet } from 'react-router-dom';
import {
  Box,
  Typography,
  useMediaQuery,
  useTheme,
} from '@mui/material';
import {
  AutoAwesome,
  NotificationsActive,
  Psychology,
  AccountTree,
} from '@mui/icons-material';

const features = [
  {
    icon: <Psychology sx={{ fontSize: 20 }} />,
    title: 'AI 기반 입찰 분석',
    description: '머신러닝으로 최적 입찰 기회를 자동 탐지',
  },
  {
    icon: <NotificationsActive sx={{ fontSize: 20 }} />,
    title: '실시간 공고 알림',
    description: '조건 맞춤 입찰공고를 즉시 이메일로 수신',
  },
  {
    icon: <AutoAwesome sx={{ fontSize: 20 }} />,
    title: '맞춤형 추천 시스템',
    description: '업종·지역·규모 기반 개인화 공고 추천',
  },
  {
    icon: <AccountTree sx={{ fontSize: 20 }} />,
    title: '지식 그래프 탐색',
    description: '발주기관·업종·키워드의 연결망을 시각화',
  },
];

const AuthLayout: React.FC = () => {
  const theme = useTheme();
  const isDesktop = useMediaQuery(theme.breakpoints.up('md'));

  return (
    <Box
      sx={{
        minHeight: '100vh',
        display: 'flex',
        flexDirection: { xs: 'column', md: 'row' },
        bgcolor: '#F8FAFC',
      }}
    >
      {/* ── Left hero panel ─────────────────────────────────────── */}
      {isDesktop && (
        <Box
          sx={{
            flex: '0 0 45%',
            position: 'relative',
            display: 'flex',
            flexDirection: 'column',
            justifyContent: 'center',
            px: 7,
            py: 8,
            background:
              'linear-gradient(145deg, #1E40AF 0%, #2563EB 35%, #4F46E5 65%, #7C3AED 100%)',
            overflow: 'hidden',
          }}
        >
          {/* Decorative dot grid */}
          <Box
            sx={{
              position: 'absolute',
              inset: 0,
              backgroundImage:
                'radial-gradient(circle, rgba(255,255,255,0.12) 1px, transparent 1px)',
              backgroundSize: '28px 28px',
              pointerEvents: 'none',
            }}
          />

          {/* Soft glow circles */}
          <Box
            sx={{
              position: 'absolute',
              top: '-80px',
              right: '-80px',
              width: 320,
              height: 320,
              borderRadius: '50%',
              background:
                'radial-gradient(circle, rgba(139,92,246,0.35) 0%, transparent 70%)',
              pointerEvents: 'none',
            }}
          />
          <Box
            sx={{
              position: 'absolute',
              bottom: '-60px',
              left: '-60px',
              width: 260,
              height: 260,
              borderRadius: '50%',
              background:
                'radial-gradient(circle, rgba(37,99,235,0.45) 0%, transparent 70%)',
              pointerEvents: 'none',
            }}
          />

          {/* Content */}
          <Box sx={{ position: 'relative', zIndex: 1 }}>
            {/* Logo mark */}
            <Box
              sx={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: 1.5,
                mb: 5,
              }}
            >
              <Box
                sx={{
                  width: 40,
                  height: 40,
                  borderRadius: '10px',
                  background:
                    'linear-gradient(135deg, rgba(255,255,255,0.3) 0%, rgba(255,255,255,0.1) 100%)',
                  border: '1px solid rgba(255,255,255,0.25)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  backdropFilter: 'blur(4px)',
                }}
              >
                <AutoAwesome sx={{ color: '#fff', fontSize: 20 }} />
              </Box>
              <Typography
                sx={{
                  fontSize: '1.15rem',
                  fontWeight: 700,
                  color: '#fff',
                  letterSpacing: '0.04em',
                  textTransform: 'uppercase',
                }}
              >
                ODIN-AI
              </Typography>
            </Box>

            {/* Headline */}
            <Typography
              variant="h3"
              sx={{
                fontWeight: 800,
                color: '#fff',
                lineHeight: 1.2,
                mb: 1.5,
                fontSize: { md: '2rem', lg: '2.4rem' },
              }}
            >
              공공입찰 AI 분석
              <br />
              플랫폼
            </Typography>

            <Typography
              sx={{
                color: 'rgba(255,255,255,0.72)',
                fontSize: '1rem',
                lineHeight: 1.6,
                mb: 5.5,
                maxWidth: 340,
              }}
            >
              수천 개의 공공 입찰공고를 AI가 분석하여
              <br />
              귀사에 가장 적합한 기회를 찾아드립니다.
            </Typography>

            {/* Feature list */}
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2.5 }}>
              {features.map((f) => (
                <Box
                  key={f.title}
                  sx={{
                    display: 'flex',
                    alignItems: 'flex-start',
                    gap: 2,
                  }}
                >
                  <Box
                    sx={{
                      mt: '2px',
                      flexShrink: 0,
                      width: 34,
                      height: 34,
                      borderRadius: '8px',
                      background: 'rgba(255,255,255,0.15)',
                      border: '1px solid rgba(255,255,255,0.18)',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      color: '#fff',
                    }}
                  >
                    {f.icon}
                  </Box>
                  <Box>
                    <Typography
                      sx={{
                        fontWeight: 600,
                        color: '#fff',
                        fontSize: '0.9rem',
                        lineHeight: 1.3,
                        mb: 0.3,
                      }}
                    >
                      {f.title}
                    </Typography>
                    <Typography
                      sx={{
                        color: 'rgba(255,255,255,0.62)',
                        fontSize: '0.78rem',
                        lineHeight: 1.5,
                      }}
                    >
                      {f.description}
                    </Typography>
                  </Box>
                </Box>
              ))}
            </Box>

            {/* Bottom badge */}
            <Box
              sx={{
                mt: 6,
                display: 'inline-flex',
                alignItems: 'center',
                gap: 1,
                px: 2,
                py: 0.75,
                borderRadius: '20px',
                background: 'rgba(255,255,255,0.1)',
                border: '1px solid rgba(255,255,255,0.15)',
              }}
            >
              <Box
                sx={{
                  width: 7,
                  height: 7,
                  borderRadius: '50%',
                  bgcolor: '#34D399',
                  boxShadow: '0 0 6px #34D399',
                }}
              />
              <Typography
                sx={{
                  color: 'rgba(255,255,255,0.80)',
                  fontSize: '0.72rem',
                  fontWeight: 500,
                  letterSpacing: '0.02em',
                }}
              >
                실시간 데이터 수집 · 24시간 분석
              </Typography>
            </Box>
          </Box>
        </Box>
      )}

      {/* ── Right form panel ────────────────────────────────────── */}
      <Box
        sx={{
          flex: 1,
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'center',
          alignItems: 'center',
          px: { xs: 3, sm: 6, md: 7, lg: 9 },
          py: { xs: 5, md: 6 },
          bgcolor: '#fff',
          minHeight: { xs: '100vh', md: 'auto' },
        }}
      >
        {/* Mobile-only logo */}
        {!isDesktop && (
          <Box
            sx={{
              display: 'flex',
              alignItems: 'center',
              gap: 1.2,
              mb: 4,
            }}
          >
            <Box
              sx={{
                width: 36,
                height: 36,
                borderRadius: '9px',
                background: 'linear-gradient(135deg, #2563EB 0%, #7C3AED 100%)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}
            >
              <AutoAwesome sx={{ color: '#fff', fontSize: 18 }} />
            </Box>
            <Typography
              sx={{
                fontSize: '1.1rem',
                fontWeight: 800,
                color: '#1E293B',
                letterSpacing: '0.05em',
                textTransform: 'uppercase',
              }}
            >
              ODIN-AI
            </Typography>
          </Box>
        )}

        <Box sx={{ width: '100%', maxWidth: 400 }}>
          <Outlet />
        </Box>
      </Box>
    </Box>
  );
};

export default AuthLayout;
