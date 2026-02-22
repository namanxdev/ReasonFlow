"use client";

import { motion } from "framer-motion";
import { Button } from "@/components/ui/button";
import Link from "next/link";
import { ArrowRight, Github } from "lucide-react";
import { useReducedMotion } from "@/hooks/use-reduced-motion";

export function CTASection() {
  const reducedMotion = useReducedMotion();

  // Render without animations if reduced motion is preferred
  if (reducedMotion) {
    return (
      <section className="relative py-24 lg:py-32 overflow-hidden">
        {/* Background */}
        <div className="absolute inset-0 bg-mesh" />
        <div className="absolute inset-0 bg-dot-pattern opacity-30" />
        <div className="absolute inset-0 bg-aurora" />
        
        <div className="relative max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center">
            {/* Badge */}
            <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-white/80 backdrop-blur-sm border border-border/50 shadow-sm mb-8">
              <span className="flex h-2 w-2 rounded-full bg-green-500" />
              <span className="text-sm text-muted-foreground">
                Open Source • MIT License
              </span>
            </div>

            <h2 className="text-3xl sm:text-4xl lg:text-5xl font-medium tracking-tight mb-4">
              Ready to reclaim your{" "}
              <span className="text-muted-foreground">inbox?</span>
            </h2>
            <p className="text-lg text-muted-foreground mb-8 max-w-xl mx-auto">
              Join developers and teams using ReasonFlow to automate email management. 
              Self-host for free or deploy to your own infrastructure.
            </p>

            <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
              <Button size="lg" className="group min-w-[180px] h-12" asChild>
                <Link href="/register">
                  Get started free
                  <ArrowRight className="ml-2 w-4 h-4 group-hover:translate-x-1 transition-transform" />
                </Link>
              </Button>
              <Button variant="outline" size="lg" className="min-w-[180px] h-12 gap-2" asChild>
                <Link href="https://github.com" target="_blank">
                  <Github className="w-4 h-4" />
                  View on GitHub
                </Link>
              </Button>
            </div>

            {/* Tech Stack */}
            <div className="mt-16 pt-8 border-t border-border/50">
              <p className="text-sm text-muted-foreground mb-4">Built with modern technologies</p>
              <div className="flex flex-wrap items-center justify-center gap-x-6 gap-y-2 text-muted-foreground">
                {["FastAPI", "LangGraph", "Gemini", "Next.js", "PostgreSQL"].map((tech) => (
                  <span key={tech} className="text-sm hover:text-foreground transition-colors">
                    {tech}
                  </span>
                ))}
              </div>
            </div>
          </div>
        </div>
      </section>
    );
  }

  return (
    <section className="relative py-24 lg:py-32 overflow-hidden">
      {/* Background */}
      <div className="absolute inset-0 bg-mesh" />
      <div className="absolute inset-0 bg-dot-pattern opacity-30" />
      <div className="absolute inset-0 bg-aurora" />
      
      <div className="relative max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.5 }}
          className="text-center"
        >
          {/* Badge */}
          <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-white/80 backdrop-blur-sm border border-border/50 shadow-sm mb-8">
            <span className="flex h-2 w-2 rounded-full bg-green-500" />
            <span className="text-sm text-muted-foreground">
              Open Source • MIT License
            </span>
          </div>

          <h2 className="text-3xl sm:text-4xl lg:text-5xl font-medium tracking-tight mb-4">
            Ready to reclaim your{" "}
            <span className="text-muted-foreground">inbox?</span>
          </h2>
          <p className="text-lg text-muted-foreground mb-8 max-w-xl mx-auto">
            Join developers and teams using ReasonFlow to automate email management. 
            Self-host for free or deploy to your own infrastructure.
          </p>

          <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
            <Button size="lg" className="group min-w-[180px] h-12" asChild>
              <Link href="/register">
                Get started free
                <ArrowRight className="ml-2 w-4 h-4 group-hover:translate-x-1 transition-transform" />
              </Link>
            </Button>
            <Button variant="outline" size="lg" className="min-w-[180px] h-12 gap-2" asChild>
              <Link href="https://github.com" target="_blank">
                <Github className="w-4 h-4" />
                View on GitHub
              </Link>
            </Button>
          </div>

          {/* Tech Stack */}
          <div className="mt-16 pt-8 border-t border-border/50">
            <p className="text-sm text-muted-foreground mb-4">Built with modern technologies</p>
            <div className="flex flex-wrap items-center justify-center gap-x-6 gap-y-2 text-muted-foreground">
              {["FastAPI", "LangGraph", "Gemini", "Next.js", "PostgreSQL"].map((tech) => (
                <span key={tech} className="text-sm hover:text-foreground transition-colors">
                  {tech}
                </span>
              ))}
            </div>
          </div>
        </motion.div>
      </div>
    </section>
  );
}
