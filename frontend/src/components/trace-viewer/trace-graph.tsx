"use client";

import { motion } from "framer-motion";
import { PIPELINE_STEPS } from "@/lib/constants";
import type { AgentLog } from "@/types";
import { cn } from "@/lib/utils";
import { ChevronRight, Check, X, Minus, User } from "lucide-react";
import { useReducedMotion } from "@/hooks/use-reduced-motion";

interface TraceGraphProps {
  steps: AgentLog[];
  onSelectStep: (step: AgentLog) => void;
  selectedStepId?: string;
}

function normalizeStepName(stepName: string): string {
  if (stepName === "execute_tools") {
    return "execute";
  }
  return stepName;
}

function formatStepName(stepName: string): string {
  return stepName
    .split("_")
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(" ");
}

function formatLatency(ms: number): string {
  if (ms < 1000) return `${ms}ms`;
  return `${(ms / 1000).toFixed(1)}s`;
}

function getStepStatus(stepName: string, steps: AgentLog[]): "completed" | "failed" | "skipped" | "human_queue" {
  const step = steps.find((s) => normalizeStepName(s.step_name) === stepName);

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

function getStatusConfig(status: "completed" | "failed" | "skipped" | "human_queue") {
  switch (status) {
    case "completed":
      return {
        border: "border-green-500",
        bg: "bg-gradient-to-br from-green-50 to-emerald-50",
        text: "text-green-700",
        icon: Check,
        iconBg: "bg-green-500",
        shadow: "shadow-green-500/20",
      };
    case "failed":
      return {
        border: "border-red-500",
        bg: "bg-gradient-to-br from-red-50 to-rose-50",
        text: "text-red-700",
        icon: X,
        iconBg: "bg-red-500",
        shadow: "shadow-red-500/20",
      };
    case "skipped":
      return {
        border: "border-slate-300",
        bg: "bg-gradient-to-br from-slate-50 to-gray-50",
        text: "text-slate-500",
        icon: Minus,
        iconBg: "bg-slate-400",
        shadow: "shadow-slate-500/10",
      };
    case "human_queue":
      return {
        border: "border-blue-500",
        bg: "bg-gradient-to-br from-blue-50 to-indigo-50",
        text: "text-blue-700",
        icon: User,
        iconBg: "bg-blue-500",
        shadow: "shadow-blue-500/20",
      };
  }
}

export function TraceGraph({ steps, onSelectStep, selectedStepId }: TraceGraphProps) {
  const reducedMotion = useReducedMotion();

  return (
    <div className="w-full overflow-x-auto pb-2">
      <div className="inline-flex items-center gap-3 min-w-full p-2">
        {PIPELINE_STEPS.map((stepName, index) => {
          const step = steps.find((s) => normalizeStepName(s.step_name) === stepName);
          const status = getStepStatus(stepName, steps);
          const config = getStatusConfig(status);
          const StatusIcon = config.icon;
          const isSelected = step && step.id === selectedStepId;
          const hasStep = !!step;

          const stepContent = (
            <>
              {/* Status Icon */}
              <div className={cn(
                "absolute -top-3 -right-3 w-8 h-8 rounded-full flex items-center justify-center shadow-lg",
                config.iconBg,
                config.shadow
              )}>
                <StatusIcon className="size-4 text-white" />
              </div>

              <div className="space-y-2">
                {/* Step Name */}
                <div className="font-semibold text-sm pr-4">
                  {formatStepName(stepName)}
                </div>

                {/* Latency */}
                {step ? (
                  <div className="flex items-center gap-1.5 text-xs opacity-80">
                    <span className="w-1.5 h-1.5 rounded-full bg-current" />
                    {formatLatency(step.latency_ms)}
                  </div>
                ) : (
                  <div className="flex items-center gap-1.5 text-xs opacity-60">
                    <span className="w-1.5 h-1.5 rounded-full bg-current" />
                    Skipped
                  </div>
                )}
              </div>

              {/* Selected indicator */}
              {isSelected && reducedMotion && (
                <div className="absolute inset-0 rounded-2xl border-2 border-violet-500 pointer-events-none" />
              )}
            </>
          );

          const buttonClassName = cn(
            "relative rounded-2xl border-2 px-5 py-4 min-w-[160px] transition-all duration-200",
            config.border,
            config.bg,
            config.text,
            hasStep && "hover:shadow-lg cursor-pointer",
            !hasStep && "opacity-60 cursor-not-allowed",
            isSelected && "ring-4 ring-violet-500/30 shadow-lg",
            "shadow-sm"
          );

          return (
            <div key={stepName} className="flex items-center gap-3">
              {reducedMotion ? (
                <button
                  onClick={() => step && onSelectStep(step)}
                  disabled={!hasStep}
                  className={buttonClassName}
                >
                  {stepContent}
                </button>
              ) : (
                <motion.button
                  whileHover={hasStep ? { scale: 1.02 } : {}}
                  whileTap={hasStep ? { scale: 0.98 } : {}}
                  onClick={() => step && onSelectStep(step)}
                  disabled={!hasStep}
                  className={buttonClassName}
                >
                  {stepContent}
                  {/* Selected indicator with animation */}
                  {isSelected && (
                    <motion.div
                      layoutId="selectedStep"
                      className="absolute inset-0 rounded-2xl border-2 border-violet-500 pointer-events-none"
                    />
                  )}
                </motion.button>
              )}

              {/* Arrow connector */}
              {index < PIPELINE_STEPS.length - 1 && (
                <div className="flex items-center">
                  <ChevronRight className="size-5 text-slate-300" />
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
