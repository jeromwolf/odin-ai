import { createSlice, PayloadAction } from '@reduxjs/toolkit';

interface Bid {
  id: string;
  bid_notice_no: string;
  title: string;
  organization_name: string;
  announcement_date: string;
  closing_date: string;
  bid_amount?: number;
  industry_type?: string;
  location?: string;
  is_bookmarked: boolean;
}

interface BidState {
  bids: Bid[];
  selectedBid: Bid | null;
  searchResults: Bid[];
  bookmarks: string[];
  filters: {
    industry?: string;
    location?: string;
    minAmount?: number;
    maxAmount?: number;
    dateFrom?: string;
    dateTo?: string;
  };
  isLoading: boolean;
  error: string | null;
  totalCount: number;
  currentPage: number;
  pageSize: number;
}

const initialState: BidState = {
  bids: [],
  selectedBid: null,
  searchResults: [],
  bookmarks: [],
  filters: {},
  isLoading: false,
  error: null,
  totalCount: 0,
  currentPage: 1,
  pageSize: 20,
};

const bidSlice = createSlice({
  name: 'bid',
  initialState,
  reducers: {
    setBids: (state, action: PayloadAction<Bid[]>) => {
      state.bids = action.payload;
    },
    setSelectedBid: (state, action: PayloadAction<Bid | null>) => {
      state.selectedBid = action.payload;
    },
    setSearchResults: (state, action: PayloadAction<Bid[]>) => {
      state.searchResults = action.payload;
    },
    addBookmark: (state, action: PayloadAction<string>) => {
      if (!state.bookmarks.includes(action.payload)) {
        state.bookmarks.push(action.payload);
      }
    },
    removeBookmark: (state, action: PayloadAction<string>) => {
      state.bookmarks = state.bookmarks.filter((id) => id !== action.payload);
    },
    setFilters: (state, action: PayloadAction<typeof initialState.filters>) => {
      state.filters = action.payload;
    },
    updateFilter: (state, action: PayloadAction<Partial<typeof initialState.filters>>) => {
      state.filters = { ...state.filters, ...action.payload };
    },
    clearFilters: (state) => {
      state.filters = {};
    },
    setLoading: (state, action: PayloadAction<boolean>) => {
      state.isLoading = action.payload;
    },
    setError: (state, action: PayloadAction<string | null>) => {
      state.error = action.payload;
    },
    setPagination: (
      state,
      action: PayloadAction<{ totalCount?: number; currentPage?: number; pageSize?: number }>
    ) => {
      if (action.payload.totalCount !== undefined) {
        state.totalCount = action.payload.totalCount;
      }
      if (action.payload.currentPage !== undefined) {
        state.currentPage = action.payload.currentPage;
      }
      if (action.payload.pageSize !== undefined) {
        state.pageSize = action.payload.pageSize;
      }
    },
  },
});

export const {
  setBids,
  setSelectedBid,
  setSearchResults,
  addBookmark,
  removeBookmark,
  setFilters,
  updateFilter,
  clearFilters,
  setLoading,
  setError,
  setPagination,
} = bidSlice.actions;

export default bidSlice.reducer;