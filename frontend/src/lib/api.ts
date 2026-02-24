import axios from "axios";
import { toast } from "sonner";
import { useAuthStore } from "@/stores";
import { getCSRFHeaders, requiresCSRF } from "./csrf";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// Axios instance for API calls
export const api = axios.create({
  baseURL: `${API_BASE_URL}/api/v1`,
  headers: {
    "Content-Type": "application/json",
  },
  withCredentials: true, // Include cookies in requests
});

// Separate instance for auth calls that handles 401 differently
export const authApi = axios.create({
  baseURL: `${API_BASE_URL}/api/v1`,
  headers: {
    "Content-Type": "application/json",
  },
  withCredentials: true,
});

// Buffer time in seconds before token expiration to trigger proactive refresh
const TOKEN_EXPIRY_BUFFER_SECONDS = 60;

/**
 * Decode JWT payload and check if token is expiring soon
 * @param token - JWT access token
 * @param bufferSeconds - Time buffer before expiration (default: 60 seconds)
 * @returns true if token is expiring soon or invalid
 */
function isTokenExpiringSoon(token: string, bufferSeconds: number = TOKEN_EXPIRY_BUFFER_SECONDS): boolean {
  try {
    const payload = JSON.parse(atob(token.split('.')[1]));
    const exp = payload.exp * 1000; // Convert to milliseconds
    return Date.now() + bufferSeconds * 1000 >= exp;
  } catch {
    return true; // Treat invalid tokens as expired
  }
}

/**
 * Refresh the access token using the httpOnly cookie
 * @returns Promise that resolves when refresh is complete
 */
async function refreshToken(): Promise<string> {
  const response = await authApi.post("/auth/refresh", {});
  const { access_token } = response.data;
  useAuthStore.getState().updateAccessToken(access_token);
  return access_token;
}

/**
 * Logout the user and redirect to login page
 */
async function handleLogout(reason: string = "session_expired"): Promise<void> {
  try {
    // Call logout endpoint to clear httpOnly cookie
    await authApi.post("/auth/logout", {});
  } catch {
    // Ignore errors during logout
  }
  useAuthStore.getState().logout();
  toast.error("Your session has expired. Please log in again.");
  setTimeout(() => {
    window.location.href = `/login?reason=${reason}`;
  }, 100);
}

// Track whether a token refresh is already in-flight to avoid duplicate calls.
let isRefreshing = false;
let refreshSubscribers: Array<(token: string) => void> = [];

function subscribeTokenRefresh(cb: (token: string) => void) {
  refreshSubscribers.push(cb);
}

function onTokenRefreshed(newToken: string) {
  refreshSubscribers.forEach((cb) => cb(newToken));
  refreshSubscribers = [];
}

// Request interceptor — attach JWT token and proactively refresh if expiring soon
// Also adds CSRF token for state-changing requests
api.interceptors.request.use(
  async (config) => {
    if (typeof window !== "undefined") {
      const { accessToken } = useAuthStore.getState();
      
      // Add auth token
      if (accessToken && isTokenExpiringSoon(accessToken, TOKEN_EXPIRY_BUFFER_SECONDS)) {
        // Trigger refresh before the request
        try {
          const newToken = await refreshToken();
          config.headers.Authorization = `Bearer ${newToken}`;
        } catch {
          // Refresh failed - logout and redirect
          handleLogout("session_expired");
        }
      } else if (accessToken) {
        config.headers.Authorization = `Bearer ${accessToken}`;
      }
      
      // Add CSRF token for state-changing requests
      if (config.method && requiresCSRF(config.method)) {
        const csrfHeaders = getCSRFHeaders();
        Object.assign(config.headers, csrfHeaders);
      }
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor — attempt token refresh on 401, fallback to login redirect
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    // Only attempt refresh once per request, and skip for auth endpoints
    if (
      error.response?.status === 401 &&
      !originalRequest._retry &&
      typeof window !== "undefined" &&
      !originalRequest.url?.includes("/auth/login") &&
      !originalRequest.url?.includes("/auth/register") &&
      !originalRequest.url?.includes("/auth/refresh")
    ) {
      originalRequest._retry = true;

      if (!isRefreshing) {
        isRefreshing = true;

        try {
          const newToken = await refreshToken();
          isRefreshing = false;
          onTokenRefreshed(newToken);

          originalRequest.headers.Authorization = `Bearer ${newToken}`;
          return api(originalRequest);
        } catch {
          isRefreshing = false;
          refreshSubscribers = [];
          handleLogout("session_expired");
          return Promise.reject(error);
        }
      } else {
        // Another refresh is in-flight; queue this request
        return new Promise((resolve) => {
          subscribeTokenRefresh((newToken: string) => {
            originalRequest.headers.Authorization = `Bearer ${newToken}`;
            resolve(api(originalRequest));
          });
        });
      }
    }

    // Non-401 or already retried — reject
    if (error.response?.status === 401 && typeof window !== "undefined") {
      handleLogout("session_expired");
    }
    return Promise.reject(error);
  }
);

export default api;
