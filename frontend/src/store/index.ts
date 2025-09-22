import { configureStore } from '@reduxjs/toolkit';
import authReducer from './slices/authSlice';
import bidReducer from './slices/bidSlice';
import subscriptionReducer from './slices/subscriptionSlice';
import notificationReducer from './slices/notificationSlice';

export const store = configureStore({
  reducer: {
    auth: authReducer,
    bid: bidReducer,
    subscription: subscriptionReducer,
    notification: notificationReducer,
  },
});

export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;