import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import api from "@/lib/api";
import type { Email, EmailFilters, EmailStats, PaginatedResponse } from "@/types";

const POLLING_INTERVAL = 30000; // 30 seconds

export function useEmails(filters: EmailFilters) {
  return useQuery({
    queryKey: ["emails", filters],
    queryFn: ({ signal }) =>
      api
        .get<PaginatedResponse<Email>>("/emails", {
          params: {
            status: filters.status,
            classification: filters.classification,
            search: filters.search,
            page: filters.page,
            per_page: filters.page_size,
            sort_by: filters.sort_by,
            sort_order: filters.sort_order,
          },
          signal,
        })
        .then((r) => r.data),
    staleTime: 10_000,
    gcTime: 5 * 60 * 1000,
    // Real-time updates configuration
    refetchInterval: POLLING_INTERVAL,
    refetchIntervalInBackground: false, // Don't poll when tab is hidden
    refetchOnWindowFocus: true, // Refresh when user returns to tab
    placeholderData: (previousData) => previousData,
  });
}

export function useEmail(id: string) {
  return useQuery({
    queryKey: ["emails", id],
    queryFn: () => api.get<Email>(`/emails/${id}`).then((r) => r.data),
    enabled: !!id,
  });
}

export function useSyncEmails() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () =>
      api.post<{ fetched: number; created: number }>("/emails/sync").then((r) => r.data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["emails"] });
    },
  });
}

export function useClassifyEmails() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () =>
      api.post<{ classified: number; failed: number }>("/emails/classify").then((r) => r.data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["emails"] });
    },
  });
}

export function useProcessEmail() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) =>
      api.post<Email>(`/emails/${id}/process`).then((r) => r.data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["emails"] });
    },
  });
}

export function useEmailStats() {
  return useQuery({
    queryKey: ["emails", "stats"],
    queryFn: () => api.get<EmailStats>("/emails/stats").then((r) => r.data),
    refetchInterval: 30000,
  });
}

export function useSyncStatus() {
  return useQuery({
    queryKey: ["emails", "sync-status"],
    queryFn: () =>
      api
        .get<{ auto_sync_active: boolean; gmail_connected: boolean }>("/emails/sync/status")
        .then((r) => r.data),
    refetchInterval: 60000,
  });
}
