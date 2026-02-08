"use client";

import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import type { Email } from "@/types";
import { Mail } from "lucide-react";

interface OriginalEmailProps {
  email: Email;
}

function formatDate(dateString: string): string {
  const date = new Date(dateString);
  return new Intl.DateTimeFormat("en-US", {
    month: "long",
    day: "numeric",
    year: "numeric",
    hour: "numeric",
    minute: "2-digit",
    hour12: true,
  }).format(date);
}

export function OriginalEmail({ email }: OriginalEmailProps) {
  return (
    <Card className="bg-muted/50">
      <CardHeader>
        <div className="flex items-center gap-2">
          <Mail className="size-5 text-muted-foreground" />
          <CardTitle className="text-lg">Original Email</CardTitle>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="space-y-2">
          <div className="text-sm text-muted-foreground">From</div>
          <div className="font-medium">{email.sender}</div>
        </div>
        <div className="space-y-2">
          <div className="text-sm text-muted-foreground">Date</div>
          <div className="text-sm">{formatDate(email.received_at)}</div>
        </div>
        <div className="space-y-2">
          <div className="text-sm text-muted-foreground">Subject</div>
          <div className="font-medium">{email.subject}</div>
        </div>
        <div className="space-y-2">
          <div className="text-sm text-muted-foreground">Message</div>
          <div className="whitespace-pre-wrap text-sm leading-relaxed rounded-md bg-background/80 p-4 border">
            {email.body}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
