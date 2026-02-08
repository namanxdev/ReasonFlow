"use client";

import { useIntentDistribution } from "@/hooks/use-metrics";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip, Legend } from "recharts";
import { CHART_COLORS } from "@/lib/constants";

interface IntentChartProps {
  dateFrom?: string;
  dateTo?: string;
}

function SkeletonChart() {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Intent Distribution</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="h-[300px] flex items-center justify-center">
          <div className="size-48 rounded-full bg-muted animate-pulse" />
        </div>
      </CardContent>
    </Card>
  );
}

function EmptyState() {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Intent Distribution</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="h-[300px] flex items-center justify-center text-muted-foreground">
          No data available
        </div>
      </CardContent>
    </Card>
  );
}

function formatLabel(classification: string): string {
  return classification
    .split("_")
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(" ");
}

export function IntentChart({ dateFrom, dateTo }: IntentChartProps) {
  const { data, isLoading } = useIntentDistribution(dateFrom, dateTo);

  if (isLoading) {
    return <SkeletonChart />;
  }

  if (!data || data.length === 0) {
    return <EmptyState />;
  }

  const chartData = data.map((item) => ({
    name: formatLabel(item.classification),
    value: item.count,
    percentage: item.percentage,
  }));

  return (
    <Card>
      <CardHeader>
        <CardTitle>Intent Distribution</CardTitle>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={300}>
          <PieChart>
            <Pie
              data={chartData}
              cx="50%"
              cy="50%"
              innerRadius={60}
              outerRadius={100}
              paddingAngle={2}
              dataKey="value"
            >
              {chartData.map((_, index) => (
                <Cell
                  key={`cell-${index}`}
                  fill={CHART_COLORS[index % CHART_COLORS.length]}
                />
              ))}
            </Pie>
            <Tooltip
              formatter={(value, name, props: any) => [
                `${value} (${props?.payload?.percentage?.toFixed(1) ?? 0}%)`,
                name ?? "",
              ]}
              contentStyle={{
                backgroundColor: "hsl(var(--card))",
                border: "1px solid hsl(var(--border))",
                borderRadius: "8px",
              }}
            />
            <Legend
              verticalAlign="bottom"
              height={36}
              formatter={(value, entry: any) => (
                <span className="text-sm">{value}</span>
              )}
            />
          </PieChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}
