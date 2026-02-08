"use client";

import { use, useState } from "react";
import Link from "next/link";
import { AppShell } from "@/components/layout/app-shell";
import { TraceGraph } from "@/components/trace-viewer/trace-graph";
import { StepDetail } from "@/components/trace-viewer/step-detail";
import { ClassificationBadge } from "@/components/inbox/classification-badge";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { useTraceDetail } from "@/hooks/use-traces";
import type { AgentLog } from "@/types";
import { ArrowLeft, Mail, User, Calendar } from "lucide-react";

function formatDate(dateString: string): string {
  const date = new Date(dateString);
  return date.toLocaleString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
    hour: "numeric",
    minute: "2-digit",
    hour12: true,
  });
}

export default function TraceDetailPage({
  params,
}: {
  params: Promise<{ traceId: string }>;
}) {
  const { traceId } = use(params);
  const { data, isLoading } = useTraceDetail(traceId);
  const [selectedStep, setSelectedStep] = useState<AgentLog | null>(null);

  const handleSelectStep = (step: AgentLog) => {
    setSelectedStep(step);
  };

  if (isLoading) {
    return (
      <AppShell>
        <div className="space-y-6">
          <div className="flex items-center gap-4">
            <div className="h-9 w-32 bg-muted animate-pulse rounded" />
            <div className="h-6 w-64 bg-muted animate-pulse rounded" />
          </div>
          <div className="h-48 bg-muted animate-pulse rounded-lg" />
          <div className="h-96 bg-muted animate-pulse rounded-lg" />
        </div>
      </AppShell>
    );
  }

  if (!data) {
    return (
      <AppShell>
        <div className="flex flex-col items-center justify-center py-16 text-center">
          <h3 className="text-lg font-semibold mb-2">Trace not found</h3>
          <p className="text-muted-foreground text-sm mb-4">
            The trace you are looking for does not exist.
          </p>
          <Button asChild variant="default">
            <Link href="/traces">
              <ArrowLeft />
              Back to Traces
            </Link>
          </Button>
        </div>
      </AppShell>
    );
  }

  const { email, steps } = data;

  return (
    <AppShell>
      <div className="space-y-6">
        <div className="flex items-center gap-4">
          <Button asChild variant="outline" size="sm">
            <Link href="/traces">
              <ArrowLeft />
              Back to Traces
            </Link>
          </Button>
        </div>

        <div className="border rounded-lg p-6 bg-card space-y-4">
          <div className="flex items-start justify-between">
            <div className="space-y-3 flex-1">
              <div className="flex items-center gap-2">
                <Mail className="size-5 text-muted-foreground" />
                <h1 className="text-2xl font-bold">{email.subject}</h1>
              </div>

              <div className="flex flex-wrap items-center gap-4 text-sm">
                <div className="flex items-center gap-2">
                  <User className="size-4 text-muted-foreground" />
                  <span className="text-muted-foreground">From:</span>
                  <span className="font-medium">{email.sender}</span>
                </div>

                <div className="flex items-center gap-2">
                  <Calendar className="size-4 text-muted-foreground" />
                  <span className="text-muted-foreground">Received:</span>
                  <span className="font-medium">{formatDate(email.received_at)}</span>
                </div>

                <div className="flex items-center gap-2">
                  <span className="text-muted-foreground">Classification:</span>
                  <ClassificationBadge classification={email.classification} />
                </div>
              </div>
            </div>
          </div>
        </div>

        <div className="space-y-4">
          <div>
            <h2 className="text-xl font-semibold mb-2">Pipeline Execution</h2>
            <p className="text-sm text-muted-foreground">
              Click on a step to view detailed information
            </p>
          </div>

          <div className="border rounded-lg bg-card">
            <TraceGraph
              steps={steps}
              onSelectStep={handleSelectStep}
              selectedStepId={selectedStep?.id}
            />
          </div>
        </div>

        {selectedStep && (
          <div className="space-y-4">
            <Separator />
            <div>
              <h2 className="text-xl font-semibold mb-2">Step Details</h2>
              <p className="text-sm text-muted-foreground">
                Detailed execution information for the selected step
              </p>
            </div>
            <StepDetail step={selectedStep} />
          </div>
        )}

        {!selectedStep && steps.length > 0 && (
          <div className="border rounded-lg p-8 bg-muted/30 text-center">
            <p className="text-muted-foreground">
              Select a step from the pipeline above to view its details
            </p>
          </div>
        )}
      </div>
    </AppShell>
  );
}
