import { createSlice, PayloadAction } from '@reduxjs/toolkit';

interface SubscriptionPlan {
  id: number;
  plan_type: string;
  plan_name: string;
  display_name: string;
  monthly_price: number;
  annual_price?: number;
  max_searches_per_month: number;
  max_bookmarks: number;
  max_email_alerts: number;
  max_api_calls: number;
  features: Record<string, boolean>;
  is_popular?: boolean;
  is_recommended?: boolean;
}

interface Subscription {
  id: number;
  plan_type: string;
  plan_name: string;
  is_active: boolean;
  is_trial: boolean;
  started_at: string;
  expires_at?: string;
  trial_ends_at?: string;
  monthly_price: number;
  current_searches: number;
  current_api_calls: number;
  max_searches_per_month: number;
  max_bookmarks: number;
  max_email_alerts: number;
  max_api_calls: number;
}

interface Usage {
  search: number;
  api_call: number;
  bookmark: number;
  email: number;
}

interface SubscriptionState {
  plans: SubscriptionPlan[];
  currentSubscription: Subscription | null;
  usage: Usage;
  usagePercentage: Usage;
  paymentHistory: any[];
  isLoading: boolean;
  error: string | null;
}

const initialState: SubscriptionState = {
  plans: [],
  currentSubscription: null,
  usage: {
    search: 0,
    api_call: 0,
    bookmark: 0,
    email: 0,
  },
  usagePercentage: {
    search: 0,
    api_call: 0,
    bookmark: 0,
    email: 0,
  },
  paymentHistory: [],
  isLoading: false,
  error: null,
};

const subscriptionSlice = createSlice({
  name: 'subscription',
  initialState,
  reducers: {
    setPlans: (state, action: PayloadAction<SubscriptionPlan[]>) => {
      state.plans = action.payload;
    },
    setCurrentSubscription: (state, action: PayloadAction<Subscription | null>) => {
      state.currentSubscription = action.payload;
    },
    setUsage: (state, action: PayloadAction<Usage>) => {
      state.usage = action.payload;
    },
    setUsagePercentage: (state, action: PayloadAction<Usage>) => {
      state.usagePercentage = action.payload;
    },
    updateUsage: (state, action: PayloadAction<Partial<Usage>>) => {
      state.usage = { ...state.usage, ...action.payload };
    },
    setPaymentHistory: (state, action: PayloadAction<any[]>) => {
      state.paymentHistory = action.payload;
    },
    setLoading: (state, action: PayloadAction<boolean>) => {
      state.isLoading = action.payload;
    },
    setError: (state, action: PayloadAction<string | null>) => {
      state.error = action.payload;
    },
    upgradeSubscription: (state, action: PayloadAction<string>) => {
      if (state.currentSubscription) {
        state.currentSubscription.plan_type = action.payload;
      }
    },
    cancelSubscription: (state) => {
      if (state.currentSubscription) {
        state.currentSubscription.is_active = false;
      }
    },
  },
});

export const {
  setPlans,
  setCurrentSubscription,
  setUsage,
  setUsagePercentage,
  updateUsage,
  setPaymentHistory,
  setLoading,
  setError,
  upgradeSubscription,
  cancelSubscription,
} = subscriptionSlice.actions;

export default subscriptionSlice.reducer;