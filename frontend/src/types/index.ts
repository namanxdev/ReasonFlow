// ── Enums ──

export type EmailClassification =
  | "inquiry"
  | "meeting_request"
  | "complaint"
  | "follow_up"
  | "spam"
  | "other";

export type EmailStatus =
  | "pending"
  | "processing"
  | "drafted"
  | "needs_review"
  | "approved"
  | "sent"
  | "rejected";

// ── Models ──

export interface User {
  id: string;
  email: string;
  created_at: string;
  updated_at: string;
}

export interface Email {
  id: string;
  user_id: string;
  gmail_id: string;
  thread_id: string | null;
  subject: string;
  body: string;
  sender: string;
  recipient: string | null;
  received_at: string;
  classification: EmailClassification | null;
  confidence: number | null;
  status: EmailStatus;
  draft_response: string | null;
  created_at: string;
  updated_at: string;
}

export interface AgentLog {
  id: string;
  email_id: string;
  trace_id: string;
  step_name: string;
  step_order: number;
  input_state: Record<string, unknown> | null;
  output_state: Record<string, unknown> | null;
  error_message: string | null;
  latency_ms: number;
  tool_executions: ToolExecution[];
  created_at: string;
}

export interface ToolExecution {
  id: string;
  agent_log_id: string;
  tool_name: string;
  params: Record<string, unknown> | null;
  result: Record<string, unknown> | null;
  success: boolean;
  error_message: string | null;
  latency_ms: number;
  created_at: string;
}

export interface Contact {
  email: string;
  name: string;
  company: string;
  title: string;
  phone: string | null;
  last_interaction: string;
  notes: string;
  tags: string[];
}

// ── Trace Aggregations ──

export interface TraceRun {
  trace_id: string;
  email_subject: string;
  classification: EmailClassification;
  total_latency_ms: number;
  step_count: number;
  status: "completed" | "failed" | "in_progress";
  created_at: string;
}

export interface TraceDetail {
  trace_id: string;
  email: Email;
  steps: AgentLog[];
}

// ── Metrics ──

export interface IntentDistribution {
  classification: EmailClassification;
  count: number;
  percentage: number;
}

export interface LatencyPercentiles {
  p50: number;
  p90: number;
  p99: number;
  mean: number;
  min: number;
  max: number;
}

export interface LatencyMetrics {
  overall: LatencyPercentiles;
  by_step: Record<string, LatencyPercentiles>;
  sample_count: number;
  start: string | null;
  end: string | null;
}

export interface ToolAccuracy {
  tool_name: string;
  total_calls: number;
  successful_calls: number;
  failed_calls: number;
  success_rate: number;
}

export interface SummaryStats {
  total_emails_processed: number;
  average_response_time_ms: number;
  approval_rate: number;
  human_review_rate: number;
}

// ── API Responses ──

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  per_page: number;
}

export interface EmailFilters {
  classification?: EmailClassification;
  status?: EmailStatus;
  search?: string;
  date_from?: string;
  date_to?: string;
  page?: number;
  page_size?: number;
  sort_by?: string;
  sort_order?: "asc" | "desc";
}
