"use client";

import { useRouter } from "next/navigation";
import { toast } from "sonner";
import { Sidebar } from "./sidebar";
import { Header } from "./header";
import { useSyncEmails } from "@/hooks/use-emails";

interface AppShellProps {
  children: React.ReactNode;
  userEmail?: string;
}

export function AppShell({ children, userEmail }: AppShellProps) {
  const router = useRouter();
  const syncMutation = useSyncEmails();

  const handleSync = () => {
    syncMutation.mutate(undefined, {
      onSuccess: (data) => {
        toast.success(
          `Successfully synced ${data.new_count} new email${
            data.new_count !== 1 ? "s" : ""
          }`
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
        userEmail={userEmail}
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
