"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { toast } from "sonner";
import { TopNav } from "./top-nav";
import { useSyncEmails } from "@/hooks/use-emails";

interface AppShellTopNavProps {
  children: React.ReactNode;
}

function getUserEmailFromToken(): string | null {
  if (typeof window === "undefined") return null;
  const token = localStorage.getItem("rf_access_token");
  if (!token) return null;
  try {
    const payload = JSON.parse(atob(token.split(".")[1]));
    return payload.sub || null;
  } catch {
    return null;
  }
}

export function AppShellTopNav({ children }: AppShellTopNavProps) {
  const router = useRouter();
  const syncMutation = useSyncEmails();
  const [userEmail, setUserEmail] = useState<string | null>(null);

  useEffect(() => {
    setUserEmail(getUserEmailFromToken());
  }, []);

  const handleSync = () => {
    syncMutation.mutate(undefined, {
      onSuccess: (data) => {
        toast.success(
          `Synced ${data.created} new email${data.created !== 1 ? "s" : ""} (${data.fetched} checked)`
        );
      },
      onError: (error) => {
        toast.error(
          `Failed to sync emails: ${
            error instanceof Error ? error.message : "Unknown error"
          }`
        );
      },
    });
  };

  const handleLogout = () => {
    if (typeof window !== "undefined") {
      localStorage.removeItem("rf_access_token");
      router.push("/login");
    }
  };

  return (
    <div className="min-h-screen bg-page">
      {/* Background */}
      <div className="fixed inset-0 bg-dot-pattern opacity-[0.03]" />
      <div className="fixed inset-0 bg-aurora-pink opacity-30" />
      
      {/* Top Navigation */}
      <TopNav
        onSync={handleSync}
        isSyncing={syncMutation.isPending}
        userEmail={userEmail || undefined}
        onLogout={handleLogout}
      />

      {/* Main Content */}
      <main className="relative z-10 pt-24 pb-6 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto">
          {children}
        </div>
      </main>
    </div>
  );
}
