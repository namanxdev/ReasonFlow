"use client";

import { useState } from "react";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import type { AgentLog, ToolExecution } from "@/types";
import { ChevronDown, ChevronRight, Check, X, AlertTriangle } from "lucide-react";
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

function JsonViewer({ data }: { data: Record<string, unknown> | null }) {
  if (!data) {
    return (
      <div className="text-sm text-muted-foreground italic">No data</div>
    );
  }

  return (
    <pre className="text-xs font-mono bg-muted/50 p-4 rounded-md overflow-x-auto">
      {JSON.stringify(data, null, 2)}
    </pre>
  );
}

export function StepDetail({ step }: StepDetailProps) {
  const [inputOpen, setInputOpen] = useState(false);
  const [outputOpen, setOutputOpen] = useState(false);

  const hasToolExecutions = step.tool_executions && step.tool_executions.length > 0;

  return (
    <div className="space-y-6 border rounded-lg p-6 bg-card">
      <div className="flex items-start justify-between">
        <div className="space-y-1">
          <h2 className="text-2xl font-bold">
            {formatStepName(step.step_name)}
          </h2>
          <div className="flex items-center gap-3 text-sm text-muted-foreground">
            <span>Step {step.step_order}</span>
            <span>•</span>
            <Badge variant="outline" className="text-xs">
              {step.latency_ms}ms
            </Badge>
          </div>
        </div>
      </div>

      {step.error_message && (
        <div className="bg-red-50 dark:bg-red-950/30 border border-red-200 dark:border-red-900 rounded-md p-4">
          <div className="flex items-start gap-3">
            <AlertTriangle className="size-5 text-red-600 dark:text-red-400 flex-shrink-0 mt-0.5" />
            <div className="space-y-1">
              <h3 className="font-semibold text-red-900 dark:text-red-100">
                Error
              </h3>
              <p className="text-sm text-red-800 dark:text-red-200">
                {step.error_message}
              </p>
            </div>
          </div>
        </div>
      )}

      <div className="space-y-4">
        <Collapsible open={inputOpen} onOpenChange={setInputOpen}>
          <CollapsibleTrigger className="flex items-center gap-2 w-full group">
            <div className="flex items-center gap-2 flex-1">
              {inputOpen ? (
                <ChevronDown className="size-4 text-muted-foreground" />
              ) : (
                <ChevronRight className="size-4 text-muted-foreground" />
              )}
              <h3 className="font-semibold text-sm group-hover:text-foreground transition-colors">
                Input State
              </h3>
            </div>
          </CollapsibleTrigger>
          <CollapsibleContent className="mt-3">
            <JsonViewer data={step.input_state} />
          </CollapsibleContent>
        </Collapsible>

        <Collapsible open={outputOpen} onOpenChange={setOutputOpen}>
          <CollapsibleTrigger className="flex items-center gap-2 w-full group">
            <div className="flex items-center gap-2 flex-1">
              {outputOpen ? (
                <ChevronDown className="size-4 text-muted-foreground" />
              ) : (
                <ChevronRight className="size-4 text-muted-foreground" />
              )}
              <h3 className="font-semibold text-sm group-hover:text-foreground transition-colors">
                Output State
              </h3>
            </div>
          </CollapsibleTrigger>
          <CollapsibleContent className="mt-3">
            <JsonViewer data={step.output_state} />
          </CollapsibleContent>
        </Collapsible>
      </div>

      {hasToolExecutions && (
        <div className="space-y-3">
          <h3 className="font-semibold text-sm">Tool Executions</h3>
          <div className="border rounded-md">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Tool Name</TableHead>
                  <TableHead>Parameters</TableHead>
                  <TableHead>Result</TableHead>
                  <TableHead>Success</TableHead>
                  <TableHead>Latency</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {step.tool_executions.map((tool) => (
                  <TableRow key={tool.id}>
                    <TableCell>
                      <span className="font-mono text-xs">{tool.tool_name}</span>
                    </TableCell>
                    <TableCell>
                      <details className="cursor-pointer">
                        <summary className="text-xs text-muted-foreground hover:text-foreground">
                          View params
                        </summary>
                        <div className="mt-2">
                          <JsonViewer data={tool.params} />
                        </div>
                      </details>
                    </TableCell>
                    <TableCell>
                      <details className="cursor-pointer">
                        <summary className="text-xs text-muted-foreground hover:text-foreground">
                          View result
                        </summary>
                        <div className="mt-2">
                          {tool.error_message ? (
                            <div className="text-xs text-red-600 dark:text-red-400">
                              {tool.error_message}
                            </div>
                          ) : (
                            <JsonViewer data={tool.result} />
                          )}
                        </div>
                      </details>
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center">
                        {tool.success ? (
                          <Check className="size-4 text-green-600 dark:text-green-400" />
                        ) : (
                          <X className="size-4 text-red-600 dark:text-red-400" />
                        )}
                      </div>
                    </TableCell>
                    <TableCell>
                      <span className="text-xs text-muted-foreground">
                        {tool.latency_ms}ms
                      </span>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        </div>
      )}
    </div>
  );
}
