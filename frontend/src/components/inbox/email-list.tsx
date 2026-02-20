"use client";

import { motion } from "framer-motion";
import { EmailCard } from "./email-card";
import type { Email } from "@/types";
import { ArrowUpDown, Inbox, Mail } from "lucide-react";

interface EmailListProps {
  emails: Email[];
  isLoading: boolean;
  selectedId: string | null;
  onSelect: (id: string) => void;
  onSort?: (field: string) => void;
}

function SkeletonRow() {
  return (
    <div className="flex items-center gap-4 p-4 border-b border-slate-100">
      <div className="h-10 w-10 rounded-full bg-slate-200 animate-pulse" />
      <div className="flex-1 space-y-2">
        <div className="h-4 w-32 bg-slate-200 animate-pulse rounded" />
        <div className="h-3 w-64 bg-slate-200 animate-pulse rounded" />
      </div>
      <div className="h-6 w-20 bg-slate-200 animate-pulse rounded-full" />
      <div className="h-6 w-24 bg-slate-200 animate-pulse rounded-full" />
    </div>
  );
}

function EmptyState() {
  return (
    <div className="flex flex-col items-center justify-center py-16 text-center">
      <div className="w-16 h-16 rounded-2xl bg-blue-50 flex items-center justify-center mb-4">
        <Mail className="size-8 text-blue-400" />
      </div>
      <h3 className="text-lg font-semibold mb-2 text-slate-900">No emails found</h3>
      <p className="text-slate-500 text-sm max-w-sm">
        There are no emails matching your current filters. Try adjusting your
        search criteria or sync new emails.
      </p>
    </div>
  );
}

const tableHeaders = [
  { key: "sender", label: "Sender", width: "w-48" },
  { key: "subject", label: "Subject", width: "flex-1" },
  { key: "classification", label: "Type", width: "w-28" },
  { key: "status", label: "Status", width: "w-32" },
  { key: "received_at", label: "Date", width: "w-32" },
];

export function EmailList({
  emails,
  isLoading,
  selectedId,
  onSelect,
  onSort,
}: EmailListProps) {
  if (isLoading) {
    return (
      <div className="divide-y divide-slate-100">
        {Array.from({ length: 5 }).map((_, i) => (
          <SkeletonRow key={i} />
        ))}
      </div>
    );
  }

  if (emails.length === 0) {
    return <EmptyState />;
  }

  return (
    <div>
      {/* Table Header */}
      <div className="flex items-center gap-4 px-4 py-3 bg-slate-50/80 border-b border-slate-100 text-xs font-medium text-slate-500 uppercase tracking-wide">
        {tableHeaders.map((header) => (
          <div key={header.key} className={header.width}>
            {onSort ? (
              <button
                onClick={() => onSort(header.key)}
                className="flex items-center gap-1 hover:text-slate-700 transition-colors"
              >
                {header.label}
                <ArrowUpDown className="size-3" />
              </button>
            ) : (
              header.label
            )}
          </div>
        ))}
      </div>

      {/* Email List */}
      <motion.div
        initial="hidden"
        animate="visible"
        variants={{
          hidden: { opacity: 0 },
          visible: {
            opacity: 1,
            transition: { staggerChildren: 0.02 },
          },
        }}
        className="divide-y divide-slate-100"
      >
        {emails.map((email) => (
          <motion.div
            key={email.id}
            variants={{
              hidden: { opacity: 0, y: 10 },
              visible: { opacity: 1, y: 0 },
            }}
          >
            <EmailCard
              email={email}
              isSelected={selectedId === email.id}
              onClick={() => onSelect(email.id)}
            />
          </motion.div>
        ))}
      </motion.div>
    </div>
  );
}
