"use client";

import { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import {
  Inbox,
  FileEdit,
  BarChart3,
  GitBranch,
  RefreshCw,
  LogOut,
  ChevronLeft,
  ChevronRight,
  Loader2,
} from "lucide-react";

const NAV_ITEMS = [
  { icon: Inbox, label: "Inbox", href: "/inbox" },
  { icon: FileEdit, label: "Drafts", href: "/drafts" },
  { icon: BarChart3, label: "Metrics", href: "/metrics" },
  { icon: GitBranch, label: "Traces", href: "/traces" },
];

interface SidebarProps {
  onSync?: () => void;
  isSyncing?: boolean;
  userEmail?: string;
  onLogout?: () => void;
}

export function Sidebar({
  onSync,
  isSyncing = false,
  userEmail = "user@example.com",
  onLogout,
}: SidebarProps) {
  const pathname = usePathname();
  const [isExpanded, setIsExpanded] = useState(true);

  return (
    <aside
      className={cn(
        "flex h-screen flex-col border-r bg-zinc-950 text-zinc-100 transition-all duration-300",
        isExpanded ? "w-60" : "w-16"
      )}
    >
      {/* Header with toggle */}
      <div className="flex h-14 items-center justify-between border-b border-zinc-800 px-4">
        {isExpanded && (
          <h1 className="text-lg font-semibold tracking-tight">ReasonFlow</h1>
        )}
        <button
          onClick={() => setIsExpanded(!isExpanded)}
          className={cn(
            "rounded-md p-1.5 text-zinc-400 transition-colors hover:bg-zinc-800 hover:text-zinc-100",
            !isExpanded && "mx-auto"
          )}
          aria-label={isExpanded ? "Collapse sidebar" : "Expand sidebar"}
        >
          {isExpanded ? (
            <ChevronLeft className="size-4" />
          ) : (
            <ChevronRight className="size-4" />
          )}
        </button>
      </div>

      {/* Navigation */}
      <nav className="flex-1 space-y-1 p-3" aria-label="Main navigation">
        {NAV_ITEMS.map((item) => {
          const Icon = item.icon;
          const isActive = pathname === item.href;

          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-all",
                isActive
                  ? "bg-zinc-800 text-zinc-50 shadow-sm"
                  : "text-zinc-400 hover:bg-zinc-900 hover:text-zinc-100",
                !isExpanded && "justify-center px-2"
              )}
              aria-current={isActive ? "page" : undefined}
              title={!isExpanded ? item.label : undefined}
            >
              <Icon className="size-5 shrink-0" aria-hidden="true" />
              {isExpanded && <span>{item.label}</span>}
            </Link>
          );
        })}
      </nav>

      {/* Bottom section */}
      <div className="border-t border-zinc-800 p-3">
        {/* Gmail connection status */}
        <div
          className={cn(
            "mb-3 flex items-center gap-2 rounded-md bg-zinc-900 px-3 py-2",
            !isExpanded && "justify-center px-2"
          )}
        >
          <div
            className="size-2 shrink-0 rounded-full bg-green-500 shadow-sm shadow-green-500/50"
            aria-label="Gmail connected"
          />
          {isExpanded && (
            <span className="text-xs text-zinc-400">Gmail Connected</span>
          )}
        </div>

        {/* Sync button */}
        <Button
          onClick={onSync}
          disabled={isSyncing}
          variant="outline"
          size={isExpanded ? "sm" : "icon-sm"}
          className={cn(
            "w-full bg-zinc-900 text-zinc-100 hover:bg-zinc-800",
            !isExpanded && "px-0"
          )}
          aria-label="Sync emails"
        >
          {isSyncing ? (
            <Loader2 className="size-4 animate-spin" aria-hidden="true" />
          ) : (
            <RefreshCw className="size-4" aria-hidden="true" />
          )}
          {isExpanded && <span>Sync Emails</span>}
        </Button>

        <Separator className="my-3 bg-zinc-800" />

        {/* User info and logout */}
        <div className="space-y-2">
          {isExpanded && (
            <div className="px-3 py-1">
              <p className="truncate text-xs text-zinc-400" title={userEmail}>
                {userEmail}
              </p>
            </div>
          )}
          <Button
            onClick={onLogout}
            variant="ghost"
            size={isExpanded ? "sm" : "icon-sm"}
            className={cn(
              "w-full text-zinc-400 hover:bg-zinc-900 hover:text-zinc-100",
              !isExpanded && "px-0"
            )}
            aria-label="Logout"
          >
            <LogOut className="size-4" aria-hidden="true" />
            {isExpanded && <span>Logout</span>}
          </Button>
        </div>
      </div>
    </aside>
  );
}
