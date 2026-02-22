"use client";

import { motion } from "framer-motion";
import { useReducedMotion } from "@/hooks/use-reduced-motion";

const stats = [
  { value: "<4s", label: "Processing time" },
  { value: "95%", label: "Classification accuracy" },
  { value: "10x", label: "Faster than manual" },
  { value: "24/7", label: "Always available" },
];

export function StatsSection() {
  const reducedMotion = useReducedMotion();

  // Render without animations if reduced motion is preferred
  if (reducedMotion) {
    return (
      <section className="relative py-16 border-y border-border/50 overflow-hidden">
        {/* Background */}
        <div className="absolute inset-0 bg-white/50" />
        <div className="absolute inset-0 bg-dot-pattern opacity-20" />
        
        <div className="relative max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-8">
            {stats.map((stat) => (
              <div key={stat.label} className="text-center">
                <div className="text-3xl sm:text-4xl font-medium tracking-tight mb-1">
                  {stat.value}
                </div>
                <p className="text-sm text-muted-foreground">{stat.label}</p>
              </div>
            ))}
          </div>
        </div>
      </section>
    );
  }

  return (
    <section className="relative py-16 border-y border-border/50 overflow-hidden">
      {/* Background */}
      <div className="absolute inset-0 bg-white/50" />
      <div className="absolute inset-0 bg-dot-pattern opacity-20" />
      
      <div className="relative max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.5 }}
          className="grid grid-cols-2 md:grid-cols-4 gap-8"
        >
          {stats.map((stat) => (
            <div key={stat.label} className="text-center">
              <div className="text-3xl sm:text-4xl font-medium tracking-tight mb-1">
                {stat.value}
              </div>
              <p className="text-sm text-muted-foreground">{stat.label}</p>
            </div>
          ))}
        </motion.div>
      </div>
    </section>
  );
}
