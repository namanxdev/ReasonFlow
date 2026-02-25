"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import { AppShellTopNav } from "@/components/layout/app-shell-top-nav";
import { StatsCards } from "@/components/metrics/stats-cards";
import { IntentChart } from "@/components/metrics/intent-chart";
import { LatencyChart } from "@/components/metrics/latency-chart";
import { AccuracyChart } from "@/components/metrics/accuracy-chart";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { BarChart3, TrendingUp, Clock, Target } from "lucide-react";
import { PageHeader, SectionCard, StaggerContainer, StaggerItem, StatCard } from "@/components/layout/dashboard-shell";

export default function MetricsPage() {
  const [dateFrom, setDateFrom] = useState<string>("");
  const [dateTo, setDateTo] = useState<string>("");

  return (
    <AppShellTopNav>
      <StaggerContainer className="space-y-6">
          {/* Header */}
          <StaggerItem>
            <PageHeader
              icon={<BarChart3 className="w-6 h-6 text-violet-600" />}
              iconColor="bg-violet-500/10"
              title="Metrics Dashboard"
              subtitle="Monitor system performance and analytics"
            />
          </StaggerItem>

          {/* Quick Stats */}
          <StaggerItem>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
              <StatCard
                label="Total Emails"
                value="1,284"
                change="+12% from last week"
                changeType="positive"
                icon={<BarChart3 className="w-5 h-5" />}
                color="violet"
              />
              <StatCard
                label="Avg. Response Time"
                value="2.4s"
                change="-0.3s improvement"
                changeType="positive"
                icon={<Clock className="w-5 h-5" />}
                color="blue"
              />
              <StatCard
                label="AI Accuracy"
                value="94.2%"
                change="+2.1% from last week"
                changeType="positive"
                icon={<Target className="w-5 h-5" />}
                color="green"
              />
              <StatCard
                label="Processed Today"
                value="47"
                change="On track with daily avg"
                changeType="neutral"
                icon={<TrendingUp className="w-5 h-5" />}
                color="pink"
              />
            </div>
          </StaggerItem>

          {/* Date Filters */}
          <StaggerItem>
            <SectionCard className="p-4">
              <div className="flex flex-col sm:flex-row gap-4">
                <div className="flex-1">
                  <Label htmlFor="date-from" className="text-sm font-medium text-muted-foreground">
                    From Date
                  </Label>
                  <Input
                    id="date-from"
                    type="date"
                    value={dateFrom}
                    onChange={(e) => setDateFrom(e.target.value)}
                    className="mt-1.5 h-11 bg-white/70 border-white/50"
                  />
                </div>
                <div className="flex-1">
                  <Label htmlFor="date-to" className="text-sm font-medium text-muted-foreground">
                    To Date
                  </Label>
                  <Input
                    id="date-to"
                    type="date"
                    value={dateTo}
                    onChange={(e) => setDateTo(e.target.value)}
                    className="mt-1.5 h-11 bg-white/70 border-white/50"
                  />
                </div>
              </div>
            </SectionCard>
          </StaggerItem>

          {/* Charts Row 1 */}
          <StaggerItem>
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              <div className="lg:col-span-1">
                <SectionCard className="h-full p-5">
                  <IntentChart dateFrom={dateFrom || undefined} dateTo={dateTo || undefined} />
                </SectionCard>
              </div>
              <div className="lg:col-span-2">
                <SectionCard className="h-full p-5">
                  <LatencyChart dateFrom={dateFrom || undefined} dateTo={dateTo || undefined} />
                </SectionCard>
              </div>
            </div>
          </StaggerItem>

          {/* Charts Row 2 */}
          <StaggerItem>
            <SectionCard className="p-5">
              <AccuracyChart dateFrom={dateFrom || undefined} dateTo={dateTo || undefined} />
            </SectionCard>
          </StaggerItem>
      </StaggerContainer>
    </AppShellTopNav>
  );
}
