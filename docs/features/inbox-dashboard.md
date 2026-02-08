# Inbox Dashboard

## Overview

The inbox dashboard is the primary interface for viewing and managing emails processed by the AI agent.

## Features

### Email List
- Paginated table of emails sorted by `received_at` (newest first)
- Columns: Sender, Subject, Classification Badge, Status, Date
- Sortable by any column
- Filterable by classification, status, date range, search text

### Classification Badges
Color-coded badges showing AI-assigned intent:
| Classification | Color | Icon |
|---------------|-------|------|
| Meeting Request | Blue | 🗓️ |
| Inquiry | Green | ❓ |
| Complaint | Red | ⚠️ |
| Follow-up | Yellow | 🔄 |
| Spam | Gray | 🚫 |
| Other | Purple | 📌 |

### Status Indicators
| Status | Display |
|--------|---------|
| Pending | Gray dot |
| Processing | Spinning icon |
| Drafted | Orange dot |
| Needs Review | Yellow warning |
| Approved | Green check |
| Sent | Blue check |
| Rejected | Red X |

### Email Detail Panel
Click an email to open a slide-out sheet showing:
- Full email body
- Agent classification with confidence score
- Suggested actions
- Link to trace viewer for this email
- Quick approve/reject buttons if draft exists

## Components

| Component | File | Description |
|-----------|------|-------------|
| Page | `inbox/page.tsx` | Main inbox page with layout |
| EmailList | `inbox/email-list.tsx` | Sortable/filterable table |
| EmailCard | `inbox/email-card.tsx` | Single email row |
| EmailDetailPanel | `inbox/email-detail-panel.tsx` | Slide-out detail view |
| ClassificationBadge | `inbox/classification-badge.tsx` | Color-coded badge |

## Data Fetching

Uses TanStack Query hooks:
- `useEmails(filters)` — paginated email list with filtering
- `useEmail(id)` — single email details
- `useProcessEmail()` — mutation to trigger agent processing

## UI Libraries Used

- **HeroUI** — Productivity dashboard components for the email table
- **shadcn/ui** — Base components (badges, buttons, sheets)
