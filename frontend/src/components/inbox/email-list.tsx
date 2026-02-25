"use client";

import { motion, AnimatePresence } from "framer-motion";
import { EmailCard } from "./email-card";
import type { Email } from "@/types";
import { ArrowUpDown, Inbox, Mail } from "lucide-react";
import { useReducedMotion } from "@/hooks/use-reduced-motion";

interface EmailListProps {
  emails: Email[];
  isLoading: boolean;
  selectedId: string | null;
  onSelect: (id: string) => void;
  onSort?: (field: string) => void;
  currentPage?: number;
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
  currentPage,
}: EmailListProps) {
  const reducedMotion = useReducedMotion();

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

  // Render without animations if reduced motion is preferred
  if (reducedMotion) {
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

        {/* Email List - no animation */}
        <div className="divide-y divide-slate-100">
          {emails.map((email) => (
            <div key={email.id}>
              <EmailCard
                email={email}
                isSelected={selectedId === email.id}
                onClick={() => onSelect(email.id)}
              />
            </div>
          ))}
        </div>
      </div>
    );
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
      <div className="divide-y divide-slate-100">
        <AnimatePresence mode="popLayout">
          {emails.map((email, index) => (
            <motion.div
              key={email.id}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.15, delay: index * 0.02 }}
            >
              <EmailCard
                email={email}
                isSelected={selectedId === email.id}
                onClick={() => onSelect(email.id)}
              />
            </motion.div>
          ))}
        </AnimatePresence>
      </div>
    </div>
  );
}
