import React, { useState } from 'react';
import { Link as RouterLink, useNavigate } from 'react-router-dom';
import {
  Box,
  Button,
  TextField,
  Link,
  Grid,
  Alert,
  IconButton,
  InputAdornment,
  FormControlLabel,
  Checkbox,
  CircularProgress,
  Stepper,
  Step,
  StepLabel,
  Typography,
} from '@mui/material';
import { Visibility, VisibilityOff } from '@mui/icons-material';
import { useForm } from 'react-hook-form';
import { useAuth } from '../contexts/AuthContext';

interface RegisterFormData {
  email: string;
  password: string;
  passwordConfirm: string;
  name: string;
  company: string;
  phone: string;
  agreeTerms: boolean;
  agreeMarketing: boolean;
}

const steps = ['기본 정보', '회사 정보', '약관 동의'];

const Register: React.FC = () => {
  const [activeStep, setActiveStep] = useState(0);
  const [showPassword, setShowPassword] = useState(false);
  const [showPasswordConfirm, setShowPasswordConfirm] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const navigate = useNavigate();
  const { register: registerUser } = useAuth();

  const {
    register,
    handleSubmit,
    formState: { errors },
    watch,
    trigger,
  } = useForm<RegisterFormData>({
    defaultValues: {
      email: '',
      password: '',
      passwordConfirm: '',
      name: '',
      company: '',
      phone: '',
      agreeTerms: false,
      agreeMarketing: false,
    },
  });

  const password = watch('password');

  const handleNext = async () => {
    let fieldsToValidate: (keyof RegisterFormData)[] = [];

    if (activeStep === 0) {
      fieldsToValidate = ['email', 'password', 'passwordConfirm', 'name'];
    } else if (activeStep === 1) {
      fieldsToValidate = ['company', 'phone'];
    }

    const isValid = await trigger(fieldsToValidate);
    if (isValid) {
      setActiveStep((prevStep) => prevStep + 1);
    }
  };

  const handleBack = () => {
    setActiveStep((prevStep) => prevStep - 1);
  };

  const onSubmit = async (data: RegisterFormData) => {
    if (!data.agreeTerms) {
      setError('서비스 이용약관에 동의해주세요.');
      return;
    }

    setError(null);
    setIsLoading(true);

    try {
      await registerUser({
        email: data.email,
        password: data.password,
        name: data.name,
        company: data.company,
        phone: data.phone,
        marketing_consent: data.agreeMarketing,
      });
      navigate('/dashboard');
    } catch (err: any) {
      setError(
        err.response?.data?.detail ||
        err.message ||
        '회원가입에 실패했습니다. 다시 시도해주세요.'
      );
    } finally {
      setIsLoading(false);
    }
  };

  const getStepContent = (step: number) => {
    switch (step) {
      case 0:
        return (
          <>
            <TextField
              {...register('email', {
                required: '이메일을 입력해주세요',
                pattern: {
                  value: /^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}$/i,
                  message: '올바른 이메일 형식이 아닙니다',
                },
              })}
              margin="normal"
              required
              fullWidth
              label="이메일"
              autoComplete="email"
              error={!!errors.email}
              helperText={errors.email?.message}
            />

            <TextField
              {...register('password', {
                required: '비밀번호를 입력해주세요',
                minLength: {
                  value: 8,
                  message: '비밀번호는 최소 8자 이상이어야 합니다',
                },
                pattern: {
                  value: /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]/,
                  message: '비밀번호는 대소문자, 숫자, 특수문자를 포함해야 합니다',
                },
              })}
              margin="normal"
              required
              fullWidth
              label="비밀번호"
              type={showPassword ? 'text' : 'password'}
              autoComplete="new-password"
              error={!!errors.password}
              helperText={errors.password?.message}
              InputProps={{
                endAdornment: (
                  <InputAdornment position="end">
                    <IconButton
                      onClick={() => setShowPassword(!showPassword)}
                      edge="end"
                    >
                      {showPassword ? <VisibilityOff /> : <Visibility />}
                    </IconButton>
                  </InputAdornment>
                ),
              }}
            />

            <TextField
              {...register('passwordConfirm', {
                required: '비밀번호를 다시 입력해주세요',
                validate: (value) =>
                  value === password || '비밀번호가 일치하지 않습니다',
              })}
              margin="normal"
              required
              fullWidth
              label="비밀번호 확인"
              type={showPasswordConfirm ? 'text' : 'password'}
              error={!!errors.passwordConfirm}
              helperText={errors.passwordConfirm?.message}
              InputProps={{
                endAdornment: (
                  <InputAdornment position="end">
                    <IconButton
                      onClick={() => setShowPasswordConfirm(!showPasswordConfirm)}
                      edge="end"
                    >
                      {showPasswordConfirm ? <VisibilityOff /> : <Visibility />}
                    </IconButton>
                  </InputAdornment>
                ),
              }}
            />

            <TextField
              {...register('name', {
                required: '이름을 입력해주세요',
                minLength: {
                  value: 2,
                  message: '이름은 최소 2자 이상이어야 합니다',
                },
              })}
              margin="normal"
              required
              fullWidth
              label="이름"
              autoComplete="name"
              error={!!errors.name}
              helperText={errors.name?.message}
            />
          </>
        );

      case 1:
        return (
          <>
            <TextField
              {...register('company', {
                required: '회사명을 입력해주세요',
              })}
              margin="normal"
              required
              fullWidth
              label="회사명"
              autoComplete="organization"
              error={!!errors.company}
              helperText={errors.company?.message}
            />

            <TextField
              {...register('phone', {
                required: '연락처를 입력해주세요',
                pattern: {
                  value: /^01[0-9]-?[0-9]{3,4}-?[0-9]{4}$/,
                  message: '올바른 휴대폰 번호 형식이 아닙니다',
                },
              })}
              margin="normal"
              required
              fullWidth
              label="휴대폰 번호"
              placeholder="010-1234-5678"
              autoComplete="tel"
              error={!!errors.phone}
              helperText={errors.phone?.message}
            />
          </>
        );

      case 2:
        return (
          <>
            <Box sx={{ mb: 2 }}>
              <Typography variant="body2" sx={{ mb: 1 }}>
                서비스 이용약관 및 개인정보 처리방침에 동의해주세요.
              </Typography>
              <Box
                sx={{
                  p: 2,
                  border: '1px solid #ddd',
                  borderRadius: 1,
                  maxHeight: 200,
                  overflowY: 'auto',
                  mb: 1,
                }}
              >
                <Typography variant="caption">
                  [서비스 이용약관 내용]
                  당사는 개인정보를 안전하게 보호하며...
                </Typography>
              </Box>
              <FormControlLabel
                control={
                  <Checkbox
                    {...register('agreeTerms', {
                      required: '서비스 이용약관에 동의해주세요',
                    })}
                    color="primary"
                  />
                }
                label="(필수) 서비스 이용약관에 동의합니다"
              />
              {errors.agreeTerms && (
                <Typography variant="caption" color="error">
                  {errors.agreeTerms.message}
                </Typography>
              )}
            </Box>

            <FormControlLabel
              control={
                <Checkbox {...register('agreeMarketing')} color="primary" />
              }
              label="(선택) 마케팅 정보 수신에 동의합니다"
            />
          </>
        );

      default:
        return 'Unknown step';
    }
  };

  return (
    <Box sx={{ width: '100%' }}>
      <Stepper activeStep={activeStep} sx={{ mb: 4 }}>
        {steps.map((label) => (
          <Step key={label}>
            <StepLabel>{label}</StepLabel>
          </Step>
        ))}
      </Stepper>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      <form onSubmit={handleSubmit(onSubmit)} noValidate>
        {getStepContent(activeStep)}

        <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 3 }}>
          <Button
            onClick={handleBack}
            disabled={activeStep === 0 || isLoading}
          >
            이전
          </Button>

          {activeStep === steps.length - 1 ? (
            <Button
              type="submit"
              variant="contained"
              disabled={isLoading}
            >
              {isLoading ? <CircularProgress size={24} /> : '회원가입'}
            </Button>
          ) : (
            <Button
              variant="contained"
              onClick={handleNext}
              disabled={isLoading}
            >
              다음
            </Button>
          )}
        </Box>
      </form>

      <Grid container justifyContent="center" sx={{ mt: 3 }}>
        <Grid item>
          <Link component={RouterLink} to="/login" variant="body2">
            이미 계정이 있으신가요? 로그인
          </Link>
        </Grid>
      </Grid>
    </Box>
  );
};

export default Register;