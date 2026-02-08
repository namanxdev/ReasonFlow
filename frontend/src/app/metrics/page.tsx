"use client";

import { useState } from "react";
import { AppShell } from "@/components/layout/app-shell";
import { StatsCards } from "@/components/metrics/stats-cards";
import { IntentChart } from "@/components/metrics/intent-chart";
import { LatencyChart } from "@/components/metrics/latency-chart";
import { AccuracyChart } from "@/components/metrics/accuracy-chart";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

export default function MetricsPage() {
  const [dateFrom, setDateFrom] = useState<string>("");
  const [dateTo, setDateTo] = useState<string>("");

  return (
    <AppShell>
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Metrics Dashboard</h1>
          <p className="text-muted-foreground mt-1">
            Monitor system performance and analytics
          </p>
        </div>

        <StatsCards />

        <div className="flex flex-col sm:flex-row gap-4">
          <div className="flex-1">
            <Label htmlFor="date-from" className="text-sm font-medium">
              From
            </Label>
            <Input
              id="date-from"
              type="date"
              value={dateFrom}
              onChange={(e) => setDateFrom(e.target.value)}
              className="mt-1.5"
            />
          </div>
          <div className="flex-1">
            <Label htmlFor="date-to" className="text-sm font-medium">
              To
            </Label>
            <Input
              id="date-to"
              type="date"
              value={dateTo}
              onChange={(e) => setDateTo(e.target.value)}
              className="mt-1.5"
            />
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-1">
            <IntentChart dateFrom={dateFrom || undefined} dateTo={dateTo || undefined} />
          </div>
          <div className="lg:col-span-2">
            <LatencyChart dateFrom={dateFrom || undefined} dateTo={dateTo || undefined} />
          </div>
        </div>

        <div className="w-full">
          <AccuracyChart />
        </div>
      </div>
    </AppShell>
  );
}
