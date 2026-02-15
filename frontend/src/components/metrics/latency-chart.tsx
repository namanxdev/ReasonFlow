"use client";

import { useLatencyStats } from "@/hooks/use-metrics";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
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
          No latency data available yet
        </div>
      </CardContent>
    </Card>
  );
}

export function LatencyChart({ dateFrom, dateTo }: LatencyChartProps) {
  const { data, isLoading } = useLatencyStats(dateFrom, dateTo);

  if (isLoading) {
    return <SkeletonChart />;
  }

  if (!data || data.sample_count === 0) {
    return <EmptyState />;
  }

  // Build chart data: overall + each step
  const chartData = [
    { name: "Overall", ...data.overall },
    ...Object.entries(data.by_step).map(([step, stats]) => ({
      name: step.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase()),
      ...stats,
    })),
  ];

  return (
    <Card>
      <CardHeader>
        <CardTitle>
          Response Latency
          <span className="ml-2 text-sm font-normal text-muted-foreground">
            ({data.sample_count} traces)
          </span>
        </CardTitle>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
            <XAxis
              dataKey="name"
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
              formatter={(value: number) => [`${value.toFixed(1)}ms`]}
              contentStyle={{
                backgroundColor: "hsl(var(--card))",
                border: "1px solid hsl(var(--border))",
                borderRadius: "8px",
              }}
            />
            <Legend wrapperStyle={{ fontSize: "14px" }} />
            <Bar dataKey="p50" name="Median (p50)" fill="#3b82f6" />
            <Bar dataKey="p90" name="p90" fill="#f59e0b" />
            <Bar dataKey="p99" name="p99" fill="#ef4444" />
          </BarChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}
