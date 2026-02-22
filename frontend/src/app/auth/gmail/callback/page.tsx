"use client";

import { Suspense } from "react";
import { useEffect, useState } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { useReducedMotion } from "@/hooks/use-reduced-motion";
import { Loader2, XCircle, Sparkles } from "lucide-react";
import { Button } from "@/components/ui/button";
import api from "@/lib/api";

type CallbackStatus = "loading" | "success" | "error";

function GmailCallbackContent() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const [status, setStatus] = useState<CallbackStatus>("loading");
  const [errorMessage, setErrorMessage] = useState("");
  const reducedMotion = useReducedMotion();

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

        // If the server returned a JWT (unauthenticated Gmail login flow),
        // store it so the user is logged in.
        if (response.data.access_token) {
          localStorage.setItem("rf_access_token", response.data.access_token);
        }

        // Auto-redirect to inbox on success
        setStatus("success");
        setTimeout(() => {
          router.push("/inbox");
        }, 800);
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
  }, [searchParams, router]);

  return (
    <div className="relative min-h-screen flex items-center justify-center overflow-hidden">
      {/* Background Layers - Matching landing page style */}
      <div className="absolute inset-0 bg-mesh" />
      <div className="absolute inset-0 bg-dot-pattern opacity-50" />
      <div className="absolute inset-0 bg-aurora" />

      {/* Content */}
      {reducedMotion ? (
        <div className="relative text-center px-4">
          {status === "loading" && (
            <div className="flex flex-col items-center gap-4">
              <div className="relative">
                <div className="absolute inset-0 bg-primary/20 blur-xl rounded-full" />
                <div className="relative w-16 h-16 rounded-2xl bg-white/80 backdrop-blur-sm border border-border/50 shadow-xl flex items-center justify-center">
                  <Loader2 className="size-8 animate-spin text-primary" />
                </div>
              </div>
              <div className="space-y-1">
                <p className="text-lg font-medium">Connecting your account...</p>
                <p className="text-sm text-muted-foreground">
                  Exchanging authorization code with Google
                </p>
              </div>
            </div>
          )}

          {status === "success" && (
            <div className="flex flex-col items-center gap-4">
              <div className="relative">
                <div className="absolute inset-0 bg-green-500/20 blur-xl rounded-full" />
                <div className="relative w-16 h-16 rounded-2xl bg-white/80 backdrop-blur-sm border border-green-500/30 shadow-xl flex items-center justify-center">
                  <Sparkles className="size-8 text-green-500" />
                </div>
              </div>
              <div className="space-y-1">
                <p className="text-lg font-medium">Successfully connected!</p>
                <p className="text-sm text-muted-foreground">
                  Redirecting to your inbox...
                </p>
              </div>
            </div>
          )}

          {status === "error" && (
            <div className="flex flex-col items-center gap-4 max-w-md">
              <div className="relative">
                <div className="absolute inset-0 bg-destructive/20 blur-xl rounded-full" />
                <div className="relative w-16 h-16 rounded-2xl bg-white/80 backdrop-blur-sm border border-destructive/30 shadow-xl flex items-center justify-center">
                  <XCircle className="size-8 text-destructive" />
                </div>
              </div>
              <div className="space-y-1">
                <p className="text-lg font-medium">Connection failed</p>
                <p className="text-sm text-muted-foreground">{errorMessage}</p>
              </div>
              <div className="flex gap-2 mt-4">
                <Button
                  variant="outline"
                  onClick={() => router.push("/login")}
                >
                  Back to Login
                </Button>
                <Button onClick={() => router.push("/inbox")}>Go to Inbox</Button>
              </div>
            </div>
          )}
        </div>
      ) : (
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.3 }}
          className="relative text-center px-4"
        >
          {status === "loading" && (
            <div className="flex flex-col items-center gap-4">
              <div className="relative">
                <div className="absolute inset-0 bg-primary/20 blur-xl rounded-full" />
                <div className="relative w-16 h-16 rounded-2xl bg-white/80 backdrop-blur-sm border border-border/50 shadow-xl flex items-center justify-center">
                  <Loader2 className="size-8 animate-spin text-primary" />
                </div>
              </div>
              <div className="space-y-1">
                <p className="text-lg font-medium">Connecting your account...</p>
                <p className="text-sm text-muted-foreground">
                  Exchanging authorization code with Google
                </p>
              </div>
            </div>
          )}

          {status === "success" && (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className="flex flex-col items-center gap-4"
            >
              <div className="relative">
                <div className="absolute inset-0 bg-green-500/20 blur-xl rounded-full" />
                <div className="relative w-16 h-16 rounded-2xl bg-white/80 backdrop-blur-sm border border-green-500/30 shadow-xl flex items-center justify-center">
                  <Sparkles className="size-8 text-green-500" />
                </div>
              </div>
              <div className="space-y-1">
                <p className="text-lg font-medium">Successfully connected!</p>
                <p className="text-sm text-muted-foreground">
                  Redirecting to your inbox...
                </p>
              </div>
            </motion.div>
          )}

          {status === "error" && (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className="flex flex-col items-center gap-4 max-w-md"
            >
              <div className="relative">
                <div className="absolute inset-0 bg-destructive/20 blur-xl rounded-full" />
                <div className="relative w-16 h-16 rounded-2xl bg-white/80 backdrop-blur-sm border border-destructive/30 shadow-xl flex items-center justify-center">
                  <XCircle className="size-8 text-destructive" />
                </div>
              </div>
              <div className="space-y-1">
                <p className="text-lg font-medium">Connection failed</p>
                <p className="text-sm text-muted-foreground">{errorMessage}</p>
              </div>
              <div className="flex gap-2 mt-4">
                <Button
                  variant="outline"
                  onClick={() => router.push("/login")}
                >
                  Back to Login
                </Button>
                <Button onClick={() => router.push("/inbox")}>Go to Inbox</Button>
              </div>
            </motion.div>
          )}
        </motion.div>
      )}
    </div>
  );
}

export default function GmailCallbackPage() {
  return (
    <Suspense fallback={
      <div className="relative min-h-screen flex items-center justify-center overflow-hidden">
        <div className="absolute inset-0 bg-mesh" />
        <div className="absolute inset-0 bg-dot-pattern opacity-50" />
        <div className="absolute inset-0 bg-aurora" />
        <div className="flex flex-col items-center gap-4">
          <div className="relative">
            <div className="absolute inset-0 bg-primary/20 blur-xl rounded-full" />
            <div className="relative w-16 h-16 rounded-2xl bg-white/80 backdrop-blur-sm border border-border/50 shadow-xl flex items-center justify-center">
              <Loader2 className="size-8 animate-spin text-primary" />
            </div>
          </div>
          <div className="space-y-1">
            <p className="text-lg font-medium">Loading...</p>
          </div>
        </div>
      </div>
    }>
      <GmailCallbackContent />
    </Suspense>
  );
}
