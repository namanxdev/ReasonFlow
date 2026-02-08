"use client";

import { useLatencyStats } from "@/hooks/use-metrics";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  ReferenceLine,
} from "recharts";

interface LatencyChartProps {
  dateFrom?: string;
  dateTo?: string;
}

function SkeletonChart() {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Response Latency</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="h-[300px] flex items-center justify-center">
          <div className="w-full h-full bg-muted rounded animate-pulse" />
        </div>
      </CardContent>
    </Card>
  );
}

function EmptyState() {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Response Latency</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="h-[300px] flex items-center justify-center text-muted-foreground">
          No data available
        </div>
      </CardContent>
    </Card>
  );
}

function formatTimestamp(timestamp: string): string {
  const date = new Date(timestamp);
  return date.toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    hour: "2-digit",
  });
}

export function LatencyChart({ dateFrom, dateTo }: LatencyChartProps) {
  const { data, isLoading } = useLatencyStats(dateFrom, dateTo);

  if (isLoading) {
    return <SkeletonChart />;
  }

  if (!data || data.length === 0) {
    return <EmptyState />;
  }

  const chartData = data.map((item) => ({
    timestamp: formatTimestamp(item.timestamp),
    "Total Cycle": item.total_cycle_ms,
    "Classification": item.classification_ms,
    "Generation": item.generation_ms,
  }));

  return (
    <Card>
      <CardHeader>
        <CardTitle>Response Latency</CardTitle>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
            <XAxis
              dataKey="timestamp"
              stroke="hsl(var(--muted-foreground))"
              fontSize={12}
              tickMargin={8}
            />
            <YAxis
              stroke="hsl(var(--muted-foreground))"
              fontSize={12}
              tickMargin={8}
              tickFormatter={(value) => `${value}ms`}
            />
            <Tooltip
              formatter={(value) => [`${value}ms`, ""]}
              contentStyle={{
                backgroundColor: "hsl(var(--card))",
                border: "1px solid hsl(var(--border))",
                borderRadius: "8px",
              }}
            />
            <Legend
              wrapperStyle={{ fontSize: "14px" }}
              iconType="line"
            />
            <ReferenceLine
              y={4000}
              label={{ value: "4s Benchmark", position: "right", fontSize: 12 }}
              stroke="#ef4444"
              strokeDasharray="5 5"
            />
            <Line
              type="monotone"
              dataKey="Total Cycle"
              stroke="#3b82f6"
              strokeWidth={2}
              dot={false}
            />
            <Line
              type="monotone"
              dataKey="Classification"
              stroke="#22c55e"
              strokeWidth={2}
              strokeDasharray="5 5"
              dot={false}
            />
            <Line
              type="monotone"
              dataKey="Generation"
              stroke="#a855f7"
              strokeWidth={2}
              strokeDasharray="5 5"
              dot={false}
            />
          </LineChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}
