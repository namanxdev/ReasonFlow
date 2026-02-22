"use client";

import { use, useEffect, useState } from "react";
import Link from "next/link";
import { motion } from "framer-motion";
import { useReducedMotion } from "@/hooks/use-reduced-motion";
import { AppShellTopNav } from "@/components/layout/app-shell-top-nav";
import { TraceGraph } from "@/components/trace-viewer/trace-graph";
import { StepDetail } from "@/components/trace-viewer/step-detail";
import { ClassificationBadge } from "@/components/inbox/classification-badge";
import { Button } from "@/components/ui/button";
import { useTraceDetail } from "@/hooks/use-traces";
import type { AgentLog } from "@/types";
import { ArrowLeft, Mail, User, Calendar, Activity, Loader2, AlertCircle, Workflow, Info } from "lucide-react";
import { SectionCard, StaggerContainer, StaggerItem } from "@/components/layout/dashboard-shell";

const PIPELINE_STEP_SET = new Set([
  "classify",
  "retrieve",
  "decide",
  "execute",
  "execute_tools",
  "generate",
  "review",
  "dispatch",
]);

function normalizeStepName(stepName: string | null | undefined): string {
  if (!stepName) {
    return "";
  }
  if (stepName === "execute_tools") {
    return "execute";
  }
  return stepName;
}

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
  const reducedMotion = useReducedMotion();

  useEffect(() => {
    if (!data?.steps?.length) {
      setSelectedStep(null);
      return;
    }

    if (
      selectedStep &&
      data.steps.some(
        (step) =>
          step.id === selectedStep.id ||
          normalizeStepName(step.step_name) === normalizeStepName(selectedStep.step_name)
      )
    ) {
      return;
    }

    const preferredStep = data.steps.find((step) =>
      PIPELINE_STEP_SET.has(normalizeStepName(step.step_name))
    );
    setSelectedStep(preferredStep ?? data.steps[0]);
  }, [data, selectedStep]);

  const handleSelectStep = (step: AgentLog) => {
    console.log("Step selected:", step);
    setSelectedStep(step);
  };

  if (isLoading) {
    return (
      <AppShellTopNav>
        <div className="flex items-center justify-center h-[50vh]">
          <div className="relative">
            <div className="absolute inset-0 bg-violet-500/20 blur-xl rounded-full" />
            <Loader2 className="relative size-8 animate-spin text-violet-500" />
          </div>
        </div>
      </AppShellTopNav>
    );
  }

  if (!data) {
    return (
      <AppShellTopNav>
        {reducedMotion ? (
          <div className="flex flex-col items-center justify-center py-16 text-center">
            <div className="w-16 h-16 rounded-2xl bg-slate-100 flex items-center justify-center mb-4">
              <AlertCircle className="size-8 text-slate-500" />
            </div>
            <h3 className="text-lg font-medium mb-2">Trace not found</h3>
            <p className="text-muted-foreground text-sm mb-4">
              The trace you are looking for does not exist.
            </p>
            <Button asChild variant="default" className="bg-gradient-to-r from-violet-600 to-purple-600">
              <Link href="/traces">
                <ArrowLeft className="mr-2 size-4" />
                Back to Traces
              </Link>
            </Button>
          </div>
        ) : (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="flex flex-col items-center justify-center py-16 text-center"
          >
            <div className="w-16 h-16 rounded-2xl bg-slate-100 flex items-center justify-center mb-4">
              <AlertCircle className="size-8 text-slate-500" />
            </div>
            <h3 className="text-lg font-medium mb-2">Trace not found</h3>
            <p className="text-muted-foreground text-sm mb-4">
              The trace you are looking for does not exist.
            </p>
            <Button asChild variant="default" className="bg-gradient-to-r from-violet-600 to-purple-600">
              <Link href="/traces">
                <ArrowLeft className="mr-2 size-4" />
                Back to Traces
              </Link>
            </Button>
          </motion.div>
        )}
      </AppShellTopNav>
    );
  }

  const { email, steps } = data;
  const activeStep =
    selectedStep ??
    steps.find((step) => PIPELINE_STEP_SET.has(normalizeStepName(step.step_name))) ??
    null;

  return (
    <AppShellTopNav>
      <StaggerContainer className="space-y-6">
        <StaggerItem>
          <div className="flex items-center gap-4">
            <Button asChild variant="outline" size="sm" className="gap-2 bg-white/70">
              <Link href="/traces">
                <ArrowLeft className="size-4" />
                Back to Traces
              </Link>
            </Button>
          </div>
        </StaggerItem>

        <StaggerItem>
          <SectionCard>
            <div className="p-6">
              <div className="flex items-start gap-4">
                <div className="w-12 h-12 rounded-2xl bg-violet-500/10 flex items-center justify-center flex-shrink-0">
                  <Mail className="w-6 h-6 text-violet-600" />
                </div>
                <div className="flex-1 min-w-0">
                  <h1 className="text-xl font-medium">{email.subject}</h1>
                  <div className="flex flex-wrap items-center gap-4 text-sm mt-2">
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
          </SectionCard>
        </StaggerItem>

        <StaggerItem>
          <SectionCard>
            <div className="p-5 border-b bg-gradient-to-r from-violet-50/50 to-purple-50/50">
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 rounded-xl bg-violet-500/10 flex items-center justify-center">
                  <Activity className="w-4 h-4 text-violet-600" />
                </div>
                <div>
                  <h3 className="font-medium">Pipeline Execution</h3>
                  <p className="text-xs text-muted-foreground">Click on a step to view details</p>
                </div>
              </div>
            </div>
            <div className="p-5">
              <TraceGraph
                steps={steps}
                onSelectStep={handleSelectStep}
                selectedStepId={selectedStep?.id}
              />
            </div>
          </SectionCard>
        </StaggerItem>

        {activeStep && (
          <StaggerItem>
            {reducedMotion ? (
              <div key={activeStep.id ?? activeStep.step_name}>
                <SectionCard>
                  <div className="p-5 border-b bg-gradient-to-r from-blue-50/50 to-violet-50/50">
                    <div className="flex items-center gap-2">
                      <Workflow className="w-4 h-4 text-blue-500" />
                      <span className="text-sm font-medium">Step Details</span>
                      <span className="text-xs text-slate-400 ml-2">({activeStep.step_name})</span>
                    </div>
                  </div>
                  <div className="p-5">
                    <StepDetail step={activeStep} />
                  </div>
                </SectionCard>
              </div>
            ) : (
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                key={activeStep.id ?? activeStep.step_name}
              >
                <SectionCard>
                  <div className="p-5 border-b bg-gradient-to-r from-blue-50/50 to-violet-50/50">
                    <div className="flex items-center gap-2">
                      <Workflow className="w-4 h-4 text-blue-500" />
                      <span className="text-sm font-medium">Step Details</span>
                      <span className="text-xs text-slate-400 ml-2">({activeStep.step_name})</span>
                    </div>
                  </div>
                  <div className="p-5">
                    <StepDetail step={activeStep} />
                  </div>
                </SectionCard>
              </motion.div>
            )}
          </StaggerItem>
        )}

        {!activeStep && steps.length > 0 && (
          <StaggerItem>
            <div className="border rounded-xl p-8 bg-slate-50/50 text-center flex flex-col items-center gap-3">
              <Info className="size-8 text-slate-400" />
              <p className="text-muted-foreground">
                Select a step from the pipeline above to view its details
              </p>
            </div>
          </StaggerItem>
        )}

        {steps.length === 0 && (
          <StaggerItem>
            <div className="border rounded-xl p-8 bg-amber-50/50 text-center">
              <AlertCircle className="size-8 text-amber-500 mx-auto mb-2" />
              <p className="text-amber-700">No step data available for this trace.</p>
            </div>
          </StaggerItem>
        )}
      </StaggerContainer>
    </AppShellTopNav>
  );
}
