import axios, { AxiosInstance, AxiosRequestConfig, AxiosError } from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'http://localhost:9000/api';
const TOKEN_KEY = process.env.REACT_APP_TOKEN_KEY || 'odin_ai_token';
const REFRESH_TOKEN_KEY = process.env.REACT_APP_REFRESH_TOKEN_KEY || 'odin_ai_refresh_token';

class ApiClient {
  private client: AxiosInstance;
  private isRefreshing: boolean = false;
  private refreshSubscribers: Array<(token: string) => void> = [];

  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    this.setupInterceptors();
  }

  private setupInterceptors(): void {
    // Request Interceptor
    this.client.interceptors.request.use(
      (config) => {
        const token = this.getToken();
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
      },
      (error) => {
        return Promise.reject(error);
      }
    );

    // Response Interceptor
    this.client.interceptors.response.use(
      (response) => response,
      async (error: AxiosError) => {
        const originalRequest = error.config as AxiosRequestConfig & { _retry?: boolean };

        if (error.response?.status === 401 && !originalRequest._retry) {
          if (this.isRefreshing) {
            return new Promise((resolve) => {
              this.refreshSubscribers.push((token: string) => {
                if (originalRequest.headers) {
                  originalRequest.headers.Authorization = `Bearer ${token}`;
                }
                resolve(this.client(originalRequest));
              });
            });
          }

          originalRequest._retry = true;
          this.isRefreshing = true;

          try {
            const newToken = await this.refreshToken();
            this.isRefreshing = false;
            this.onRefreshed(newToken);
            this.refreshSubscribers = [];

            if (originalRequest.headers) {
              originalRequest.headers.Authorization = `Bearer ${newToken}`;
            }
            return this.client(originalRequest);
          } catch (refreshError) {
            this.isRefreshing = false;
            this.clearTokens();
            window.location.href = '/login';
            return Promise.reject(refreshError);
          }
        }

        return Promise.reject(error);
      }
    );
  }

  private getToken(): string | null {
    return localStorage.getItem(TOKEN_KEY);
  }

  private getRefreshToken(): string | null {
    return localStorage.getItem(REFRESH_TOKEN_KEY);
  }

  private setToken(token: string): void {
    localStorage.setItem(TOKEN_KEY, token);
  }

  private setRefreshToken(token: string): void {
    localStorage.setItem(REFRESH_TOKEN_KEY, token);
  }

  private clearTokens(): void {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(REFRESH_TOKEN_KEY);
  }

  private async refreshToken(): Promise<string> {
    const refreshToken = this.getRefreshToken();
    if (!refreshToken) {
      throw new Error('No refresh token available');
    }

    const response = await this.client.post('/auth/refresh', {
      refresh_token: refreshToken,
    });

    const { access_token, refresh_token: newRefreshToken } = response.data;
    this.setToken(access_token);
    this.setRefreshToken(newRefreshToken);

    return access_token;
  }

  private onRefreshed(token: string): void {
    this.refreshSubscribers.forEach((callback) => callback(token));
  }

  // Auth API
  async login(email: string, password: string) {
    const response = await this.client.post('/auth/login', { email, password });
    const { access_token, refresh_token, user } = response.data;
    this.setToken(access_token);
    this.setRefreshToken(refresh_token);
    return { user, access_token };
  }

  async register(data: any) {
    const response = await this.client.post('/auth/register', data);
    return response.data;
  }

  async logout() {
    try {
      await this.client.post('/auth/logout');
    } finally {
      this.clearTokens();
    }
  }

  // Bid API
  async getBids(params?: any) {
    const response = await this.client.get('/bids', { params });
    return response.data;
  }

  async getBidDetail(id: string) {
    const response = await this.client.get(`/bids/${id}`);
    return response.data;
  }

  async searchBids(query: string, filters?: any) {
    const response = await this.client.get('/search', {
      params: { q: query, ...filters },
    });
    return response.data;
  }

  // Subscription API
  async getSubscriptionPlans() {
    const response = await this.client.get('/subscription/plans');
    return response.data;
  }

  async getCurrentSubscription() {
    const response = await this.client.get('/subscription/current');
    return response.data;
  }

  async upgradeSubscription(planType: string, applyImmediately: boolean = false) {
    const response = await this.client.post('/subscription/upgrade', {
      new_plan_type: planType,
      apply_immediately: applyImmediately,
    });
    return response.data;
  }

  async cancelSubscription(reason?: string) {
    const response = await this.client.post('/subscription/cancel', { reason });
    return response.data;
  }

  async getUsageStatistics(period: string = 'current') {
    const response = await this.client.get('/subscription/usage', {
      params: { period },
    });
    return response.data;
  }

  // Dashboard API
  async getDashboardOverview() {
    const response = await this.client.get('/dashboard/overview');
    return response.data;
  }

  async getBidStatistics(period: string = '7d') {
    const response = await this.client.get('/dashboard/statistics', {
      params: { days: period === '7d' ? 7 : 30 },
    });
    return response.data;
  }

  async getUpcomingDeadlines(days: number = 7) {
    const response = await this.client.get('/dashboard/deadlines', {
      params: { days },
    });
    return response.data;
  }

  async getRecommendedBids(limit: number = 10) {
    const response = await this.client.get('/dashboard/recommendations', {
      params: { limit },
    });
    return response.data;
  }

  // Profile API
  async getProfile() {
    const response = await this.client.get('/profile');
    return response.data;
  }

  async updateProfile(data: any) {
    const response = await this.client.put('/profile', data);
    return response.data;
  }

  async changePassword(oldPassword: string, newPassword: string) {
    const response = await this.client.post('/profile/change-password', {
      current_password: oldPassword,
      new_password: newPassword,
    });
    return response.data;
  }

  // Settings API
  async getSettings() {
    const response = await this.client.get('/settings');
    return response.data;
  }

  async updateSettings(data: any) {
    const response = await this.client.put('/settings', data);
    return response.data;
  }

  // Keywords API
  async getKeywords() {
    const response = await this.client.get('/keywords');
    return response.data;
  }

  async addKeyword(keyword: string, category?: string) {
    const response = await this.client.post('/keywords', { keyword, category });
    return response.data;
  }

  async deleteKeyword(id: string) {
    const response = await this.client.delete(`/keywords/${id}`);
    return response.data;
  }

  // Notifications API
  async getNotifications(unreadOnly: boolean = false) {
    const response = await this.client.get('/notifications', {
      params: { unread_only: unreadOnly },
    });
    return response.data;
  }

  async markNotificationAsRead(id: string) {
    const response = await this.client.put(`/notifications/${id}/read`);
    return response.data;
  }

  async markAllNotificationsAsRead() {
    const response = await this.client.put('/notifications/read-all');
    return response.data;
  }

  // Bookmarks API
  async addBookmark(bidId: string) {
    const response = await this.client.post(`/bookmarks/${bidId}`);
    return response.data;
  }

  async removeBookmark(bidId: string) {
    const response = await this.client.delete(`/bookmarks/${bidId}`);
    return response.data;
  }

  async getBookmarks() {
    const response = await this.client.get('/bookmarks');
    return response.data;
  }

  async updateBookmarkNote(bidNoticeNo: string, note: string) {
    const response = await this.client.put(`/bookmarks/${bidNoticeNo}/note`, null, {
      params: { note }
    });
    return response.data;
  }

  // Notification Settings API
  async getNotificationSettings() {
    const response = await this.client.get('/notifications/settings');
    return response.data;
  }

  async updateNotificationSettings(settings: any) {
    const response = await this.client.put('/notifications/settings', settings);
    return response.data;
  }

  async addNotificationRule(rule: any) {
    const response = await this.client.post('/notifications/rules', rule);
    return response.data;
  }

  async deleteNotificationRule(ruleId: string) {
    const response = await this.client.delete(`/notifications/rules/${ruleId}`);
    return response.data;
  }

  // Subscription API
  async getSubscription() {
    const response = await this.client.get('/subscription');
    return response.data;
  }

  async updateSubscription(planId: string) {
    const response = await this.client.post('/subscription/change-plan', { plan_id: planId });
    return response.data;
  }

  async getPaymentHistory() {
    const response = await this.client.get('/subscription/payment-history');
    return response.data;
  }

  // User Activity API
  async getUserActivity() {
    const response = await this.client.get('/profile/activity');
    return response.data;
  }

  // Data Export/Import API
  async exportData() {
    const response = await this.client.get('/settings/export', {
      responseType: 'blob',
    });
    return response.data;
  }

  async deleteAccount() {
    const response = await this.client.delete('/settings/account');
    return response.data;
  }
}

export const apiClient = new ApiClient();
export default apiClient;