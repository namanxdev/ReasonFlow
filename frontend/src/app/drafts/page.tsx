"use client";

import { useState, Suspense } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import { AppShell } from "@/components/layout/app-shell";
import { OriginalEmail } from "@/components/draft-review/original-email";
import { DraftEditor } from "@/components/draft-review/draft-editor";
import { ConfidenceIndicator } from "@/components/draft-review/confidence-indicator";
import { ApprovalButtons } from "@/components/draft-review/approval-buttons";
import { ClassificationBadge } from "@/components/inbox/classification-badge";
import {
  useDrafts,
  useEditDraft,
  useApproveDraft,
} from "@/hooks/use-drafts";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Loader2, Mail, AlertCircle } from "lucide-react";
import { toast } from "sonner";
import type { Email } from "@/types";
import { cn } from "@/lib/utils";

function getRelativeTime(dateString: string): string {
  const now = new Date();
  const date = new Date(dateString);
  const diffInMs = now.getTime() - date.getTime();
  const diffInMinutes = Math.floor(diffInMs / 60000);
  const diffInHours = Math.floor(diffInMinutes / 60);
  const diffInDays = Math.floor(diffInHours / 24);

  if (diffInMinutes < 1) return "Just now";
  if (diffInMinutes < 60) return `${diffInMinutes}m ago`;
  if (diffInHours < 24) return `${diffInHours}h ago`;
  if (diffInDays < 7) return `${diffInDays}d ago`;
  if (diffInDays < 30) return `${Math.floor(diffInDays / 7)}w ago`;
  return `${Math.floor(diffInDays / 30)}mo ago`;
}

function ConfidenceBar({ confidence }: { confidence: number | null }) {
  if (confidence === null) return null;

  const percentage = Math.round(confidence * 100);
  let color = "bg-red-500";
  if (confidence > 0.9) color = "bg-green-500";
  else if (confidence >= 0.7) color = "bg-amber-500";

  return (
    <div className="flex items-center gap-2">
      <div className="relative h-1.5 w-16 overflow-hidden rounded-full bg-muted">
        <div
          className={cn("h-full rounded-full", color)}
          style={{ width: `${percentage}%` }}
        />
      </div>
      <span className="text-xs text-muted-foreground">{percentage}%</span>
    </div>
  );
}

function DraftListItem({
  email,
  isSelected,
  onClick,
}: {
  email: Email;
  isSelected: boolean;
  onClick: () => void;
}) {
  return (
    <div
      onClick={onClick}
      className={cn(
        "p-4 border-b cursor-pointer transition-colors hover:bg-accent/50",
        isSelected && "bg-accent border-l-4 border-l-primary"
      )}
    >
      <div className="space-y-2">
        <div className="flex items-start justify-between gap-2">
          <div className="flex-1 min-w-0">
            <h3 className="font-medium truncate">{email.subject}</h3>
            <p className="text-sm text-muted-foreground truncate">
              {email.sender}
            </p>
          </div>
          <span className="text-xs text-muted-foreground whitespace-nowrap">
            {getRelativeTime(email.received_at)}
          </span>
        </div>
        <div className="flex items-center gap-2 flex-wrap">
          <ClassificationBadge classification={email.classification} />
          <ConfidenceBar confidence={email.confidence} />
        </div>
      </div>
    </div>
  );
}

function DraftsContent() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const emailId = searchParams.get("emailId");

  const { data: drafts, isLoading, error } = useDrafts();
  const [isEditing, setIsEditing] = useState(false);
  const [editedContent, setEditedContent] = useState("");

  const editMutation = useEditDraft();
  const approveMutation = useApproveDraft();

  const selectedEmail = drafts?.find((draft) => draft.id === emailId);

  const handleSelectDraft = (id: string) => {
    router.push(`/drafts?emailId=${id}`);
    setIsEditing(false);
  };

  const handleToggleEdit = () => {
    if (!isEditing && selectedEmail?.draft_response) {
      setEditedContent(selectedEmail.draft_response);
    }
    setIsEditing(!isEditing);
  };

  const handleSaveAndApprove = () => {
    if (!selectedEmail) return;

    editMutation.mutate(
      {
        id: selectedEmail.id,
        draft_response: editedContent,
      },
      {
        onSuccess: () => {
          approveMutation.mutate(selectedEmail.id, {
            onSuccess: () => {
              toast.success("Draft updated and approved successfully");
              router.push("/drafts");
              setIsEditing(false);
            },
            onError: (error) => {
              toast.error(
                `Failed to approve draft: ${
                  error instanceof Error ? error.message : "Unknown error"
                }`
              );
            },
          });
        },
        onError: (error) => {
          toast.error(
            `Failed to update draft: ${
              error instanceof Error ? error.message : "Unknown error"
            }`
          );
        },
      }
    );
  };

  const handleAction = () => {
    router.push("/drafts");
    setIsEditing(false);
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-[50vh]">
        <Loader2 className="size-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-[50vh]">
        <div className="text-center space-y-2">
          <AlertCircle className="size-12 mx-auto text-destructive" />
          <h3 className="text-lg font-semibold">Error Loading Drafts</h3>
          <p className="text-sm text-muted-foreground">
            {error instanceof Error ? error.message : "Unknown error"}
          </p>
        </div>
      </div>
    );
  }

  if (!drafts || drafts.length === 0) {
    return (
      <div className="flex items-center justify-center h-[50vh]">
        <div className="text-center space-y-2">
          <Mail className="size-12 mx-auto text-muted-foreground" />
          <h3 className="text-lg font-semibold">No Drafts to Review</h3>
          <p className="text-sm text-muted-foreground">
            All drafts have been reviewed or there are no pending drafts.
          </p>
        </div>
      </div>
    );
  }

  if (!emailId || !selectedEmail) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold">Draft Review</h1>
          <p className="text-muted-foreground">
            Review and approve AI-generated email drafts
          </p>
        </div>
        <Card>
          <CardHeader>
            <CardTitle>Pending Drafts ({drafts.length})</CardTitle>
          </CardHeader>
          <CardContent className="p-0">
            <div className="divide-y">
              {drafts.map((draft) => (
                <DraftListItem
                  key={draft.id}
                  email={draft}
                  isSelected={false}
                  onClick={() => handleSelectDraft(draft.id)}
                />
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Draft Review</h1>
        <p className="text-muted-foreground">
          Review and approve AI-generated email draft
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="space-y-6">
          <OriginalEmail email={selectedEmail} />
        </div>

        <div className="space-y-6">
          <DraftEditor
            draftContent={
              isEditing ? editedContent : selectedEmail.draft_response || ""
            }
            isEditing={isEditing}
            onChange={setEditedContent}
          />

          {selectedEmail.confidence !== null && (
            <ConfidenceIndicator confidence={selectedEmail.confidence} />
          )}

          <ApprovalButtons
            emailId={selectedEmail.id}
            onAction={isEditing ? handleSaveAndApprove : handleAction}
            isEditing={isEditing}
            onToggleEdit={handleToggleEdit}
          />
        </div>
      </div>
    </div>
  );
}

export default function DraftsPage() {
  return (
    <AppShell>
      <Suspense
        fallback={
          <div className="flex items-center justify-center h-[50vh]">
            <Loader2 className="size-8 animate-spin text-muted-foreground" />
          </div>
        }
      >
        <DraftsContent />
      </Suspense>
    </AppShell>
  );
}
