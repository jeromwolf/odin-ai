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
  }, []);

  const checkAuth = async () => {
    const token = localStorage.getItem(process.env.REACT_APP_TOKEN_KEY || 'odin_ai_token');
    if (token) {
      try {
        const userData = await apiClient.getProfile();
        setUser(userData);
        setIsAuthenticated(true);
      } catch (error) {
        console.error('인증 확인 실패:', error);
        localStorage.removeItem(process.env.REACT_APP_TOKEN_KEY || 'odin_ai_token');
        localStorage.removeItem(process.env.REACT_APP_REFRESH_TOKEN_KEY || 'odin_ai_refresh_token');
      }
    }
    setIsLoading(false);
  };

  const login = async (email: string, password: string) => {
    try {
      const { user: userData } = await apiClient.login(email, password);
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
    try {
      await apiClient.logout();
    } catch (error) {
      console.error('로그아웃 실패:', error);
    } finally {
      setUser(null);
      setIsAuthenticated(false);
      window.location.href = '/login';
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