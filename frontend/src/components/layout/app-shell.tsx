"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { toast } from "sonner";
import { Sidebar } from "./sidebar";
import { Header } from "./header";
import { useSyncEmails } from "@/hooks/use-emails";

interface AppShellProps {
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

export function AppShell({ children }: AppShellProps) {
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
    <div className="flex h-screen overflow-hidden">
      <Sidebar
        onSync={handleSync}
        isSyncing={syncMutation.isPending}
        userEmail={userEmail || undefined}
        onLogout={handleLogout}
      />
      <div className="flex flex-1 flex-col overflow-hidden">
        <Header />
        <main className="flex-1 overflow-y-auto p-6 bg-background">
          {children}
        </main>
      </div>
    </div>
  );
}
