"use client";

import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { TrendingUp } from "lucide-react";
import { cn } from "@/lib/utils";

interface ConfidenceIndicatorProps {
  confidence: number;
}

function getConfidenceLevel(confidence: number): {
  label: string;
  color: string;
  bgColor: string;
} {
  if (confidence > 0.9) {
    return {
      label: "High Confidence",
      color: "text-green-700 dark:text-green-300",
      bgColor: "bg-gradient-to-r from-green-500 to-green-600",
    };
  }
  if (confidence >= 0.7) {
    return {
      label: "Medium Confidence",
      color: "text-amber-700 dark:text-amber-300",
      bgColor: "bg-gradient-to-r from-amber-500 to-amber-600",
    };
  }
  return {
    label: "Low Confidence",
    color: "text-red-700 dark:text-red-300",
    bgColor: "bg-gradient-to-r from-red-500 to-red-600",
  };
}

export function ConfidenceIndicator({ confidence }: ConfidenceIndicatorProps) {
  const percentage = Math.round(confidence * 100);
  const { label, color, bgColor } = getConfidenceLevel(confidence);

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center gap-2">
          <TrendingUp className="size-5 text-muted-foreground" />
          <CardTitle className="text-lg">Confidence Score</CardTitle>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="flex items-center justify-between">
          <span className={cn("font-semibold text-sm", color)}>{label}</span>
          <span className="text-2xl font-bold">{percentage}%</span>
        </div>
        <div className="relative h-3 w-full overflow-hidden rounded-full bg-muted">
          <div
            className={cn(
              "h-full transition-all duration-500 ease-out rounded-full",
              bgColor
            )}
            style={{ width: `${percentage}%` }}
            role="progressbar"
            aria-valuenow={percentage}
            aria-valuemin={0}
            aria-valuemax={100}
            aria-label={`Confidence level: ${percentage}%`}
          />
        </div>
        <p className="text-xs text-muted-foreground">
          AI-generated confidence based on email analysis and context matching.
        </p>
      </CardContent>
    </Card>
  );
}
