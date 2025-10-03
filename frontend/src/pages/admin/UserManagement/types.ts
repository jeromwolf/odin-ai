/**
 * UserManagement 페이지 타입 정의
 */

export interface User {
  id: number;
  email: string;
  username: string;
  full_name: string | null;
  company: string | null;
  phone: string | null;
  subscription_plan: string;
  is_active: boolean;
  email_verified: boolean;
  created_at: string;
  last_login: string | null;
}

export interface UserDetail {
  user: User;
  activity_stats: {
    total_searches: number;
    total_bookmarks: number;
    total_notifications: number;
    last_search_date: string | null;
  };
  notification_rules: any[];
  bookmarks: any[];
  recent_activities: any[];
}

export interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}
