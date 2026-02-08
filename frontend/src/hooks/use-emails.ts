import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import api from "@/lib/api";
import type { Email, EmailFilters, PaginatedResponse } from "@/types";

export function useEmails(filters: EmailFilters) {
  return useQuery({
    queryKey: ["emails", filters],
    queryFn: () =>
      api
        .get<PaginatedResponse<Email>>("/emails", { params: filters })
        .then((r) => r.data),
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
      api.post<{ new_count: number }>("/emails/sync").then((r) => r.data),
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
