import React, { createContext, useState, useContext, useEffect, ReactNode } from 'react';
import apiClient from '../services/api';

interface User {
  id: number;
  email: string;
  name: string;
  company?: string;
  role: string;
  subscription_plan?: string;
}

interface AuthContextType {
  user: User | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (data: any) => Promise<void>;
  logout: () => Promise<void>;
  updateUser: (user: User) => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

interface AuthProviderProps {
  children: ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isAuthenticated, setIsAuthenticated] = useState(false);

  useEffect(() => {
    checkAuth();

    // 토큰 만료 시 인터셉터가 보내는 이벤트 수신
    const handleSessionExpired = () => {
      setUser(null);
      setIsAuthenticated(false);
      setIsLoading(false);
    };
    window.addEventListener('auth:session-expired', handleSessionExpired);
    return () => window.removeEventListener('auth:session-expired', handleSessionExpired);
  }, []);

  const checkAuth = async () => {
    const token = localStorage.getItem(process.env.REACT_APP_TOKEN_KEY || 'odin_ai_token');
    if (token) {
      try {
        const userData = await apiClient.getProfile();
        setUser(userData);
        setIsAuthenticated(true);
      } catch (error) {
        localStorage.removeItem(process.env.REACT_APP_TOKEN_KEY || 'odin_ai_token');
        localStorage.removeItem(process.env.REACT_APP_REFRESH_TOKEN_KEY || 'odin_ai_refresh_token');
      }
    }
    setIsLoading(false);
  };

  const login = async (email: string, password: string) => {
    try {
      await apiClient.login(email, password);
      // 로그인 후 프로필 정보 가져오기 (role 포함)
      const userData = await apiClient.getProfile();
      setUser(userData);
      setIsAuthenticated(true);
    } catch (error) {
      throw error;
    }
  };

  const register = async (data: any) => {
    try {
      await apiClient.register(data);
      // 회원가입 후 자동 로그인
      await login(data.email, data.password);
    } catch (error) {
      throw error;
    }
  };

  const logout = async () => {
    // 토큰 존재 여부 확인
    const token = localStorage.getItem('odin_ai_token');

    try {
      if (token) {
        await apiClient.logout();
      }
    } catch (error) {
      // 401 에러든 다른 에러든 상관없이 로컬 상태는 정리
    } finally {
      setUser(null);
      setIsAuthenticated(false);
      // 토큰들 수동 제거
      localStorage.removeItem('odin_ai_token');
      localStorage.removeItem('odin_ai_refresh_token');
      // React Router의 Navigate가 /login으로 리다이렉트 처리
    }
  };

  const updateUser = (userData: User) => {
    setUser(userData);
  };

  const value = {
    user,
    isLoading,
    isAuthenticated,
    login,
    register,
    logout,
    updateUser,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};