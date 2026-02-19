"use client";

import { cn } from "@/lib/utils";
import { CLASSIFICATION_COLORS } from "@/lib/constants";
import type { EmailClassification } from "@/types";
import {
  Calendar,
  HelpCircle,
  AlertTriangle,
  RefreshCw,
  Ban,
  Pin,
} from "lucide-react";

const ICON_MAP = {
  Calendar,
  HelpCircle,
  AlertTriangle,
  RefreshCw,
  Ban,
  Pin,
} as const;

interface ClassificationBadgeProps {
  classification: EmailClassification | null;
  size?: "sm" | "md" | "lg";
}

export function ClassificationBadge({
  classification,
  size = "md",
}: ClassificationBadgeProps) {
  if (!classification) {
    return (
      <div 
        className={cn(
          "inline-flex items-center rounded-lg bg-muted text-muted-foreground",
          size === "sm" && "px-2 py-0.5 text-xs gap-1",
          size === "md" && "px-2.5 py-1 text-xs gap-1.5",
          size === "lg" && "px-3 py-1.5 text-sm gap-2",
        )}
      >
        <span className="w-1.5 h-1.5 rounded-full bg-muted-foreground/50" />
        Unclassified
      </div>
    );
  }

  const config = CLASSIFICATION_COLORS[classification];
  const IconComponent = ICON_MAP[config.icon as keyof typeof ICON_MAP];

  const label = classification
    .split("_")
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(" ");

  const sizeClasses = {
    sm: "px-2 py-0.5 text-xs gap-1",
    md: "px-2.5 py-1 text-xs gap-1.5",
    lg: "px-3 py-1.5 text-sm gap-2",
  };

  const iconSizes = {
    sm: "w-3 h-3",
    md: "w-3.5 h-3.5",
    lg: "w-4 h-4",
  };

  // Extract color without dark mode classes for cleaner styling
  const bgColor = config.bg.split(" ")[0]; // Get only the bg class
  const textColor = config.text.split(" ")[0]; // Get only the text class

  return (
    <div 
      className={cn(
        "inline-flex items-center rounded-lg font-medium",
        bgColor.replace("bg-", "bg-").replace("/30", "/15").replace("/50", "/15"),
        textColor,
        sizeClasses[size]
      )}
    >
      <span className={cn(
        "w-1.5 h-1.5 rounded-full",
        textColor.replace("text-", "bg-").replace("/30", "").replace("/50", "")
      )} />
      {IconComponent && <IconComponent className={iconSizes[size]} />}
      {label}
    </div>
  );
}
