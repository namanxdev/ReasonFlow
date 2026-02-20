"use client";

import Link from "next/link";
import { motion } from "framer-motion";

export default function AuthLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="relative min-h-screen flex items-center justify-center overflow-hidden">
      {/* Background Layers - Matching landing page style */}
      <div className="absolute inset-0 bg-mesh" />
      <div className="absolute inset-0 bg-dot-pattern opacity-50" />
      <div className="absolute inset-0 bg-aurora" />

      {/* Content */}
      <div className="relative w-full max-w-md px-4 sm:px-6">
        {/* Logo */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          className="flex items-center justify-center gap-2 mb-8"
        >
          <Link href="/" className="flex items-center gap-2">
            <div className="w-10 h-10 rounded-xl bg-foreground flex items-center justify-center shadow-lg">
              <span className="text-background font-bold text-lg">R</span>
            </div>
            <span className="font-medium text-xl tracking-tight">ReasonFlow</span>
          </Link>
        </motion.div>

        {/* Auth Card */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.1 }}
        >
          {children}
        </motion.div>

        {/* Footer */}
        <motion.p
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.5, delay: 0.3 }}
          className="mt-8 text-center text-sm text-muted-foreground"
        >
          By continuing, you agree to our{" "}
          <Link href="#" className="underline hover:text-foreground transition-colors">
            Terms of Service
          </Link>{" "}
          and{" "}
          <Link href="#" className="underline hover:text-foreground transition-colors">
            Privacy Policy
          </Link>
        </motion.p>
      </div>
    </div>
  );
}
