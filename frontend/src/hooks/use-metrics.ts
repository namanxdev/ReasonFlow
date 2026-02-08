import { useQuery } from "@tanstack/react-query";
import api from "@/lib/api";
import type {
  IntentDistribution,
  LatencyDataPoint,
  ToolAccuracy,
  SummaryStats,
} from "@/types";

export function useIntentDistribution(dateFrom?: string, dateTo?: string) {
  return useQuery({
    queryKey: ["metrics", "intents", dateFrom, dateTo],
    queryFn: () =>
      api
        .get<IntentDistribution[]>("/metrics/intents", {
          params: { date_from: dateFrom, date_to: dateTo },
        })
        .then((r) => r.data),
  });
}

export function useLatencyStats(dateFrom?: string, dateTo?: string) {
  return useQuery({
    queryKey: ["metrics", "latency", dateFrom, dateTo],
    queryFn: () =>
      api
        .get<LatencyDataPoint[]>("/metrics/latency", {
          params: { date_from: dateFrom, date_to: dateTo },
        })
        .then((r) => r.data),
  });
}

export function useToolAccuracy() {
  return useQuery({
    queryKey: ["metrics", "tools"],
    queryFn: () =>
      api.get<ToolAccuracy[]>("/metrics/tools").then((r) => r.data),
  });
}

export function useSummaryStats() {
  return useQuery({
    queryKey: ["metrics", "summary"],
    queryFn: () =>
      api.get<SummaryStats>("/metrics/summary").then((r) => r.data),
  });
}
