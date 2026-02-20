"use client";

import { usePathname } from "next/navigation";
import { ChevronRight, Sparkles } from "lucide-react";

const ROUTE_TITLES: Record<string, string> = {
  "/inbox": "Inbox",
  "/drafts": "Draft Review",
  "/calendar": "Calendar",
  "/crm": "CRM Contacts",
  "/metrics": "Metrics",
  "/traces": "Traces",
};

interface Breadcrumb {
  label: string;
  href?: string;
}

function getBreadcrumbs(pathname: string): Breadcrumb[] {
  if (pathname.startsWith("/traces/") && pathname !== "/traces") {
    return [
      { label: "Traces", href: "/traces" },
      { label: "Trace Detail" },
    ];
  }

  const title = ROUTE_TITLES[pathname];
  if (title) {
    return [{ label: title }];
  }

  return [{ label: "ReasonFlow" }];
}

export function Header() {
  const pathname = usePathname();
  const breadcrumbs = getBreadcrumbs(pathname);

  return (
    <header className="flex h-16 items-center border-b border-slate-100 bg-white/50 backdrop-blur-sm px-6">
      <nav aria-label="Breadcrumb" className="flex-1">
        <ol className="flex items-center gap-2">
          {breadcrumbs.map((crumb, index) => {
            const isLast = index === breadcrumbs.length - 1;

            return (
              <li key={index} className="flex items-center gap-2">
                {index > 0 && (
                  <ChevronRight
                    className="size-4 text-slate-300"
                    aria-hidden="true"
                  />
                )}
                {crumb.href && !isLast ? (
                  <a
                    href={crumb.href}
                    className="text-sm font-medium text-slate-500 hover:text-slate-700 transition-colors"
                  >
                    {crumb.label}
                  </a>
                ) : (
                  <span
                    className={
                      isLast
                        ? "text-lg font-semibold text-slate-900"
                        : "text-sm font-medium text-slate-500"
                    }
                    aria-current={isLast ? "page" : undefined}
                  >
                    {crumb.label}
                  </span>
                )}
              </li>
            );
          })}
        </ol>
      </nav>
      
      {/* AI Badge */}
      <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-gradient-to-r from-blue-500/10 to-violet-500/10 border border-blue-200/50">
        <Sparkles className="size-3.5 text-blue-600" />
        <span className="text-xs font-medium text-blue-700">AI Powered</span>
      </div>
    </header>
  );
}
