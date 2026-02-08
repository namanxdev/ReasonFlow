"use client";

import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Textarea } from "@/components/ui/textarea";
import { FileEdit, FileText } from "lucide-react";
import { cn } from "@/lib/utils";

interface DraftEditorProps {
  draftContent: string;
  isEditing: boolean;
  onChange: (value: string) => void;
}

export function DraftEditor({
  draftContent,
  isEditing,
  onChange,
}: DraftEditorProps) {
  return (
    <Card>
      <CardHeader>
        <div className="flex items-center gap-2">
          {isEditing ? (
            <FileEdit className="size-5 text-primary" />
          ) : (
            <FileText className="size-5 text-muted-foreground" />
          )}
          <CardTitle className="text-lg">
            {isEditing ? "Edit Draft Response" : "Draft Response"}
          </CardTitle>
        </div>
      </CardHeader>
      <CardContent>
        <div
          className={cn(
            "transition-all duration-200 ease-in-out",
            isEditing ? "opacity-100" : "opacity-100"
          )}
        >
          {isEditing ? (
            <Textarea
              value={draftContent}
              onChange={(e) => onChange(e.target.value)}
              className="min-h-[300px] font-mono text-sm resize-y"
              placeholder="Edit your draft response..."
              aria-label="Draft response editor"
            />
          ) : (
            <div className="whitespace-pre-wrap text-sm leading-relaxed rounded-md bg-muted/30 p-4 border min-h-[300px]">
              {draftContent}
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
