"use client";

import { useState, useCallback, useEffect } from "react";
import { AppShell } from "@/components/layout/app-shell";
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
import { useEmails, useSyncEmails, useClassifyEmails } from "@/hooks/use-emails";
import type { EmailFilters, EmailClassification, EmailStatus } from "@/types";
import { RefreshCw, Search, ChevronLeft, ChevronRight, Sparkles, Loader2 } from "lucide-react";
import { toast } from "sonner";

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

  const { data, isLoading } = useEmails(filters);
  const syncMutation = useSyncEmails();
  const classifyMutation = useClassifyEmails();

  useEffect(() => {
    const timer = setTimeout(() => {
      setFilters((prev) => ({
        ...prev,
        search: searchInput || undefined,
        page: 1,
      }));
    }, 300);

    return () => clearTimeout(timer);
  }, [searchInput]);

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

  const handlePageSizeChange = (value: string) => {
    setFilters((prev) => ({
      ...prev,
      page_size: parseInt(value),
      page: 1,
    }));
  };

  const handlePreviousPage = () => {
    setFilters((prev) => ({
      ...prev,
      page: Math.max(1, (prev.page || 1) - 1),
    }));
  };

  const handleNextPage = () => {
    if (!data) return;
    const maxPage = Math.ceil(data.total / data.per_page) || 1;
    setFilters((prev) => ({
      ...prev,
      page: Math.min(maxPage, (prev.page || 1) + 1),
    }));
  };

  const currentPage = filters.page || 1;
  const totalPages = data ? Math.ceil(data.total / data.per_page) || 1 : 1;
  const emails = data?.items || [];

  return (
    <AppShell>
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold tracking-tight">Inbox</h1>
            <p className="text-muted-foreground mt-1">
              Manage and process your incoming emails
            </p>
          </div>
          <div className="flex gap-2">
            <Button
              onClick={handleClassify}
              disabled={classifyMutation.isPending}
              variant="outline"
            >
              {classifyMutation.isPending ? (
                <Loader2 className="animate-spin" />
              ) : (
                <Sparkles className="size-4" />
              )}
              Classify All
            </Button>
            <Button
              onClick={handleSync}
              disabled={syncMutation.isPending}
              variant="default"
            >
              <RefreshCw
                className={syncMutation.isPending ? "animate-spin" : ""}
              />
              Sync
            </Button>
          </div>
        </div>

        <div className="flex flex-col sm:flex-row gap-4">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 size-4 text-muted-foreground" />
            <Input
              placeholder="Search emails..."
              value={searchInput}
              onChange={(e) => setSearchInput(e.target.value)}
              className="pl-9"
            />
          </div>

          <Select
            value={filters.classification || "all"}
            onValueChange={handleClassificationChange}
          >
            <SelectTrigger className="w-full sm:w-48">
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
            <SelectTrigger className="w-full sm:w-48">
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

        <EmailList
          emails={emails}
          isLoading={isLoading}
          selectedId={selectedEmailId}
          onSelect={handleEmailSelect}
          onSort={handleSort}
        />

        {!isLoading && data && emails.length > 0 && (
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <p className="text-sm text-muted-foreground">
                Showing {(currentPage - 1) * (filters.page_size || 25) + 1} to{" "}
                {Math.min(currentPage * (filters.page_size || 25), data.total)}{" "}
                of {data.total} emails
              </p>
              <Select
                value={String(filters.page_size || 25)}
                onValueChange={handlePageSizeChange}
              >
                <SelectTrigger className="w-32">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="10">10 per page</SelectItem>
                  <SelectItem value="25">25 per page</SelectItem>
                  <SelectItem value="50">50 per page</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="flex items-center gap-2">
              <p className="text-sm text-muted-foreground">
                Page {currentPage} of {totalPages}
              </p>
              <div className="flex gap-1">
                <Button
                  variant="outline"
                  size="icon-sm"
                  onClick={handlePreviousPage}
                  disabled={currentPage === 1}
                >
                  <ChevronLeft />
                </Button>
                <Button
                  variant="outline"
                  size="icon-sm"
                  onClick={handleNextPage}
                  disabled={currentPage === totalPages}
                >
                  <ChevronRight />
                </Button>
              </div>
            </div>
          </div>
        )}
      </div>

      <EmailDetailPanel
        emailId={selectedEmailId}
        open={isPanelOpen}
        onClose={handlePanelClose}
      />
    </AppShell>
  );
}
