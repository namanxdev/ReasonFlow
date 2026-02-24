"use client";

import { useState, useCallback, useEffect } from "react";
import { AppShellTopNav } from "@/components/layout/app-shell-top-nav";
import { EmailList } from "@/components/inbox/email-list";
import { EmailDetailPanel } from "@/components/inbox/email-detail-panel";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Pagination } from "@/components/ui/pagination";
import { useEmails, useSyncEmails, useClassifyEmails, useEmailStats, useSyncStatus } from "@/hooks/use-emails";
import { useWebSocket } from "@/hooks/use-websocket";
import { useQueryClient } from "@tanstack/react-query";
import type { EmailFilters, EmailClassification, EmailStatus } from "@/types";
import { RefreshCw, Search, Sparkles, Loader2, Inbox, Mail } from "lucide-react";
import { toast } from "sonner";
import { PageHeader, SectionCard, StaggerContainer, StaggerItem } from "@/components/layout/dashboard-shell";

const CLASSIFICATIONS: EmailClassification[] = [
  "inquiry",
  "meeting_request",
  "complaint",
  "follow_up",
  "spam",
  "other",
];

const STATUSES: EmailStatus[] = [
  "pending",
  "processing",
  "drafted",
  "needs_review",
  "approved",
  "sent",
  "rejected",
];

export default function InboxPage() {
  const [filters, setFilters] = useState<EmailFilters>({
    page: 1,
    page_size: 25,
    sort_by: "received_at",
    sort_order: "desc",
  });
  const [searchInput, setSearchInput] = useState("");
  const [selectedEmailId, setSelectedEmailId] = useState<string | null>(null);
  const [isPanelOpen, setIsPanelOpen] = useState(false);

  const queryClient = useQueryClient();

  const { data, isLoading, isFetching } = useEmails(filters);
  const { data: stats } = useEmailStats();
  const syncMutation = useSyncEmails();
  const classifyMutation = useClassifyEmails();

  const { data: syncStatus } = useSyncStatus();

  // WebSocket for real-time updates
  useWebSocket({
    url: `${process.env.NEXT_PUBLIC_WS_URL || "ws://localhost:8000"}/api/v1/ws`,
    onMessage: useCallback(
      (data: any) => {
        if (
          data.type === "email_received" ||
          data.type === "email_classified" ||
          data.type === "email_sync_complete"
        ) {
          queryClient.invalidateQueries({ queryKey: ["emails"] });
        }
      },
      [queryClient]
    ),
  });

  useEffect(() => {
    const timer = setTimeout(() => {
      // Cancel any in-flight queries for this key before triggering new search
      queryClient.cancelQueries({ queryKey: ["emails"] });
      setFilters((prev) => ({
        ...prev,
        search: searchInput || undefined,
        page: 1,
      }));
    }, 300);

    return () => clearTimeout(timer);
  }, [searchInput, queryClient]);

  const handleSync = () => {
    syncMutation.mutate(undefined, {
      onSuccess: (result) => {
        toast.success(
          `Synced ${result.created} new email${result.created !== 1 ? "s" : ""} (${result.fetched} checked)`
        );
      },
      onError: (error) => {
        toast.error(
          `Failed to sync emails: ${
            error instanceof Error ? error.message : "Unknown error"
          }`
        );
      },
    });
  };

  const handleClassify = () => {
    classifyMutation.mutate(undefined, {
      onSuccess: (result) => {
        toast.success(
          `Classified ${result.classified} email${result.classified !== 1 ? "s" : ""}${result.failed > 0 ? ` (${result.failed} failed)` : ""}`
        );
      },
      onError: (error) => {
        toast.error(
          `Failed to classify: ${error instanceof Error ? error.message : "Unknown error"}`
        );
      },
    });
  };

  const handleEmailSelect = useCallback((id: string) => {
    setSelectedEmailId(id);
    setIsPanelOpen(true);
  }, []);

  const handlePanelClose = useCallback(() => {
    setIsPanelOpen(false);
    setTimeout(() => setSelectedEmailId(null), 300);
  }, []);

  const handleSort = useCallback((field: string) => {
    setFilters((prev) => ({
      ...prev,
      sort_by: field,
      sort_order: prev.sort_by === field && prev.sort_order === "asc" ? "desc" : "asc",
    }));
  }, []);

  const handleClassificationChange = (value: string) => {
    setFilters((prev) => ({
      ...prev,
      classification: value === "all" ? undefined : (value as EmailClassification),
      page: 1,
    }));
  };

  const handleStatusChange = (value: string) => {
    setFilters((prev) => ({
      ...prev,
      status: value === "all" ? undefined : (value as EmailStatus),
      page: 1,
    }));
  };

  const currentPage = filters.page || 1;
  const totalPages = data ? Math.ceil(data.total / data.per_page) || 1 : 1;
  const emails = data?.items || [];

  useEffect(() => {
    if (!data) return;
    if (data.total === 0) return;

    const maxPage = Math.ceil(data.total / data.per_page) || 1;
    if (currentPage > maxPage) {
      setFilters((prev) => ({
        ...prev,
        page: maxPage,
      }));
    }
  }, [data, currentPage]);

  // Use stats from dedicated endpoint (full dataset, not just current page)
  const pendingCount = stats?.pending ?? 0;
  const needsReviewCount = stats?.needs_review ?? 0;
  const processedCount = stats?.sent ?? 0;

  return (
    <AppShellTopNav>
      <div className="py-6">
        <StaggerContainer className="space-y-6">
          {/* Header */}
          <StaggerItem>
            <PageHeader
              icon={<Inbox className="w-6 h-6 text-blue-600" />}
              iconColor="bg-blue-500/10"
              title="Inbox"
              subtitle="Manage and process your incoming emails"
              action={
                <>
                  {syncStatus?.auto_sync_active && (
                    <div className="flex items-center gap-2 text-sm text-green-600 mr-2">
                      <span className="relative flex h-2.5 w-2.5">
                        <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75" />
                        <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-green-500" />
                      </span>
                      Auto-sync active
                    </div>
                  )}
                  <Button
                    onClick={handleClassify}
                    disabled={classifyMutation.isPending}
                    variant="outline"
                    className="gap-2 bg-white/80 border-blue-200 hover:bg-blue-50"
                  >
                    {classifyMutation.isPending ? (
                      <Loader2 className="animate-spin size-4" />
                    ) : (
                      <Sparkles className="size-4 text-blue-600" />
                    )}
                    Classify All
                  </Button>
                  <Button
                    onClick={handleSync}
                    disabled={syncMutation.isPending}
                    className="gap-2 bg-gradient-to-r from-blue-600 to-violet-600 hover:from-blue-700 hover:to-violet-700 text-white border-0"
                  >
                    <RefreshCw className={syncMutation.isPending ? "animate-spin" : ""} />
                    Sync
                  </Button>
                </>
              }
            />
          </StaggerItem>

          {/* Quick Stats */}
          <StaggerItem>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="glass-card rounded-xl p-4 feature-card">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-xl bg-blue-500/10 flex items-center justify-center">
                    <Mail className="w-5 h-5 text-blue-600" />
                  </div>
                  <div>
                    <p className="text-xs text-muted-foreground">Total Emails</p>
                    <p className="text-lg font-semibold">{data?.total || 0}</p>
                  </div>
                </div>
              </div>
              <div className="glass-card rounded-xl p-4 feature-card">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-xl bg-amber-500/10 flex items-center justify-center">
                    <RefreshCw className="w-5 h-5 text-amber-600" />
                  </div>
                  <div>
                    <p className="text-xs text-muted-foreground">Pending</p>
                    <p className="text-lg font-semibold">{pendingCount}</p>
                  </div>
                </div>
              </div>
              <div className="glass-card rounded-xl p-4 feature-card">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-xl bg-pink-500/10 flex items-center justify-center">
                    <Sparkles className="w-5 h-5 text-pink-600" />
                  </div>
                  <div>
                    <p className="text-xs text-muted-foreground">Needs Review</p>
                    <p className="text-lg font-semibold">{needsReviewCount}</p>
                  </div>
                </div>
              </div>
              <div className="glass-card rounded-xl p-4 feature-card">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-xl bg-green-500/10 flex items-center justify-center">
                    <Inbox className="w-5 h-5 text-green-600" />
                  </div>
                  <div>
                    <p className="text-xs text-muted-foreground">Processed</p>
                    <p className="text-lg font-semibold">{processedCount}</p>
                  </div>
                </div>
              </div>
            </div>
          </StaggerItem>

          {/* Filters */}
          <StaggerItem>
            <div className="flex flex-col sm:flex-row gap-3">
              <div className="relative flex-1">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 size-4 text-muted-foreground" />
                <Input
                  placeholder="Search emails..."
                  value={searchInput}
                  onChange={(e) => setSearchInput(e.target.value)}
                  className="pl-9 h-11 bg-white/70 border-white/50 focus:bg-white"
                />
              </div>

              <Select
                value={filters.classification || "all"}
                onValueChange={handleClassificationChange}
              >
                <SelectTrigger className="w-full sm:w-44 h-11 bg-white/70 border-white/50">
                  <SelectValue placeholder="Classification" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Classifications</SelectItem>
                  {CLASSIFICATIONS.map((classification) => (
                    <SelectItem key={classification} value={classification}>
                      {classification
                        .split("_")
                        .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
                        .join(" ")}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>

              <Select
                value={filters.status || "all"}
                onValueChange={handleStatusChange}
              >
                <SelectTrigger className="w-full sm:w-44 h-11 bg-white/70 border-white/50">
                  <SelectValue placeholder="Status" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Statuses</SelectItem>
                  {STATUSES.map((status) => (
                    <SelectItem key={status} value={status}>
                      {status
                        .split("_")
                        .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
                        .join(" ")}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </StaggerItem>

          {/* Email List */}
          <StaggerItem>
            <SectionCard className="overflow-hidden relative">
              {isFetching && (
                <div className="absolute inset-0 bg-white/60 backdrop-blur-sm flex items-center justify-center z-10">
                  <Loader2 className="size-8 animate-spin text-blue-500" />
                </div>
              )}
              <EmailList
                emails={emails}
                isLoading={isLoading && !data}
                selectedId={selectedEmailId}
                onSelect={handleEmailSelect}
                onSort={handleSort}
              />
            </SectionCard>
          </StaggerItem>

          {/* Pagination - always show when there's data */}
          {data && data.total > 0 && (
            <StaggerItem>
              <Pagination
                currentPage={currentPage}
                totalPages={totalPages}
                totalItems={data.total}
                pageSize={filters.page_size || 25}
                isFetching={isFetching}
                itemLabel="emails"
                onPageChange={(page) =>
                  setFilters((prev) => ({ ...prev, page }))
                }
                onPageSizeChange={(size) =>
                  setFilters((prev) => ({ ...prev, page_size: size, page: 1 }))
                }
              />
            </StaggerItem>
          )}
        </StaggerContainer>
      </div>

      <EmailDetailPanel
        emailId={selectedEmailId}
        open={isPanelOpen}
        onClose={handlePanelClose}
      />
    </AppShellTopNav>
  );
}
