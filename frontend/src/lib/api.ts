import axios from "axios";
import { toast } from "sonner";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export const api = axios.create({
  baseURL: `${API_BASE_URL}/api/v1`,
  headers: {
    "Content-Type": "application/json",
  },
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
 * Refresh the access token using the refresh token
 * @returns Promise that resolves when refresh is complete
 */
async function refreshToken(): Promise<void> {
  const refreshTokenValue = localStorage.getItem("rf_refresh_token");
  if (!refreshTokenValue) {
    throw new Error("No refresh token available");
  }

  const response = await axios.post(
    `${API_BASE_URL}/api/v1/auth/refresh`,
    {},
    {
      headers: {
        Authorization: `Bearer ${refreshTokenValue}`,
        "Content-Type": "application/json",
      },
    }
  );

  const { access_token } = response.data;
  localStorage.setItem("rf_access_token", access_token);
}

// Request interceptor — attach JWT token and proactively refresh if expiring soon
api.interceptors.request.use(
  async (config) => {
    if (typeof window !== "undefined") {
      const token = localStorage.getItem("rf_access_token");
      if (token && isTokenExpiringSoon(token, TOKEN_EXPIRY_BUFFER_SECONDS)) {
        // Trigger refresh before the request
        try {
          await refreshToken();
          const newToken = localStorage.getItem("rf_access_token");
          if (newToken) {
            config.headers.Authorization = `Bearer ${newToken}`;
          }
        } catch {
          // Refresh failed - show toast, clear tokens, and redirect to login
          toast.error("Your session has expired. Please log in again.");
          localStorage.removeItem("rf_access_token");
          localStorage.removeItem("rf_refresh_token");
          setTimeout(() => {
            window.location.href = "/login?reason=session_expired";
          }, 100);
        }
      } else if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
    }
    return config;
  },
  (error) => Promise.reject(error)
);

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
          const refreshToken = localStorage.getItem("rf_refresh_token");
          if (!refreshToken) {
            throw new Error("No refresh token available");
          }

          const response = await axios.post(
            `${API_BASE_URL}/api/v1/auth/refresh`,
            {},
            {
              headers: {
                Authorization: `Bearer ${refreshToken}`,
                "Content-Type": "application/json",
              },
            }
          );

          const { access_token } = response.data;
          localStorage.setItem("rf_access_token", access_token);
          isRefreshing = false;
          onTokenRefreshed(access_token);

          originalRequest.headers.Authorization = `Bearer ${access_token}`;
          return api(originalRequest);
        } catch {
          isRefreshing = false;
          refreshSubscribers = [];
          toast.error("Your session has expired. Please log in again.");
          localStorage.removeItem("rf_access_token");
          localStorage.removeItem("rf_refresh_token");
          setTimeout(() => {
            window.location.href = "/login?reason=session_expired";
          }, 100);
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
      toast.error("Your session has expired. Please log in again.");
      localStorage.removeItem("rf_access_token");
      localStorage.removeItem("rf_refresh_token");
      setTimeout(() => {
        window.location.href = "/login?reason=session_expired";
      }, 100);
    }
    return Promise.reject(error);
  }
);

export default api;
