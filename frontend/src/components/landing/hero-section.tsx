"use client";

import { Button } from "@/components/ui/button";
import Link from "next/link";
import { motion } from "framer-motion";
import { ArrowRight, Play, Mail, Sparkles, Zap, Shield } from "lucide-react";

export function HeroSection() {
  return (
    <section className="relative min-h-screen flex items-center justify-center overflow-hidden pt-20">
      {/* Background Layers */}
      <div className="absolute inset-0 bg-mesh" />
      <div className="absolute inset-0 bg-dot-pattern opacity-50" />
      <div className="absolute inset-0 bg-aurora" />
      
      {/* Content */}
      <div className="relative max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-20">
        <div className="text-center">
          {/* Badge */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
            className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-white/80 backdrop-blur-sm border border-border/50 shadow-sm mb-8"
          >
            <span className="flex h-2 w-2 rounded-full bg-green-500 animate-pulse" />
            <span className="text-sm text-muted-foreground">
              Powered by LangGraph + Gemini
            </span>
          </motion.div>

          {/* Headline */}
          <motion.h1
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.1 }}
            className="text-4xl sm:text-5xl md:text-6xl lg:text-7xl font-medium tracking-tight mb-6"
          >
            <span className="block">The AI inbox agent</span>
            <span className="block text-muted-foreground">built for professionals</span>
          </motion.h1>

          {/* Subheadline */}
          <motion.p
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.2 }}
            className="text-lg sm:text-xl text-muted-foreground max-w-2xl mx-auto mb-10"
          >
            Everything you need to automate email responses—classification, 
            context retrieval, and human-in-the-loop approvals.
          </motion.p>

          {/* CTAs */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.3 }}
            className="flex flex-col sm:flex-row items-center justify-center gap-4 mb-16"
          >
            <Button size="lg" className="group min-w-[180px] h-12" asChild>
              <Link href="/register">
                Start for free
                <ArrowRight className="ml-2 w-4 h-4 group-hover:translate-x-1 transition-transform" />
              </Link>
            </Button>
            <Button variant="outline" size="lg" className="min-w-[180px] h-12 gap-2" asChild>
              <Link href="#demo">
                <Play className="w-4 h-4" />
                Watch demo
              </Link>
            </Button>
          </motion.div>

          {/* Product Preview Card */}
          <motion.div
            initial={{ opacity: 0, y: 40 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.7, delay: 0.5 }}
            className="relative mx-auto max-w-5xl"
          >
            <div className="relative rounded-2xl bg-white/60 backdrop-blur-xl border border-border/50 shadow-2xl p-6">
              {/* App UI Mock */}
              <div className="bg-white rounded-xl border border-border/50 overflow-hidden">
                {/* Header */}
                <div className="flex items-center justify-between px-4 py-3 border-b border-border/50 bg-muted/30">
                  <div className="flex items-center gap-2">
                    <div className="w-8 h-8 rounded-lg bg-foreground flex items-center justify-center">
                      <span className="text-background font-bold text-xs">R</span>
                    </div>
                    <span className="font-medium text-sm">Inbox</span>
                  </div>
                  <div className="flex gap-2">
                    <div className="h-8 px-3 bg-primary text-primary-foreground rounded-md flex items-center text-xs font-medium">
                      <Sparkles className="w-3.5 h-3.5 mr-1.5" />
                      Classify All
                    </div>
                    <div className="h-8 px-3 bg-muted rounded-md flex items-center text-xs">
                      Sync
                    </div>
                  </div>
                </div>

                {/* Email List */}
                <div className="divide-y divide-border/50">
                  {[
                    { icon: Mail, title: "Product inquiry from Acme Corp", type: "Inquiry", confidence: 94, color: "bg-blue-500" },
                    { icon: Zap, title: "Meeting request with Sarah", type: "Meeting", confidence: 91, color: "bg-amber-500" },
                    { icon: Shield, title: "Support escalation #2847", type: "Urgent", confidence: 88, color: "bg-rose-500" },
                  ].map((email, i) => (
                    <div key={i} className="flex items-center gap-4 p-4 hover:bg-muted/30 transition-colors">
                      <div className={`w-10 h-10 rounded-full ${email.color} flex items-center justify-center flex-shrink-0`}>
                        <email.icon className="w-4 h-4 text-white" />
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium truncate">{email.title}</p>
                        <p className="text-xs text-muted-foreground">{email.type}</p>
                      </div>
                      <div className="flex items-center gap-2">
                        <span className="text-xs font-medium text-muted-foreground">{email.confidence}%</span>
                        <div className="w-16 h-1.5 bg-muted rounded-full overflow-hidden">
                          <div 
                            className="h-full bg-green-500 rounded-full"
                            style={{ width: `${email.confidence}%` }}
                          />
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Floating Elements */}
              <motion.div
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.8 }}
                className="absolute -left-4 top-1/4 bg-white rounded-xl border border-border/50 shadow-lg p-3 hidden lg:block"
              >
                <div className="flex items-center gap-2">
                  <div className="w-8 h-8 rounded-full bg-gradient-to-br from-indigo-500 to-purple-500 flex items-center justify-center">
                    <Sparkles className="w-4 h-4 text-white" />
                  </div>
                  <div>
                    <p className="text-xs font-medium">AI Generated</p>
                    <p className="text-[10px] text-muted-foreground">Draft ready</p>
                  </div>
                </div>
              </motion.div>

              <motion.div
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.9 }}
                className="absolute -right-4 top-1/3 bg-white rounded-xl border border-border/50 shadow-lg p-3 hidden lg:block"
              >
                <div className="flex items-center gap-2">
                  <div className="flex -space-x-2">
                    <div className="w-6 h-6 rounded-full bg-blue-500 border-2 border-white" />
                    <div className="w-6 h-6 rounded-full bg-green-500 border-2 border-white" />
                    <div className="w-6 h-6 rounded-full bg-purple-500 border-2 border-white" />
                  </div>
                  <p className="text-xs font-medium">3 approvals</p>
                </div>
              </motion.div>
            </div>
          </motion.div>

          {/* Trust badge */}
          <motion.p
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.5, delay: 0.7 }}
            className="mt-16 text-sm text-muted-foreground"
          >
            Open source • Self-hostable • MIT License
          </motion.p>
        </div>
      </div>
    </section>
  );
}
