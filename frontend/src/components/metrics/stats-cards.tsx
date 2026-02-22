"use client";

import { useSummaryStats } from "@/hooks/use-metrics";
import { Card, CardContent } from "@/components/ui/card";
import { Mail, Clock, CheckCircle, Eye } from "lucide-react";
import { motion } from "framer-motion";
import { useReducedMotion } from "@/hooks/use-reduced-motion";

interface StatCardProps {
  title: string;
  value: string;
  icon: React.ReactNode;
  index: number;
  reducedMotion: boolean;
}

function StatCard({ title, value, icon, index, reducedMotion }: StatCardProps) {
  if (reducedMotion) {
    return (
      <Card>
        <CardContent className="flex flex-col gap-2">
          <div className="flex items-start justify-between">
            <div className="flex-1">
              <p className="text-2xl font-bold">{value}</p>
              <p className="text-sm text-muted-foreground mt-1">{title}</p>
            </div>
            <div className="text-muted-foreground">{icon}</div>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3, delay: index * 0.05 }}
    >
      <Card>
        <CardContent className="flex flex-col gap-2">
          <div className="flex items-start justify-between">
            <div className="flex-1">
              <p className="text-2xl font-bold">{value}</p>
              <p className="text-sm text-muted-foreground mt-1">{title}</p>
            </div>
            <div className="text-muted-foreground">{icon}</div>
          </div>
        </CardContent>
      </Card>
    </motion.div>
  );
}

function SkeletonCard() {
  return (
    <Card>
      <CardContent className="flex flex-col gap-2">
        <div className="flex items-start justify-between">
          <div className="flex-1 space-y-2">
            <div className="h-8 w-24 bg-muted rounded animate-pulse" />
            <div className="h-4 w-32 bg-muted rounded animate-pulse" />
          </div>
          <div className="size-5 bg-muted rounded animate-pulse" />
        </div>
      </CardContent>
    </Card>
  );
}

export function StatsCards() {
  const { data, isLoading } = useSummaryStats();
  const reducedMotion = useReducedMotion();

  if (isLoading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {[...Array(4)].map((_, i) => (
          <SkeletonCard key={i} />
        ))}
      </div>
    );
  }

  if (!data) {
    return null;
  }

  const stats = [
    {
      title: "Emails Processed",
      value: data.total_emails_processed.toLocaleString(),
      icon: <Mail className="size-5" />,
    },
    {
      title: "Avg Response Time",
      value: `${(data.average_response_time_ms / 1000).toFixed(1)}s`,
      icon: <Clock className="size-5" />,
    },
    {
      title: "Approval Rate",
      value: `${Math.round(data.approval_rate * 100)}%`,
      icon: <CheckCircle className="size-5" />,
    },
    {
      title: "Human Review Rate",
      value: `${Math.round(data.human_review_rate * 100)}%`,
      icon: <Eye className="size-5" />,
    },
  ];

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
      {stats.map((stat, index) => (
        <StatCard
          key={stat.title}
          title={stat.title}
          value={stat.value}
          icon={stat.icon}
          index={index}
          reducedMotion={reducedMotion}
        />
      ))}
    </div>
  );
}
