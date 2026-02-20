"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import { AppShellTopNav } from "@/components/layout/app-shell-top-nav";
import { TraceList } from "@/components/trace-viewer/trace-list";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { useTraces } from "@/hooks/use-traces";
import { ChevronLeft, ChevronRight, Activity, Workflow, Loader2 } from "lucide-react";
import { PageHeader, SectionCard, StaggerContainer, StaggerItem } from "@/components/layout/dashboard-shell";

export default function TracesPage() {
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(25);

  const { data, isLoading, isFetching } = useTraces(page, pageSize);

  const traces = data?.items || [];
  const totalPages = data ? Math.ceil(data.total / data.per_page) || 1 : 1;
  const total = data?.total || 0;

  const handlePreviousPage = () => {
    setPage((prev) => Math.max(1, prev - 1));
  };

  const handleNextPage = () => {
    setPage((prev) => Math.min(totalPages, prev + 1));
  };

  const handlePageSizeChange = (value: string) => {
    setPageSize(parseInt(value));
    setPage(1);
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
            <motion.div 
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="flex items-center justify-between bg-white/50 rounded-xl p-3"
            >
              <div className="flex items-center gap-4">
                <p className="text-sm text-muted-foreground">
                  Showing {(page - 1) * pageSize + 1} to{" "}
                  {Math.min(page * pageSize, total)} of {total} traces
                </p>
                <Select value={String(pageSize)} onValueChange={handlePageSizeChange}>
                  <SelectTrigger className="w-28 h-9 bg-white/70">
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
                  Page <span className="font-medium text-foreground">{page}</span> of {totalPages}
                </p>
                <div className="flex gap-1">
                  <Button
                    variant="outline"
                    size="icon-sm"
                    onClick={handlePreviousPage}
                    disabled={page <= 1 || isFetching}
                    className="bg-white/70"
                  >
                    <ChevronLeft className="size-4" />
                  </Button>
                  <Button
                    variant="outline"
                    size="icon-sm"
                    onClick={handleNextPage}
                    disabled={page >= totalPages || isFetching}
                    className="bg-white/70"
                  >
                    <ChevronRight className="size-4" />
                  </Button>
                </div>
              </div>
            </motion.div>
          </StaggerItem>
        )}
      </StaggerContainer>
    </AppShellTopNav>
  );
}
