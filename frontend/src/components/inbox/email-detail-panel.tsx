"use client";

import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetDescription,
} from "@/components/ui/sheet";
import { Button } from "@/components/ui/button";
import { ClassificationBadge } from "./classification-badge";
import { STATUS_STYLES } from "@/lib/constants";
import { useEmail, useProcessEmail } from "@/hooks/use-emails";
import {
  Circle,
  Loader2,
  AlertCircle,
  CheckCircle,
  CheckCheck,
  XCircle,
  FileText,
  Activity,
  Mail,
  Calendar,
  User,
  Sparkles,
  ArrowRight,
  Zap,
} from "lucide-react";
import { cn } from "@/lib/utils";
import Link from "next/link";
import { toast } from "sonner";
import { useEffect, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";

const STATUS_ICON_MAP = {
  Circle,
  Loader2,
  AlertCircle,
  CheckCircle,
  CheckCheck,
  XCircle,
} as const;

interface EmailDetailPanelProps {
  emailId: string | null;
  open: boolean;
  onClose: () => void;
}

function formatDate(dateString: string): string {
  const date = new Date(dateString);
  return date.toLocaleString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
    hour: "numeric",
    minute: "2-digit",
    hour12: true,
  });
}

function formatDateRelative(dateString: string): string {
  const date = new Date(dateString);
  const now = new Date();
  const diffInHours = (now.getTime() - date.getTime()) / (1000 * 60 * 60);
  
  if (diffInHours < 1) return "Just now";
  if (diffInHours < 24) return `${Math.floor(diffInHours)}h ago`;
  if (diffInHours < 48) return "Yesterday";
  return formatDate(dateString);
}

// Spotlight Card Component
function SpotlightCard({ 
  children, 
  className,
  spotlightColor = "rgba(99, 102, 241, 0.15)"
}: { 
  children: React.ReactNode; 
  className?: string;
  spotlightColor?: string;
}) {
  const [mousePosition, setMousePosition] = useState({ x: 0, y: 0 });
  const [isHovered, setIsHovered] = useState(false);

  const handleMouseMove = (e: React.MouseEvent<HTMLDivElement>) => {
    const rect = e.currentTarget.getBoundingClientRect();
    setMousePosition({
      x: e.clientX - rect.left,
      y: e.clientY - rect.top,
    });
  };

  return (
    <div
      className={cn(
        "relative overflow-hidden rounded-xl border bg-card",
        className
      )}
      onMouseMove={handleMouseMove}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
    >
      <motion.div
        className="pointer-events-none absolute -inset-px rounded-xl opacity-0 transition-opacity duration-300"
        style={{
          background: `radial-gradient(400px circle at ${mousePosition.x}px ${mousePosition.y}px, ${spotlightColor}, transparent 60%)`,
        }}
        animate={{ opacity: isHovered ? 1 : 0 }}
      />
      <div className="relative">{children}</div>
    </div>
  );
}

// Animated Border Card
function AnimatedBorderCard({
  children,
  className,
}: {
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <div className={cn("relative group", className)}>
      <div className="absolute -inset-[1px] bg-gradient-to-r from-indigo-500 via-purple-500 to-indigo-500 rounded-xl opacity-20 group-hover:opacity-40 transition-opacity duration-500 blur-[1px]" />
      <div className="relative bg-card rounded-xl border shadow-sm overflow-hidden">
        {children}
      </div>
    </div>
  );
}

export function EmailDetailPanel({
  emailId,
  open,
  onClose,
}: EmailDetailPanelProps) {
  const { data: email, isLoading, refetch } = useEmail(emailId || "");
  const processEmailMutation = useProcessEmail();

  useEffect(() => {
    if (email?.status !== "processing") return;
    const interval = setInterval(() => {
      refetch();
    }, 3000);
    return () => clearInterval(interval);
  }, [email?.status, refetch]);

  const handleProcessEmail = () => {
    if (!emailId) return;
    processEmailMutation.mutate(emailId, {
      onSuccess: () => {
        toast.success("Email processing started");
        refetch();
      },
      onError: (error) => {
        toast.error(
          `Failed to process email: ${
            error instanceof Error ? error.message : "Unknown error"
          }`
        );
      },
    });
  };

  if (!emailId) return null;

  return (
    <Sheet open={open} onOpenChange={(isOpen) => !isOpen && onClose()}>
      <SheetContent className="w-full sm:max-w-lg p-0 border-l border-border/50 bg-background overflow-hidden">
        <SheetTitle className="sr-only">
          {isLoading ? "Loading email" : email ? email.subject : "Email not found"}
        </SheetTitle>
        <AnimatePresence mode="wait">
          {isLoading ? (
            <motion.div
              key="loading"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="h-full flex flex-col"
            >
              <div className="p-6 space-y-6">
                <div className="space-y-3">
                  <div className="h-8 w-3/4 bg-muted rounded-lg animate-pulse" />
                  <div className="h-4 w-1/2 bg-muted rounded animate-pulse" />
                </div>
                <div className="space-y-3">
                  <div className="h-24 bg-muted rounded-xl animate-pulse" />
                  <div className="h-48 bg-muted rounded-xl animate-pulse" />
                </div>
              </div>
            </motion.div>
          ) : email ? (
            <motion.div
              key="content"
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.3, ease: [0.23, 1, 0.32, 1] }}
              className="flex flex-col h-full"
            >
              {/* Header */}
              <div className="flex-shrink-0 px-6 py-5 border-b border-border/50 bg-muted/30">
                <SheetHeader className="space-y-4">
                  <div className="flex items-start gap-3">
                    <div className="flex-shrink-0 w-10 h-10 rounded-xl bg-primary/10 flex items-center justify-center ring-1 ring-primary/20">
                      <Mail className="w-5 h-5 text-primary" />
                    </div>
                    <div className="flex-1 min-w-0 pt-0.5">
                      <div className="text-base font-semibold tracking-tight line-clamp-2">
                        {email.subject}
                      </div>
                    </div>
                  </div>
                  
                  {/* Meta Info */}
                  <div className="flex flex-col gap-2 text-sm">
                    <div className="flex items-center gap-2 text-muted-foreground">
                      <User className="w-3.5 h-3.5" />
                      <span className="truncate">{email.sender}</span>
                    </div>
                    <div className="flex items-center gap-2 text-muted-foreground">
                      <Calendar className="w-3.5 h-3.5" />
                      <span>{formatDate(email.received_at)}</span>
                      <span className="text-muted-foreground/60">•</span>
                      <span className="text-muted-foreground/60">{formatDateRelative(email.received_at)}</span>
                    </div>
                  </div>
                </SheetHeader>
              </div>

              {/* Scrollable Content */}
              <div className="flex-1 overflow-y-auto">
                <div className="p-6 space-y-5">
                  {/* AI Analysis Section */}
                  <AnimatedBorderCard>
                    <div className="p-4 space-y-4">
                      <div className="flex items-center gap-2">
                        <div className="w-6 h-6 rounded-lg bg-gradient-to-br from-indigo-500 to-purple-500 flex items-center justify-center">
                          <Sparkles className="w-3.5 h-3.5 text-white" />
                        </div>
                        <span className="text-sm font-semibold">AI Analysis</span>
                      </div>
                      
                      <div className="grid grid-cols-2 gap-4">
                        <div className="space-y-2">
                          <span className="text-xs text-muted-foreground uppercase tracking-wider">Classification</span>
                          <ClassificationBadge classification={email.classification} size="md" />
                          {email.confidence !== null && (
                            <div className="flex items-center gap-2">
                              <div className="flex-1 h-1 bg-muted rounded-full overflow-hidden">
                                <motion.div 
                                  className="h-full bg-gradient-to-r from-indigo-500 to-purple-500 rounded-full"
                                  initial={{ width: 0 }}
                                  animate={{ width: `${Math.round(email.confidence * 100)}%` }}
                                  transition={{ duration: 0.8, ease: "easeOut" }}
                                />
                              </div>
                              <span className="text-xs font-medium tabular-nums">
                                {Math.round(email.confidence * 100)}%
                              </span>
                            </div>
                          )}
                        </div>

                        <div className="space-y-2">
                          <span className="text-xs text-muted-foreground uppercase tracking-wider">Status</span>
                          <StatusBadge status={email.status} />
                        </div>
                      </div>
                    </div>
                  </AnimatedBorderCard>

                  {/* Email Body */}
                  <SpotlightCard className="bg-card" spotlightColor="rgba(99, 102, 241, 0.08)">
                    <div className="p-4 space-y-3">
                      <div className="flex items-center gap-2 text-sm font-medium text-muted-foreground">
                        <FileText className="w-4 h-4" />
                        Content
                      </div>
                      <div className="text-sm leading-relaxed text-foreground/90 whitespace-pre-wrap font-mono">
                        {email.body}
                      </div>
                    </div>
                  </SpotlightCard>
                </div>
              </div>

              {/* Footer Actions */}
              <div className="flex-shrink-0 px-6 py-4 border-t border-border/50 bg-muted/30">
                <div className="space-y-2">
                  <span className="text-xs text-muted-foreground uppercase tracking-wider">Actions</span>
                  <div className="flex flex-col gap-2">
                    {email.status === "needs_review" && (
                      <Button 
                        asChild 
                        className="w-full h-10 bg-primary hover:bg-primary/90 text-primary-foreground font-medium"
                      >
                        <Link href={`/drafts?emailId=${email.id}`}>
                          <FileText className="w-4 h-4 mr-2" />
                          View Draft
                          <ArrowRight className="w-4 h-4 ml-auto opacity-50" />
                        </Link>
                      </Button>
                    )}

                    {email.status === "pending" && (
                      <Button
                        className="w-full h-10 bg-primary hover:bg-primary/90 text-primary-foreground font-medium"
                        onClick={handleProcessEmail}
                        disabled={processEmailMutation.isPending}
                      >
                        {processEmailMutation.isPending ? (
                          <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                        ) : (
                          <Zap className="w-4 h-4 mr-2" />
                        )}
                        Process with Agent
                      </Button>
                    )}

                    {email.status !== "pending" && (
                      <Button 
                        asChild 
                        variant="outline"
                        className="w-full h-10"
                      >
                        <Link href="/traces">
                          <Activity className="w-4 h-4 mr-2" />
                          View Trace
                          <ArrowRight className="w-4 h-4 ml-auto opacity-50" />
                        </Link>
                      </Button>
                    )}
                  </div>
                </div>
              </div>
            </motion.div>
          ) : (
            <motion.div
              key="not-found"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="flex items-center justify-center h-full"
            >
              <div className="text-center space-y-3">
                <div className="w-12 h-12 rounded-xl bg-muted flex items-center justify-center mx-auto">
                  <Mail className="w-6 h-6 text-muted-foreground" />
                </div>
                <p className="text-muted-foreground">Email not found</p>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </SheetContent>
    </Sheet>
  );
}

// Status Badge Component
function StatusBadge({ status }: { status: string }) {
  const statusConfig = STATUS_STYLES[status as keyof typeof STATUS_STYLES];
  const StatusIcon = STATUS_ICON_MAP[statusConfig.icon as keyof typeof STATUS_ICON_MAP];

  const variants: Record<string, { bg: string; dot: string }> = {
    pending: { bg: "bg-slate-500/10 text-slate-600", dot: "bg-slate-500" },
    processing: { bg: "bg-blue-500/10 text-blue-600", dot: "bg-blue-500" },
    drafted: { bg: "bg-orange-500/10 text-orange-600", dot: "bg-orange-500" },
    needs_review: { bg: "bg-yellow-500/10 text-yellow-600", dot: "bg-yellow-500" },
    approved: { bg: "bg-green-500/10 text-green-600", dot: "bg-green-500" },
    sent: { bg: "bg-blue-600/10 text-blue-700", dot: "bg-blue-600" },
    rejected: { bg: "bg-red-500/10 text-red-600", dot: "bg-red-500" },
  };

  const variant = variants[status] || variants.pending;

  return (
    <div className={cn(
      "inline-flex items-center gap-2 rounded-lg px-2.5 py-1.5 text-xs font-medium",
      variant.bg
    )}>
      <span className={cn("w-1.5 h-1.5 rounded-full", variant.dot, status === "processing" && "animate-pulse")} />
      <StatusIcon className={cn("w-3.5 h-3.5", status === "processing" && "animate-spin")} />
      <span>{statusConfig.label}</span>
    </div>
  );
}
