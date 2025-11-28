/**
 * Authentication API service.
 */

import apiClient from './client';

export interface LoginCredentials {
  username: string;
  password: string;
}

export interface RegisterData {
  username: string;
  email: string;
  password: string;
  password_confirm: string;
  first_name?: string;
  last_name?: string;
}

export interface TokenResponse {
  access: string;
  refresh: string;
}

export interface User {
  id: number;
  username: string;
  email: string;
  first_name: string;
  last_name: string;
  date_joined: string;
}

const TOKEN_KEY = 'auth_token';
const REFRESH_KEY = 'refresh_token';

/**
 * Login with username and password.
 */
export async function login(credentials: LoginCredentials): Promise<TokenResponse> {
  const response = await apiClient.post<TokenResponse>('/auth/token/', credentials);

  // Store tokens
  localStorage.setItem(TOKEN_KEY, response.data.access);
  localStorage.setItem(REFRESH_KEY, response.data.refresh);

  return response.data;
}

/**
 * Register a new user.
 */
export async function register(data: RegisterData): Promise<{ user: User; message: string }> {
  const response = await apiClient.post('/auth/register/', data);
  return response.data;
}

/**
 * Refresh the access token.
 */
export async function refreshToken(): Promise<TokenResponse> {
  const refresh = localStorage.getItem(REFRESH_KEY);

  if (!refresh) {
    throw new Error('No refresh token available');
  }

  const response = await apiClient.post<TokenResponse>('/auth/token/refresh/', { refresh });

  // Update stored token
  localStorage.setItem(TOKEN_KEY, response.data.access);
  if (response.data.refresh) {
    localStorage.setItem(REFRESH_KEY, response.data.refresh);
  }

  return response.data;
}

/**
 * Get current user profile.
 */
export async function getCurrentUser(): Promise<User> {
  const response = await apiClient.get<User>('/auth/me/');
  return response.data;
}

/**
 * Update user profile.
 */
export async function updateProfile(data: Partial<User>): Promise<User> {
  const response = await apiClient.put<User>('/auth/profile/', data);
  return response.data;
}

/**
 * Change password.
 */
export async function changePassword(oldPassword: string, newPassword: string): Promise<void> {
  await apiClient.post('/auth/change-password/', {
    old_password: oldPassword,
    new_password: newPassword,
  });
}

/**
 * Logout - clear stored tokens.
 */
export function logout(): void {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(REFRESH_KEY);
}

/**
 * Check if user is authenticated.
 */
export function isAuthenticated(): boolean {
  return !!localStorage.getItem(TOKEN_KEY);
}

/**
 * Get stored access token.
 */
export function getAccessToken(): string | null {
  return localStorage.getItem(TOKEN_KEY);
}

export default {
  login,
  register,
  refreshToken,
  getCurrentUser,
  updateProfile,
  changePassword,
  logout,
  isAuthenticated,
  getAccessToken,
};
