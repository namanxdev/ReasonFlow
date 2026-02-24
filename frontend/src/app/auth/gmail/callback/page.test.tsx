import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import { useAuthStore } from "@/stores/auth-store";

// Mock the API module
vi.mock("@/lib/api", () => ({
  default: {
    post: vi.fn(),
  },
}));

// Mock framer-motion to avoid animation complexity in tests
vi.mock("framer-motion", () => ({
  motion: {
    div: ({ children, ...props }: React.HTMLAttributes<HTMLDivElement>) => (
      <div {...props}>{children}</div>
    ),
  },
  AnimatePresence: ({ children }: { children: React.ReactNode }) => children,
}));

// Mock lucide-react icons
vi.mock("lucide-react", () => ({
  Loader2: () => <span data-testid="loader-icon" />,
  XCircle: () => <span data-testid="xcircle-icon" />,
  Sparkles: () => <span data-testid="sparkles-icon" />,
}));

// Mock the Button component
vi.mock("@/components/ui/button", () => ({
  Button: ({ children, onClick }: { children: React.ReactNode; onClick?: () => void }) => (
    <button onClick={onClick}>{children}</button>
  ),
}));

// Mock use-reduced-motion
vi.mock("@/hooks/use-reduced-motion", () => ({
  useReducedMotion: () => true,
}));

import api from "@/lib/api";
import GmailCallbackPage from "./page";

const mockApi = api as { post: ReturnType<typeof vi.fn> };

describe("GmailCallbackPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    // Reset auth store
    useAuthStore.setState({
      user: null,
      accessToken: null,
      isAuthenticated: false,
      isLoading: false,
    });
    // Reset localStorage mock
    (localStorage.setItem as ReturnType<typeof vi.fn>).mockClear();
  });

  it("shows loading state initially", () => {
    // Provide a code param so the effect runs
    vi.mocked(
      (await import("next/navigation")).useSearchParams
    );

    render(<GmailCallbackPage />);
    expect(screen.getByText("Connecting your account...")).toBeInTheDocument();
  });

  it("calls login() on auth store when access_token is returned", async () => {
    // Override useSearchParams to return a code
    const { useSearchParams } = await import("next/navigation");
    vi.mocked(useSearchParams).mockReturnValue(
      new URLSearchParams("code=test-oauth-code") as unknown as ReturnType<typeof useSearchParams>
    );

    mockApi.post.mockResolvedValueOnce({
      data: {
        status: "logged_in",
        email: "gmailuser@gmail.com",
        access_token: "test-jwt-token",
      },
    });

    render(<GmailCallbackPage />);

    await waitFor(() => {
      expect(mockApi.post).toHaveBeenCalledWith("/auth/gmail/callback", {
        code: "test-oauth-code",
      });
    });

    await waitFor(() => {
      const state = useAuthStore.getState();
      expect(state.isAuthenticated).toBe(true);
      expect(state.accessToken).toBe("test-jwt-token");
      expect(state.user).toEqual({ id: "", email: "gmailuser@gmail.com" });
    });

    expect(localStorage.setItem).toHaveBeenCalledWith(
      "rf_access_token",
      "test-jwt-token"
    );
  });

  it("does NOT call login() on auth store when no access_token is returned", async () => {
    const { useSearchParams } = await import("next/navigation");
    vi.mocked(useSearchParams).mockReturnValue(
      new URLSearchParams("code=test-oauth-code") as unknown as ReturnType<typeof useSearchParams>
    );

    mockApi.post.mockResolvedValueOnce({
      data: {
        status: "connected",
        email: "gmailuser@gmail.com",
        // No access_token — this is the link-account flow
      },
    });

    render(<GmailCallbackPage />);

    await waitFor(() => {
      expect(mockApi.post).toHaveBeenCalled();
    });

    // Wait a tick to ensure the effect has finished processing
    await waitFor(() => {
      const state = useAuthStore.getState();
      expect(state.isAuthenticated).toBe(false);
      expect(state.accessToken).toBeNull();
    });

    expect(localStorage.setItem).not.toHaveBeenCalled();
  });

  it("shows error state when no code param is present", async () => {
    const { useSearchParams } = await import("next/navigation");
    vi.mocked(useSearchParams).mockReturnValue(
      new URLSearchParams() as unknown as ReturnType<typeof useSearchParams>
    );

    render(<GmailCallbackPage />);

    await waitFor(() => {
      expect(screen.getByText("Connection failed")).toBeInTheDocument();
    });

    expect(
      screen.getByText(
        "No authorization code received from Google. Please try again."
      )
    ).toBeInTheDocument();
    expect(mockApi.post).not.toHaveBeenCalled();
  });

  it("shows error state when the API call fails", async () => {
    const { useSearchParams } = await import("next/navigation");
    vi.mocked(useSearchParams).mockReturnValue(
      new URLSearchParams("code=bad-code") as unknown as ReturnType<typeof useSearchParams>
    );

    mockApi.post.mockRejectedValueOnce({
      response: { data: { detail: "Invalid OAuth code." } },
    });

    render(<GmailCallbackPage />);

    await waitFor(() => {
      expect(screen.getByText("Connection failed")).toBeInTheDocument();
    });

    expect(screen.getByText("Invalid OAuth code.")).toBeInTheDocument();

    const state = useAuthStore.getState();
    expect(state.isAuthenticated).toBe(false);
  });
});
