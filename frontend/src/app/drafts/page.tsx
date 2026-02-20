"use client";

import { useState, Suspense } from "react";
import { motion } from "framer-motion";
import { useSearchParams, useRouter } from "next/navigation";
import { AppShellTopNav } from "@/components/layout/app-shell-top-nav";
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
import { Loader2, Mail, AlertCircle, FileText, Edit3, Sparkles } from "lucide-react";
import { toast } from "sonner";
import type { Email } from "@/types";
import { cn } from "@/lib/utils";
import { PageHeader, SectionCard, StaggerContainer, StaggerItem } from "@/components/layout/dashboard-shell";

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
        "p-4 border-b cursor-pointer transition-all hover:bg-blue-50/50",
        isSelected && "bg-blue-50/80 border-l-4 border-l-blue-500"
      )}
    >
      <div className="space-y-2">
        <div className="flex items-start justify-between gap-2">
          <div className="flex-1 min-w-0">
            <h3 className="font-medium truncate text-sm">{email.subject}</h3>
            <p className="text-xs text-muted-foreground truncate">
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
        <div className="relative">
          <div className="absolute inset-0 bg-pink-500/20 blur-xl rounded-full" />
          <Loader2 className="relative size-8 animate-spin text-pink-500" />
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        className="flex items-center justify-center h-[50vh]"
      >
        <div className="text-center space-y-3">
          <div className="w-16 h-16 rounded-2xl bg-red-100 flex items-center justify-center mx-auto">
            <AlertCircle className="size-8 text-red-500" />
          </div>
          <h3 className="text-lg font-medium">Error Loading Drafts</h3>
          <p className="text-sm text-muted-foreground">
            {error instanceof Error ? error.message : "Unknown error"}
          </p>
        </div>
      </motion.div>
    );
  }

  if (!drafts || drafts.length === 0) {
    return (
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        className="flex items-center justify-center h-[50vh]"
      >
        <div className="text-center space-y-3">
          <div className="w-16 h-16 rounded-2xl bg-pink-100 flex items-center justify-center mx-auto">
            <Mail className="size-8 text-pink-500" />
          </div>
          <h3 className="text-lg font-medium">No Drafts to Review</h3>
          <p className="text-sm text-muted-foreground max-w-sm">
            All drafts have been reviewed or there are no pending drafts.
          </p>
        </div>
      </motion.div>
    );
  }

  if (!emailId || !selectedEmail) {
    return (
      <StaggerContainer className="space-y-6 max-w-5xl mx-auto">
        <StaggerItem>
          <PageHeader
            icon={<FileText className="w-6 h-6 text-pink-600" />}
            iconColor="bg-pink-500/10"
            title="Draft Review"
            subtitle="Review and approve AI-generated email drafts"
          />
        </StaggerItem>

        <StaggerItem>
          <SectionCard className="overflow-hidden">
            <div className="px-6 py-4 border-b bg-gradient-to-r from-pink-50/50 to-violet-50/50">
              <div className="flex items-center gap-2">
                <Sparkles className="w-4 h-4 text-pink-500" />
                <span className="text-sm font-medium">Pending Drafts</span>
                <span className="px-2 py-0.5 rounded-full bg-pink-100 text-pink-600 text-xs font-medium">
                  {drafts.length}
                </span>
              </div>
            </div>
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
          </SectionCard>
        </StaggerItem>
      </StaggerContainer>
    );
  }

  return (
    <StaggerContainer className="space-y-6 max-w-6xl mx-auto">
      <StaggerItem>
        <PageHeader
          icon={<Edit3 className="w-6 h-6 text-pink-600" />}
          iconColor="bg-pink-500/10"
          title="Review Draft"
          subtitle="Edit and approve the AI-generated response"
        />
      </StaggerItem>

      <StaggerItem>
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
      </StaggerItem>
    </StaggerContainer>
  );
}

export default function DraftsPage() {
  return (
    <AppShellTopNav>
      <Suspense
        fallback={
          <div className="flex items-center justify-center h-[50vh]">
            <div className="relative">
              <div className="absolute inset-0 bg-pink-500/20 blur-xl rounded-full" />
              <Loader2 className="relative size-8 animate-spin text-pink-500" />
            </div>
          </div>
        }
      >
        <DraftsContent />
      </Suspense>
    </AppShellTopNav>
  );
}
