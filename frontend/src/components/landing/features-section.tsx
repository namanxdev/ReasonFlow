"use client";

import { motion } from "framer-motion";
import {
  Brain,
  Workflow,
  Shield,
  Zap,
  BarChart3,
  Mail,
  GitBranch,
  Lock,
} from "lucide-react";
import { useReducedMotion } from "@/hooks/use-reduced-motion";

const features = [
  {
    icon: Brain,
    title: "AI Classification",
    description: "Automatically sort emails by intent—inquiries, meetings, complaints, and more.",
    gradient: "from-violet-500/20 to-purple-500/20",
    iconBg: "bg-violet-500",
  },
  {
    icon: Workflow,
    title: "Human-in-the-Loop",
    description: "Low-confidence responses route to you for approval. Full control, AI speed.",
    gradient: "from-pink-500/20 to-rose-500/20",
    iconBg: "bg-pink-500",
  },
  {
    icon: Zap,
    title: "Auto-Responses",
    description: "High-confidence emails get instant, contextual replies. Your inbox never sleeps.",
    gradient: "from-amber-500/20 to-orange-500/20",
    iconBg: "bg-amber-500",
  },
  {
    icon: Mail,
    title: "Context Retrieval",
    description: "Searches past emails, CRM, and calendar to craft informed responses.",
    gradient: "from-emerald-500/20 to-teal-500/20",
    iconBg: "bg-emerald-500",
  },
  {
    icon: BarChart3,
    title: "Full Observability",
    description: "Trace every decision with step-by-step execution logs and reasoning.",
    gradient: "from-blue-500/20 to-cyan-500/20",
    iconBg: "bg-blue-500",
  },
  {
    icon: Lock,
    title: "Privacy First",
    description: "Self-host on your infrastructure. No data sent to third parties.",
    gradient: "from-slate-500/20 to-gray-500/20",
    iconBg: "bg-slate-500",
  },
];

const containerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      staggerChildren: 0.1,
    },
  },
};

const itemVariants = {
  hidden: { opacity: 0, y: 20 },
  visible: {
    opacity: 1,
    y: 0,
    transition: {
      duration: 0.5,
    },
  },
};

export function FeaturesSection() {
  const reducedMotion = useReducedMotion();

  // Render without animations if reduced motion is preferred
  if (reducedMotion) {
    return (
      <section id="features" className="relative py-24 lg:py-32 overflow-hidden">
        {/* Background */}
        <div className="absolute inset-0 bg-dot-pattern opacity-30" />
        <div className="absolute inset-0 bg-gradient-to-b from-transparent via-background/50 to-background" />
        
        <div className="relative max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
          {/* Section Header */}
          <div className="text-center max-w-3xl mx-auto mb-16">
            <h2 className="text-3xl sm:text-4xl lg:text-5xl font-medium tracking-tight mb-4">
              Everything you need to{" "}
              <span className="text-muted-foreground">automate email</span>
            </h2>
          </div>

          {/* Features Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {features.map((feature) => (
              <div
                key={feature.title}
                className="group relative p-6 rounded-2xl bg-white/60 backdrop-blur-sm border border-border/50 hover:border-border transition-all duration-300 hover:shadow-lg"
              >
                {/* Gradient background on hover */}
                <div className={`absolute inset-0 rounded-2xl bg-gradient-to-br ${feature.gradient} opacity-0 group-hover:opacity-100 transition-opacity duration-300`} />
                
                <div className="relative">
                  {/* Icon */}
                  <div className={`w-12 h-12 rounded-xl ${feature.iconBg} flex items-center justify-center mb-4 shadow-lg`}>
                    <feature.icon className="w-6 h-6 text-white" />
                  </div>

                  {/* Content */}
                  <h3 className="text-lg font-medium mb-2">{feature.title}</h3>
                  <p className="text-sm text-muted-foreground leading-relaxed">
                    {feature.description}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>
    );
  }

  return (
    <section id="features" className="relative py-24 lg:py-32 overflow-hidden">
      {/* Background */}
      <div className="absolute inset-0 bg-dot-pattern opacity-30" />
      <div className="absolute inset-0 bg-gradient-to-b from-transparent via-background/50 to-background" />
      
      <div className="relative max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Section Header */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.5 }}
          className="text-center max-w-3xl mx-auto mb-16"
        >
          <h2 className="text-3xl sm:text-4xl lg:text-5xl font-medium tracking-tight mb-4">
            Everything you need to{" "}
            <span className="text-muted-foreground">automate email</span>
          </h2>
        </motion.div>

        {/* Features Grid */}
        <motion.div
          variants={containerVariants}
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true }}
          className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6"
        >
          {features.map((feature) => (
            <motion.div
              key={feature.title}
              variants={itemVariants}
              className="group relative p-6 rounded-2xl bg-white/60 backdrop-blur-sm border border-border/50 hover:border-border transition-all duration-300 hover:shadow-lg"
            >
              {/* Gradient background on hover */}
              <div className={`absolute inset-0 rounded-2xl bg-gradient-to-br ${feature.gradient} opacity-0 group-hover:opacity-100 transition-opacity duration-300`} />
              
              <div className="relative">
                {/* Icon */}
                <div className={`w-12 h-12 rounded-xl ${feature.iconBg} flex items-center justify-center mb-4 shadow-lg`}>
                  <feature.icon className="w-6 h-6 text-white" />
                </div>

                {/* Content */}
                <h3 className="text-lg font-medium mb-2">{feature.title}</h3>
                <p className="text-sm text-muted-foreground leading-relaxed">
                  {feature.description}
                </p>
              </div>
            </motion.div>
          ))}
        </motion.div>
      </div>
    </section>
  );
}
