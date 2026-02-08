# ReasonFlow Frontend — AI Agent Build Guide

> This document is the single source of truth for building the ReasonFlow frontend. Follow it section by section, in order. Every component, route, data shape, API endpoint, and design decision is specified below.

---

## 1. Project Overview

ReasonFlow is an AI-powered email agent that connects to Gmail, classifies incoming emails using Google Gemini (via LangGraph), generates draft responses, and lets users review/approve/reject them. The frontend is a dashboard for managing this workflow.

---

## 2. Tech Stack (Already Installed)

| Layer | Package | Version | Notes |
|-------|---------|---------|-------|
| Framework | `next` | 16.1.6 | App Router (`src/app/`) |
| Language | `typescript` | ^5 | Strict mode enabled |
| Styling | `tailwindcss` | ^4 | PostCSS plugin via `@tailwindcss/postcss` |
| Data Fetching | `@tanstack/react-query` | ^5.90 | Server state management |
| HTTP Client | `axios` | ^1.13 | Pre-configured in `src/lib/api.ts` |
| Charts | `recharts` | ^3.7 | For metrics dashboards |
| Animations | `framer-motion` | ^12.33 | Page transitions, micro-interactions |
| Icons | `lucide-react` | ^0.563 | Icon library |
| State | `zustand` | ^5.0 | Client-side state (filters, UI state) |
| Utility | `clsx` + `tailwind-merge` | — | `cn()` helper in `src/lib/utils.ts` |
| Base UI | `@radix-ui/*` | — | Primitives: dialog, dropdown, tabs, toast, select, collapsible, label, separator, slot |
| Class Variants | `class-variance-authority` | ^0.7 | Component variant styling |

### UI Component Libraries to Use

| Library | Use For | Install Reference |
|---------|---------|-------------------|
| **shadcn/ui** | Buttons, badges, cards, sheets, dialogs, tables, inputs, toasts, date pickers | Already partially set up via Radix primitives. Add components via `npx shadcn@latest add <component>` |
| **HeroUI** | Inbox email table, productivity dashboard components | Refer to HeroUI docs for table/list components |
| **Magic UI** | Split view panels, confidence meter widgets | Refer to Magic UI docs for animated widgets |
| **Aceternity UI** | Trace viewer flowchart, interactive graph layouts | Refer to Aceternity UI docs for flowchart/timeline components |
| **Fancy Components** | Data visualization overlays, animated stat counters | Refer to Fancy Components docs for animated numbers |

---

## 3. Project Structure

```
frontend/
├── src/
│   ├── app/                          # Next.js App Router pages
│   │   ├── layout.tsx                # Root layout (exists)
│   │   ├── globals.css               # Global styles + theme tokens (exists)
│   │   ├── page.tsx                  # Landing/redirect → /inbox
│   │   ├── login/
│   │   │   └── page.tsx              # Login page
│   │   ├── inbox/
│   │   │   └── page.tsx              # Inbox dashboard
│   │   ├── drafts/
│   │   │   └── page.tsx              # Draft review page
│   │   ├── metrics/
│   │   │   └── page.tsx              # Metrics dashboard
│   │   └── traces/
│   │       ├── page.tsx              # Trace list
│   │       └── [traceId]/
│   │           └── page.tsx          # Trace detail view
│   ├── components/
│   │   ├── ui/                       # shadcn/ui base components
│   │   │   ├── button.tsx
│   │   │   ├── badge.tsx
│   │   │   ├── card.tsx
│   │   │   ├── sheet.tsx
│   │   │   ├── table.tsx
│   │   │   ├── dialog.tsx
│   │   │   ├── input.tsx
│   │   │   ├── select.tsx
│   │   │   ├── tabs.tsx
│   │   │   ├── toast.tsx
│   │   │   ├── toaster.tsx
│   │   │   ├── separator.tsx
│   │   │   ├── collapsible.tsx
│   │   │   ├── label.tsx
│   │   │   ├── textarea.tsx
│   │   │   └── dropdown-menu.tsx
│   │   ├── layout/                   # App shell components
│   │   │   ├── sidebar.tsx           # Navigation sidebar
│   │   │   ├── header.tsx            # Top bar with user info
│   │   │   └── app-shell.tsx         # Sidebar + header + content wrapper
│   │   ├── inbox/                    # Inbox feature components
│   │   │   ├── email-list.tsx
│   │   │   ├── email-card.tsx
│   │   │   ├── email-detail-panel.tsx
│   │   │   └── classification-badge.tsx
│   │   ├── draft-review/             # Draft review feature components
│   │   │   ├── draft-editor.tsx
│   │   │   ├── original-email.tsx
│   │   │   ├── approval-buttons.tsx
│   │   │   └── confidence-indicator.tsx
│   │   ├── metrics/                  # Metrics feature components
│   │   │   ├── intent-chart.tsx
│   │   │   ├── latency-chart.tsx
│   │   │   ├── accuracy-chart.tsx
│   │   │   └── stats-cards.tsx
│   │   └── trace-viewer/             # Trace viewer feature components
│   │       ├── trace-list.tsx
│   │       ├── trace-graph.tsx
│   │       └── step-detail.tsx
│   ├── hooks/                        # Custom React hooks
│   │   ├── use-emails.ts
│   │   ├── use-drafts.ts
│   │   ├── use-metrics.ts
│   │   └── use-traces.ts
│   ├── lib/                          # Utilities
│   │   ├── api.ts                    # Axios instance (exists)
│   │   ├── utils.ts                  # cn() helper (exists)
│   │   └── constants.ts              # Enums, color maps, config values
│   ├── types/                        # TypeScript type definitions
│   │   └── index.ts                  # All shared types
│   └── providers/                    # React context providers
│       └── query-provider.tsx        # TanStack Query provider
├── package.json                      # (exists)
├── tsconfig.json                     # (exists — NOTE: fix paths alias to @/* → ./src/*)
├── next.config.ts                    # (exists — has API proxy rewrites)
├── postcss.config.mjs                # (exists)
└── eslint.config.mjs                 # (exists)
```

---

## 4. Configuration Notes

### tsconfig.json Path Alias Fix

The current `tsconfig.json` has an incorrect path alias pointing to `../frontend2/src/*`. Fix it:

```json
"paths": {
  "@/*": ["./src/*"]
}
```

### API Proxy

`next.config.ts` already proxies `/api/v1/*` to the backend at `NEXT_PUBLIC_API_URL` (default `http://localhost:8000`). All API calls go through the Axios instance in `src/lib/api.ts` which:
- Prefixes all requests with `/api/v1`
- Attaches JWT from `localStorage` key `rf_access_token`
- Redirects to `/login` on 401 responses

### Theme System

`globals.css` defines CSS custom properties for light/dark mode using HSL values. The theme follows shadcn/ui conventions with these semantic tokens: `--background`, `--foreground`, `--primary`, `--secondary`, `--muted`, `--accent`, `--destructive`, `--card`, `--border`, `--input`, `--ring`, `--radius`.

---

## 5. TypeScript Types

Create `src/types/index.ts` with these types derived from the backend SQLAlchemy models:

```typescript
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
  received_at: string;           // ISO 8601
  classification: EmailClassification | null;
  confidence: number | null;     // 0.0 – 1.0
  status: EmailStatus;
  draft_response: string | null;
  created_at: string;
  updated_at: string;
}

export interface AgentLog {
  id: string;
  email_id: string;
  trace_id: string;
  step_name: string;             // "classify" | "retrieve" | "decide" | "execute_tools" | "generate" | "review" | "dispatch"
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
  tool_name: string;             // "send_email" | "create_draft" | "check_calendar" | "create_event" | "get_contact" | "update_contact"
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
  last_interaction: string;
  notes: string;
  tags: string[];
}

// ── Trace Aggregations ──

export interface TraceRun {
  trace_id: string;
  email_id: string;
  email_subject: string;
  classification: EmailClassification;
  total_time_ms: number;
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

export interface LatencyDataPoint {
  timestamp: string;
  total_cycle_ms: number;
  classification_ms: number;
  generation_ms: number;
}

export interface ToolAccuracy {
  tool_name: string;
  total_calls: number;
  success_count: number;
  failure_count: number;
  success_rate: number;
}

export interface SummaryStats {
  total_emails_processed: number;
  average_response_time_ms: number;
  approval_rate: number;          // 0.0 – 1.0
  human_review_rate: number;      // 0.0 – 1.0
}

// ── API Responses ──

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
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
```

---

## 6. Constants & Color Maps

Create `src/lib/constants.ts`:

```typescript
import type { EmailClassification, EmailStatus } from "@/types";

// Classification badge colors (Tailwind classes)
export const CLASSIFICATION_COLORS: Record<EmailClassification, { bg: string; text: string; icon: string }> = {
  meeting_request: { bg: "bg-blue-100 dark:bg-blue-900/30",    text: "text-blue-700 dark:text-blue-300",    icon: "Calendar" },
  inquiry:         { bg: "bg-green-100 dark:bg-green-900/30",   text: "text-green-700 dark:text-green-300",  icon: "HelpCircle" },
  complaint:       { bg: "bg-red-100 dark:bg-red-900/30",      text: "text-red-700 dark:text-red-300",      icon: "AlertTriangle" },
  follow_up:       { bg: "bg-yellow-100 dark:bg-yellow-900/30", text: "text-yellow-700 dark:text-yellow-300", icon: "RefreshCw" },
  spam:            { bg: "bg-gray-100 dark:bg-gray-800/50",     text: "text-gray-500 dark:text-gray-400",    icon: "Ban" },
  other:           { bg: "bg-purple-100 dark:bg-purple-900/30", text: "text-purple-700 dark:text-purple-300", icon: "Pin" },
};

// Status indicator styles
export const STATUS_STYLES: Record<EmailStatus, { color: string; label: string; icon: string }> = {
  pending:      { color: "text-gray-400",   label: "Pending",      icon: "Circle" },
  processing:   { color: "text-blue-500",   label: "Processing",   icon: "Loader2" },    // animate-spin
  drafted:      { color: "text-orange-500", label: "Drafted",      icon: "Circle" },
  needs_review: { color: "text-yellow-500", label: "Needs Review", icon: "AlertCircle" },
  approved:     { color: "text-green-500",  label: "Approved",     icon: "CheckCircle" },
  sent:         { color: "text-blue-600",   label: "Sent",         icon: "CheckCheck" },
  rejected:     { color: "text-red-500",    label: "Rejected",     icon: "XCircle" },
};

// Trace graph node colors
export const TRACE_NODE_COLORS = {
  success: "#22c55e",   // green-500
  failed:  "#ef4444",   // red-500
  skipped: "#eab308",   // yellow-500
  human_queue: "#3b82f6", // blue-500
} as const;

// Agent pipeline steps in order
export const PIPELINE_STEPS = [
  "classify",
  "retrieve",
  "decide",
  "execute_tools",
  "generate",
  "review",
  "dispatch",
] as const;

// Confidence thresholds
export const CONFIDENCE = {
  HIGH: 0.9,
  MEDIUM: 0.7,
  AUTO_APPROVE: 0.8,
} as const;

// Recharts color palette
export const CHART_COLORS = [
  "#3b82f6", // blue
  "#22c55e", // green
  "#ef4444", // red
  "#eab308", // yellow
  "#6b7280", // gray
  "#a855f7", // purple
] as const;
```

---

## 7. API Endpoints & Data Fetching Hooks

### 7.1 Backend API Endpoints

All endpoints are prefixed with `/api/v1`. The Axios instance already handles this.

| Method | Path | Description | Request | Response |
|--------|------|-------------|---------|----------|
| **Auth** | | | | |
| POST | `/auth/register` | Register user | `{ email, password }` | `{ user, access_token }` |
| POST | `/auth/login` | Login | `{ email, password }` | `{ access_token }` |
| GET | `/auth/gmail/url` | Get Gmail OAuth URL | — | `{ url }` |
| GET | `/auth/gmail/callback` | Gmail OAuth callback | `?code=...` | redirect |
| **Emails** | | | | |
| GET | `/emails` | List emails (paginated) | query: `EmailFilters` | `PaginatedResponse<Email>` |
| GET | `/emails/{id}` | Get single email | — | `Email` |
| POST | `/emails/sync` | Sync from Gmail | — | `{ new_count }` |
| POST | `/emails/{id}/process` | Trigger agent processing | — | `Email` |
| **Drafts** | | | | |
| GET | `/drafts` | List drafts awaiting review | — | `Email[]` (status = needs_review) |
| POST | `/drafts/{id}/approve` | Approve draft | — | `Email` |
| POST | `/drafts/{id}/reject` | Reject draft | — | `Email` |
| PUT | `/drafts/{id}` | Update draft content | `{ draft_response }` | `Email` |
| **Traces** | | | | |
| GET | `/traces` | List trace runs (paginated) | query: `page, page_size` | `PaginatedResponse<TraceRun>` |
| GET | `/traces/{traceId}` | Get trace detail with steps | — | `TraceDetail` |
| **Metrics** | | | | |
| GET | `/metrics/intents` | Intent distribution | query: `date_from, date_to` | `IntentDistribution[]` |
| GET | `/metrics/latency` | Latency over time | query: `date_from, date_to` | `LatencyDataPoint[]` |
| GET | `/metrics/tools` | Tool accuracy stats | — | `ToolAccuracy[]` |
| GET | `/metrics/summary` | Summary statistics | — | `SummaryStats` |
| **Calendar** | | | | |
| GET | `/calendar/availability` | Get free time slots | query: `start, end` | `TimeSlot[]` |
| POST | `/calendar/events` | Create calendar event | `{ title, start, end, attendees }` | `{ event_id }` |
| **CRM** | | | | |
| GET | `/crm/contacts/{email}` | Get contact by email | — | `Contact` |
| PUT | `/crm/contacts/{email}` | Update contact | `{ data }` | `Contact` |

### 7.2 TanStack Query Hooks

Create these in `src/hooks/`. Each hook wraps an API call with TanStack Query.

**`src/hooks/use-emails.ts`**
```typescript
// useEmails(filters: EmailFilters)       → useQuery  → GET /emails
// useEmail(id: string)                   → useQuery  → GET /emails/{id}
// useSyncEmails()                        → useMutation → POST /emails/sync
// useProcessEmail()                      → useMutation → POST /emails/{id}/process
```

**`src/hooks/use-drafts.ts`**
```typescript
// useDrafts()                            → useQuery  → GET /drafts
// useApproveDraft()                      → useMutation → POST /drafts/{id}/approve
// useRejectDraft()                       → useMutation → POST /drafts/{id}/reject
// useEditDraft()                         → useMutation → PUT /drafts/{id}
```

**`src/hooks/use-traces.ts`**
```typescript
// useTraces(page, pageSize)              → useQuery  → GET /traces
// useTraceDetail(traceId: string)        → useQuery  → GET /traces/{traceId}
```

**`src/hooks/use-metrics.ts`**
```typescript
// useIntentDistribution(dateFrom, dateTo) → useQuery → GET /metrics/intents
// useLatencyStats(dateFrom, dateTo)       → useQuery → GET /metrics/latency
// useToolAccuracy()                       → useQuery → GET /metrics/tools
// useSummaryStats()                       → useQuery → GET /metrics/summary
```

All mutations should invalidate relevant query keys on success. For example, `useApproveDraft` should invalidate both `["drafts"]` and `["emails"]`.

---

## 8. Providers Setup

### `src/providers/query-provider.tsx`

Wrap the app with `QueryClientProvider` from `@tanstack/react-query`. Configure with:
- `staleTime: 30_000` (30 seconds)
- `retry: 1`

### Root Layout Update (`src/app/layout.tsx`)

Wrap `{children}` with:
1. `QueryProvider`
2. `Toaster` (shadcn/ui toast)
3. `AppShell` (sidebar + header layout, only on authenticated routes)

---

## 9. App Shell & Navigation

### Sidebar (`src/components/layout/sidebar.tsx`)

Fixed left sidebar with navigation links:

| Icon | Label | Route | Description |
|------|-------|-------|-------------|
| `Inbox` | Inbox | `/inbox` | Email dashboard |
| `FileEdit` | Drafts | `/drafts` | Draft review |
| `BarChart3` | Metrics | `/metrics` | Analytics |
| `GitBranch` | Traces | `/traces` | Agent trace viewer |

Bottom section:
- Gmail connection status indicator (green dot if connected, red if not)
- "Sync Emails" button triggering `useSyncEmails()` mutation
- User email display + logout button

### Header (`src/components/layout/header.tsx`)

Top bar showing:
- Page title (dynamic based on current route)
- Breadcrumbs for nested routes (e.g., Traces > Trace Detail)

---

## 10. Page Specifications

---

### 10.1 Login Page — `/login`

Simple centered card with email + password form. On success, store JWT in `localStorage` as `rf_access_token` and redirect to `/inbox`. Include a "Connect Gmail" button that calls `GET /auth/gmail/url` and redirects to the returned OAuth URL.

---

### 10.2 Inbox Dashboard — `/inbox`

**Purpose**: Primary interface for viewing and managing AI-processed emails.

**Layout**: Full-width page with filter bar on top, email table below, and a slide-out detail panel.

#### Filter Bar
- Classification dropdown (all 6 values + "All")
- Status dropdown (all 7 values + "All")
- Date range picker (from/to)
- Search input (searches subject + sender)
- "Sync Emails" button

#### Email List Table (`src/components/inbox/email-list.tsx`)
- Columns: Sender, Subject, Classification Badge, Status Indicator, Received Date
- Sortable by clicking column headers (sender, subject, received_at)
- Paginated (page size selector: 10, 25, 50)
- Click a row to open the detail panel
- Uses HeroUI table components for the productivity dashboard feel

#### Email Card / Row (`src/components/inbox/email-card.tsx`)
Each row displays:
- Sender name/email
- Subject (truncated to 60 chars)
- `ClassificationBadge` component
- Status icon + label
- Relative time ("2 hours ago")

#### Classification Badge (`src/components/inbox/classification-badge.tsx`)
```
Props: { classification: EmailClassification }
```
Renders a colored badge using the `CLASSIFICATION_COLORS` map. Shows icon + label text. Uses shadcn/ui `Badge` as the base.

#### Email Detail Panel (`src/components/inbox/email-detail-panel.tsx`)
Slide-out sheet (shadcn/ui `Sheet`, opens from right side) showing:
- **Header**: Subject line, sender, date
- **Body**: Full email body (rendered as plain text or basic HTML)
- **Classification**: Badge + confidence percentage (e.g., "Meeting Request — 94% confidence")
- **Status**: Current status with icon
- **Actions section**:
  - If `status === "needs_review"`: Show "View Draft" link → `/drafts?emailId={id}`
  - If `status === "pending"`: Show "Process with Agent" button → `useProcessEmail()` mutation
  - Link: "View Trace" → `/traces?emailId={id}` (if trace exists)
- **Quick actions**: Approve / Reject buttons (only if draft exists)

**Data**: `useEmails(filters)` for the list, `useEmail(id)` for the detail panel.

---

### 10.3 Draft Review — `/drafts`

**Purpose**: Inspect, edit, approve, or reject AI-generated email drafts before sending.

**Layout**: Split-view — original email on the left, editable draft on the right.

#### Draft List
If no specific email is selected (no `?emailId=` query param), show a list of all drafts awaiting review using `useDrafts()`. Each item shows subject, sender, classification badge, confidence indicator. Click to select.

#### Split View (when a draft is selected)

**Left Panel — Original Email (`src/components/draft-review/original-email.tsx`)**
- Read-only display of the original email
- Shows: sender, date, subject, full body
- Styled as a "received email" card with muted background

**Right Panel — Draft Editor (`src/components/draft-review/draft-editor.tsx`)**
- Displays the AI-generated `draft_response`
- Two modes:
  - **Review mode** (default): Read-only display of the draft
  - **Edit mode**: Textarea with the draft text, user can modify freely
- Toggle between modes with an "Edit" button

#### Confidence Indicator (`src/components/draft-review/confidence-indicator.tsx`)
```
Props: { confidence: number }
```
Visual meter/bar:
- `> 0.9` → Green background, "High Confidence" label
- `0.7 – 0.9` → Yellow/amber background, "Medium Confidence" label
- `< 0.7` → Red background, "Low Confidence" label

Display as a horizontal gradient bar with the confidence percentage.

#### Approval Buttons (`src/components/draft-review/approval-buttons.tsx`)
```
Props: { emailId: string; onAction: () => void }
```
Three buttons:
| Button | Style | Action | Effect |
|--------|-------|--------|--------|
| Approve | Green / primary | `useApproveDraft()` | Sends email immediately via Gmail |
| Edit | Outline / secondary | Enters edit mode | Shows textarea for modifications |
| Reject | Red / destructive | `useRejectDraft()` | Marks for manual handling |

When in edit mode, buttons change to:
- "Send Edited" (green) — calls `useEditDraft()` then `useApproveDraft()`
- "Cancel" (ghost) — returns to review mode

All destructive actions (Approve, Reject) should show a confirmation dialog (shadcn/ui `Dialog`).

**Data**: `useDrafts()`, `useApproveDraft()`, `useRejectDraft()`, `useEditDraft()`.

---

### 10.4 Metrics Dashboard — `/metrics`

**Purpose**: Analytics dashboard for agent performance, classification distribution, and tool accuracy.

**Layout**: Grid of cards — 4 stat cards on top, then 3 chart cards below.

#### Summary Stats Cards (`src/components/metrics/stats-cards.tsx`)
Four cards in a row using `useSummaryStats()`:

| Card | Value | Format | Icon |
|------|-------|--------|------|
| Emails Processed | `total_emails_processed` | Number with animated counter | `Mail` |
| Avg Response Time | `average_response_time_ms` | Format as seconds (e.g., "2.4s") | `Clock` |
| Approval Rate | `approval_rate` | Percentage (e.g., "87%") | `CheckCircle` |
| Human Review Rate | `human_review_rate` | Percentage (e.g., "23%") | `Eye` |

Each card shows the value prominently with a subtle icon and label beneath.

#### Intent Distribution Chart (`src/components/metrics/intent-chart.tsx`)
- **Type**: Pie/Donut chart (recharts `PieChart`)
- **Data**: `useIntentDistribution(dateFrom, dateTo)`
- **Segments**: One per `EmailClassification`, colors from `CHART_COLORS`
- **Interaction**: Hover for tooltip showing count + percentage
- **Filter**: Date range picker above the chart
- **Legend**: Below or beside chart with classification labels + colors

#### Response Latency Chart (`src/components/metrics/latency-chart.tsx`)
- **Type**: Line chart (recharts `LineChart`)
- **Data**: `useLatencyStats(dateFrom, dateTo)`
- **Lines**:
  - Total cycle time (blue, solid)
  - Classification time (green, dashed)
  - Generation time (purple, dashed)
- **Reference line**: Horizontal line at 4000ms labeled "4s Benchmark" (red, dotted)
- **X-axis**: Timestamps (daily or hourly)
- **Y-axis**: Milliseconds
- **Tooltip**: Shows all three values on hover

#### Tool Accuracy Chart (`src/components/metrics/accuracy-chart.tsx`)
- **Type**: Stacked bar chart (recharts `BarChart`)
- **Data**: `useToolAccuracy()`
- **Bars**: One per tool (`send_email`, `check_calendar`, `get_contact`, etc.)
- **Stacked segments**: Green (success) + Red (failure)
- **Labels**: Percentage on each bar showing success rate
- **X-axis**: Tool names
- **Y-axis**: Call count

**Data**: `useSummaryStats()`, `useIntentDistribution()`, `useLatencyStats()`, `useToolAccuracy()`.

---

### 10.5 Trace Viewer — `/traces`

**Purpose**: Detailed step-by-step visibility into agent pipeline runs for debugging.

#### Trace List Page (`/traces`)

**Component**: `src/components/trace-viewer/trace-list.tsx`

Table showing recent agent runs using `useTraces()`:

| Column | Field | Format |
|--------|-------|--------|
| Email Subject | `email_subject` | Text (link to detail) |
| Classification | `classification` | `ClassificationBadge` |
| Total Time | `total_time_ms` | Formatted as seconds (e.g., "3.2s") |
| Steps | `step_count` | Number (e.g., "7 steps") |
| Status | `status` | Color-coded: green=completed, red=failed, blue=in_progress |
| Date | `created_at` | Relative time |

Click a row to navigate to `/traces/[traceId]`.

#### Trace Detail Page (`/traces/[traceId]`)

Uses `useTraceDetail(traceId)`.

**Layout**: Two sections — flowchart graph on top, step detail panel below.

##### Trace Graph (`src/components/trace-viewer/trace-graph.tsx`)
```
Props: { steps: AgentLog[]; onSelectStep: (step: AgentLog) => void; selectedStepId?: string }
```
Visual flowchart showing the 7-step pipeline:

```
[classify] → [retrieve] → [decide] → [execute_tools] → [generate] → [review] → [dispatch]
```

Each node is a rounded box showing:
- Step name
- Latency (e.g., "420ms")
- Color based on result:
  - Green border/bg: completed successfully (`error_message === null`)
  - Red border/bg: failed (`error_message !== null`)
  - Yellow border/bg: skipped (not present in steps)
  - Blue border/bg: waiting in human queue (status = needs_review at review step)

Arrows/edges between nodes show data flow direction. Use Aceternity UI flowchart components or build with CSS Grid + SVG arrows.

Clicking a node selects it and populates the Step Detail Panel.

##### Step Detail Panel (`src/components/trace-viewer/step-detail.tsx`)
```
Props: { step: AgentLog }
```
Collapsible panel showing details of the selected pipeline step:

| Section | Content |
|---------|---------|
| **Step Name** | Step name + order number |
| **Latency** | Execution time in ms |
| **Input State** | Collapsible JSON viewer showing `input_state` |
| **Output State** | Collapsible JSON viewer showing `output_state` |
| **Tool Executions** | Table of `tool_executions` for this step: tool_name, params (JSON), result (JSON), success (green check / red X), latency_ms |
| **Errors** | Error message displayed in red if present |

Use shadcn/ui `Collapsible` for JSON sections. Format JSON with syntax highlighting (use `<pre>` with Tailwind `font-mono` styling or a JSON viewer component).

---

## 11. Shared Patterns & Conventions

### Component Pattern
```typescript
// Use named exports, not default exports
// Props interface defined inline or above the component
// Use cn() for conditional class merging

export function ComponentName({ prop1, prop2 }: ComponentNameProps) {
  return (...)
}
```

### Data Fetching Pattern
```typescript
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import api from "@/lib/api";

export function useEmails(filters: EmailFilters) {
  return useQuery({
    queryKey: ["emails", filters],
    queryFn: () => api.get("/emails", { params: filters }).then(r => r.data),
  });
}

export function useProcessEmail() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => api.post(`/emails/${id}/process`).then(r => r.data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["emails"] });
    },
  });
}
```

### Loading States
- Use skeleton loaders (shadcn/ui pattern) for initial page loads
- Use `Loader2` icon with `animate-spin` for button loading states
- Show toast notifications (shadcn/ui `toast`) on mutation success/failure

### Error Handling
- Show inline error messages for failed queries
- Show toast notifications for failed mutations
- The API interceptor handles 401 → redirect to login automatically

### Responsive Design
- Sidebar collapses to icons-only on `md` breakpoint and below
- Email detail panel uses full-screen sheet on mobile
- Metric charts stack vertically on small screens
- Split view in draft review stacks vertically on `< lg`

---

## 12. Build Order (Recommended Sequence)

Follow this order to build incrementally with working features at each step:

1. **Foundation**: Fix tsconfig paths, create `types/index.ts`, create `lib/constants.ts`, create `providers/query-provider.tsx`, update root layout
2. **shadcn/ui Setup**: Install all needed shadcn/ui components (`button`, `badge`, `card`, `sheet`, `table`, `dialog`, `input`, `select`, `tabs`, `toast`, `separator`, `collapsible`, `label`, `textarea`, `dropdown-menu`)
3. **App Shell**: Build `sidebar.tsx`, `header.tsx`, `app-shell.tsx` with navigation
4. **Login Page**: Build `/login` with auth form + Gmail connect
5. **Inbox Dashboard**: Build email list → classification badge → email card → email detail panel → filter bar → page assembly
6. **Draft Review**: Build original email → draft editor → confidence indicator → approval buttons → split view page
7. **Metrics Dashboard**: Build stats cards → intent chart → latency chart → accuracy chart → page assembly
8. **Trace Viewer**: Build trace list → trace graph → step detail → trace list page → trace detail page

---

## 13. Design Guidelines

- **Visual tone**: Clean, professional SaaS dashboard. Not playful — this handles business emails.
- **Spacing**: Use Tailwind's spacing scale consistently. Prefer `gap-4` / `p-6` for card padding, `gap-6` for section spacing.
- **Typography**: Inter font (already configured). Use `text-sm` for table content, `text-base` for body, `text-lg`/`text-xl` for headings.
- **Colors**: Follow the semantic color tokens defined in `globals.css`. Use classification/status colors from `constants.ts` for data-driven elements.
- **Dark mode**: All components must support dark mode via the `.dark` class on `<html>`. Use Tailwind's `dark:` prefix.
- **Animations**: Use `framer-motion` for page transitions and panel open/close. Keep animations subtle (200-300ms duration). Use `animate-spin` on `Loader2` for loading states.
- **Empty states**: Every list/table should handle the empty state with an icon + message + call-to-action (e.g., "No emails yet. Click Sync to fetch from Gmail.").
- **Accessibility**: All interactive elements need proper `aria-label` attributes. Use semantic HTML (`<main>`, `<nav>`, `<section>`). Ensure color contrast meets WCAG AA.
