"use client";

import { useState, useEffect } from "react";
import { AppShellTopNav } from "@/components/layout/app-shell-top-nav";
import { TraceList } from "@/components/trace-viewer/trace-list";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Pagination } from "@/components/ui/pagination";
import { useTraces } from "@/hooks/use-traces";
import { Activity, Workflow, Loader2, Search } from "lucide-react";
import { PageHeader, SectionCard, StaggerContainer, StaggerItem } from "@/components/layout/dashboard-shell";
import type { TraceFilters } from "@/types";
import { useQueryClient } from "@tanstack/react-query";

type TraceStatus = "completed" | "failed" | "processing";

const STATUSES: TraceStatus[] = ["completed", "failed", "processing"];

export default function TracesPage() {
  const queryClient = useQueryClient();
  const [searchInput, setSearchInput] = useState("");
  const [filters, setFilters] = useState<TraceFilters>({
    page: 1,
    page_size: 25,
  });
  // Debounce search input
  useEffect(() => {
    const timer = setTimeout(() => {
      // Cancel any in-flight queries for this key before triggering new search
      queryClient.cancelQueries({ queryKey: ["traces"] });
      setFilters((prev) => ({
        ...prev,
        search: searchInput || undefined,
        page: 1,
      }));
    }, 300);

    return () => clearTimeout(timer);
  }, [searchInput, queryClient]);

  const { data, isLoading, isFetching } = useTraces(filters);

  const traces = data?.items || [];
  const totalPages = data ? Math.ceil(data.total / data.per_page) || 1 : 1;
  const total = data?.total || 0;
  const page = filters.page || 1;
  const pageSize = filters.page_size || 25;

  const handleStatusChange = (value: string) => {
    setFilters((prev) => ({
      ...prev,
      status: value === "all" ? undefined : (value as TraceStatus),
      page: 1,
    }));
  };

  return (
    <AppShellTopNav>
      <StaggerContainer className="space-y-6">
        {/* Header */}
        <StaggerItem>
          <PageHeader
            icon={<Activity className="w-6 h-6 text-violet-600" />}
            iconColor="bg-violet-500/10"
            title="Trace Viewer"
            subtitle="View detailed execution traces of agent processing runs"
          />
        </StaggerItem>

        {/* Filters */}
        <StaggerItem>
          <div className="flex flex-col sm:flex-row gap-3">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 size-4 text-muted-foreground" />
              <Input
                placeholder="Search traces..."
                value={searchInput}
                onChange={(e) => setSearchInput(e.target.value)}
                className="pl-9 h-11 bg-white/70 border-white/50 focus:bg-white"
              />
            </div>

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

        {/* Trace List */}
        <StaggerItem>
          <SectionCard className="overflow-hidden relative">
            <div className="p-4 border-b bg-gradient-to-r from-violet-50/50 to-purple-50/50">
              <div className="flex items-center gap-2">
                <Workflow className="w-4 h-4 text-violet-500" />
                <span className="text-sm font-medium">Execution Traces</span>
                {data && (
                  <span className="px-2 py-0.5 rounded-full bg-violet-100 text-violet-600 text-xs font-medium">
                    {data.total}
                  </span>
                )}
              </div>
            </div>
            {isFetching && (
              <div className="absolute inset-0 bg-white/60 backdrop-blur-sm flex items-center justify-center z-10">
                <Loader2 className="size-8 animate-spin text-violet-500" />
              </div>
            )}
            <TraceList traces={traces} isLoading={isLoading && !data} />
          </SectionCard>
        </StaggerItem>

        {/* Pagination - always show when there's data */}
        {data && data.total > 0 && (
          <StaggerItem>
            <Pagination
              currentPage={page}
              totalPages={totalPages}
              totalItems={total}
              pageSize={pageSize}
              isFetching={isFetching}
              itemLabel="traces"
              onPageChange={(p) =>
                setFilters((prev) => ({ ...prev, page: p }))
              }
              onPageSizeChange={(size) =>
                setFilters((prev) => ({ ...prev, page_size: size, page: 1 }))
              }
            />
          </StaggerItem>
        )}
      </StaggerContainer>
    </AppShellTopNav>
  );
}
