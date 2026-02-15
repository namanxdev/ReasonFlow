import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import api from "@/lib/api";
import type { Email, PaginatedResponse } from "@/types";

export function useDrafts() {
  return useQuery({
    queryKey: ["drafts"],
    queryFn: () =>
      api
        .get<PaginatedResponse<Email>>("/drafts")
        .then((r) => r.data.items),
  });
}

export function useApproveDraft() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) =>
      api.post<Email>(`/drafts/${id}/approve`).then((r) => r.data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["drafts"] });
      queryClient.invalidateQueries({ queryKey: ["emails"] });
    },
  });
}

export function useRejectDraft() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) =>
      api.post<Email>(`/drafts/${id}/reject`).then((r) => r.data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["drafts"] });
      queryClient.invalidateQueries({ queryKey: ["emails"] });
    },
  });
}

export function useEditDraft() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({
      id,
      draft_response,
    }: {
      id: string;
      draft_response: string;
    }) =>
      api
        .put<Email>(`/drafts/${id}`, { content: draft_response })
        .then((r) => r.data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["drafts"] });
      queryClient.invalidateQueries({ queryKey: ["emails"] });
    },
  });
}
