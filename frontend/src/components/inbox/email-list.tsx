"use client";

import {
  Table,
  TableBody,
  TableHead,
  TableHeader,
  TableRow,
  TableCell,
} from "@/components/ui/table";
import { EmailCard } from "./email-card";
import type { Email } from "@/types";
import { ArrowUpDown, Inbox } from "lucide-react";

interface EmailListProps {
  emails: Email[];
  isLoading: boolean;
  selectedId: string | null;
  onSelect: (id: string) => void;
  onSort?: (field: string) => void;
}

function SkeletonRow() {
  return (
    <TableRow>
      <TableCell>
        <div className="h-4 w-32 bg-muted animate-pulse rounded" />
      </TableCell>
      <TableCell>
        <div className="h-4 w-64 bg-muted animate-pulse rounded" />
      </TableCell>
      <TableCell>
        <div className="h-6 w-24 bg-muted animate-pulse rounded-full" />
      </TableCell>
      <TableCell>
        <div className="h-4 w-28 bg-muted animate-pulse rounded" />
      </TableCell>
      <TableCell>
        <div className="h-4 w-16 bg-muted animate-pulse rounded" />
      </TableCell>
    </TableRow>
  );
}

function EmptyState() {
  return (
    <div className="flex flex-col items-center justify-center py-16 text-center">
      <div className="bg-muted/30 rounded-full p-6 mb-4">
        <Inbox className="size-12 text-muted-foreground" />
      </div>
      <h3 className="text-lg font-semibold mb-2">No emails found</h3>
      <p className="text-muted-foreground text-sm max-w-sm">
        There are no emails matching your current filters. Try adjusting your
        search criteria or sync new emails.
      </p>
    </div>
  );
}

export function EmailList({
  emails,
  isLoading,
  selectedId,
  onSelect,
  onSort,
}: EmailListProps) {
  if (isLoading) {
    return (
      <div className="border rounded-md">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Sender</TableHead>
              <TableHead>Subject</TableHead>
              <TableHead>Classification</TableHead>
              <TableHead>Status</TableHead>
              <TableHead>Date</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {Array.from({ length: 5 }).map((_, i) => (
              <SkeletonRow key={i} />
            ))}
          </TableBody>
        </Table>
      </div>
    );
  }

  if (emails.length === 0) {
    return <EmptyState />;
  }

  return (
    <div className="border rounded-md">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>
              <button
                onClick={() => onSort?.("sender")}
                className="flex items-center gap-1 hover:text-foreground transition-colors"
              >
                Sender
                {onSort && <ArrowUpDown className="size-3" />}
              </button>
            </TableHead>
            <TableHead>
              <button
                onClick={() => onSort?.("subject")}
                className="flex items-center gap-1 hover:text-foreground transition-colors"
              >
                Subject
                {onSort && <ArrowUpDown className="size-3" />}
              </button>
            </TableHead>
            <TableHead>
              <button
                onClick={() => onSort?.("classification")}
                className="flex items-center gap-1 hover:text-foreground transition-colors"
              >
                Classification
                {onSort && <ArrowUpDown className="size-3" />}
              </button>
            </TableHead>
            <TableHead>
              <button
                onClick={() => onSort?.("status")}
                className="flex items-center gap-1 hover:text-foreground transition-colors"
              >
                Status
                {onSort && <ArrowUpDown className="size-3" />}
              </button>
            </TableHead>
            <TableHead>
              <button
                onClick={() => onSort?.("received_at")}
                className="flex items-center gap-1 hover:text-foreground transition-colors"
              >
                Date
                {onSort && <ArrowUpDown className="size-3" />}
              </button>
            </TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {emails.map((email) => (
            <EmailCard
              key={email.id}
              email={email}
              isSelected={selectedId === email.id}
              onClick={() => onSelect(email.id)}
            />
          ))}
        </TableBody>
      </Table>
    </div>
  );
}
