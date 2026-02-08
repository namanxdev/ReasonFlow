# Draft Review

## Overview

The draft review panel allows users to inspect, edit, approve, or reject AI-generated email responses before they are sent.

## Features

### Split View
- **Left panel**: Original email (read-only)
- **Right panel**: AI-generated draft (editable)

### Confidence Indicator
- Visual meter showing the agent's classification confidence
- Color gradient: green (>0.9) → yellow (0.7-0.9) → red (<0.7)
- Displays: "High Confidence", "Medium Confidence", "Low Confidence"

### Action Buttons
| Action | Description | Effect |
|--------|-------------|--------|
| Approve | Accept draft as-is | Sends email immediately |
| Edit | Enable editing mode | Allows text modification before sending |
| Reject | Discard draft | Marks email for manual handling |

### Edit Mode
- Rich textarea with the AI draft
- User can modify text freely
- "Send Edited" button to approve modified version
- "Cancel" returns to review view

## Components

| Component | File | Description |
|-----------|------|-------------|
| Page | `drafts/page.tsx` | Draft review page |
| DraftEditor | `draft-review/draft-editor.tsx` | Editable draft textarea |
| OriginalEmail | `draft-review/original-email.tsx` | Read-only original display |
| ApprovalButtons | `draft-review/approval-buttons.tsx` | Accept/Edit/Reject with confirmations |
| ConfidenceIndicator | `draft-review/confidence-indicator.tsx` | Visual confidence meter |

## Data Fetching

TanStack Query hooks:
- `useDrafts()` — list drafts awaiting review
- `useApproveDraft()` — mutation to approve
- `useRejectDraft()` — mutation to reject
- `useEditDraft()` — mutation to update draft content

## UI Libraries Used

- **Magic UI** — Advanced widgets for the split view and confidence meter
- **shadcn/ui** — Dialog confirmations, textarea, buttons
