/**
 * 관리자 API 클라이언트
 * 관리자 웹 전용 API 호출 서비스
 */

import axios, { AxiosInstance } from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:9000';

class AdminApiClient {
  private client: AxiosInstance;
  private token: string | null = null;

  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // 요청 인터셉터: 토큰 자동 추가
    this.client.interceptors.request.use(
      (config) => {
        const token = this.getToken();
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
      },
      (error) => Promise.reject(error)
    );

    // 응답 인터셉터: 401 에러 시 로그아웃
    this.client.interceptors.response.use(
      (response) => response,
      (error) => {
        if (error.response?.status === 401) {
          this.clearToken();
          window.location.href = '/admin/login';
        }
        return Promise.reject(error);
      }
    );
  }

  // ============================================
  // 토큰 관리
  // ============================================

  setToken(token: string) {
    this.token = token;
    localStorage.setItem('admin_token', token);
  }

  getToken(): string | null {
    if (!this.token) {
      this.token = localStorage.getItem('admin_token');
    }
    return this.token;
  }

  clearToken() {
    this.token = null;
    localStorage.removeItem('admin_token');
  }

  // ============================================
  // 인증 API
  // ============================================

  async login(email: string, password: string) {
    const response = await this.client.post('/api/admin/auth/login', {
      email,
      password,
    });
    const { access_token, admin_info } = response.data;
    this.setToken(access_token);
    return { token: access_token, admin: admin_info };
  }

  async logout() {
    await this.client.post('/api/admin/auth/logout');
    this.clearToken();
  }

  async getCurrentAdmin() {
    const response = await this.client.get('/api/admin/auth/me');
    return response.data;
  }

  async getActivityLogs(limit: number = 50) {
    const response = await this.client.get('/api/admin/auth/activity-logs', {
      params: { limit },
    });
    return response.data;
  }

  // ============================================
  // 배치 모니터링 API
  // ============================================

  async getBatchExecutions(params: {
    start_date?: string;
    end_date?: string;
    batch_type?: string;
    status?: string;
    page?: number;
    limit?: number;
  }) {
    const response = await this.client.get('/api/admin/batch/executions', {
      params,
    });
    return response.data;
  }

  async getBatchExecutionDetail(executionId: number) {
    const response = await this.client.get(
      `/api/admin/batch/executions/${executionId}`
    );
    return response.data;
  }

  async getBatchStatistics(params: {
    start_date?: string;
    end_date?: string;
    batch_type?: string;
  }) {
    const response = await this.client.get('/api/admin/batch/statistics', {
      params,
    });
    return response.data;
  }

  async executeBatchManual(data: {
    batch_type: string;
    test_mode?: boolean;
    start_date?: string;
    end_date?: string;
    enable_notification?: boolean;
  }) {
    const response = await this.client.post('/api/admin/batch/execute', data);
    return response.data;
  }

  // ============================================
  // 시스템 모니터링 API
  // ============================================

  async getSystemMetrics(params: {
    metric_type?: string;
    start_time?: string;
    end_time?: string;
    limit?: number;
  }) {
    const response = await this.client.get('/api/admin/system/metrics', {
      params,
    });
    return response.data;
  }

  async getSystemStatus() {
    const response = await this.client.get('/api/admin/system/status');
    return response.data;
  }

  async getApiPerformance(params: {
    start_time?: string;
    end_time?: string;
  }) {
    const response = await this.client.get('/api/admin/system/api-performance', {
      params,
    });
    return response.data;
  }

  async getNotificationStatus(params: {
    start_time?: string;
    end_time?: string;
  }) {
    const response = await this.client.get(
      '/api/admin/system/notifications/status',
      { params }
    );
    return response.data;
  }

  // ============================================
  // 사용자 관리 API
  // ============================================

  async getUsers(params: {
    search?: string;
    is_active?: boolean;
    page?: number;
    limit?: number;
  }) {
    const response = await this.client.get('/api/admin/users', { params });
    return response.data;
  }

  async getUserDetail(userId: number) {
    const response = await this.client.get(`/api/admin/users/${userId}`);
    return response.data;
  }

  async updateUser(userId: number, data: { is_active?: boolean }) {
    const response = await this.client.patch(`/api/admin/users/${userId}`, data);
    return response.data;
  }

  async getUserStatistics() {
    const response = await this.client.get('/api/admin/users/statistics/summary');
    return response.data;
  }

  // ============================================
  // 로그 조회 API
  // ============================================

  async getLogs(params: {
    start_date?: string;
    end_date?: string;
    level?: string;
    keyword?: string;
    page?: number;
    limit?: number;
  }) {
    const response = await this.client.get('/api/admin/logs', { params });
    return response.data;
  }

  async downloadLogs(logDate: string) {
    const response = await this.client.get(`/api/admin/logs/download/${logDate}`, {
      responseType: 'blob',
    });
    return response.data;
  }

  async getErrorStatistics(params: { start_date?: string; end_date?: string }) {
    const response = await this.client.get('/api/admin/logs/errors/statistics', {
      params,
    });
    return response.data;
  }

  // ============================================
  // 통계 분석 API
  // ============================================

  async getBidCollectionStats(params: {
    start_date?: string;
    end_date?: string;
    group_by?: 'day' | 'week' | 'month';
  }) {
    const response = await this.client.get(
      '/api/admin/statistics/bid-collection',
      { params }
    );
    return response.data;
  }

  async getCategoryDistribution(params: {
    start_date?: string;
    end_date?: string;
  }) {
    const response = await this.client.get(
      '/api/admin/statistics/category-distribution',
      { params }
    );
    return response.data;
  }

  async getUserGrowthStats(params: {
    start_date?: string;
    end_date?: string;
  }) {
    const response = await this.client.get(
      '/api/admin/statistics/user-growth',
      { params }
    );
    return response.data;
  }

  async getNotificationStats(params: {
    start_date?: string;
    end_date?: string;
  }) {
    const response = await this.client.get(
      '/api/admin/statistics/notifications',
      { params }
    );
    return response.data;
  }
}

export const adminApi = new AdminApiClient();
export default adminApi;
