"use client";

import { Badge } from "@/components/ui/badge";
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
}

export function ClassificationBadge({
  classification,
}: ClassificationBadgeProps) {
  if (!classification) {
    return (
      <Badge variant="outline" className="bg-gray-50 dark:bg-gray-800/30">
        Unclassified
      </Badge>
    );
  }

  const config = CLASSIFICATION_COLORS[classification];
  const IconComponent = ICON_MAP[config.icon as keyof typeof ICON_MAP];

  const label = classification
    .split("_")
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(" ");

  return (
    <Badge variant="outline" className={cn(config.bg, config.text)}>
      {IconComponent && <IconComponent className="size-3" />}
      {label}
    </Badge>
  );
}
