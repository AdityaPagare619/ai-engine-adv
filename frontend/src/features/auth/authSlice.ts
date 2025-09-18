import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit';
import { RootState } from '../../store/store';
import * as authAPI from '../../api/auth';

// Types
export interface User {
  id: string;
  name: string;
  email: string;
  role: 'student' | 'admin' | 'teacher';
  permissions: string[];
  verified: boolean;
  lastLogin: string;
  profilePicture?: string;
}

export interface AuthState {
  user: User | null;
  token: string | null;
  refreshToken: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
  sessionExpiry: number | null;
  loginAttempts: number;
  isLocked: boolean;
  lockoutExpiry: number | null;
  mfaRequired: boolean;
  mfaToken: string | null;
}

// Initial state
const initialState: AuthState = {
  user: null,
  token: localStorage.getItem('accessToken'),
  refreshToken: localStorage.getItem('refreshToken'),
  isAuthenticated: false,
  isLoading: false,
  error: null,
  sessionExpiry: null,
  loginAttempts: 0,
  isLocked: false,
  lockoutExpiry: null,
  mfaRequired: false,
  mfaToken: null,
};

// Security constants
const MAX_LOGIN_ATTEMPTS = 5;
const LOCKOUT_DURATION = 15 * 60 * 1000; // 15 minutes
const SESSION_WARNING_TIME = 5 * 60 * 1000; // 5 minutes before expiry

// Async thunks
export const loginUser = createAsyncThunk(
  'auth/loginUser',
  async (
    credentials: { email: string; password: string; rememberMe?: boolean },
    { rejectWithValue, getState }
  ) => {
    try {
      const state = getState() as RootState;

      // Check if account is locked
      if (state.auth.isLocked && state.auth.lockoutExpiry && Date.now() < state.auth.lockoutExpiry) {
        throw new Error('Account temporarily locked due to too many failed attempts');
      }

      const response = await authAPI.login(credentials);

      // Store tokens securely
      if (credentials.rememberMe) {
        localStorage.setItem('accessToken', response.token);
        localStorage.setItem('refreshToken', response.refreshToken);
      } else {
        sessionStorage.setItem('accessToken', response.token);
        sessionStorage.setItem('refreshToken', response.refreshToken);
      }

      // Set session expiry
      const sessionExpiry = Date.now() + (response.expiresIn * 1000);

      return {
        user: response.user,
        token: response.token,
        refreshToken: response.refreshToken,
        sessionExpiry,
        mfaRequired: response.mfaRequired,
        mfaToken: response.mfaToken,
      };
    } catch (error: any) {
      // Security logging (in production, log to secure service)
      console.warn('Failed login attempt:', {
        email: credentials.email,
        timestamp: new Date().toISOString(),
        userAgent: navigator.userAgent,
        ip: 'logged-server-side',
      });

      return rejectWithValue(error.message || 'Login failed');
    }
  }
);

export const verifyMFA = createAsyncThunk(
  'auth/verifyMFA',
  async (
    { mfaCode, mfaToken }: { mfaCode: string; mfaToken: string },
    { rejectWithValue }
  ) => {
    try {
      const response = await authAPI.verifyMFA({ mfaCode, mfaToken });

      localStorage.setItem('accessToken', response.token);
      localStorage.setItem('refreshToken', response.refreshToken);

      const sessionExpiry = Date.now() + (response.expiresIn * 1000);

      return {
        user: response.user,
        token: response.token,
        refreshToken: response.refreshToken,
        sessionExpiry,
      };
    } catch (error: any) {
      return rejectWithValue(error.message || 'MFA verification failed');
    }
  }
);

export const refreshAuthToken = createAsyncThunk(
  'auth/refreshToken',
  async (_, { getState, rejectWithValue }) => {
    try {
      const state = getState() as RootState;
      const refreshToken = state.auth.refreshToken;

      if (!refreshToken) {
        throw new Error('No refresh token available');
      }

      const response = await authAPI.refreshToken(refreshToken);

      localStorage.setItem('accessToken', response.token);
      const sessionExpiry = Date.now() + (response.expiresIn * 1000);

      return {
        token: response.token,
        sessionExpiry,
      };
    } catch (error: any) {
      return rejectWithValue(error.message || 'Token refresh failed');
    }
  }
);

export const logoutUser = createAsyncThunk(
  'auth/logoutUser',
  async (_, { getState }) => {
    try {
      const state = getState() as RootState;
      if (state.auth.token) {
        await authAPI.logout();
      }
    } catch (error) {
      // Even if logout API fails, we still clear local state
      console.warn('Logout API call failed:', error);
    } finally {
      // Always clear tokens
      localStorage.removeItem('accessToken');
      localStorage.removeItem('refreshToken');
      sessionStorage.removeItem('accessToken');
      sessionStorage.removeItem('refreshToken');
    }
  }
);

export const validateSession = createAsyncThunk(
  'auth/validateSession',
  async (_, { getState, rejectWithValue }) => {
    try {
      const state = getState() as RootState;
      const token = state.auth.token;

      if (!token) {
        throw new Error('No token found');
      }

      const response = await authAPI.validateSession();
      return response.user;
    } catch (error: any) {
      return rejectWithValue(error.message || 'Session validation failed');
    }
  }
);

// Auth slice
const authSlice = createSlice({
  name: 'auth',
  initialState,
  reducers: {
    clearError: (state) => {
      state.error = null;
    },
    resetLoginAttempts: (state) => {
      state.loginAttempts = 0;
      state.isLocked = false;
      state.lockoutExpiry = null;
    },
    updateSessionWarning: (state, action: PayloadAction<boolean>) => {
      // Handle session warning state if needed
    },
    updateUserProfile: (state, action: PayloadAction<Partial<User>>) => {
      if (state.user) {
        state.user = { ...state.user, ...action.payload };
      }
    },
    forceLogout: (state) => {
      state.user = null;
      state.token = null;
      state.refreshToken = null;
      state.isAuthenticated = false;
      state.sessionExpiry = null;
      state.mfaRequired = false;
      state.mfaToken = null;
      localStorage.removeItem('accessToken');
      localStorage.removeItem('refreshToken');
      sessionStorage.removeItem('accessToken');
      sessionStorage.removeItem('refreshToken');
    },
  },
  extraReducers: (builder) => {
    builder
      // Login cases
      .addCase(loginUser.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(loginUser.fulfilled, (state, action) => {
        state.isLoading = false;
        state.error = null;
        state.loginAttempts = 0;
        state.isLocked = false;
        state.lockoutExpiry = null;

        if (action.payload.mfaRequired) {
          state.mfaRequired = true;
          state.mfaToken = action.payload.mfaToken;
        } else {
          state.user = action.payload.user;
          state.token = action.payload.token;
          state.refreshToken = action.payload.refreshToken;
          state.isAuthenticated = true;
          state.sessionExpiry = action.payload.sessionExpiry;
        }
      })
      .addCase(loginUser.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.payload as string;
        state.loginAttempts += 1;

        // Implement account lockout
        if (state.loginAttempts >= MAX_LOGIN_ATTEMPTS) {
          state.isLocked = true;
          state.lockoutExpiry = Date.now() + LOCKOUT_DURATION;
        }
      })

      // MFA verification cases
      .addCase(verifyMFA.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(verifyMFA.fulfilled, (state, action) => {
        state.isLoading = false;
        state.user = action.payload.user;
        state.token = action.payload.token;
        state.refreshToken = action.payload.refreshToken;
        state.isAuthenticated = true;
        state.sessionExpiry = action.payload.sessionExpiry;
        state.mfaRequired = false;
        state.mfaToken = null;
      })
      .addCase(verifyMFA.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.payload as string;
      })

      // Token refresh cases
      .addCase(refreshAuthToken.fulfilled, (state, action) => {
        state.token = action.payload.token;
        state.sessionExpiry = action.payload.sessionExpiry;
        state.error = null;
      })
      .addCase(refreshAuthToken.rejected, (state) => {
        state.user = null;
        state.token = null;
        state.refreshToken = null;
        state.isAuthenticated = false;
        state.sessionExpiry = null;
      })

      // Logout cases
      .addCase(logoutUser.fulfilled, (state) => {
        state.user = null;
        state.token = null;
        state.refreshToken = null;
        state.isAuthenticated = false;
        state.sessionExpiry = null;
        state.mfaRequired = false;
        state.mfaToken = null;
        state.error = null;
      })

      // Session validation cases
      .addCase(validateSession.fulfilled, (state, action) => {
        state.user = action.payload;
        state.isAuthenticated = true;
      })
      .addCase(validateSession.rejected, (state) => {
        state.user = null;
        state.token = null;
        state.refreshToken = null;
        state.isAuthenticated = false;
        state.sessionExpiry = null;
      });
  },
});

// Actions
export const {
  clearError,
  resetLoginAttempts,
  updateSessionWarning,
  updateUserProfile,
  forceLogout
} = authSlice.actions;

// Selectors
export const selectAuth = (state: RootState) => state.auth;
export const selectUser = (state: RootState) => state.auth.user;
export const selectIsAuthenticated = (state: RootState) => state.auth.isAuthenticated;
export const selectIsLoading = (state: RootState) => state.auth.isLoading;
export const selectAuthError = (state: RootState) => state.auth.error;
export const selectSessionExpiry = (state: RootState) => state.auth.sessionExpiry;
export const selectIsLocked = (state: RootState) => state.auth.isLocked;
export const selectMfaRequired = (state: RootState) => state.auth.mfaRequired;

// Utility selectors
export const selectUserPermissions = (state: RootState): string[] =>
  state.auth.user?.permissions || [];

export const selectUserRole = (state: RootState): string =>
  state.auth.user?.role || 'guest';

export const selectSessionTimeRemaining = (state: RootState): number => {
  const expiry = state.auth.sessionExpiry;
  return expiry ? Math.max(0, expiry - Date.now()) : 0;
};

export const selectShouldShowSessionWarning = (state: RootState): boolean => {
  const timeRemaining = selectSessionTimeRemaining(state);
  return timeRemaining > 0 && timeRemaining <= SESSION_WARNING_TIME;
};

export default authSlice.reducer;
