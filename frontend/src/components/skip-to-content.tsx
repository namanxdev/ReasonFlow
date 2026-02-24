"use client";

import { cn } from "@/lib/utils";

/**
 * Skip to content link for accessibility (A11Y-NEW-1 fix)
 * 
 * This component provides a "skip to main content" link that is visually hidden
 * but becomes visible when focused. This allows keyboard users to skip
 * repetitive navigation and jump directly to the main content.
 * 
 * Usage:
 *   <SkipToContent contentId="main-content" />
 *   ...
 *   <main id="main-content">
 *     <!-- Main content here -->
 *   </main>
 */
interface SkipToContentProps {
  /** The ID of the main content element to skip to */
  contentId?: string;
  /** Additional CSS classes */
  className?: string;
}

export function SkipToContent({ 
  contentId = "main-content",
  className 
}: SkipToContentProps) {
  return (
    <a
      href={`#${contentId}`}
      className={cn(
        "sr-only focus:not-sr-only focus:absolute focus:z-50",
        "focus:top-4 focus:left-4",
        "focus:px-4 focus:py-2",
        "focus:bg-indigo-600 focus:text-white",
        "focus:rounded-md focus:shadow-lg",
        "focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-600",
        "text-sm font-medium",
        className
      )}
    >
      Skip to main content
    </a>
  );
}

export default SkipToContent;
