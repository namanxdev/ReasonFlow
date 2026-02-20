"use client";

import { motion } from "framer-motion";
import { Mail, Brain, UserCheck, Send, ArrowUpRight } from "lucide-react";
import { Button } from "@/components/ui/button";
import Link from "next/link";

const steps = [
  {
    number: "01",
    title: "Connect Your Inbox",
    description: "Link your Gmail account with OAuth. Secure, encrypted, and revocable anytime.",
    icon: Mail,
    color: "bg-blue-500",
    gradient: "from-blue-500/10 to-cyan-500/10",
  },
  {
    number: "02",
    title: "AI Analyzes & Classifies",
    description: "Gemini-powered agent reads and classifies emails by intent with 95%+ accuracy.",
    icon: Brain,
    color: "bg-violet-500",
    gradient: "from-violet-500/10 to-purple-500/10",
  },
  {
    number: "03",
    title: "Review & Approve",
    description: "High-confidence emails auto-send. Others wait for your quick approval.",
    icon: UserCheck,
    color: "bg-pink-500",
    gradient: "from-pink-500/10 to-rose-500/10",
  },
  {
    number: "04",
    title: "Auto-Dispatch",
    description: "Approved responses are sent automatically. Full traceability for every email.",
    icon: Send,
    color: "bg-emerald-500",
    gradient: "from-emerald-500/10 to-teal-500/10",
  },
];

export function WorkflowSection() {
  return (
    <section id="workflow" className="relative py-24 lg:py-32 overflow-hidden">
      {/* Background */}
      <div className="absolute inset-0 bg-muted/30" />
      <div className="absolute inset-0 bg-dot-pattern opacity-20" />
      
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
            <p className="text-sm text-muted-foreground mb-2">How it works</p>
            <h2 className="text-3xl sm:text-4xl lg:text-5xl font-medium tracking-tight">
              Four steps to{" "}
              <span className="text-muted-foreground">inbox zero</span>
            </h2>
          </div>
          <Button variant="outline" size="sm" className="w-fit" asChild>
            <Link href="/docs" className="gap-1">
              View Documentation
              <ArrowUpRight className="w-3.5 h-3.5" />
            </Link>
          </Button>
        </motion.div>

        {/* Steps Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {steps.map((step, index) => (
            <motion.div
              key={step.number}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.5, delay: index * 0.1 }}
              className={`group relative rounded-2xl bg-white/80 backdrop-blur-sm border border-border/50 p-6 overflow-hidden hover:shadow-lg transition-all duration-300`}
            >
              {/* Gradient background */}
              <div className={`absolute inset-0 bg-gradient-to-br ${step.gradient} opacity-0 group-hover:opacity-100 transition-opacity duration-300`} />
              
              <div className="relative">
                {/* Number and Icon */}
                <div className="flex items-start justify-between mb-4">
                  <span className="text-4xl font-semibold text-muted-foreground/40">{step.number}</span>
                  <div className={`w-12 h-12 rounded-xl ${step.color} flex items-center justify-center shadow-lg`}>
                    <step.icon className="w-6 h-6 text-white" />
                  </div>
                </div>

                {/* Content */}
                <h3 className="text-xl font-medium mb-2">{step.title}</h3>
                <p className="text-sm text-muted-foreground leading-relaxed">
                  {step.description}
                </p>
              </div>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}
