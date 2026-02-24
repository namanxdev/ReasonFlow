"use client";

import { useEffect } from "react";
import { useAuthStore } from "@/stores/auth-store";
import api from "@/lib/api";

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const setLoading = useAuthStore((state) => state.setLoading);
  const login = useAuthStore((state) => state.login);

  useEffect(() => {
    const initAuth = async () => {
      // First try to restore from localStorage (for page reloads)
      const storedToken = localStorage.getItem("rf_access_token");
      if (storedToken) {
        try {
          // Decode the JWT to check expiry
          const payload = JSON.parse(atob(storedToken.split(".")[1]));
          const isExpired = payload.exp * 1000 < Date.now();

          if (!isExpired) {
            // Token still valid - restore session
            login(
              { id: "", email: payload.sub || "" },
              storedToken
            );
            return;
          }
        } catch {
          // Invalid token, fall through to refresh
        }
      }

      // Try to refresh using httpOnly cookie
      try {
        const response = await api.post("/auth/refresh", null, {
          // Skip the auth interceptor for this request
          headers: { "X-Skip-Auth": "true" },
        });
        const { access_token } = response.data;
        if (access_token) {
          const payload = JSON.parse(atob(access_token.split(".")[1]));
          localStorage.setItem("rf_access_token", access_token);
          login(
            { id: "", email: payload.sub || "" },
            access_token
          );
        }
      } catch {
        // No valid session - user needs to log in
        localStorage.removeItem("rf_access_token");
      } finally {
        setLoading(false);
      }
    };

    initAuth();
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  return <>{children}</>;
}
