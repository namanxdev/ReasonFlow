"use client";

import { TableRow, TableCell } from "@/components/ui/table";
import { ClassificationBadge } from "./classification-badge";
import { STATUS_STYLES } from "@/lib/constants";
import type { Email } from "@/types";
import {
  Circle,
  Loader2,
  AlertCircle,
  CheckCircle,
  CheckCheck,
  XCircle,
} from "lucide-react";
import { cn } from "@/lib/utils";

const STATUS_ICON_MAP = {
  Circle,
  Loader2,
  AlertCircle,
  CheckCircle,
  CheckCheck,
  XCircle,
} as const;

interface EmailCardProps {
  email: Email;
  isSelected: boolean;
  onClick: () => void;
}

function getRelativeTime(dateString: string): string {
  const now = new Date();
  const date = new Date(dateString);
  const diffInMs = now.getTime() - date.getTime();
  const diffInMinutes = Math.floor(diffInMs / 60000);
  const diffInHours = Math.floor(diffInMinutes / 60);
  const diffInDays = Math.floor(diffInHours / 24);

  if (diffInMinutes < 1) return "Just now";
  if (diffInMinutes < 60) return `${diffInMinutes}m ago`;
  if (diffInHours < 24) return `${diffInHours}h ago`;
  if (diffInDays < 7) return `${diffInDays}d ago`;
  if (diffInDays < 30) return `${Math.floor(diffInDays / 7)}w ago`;
  return `${Math.floor(diffInDays / 30)}mo ago`;
}

export function EmailCard({ email, isSelected, onClick }: EmailCardProps) {
  const statusConfig = STATUS_STYLES[email.status];
  const StatusIcon =
    STATUS_ICON_MAP[statusConfig.icon as keyof typeof STATUS_ICON_MAP];

  const truncatedSubject =
    email.subject.length > 60
      ? email.subject.substring(0, 60) + "..."
      : email.subject;

  const truncatedSender =
    email.sender.length > 30
      ? email.sender.substring(0, 30) + "..."
      : email.sender;

  return (
    <TableRow
      data-state={isSelected ? "selected" : undefined}
      onClick={onClick}
      className={cn(
        "cursor-pointer transition-colors",
        isSelected && "bg-accent"
      )}
    >
      <TableCell className="font-medium">{truncatedSender}</TableCell>
      <TableCell className="max-w-md">{truncatedSubject}</TableCell>
      <TableCell>
        <ClassificationBadge classification={email.classification} />
      </TableCell>
      <TableCell>
        <div className="flex items-center gap-2">
          <StatusIcon
            className={cn(
              "size-4",
              statusConfig.color,
              email.status === "processing" && "animate-spin"
            )}
          />
          <span className="text-sm">{statusConfig.label}</span>
        </div>
      </TableCell>
      <TableCell className="text-muted-foreground text-sm">
        {getRelativeTime(email.received_at)}
      </TableCell>
    </TableRow>
  );
}
