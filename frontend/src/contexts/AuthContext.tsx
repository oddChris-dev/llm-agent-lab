/**
 * Authentication context for managing user auth state.
 */

import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import authApi, { User, LoginCredentials, RegisterData, TokenResponse } from '../api/auth';

interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
}

interface AuthContextValue extends AuthState {
  login: (credentials: LoginCredentials) => Promise<void>;
  register: (data: RegisterData) => Promise<void>;
  logout: () => void;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | null>(null);

const TOKEN_KEY = 'auth_token';
const REFRESH_TOKEN_KEY = 'refresh_token';

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [state, setState] = useState<AuthState>({
    user: null,
    isAuthenticated: false,
    isLoading: true,
  });

  const setTokens = useCallback((tokens: TokenResponse) => {
    localStorage.setItem(TOKEN_KEY, tokens.access);
    localStorage.setItem(REFRESH_TOKEN_KEY, tokens.refresh);
  }, []);

  const clearTokens = useCallback(() => {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(REFRESH_TOKEN_KEY);
  }, []);

  const refreshUser = useCallback(async () => {
    const token = localStorage.getItem(TOKEN_KEY);
    if (!token) {
      setState({ user: null, isAuthenticated: false, isLoading: false });
      return;
    }

    try {
      const user = await authApi.getCurrentUser();
      setState({ user, isAuthenticated: true, isLoading: false });
    } catch {
      // Token might be expired, try to refresh
      try {
        const tokens = await authApi.refreshToken();
        setTokens(tokens);
        const user = await authApi.getCurrentUser();
        setState({ user, isAuthenticated: true, isLoading: false });
      } catch {
        clearTokens();
        setState({ user: null, isAuthenticated: false, isLoading: false });
      }
    }
  }, [setTokens, clearTokens]);

  useEffect(() => {
    refreshUser();
  }, [refreshUser]);

  const login = useCallback(async (credentials: LoginCredentials) => {
    const tokens = await authApi.login(credentials);
    setTokens(tokens);
    const user = await authApi.getCurrentUser();
    setState({ user, isAuthenticated: true, isLoading: false });
  }, [setTokens]);

  const register = useCallback(async (data: RegisterData) => {
    const result = await authApi.register(data);
    setTokens(result.tokens);
    setState({ user: result.user, isAuthenticated: true, isLoading: false });
  }, [setTokens]);

  const logout = useCallback(() => {
    clearTokens();
    setState({ user: null, isAuthenticated: false, isLoading: false });
  }, [clearTokens]);

  const value: AuthContextValue = {
    ...state,
    login,
    register,
    logout,
    refreshUser,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}

export default AuthContext;
