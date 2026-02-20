"use client";

import { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import {
  Inbox,
  FileEdit,
  BarChart3,
  GitBranch,
  RefreshCw,
  LogOut,
  Loader2,
  Calendar,
  Users,
  Menu,
  X,
  ChevronDown,
  Sparkles,
} from "lucide-react";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";

const NAV_ITEMS = [
  { icon: Inbox, label: "Inbox", href: "/inbox", color: "text-blue-600", bgColor: "bg-blue-500/10" },
  { icon: FileEdit, label: "Drafts", href: "/drafts", color: "text-pink-600", bgColor: "bg-pink-500/10" },
  { icon: Calendar, label: "Calendar", href: "/calendar", color: "text-amber-600", bgColor: "bg-amber-500/10" },
  { icon: Users, label: "CRM", href: "/crm", color: "text-indigo-600", bgColor: "bg-indigo-500/10" },
  { icon: BarChart3, label: "Metrics", href: "/metrics", color: "text-violet-600", bgColor: "bg-violet-500/10" },
  { icon: GitBranch, label: "Traces", href: "/traces", color: "text-emerald-600", bgColor: "bg-emerald-500/10" },
];

interface TopNavProps {
  onSync?: () => void;
  isSyncing?: boolean;
  userEmail?: string;
  onLogout?: () => void;
}

export function TopNav({
  onSync,
  isSyncing = false,
  userEmail,
  onLogout,
}: TopNavProps) {
  const pathname = usePathname();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  return (
    <header className="fixed top-0 left-0 right-0 z-50">
      {/* Glass morphism nav bar like Sarvam */}
      <div className="mx-4 mt-4">
        <nav className="bg-white/80 backdrop-blur-xl border border-white/20 rounded-2xl shadow-lg shadow-black/5">
          <div className="px-4 sm:px-6">
            <div className="flex h-14 items-center justify-between">
              {/* Logo */}
              <Link href="/inbox" className="flex items-center gap-2">
                <div className="w-8 h-8 rounded-xl bg-gradient-to-br from-blue-600 to-violet-600 flex items-center justify-center shadow-lg shadow-blue-500/20">
                  <span className="text-white font-bold text-sm">R</span>
                </div>
                <span className="text-lg font-semibold tracking-tight hidden sm:block">ReasonFlow</span>
              </Link>

              {/* Desktop Navigation - Center */}
              <div className="hidden lg:flex items-center gap-1">
                {NAV_ITEMS.map((item) => {
                  const Icon = item.icon;
                  const isActive = pathname === item.href || pathname.startsWith(`${item.href}/`);

                  return (
                    <Link
                      key={item.href}
                      href={item.href}
                      className={cn(
                        "flex items-center gap-2 px-3 py-2 rounded-xl text-sm font-medium transition-all",
                        isActive
                          ? `${item.bgColor} ${item.color}`
                          : "text-slate-600 hover:bg-slate-100 hover:text-slate-900"
                      )}
                    >
                      <Icon className="size-4" />
                      <span>{item.label}</span>
                    </Link>
                  );
                })}
              </div>

              {/* Right side actions */}
              <div className="flex items-center gap-2">
                {/* AI Badge */}
                <div className="hidden sm:flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-gradient-to-r from-blue-500/10 to-violet-500/10 border border-blue-200/50">
                  <Sparkles className="size-3 text-blue-600" />
                  <span className="text-xs font-medium text-blue-700">AI</span>
                </div>

                {/* Sync Button */}
                <Button
                  onClick={onSync}
                  disabled={isSyncing}
                  variant="outline"
                  size="sm"
                  className="hidden sm:flex items-center gap-1.5 bg-white border-slate-200 hover:bg-slate-50"
                >
                  {isSyncing ? (
                    <Loader2 className="size-3.5 animate-spin text-blue-600" />
                  ) : (
                    <RefreshCw className="size-3.5 text-blue-600" />
                  )}
                  <span className="hidden xl:inline">Sync</span>
                </Button>

                {/* User Dropdown */}
                {userEmail && (
                  <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                      <Button
                        variant="ghost"
                        size="sm"
                        className="flex items-center gap-2 px-2 hover:bg-slate-100"
                      >
                        <div className="w-7 h-7 rounded-full bg-gradient-to-br from-blue-500 to-violet-500 flex items-center justify-center text-xs font-medium text-white uppercase">
                          {userEmail.charAt(0)}
                        </div>
                        <ChevronDown className="size-3.5 text-slate-400 hidden sm:block" />
                      </Button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent align="end" className="w-56">
                      <div className="px-2 py-1.5">
                        <p className="text-xs text-muted-foreground">Signed in as</p>
                        <p className="text-sm font-medium truncate">{userEmail}</p>
                      </div>
                      <DropdownMenuSeparator />
                      <DropdownMenuItem asChild>
                        <Link href="/inbox" className="cursor-pointer">
                          <Inbox className="size-4 mr-2" />
                          Inbox
                        </Link>
                      </DropdownMenuItem>
                      <DropdownMenuItem asChild>
                        <Link href="/drafts" className="cursor-pointer">
                          <FileEdit className="size-4 mr-2" />
                          Drafts
                        </Link>
                      </DropdownMenuItem>
                      <DropdownMenuSeparator />
                      <DropdownMenuItem
                        onClick={onSync}
                        disabled={isSyncing}
                        className="cursor-pointer lg:hidden"
                      >
                        <RefreshCw className={cn("size-4 mr-2", isSyncing && "animate-spin")} />
                        Sync Emails
                      </DropdownMenuItem>
                      <DropdownMenuSeparator className="lg:hidden" />
                      <DropdownMenuItem
                        onClick={onLogout}
                        className="cursor-pointer text-red-600 focus:text-red-600"
                      >
                        <LogOut className="size-4 mr-2" />
                        Logout
                      </DropdownMenuItem>
                    </DropdownMenuContent>
                  </DropdownMenu>
                )}

                {/* Mobile menu button */}
                <Button
                  variant="ghost"
                  size="icon"
                  className="lg:hidden"
                  onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
                >
                  {mobileMenuOpen ? (
                    <X className="size-5" />
                  ) : (
                    <Menu className="size-5" />
                  )}
                </Button>
              </div>
            </div>
          </div>

          {/* Mobile Navigation */}
          {mobileMenuOpen && (
            <div className="lg:hidden border-t border-slate-100 px-4 py-3">
              <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
                {NAV_ITEMS.map((item) => {
                  const Icon = item.icon;
                  const isActive = pathname === item.href || pathname.startsWith(`${item.href}/`);

                  return (
                    <Link
                      key={item.href}
                      href={item.href}
                      onClick={() => setMobileMenuOpen(false)}
                      className={cn(
                        "flex items-center gap-2 px-3 py-2.5 rounded-xl text-sm font-medium transition-all",
                        isActive
                          ? `${item.bgColor} ${item.color}`
                          : "text-slate-600 hover:bg-slate-100"
                      )}
                    >
                      <Icon className="size-4" />
                      <span>{item.label}</span>
                    </Link>
                  );
                })}
              </div>
              
              {/* Mobile sync button */}
              <Button
                onClick={() => {
                  onSync?.();
                  setMobileMenuOpen(false);
                }}
                disabled={isSyncing}
                className="w-full mt-3 gap-2"
                variant="outline"
              >
                {isSyncing ? (
                  <Loader2 className="size-4 animate-spin" />
                ) : (
                  <RefreshCw className="size-4" />
                )}
                Sync Emails
              </Button>
            </div>
          )}
        </nav>
      </div>
    </header>
  );
}
