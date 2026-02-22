"use client";

import { motion } from "framer-motion";
import { Mail, Brain, UserCheck, Send, ArrowUpRight } from "lucide-react";
import { Button } from "@/components/ui/button";
import Link from "next/link";
import { useReducedMotion } from "@/hooks/use-reduced-motion";

const steps = [
  {
    number: "01",
    title: "Connect Your Inbox",
    description: "Link your Gmail account with OAuth. Secure, encrypted, and revocable anytime.",
    icon: Mail,
    color: "from-blue-500 to-cyan-500",
    bgColor: "bg-blue-500/10",
    iconColor: "text-blue-600",
    borderColor: "border-blue-200",
  },
  {
    number: "02",
    title: "AI Analyzes & Classifies",
    description: "Gemini-powered agent reads and classifies emails by intent with 95%+ accuracy.",
    icon: Brain,
    color: "from-violet-500 to-purple-500",
    bgColor: "bg-violet-500/10",
    iconColor: "text-violet-600",
    borderColor: "border-violet-200",
  },
  {
    number: "03",
    title: "Review & Approve",
    description: "High-confidence emails auto-send. Others wait for your quick approval.",
    icon: UserCheck,
    color: "from-pink-500 to-rose-500",
    bgColor: "bg-pink-500/10",
    iconColor: "text-pink-600",
    borderColor: "border-pink-200",
  },
  {
    number: "04",
    title: "Auto-Dispatch",
    description: "Approved responses are sent automatically. Full traceability for every email.",
    icon: Send,
    color: "from-emerald-500 to-teal-500",
    bgColor: "bg-emerald-500/10",
    iconColor: "text-emerald-600",
    borderColor: "border-emerald-200",
  },
];

const containerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      staggerChildren: 0.15,
    },
  },
};

const itemVariants = {
  hidden: { opacity: 0, y: 30 },
  visible: {
    opacity: 1,
    y: 0,
    transition: {
      duration: 0.5,
      ease: [0.4, 0, 0.2, 1] as const,
    },
  },
};

export function WorkflowSection() {
  const reducedMotion = useReducedMotion();

  // Render without animations if reduced motion is preferred
  if (reducedMotion) {
    return (
      <section id="workflow" className="relative py-24 lg:py-32 overflow-hidden">
        {/* Background */}
        <div className="absolute inset-0 bg-gradient-to-b from-white via-slate-50/50 to-white" />
        <div className="absolute inset-0 bg-dot-pattern opacity-[0.03]" />
        
        <div className="relative max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
          {/* Section Header */}
          <div className="flex flex-col sm:flex-row sm:items-end sm:justify-between gap-4 mb-16">
            <div>
              <p className="text-sm font-medium text-muted-foreground mb-2">How it works</p>
              <h2 className="text-3xl sm:text-4xl lg:text-5xl font-semibold tracking-tight">
                Four steps to{" "}
                <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-600 to-violet-600">
                  inbox zero
                </span>
              </h2>
            </div>
            <Button variant="outline" size="sm" className="w-fit bg-white/80" asChild>
              <Link href="/docs" className="gap-1">
                View Documentation
                <ArrowUpRight className="w-3.5 h-3.5" />
              </Link>
            </Button>
          </div>

          {/* Steps Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {steps.map((step, index) => (
              <div
                key={step.number}
                className="group relative"
              >
                {/* Card */}
                <div className={`relative rounded-2xl border ${step.borderColor} bg-white p-6 shadow-sm transition-all duration-300 hover:shadow-xl hover:-translate-y-1`}>
                  {/* Gradient background on hover */}
                  <div className={`absolute inset-0 rounded-2xl bg-gradient-to-br ${step.color} opacity-0 group-hover:opacity-[0.03] transition-opacity duration-300`} />
                  
                  <div className="relative">
                    {/* Top row: Number and Icon */}
                    <div className="flex items-start justify-between mb-5">
                      {/* Large Step Number */}
                      <span className={`text-5xl font-bold bg-gradient-to-br ${step.color} bg-clip-text text-transparent`}>
                        {step.number}
                      </span>
                      
                      {/* Icon */}
                      <div className={`w-12 h-12 rounded-xl ${step.bgColor} flex items-center justify-center shadow-sm`}>
                        <step.icon className={`w-6 h-6 ${step.iconColor}`} />
                      </div>
                    </div>

                    {/* Content */}
                    <h3 className="text-lg font-semibold mb-2 text-slate-900">{step.title}</h3>
                    <p className="text-sm text-slate-600 leading-relaxed">
                      {step.description}
                    </p>
                  </div>

                  {/* Bottom gradient line */}
                  <div className={`absolute bottom-0 left-0 right-0 h-1 bg-gradient-to-r ${step.color} rounded-b-2xl opacity-0 group-hover:opacity-100 transition-opacity duration-300`} />
                </div>

                {/* Connector line (for desktop) */}
                {index < steps.length - 1 && (
                  <div className="hidden md:block absolute top-1/2 -right-3 w-6 h-px bg-gradient-to-r from-slate-200 to-transparent z-10" />
                )}
              </div>
            ))}
          </div>

          {/* Bottom CTA */}
          <div className="mt-16 text-center">
            <p className="text-muted-foreground mb-4">Ready to automate your inbox?</p>
            <Button size="lg" className="bg-gradient-to-r from-blue-600 to-violet-600 hover:from-blue-700 hover:to-violet-700 text-white border-0" asChild>
              <Link href="/register">
                Get Started Free
              </Link>
            </Button>
          </div>
        </div>
      </section>
    );
  }

  return (
    <section id="workflow" className="relative py-24 lg:py-32 overflow-hidden">
      {/* Background */}
      <div className="absolute inset-0 bg-gradient-to-b from-white via-slate-50/50 to-white" />
      <div className="absolute inset-0 bg-dot-pattern opacity-[0.03]" />
      
      <div className="relative max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Section Header */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.5 }}
          className="flex flex-col sm:flex-row sm:items-end sm:justify-between gap-4 mb-16"
        >
          <div>
            <p className="text-sm font-medium text-muted-foreground mb-2">How it works</p>
            <h2 className="text-3xl sm:text-4xl lg:text-5xl font-semibold tracking-tight">
              Four steps to{" "}
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-600 to-violet-600">
                inbox zero
              </span>
            </h2>
          </div>
          <Button variant="outline" size="sm" className="w-fit bg-white/80" asChild>
            <Link href="/docs" className="gap-1">
              View Documentation
              <ArrowUpRight className="w-3.5 h-3.5" />
            </Link>
          </Button>
        </motion.div>

        {/* Steps Grid */}
        <motion.div
          variants={containerVariants}
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true }}
          className="grid grid-cols-1 md:grid-cols-2 gap-6"
        >
          {steps.map((step, index) => (
            <motion.div
              key={step.number}
              variants={itemVariants}
              className="group relative"
            >
              {/* Card */}
              <div className={`relative rounded-2xl border ${step.borderColor} bg-white p-6 shadow-sm transition-all duration-300 hover:shadow-xl hover:-translate-y-1`}>
                {/* Gradient background on hover */}
                <div className={`absolute inset-0 rounded-2xl bg-gradient-to-br ${step.color} opacity-0 group-hover:opacity-[0.03] transition-opacity duration-300`} />
                
                <div className="relative">
                  {/* Top row: Number and Icon */}
                  <div className="flex items-start justify-between mb-5">
                    {/* Large Step Number */}
                    <span className={`text-5xl font-bold bg-gradient-to-br ${step.color} bg-clip-text text-transparent`}>
                      {step.number}
                    </span>
                    
                    {/* Icon */}
                    <div className={`w-12 h-12 rounded-xl ${step.bgColor} flex items-center justify-center shadow-sm`}>
                      <step.icon className={`w-6 h-6 ${step.iconColor}`} />
                    </div>
                  </div>

                  {/* Content */}
                  <h3 className="text-lg font-semibold mb-2 text-slate-900">{step.title}</h3>
                  <p className="text-sm text-slate-600 leading-relaxed">
                    {step.description}
                  </p>
                </div>

                {/* Bottom gradient line */}
                <div className={`absolute bottom-0 left-0 right-0 h-1 bg-gradient-to-r ${step.color} rounded-b-2xl opacity-0 group-hover:opacity-100 transition-opacity duration-300`} />
              </div>

              {/* Connector line (for desktop) */}
              {index < steps.length - 1 && (
                <div className="hidden md:block absolute top-1/2 -right-3 w-6 h-px bg-gradient-to-r from-slate-200 to-transparent z-10" />
              )}
            </motion.div>
          ))}
        </motion.div>

        {/* Bottom CTA */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.5, delay: 0.4 }}
          className="mt-16 text-center"
        >
          <p className="text-muted-foreground mb-4">Ready to automate your inbox?</p>
          <Button size="lg" className="bg-gradient-to-r from-blue-600 to-violet-600 hover:from-blue-700 hover:to-violet-700 text-white border-0" asChild>
            <Link href="/register">
              Get Started Free
            </Link>
          </Button>
        </motion.div>
      </div>
    </section>
  );
}
