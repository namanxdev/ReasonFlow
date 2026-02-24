import { describe, it, expect, beforeEach } from 'vitest';
import { useAuthStore } from './auth-store';

describe('Auth Store', () => {
  beforeEach(() => {
    // Reset store to initial state before each test
    useAuthStore.setState({
      user: null,
      accessToken: null,
      refreshToken: null,
      isAuthenticated: false,
      isLoading: false,
    });
  });

  describe('login', () => {
    it('should set user and tokens on login', () => {
      const user = { id: '1', email: 'test@example.com' };
      const accessToken = 'access-token';
      const refreshToken = 'refresh-token';

      useAuthStore.getState().login(user, accessToken, refreshToken);

      const state = useAuthStore.getState();
      expect(state.user).toEqual(user);
      expect(state.accessToken).toBe(accessToken);
      expect(state.refreshToken).toBe(refreshToken);
      expect(state.isAuthenticated).toBe(true);
    });
  });

  describe('logout', () => {
    it('should clear all auth state on logout', () => {
      // First login
      useAuthStore.getState().login(
        { id: '1', email: 'test@example.com' },
        'access-token',
        'refresh-token'
      );

      // Then logout
      useAuthStore.getState().logout();

      const state = useAuthStore.getState();
      expect(state.user).toBeNull();
      expect(state.accessToken).toBeNull();
      expect(state.refreshToken).toBeNull();
      expect(state.isAuthenticated).toBe(false);
    });
  });

  describe('updateAccessToken', () => {
    it('should update only the access token', () => {
      // First login
      useAuthStore.getState().login(
        { id: '1', email: 'test@example.com' },
        'old-access-token',
        'refresh-token'
      );

      // Update access token
      useAuthStore.getState().updateAccessToken('new-access-token');

      const state = useAuthStore.getState();
      expect(state.accessToken).toBe('new-access-token');
      expect(state.refreshToken).toBe('refresh-token');
      expect(state.user).toEqual({ id: '1', email: 'test@example.com' });
      expect(state.isAuthenticated).toBe(true);
    });
  });
});
