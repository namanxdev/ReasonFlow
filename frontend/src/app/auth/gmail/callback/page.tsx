"use client";

import { useEffect, useState } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import { Loader2, CheckCircle, XCircle, Workflow } from "lucide-react";
import {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import api from "@/lib/api";

type CallbackStatus = "loading" | "success" | "error";

export default function GmailCallbackPage() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const [status, setStatus] = useState<CallbackStatus>("loading");
  const [connectedEmail, setConnectedEmail] = useState<string>("");
  const [errorMessage, setErrorMessage] = useState("");

  useEffect(() => {
    const code = searchParams.get("code");

    if (!code) {
      setStatus("error");
      setErrorMessage(
        "No authorization code received from Google. Please try again."
      );
      return;
    }

    const exchangeCode = async () => {
      try {
        const response = await api.post("/auth/gmail/callback", { code });
        setConnectedEmail(response.data.email || "");
        setStatus("success");

        // If the server returned a JWT (unauthenticated Gmail login flow),
        // store it so the user is logged in.
        if (response.data.access_token) {
          localStorage.setItem("rf_access_token", response.data.access_token);
        }
      } catch (err: any) {
        setStatus("error");
        setErrorMessage(
          err.response?.data?.detail ||
            err.response?.data?.message ||
            "Failed to connect Gmail account. Please try again."
        );
      }
    };

    exchangeCode();
  }, [searchParams]);

  return (
    <div className="flex min-h-screen items-center justify-center bg-background p-4">
      <Card className="w-full max-w-md">
        <CardHeader className="text-center">
          <div className="flex items-center justify-center gap-2 mb-2">
            <Workflow className="size-8 text-primary" />
            <CardTitle className="text-2xl">Gmail Connection</CardTitle>
          </div>
          <CardDescription>
            {status === "loading" && "Connecting your Gmail account..."}
            {status === "success" && "Gmail connected successfully!"}
            {status === "error" && "Connection failed"}
          </CardDescription>
        </CardHeader>

        <CardContent className="flex flex-col items-center gap-4">
          {status === "loading" && (
            <div className="flex flex-col items-center gap-3 py-6">
              <Loader2 className="size-12 animate-spin text-primary" />
              <p className="text-sm text-muted-foreground">
                Exchanging authorization code with Google...
              </p>
            </div>
          )}

          {status === "success" && (
            <div className="flex flex-col items-center gap-3 py-6">
              <CheckCircle className="size-12 text-green-500" />
              <div className="text-center space-y-1">
                <p className="text-sm font-medium">
                  Connected as {connectedEmail}
                </p>
                <p className="text-sm text-muted-foreground">
                  You can now sync and process your emails.
                </p>
              </div>
              <Button onClick={() => router.push("/inbox")} className="mt-2">
                Go to Inbox
              </Button>
            </div>
          )}

          {status === "error" && (
            <div className="flex flex-col items-center gap-3 py-6">
              <XCircle className="size-12 text-destructive" />
              <div className="text-center space-y-1">
                <p className="text-sm text-destructive">{errorMessage}</p>
              </div>
              <div className="flex gap-2 mt-2">
                <Button
                  variant="outline"
                  onClick={() => router.push("/login")}
                >
                  Back to Login
                </Button>
                <Button onClick={() => router.push("/inbox")}>
                  Go to Inbox
                </Button>
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
