"use client";

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
  Mail,
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

function getStatusColor(status: string) {
  switch (status) {
    case "pending":
      return { bg: "bg-slate-100", text: "text-slate-600", border: "border-slate-200" };
    case "processing":
      return { bg: "bg-blue-50", text: "text-blue-600", border: "border-blue-200" };
    case "drafted":
      return { bg: "bg-violet-50", text: "text-violet-600", border: "border-violet-200" };
    case "needs_review":
      return { bg: "bg-amber-50", text: "text-amber-600", border: "border-amber-200" };
    case "approved":
      return { bg: "bg-green-50", text: "text-green-600", border: "border-green-200" };
    case "sent":
      return { bg: "bg-emerald-50", text: "text-emerald-600", border: "border-emerald-200" };
    case "rejected":
      return { bg: "bg-red-50", text: "text-red-600", border: "border-red-200" };
    default:
      return { bg: "bg-slate-100", text: "text-slate-600", border: "border-slate-200" };
  }
}

export function EmailCard({ email, isSelected, onClick }: EmailCardProps) {
  const statusColors = getStatusColor(email.status);
  const statusConfig = STATUS_STYLES[email.status];
  const StatusIcon = STATUS_ICON_MAP[statusConfig.icon as keyof typeof STATUS_ICON_MAP];

  const truncatedSubject =
    email.subject.length > 80
      ? email.subject.substring(0, 80) + "..."
      : email.subject;

  const truncatedSender =
    email.sender.length > 35
      ? email.sender.substring(0, 35) + "..."
      : email.sender;

  return (
    <div
      onClick={onClick}
      className={cn(
        "flex items-center gap-4 px-4 py-3 cursor-pointer transition-all duration-200 group",
        isSelected 
          ? "bg-blue-50/80 border-l-4 border-l-blue-500" 
          : "hover:bg-slate-50 border-l-4 border-l-transparent"
      )}
    >
      {/* Avatar */}
      <div className={cn(
        "w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0 transition-colors",
        isSelected ? "bg-blue-500 text-white" : "bg-slate-100 text-slate-500 group-hover:bg-white group-hover:shadow-sm"
      )}>
        <Mail className="size-4" />
      </div>

      {/* Sender */}
      <div className="w-48 min-w-0">
        <p className={cn(
          "font-medium text-sm truncate",
          isSelected ? "text-blue-900" : "text-slate-900"
        )}>
          {truncatedSender}
        </p>
        <p className="text-xs text-slate-400 truncate">
          {email.gmail_id ? "Gmail" : "Email"}
        </p>
      </div>

      {/* Subject */}
      <div className="flex-1 min-w-0 pr-4">
        <p className={cn(
          "text-sm truncate",
          isSelected ? "text-blue-800" : "text-slate-700"
        )}>
          {truncatedSubject || "(No subject)"}
        </p>
      </div>

      {/* Classification */}
      <div className="w-28 flex-shrink-0">
        <ClassificationBadge classification={email.classification} />
      </div>

      {/* Status */}
      <div className="w-32 flex-shrink-0">
        <div className={cn(
          "flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-medium w-fit border",
          statusColors.bg,
          statusColors.text,
          statusColors.border
        )}>
          <StatusIcon
            className={cn(
              "size-3.5",
              email.status === "processing" && "animate-spin"
            )}
          />
          <span>{statusConfig.label}</span>
        </div>
      </div>

      {/* Date */}
      <div className="w-32 flex-shrink-0 text-right">
        <p className={cn(
          "text-xs",
          isSelected ? "text-blue-600" : "text-slate-500"
        )}>
          {getRelativeTime(email.received_at)}
        </p>
      </div>
    </div>
  );
}
