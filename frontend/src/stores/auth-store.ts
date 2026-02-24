"use client";

import { create } from "zustand";

/**
 * User data structure
 */
export interface User {
  id: string;
  email: string;
}

/**
 * Authentication state interface
 * 
 * SECURITY NOTE: The access token is stored in memory only (not in localStorage
 * or cookies) to prevent XSS attacks. The refresh token is stored in an httpOnly
 * cookie that is inaccessible to JavaScript.
 * 
 * This implements the SEC-3 fix for JWT security.
 */
interface AuthState {
  // State
  user: User | null;
  accessToken: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  
  // Actions
  setUser: (user: User | null) => void;
  login: (user: User, accessToken: string) => void;
  logout: () => void;
  setLoading: (isLoading: boolean) => void;
  updateAccessToken: (accessToken: string) => void;
}

/**
 * Auth store with Zustand
 * 
 * IMPORTANT: This store does NOT persist the access token. The token is kept
 * in memory only and will be lost on page refresh. On refresh, the app should
 * call the /auth/refresh endpoint (which uses the httpOnly cookie) to get a
 * new access token.
 * 
 * This is the secure approach recommended for SPAs to prevent XSS token theft.
 */
export const useAuthStore = create<AuthState>()(
  (set) => ({
    // Initial state - no persistence for security
    user: null,
    accessToken: null,
    isAuthenticated: false,
    isLoading: true, // Start loading to check for existing session

    // Actions
    setUser: (user) => set({ user }),
    
    login: (user, accessToken) =>
      set({
        user,
        accessToken,
        isAuthenticated: true,
        isLoading: false,
      }),
    
    logout: () =>
      set({
        user: null,
        accessToken: null,
        isAuthenticated: false,
        isLoading: false,
      }),
    
    setLoading: (isLoading) => set({ isLoading }),
    
    updateAccessToken: (accessToken) => set({ accessToken }),
  })
);

/**
 * Hook to get the current auth headers for API requests
 */
export function useAuthHeaders(): { Authorization?: string } {
  const { accessToken } = useAuthStore();
  return accessToken ? { Authorization: `Bearer ${accessToken}` } : {};
}

/**
 * Get auth headers outside of React components
 */
export function getAuthHeaders(): { Authorization?: string } {
  const state = useAuthStore.getState();
  return state.accessToken ? { Authorization: `Bearer ${state.accessToken}` } : {};
}
