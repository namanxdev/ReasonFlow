# App Shell Components

This directory contains the layout components for the ReasonFlow application.

## Components

### AppShell

The main layout wrapper that combines the Sidebar and Header components.

#### Usage

```tsx
import { AppShell } from "@/components/layout";

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return <AppShell userEmail="user@example.com">{children}</AppShell>;
}
```

#### Props

- `children: React.ReactNode` - The page content to render
- `userEmail?: string` - The user's email address (optional, defaults to "user@example.com")

#### Features

- Handles email sync using `useSyncEmails` hook
- Shows toast notifications on sync success/failure
- Handles logout (clears localStorage and redirects to /login)
- Responsive layout with fixed sidebar and scrollable content area

### Sidebar

Fixed left sidebar with navigation and user controls.

#### Features

- Collapsible design (240px expanded, 64px collapsed)
- Navigation links with active state highlighting
- Gmail connection status indicator (hardcoded as connected)
- Sync emails button with loading state
- User email display and logout button
- Smooth transitions and hover states

#### Navigation Links

- Inbox → /inbox
- Drafts → /drafts
- Metrics → /metrics
- Traces → /traces

### Header

Top header bar with breadcrumb navigation.

#### Features

- Dynamic page title based on current route
- Breadcrumb navigation for nested routes (e.g., Traces > Trace Detail)
- Clean, minimal design with border-bottom

#### Route Mappings

- `/inbox` → "Inbox"
- `/drafts` → "Draft Review"
- `/metrics` → "Metrics"
- `/traces` → "Traces"
- `/traces/[id]` → "Traces > Trace Detail"

## Example: Dashboard Layout

Create a layout file at `src/app/(dashboard)/layout.tsx`:

```tsx
"use client";

import { AppShell } from "@/components/layout";

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return <AppShell userEmail="user@example.com">{children}</AppShell>;
}
```

## Dependencies

- Next.js 16 App Router
- Tailwind CSS v4
- shadcn/ui components (Button, Separator, Toaster)
- lucide-react for icons
- sonner for toast notifications
- @tanstack/react-query for data fetching

## Notes

- All components use "use client" directive
- The Toaster component must be added to the root layout for toast notifications to work
- The sidebar defaults to expanded on larger screens and can be toggled
- Active navigation links are highlighted based on the current pathname
