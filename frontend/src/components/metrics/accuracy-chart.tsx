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

export function AccuracyChart() {
  const { data, isLoading } = useToolAccuracy();

  if (isLoading) {
    return <SkeletonChart />;
  }

  if (!data || data.length === 0) {
    return <EmptyState />;
  }

  const chartData = data.map((item) => ({
    name: formatToolName(item.tool_name),
    Success: item.successful_calls,
    Failure: item.failed_calls,
    successRate: item.success_rate,
  }));

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
              label={{ value: "Call Count", angle: -90, position: "insideLeft" }}
            />
            <Tooltip
              formatter={(value) => [value, ""]}
              contentStyle={{
                backgroundColor: "hsl(var(--card))",
                border: "1px solid hsl(var(--border))",
                borderRadius: "8px",
              }}
            />
            <Legend wrapperStyle={{ fontSize: "14px" }} />
            <Bar dataKey="Success" stackId="a" fill="#22c55e">
              <LabelList
                dataKey="successRate"
                position="top"
                formatter={(value) => `${Math.round(Number(value) * 100)}%`}
                fontSize={12}
              />
            </Bar>
            <Bar dataKey="Failure" stackId="a" fill="#ef4444" />
          </BarChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}
