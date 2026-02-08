# Metrics Dashboard

## Overview

The metrics dashboard provides visibility into agent performance, email classification distribution, and tool execution statistics.

## Charts

### 1. Intent Distribution (Pie/Donut Chart)
- Shows breakdown of email classifications over time
- Segments: Inquiry, Meeting Request, Complaint, Follow-up, Spam, Other
- Color-coded to match classification badges
- Filterable by date range

### 2. Response Latency (Line Chart)
- Agent processing time over time (daily/hourly)
- Lines for: total cycle time, classification time, generation time
- Target line at 4s (performance benchmark)
- Tooltip with exact latency values

### 3. Tool Accuracy (Bar Chart)
- Success rate per tool (send_email, check_calendar, get_contact, etc.)
- Stacked bars: success vs failure
- Percentage labels on each bar

### 4. Summary Stats Cards
- Total emails processed
- Average response time
- Approval rate (auto-approved / total)
- Human review rate

## Components

| Component | File | Description |
|-----------|------|-------------|
| Page | `metrics/page.tsx` | Dashboard grid layout |
| IntentChart | `metrics/intent-chart.tsx` | Pie chart (recharts) |
| LatencyChart | `metrics/latency-chart.tsx` | Line chart (recharts) |
| AccuracyChart | `metrics/accuracy-chart.tsx` | Bar chart (recharts) |
| StatsCards | `metrics/stats-cards.tsx` | Summary stat cards |

## Data Fetching

TanStack Query hooks:
- `useIntentDistribution()` — GET /metrics/intents
- `useLatencyStats()` — GET /metrics/latency
- `useToolAccuracy()` — GET /metrics/tools

## UI Libraries Used

- **Fancy Components** — Data visualization overlays and animated counters
- **recharts** — Core charting library
- **shadcn/ui** — Card containers, date picker for filtering
