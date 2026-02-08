"use client";

import { useState } from "react";
import { AppShell } from "@/components/layout/app-shell";
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
import { ChevronLeft, ChevronRight } from "lucide-react";

export default function TracesPage() {
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(25);

  const { data, isLoading } = useTraces(page, pageSize);

  const traces = data?.items || [];
  const totalPages = data?.total_pages || 1;
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
    <AppShell>
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold tracking-tight">Trace Viewer</h1>
            <p className="text-muted-foreground mt-1">
              View detailed execution traces of agent processing runs
            </p>
          </div>
        </div>

        <TraceList traces={traces} isLoading={isLoading} />

        {!isLoading && data && traces.length > 0 && (
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <p className="text-sm text-muted-foreground">
                Showing {(page - 1) * pageSize + 1} to{" "}
                {Math.min(page * pageSize, total)} of {total} traces
              </p>
              <Select value={String(pageSize)} onValueChange={handlePageSizeChange}>
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
                Page {page} of {totalPages}
              </p>
              <div className="flex gap-1">
                <Button
                  variant="outline"
                  size="icon-sm"
                  onClick={handlePreviousPage}
                  disabled={page === 1}
                >
                  <ChevronLeft />
                </Button>
                <Button
                  variant="outline"
                  size="icon-sm"
                  onClick={handleNextPage}
                  disabled={page === totalPages}
                >
                  <ChevronRight />
                </Button>
              </div>
            </div>
          </div>
        )}
      </div>
    </AppShell>
  );
}
