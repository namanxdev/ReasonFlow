import type { EmailClassification, EmailStatus } from "@/types";

export const CLASSIFICATION_COLORS: Record<
  EmailClassification,
  { bg: string; text: string; icon: string }
> = {
  meeting_request: {
    bg: "bg-blue-100 dark:bg-blue-900/30",
    text: "text-blue-700 dark:text-blue-300",
    icon: "Calendar",
  },
  inquiry: {
    bg: "bg-green-100 dark:bg-green-900/30",
    text: "text-green-700 dark:text-green-300",
    icon: "HelpCircle",
  },
  complaint: {
    bg: "bg-red-100 dark:bg-red-900/30",
    text: "text-red-700 dark:text-red-300",
    icon: "AlertTriangle",
  },
  follow_up: {
    bg: "bg-yellow-100 dark:bg-yellow-900/30",
    text: "text-yellow-700 dark:text-yellow-300",
    icon: "RefreshCw",
  },
  spam: {
    bg: "bg-gray-100 dark:bg-gray-800/50",
    text: "text-gray-500 dark:text-gray-400",
    icon: "Ban",
  },
  other: {
    bg: "bg-purple-100 dark:bg-purple-900/30",
    text: "text-purple-700 dark:text-purple-300",
    icon: "Pin",
  },
};

export const STATUS_STYLES: Record<
  EmailStatus,
  { color: string; bg: string; label: string; icon: string }
> = {
  pending: { color: "text-gray-500", bg: "bg-gray-100 dark:bg-gray-800/30", label: "Pending", icon: "Circle" },
  processing: {
    color: "text-blue-500",
    bg: "bg-blue-100 dark:bg-blue-900/30",
    label: "Processing",
    icon: "Loader2",
  },
  drafted: { color: "text-orange-500", bg: "bg-orange-100 dark:bg-orange-900/30", label: "Drafted", icon: "Circle" },
  needs_review: {
    color: "text-yellow-600",
    bg: "bg-yellow-100 dark:bg-yellow-900/30",
    label: "Needs Review",
    icon: "AlertCircle",
  },
  approved: {
    color: "text-green-500",
    bg: "bg-green-100 dark:bg-green-900/30",
    label: "Approved",
    icon: "CheckCircle",
  },
  sent: { color: "text-blue-600", bg: "bg-blue-100 dark:bg-blue-900/30", label: "Sent", icon: "CheckCheck" },
  rejected: { color: "text-red-500", bg: "bg-red-100 dark:bg-red-900/30", label: "Rejected", icon: "XCircle" },
};

export const TRACE_NODE_COLORS = {
  success: "#22c55e",
  failed: "#ef4444",
  skipped: "#eab308",
  human_queue: "#3b82f6",
} as const;

export const PIPELINE_STEPS = [
  "classify",
  "retrieve",
  "decide",
  "execute",
  "generate",
  "review",
  "dispatch",
] as const;

export const CONFIDENCE = {
  HIGH: 0.9,
  MEDIUM: 0.7,
  AUTO_APPROVE: 0.8,
} as const;

export const CHART_COLORS = [
  "#3b82f6",
  "#22c55e",
  "#ef4444",
  "#eab308",
  "#6b7280",
  "#a855f7",
] as const;
