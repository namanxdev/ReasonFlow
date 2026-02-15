import { useQuery } from "@tanstack/react-query";
import api from "@/lib/api";
import type {
  IntentDistribution,
  LatencyMetrics,
  ToolAccuracy,
  SummaryStats,
} from "@/types";

export function useIntentDistribution(dateFrom?: string, dateTo?: string) {
  return useQuery({
    queryKey: ["metrics", "intents", dateFrom, dateTo],
    queryFn: () =>
      api
        .get<{ buckets: IntentDistribution[]; total: number }>("/metrics/intents", {
          params: { start: dateFrom, end: dateTo },
        })
        .then((r) => r.data.buckets),
  });
}

export function useLatencyStats(dateFrom?: string, dateTo?: string) {
  return useQuery({
    queryKey: ["metrics", "latency", dateFrom, dateTo],
    queryFn: () =>
      api
        .get<LatencyMetrics>("/metrics/latency", {
          params: { start: dateFrom, end: dateTo },
        })
        .then((r) => r.data),
  });
}

export function useToolAccuracy() {
  return useQuery({
    queryKey: ["metrics", "tools"],
    queryFn: () =>
      api
        .get<{ tools: ToolAccuracy[] }>("/metrics/tools")
        .then((r) => r.data.tools),
  });
}

export function useSummaryStats() {
  return useQuery({
    queryKey: ["metrics", "summary"],
    queryFn: () =>
      api.get<SummaryStats>("/metrics/summary").then((r) => r.data),
  });
}
