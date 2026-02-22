"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { motion, AnimatePresence } from "framer-motion";
import { useReducedMotion } from "@/hooks/use-reduced-motion";
import { Loader2, ArrowRight, Sparkles } from "lucide-react";

// Google logo SVG component
function GoogleLogo({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
      <path
        d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
        fill="#4285F4"
      />
      <path
        d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
        fill="#34A853"
      />
      <path
        d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
        fill="#FBBC05"
      />
      <path
        d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
        fill="#EA4335"
      />
    </svg>
  );
}
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import api from "@/lib/api";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [isGmailLoading, setIsGmailLoading] = useState(false);
  const [error, setError] = useState("");
  const [validationErrors, setValidationErrors] = useState<{
    email?: string;
    password?: string;
  }>({});
  const reducedMotion = useReducedMotion();

  const validateForm = () => {
    const errors: { email?: string; password?: string } = {};

    if (!email) {
      errors.email = "Email is required";
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      errors.email = "Invalid email format";
    }

    if (!password) {
      errors.password = "Password is required";
    } else if (password.length < 8) {
      errors.password = "Password must be at least 8 characters";
    }

    setValidationErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");

    if (!validateForm()) {
      return;
    }

    setIsLoading(true);

    try {
      const response = await api.post("/auth/login", {
        email,
        password,
      });

      const { access_token, refresh_token } = response.data;

      if (access_token) {
        localStorage.setItem("rf_access_token", access_token);
        if (refresh_token) {
          localStorage.setItem("rf_refresh_token", refresh_token);
        }
        router.push("/inbox");
      } else {
        setError("Login failed. No access token received.");
      }
    } catch (err: any) {
      setError(
        err.response?.data?.detail ||
          err.response?.data?.message ||
          "Login failed. Please check your credentials."
      );
    } finally {
      setIsLoading(false);
    }
  };

  const handleGmailConnect = async () => {
    setIsGmailLoading(true);
    setError("");

    try {
      const response = await api.get("/auth/gmail/url");
      const { url } = response.data;

      if (url) {
        window.location.href = url;
      } else {
        setError("Failed to get Gmail OAuth URL");
        setIsGmailLoading(false);
      }
    } catch (err: any) {
      setError(
        err.response?.data?.detail ||
          err.response?.data?.message ||
          "Failed to connect with Gmail"
      );
      setIsGmailLoading(false);
    }
  };

  return (
    <>
      {/* Header */}
      <div className="text-center mb-6">
        {reducedMotion ? (
          <>
            <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-white/80 backdrop-blur-sm border border-border/50 shadow-sm mb-4">
              <Sparkles className="w-3.5 h-3.5 text-amber-500" />
              <span className="text-xs text-muted-foreground">
                Welcome back
              </span>
            </div>
            <h1 className="text-2xl font-medium tracking-tight">
              Sign in to your account
            </h1>
            <p className="text-sm text-muted-foreground mt-1">
              Continue automating your inbox
            </p>
          </>
        ) : (
          <>
            <motion.div
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ duration: 0.3, delay: 0.15 }}
              className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-white/80 backdrop-blur-sm border border-border/50 shadow-sm mb-4"
            >
              <Sparkles className="w-3.5 h-3.5 text-amber-500" />
              <span className="text-xs text-muted-foreground">
                Welcome back
              </span>
            </motion.div>
            <motion.h1
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.4, delay: 0.2 }}
              className="text-2xl font-medium tracking-tight"
            >
              Sign in to your account
            </motion.h1>
            <motion.p
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.4, delay: 0.25 }}
              className="text-sm text-muted-foreground mt-1"
            >
              Continue automating your inbox
            </motion.p>
          </>
        )}
      </div>

      {/* Card */}
      {reducedMotion ? (
        <div>
          <Card className="border-border/50 shadow-xl bg-white/80 backdrop-blur-xl">
            <CardContent className="pt-6 space-y-4">
              {/* Google OAuth Button */}
              <Button
                type="button"
                variant="outline"
                className="w-full h-11 relative overflow-hidden group"
                onClick={handleGmailConnect}
                disabled={isGmailLoading || isLoading}
              >
                <div className="absolute inset-0 bg-gradient-to-r from-blue-500/5 via-red-500/5 to-yellow-500/5 opacity-0 group-hover:opacity-100 transition-opacity" />
                <div className="relative flex items-center justify-center gap-2">
                  {isGmailLoading ? (
                    <Loader2 className="animate-spin w-4 h-4" />
                  ) : (
                    <GoogleLogo className="w-4 h-4" />
                  )}
                  <span>
                    {isGmailLoading ? "Connecting..." : "Continue with Google"}
                  </span>
                </div>
              </Button>

              {/* Divider */}
              <div className="relative">
                <div className="absolute inset-0 flex items-center">
                  <Separator className="w-full" />
                </div>
                <div className="relative flex justify-center text-xs">
                  <span className="bg-card px-2 text-muted-foreground">
                    or continue with email
                  </span>
                </div>
              </div>

              {/* Form */}
              <form onSubmit={handleSubmit} className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="email" className="text-sm font-medium">
                    Email
                  </Label>
                  <Input
                    id="email"
                    type="email"
                    placeholder="name@example.com"
                    value={email}
                    onChange={(e) => {
                      setEmail(e.target.value);
                      setValidationErrors({ ...validationErrors, email: undefined });
                    }}
                    disabled={isLoading}
                    aria-invalid={!!validationErrors.email}
                    className="h-11 bg-white/50"
                  />
                  {validationErrors.email && (
                    <p className="text-sm text-destructive">
                      {validationErrors.email}
                    </p>
                  )}
                </div>

                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <Label htmlFor="password" className="text-sm font-medium">
                      Password
                    </Label>
                    <Link
                      href="#"
                      className="text-xs text-muted-foreground hover:text-foreground transition-colors"
                    >
                      Forgot password?
                    </Link>
                  </div>
                  <Input
                    id="password"
                    type="password"
                    placeholder="Enter your password"
                    value={password}
                    onChange={(e) => {
                      setPassword(e.target.value);
                      setValidationErrors({ ...validationErrors, password: undefined });
                    }}
                    disabled={isLoading}
                    aria-invalid={!!validationErrors.password}
                    className="h-11 bg-white/50"
                  />
                  {validationErrors.password && (
                    <p className="text-sm text-destructive">
                      {validationErrors.password}
                    </p>
                  )}
                </div>

                <Button
                  type="submit"
                  className="w-full h-11 group"
                  disabled={isLoading}
                >
                  {isLoading ? (
                    <>
                      <Loader2 className="animate-spin mr-2" />
                      Signing in...
                    </>
                  ) : (
                    <>
                      Sign in
                      <ArrowRight className="ml-2 w-4 h-4 group-hover:translate-x-1 transition-transform" />
                    </>
                  )}
                </Button>
              </form>

              {/* Error Message */}
              {error && (
                <div className="rounded-lg bg-destructive/10 border border-destructive/20 p-3 text-sm text-destructive">
                  {error}
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      ) : (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.3 }}
        >
        <Card className="border-border/50 shadow-xl bg-white/80 backdrop-blur-xl">
          <CardContent className="pt-6 space-y-4">
            {/* Google OAuth Button */}
            <Button
              type="button"
              variant="outline"
              className="w-full h-11 relative overflow-hidden group"
              onClick={handleGmailConnect}
              disabled={isGmailLoading || isLoading}
            >
              <div className="absolute inset-0 bg-gradient-to-r from-blue-500/5 via-red-500/5 to-yellow-500/5 opacity-0 group-hover:opacity-100 transition-opacity" />
              <div className="relative flex items-center justify-center gap-2">
                {isGmailLoading ? (
                  <Loader2 className="animate-spin w-4 h-4" />
                ) : (
                  <GoogleLogo className="w-4 h-4" />
                )}
                <span>
                  {isGmailLoading ? "Connecting..." : "Continue with Google"}
                </span>
              </div>
            </Button>

            {/* Divider */}
            <div className="relative">
              <div className="absolute inset-0 flex items-center">
                <Separator className="w-full" />
              </div>
              <div className="relative flex justify-center text-xs">
                <span className="bg-card px-2 text-muted-foreground">
                  or continue with email
                </span>
              </div>
            </div>

            {/* Form */}
            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="email" className="text-sm font-medium">
                  Email
                </Label>
                <Input
                  id="email"
                  type="email"
                  placeholder="name@example.com"
                  value={email}
                  onChange={(e) => {
                    setEmail(e.target.value);
                    setValidationErrors({ ...validationErrors, email: undefined });
                  }}
                  disabled={isLoading}
                  aria-invalid={!!validationErrors.email}
                  className="h-11 bg-white/50"
                />
                <AnimatePresence>
                  {validationErrors.email && (
                    <motion.p
                      initial={{ opacity: 0, height: 0 }}
                      animate={{ opacity: 1, height: "auto" }}
                      exit={{ opacity: 0, height: 0 }}
                      className="text-sm text-destructive"
                    >
                      {validationErrors.email}
                    </motion.p>
                  )}
                </AnimatePresence>
              </div>

              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <Label htmlFor="password" className="text-sm font-medium">
                    Password
                  </Label>
                  <Link
                    href="#"
                    className="text-xs text-muted-foreground hover:text-foreground transition-colors"
                  >
                    Forgot password?
                  </Link>
                </div>
                <Input
                  id="password"
                  type="password"
                  placeholder="Enter your password"
                  value={password}
                  onChange={(e) => {
                    setPassword(e.target.value);
                    setValidationErrors({ ...validationErrors, password: undefined });
                  }}
                  disabled={isLoading}
                  aria-invalid={!!validationErrors.password}
                  className="h-11 bg-white/50"
                />
                <AnimatePresence>
                  {validationErrors.password && (
                    <motion.p
                      initial={{ opacity: 0, height: 0 }}
                      animate={{ opacity: 1, height: "auto" }}
                      exit={{ opacity: 0, height: 0 }}
                      className="text-sm text-destructive"
                    >
                      {validationErrors.password}
                    </motion.p>
                  )}
                </AnimatePresence>
              </div>

              <Button
                type="submit"
                className="w-full h-11 group"
                disabled={isLoading}
              >
                {isLoading ? (
                  <>
                    <Loader2 className="animate-spin mr-2" />
                    Signing in...
                  </>
                ) : (
                  <>
                    Sign in
                    <ArrowRight className="ml-2 w-4 h-4 group-hover:translate-x-1 transition-transform" />
                  </>
                )}
              </Button>
            </form>

            {/* Error Message */}
            <AnimatePresence>
              {error && (
                <motion.div
                  initial={{ opacity: 0, y: -10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -10 }}
                  className="rounded-lg bg-destructive/10 border border-destructive/20 p-3 text-sm text-destructive"
                >
                  {error}
                </motion.div>
              )}
            </AnimatePresence>
          </CardContent>
        </Card>
      </motion.div>
      )}

      {/* Footer Link */}
      {reducedMotion ? (
        <p className="mt-6 text-center text-sm">
          <span className="text-muted-foreground">Don&apos;t have an account?</span>{" "}
          <Link
            href="/register"
            className="font-medium text-foreground hover:underline underline-offset-4 transition-all"
          >
            Create one
          </Link>
        </p>
      ) : (
        <motion.p
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.5, delay: 0.4 }}
          className="mt-6 text-center text-sm"
        >
          <span className="text-muted-foreground">Don&apos;t have an account?</span>{" "}
          <Link
            href="/register"
            className="font-medium text-foreground hover:underline underline-offset-4 transition-all"
          >
            Create one
          </Link>
        </motion.p>
      )}
    </>
  );
}
