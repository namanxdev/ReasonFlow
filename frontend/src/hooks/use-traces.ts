import { useQuery } from "@tanstack/react-query";
import api from "@/lib/api";
import type { TraceRun, TraceDetail, PaginatedResponse } from "@/types";

export function useTraces(page: number = 1, pageSize: number = 20) {
  return useQuery({
    queryKey: ["traces", page, pageSize],
    queryFn: () =>
      api
        .get<PaginatedResponse<TraceRun>>("/traces", {
          params: { limit: pageSize, offset: (page - 1) * pageSize },
        })
        .then((r) => r.data),
  });
}

export function useTraceDetail(traceId: string) {
  return useQuery({
    queryKey: ["traces", traceId],
    queryFn: () =>
      api.get<TraceDetail>(`/traces/${traceId}`).then((r) => r.data),
    enabled: !!traceId,
  });
}
