# Trace Viewer

## Overview

The trace viewer provides detailed visibility into each step of the agent workflow, enabling debugging and performance analysis.

## Features

### Trace List
- Table of recent agent runs
- Columns: Email Subject, Classification, Total Time, Step Count, Status, Date
- Click to expand full trace detail

### Trace Graph (Flowchart)
Visual representation of the LangGraph workflow:
- Nodes rendered as boxes with step name + latency
- Edges as arrows showing data flow
- Color coding:
  - Green: completed successfully
  - Red: failed
  - Yellow: skipped
  - Blue: currently in HUMAN_QUEUE
- Timing annotations on each edge

### Step Detail Panel
Click any node in the graph to see:
- **Input State**: Full JSON state entering the node
- **Output State**: Full JSON state exiting the node
- **Tool Executions**: Any tools invoked during this step
- **Latency**: Exact execution time in milliseconds
- **Errors**: Error messages if the step failed

## Components

| Component | File | Description |
|-----------|------|-------------|
| Trace List Page | `traces/page.tsx` | Table of agent runs |
| Trace Detail Page | `traces/[traceId]/page.tsx` | Single run detail |
| TraceList | `trace-viewer/trace-list.tsx` | Sortable trace table |
| TraceGraph | `trace-viewer/trace-graph.tsx` | Visual flowchart |
| StepDetail | `trace-viewer/step-detail.tsx` | Node I/O inspector |

## Data Fetching

TanStack Query hooks:
- `useTraces()` — GET /traces (paginated list)
- `useTraceDetail(traceId)` — GET /traces/{id} (full detail with steps)

## UI Libraries Used

- **Aceternity UI** — Interactive flowchart layouts with animations
- **shadcn/ui** — Collapsible panels, JSON viewer, tables
