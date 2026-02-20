"use client";

import { ReactNode } from "react";
import { motion } from "framer-motion";

interface DashboardShellProps {
  children: ReactNode;
  className?: string;
}

export function DashboardShell({ children, className = "" }: DashboardShellProps) {
  return (
    <div className="relative min-h-screen">
      {/* Background */}
      <div className="fixed inset-0 bg-page" />
      <div className="fixed inset-0 bg-dot-pattern opacity-[0.03]" />
      <div className="fixed inset-0 bg-aurora-pink opacity-30" />
      
      {/* Content */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.5 }}
        className={`relative z-10 ${className}`}
      >
        {children}
      </motion.div>
    </div>
  );
}

// Page header component
interface PageHeaderProps {
  icon: ReactNode;
  iconColor?: string;
  title: string;
  subtitle: string;
  action?: ReactNode;
}

export function PageHeader({ icon, iconColor = "bg-primary/10", title, subtitle, action }: PageHeaderProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
      className="flex items-start justify-between"
    >
      <div className="flex items-center gap-4">
        <div className={`w-12 h-12 rounded-2xl ${iconColor} flex items-center justify-center shadow-sm`}>
          {icon}
        </div>
        <div>
          <h1 className="text-2xl font-semibold tracking-tight text-foreground">{title}</h1>
          <p className="text-sm text-muted-foreground mt-0.5">{subtitle}</p>
        </div>
      </div>
      {action && <div className="flex items-center gap-2">{action}</div>}
    </motion.div>
  );
}

// Stats card
interface StatCardProps {
  label: string;
  value: string | number;
  change?: string;
  changeType?: "positive" | "negative" | "neutral";
  icon: ReactNode;
  color: "pink" | "blue" | "green" | "amber" | "violet";
}

const colorClasses = {
  pink: "card-pink text-pink-600",
  blue: "card-blue text-blue-600",
  green: "card-green text-green-600",
  amber: "card-amber text-amber-600",
  violet: "card-violet text-violet-600",
};

export function StatCard({ label, value, change, changeType = "neutral", icon, color }: StatCardProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
      className={`glass-card rounded-2xl p-5 feature-card ${colorClasses[color]}`}
    >
      <div className="flex items-start justify-between">
        <div>
          <p className="text-sm font-medium text-muted-foreground">{label}</p>
          <p className="text-2xl font-semibold mt-1 text-foreground">{value}</p>
          {change && (
            <p className={`text-xs mt-1 ${
              changeType === "positive" ? "text-green-600" :
              changeType === "negative" ? "text-red-600" :
              "text-muted-foreground"
            }`}>
              {change}
            </p>
          )}
        </div>
        <div className="w-10 h-10 rounded-xl bg-white/80 flex items-center justify-center shadow-sm">
          {icon}
        </div>
      </div>
    </motion.div>
  );
}

// Section card
interface SectionCardProps {
  children: ReactNode;
  className?: string;
  gradientBorder?: boolean;
}

export function SectionCard({ children, className = "", gradientBorder = false }: SectionCardProps) {
  if (gradientBorder) {
    return (
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4 }}
        className={`gradient-border-card ${className}`}
      >
        <div className="relative bg-white rounded-2xl p-6">
          {children}
        </div>
      </motion.div>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
      className={`glass-card rounded-2xl ${className}`}
    >
      {children}
    </motion.div>
  );
}

// Container for staggered animations
interface StaggerContainerProps {
  children: ReactNode;
  className?: string;
  staggerDelay?: number;
}

export function StaggerContainer({ children, className = "", staggerDelay = 0.05 }: StaggerContainerProps) {
  return (
    <motion.div
      initial="hidden"
      animate="visible"
      variants={{
        hidden: { opacity: 0 },
        visible: {
          opacity: 1,
          transition: { staggerChildren: staggerDelay },
        },
      }}
      className={className}
    >
      {children}
    </motion.div>
  );
}

export function StaggerItem({ children, className = "" }: { children: ReactNode; className?: string }) {
  return (
    <motion.div
      variants={{
        hidden: { opacity: 0, y: 10 },
        visible: { opacity: 1, y: 0 },
      }}
      className={className}
    >
      {children}
    </motion.div>
  );
}
