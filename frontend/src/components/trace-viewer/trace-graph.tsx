"use client";

import { PIPELINE_STEPS, TRACE_NODE_COLORS } from "@/lib/constants";
import type { AgentLog } from "@/types";
import { cn } from "@/lib/utils";
import { ChevronRight } from "lucide-react";

interface TraceGraphProps {
  steps: AgentLog[];
  onSelectStep: (step: AgentLog) => void;
  selectedStepId?: string;
}

function formatStepName(stepName: string): string {
  return stepName
    .split("_")
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(" ");
}

function formatLatency(ms: number): string {
  return `${ms}ms`;
}

function getStepStatus(
  stepName: string,
  steps: AgentLog[]
): "completed" | "failed" | "skipped" | "human_queue" {
  const step = steps.find((s) => s.step_name === stepName);

  if (!step) {
    return "skipped";
  }

  if (stepName === "review" && step.error_message === null) {
    return "human_queue";
  }

  if (step.error_message !== null) {
    return "failed";
  }

  return "completed";
}

function getNodeColors(status: "completed" | "failed" | "skipped" | "human_queue") {
  switch (status) {
    case "completed":
      return {
        border: "border-green-500",
        bg: "bg-green-50 dark:bg-green-950/30",
        text: "text-green-700 dark:text-green-300",
      };
    case "failed":
      return {
        border: "border-red-500",
        bg: "bg-red-50 dark:bg-red-950/30",
        text: "text-red-700 dark:text-red-300",
      };
    case "skipped":
      return {
        border: "border-amber-500",
        bg: "bg-amber-50 dark:bg-amber-950/30",
        text: "text-amber-700 dark:text-amber-300",
      };
    case "human_queue":
      return {
        border: "border-blue-500",
        bg: "bg-blue-50 dark:bg-blue-950/30",
        text: "text-blue-700 dark:text-blue-300",
      };
  }
}

export function TraceGraph({ steps, onSelectStep, selectedStepId }: TraceGraphProps) {
  return (
    <div className="w-full overflow-x-auto">
      <div className="inline-flex items-center gap-2 min-w-full p-4">
        {PIPELINE_STEPS.map((stepName, index) => {
          const step = steps.find((s) => s.step_name === stepName);
          const status = getStepStatus(stepName, steps);
          const colors = getNodeColors(status);
          const isSelected = step && step.id === selectedStepId;

          return (
            <div key={stepName} className="flex items-center gap-2">
              <button
                onClick={() => step && onSelectStep(step)}
                disabled={!step}
                className={cn(
                  "rounded-lg border-2 px-4 py-3 min-w-[140px] transition-all",
                  colors.border,
                  colors.bg,
                  colors.text,
                  step && "hover:shadow-md cursor-pointer",
                  !step && "opacity-50 cursor-not-allowed",
                  isSelected && "ring-4 ring-ring/50"
                )}
              >
                <div className="space-y-1">
                  <div className="font-semibold text-sm">
                    {formatStepName(stepName)}
                  </div>
                  {step ? (
                    <div className="text-xs opacity-75">
                      {formatLatency(step.latency_ms)}
                    </div>
                  ) : (
                    <div className="text-xs opacity-75">Skipped</div>
                  )}
                </div>
              </button>

              {index < PIPELINE_STEPS.length - 1 && (
                <ChevronRight className="size-5 text-muted-foreground flex-shrink-0" />
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
