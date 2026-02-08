"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { useApproveDraft, useRejectDraft } from "@/hooks/use-drafts";
import { toast } from "sonner";
import { CheckCircle2, Edit3, XCircle, Send, X, Loader2 } from "lucide-react";

interface ApprovalButtonsProps {
  emailId: string;
  onAction: () => void;
  isEditing: boolean;
  onToggleEdit: () => void;
}

export function ApprovalButtons({
  emailId,
  onAction,
  isEditing,
  onToggleEdit,
}: ApprovalButtonsProps) {
  const [showApproveDialog, setShowApproveDialog] = useState(false);
  const [showRejectDialog, setShowRejectDialog] = useState(false);

  const approveMutation = useApproveDraft();
  const rejectMutation = useRejectDraft();

  const handleApprove = () => {
    approveMutation.mutate(emailId, {
      onSuccess: () => {
        toast.success("Draft approved successfully");
        setShowApproveDialog(false);
        onAction();
      },
      onError: (error) => {
        toast.error(
          `Failed to approve draft: ${
            error instanceof Error ? error.message : "Unknown error"
          }`
        );
      },
    });
  };

  const handleReject = () => {
    rejectMutation.mutate(emailId, {
      onSuccess: () => {
        toast.success("Draft rejected successfully");
        setShowRejectDialog(false);
        onAction();
      },
      onError: (error) => {
        toast.error(
          `Failed to reject draft: ${
            error instanceof Error ? error.message : "Unknown error"
          }`
        );
      },
    });
  };

  if (isEditing) {
    return (
      <div className="flex items-center gap-3">
        <Button
          onClick={onAction}
          size="lg"
          className="flex-1"
          disabled={approveMutation.isPending}
        >
          {approveMutation.isPending ? (
            <Loader2 className="animate-spin" />
          ) : (
            <Send />
          )}
          Send Edited
        </Button>
        <Button
          onClick={onToggleEdit}
          variant="ghost"
          size="lg"
          disabled={approveMutation.isPending}
        >
          <X />
          Cancel
        </Button>
      </div>
    );
  }

  return (
    <>
      <div className="flex items-center gap-3">
        <Button
          onClick={() => setShowApproveDialog(true)}
          size="lg"
          className="flex-1"
          disabled={approveMutation.isPending || rejectMutation.isPending}
        >
          <CheckCircle2 />
          Approve
        </Button>
        <Button
          onClick={onToggleEdit}
          variant="outline"
          size="lg"
          disabled={approveMutation.isPending || rejectMutation.isPending}
        >
          <Edit3 />
          Edit
        </Button>
        <Button
          onClick={() => setShowRejectDialog(true)}
          variant="destructive"
          size="lg"
          disabled={approveMutation.isPending || rejectMutation.isPending}
        >
          <XCircle />
          Reject
        </Button>
      </div>

      <Dialog open={showApproveDialog} onOpenChange={setShowApproveDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Approve Draft</DialogTitle>
            <DialogDescription>
              Are you sure you want to approve this draft? The email will be
              sent to the recipient.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setShowApproveDialog(false)}
              disabled={approveMutation.isPending}
            >
              Cancel
            </Button>
            <Button onClick={handleApprove} disabled={approveMutation.isPending}>
              {approveMutation.isPending ? (
                <Loader2 className="animate-spin" />
              ) : (
                <CheckCircle2 />
              )}
              Confirm Approval
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <Dialog open={showRejectDialog} onOpenChange={setShowRejectDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Reject Draft</DialogTitle>
            <DialogDescription>
              Are you sure you want to reject this draft? This action cannot be
              undone and the draft will be discarded.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setShowRejectDialog(false)}
              disabled={rejectMutation.isPending}
            >
              Cancel
            </Button>
            <Button
              variant="destructive"
              onClick={handleReject}
              disabled={rejectMutation.isPending}
            >
              {rejectMutation.isPending ? (
                <Loader2 className="animate-spin" />
              ) : (
                <XCircle />
              )}
              Confirm Rejection
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
}
