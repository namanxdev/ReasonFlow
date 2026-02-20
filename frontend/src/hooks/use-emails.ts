import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import api from "@/lib/api";
import type { Email, EmailFilters, PaginatedResponse } from "@/types";

export function useEmails(filters: EmailFilters) {
  return useQuery({
    queryKey: ["emails", filters.page, filters.page_size, filters.status, filters.classification, filters.search, filters.sort_by, filters.sort_order],
    queryFn: () =>
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
        })
        .then((r) => r.data),
    staleTime: 0,
    gcTime: 5 * 60 * 1000,
    refetchOnWindowFocus: false,
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
