import React, { useState } from 'react';
import { Link as RouterLink, useNavigate, useLocation } from 'react-router-dom';
import {
  Box,
  Button,
  TextField,
  Link,
  Alert,
  IconButton,
  InputAdornment,
  FormControlLabel,
  Checkbox,
  CircularProgress,
  Typography,
  Divider,
} from '@mui/material';
import { Visibility, VisibilityOff, LockOutlined } from '@mui/icons-material';
import { useForm } from 'react-hook-form';
import { useAuth } from '../contexts/AuthContext';

interface LoginFormData {
  email: string;
  password: string;
  rememberMe: boolean;
}

const Login: React.FC = () => {
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();
  const { login } = useAuth();
  const from = location.state?.from?.pathname || '/dashboard';

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<LoginFormData>({
    defaultValues: {
      email: '',
      password: '',
      rememberMe: false,
    },
  });

  const onSubmit = async (data: LoginFormData) => {
    setError(null);
    setIsLoading(true);

    try {
      await login(data.email, data.password);
      navigate(from, { replace: true });
    } catch (err: any) {
      setError(
        err.response?.data?.detail ||
          err.message ||
          '로그인에 실패했습니다. 이메일과 비밀번호를 확인해주세요.'
      );
    } finally {
      setIsLoading(false);
    }
  };

  const handleClickShowPassword = () => {
    setShowPassword(!showPassword);
  };

  return (
    <Box>
      {/* Heading */}
      <Box sx={{ mb: 4 }}>
        <Box
          sx={{
            width: 44,
            height: 44,
            borderRadius: '12px',
            background: 'linear-gradient(135deg, #2563EB 0%, #7C3AED 100%)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            mb: 2.5,
          }}
        >
          <LockOutlined sx={{ color: '#fff', fontSize: 22 }} />
        </Box>

        <Typography
          variant="h5"
          sx={{
            fontWeight: 700,
            color: '#0F172A',
            letterSpacing: '-0.01em',
            mb: 0.6,
          }}
        >
          다시 오신 것을 환영합니다
        </Typography>
        <Typography
          sx={{
            color: '#64748B',
            fontSize: '0.875rem',
          }}
        >
          계정에 로그인하여 서비스를 이용하세요
        </Typography>
      </Box>

      {/* Error alert */}
      {error && (
        <Alert
          severity="error"
          sx={{
            mb: 2.5,
            borderRadius: '10px',
            fontSize: '0.825rem',
            '& .MuiAlert-icon': { fontSize: 18 },
          }}
        >
          {error}
        </Alert>
      )}

      {/* Form */}
      <form onSubmit={handleSubmit(onSubmit)} noValidate>
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 0.5 }}>
          {/* Email */}
          <Box>
            <Typography
              component="label"
              htmlFor="email"
              sx={{
                display: 'block',
                fontSize: '0.8rem',
                fontWeight: 600,
                color: '#374151',
                mb: 0.75,
                letterSpacing: '0.01em',
              }}
            >
              이메일
            </Typography>
            <TextField
              {...register('email', {
                required: '이메일을 입력해주세요',
                pattern: {
                  value: /^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}$/i,
                  message: '올바른 이메일 형식이 아닙니다',
                },
              })}
              required
              fullWidth
              id="email"
              name="email"
              autoComplete="email"
              autoFocus
              placeholder="name@company.com"
              error={!!errors.email}
              helperText={errors.email?.message}
              disabled={isLoading}
              sx={{
                '& .MuiOutlinedInput-root': {
                  borderRadius: '10px',
                  fontSize: '0.875rem',
                  bgcolor: '#F8FAFC',
                  transition: 'all 150ms ease',
                  '& fieldset': {
                    borderColor: '#E2E8F0',
                  },
                  '&:hover fieldset': {
                    borderColor: '#CBD5E1',
                  },
                  '&.Mui-focused': {
                    bgcolor: '#fff',
                    '& fieldset': {
                      borderColor: '#2563EB',
                      borderWidth: '1.5px',
                    },
                  },
                  '&.Mui-error fieldset': {
                    borderColor: '#EF4444',
                  },
                },
                '& .MuiInputBase-input': {
                  py: 1.4,
                  px: 1.75,
                },
                '& .MuiFormHelperText-root': {
                  fontSize: '0.75rem',
                  mt: 0.5,
                  ml: 0.25,
                },
              }}
            />
          </Box>

          {/* Password */}
          <Box sx={{ mt: 1.5 }}>
            <Box
              sx={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                mb: 0.75,
              }}
            >
              <Typography
                component="label"
                htmlFor="password"
                sx={{
                  display: 'block',
                  fontSize: '0.8rem',
                  fontWeight: 600,
                  color: '#374151',
                  letterSpacing: '0.01em',
                }}
              >
                비밀번호
              </Typography>
              <Link
                component={RouterLink}
                to="/forgot-password"
                sx={{
                  fontSize: '0.775rem',
                  color: '#2563EB',
                  textDecoration: 'none',
                  fontWeight: 500,
                  '&:hover': {
                    textDecoration: 'underline',
                  },
                }}
              >
                비밀번호 찾기
              </Link>
            </Box>
            <TextField
              {...register('password', {
                required: '비밀번호를 입력해주세요',
                minLength: {
                  value: 6,
                  message: '비밀번호는 최소 6자 이상이어야 합니다',
                },
              })}
              required
              fullWidth
              name="password"
              type={showPassword ? 'text' : 'password'}
              id="password"
              autoComplete="current-password"
              placeholder="비밀번호를 입력하세요"
              error={!!errors.password}
              helperText={errors.password?.message}
              disabled={isLoading}
              InputProps={{
                endAdornment: (
                  <InputAdornment position="end">
                    <IconButton
                      aria-label="toggle password visibility"
                      onClick={handleClickShowPassword}
                      edge="end"
                      size="small"
                      sx={{
                        color: '#94A3B8',
                        mr: 0.25,
                        '&:hover': { color: '#475569' },
                      }}
                    >
                      {showPassword ? (
                        <VisibilityOff sx={{ fontSize: 18 }} />
                      ) : (
                        <Visibility sx={{ fontSize: 18 }} />
                      )}
                    </IconButton>
                  </InputAdornment>
                ),
              }}
              sx={{
                '& .MuiOutlinedInput-root': {
                  borderRadius: '10px',
                  fontSize: '0.875rem',
                  bgcolor: '#F8FAFC',
                  transition: 'all 150ms ease',
                  '& fieldset': {
                    borderColor: '#E2E8F0',
                  },
                  '&:hover fieldset': {
                    borderColor: '#CBD5E1',
                  },
                  '&.Mui-focused': {
                    bgcolor: '#fff',
                    '& fieldset': {
                      borderColor: '#2563EB',
                      borderWidth: '1.5px',
                    },
                  },
                  '&.Mui-error fieldset': {
                    borderColor: '#EF4444',
                  },
                },
                '& .MuiInputBase-input': {
                  py: 1.4,
                  px: 1.75,
                },
                '& .MuiFormHelperText-root': {
                  fontSize: '0.75rem',
                  mt: 0.5,
                  ml: 0.25,
                },
              }}
            />
          </Box>

          {/* Remember me */}
          <FormControlLabel
            control={
              <Checkbox
                {...register('rememberMe')}
                size="small"
                disabled={isLoading}
                sx={{
                  color: '#CBD5E1',
                  '&.Mui-checked': {
                    color: '#2563EB',
                  },
                  p: 0.75,
                }}
              />
            }
            label={
              <Typography sx={{ fontSize: '0.825rem', color: '#4B5563' }}>
                로그인 상태 유지
              </Typography>
            }
            sx={{ mt: 0.5, ml: 0 }}
          />

          {/* Submit */}
          <Button
            type="submit"
            fullWidth
            variant="contained"
            disabled={isLoading}
            sx={{
              mt: 1,
              py: 1.4,
              borderRadius: '10px',
              background: isLoading
                ? undefined
                : 'linear-gradient(135deg, #2563EB 0%, #4F46E5 100%)',
              boxShadow: '0 1px 3px 0 rgba(37,99,235,0.3), 0 1px 2px -1px rgba(37,99,235,0.2)',
              fontSize: '0.9rem',
              fontWeight: 600,
              letterSpacing: '0.01em',
              textTransform: 'none',
              transition: 'all 200ms ease',
              '&:hover': {
                background: 'linear-gradient(135deg, #1D4ED8 0%, #4338CA 100%)',
                boxShadow:
                  '0 4px 6px -1px rgba(37,99,235,0.35), 0 2px 4px -2px rgba(37,99,235,0.25)',
                transform: 'translateY(-1px)',
              },
              '&:active': {
                transform: 'translateY(0)',
              },
              '&.Mui-disabled': {
                background: '#E2E8F0',
                color: '#94A3B8',
                boxShadow: 'none',
              },
            }}
          >
            {isLoading ? (
              <CircularProgress size={20} sx={{ color: '#94A3B8' }} />
            ) : (
              '로그인'
            )}
          </Button>
        </Box>
      </form>

      {/* Divider */}
      <Divider sx={{ my: 3.5 }}>
        <Typography sx={{ color: '#94A3B8', fontSize: '0.75rem', px: 1 }}>
          또는
        </Typography>
      </Divider>

      {/* Register link */}
      <Box
        sx={{
          textAlign: 'center',
          p: 2,
          borderRadius: '12px',
          border: '1px solid #E2E8F0',
          bgcolor: '#F8FAFC',
        }}
      >
        <Typography sx={{ fontSize: '0.85rem', color: '#64748B' }}>
          아직 계정이 없으신가요?{' '}
          <Link
            component={RouterLink}
            to="/register"
            sx={{
              fontWeight: 600,
              color: '#2563EB',
              textDecoration: 'none',
              '&:hover': {
                textDecoration: 'underline',
              },
            }}
          >
            무료로 시작하기
          </Link>
        </Typography>
      </Box>

      {/* Footer note */}
      <Typography
        sx={{
          mt: 3,
          textAlign: 'center',
          fontSize: '0.72rem',
          color: '#94A3B8',
          lineHeight: 1.6,
        }}
      >
        로그인하면 ODIN-AI의{' '}
        <Link
          href="#"
          sx={{ color: '#94A3B8', textDecorationColor: '#CBD5E1' }}
        >
          이용약관
        </Link>{' '}
        및{' '}
        <Link
          href="#"
          sx={{ color: '#94A3B8', textDecorationColor: '#CBD5E1' }}
        >
          개인정보처리방침
        </Link>
        에 동의하는 것으로 간주됩니다.
      </Typography>
    </Box>
  );
};

export default Login;
