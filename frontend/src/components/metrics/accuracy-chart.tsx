"use client";

import { useToolAccuracy } from "@/hooks/use-metrics";
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
  Cell,
  LabelList,
} from "recharts";

interface AccuracyChartProps {
  dateFrom?: string;
  dateTo?: string;
}

function SkeletonChart() {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Tool Accuracy</CardTitle>
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
        <CardTitle>Tool Accuracy</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="h-[300px] flex items-center justify-center text-muted-foreground">
          No data available
        </div>
      </CardContent>
    </Card>
  );
}

function formatToolName(toolName: string): string {
  return toolName
    .split("_")
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(" ");
}

interface CustomTooltipProps {
  active?: boolean;
  payload?: Array<{
    name: string;
    value: number;
    payload: {
      name: string;
      successRate: number;
      failureRate: number;
      successfulCalls: number;
      failedCalls: number;
    };
  }>;
  label?: string;
}

function CustomTooltip({ active, payload, label }: CustomTooltipProps) {
  if (!active || !payload || !payload.length) return null;
  const data = payload[0].payload;
  return (
    <div
      style={{
        backgroundColor: "hsl(var(--card))",
        border: "1px solid hsl(var(--border))",
        borderRadius: "8px",
        padding: "12px",
        fontSize: "13px",
      }}
    >
      <p style={{ fontWeight: 600, marginBottom: 4 }}>{label}</p>
      <p style={{ color: "#22c55e" }}>
        Success: {data.successRate.toFixed(1)}% ({data.successfulCalls} calls)
      </p>
      <p style={{ color: "#ef4444" }}>
        Failure: {data.failureRate.toFixed(1)}% ({data.failedCalls} calls)
      </p>
    </div>
  );
}

export function AccuracyChart({ dateFrom, dateTo }: AccuracyChartProps) {
  const { data, isLoading } = useToolAccuracy(dateFrom, dateTo);

  if (isLoading) {
    return <SkeletonChart />;
  }

  if (!data || data.length === 0) {
    return <EmptyState />;
  }

  const chartData = data.map((item) => {
    const successRate = item.success_rate * 100;
    const failureRate = 100 - successRate;
    return {
      name: formatToolName(item.tool_name),
      successRate,
      failureRate,
      successfulCalls: item.successful_calls,
      failedCalls: item.failed_calls,
    };
  });

  return (
    <Card>
      <CardHeader>
        <CardTitle>Tool Accuracy</CardTitle>
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
              domain={[0, 100]}
              tickFormatter={(value) => `${value}%`}
              label={{ value: "Success Rate (%)", angle: -90, position: "insideLeft", offset: -5 }}
            />
            <Tooltip content={<CustomTooltip />} />
            <Legend wrapperStyle={{ fontSize: "14px" }} />
            <Bar dataKey="successRate" name="Success" stackId="a" fill="#22c55e" radius={[0, 0, 0, 0]}>
              <LabelList
                dataKey="successRate"
                position="top"
                formatter={(value: string | number | boolean | null | undefined) => `${Math.round(Number(value))}%`}
                fontSize={12}
                fill="hsl(var(--foreground))"
              />
            </Bar>
            <Bar dataKey="failureRate" name="Failure" stackId="a" fill="#ef4444" radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}
