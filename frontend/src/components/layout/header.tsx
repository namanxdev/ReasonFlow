"use client";

import { usePathname } from "next/navigation";
import { ChevronRight } from "lucide-react";

const ROUTE_TITLES: Record<string, string> = {
  "/inbox": "Inbox",
  "/drafts": "Draft Review",
  "/metrics": "Metrics",
  "/traces": "Traces",
};

interface Breadcrumb {
  label: string;
  href?: string;
}

function getBreadcrumbs(pathname: string): Breadcrumb[] {
  // Handle trace detail pages
  if (pathname.startsWith("/traces/") && pathname !== "/traces") {
    return [
      { label: "Traces", href: "/traces" },
      { label: "Trace Detail" },
    ];
  }

  // For regular routes, just return the title
  const title = ROUTE_TITLES[pathname];
  if (title) {
    return [{ label: title }];
  }

  // Default fallback
  return [{ label: "ReasonFlow" }];
}

export function Header() {
  const pathname = usePathname();
  const breadcrumbs = getBreadcrumbs(pathname);

  return (
    <header className="flex h-14 items-center border-b bg-background px-6">
      <nav aria-label="Breadcrumb">
        <ol className="flex items-center gap-2">
          {breadcrumbs.map((crumb, index) => {
            const isLast = index === breadcrumbs.length - 1;

            return (
              <li key={index} className="flex items-center gap-2">
                {index > 0 && (
                  <ChevronRight
                    className="size-4 text-muted-foreground"
                    aria-hidden="true"
                  />
                )}
                {crumb.href && !isLast ? (
                  <a
                    href={crumb.href}
                    className="text-sm font-medium text-muted-foreground hover:text-foreground transition-colors"
                  >
                    {crumb.label}
                  </a>
                ) : (
                  <span
                    className={
                      isLast
                        ? "text-lg font-semibold text-foreground"
                        : "text-sm font-medium text-muted-foreground"
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
    </header>
  );
}
