"use client"

import { useState } from "react"
import { useRouter } from "next/navigation"
import { Loader2, Workflow, Mail } from "lucide-react"
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Button } from "@/components/ui/button"
import { Separator } from "@/components/ui/separator"
import api from "@/lib/api"

export default function LoginPage() {
  const router = useRouter()
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [isLoading, setIsLoading] = useState(false)
  const [isGmailLoading, setIsGmailLoading] = useState(false)
  const [error, setError] = useState("")
  const [validationErrors, setValidationErrors] = useState<{
    email?: string
    password?: string
  }>({})

  const validateForm = () => {
    const errors: { email?: string; password?: string } = {}

    if (!email) {
      errors.email = "Email is required"
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      errors.email = "Invalid email format"
    }

    if (!password) {
      errors.password = "Password is required"
    } else if (password.length < 6) {
      errors.password = "Password must be at least 6 characters"
    }

    setValidationErrors(errors)
    return Object.keys(errors).length === 0
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError("")

    if (!validateForm()) {
      return
    }

    setIsLoading(true)

    try {
      const response = await api.post("/auth/login", {
        email,
        password,
      })

      const { access_token } = response.data

      if (access_token) {
        localStorage.setItem("rf_access_token", access_token)
        router.push("/inbox")
      } else {
        setError("Login failed. No access token received.")
      }
    } catch (err: any) {
      setError(
        err.response?.data?.detail ||
        err.response?.data?.message ||
        "Login failed. Please check your credentials."
      )
    } finally {
      setIsLoading(false)
    }
  }

  const handleGmailConnect = async () => {
    setIsGmailLoading(true)
    setError("")

    try {
      const response = await api.get("/auth/gmail/url")
      const { url } = response.data

      if (url) {
        window.location.href = url
      } else {
        setError("Failed to get Gmail OAuth URL")
        setIsGmailLoading(false)
      }
    } catch (err: any) {
      setError(
        err.response?.data?.detail ||
        err.response?.data?.message ||
        "Failed to connect with Gmail"
      )
      setIsGmailLoading(false)
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-background p-4">
      <Card className="w-full max-w-md">
        <CardHeader className="text-center">
          <div className="flex items-center justify-center gap-2 mb-2">
            <Workflow className="size-8 text-primary" />
            <CardTitle className="text-2xl">ReasonFlow</CardTitle>
          </div>
          <CardDescription>
            Sign in to your account to continue
          </CardDescription>
        </CardHeader>

        <CardContent className="space-y-4">
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="email">Email</Label>
              <Input
                id="email"
                type="email"
                placeholder="name@example.com"
                value={email}
                onChange={(e) => {
                  setEmail(e.target.value)
                  setValidationErrors({ ...validationErrors, email: undefined })
                }}
                disabled={isLoading}
                aria-invalid={!!validationErrors.email}
              />
              {validationErrors.email && (
                <p className="text-sm text-destructive">{validationErrors.email}</p>
              )}
            </div>

            <div className="space-y-2">
              <Label htmlFor="password">Password</Label>
              <Input
                id="password"
                type="password"
                placeholder="Enter your password"
                value={password}
                onChange={(e) => {
                  setPassword(e.target.value)
                  setValidationErrors({ ...validationErrors, password: undefined })
                }}
                disabled={isLoading}
                aria-invalid={!!validationErrors.password}
              />
              {validationErrors.password && (
                <p className="text-sm text-destructive">{validationErrors.password}</p>
              )}
            </div>

            <Button
              type="submit"
              className="w-full"
              disabled={isLoading}
            >
              {isLoading ? (
                <>
                  <Loader2 className="animate-spin" />
                  Signing in...
                </>
              ) : (
                "Sign in"
              )}
            </Button>
          </form>

          {error && (
            <div className="rounded-md bg-destructive/10 border border-destructive/20 p-3 text-sm text-destructive">
              {error}
            </div>
          )}

          <div className="relative">
            <div className="absolute inset-0 flex items-center">
              <Separator />
            </div>
            <div className="relative flex justify-center text-xs uppercase">
              <span className="bg-card px-2 text-muted-foreground">or</span>
            </div>
          </div>

          <Button
            type="button"
            variant="outline"
            className="w-full"
            onClick={handleGmailConnect}
            disabled={isGmailLoading || isLoading}
          >
            {isGmailLoading ? (
              <>
                <Loader2 className="animate-spin" />
                Connecting...
              </>
            ) : (
              <>
                <Mail />
                Connect with Gmail
              </>
            )}
          </Button>
        </CardContent>

        <CardFooter className="flex justify-center">
          <p className="text-sm text-muted-foreground">
            Don&apos;t have an account?{" "}
            <a
              href="/register"
              className="text-primary hover:underline font-medium"
            >
              Register
            </a>
          </p>
        </CardFooter>
      </Card>
    </div>
  )
}
