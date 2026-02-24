"use client";

import { create } from "zustand";
import { persist, createJSONStorage } from "zustand/middleware";

/**
 * User data structure
 */
export interface User {
  id: string;
  email: string;
}

/**
 * Authentication state interface
 */
interface AuthState {
  // State
  user: User | null;
  accessToken: string | null;
  refreshToken: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  
  // Actions
  setUser: (user: User | null) => void;
  setTokens: (accessToken: string | null, refreshToken: string | null) => void;
  login: (user: User, accessToken: string, refreshToken: string) => void;
  logout: () => void;
  setLoading: (isLoading: boolean) => void;
  updateAccessToken: (accessToken: string) => void;
}

/**
 * Auth store with Zustand
 * 
 * Note: We persist refresh token for session restoration,
 * but the access token could be kept in memory only for higher security.
 * Current implementation persists both for seamless UX.
 */
export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      // Initial state
      user: null,
      accessToken: null,
      refreshToken: null,
      isAuthenticated: false,
      isLoading: true, // Start loading to check for existing session

      // Actions
      setUser: (user) => set({ user }),
      
      setTokens: (accessToken, refreshToken) => 
        set({ accessToken, refreshToken }),
      
      login: (user, accessToken, refreshToken) =>
        set({
          user,
          accessToken,
          refreshToken,
          isAuthenticated: true,
          isLoading: false,
        }),
      
      logout: () =>
        set({
          user: null,
          accessToken: null,
          refreshToken: null,
          isAuthenticated: false,
          isLoading: false,
        }),
      
      setLoading: (isLoading) => set({ isLoading }),
      
      updateAccessToken: (accessToken) => set({ accessToken }),
    }),
    {
      name: "reasonflow-auth", // Storage key
      storage: createJSONStorage(() => localStorage),
      // Only persist specific fields
      partialize: (state) => ({
        user: state.user,
        accessToken: state.accessToken,
        refreshToken: state.refreshToken,
        isAuthenticated: state.isAuthenticated,
      }),
    }
  )
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
  // This is a safe way to get current state outside of React
  const state = useAuthStore.getState();
  return state.accessToken ? { Authorization: `Bearer ${state.accessToken}` } : {};
}
