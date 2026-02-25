import { useQuery } from "@tanstack/react-query";
import api from "@/lib/api";
import type { TraceRun, TraceDetail, PaginatedResponse, TraceFilters } from "@/types";

export function useTraces(filters: TraceFilters = {}) {
  const { search, status, page = 1, page_size = 20 } = filters;
  return useQuery({
    queryKey: ["traces", filters],
    queryFn: ({ signal }) =>
      api
        .get<PaginatedResponse<TraceRun>>("/traces", {
          params: {
            limit: page_size,
            offset: (page - 1) * page_size,
            search: search || undefined,
            status: status || undefined,
          },
          signal,
        })
        .then((r) => r.data),
    staleTime: 10_000,
    refetchOnWindowFocus: false,
    placeholderData: (previousData) => previousData,
  });
}

export function useTraceDetail(traceId: string) {
  return useQuery({
    queryKey: ["traces", traceId],
    queryFn: () =>
      api.get<TraceDetail>(`/traces/${traceId}`).then((r) => r.data),
    enabled: !!traceId,
    staleTime: 0,
    refetchOnWindowFocus: false,
  });
}
