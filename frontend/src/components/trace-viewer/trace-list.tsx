"use client";

import { useRouter } from "next/navigation";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { ClassificationBadge } from "@/components/inbox/classification-badge";
import type { TraceRun } from "@/types";
import { Activity } from "lucide-react";
import { cn } from "@/lib/utils";

interface TraceListProps {
  traces: TraceRun[];
  isLoading: boolean;
}

function SkeletonRow() {
  return (
    <TableRow>
      <TableCell>
        <div className="h-4 w-64 bg-muted animate-pulse rounded" />
      </TableCell>
      <TableCell>
        <div className="h-6 w-24 bg-muted animate-pulse rounded-full" />
      </TableCell>
      <TableCell>
        <div className="h-4 w-16 bg-muted animate-pulse rounded" />
      </TableCell>
      <TableCell>
        <div className="h-4 w-16 bg-muted animate-pulse rounded" />
      </TableCell>
      <TableCell>
        <div className="h-2 w-2 bg-muted animate-pulse rounded-full" />
      </TableCell>
      <TableCell>
        <div className="h-4 w-20 bg-muted animate-pulse rounded" />
      </TableCell>
    </TableRow>
  );
}

function EmptyState() {
  return (
    <div className="flex flex-col items-center justify-center py-16 text-center">
      <div className="bg-muted/30 rounded-full p-6 mb-4">
        <Activity className="size-12 text-muted-foreground" />
      </div>
      <h3 className="text-lg font-semibold mb-2">No trace runs found</h3>
      <p className="text-muted-foreground text-sm max-w-sm">
        There are no trace runs to display. Process some emails to see traces here.
      </p>
    </div>
  );
}

function formatTime(ms: number): string {
  return (ms / 1000).toFixed(1) + "s";
}

function formatRelativeTime(dateString: string): string {
  const date = new Date(dateString);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffSeconds = Math.floor(diffMs / 1000);
  const diffMinutes = Math.floor(diffSeconds / 60);
  const diffHours = Math.floor(diffMinutes / 60);
  const diffDays = Math.floor(diffHours / 24);

  if (diffSeconds < 60) {
    return "just now";
  } else if (diffMinutes < 60) {
    return `${diffMinutes}m ago`;
  } else if (diffHours < 24) {
    return `${diffHours}h ago`;
  } else if (diffDays < 7) {
    return `${diffDays}d ago`;
  } else {
    return date.toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
      year: date.getFullYear() !== now.getFullYear() ? "numeric" : undefined,
    });
  }
}

const STATUS_CONFIG = {
  completed: {
    color: "bg-green-500",
    label: "Completed",
  },
  failed: {
    color: "bg-red-500",
    label: "Failed",
  },
  in_progress: {
    color: "bg-blue-500",
    label: "In Progress",
  },
} as const;

export function TraceList({ traces, isLoading }: TraceListProps) {
  const router = useRouter();

  if (isLoading) {
    return (
      <div className="border rounded-md">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Email Subject</TableHead>
              <TableHead>Classification</TableHead>
              <TableHead>Total Time</TableHead>
              <TableHead>Steps</TableHead>
              <TableHead>Status</TableHead>
              <TableHead>Date</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {Array.from({ length: 5 }).map((_, i) => (
              <SkeletonRow key={i} />
            ))}
          </TableBody>
        </Table>
      </div>
    );
  }

  if (traces.length === 0) {
    return <EmptyState />;
  }

  return (
    <div className="border rounded-md">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Email Subject</TableHead>
            <TableHead>Classification</TableHead>
            <TableHead>Total Time</TableHead>
            <TableHead>Steps</TableHead>
            <TableHead>Status</TableHead>
            <TableHead>Date</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {traces.map((trace) => {
            const statusConfig = STATUS_CONFIG[trace.status];
            return (
              <TableRow
                key={trace.trace_id}
                onClick={() => router.push(`/traces/${trace.trace_id}`)}
                className="cursor-pointer"
              >
                <TableCell>
                  <span className="font-medium hover:underline">
                    {trace.email_subject}
                  </span>
                </TableCell>
                <TableCell>
                  <ClassificationBadge classification={trace.classification} />
                </TableCell>
                <TableCell>
                  <span className="text-sm text-muted-foreground">
                    {formatTime(trace.total_time_ms)}
                  </span>
                </TableCell>
                <TableCell>
                  <span className="text-sm text-muted-foreground">
                    {trace.step_count} {trace.step_count === 1 ? "step" : "steps"}
                  </span>
                </TableCell>
                <TableCell>
                  <div
                    className="flex items-center gap-2"
                    title={statusConfig.label}
                  >
                    <div
                      className={cn(
                        "size-2 rounded-full",
                        statusConfig.color
                      )}
                    />
                  </div>
                </TableCell>
                <TableCell>
                  <span className="text-sm text-muted-foreground">
                    {formatRelativeTime(trace.created_at)}
                  </span>
                </TableCell>
              </TableRow>
            );
          })}
        </TableBody>
      </Table>
    </div>
  );
}
