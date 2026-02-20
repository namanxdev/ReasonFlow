"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible";
import { Badge } from "@/components/ui/badge";
import type { AgentLog, ToolExecution } from "@/types";
import { ChevronDown, ChevronRight, Check, X, AlertTriangle, Clock, Database, ArrowRight } from "lucide-react";
import { cn } from "@/lib/utils";

interface StepDetailProps {
  step: AgentLog;
}

function formatStepName(stepName: string): string {
  return stepName
    .split("_")
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(" ");
}

function JsonViewer({ data, label }: { data: Record<string, unknown> | null; label?: string }) {
  if (!data) {
    return (
      <div className="text-sm text-slate-400 italic bg-slate-50 rounded-lg p-4">
        No data available
      </div>
    );
  }

  return (
    <div className="bg-slate-900 rounded-lg p-4 overflow-x-auto">
      {label && <div className="text-xs text-slate-400 mb-2 font-mono">{label}</div>}
      <pre className="text-xs font-mono text-green-400">
        {JSON.stringify(data, null, 2)}
      </pre>
    </div>
  );
}

function ToolExecutionRow({ tool, index }: { tool: ToolExecution; index: number }) {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <div className="border border-slate-100 rounded-xl overflow-hidden mb-2">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="w-full flex items-center justify-between p-3 bg-slate-50/50 hover:bg-slate-100/50 transition-colors"
      >
        <div className="flex items-center gap-3">
          <div className={cn(
            "w-8 h-8 rounded-lg flex items-center justify-center",
            tool.success ? "bg-green-100 text-green-600" : "bg-red-100 text-red-600"
          )}>
            {tool.success ? <Check className="size-4" /> : <X className="size-4" />}
          </div>
          <div className="text-left">
            <p className="font-medium text-sm">{tool.tool_name}</p>
            <p className="text-xs text-slate-400">{tool.latency_ms}ms</p>
          </div>
        </div>
        {isOpen ? <ChevronDown className="size-4 text-slate-400" /> : <ChevronRight className="size-4 text-slate-400" />}
      </button>

      {isOpen && (
        <motion.div
          initial={{ height: 0, opacity: 0 }}
          animate={{ height: "auto", opacity: 1 }}
          className="p-3 space-y-3"
        >
          <div>
            <p className="text-xs font-medium text-slate-500 mb-1">Parameters</p>
            <JsonViewer data={tool.params} />
          </div>
          <div>
            <p className="text-xs font-medium text-slate-500 mb-1">Result</p>
            {tool.error_message ? (
              <div className="bg-red-50 border border-red-100 rounded-lg p-3 text-sm text-red-600">
                {tool.error_message}
              </div>
            ) : (
              <JsonViewer data={tool.result} />
            )}
          </div>
        </motion.div>
      )}
    </div>
  );
}

export function StepDetail({ step }: StepDetailProps) {
  const [inputOpen, setInputOpen] = useState(true);
  const [outputOpen, setOutputOpen] = useState(true);

  const hasToolExecutions = step.tool_executions && step.tool_executions.length > 0;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div className="space-y-1">
          <h2 className="text-xl font-semibold text-slate-900">
            {formatStepName(step.step_name)}
          </h2>
          <div className="flex items-center gap-3 text-sm text-slate-500">
            <span className="flex items-center gap-1">
              <ArrowRight className="size-3.5" />
              Step {step.step_order}
            </span>
            <span>•</span>
            <span className="flex items-center gap-1">
              <Clock className="size-3.5" />
              {step.latency_ms}ms
            </span>
          </div>
        </div>
        <Badge 
          variant={step.error_message ? "destructive" : "default"}
          className={cn(
            step.error_message 
              ? "bg-red-100 text-red-700 hover:bg-red-100" 
              : "bg-green-100 text-green-700 hover:bg-green-100"
          )}
        >
          {step.error_message ? "Failed" : "Success"}
        </Badge>
      </div>

      {/* Error Message */}
      {step.error_message && (
        <motion.div 
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-red-50 border border-red-200 rounded-xl p-4"
        >
          <div className="flex items-start gap-3">
            <AlertTriangle className="size-5 text-red-500 flex-shrink-0 mt-0.5" />
            <div className="space-y-1">
              <h3 className="font-medium text-red-900">Error Occurred</h3>
              <p className="text-sm text-red-700">{step.error_message}</p>
            </div>
          </div>
        </motion.div>
      )}

      {/* Input/Output States */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Input State */}
        <Collapsible open={inputOpen} onOpenChange={setInputOpen}>
          <CollapsibleTrigger className="flex items-center gap-2 w-full group p-3 bg-slate-50 rounded-xl hover:bg-slate-100 transition-colors">
            <div className="w-8 h-8 rounded-lg bg-blue-100 flex items-center justify-center">
              <Database className="size-4 text-blue-600" />
            </div>
            <div className="flex-1 text-left">
              <h3 className="font-medium text-sm text-slate-900">Input State</h3>
              <p className="text-xs text-slate-500">Data before processing</p>
            </div>
            {inputOpen ? (
              <ChevronDown className="size-4 text-slate-400" />
            ) : (
              <ChevronRight className="size-4 text-slate-400" />
            )}
          </CollapsibleTrigger>
          <CollapsibleContent className="mt-2">
            <JsonViewer data={step.input_state} />
          </CollapsibleContent>
        </Collapsible>

        {/* Output State */}
        <Collapsible open={outputOpen} onOpenChange={setOutputOpen}>
          <CollapsibleTrigger className="flex items-center gap-2 w-full group p-3 bg-slate-50 rounded-xl hover:bg-slate-100 transition-colors">
            <div className="w-8 h-8 rounded-lg bg-violet-100 flex items-center justify-center">
              <ArrowRight className="size-4 text-violet-600" />
            </div>
            <div className="flex-1 text-left">
              <h3 className="font-medium text-sm text-slate-900">Output State</h3>
              <p className="text-xs text-slate-500">Data after processing</p>
            </div>
            {outputOpen ? (
              <ChevronDown className="size-4 text-slate-400" />
            ) : (
              <ChevronRight className="size-4 text-slate-400" />
            )}
          </CollapsibleTrigger>
          <CollapsibleContent className="mt-2">
            <JsonViewer data={step.output_state} />
          </CollapsibleContent>
        </Collapsible>
      </div>

      {/* Tool Executions */}
      {hasToolExecutions && (
        <div className="space-y-3">
          <h3 className="font-medium text-slate-900 flex items-center gap-2">
            <Database className="size-4 text-slate-400" />
            Tool Executions ({step.tool_executions.length})
          </h3>
          <div className="space-y-2">
            {step.tool_executions.map((tool, index) => (
              <ToolExecutionRow key={tool.id} tool={tool} index={index} />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
