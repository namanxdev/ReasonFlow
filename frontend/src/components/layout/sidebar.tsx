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
  Calendar,
  Users,
  Sparkles,
} from "lucide-react";

const NAV_ITEMS = [
  { icon: Inbox, label: "Inbox", href: "/inbox", color: "text-blue-600", bgColor: "bg-blue-500/10" },
  { icon: FileEdit, label: "Drafts", href: "/drafts", color: "text-pink-600", bgColor: "bg-pink-500/10" },
  { icon: Calendar, label: "Calendar", href: "/calendar", color: "text-amber-600", bgColor: "bg-amber-500/10" },
  { icon: Users, label: "CRM", href: "/crm", color: "text-indigo-600", bgColor: "bg-indigo-500/10" },
  { icon: BarChart3, label: "Metrics", href: "/metrics", color: "text-violet-600", bgColor: "bg-violet-500/10" },
  { icon: GitBranch, label: "Traces", href: "/traces", color: "text-emerald-600", bgColor: "bg-emerald-500/10" },
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
  userEmail,
  onLogout,
}: SidebarProps) {
  const pathname = usePathname();
  const [isExpanded, setIsExpanded] = useState(true);

  return (
    <aside
      className={cn(
        "flex h-screen flex-col border-r border-slate-200/80 bg-white/80 backdrop-blur-xl transition-all duration-300",
        isExpanded ? "w-64" : "w-20"
      )}
    >
      {/* Header with logo */}
      <div className="flex h-16 items-center justify-between px-4 border-b border-slate-100">
        {isExpanded ? (
          <Link href="/" className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-blue-600 to-violet-600 flex items-center justify-center">
              <span className="text-white font-bold text-sm">R</span>
            </div>
            <span className="text-lg font-semibold tracking-tight">ReasonFlow</span>
          </Link>
        ) : (
          <Link href="/" className="mx-auto">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-blue-600 to-violet-600 flex items-center justify-center">
              <span className="text-white font-bold text-sm">R</span>
            </div>
          </Link>
        )}
        <button
          onClick={() => setIsExpanded(!isExpanded)}
          className={cn(
            "rounded-lg p-1.5 text-slate-400 transition-colors hover:bg-slate-100 hover:text-slate-600",
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
          const isActive = pathname === item.href || pathname.startsWith(`${item.href}/`);

          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition-all",
                isActive
                  ? `${item.bgColor} ${item.color} shadow-sm`
                  : "text-slate-600 hover:bg-slate-100 hover:text-slate-900",
                !isExpanded && "justify-center px-2"
              )}
              aria-current={isActive ? "page" : undefined}
              title={!isExpanded ? item.label : undefined}
            >
              <div className={cn(
                "w-8 h-8 rounded-lg flex items-center justify-center transition-colors",
                isActive ? "bg-white/60" : "bg-slate-100"
              )}>
                <Icon className="size-4 shrink-0" aria-hidden="true" />
              </div>
              {isExpanded && <span>{item.label}</span>}
            </Link>
          );
        })}
      </nav>

      {/* Bottom section */}
      <div className="border-t border-slate-100 p-3">
        {/* Gmail connection status */}
        <div
          className={cn(
            "mb-3 flex items-center gap-2 rounded-xl bg-green-50 px-3 py-2 border border-green-100",
            !isExpanded && "justify-center px-2"
          )}
        >
          <div
            className="size-2.5 shrink-0 rounded-full bg-green-500 shadow-sm shadow-green-500/30"
            aria-label="Gmail connected"
          />
          {isExpanded && (
            <span className="text-xs font-medium text-green-700">Gmail Connected</span>
          )}
        </div>

        {/* Sync button */}
        <Button
          onClick={onSync}
          disabled={isSyncing}
          variant="outline"
          size={isExpanded ? "sm" : "icon-sm"}
          className={cn(
            "w-full bg-white border-slate-200 hover:bg-slate-50 hover:border-slate-300",
            !isExpanded && "px-0"
          )}
          aria-label="Sync emails"
        >
          {isSyncing ? (
            <Loader2 className="size-4 animate-spin text-blue-600" aria-hidden="true" />
          ) : (
            <RefreshCw className="size-4 text-blue-600" aria-hidden="true" />
          )}
          {isExpanded && <span className="ml-2">Sync Emails</span>}
        </Button>

        <Separator className="my-3 bg-slate-100" />

        {/* User info and logout */}
        <div className="space-y-2">
          {isExpanded ? (
            <div className="flex items-center gap-2.5 px-3 py-1">
              <div className="flex size-8 shrink-0 items-center justify-center rounded-full bg-gradient-to-br from-blue-500 to-violet-500 text-xs font-medium text-white uppercase">
                {userEmail ? userEmail.charAt(0) : "?"}
              </div>
              <p className="truncate text-xs text-slate-500" title={userEmail}>
                {userEmail}
              </p>
            </div>
          ) : (
            <div className="flex justify-center py-1">
              <div 
                className="flex size-8 items-center justify-center rounded-full bg-gradient-to-br from-blue-500 to-violet-500 text-xs font-medium text-white uppercase" 
                title={userEmail}
              >
                {userEmail ? userEmail.charAt(0) : "?"}
              </div>
            </div>
          )}
          <Button
            onClick={onLogout}
            variant="ghost"
            size={isExpanded ? "sm" : "icon-sm"}
            className={cn(
              "w-full text-slate-500 hover:bg-slate-100 hover:text-slate-700",
              !isExpanded && "px-0"
            )}
            aria-label="Logout"
          >
            <LogOut className="size-4" aria-hidden="true" />
            {isExpanded && <span className="ml-2">Logout</span>}
          </Button>
        </div>
      </div>
    </aside>
  );
}
