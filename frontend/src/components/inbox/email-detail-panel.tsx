"use client";

import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetDescription,
} from "@/components/ui/sheet";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
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
} from "lucide-react";
import { cn } from "@/lib/utils";
import Link from "next/link";
import { toast } from "sonner";
import { useEffect } from "react";

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

export function EmailDetailPanel({
  emailId,
  open,
  onClose,
}: EmailDetailPanelProps) {
  const { data: email, isLoading, refetch } = useEmail(emailId || "");
  const processEmailMutation = useProcessEmail();

  // Poll for status updates when email is processing
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
      <SheetContent className="w-full sm:max-w-2xl overflow-y-auto">
        {isLoading ? (
          <div className="space-y-4">
            <SheetHeader>
              <SheetTitle className="sr-only">Loading email...</SheetTitle>
              <div className="h-6 w-3/4 bg-muted animate-pulse rounded" />
              <div className="h-4 w-1/2 bg-muted animate-pulse rounded" />
            </SheetHeader>
            <div className="space-y-2">
              <div className="h-4 w-full bg-muted animate-pulse rounded" />
              <div className="h-4 w-full bg-muted animate-pulse rounded" />
              <div className="h-4 w-2/3 bg-muted animate-pulse rounded" />
            </div>
          </div>
        ) : email ? (
          <div className="space-y-6">
            <SheetHeader>
              <SheetTitle className="text-xl">{email.subject}</SheetTitle>
              <SheetDescription className="sr-only">
                Email from {email.sender} received on {formatDate(email.received_at)}
              </SheetDescription>
              <div className="space-y-2 text-sm text-muted-foreground">
                <div>
                  <span className="font-medium">From:</span> {email.sender}
                </div>
                <div>
                  <span className="font-medium">Date:</span>{" "}
                  {formatDate(email.received_at)}
                </div>
              </div>
            </SheetHeader>

            <Separator />

            <div className="space-y-4">
              <div>
                <h3 className="text-sm font-medium mb-2">Classification</h3>
                <div className="flex items-center gap-3">
                  <ClassificationBadge classification={email.classification} />
                  {email.confidence !== null && (
                    <span className="text-sm text-muted-foreground">
                      {Math.round(email.confidence * 100)}% confidence
                    </span>
                  )}
                </div>
              </div>

              <div>
                <h3 className="text-sm font-medium mb-2">Status</h3>
                {(() => {
                  const statusConfig = STATUS_STYLES[email.status];
                  const StatusIcon =
                    STATUS_ICON_MAP[
                      statusConfig.icon as keyof typeof STATUS_ICON_MAP
                    ];
                  return (
                    <div className={cn("flex items-center gap-2 rounded-full px-3 py-1 text-xs font-medium w-fit", statusConfig.bg)}>
                      <StatusIcon
                        className={cn(
                          "size-3.5",
                          statusConfig.color,
                          email.status === "processing" && "animate-spin"
                        )}
                      />
                      <span className={cn("text-sm", statusConfig.color)}>{statusConfig.label}</span>
                    </div>
                  );
                })()}
              </div>
            </div>

            <Separator />

            <div>
              <h3 className="text-sm font-medium mb-3">Email Body</h3>
              <div className="bg-muted/30 rounded-md p-4 max-h-96 overflow-y-auto">
                <pre className="whitespace-pre-wrap text-sm font-sans">
                  {email.body}
                </pre>
              </div>
            </div>

            <Separator />

            <div className="space-y-3">
              <h3 className="text-sm font-medium">Actions</h3>
              <div className="flex flex-col gap-2">
                {email.status === "needs_review" && (
                  <Button asChild variant="default" className="w-full">
                    <Link href={`/drafts?emailId=${email.id}`}>
                      <FileText />
                      View Draft
                    </Link>
                  </Button>
                )}

                {email.status === "pending" && (
                  <Button
                    variant="default"
                    className="w-full"
                    onClick={handleProcessEmail}
                    disabled={processEmailMutation.isPending}
                  >
                    {processEmailMutation.isPending ? (
                      <Loader2 className="animate-spin" />
                    ) : (
                      <Activity />
                    )}
                    Process with Agent
                  </Button>
                )}

                {email.status !== "pending" && (
                  <Button asChild variant="outline" className="w-full">
                    <Link href="/traces">
                      <Activity />
                      View Trace
                    </Link>
                  </Button>
                )}
              </div>
            </div>
          </div>
        ) : (
          <div className="flex items-center justify-center h-full">
            <SheetHeader className="sr-only">
              <SheetTitle>Email not found</SheetTitle>
            </SheetHeader>
            <p className="text-muted-foreground">Email not found</p>
          </div>
        )}
      </SheetContent>
    </Sheet>
  );
}
