# ReasonFlow — Application Audit & Issues Report

> Comprehensive audit of the ReasonFlow application covering security, rate limiting, validation, error handling, CRM integration, WebSocket, and frontend completeness.
>
> **Audit Date:** 2026-02-20
> **Resolution Review:** 2026-02-21 — **53 of 83 issues resolved**, 1 partially resolved, 29 remain open.

---

## Table of Contents

- [1. CRM Integration Status](#1-crm-integration-status)
- [2. Critical Security Issues](#2-critical-security-issues)
- [3. Rate Limiting](#3-rate-limiting)
- [4. Input Validation Gaps](#4-input-validation-gaps)
- [5. Error Handling Gaps](#5-error-handling-gaps)
- [6. Missing Features](#6-missing-features)
- [7. Frontend Issues](#7-frontend-issues)
- [8. Production Readiness](#8-production-readiness)
- [Issue Summary Table](#issue-summary-table)

---

## 1. CRM Integration Status

### Architecture

The CRM system uses a **pluggable adapter pattern**:

- **Abstract base:** `backend/app/integrations/crm/base.py` — defines `CRMBase` ABC with `get_contact()`, `update_contact()`, `search_contacts()`
- **Factory:** `backend/app/integrations/crm/factory.py` — returns the appropriate CRM client based on environment
- **Mock implementation:** `backend/app/integrations/crm/mock_crm.py` — in-memory store with 3 seed contacts

### How CRM Connects to the Application

| Integration Point | File | Description |
|---|---|---|
| Email Sync Auto-Population | `backend/app/services/email_service.py:222-252` | When emails sync from Gmail, unique senders are auto-added as CRM contacts tagged `["auto-synced"]` |
| Agent Retrieve Node | `backend/app/agent/nodes/retrieve.py:68-91` | Looks up sender in CRM, adds name/company/notes as context for the LLM |
| Agent Decide Node | `backend/app/agent/nodes/decide.py` | Selects `get_contact` tool for complaint, inquiry, and follow_up emails |
| Agent Tool Registry | `backend/app/agent/tools/registry.py:181-199` | `get_contact` and `update_contact` tools registered for agent use |
| REST API | `backend/app/api/routes/crm.py` | 3 endpoints: list/search, get by email, update contact |
| Frontend Page | `frontend/src/app/crm/page.tsx` | Full contact management UI with search, view, edit |
| Frontend Hooks | `frontend/src/hooks/use-crm.ts` | `useContacts()`, `useContact()`, `useUpdateContact()` via TanStack Query |

### CRM Issues

| ID | Issue | Severity | Details |
|---|---|---|---|
| CRM-1 | **No production CRM adapter** | Medium | Only `MockCRM` exists. The factory always returns MockCRM regardless of environment. No Salesforce, HubSpot, or Pipedrive adapter implemented. |
| CRM-2 | **No CRM config in settings** | Low | `backend/app/core/config.py` has no CRM-related configuration (API keys, endpoints, provider selection). |
| CRM-3 | **CRM email param not validated** | Low | CRM route path parameter `{email}` is a plain string, not validated with `EmailStr`. File: `backend/app/api/routes/crm.py` |
| CRM-4 | **Auto-populated contacts have empty fields** | Low | Contacts created from email sync have empty `company` and `title` fields — no enrichment logic exists. |

**Suggested Fix for CRM-1:** Implement at least one real adapter (e.g., HubSpot) following the `CRMBase` interface, add provider config to `config.py`, and update `factory.py` to select based on `APP_ENV` or a `CRM_PROVIDER` setting.

---

## 2. Critical Security Issues

### SEC-1: Rate Limiting Defined but Not Applied — RESOLVED

- **Severity:** Critical
- **Location:** `backend/app/api/middleware/rate_limit.py`, `backend/app/api/router.py`
- **Resolution:** Rate limiting is now applied globally via `api_router = APIRouter(dependencies=[Depends(rate_limit)])` in `router.py:20`. A stricter `auth_rate_limit` (10 req/min) was created and applied to auth endpoints.

### SEC-2: Missing Security Headers — RESOLVED

- **Severity:** Critical
- **Location:** `backend/app/main.py:24-35`
- **Resolution:** `SecurityHeadersMiddleware` now adds all 6 headers: `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `X-XSS-Protection: 1; mode=block`, `Strict-Transport-Security`, `Content-Security-Policy: default-src 'self'`, `Referrer-Policy: strict-origin-when-cross-origin`.

### SEC-3: JWT Token Stored in localStorage

- **Severity:** Critical
- **Location:** `frontend/src/lib/api.ts`
- **Problem:** Access tokens are stored in `localStorage`, which is accessible to any JavaScript running on the page. If an XSS vulnerability exists anywhere in the frontend, tokens can be stolen.
- **Impact:** Token theft via XSS attacks.
- **Fix:** Use `httpOnly` cookies for token storage with `SameSite=Strict` and `Secure` flags. Alternatively, keep tokens in memory only with a refresh token in an httpOnly cookie.

### SEC-4: CORS Configuration Too Permissive — RESOLVED

- **Severity:** Medium
- **Location:** `backend/app/main.py:94-100`
- **Resolution:** CORS now restricted to specific methods (`GET, POST, PUT, DELETE, OPTIONS, PATCH`) and specific headers (`Content-Type, Authorization, Accept, X-Requested-With`).

### SEC-5: Password Validation Mismatch — RESOLVED

- **Severity:** Medium
- **Location:** `frontend/src/app/(auth)/login/page.tsx:64`, `frontend/src/app/(auth)/register/page.tsx:70`
- **Resolution:** Both login and register pages now validate minimum 8 characters, matching the backend `RegisterRequest` schema (`min_length=8`).

### SEC-6: Default JWT Secret in Config — RESOLVED

- **Severity:** Medium
- **Location:** `backend/app/core/config.py:39`, `backend/app/main.py:38-58`
- **Resolution:** `JWT_SECRET_KEY` default changed to empty string `""`. Production validation now calls `sys.exit(1)` to hard-abort startup if `JWT_SECRET_KEY` is empty or set to an insecure placeholder.

### SEC-7: No CSRF Protection

- **Severity:** Medium
- **Location:** Frontend state-changing operations
- **Problem:** No CSRF tokens are used for state-changing requests. Combined with `allow_credentials=True` in CORS, this creates a CSRF attack vector.
- **Fix:** Implement CSRF token middleware or use the `SameSite` cookie attribute if switching to cookie-based auth.

---

## 3. Rate Limiting

### Current State

| Aspect | Status | Details |
|---|---|---|
| Implementation | Done | `backend/app/api/middleware/rate_limit.py` — In-memory sliding window |
| Default limit | 60 req/min | Configurable via `RATE_LIMIT_PER_MINUTE` setting |
| Per-user tracking | Done | Uses user ID from JWT, falls back to IP for unauthenticated |
| 429 Response | Done | Returns `Retry-After` header |
| Applied to routes | Done | Global on `api_router` + stricter `auth_rate_limit` on auth endpoints |

### What Needs to Happen

| ID | Task | Priority |
|---|---|---|
| RL-1 | Apply rate limiting globally to the API router | Critical — **RESOLVED** (`router.py:20`) |
| RL-2 | Add stricter limits on auth endpoints (e.g., 10 req/min for login) | High — **RESOLVED** (`auth_rate_limit` applied to `/register`, `/login`, `/forgot-password`, `/reset-password`) |
| RL-3 | Add per-user email sending limits | Medium |
| RL-4 | Add rate limiting to batch operation endpoints | Medium |

---

## 4. Input Validation Gaps

### What's Done Well

- All Pydantic schemas use `ConfigDict(extra="forbid")` to reject unknown fields
- Email fields use `EmailStr` validation
- Pagination params are bounded (page >= 1, per_page 1-100)
- Batch operations have size limits (classify: 100, process: 50)
- Templates have max_length constraints on name/subject

### Gaps

| ID | Issue | Severity | Location |
|---|---|---|---|
| VAL-1 | **Timezone field accepts any string** | Low | Settings schema — allows any 100-char string instead of validating against IANA timezone database |
| VAL-2 | **CRM email path param not validated** | Low | `backend/app/api/routes/crm.py` — plain string, not `EmailStr` |
| VAL-3 | **Batch requests don't verify email ownership** | Medium | Batch routes — can reference any email ID without checking it belongs to the authenticated user |
| VAL-4 | **No character limits on email body** | Low | Email processing doesn't limit body size, which could cause LLM token overflow |
| VAL-5 | **Search query injection** | Low | Search params passed directly to CRM `search_contacts()` — safe with MockCRM but needs validation for real CRM adapters using SQL/API |

---

## 5. Error Handling Gaps

### What's Implemented

- **Global error handler middleware:** `backend/app/api/middleware/error_handler.py`
- Handles: `StarletteHTTPException`, `RequestValidationError`, `ValueError`, generic `Exception`
- Standardized `ErrorResponse` format with `detail`, `code`, and `extra` fields

### Gaps

| ID | Issue | Severity | Location |
|---|---|---|---|
| ERR-1 | **No specific database error handlers** | Medium | SQLAlchemy exceptions (connection errors, constraint violations) are caught by generic handler — no meaningful user-facing messages |
| ERR-2 | **No OAuth/Gmail API error handlers** | Medium | Gmail API failures (token expired, quota exceeded) return generic 500 errors |
| ERR-3 | **No timeout handling** — **RESOLVED** | Medium | LLM calls now use `asyncio.wait_for(timeout=30s)` in `client.py:60-63`. Agent pipeline uses `settings.AGENT_PIPELINE_TIMEOUT` in `graph.py:605-608`. |
| ERR-4 | **No structured logging** — **RESOLVED** | Medium | `backend/app/core/logging.py` implements structured JSON logging with `jsonlogger.JsonFormatter`, `RequestIdFilter` using ContextVar `request_id_var`, and `RequestIdMiddleware` propagates request IDs on every response. |
| ERR-5 | **WebSocket errors unstructured** | Low | WebSocket notifications use raw text errors, not standardized format |

---

## 6. Missing Features

| ID | Feature | Severity | Details |
|---|---|---|---|
| FEAT-1 | **Empty Zustand stores** | Medium | `frontend/src/stores/` directory exists but is empty — no centralized auth state management, relies entirely on localStorage |
| FEAT-2 | **No WebSocket heartbeat** — **RESOLVED** | Medium | Heartbeat task in `notifications.py:32-50` sends `{"type": "ping"}` every 30 seconds with proper `CancelledError` cleanup in `finally` block. |
| FEAT-3 | **No WebSocket reconnection** | Medium | Frontend has no exponential backoff reconnection logic for dropped connections |
| FEAT-4 | **Health check incomplete** — **RESOLVED** | Low | `GET /health` checks database and Gemini API configuration |
| FEAT-5 | **Forgot password flow not implemented** — **PARTIALLY RESOLVED** | Medium | Backend endpoints `/auth/forgot-password` and `/auth/reset-password` are implemented in `auth.py:152-219`. `create_password_reset_token()` exists in `security.py:24-32`. **Still missing:** actual email sending (TODO at `auth.py:175`), and frontend "Forgot password?" link still points to `href="#"` (`login/page.tsx:258`). |
| FEAT-6 | **No idempotency keys** — **RESOLVED** | Medium | `dispatch_node` checks PostgreSQL idempotency keys before sending (`dispatch.py:23-38,141-166`). `IdempotencyMiddleware` added at HTTP level (`main.py:91`). |
| FEAT-7 | **No request ID tracking** — **RESOLVED** | Low | `RequestIdMiddleware` in `backend/app/api/middleware/request_id.py:16-52` generates/propagates `X-Request-ID` headers and stores in ContextVar for log correlation. |
| FEAT-8 | **No OAuth token refresh rotation** — **RESOLVED** | Medium | `refresh_user_gmail_token()` in `auth_service.py:270-347` exchanges refresh token for new access token from Google's OAuth2 endpoint, encrypts and persists the result. Called before Gmail operations in `email_service.py:131`. |
| FEAT-9 | **No event persistence** | Low | WebSocket events are ephemeral — if client disconnects, events are lost (no message queue/replay) |
| FEAT-10 | **No API versioning strategy** | Low | Routes use `/api/v1` prefix but no v2 migration plan or deprecation strategy exists |

---

## 7. Frontend Issues

| ID | Issue | Severity | Location |
|---|---|---|---|
| FE-1 | **No proactive token expiration check** — **RESOLVED** | Medium | `isTokenExpiringSoon()` in `api.ts:22-30` decodes JWT payload and checks `exp` claim with 60-second buffer. Request interceptor proactively refreshes before requests. |
| FE-2 | **Silent auth failure redirect** — **RESOLVED** | Low | `toast.error("Your session has expired. Please log in again.")` shown before redirect to `/login?reason=session_expired` in `api.ts:72,148,169`. |
| FE-3 | **No centralized auth state** | Medium | No Zustand store for auth — token, user info, and auth status scattered across localStorage and component state |
| FE-4 | **CRM update doesn't invalidate list** — **RESOLVED** | Low | `useUpdateContact` now invalidates both `["crm", "contact", variables.email]` and `["crm", "contacts"]` list cache in `use-crm.ts:47-54`. |

---

## 8. Production Readiness

### Checklist

| Area | Status | Notes |
|---|---|---|
| JWT Authentication | Done | Refresh tokens issued, production validation blocks insecure startup, proactive expiry check |
| Password Hashing | Done | bcrypt implementation |
| OAuth Token Encryption | Done | Fernet with separate `ENCRYPTION_KEY` |
| Rate Limiting | Done | Applied globally + stricter auth limits (10 req/min) |
| Security Headers | Done | Full set via `SecurityHeadersMiddleware` |
| Input Validation | Mostly Done | Minor gaps listed above |
| Error Handling | Mostly Done | Timeouts added, structured logging added, some specific handlers still missing |
| Health Check | Done | DB + Gemini API |
| Logging | Done | Structured JSON logging with request ID correlation |
| Monitoring | **Missing** | No Prometheus/StatsD integration |
| Graceful Shutdown | **Missing** | No cleanup for background tasks |
| Database Migrations | Done | Alembic configured, runs on container startup |
| Docker | Done | Multi-stage build, frontend container, entrypoint script |
| CI/CD | Done | GitHub Actions configured |
| Tests | Good | Unit + integration tests for major features |

---

## Issue Summary Table

### Phase 1 Issues

| ID | Issue | Severity | Category | Status |
|---|---|---|---|---|
| SEC-1 | Rate limiting not applied to routes | **Critical** | Security | **RESOLVED** |
| SEC-2 | Missing security headers | **Critical** | Security | **RESOLVED** |
| SEC-3 | JWT in localStorage (XSS risk) | **Critical** | Security | |
| SEC-4 | CORS too permissive | Medium | Security | **RESOLVED** |
| SEC-5 | Password validation mismatch | Medium | Security | **RESOLVED** |
| SEC-6 | Default JWT secret in config | Medium | Security | **RESOLVED** |
| SEC-7 | No CSRF protection | Medium | Security | |
| CRM-1 | No production CRM adapter | Medium | CRM | |
| CRM-2 | No CRM config in settings | Low | CRM | |
| CRM-3 | CRM email param not validated | Low | CRM | |
| CRM-4 | Auto-populated contacts lack enrichment | Low | CRM | |
| RL-1 | Rate limiting not wired to router | **Critical** | Rate Limiting | **RESOLVED** |
| RL-2 | No stricter limits on auth endpoints | High | Rate Limiting | **RESOLVED** |
| RL-3 | No email sending rate limits | Medium | Rate Limiting | |
| RL-4 | No batch endpoint rate limits | Medium | Rate Limiting | |
| VAL-1 | Timezone field unvalidated | Low | Validation | |
| VAL-2 | CRM email path unvalidated | Low | Validation | |
| VAL-3 | Batch emails ownership unchecked | Medium | Validation | |
| VAL-4 | No email body size limit | Low | Validation | |
| VAL-5 | Search query injection risk | Low | Validation | |
| ERR-1 | No database error handlers | Medium | Error Handling | |
| ERR-2 | No OAuth/Gmail error handlers | Medium | Error Handling | |
| ERR-3 | No timeout handling | Medium | Error Handling | **RESOLVED** |
| ERR-4 | No structured logging | Medium | Error Handling | **RESOLVED** |
| ERR-5 | WebSocket errors unstructured | Low | Error Handling | |
| FEAT-1 | Empty Zustand stores | Medium | Frontend | |
| FEAT-2 | No WebSocket heartbeat | Medium | WebSocket | **RESOLVED** |
| FEAT-3 | No WebSocket reconnection | Medium | WebSocket | |
| FEAT-4 | Health check incomplete | Low | Infrastructure | |
| FEAT-5 | Forgot password not implemented | Medium | Auth | **PARTIALLY RESOLVED** |
| FEAT-6 | No idempotency keys | Medium | Email | **RESOLVED** |
| FEAT-7 | No request ID tracking | Low | Observability | **RESOLVED** |
| FEAT-8 | No OAuth token refresh rotation | Medium | Auth | **RESOLVED** |
| FEAT-9 | No event persistence | Low | WebSocket | |
| FEAT-10 | No API versioning strategy | Low | Architecture | |
| FE-1 | No proactive token expiry check | Medium | Frontend | **RESOLVED** |
| FE-2 | Silent auth failure redirect | Low | Frontend | **RESOLVED** |
| FE-3 | No centralized auth state store | Medium | Frontend | |
| FE-4 | CRM cache invalidation incomplete | Low | Frontend | **RESOLVED** |

### Phase 2 Issues

| ID | Issue | Severity | Category | Status |
|---|---|---|---|---|
| BE-NEW-1 | GmailClient instantiated without credentials | **Critical** | Runtime Bug | **RESOLVED** |
| BE-NEW-2 | Token refresh flow completely broken | **Critical** | Runtime Bug | **RESOLVED** |
| BE-NEW-3 | WebSocket parses email as UUID | **Critical** | Runtime Bug | **RESOLVED** |
| BE-NEW-4 | Inefficient email count query (loads all rows) | Medium | Backend | **RESOLVED** |
| BE-NEW-5 | Gmail fetch: 51 serial HTTP requests, no pagination | Medium | Backend | **RESOLVED** |
| BE-NEW-6 | Email deduplication is N+1 | Medium | Backend | **RESOLVED** |
| BE-NEW-7 | LangGraph recompiled per email | Low | Backend | **RESOLVED** |
| DB-NEW-1 | No index on Email `status` column | High | Database | **RESOLVED** |
| DB-NEW-2 | No index on Email `classification` column | Medium | Database | **RESOLVED** |
| DB-NEW-3 | No index on Email `received_at` column | Medium | Database | **RESOLVED** |
| DB-NEW-4 | No composite index for user+status+received_at | Medium | Database | **RESOLVED** |
| DB-NEW-5 | No soft deletes on any model | Low | Database | |
| AGENT-NEW-1 | No timeout on LLM calls | High | Agent | **RESOLVED** |
| AGENT-NEW-2 | No input truncation in generate/decide nodes | Medium | Agent | |
| AGENT-NEW-3 | No per-node error recovery | Medium | Agent | **RESOLVED** |
| AGENT-NEW-4 | Gemini singleton is not config-rotation safe | Medium | Agent | |
| GMAIL-NEW-1 | Token refresh called on every API request | Medium | Gmail | **RESOLVED** |
| GMAIL-NEW-2 | No Gmail API rate limit handling | Medium | Gmail | **RESOLVED** |
| GMAIL-NEW-3 | No attachment handling | Low | Gmail | **RESOLVED** |
| GMAIL-NEW-4 | Email HTML not sanitized | Medium | Gmail | **RESOLVED** |
| TEST-NEW-1 | Zero frontend tests | High | Testing | |
| TEST-NEW-2 | No API route/integration tests | Medium | Testing | |
| TEST-NEW-3 | No load/performance tests | Low | Testing | |
| DOCKER-NEW-1 | No frontend container in docker-compose | Medium | Docker | **RESOLVED** |
| DOCKER-NEW-2 | Dockerfile is single-stage (not multi-stage) | Low | Docker | **RESOLVED** |
| DOCKER-NEW-3 | Source mounted read-only breaks hot-reload | Low | Docker | |
| DOCKER-NEW-4 | No Alembic migration on container startup | Medium | Docker | **RESOLVED** |
| CONFIG-NEW-1 | Encryption key tied to JWT secret | Medium | Config | **RESOLVED** |
| CONFIG-NEW-2 | No Redis pool configuration | Low | Config | **RESOLVED (Redis removed)** |
| CONFIG-NEW-3 | Missing Gmail credential validation in prod | Low | Config | |
| A11Y-NEW-1 | No skip-to-content links | Low | Accessibility | |
| A11Y-NEW-2 | CRM contact cards not keyboard accessible | Medium | Accessibility | **RESOLVED** |
| A11Y-NEW-3 | Draft list items not keyboard accessible | Medium | Accessibility | **RESOLVED** |
| MISC-NEW-1 | Date utils duplicated across pages | Low | Code Quality | **RESOLVED** |
| MISC-NEW-2 | Double commit pattern in process_email | Low | Code Quality | **RESOLVED** |
| MISC-NEW-3 | No graceful shutdown for background tasks | Medium | Reliability | |
| MISC-NEW-4 | Fernet instance recreated on every call | Low | Performance | **RESOLVED** |
| MISC-NEW-5 | Agent state lacks strong typing | Low | Code Quality | |
| FE-NEW-1 | No debounced search on CRM page | Medium | Frontend UX | |
| FE-NEW-2 | No in-flight request cancellation on search | Low | Frontend UX | **RESOLVED** |
| FE-NEW-3 | Inbox stats computed from current page only | Medium | Frontend UX | **RESOLVED** |
| FE-NEW-4 | No React error boundaries | Medium | Frontend UX | **RESOLVED** |
| FE-NEW-5 | No memoization on contact list | Low | Frontend Perf | **RESOLVED** |
| FE-NEW-6 | Draft emailId param not validated | Low | Frontend | **RESOLVED** |
| FE-NEW-7 | Traces page has no search/filtering | Low | Frontend UX | **RESOLVED** |
| FE-NEW-8 | Calendar page may not be in nav | Low | Frontend UX | **RESOLVED** |
| FE-NEW-9 | No prefers-reduced-motion support | Low | Accessibility | **RESOLVED** |
| FE-NEW-10 | QueryClient missing gcTime/refetchOnWindowFocus | Low | Frontend Perf | **RESOLVED** |
| FE-NEW-11 | CRM contact update doesn't invalidate list | Medium | Frontend | **RESOLVED** |
| FE-NEW-12 | No real-time inbox updates (no polling/WS consumer) | Medium | Frontend | **RESOLVED** |

---

## Grand Total

**Total Issues: 83 | Resolved: 53 | Partially Resolved: 1 | Open: 29**

| Severity | Total | Resolved |
|---|---|---|
| **Critical** | 7 | 5 |
| **High** | 4 | 3 |
| **Medium** | 40 | 26 |
| **Low** | 32 | 19 |

### Remaining Priority Fix Order

1. **Critical** (SEC-3) — JWT in localStorage remains an XSS token theft risk
2. **High** (TEST-NEW-1) — Zero frontend tests
3. **Medium open** — SEC-7 (CSRF), CRM-1 (production adapter), VAL-3 (batch ownership), ERR-1/ERR-2 (specific error handlers), FEAT-1 (Zustand), FEAT-3 (WS reconnection), FE-3 (auth state), FE-NEW-1 (CRM debounce), FE-NEW-4 (error boundaries), AGENT-NEW-2 (truncation), AGENT-NEW-4 (singleton), TEST-NEW-2 (API tests), MISC-NEW-3 (graceful shutdown)
4. **Low open** — Address opportunistically

---

# Phase 2: Deep System-Wide Audit

> Extended audit covering frontend performance, data fetching patterns, backend runtime bugs, database design, agent workflow, Gmail integration, testing gaps, Docker, and accessibility.
>
> **Audit Date:** 2026-02-20

---

## 9. Critical Runtime Bugs

### BE-NEW-1: GmailClient Instantiated Without Credentials — RESOLVED

- **Severity:** Critical
- **Location:** `backend/app/agent/nodes/dispatch.py:41-93`, `backend/app/agent/tools/registry.py:22-69`
- **Resolution:** `dispatch.py` now has `_get_user_credentials()` that fetches user OAuth credentials from the DB, decrypts them, refreshes if needed, and passes them to `GmailClient(credentials=credentials)`. Similarly, `registry.py` has `_get_credentials_from_user_id()` used by `send_email`, `create_draft`, `check_calendar`, and `create_event` tools.

### BE-NEW-2: Token Refresh Flow is Completely Broken — RESOLVED

- **Severity:** Critical
- **Location:** `backend/app/services/auth_service.py:71-80`, `frontend/src/lib/api.ts:36-55`
- **Resolution:**
  1. `auth_service.login()` now calls `create_refresh_token(token_data)` (line 73) and includes it in `TokenResponse` (line 77).
  2. Frontend stores the refresh token as `rf_refresh_token` in localStorage (`login/page.tsx:92-94`).
  3. Frontend sends the refresh token (not access token) to `/auth/refresh` (`api.ts:37,47,122,131`).

### BE-NEW-3: WebSocket Auth Parses Email as UUID — RESOLVED

- **Severity:** Critical
- **Location:** `backend/app/api/routes/notifications.py:111-120`
- **Resolution:** The WebSocket handler now looks up the user by email via DB query: `select(User).where(User.email == user_email)` and gets `user_id = user.id` from the result.

---

## 10. Frontend Performance & UX

### FE-NEW-1: No Search Debouncing on CRM Page

- **Severity:** Medium
- **Location:** `frontend/src/app/crm/page.tsx`
- **Problem:** CRM search triggers on form submit only (not on keystroke), and the contacts list (`useContacts()`) loads ALL contacts on mount with no pagination. For large contact databases, this will be slow and transfer excessive data.
- **Why it matters:** Unlike the Inbox page which has proper 300ms debounce, the CRM page has no debounced type-ahead search — users must click "Look Up" or press Enter.
- **Fix:** Add debounced search that passes the query to `useContacts(debouncedQuery)`, which already accepts an optional `query` parameter.

### FE-NEW-2: Inbox Search Debounce Missing Cancellation — RESOLVED

- **Severity:** Low
- **Location:** `frontend/src/app/inbox/page.tsx:63-75`, `frontend/src/hooks/use-emails.ts:10,18`
- **Resolution:** `queryClient.cancelQueries({ queryKey: ["emails"] })` is called before updating filters on new keystrokes. The `useEmails` hook passes `signal` from TanStack Query to the API call for proper `AbortController` cancellation.

### FE-NEW-3: Stats Computed from Current Page Only — RESOLVED

- **Severity:** Medium
- **Location:** `frontend/src/app/inbox/page.tsx:59`, `frontend/src/hooks/use-emails.ts:76-82`
- **Resolution:** `useEmailStats()` hook added that fetches from a dedicated `/emails/stats` endpoint. Inbox page uses `stats?.pending`, `stats?.needs_review`, `stats?.sent` for full-dataset counts.

### FE-NEW-4: No Error Boundaries — RESOLVED

- **Severity:** Medium
- **Location:** `frontend/src/components/error-boundary.tsx`
- **Resolution:** Class-based `ErrorBoundary` component created with `getDerivedStateFromError`, `componentDidCatch` logging, and a fallback UI with a refresh button.

### FE-NEW-5: No Memoization on Contact List Items — RESOLVED

- **Severity:** Low
- **Location:** `frontend/src/app/crm/page.tsx:39`
- **Resolution:** Contact card extracted into `const ContactCard = memo(function ContactCard({...})` using `React.memo`.

### FE-NEW-6: Drafts Page Uses URL Search Params Without Validation — RESOLVED

- **Severity:** Low
- **Location:** `frontend/src/app/drafts/page.tsx:93-107`
- **Resolution:** `isValidUUID()` regex validation function added. `emailId` is validated with `useMemo(() => isValidUUID(emailIdParam) ? emailIdParam : null, [emailIdParam])` before use.

### FE-NEW-7: Traces Page Has No Search or Filtering — RESOLVED

- **Severity:** Low
- **Location:** `frontend/src/app/traces/page.tsx:37-49,104-134`, `frontend/src/hooks/use-traces.ts:5-16`
- **Resolution:** Search input with 300ms debounce and `cancelQueries` added. Status filter dropdown with "completed", "failed", "processing" options. `useTraces` hook accepts `TraceFilters` with `search` and `status` params.

### FE-NEW-8: Calendar Page Missing from Navigation — RESOLVED

- **Severity:** Low
- **Location:** Navigation files: `top-nav.tsx:34`, `sidebar.tsx:27`, `header.tsx:9`
- **Resolution:** Calendar page is linked in top-nav, sidebar, and header navigation components.

### FE-NEW-9: Motion/Framer Animations on Every Page Load — RESOLVED

- **Severity:** Low
- **Location:** `frontend/src/hooks/use-reduced-motion.ts`, used in inbox, drafts, traces, login, register pages
- **Resolution:** `useReducedMotion()` hook created that listens to `prefers-reduced-motion` media query. All pages conditionally render with or without `motion.div` wrappers based on the hook's return value.

---

## 11. Frontend Data Fetching

### FE-NEW-10: QueryClient Has No `gcTime` Configured — RESOLVED

- **Severity:** Low
- **Location:** `frontend/src/providers/query-provider.tsx:13-14`
- **Resolution:** Explicit `gcTime: 5 * 60 * 1000` (5 minutes) and `refetchOnWindowFocus: false` configured in the default query options.

### FE-NEW-11: CRM Contact Update Doesn't Invalidate Contacts List — RESOLVED

- **Severity:** Medium
- **Location:** `frontend/src/hooks/use-crm.ts:47-54`
- **Resolution:** `useUpdateContact` `onSuccess` now invalidates both `["crm", "contact", variables.email]` (individual) and `["crm", "contacts"]` (list) caches.

### FE-NEW-12: No Polling or WebSocket Integration for Inbox — RESOLVED

- **Severity:** Medium
- **Location:** `frontend/src/hooks/use-emails.ts:5,28-29`
- **Resolution:** `POLLING_INTERVAL = 30000` (30s) added with `refetchInterval: POLLING_INTERVAL` and `refetchIntervalInBackground: false` on the emails query.

---

## 12. Backend API Design

### BE-NEW-4: Inefficient Email Count Query — RESOLVED

- **Severity:** Medium
- **Location:** `backend/app/services/email_service.py:57,72`
- **Resolution:** Count query now uses `select(func.count()).select_from(Email)` for SQL-level COUNT. No more loading all rows into Python memory.

### BE-NEW-5: Gmail Email Fetch Has No Pagination — RESOLVED

- **Severity:** Medium
- **Location:** `backend/app/integrations/gmail/client.py:172-177`
- **Resolution:** Concurrent message fetch with `asyncio.Semaphore(10)` and `asyncio.gather(*fetch_tasks, return_exceptions=True)` instead of serial loop. Rate limit handling with `tenacity` retry on 429.

### BE-NEW-6: Email Deduplication is N+1 — RESOLVED

- **Severity:** Medium
- **Location:** `backend/app/services/email_service.py:184-189`
- **Resolution:** Batch dedup using `select(Email.gmail_id).where(Email.gmail_id.in_(gmail_ids))` — single query instead of N individual SELECTs.

### BE-NEW-7: Graph Rebuilds on Every Email Process — RESOLVED

- **Severity:** Low
- **Location:** `backend/app/agent/graph.py:45-73,602`
- **Resolution:** `get_compiled_graph()` caches the compiled graph in module-level `_compiled_graph` with a double-check locking pattern using `_graph_lock`. `process_email()` calls `compiled = await get_compiled_graph(db=db_session)`.

---

## 13. Database Design

### DB-NEW-1: No Index on Email `status` Column — RESOLVED

- **Severity:** High
- **Location:** `backend/app/models/email.py:65-70`
- **Resolution:** `index=True` added to the `status` mapped_column.

### DB-NEW-2: No Index on Email `classification` Column — RESOLVED

- **Severity:** Medium
- **Location:** `backend/app/models/email.py:59-63`
- **Resolution:** `index=True` added to the `classification` mapped_column.

### DB-NEW-3: No Index on Email `received_at` Column — RESOLVED

- **Severity:** Medium
- **Location:** `backend/app/models/email.py:56-58`
- **Resolution:** `index=True` added to the `received_at` mapped_column.

### DB-NEW-4: No Composite Index for Common Query Pattern — RESOLVED

- **Severity:** Medium
- **Location:** `backend/app/models/email.py:43-45`
- **Resolution:** `__table_args__` added with composite `Index('ix_emails_user_status_received', 'user_id', 'status', 'received_at')`.

### DB-NEW-5: No Soft Deletes

- **Severity:** Low
- **Location:** All models
- **Problem:** No model has soft delete capability. Deleting a template, email, or user is a hard DELETE with no audit trail or recovery option.
- **Fix:** Add a `deleted_at: Mapped[datetime | None]` column to models that need it, with a default query filter.

---

## 14. Agent Workflow

### AGENT-NEW-1: No Timeout on LLM Calls — RESOLVED

- **Severity:** High
- **Location:** `backend/app/llm/client.py:35-63`
- **Resolution:** `GeminiClient` has `DEFAULT_TIMEOUT = 30` seconds. `_invoke()` wraps LLM calls with `asyncio.wait_for(self.llm.ainvoke(messages), timeout=self.timeout)`. Configurable via constructor param.

### AGENT-NEW-2: No Input Truncation for Long Emails

- **Severity:** Medium
- **Location:** `backend/app/agent/nodes/classify.py`, `generate.py`, `decide.py`
- **Problem:** The classify step truncates to 2000 chars (`email_service.py:284`), but the generate and decide nodes send the full email body to Gemini without truncation. Very long emails could exceed Gemini's context window or produce degraded output.
- **Fix:** Add consistent truncation across all LLM-calling nodes, or calculate token count and truncate to fit within model limits.

### AGENT-NEW-3: No Error Recovery Between Nodes — RESOLVED

- **Severity:** Medium
- **Location:** `backend/app/agent/graph.py:99-250,351-393`
- **Resolution:** `_wrap_node_with_error_handling()` wraps each node function. Critical nodes (classify, generate) raise `NodeError` to halt the pipeline. Recoverable nodes (retrieve, decide, execute, review, dispatch) return safe defaults via `_get_safe_defaults_for_node()`. Pipeline also uses `asyncio.wait_for()` with `AGENT_PIPELINE_TIMEOUT`.

### AGENT-NEW-4: Gemini Client is a Non-Thread-Safe Singleton

- **Severity:** Medium
- **Location:** `backend/app/llm/client.py:167-176`
- **Problem:** `get_gemini_client()` uses a module-level global singleton. If multiple emails are processed concurrently, they share the same `GeminiClient` instance. While `ainvoke` is async-safe, config changes (e.g., API key rotation) require a restart.
- **Fix:** Use a factory pattern per-request or use `contextvars` for isolation.

---

## 15. Gmail Integration

### GMAIL-NEW-1: Token Refresh Always Called Before Every API Request — RESOLVED

- **Severity:** Medium
- **Location:** `backend/app/integrations/gmail/client.py:89-92`
- **Resolution:** `_refresh_if_needed()` now checks `expires_at` and only refreshes if `time.time() >= expires_at - 60` (60-second buffer). If the token is still valid, it returns early.

### GMAIL-NEW-2: No Gmail API Rate Limit Handling — RESOLVED

- **Severity:** Medium
- **Location:** `backend/app/integrations/gmail/client.py:29-50,128-157`
- **Resolution:** `GmailRateLimitError` exception, `_get_retry_after` custom wait function respecting `Retry-After` header, `_check_rate_limit()` method, and `tenacity` `@retry` decorator (up to 3 attempts with exponential backoff) applied to `fetch_emails`, `get_email`, `_fetch_message`, `send_email`, and `create_draft`.

### GMAIL-NEW-3: No Attachment Handling — RESOLVED

- **Severity:** Low
- **Location:** `backend/app/integrations/gmail/client.py:309-345,367`
- **Resolution:** `_extract_attachments()` recursively searches payload parts for attachments, extracting metadata (filename, MIME type, size). Included in `_parse_message` return dict as `"attachments"`.

### GMAIL-NEW-4: Email HTML Not Sanitized — RESOLVED

- **Severity:** Medium
- **Location:** `backend/app/integrations/gmail/client.py:306`, `backend/app/utils/sanitize.py`
- **Resolution:** `_decode_body()` calls `sanitize_html(decoded)` which uses `bleach.clean()` with an allowlist of safe tags.

---

## 16. Testing Gaps

### TEST-NEW-1: No Frontend Tests

- **Severity:** High
- **Location:** `frontend/`
- **Problem:** There are zero frontend test files — no unit tests, no component tests, no integration tests. No testing framework (Jest, Vitest, Playwright) is configured.
- **Fix:** Set up Vitest + React Testing Library, and add tests for critical flows (auth, inbox, draft approval).

### TEST-NEW-2: No API Route/Integration Tests

- **Severity:** Medium
- **Location:** `backend/tests/`
- **Problem:** Tests exist for individual services and agent nodes, but there are no API endpoint tests (no `TestClient` usage against FastAPI routes). Middleware, auth guards, and request validation are untested at the HTTP layer.
- **Fix:** Add API endpoint tests using `httpx.AsyncClient` with `app` for each route group.

### TEST-NEW-3: No Load/Performance Tests

- **Severity:** Low
- **Location:** N/A
- **Problem:** No load testing setup exists. Given that the app makes external API calls (Gmail, Gemini) and runs background agent pipelines, performance characteristics under load are unknown.
- **Fix:** Add k6 or Locust load test scripts for critical paths.

---

## 17. Docker & Deployment

### DOCKER-NEW-1: No Frontend Container in Docker Compose — RESOLVED

- **Severity:** Medium
- **Location:** `docker-compose.yml:83-100`
- **Resolution:** Frontend service added with build context `./frontend`, port 3000, and `npm run dev` command.

### DOCKER-NEW-2: Dockerfile is Single-Stage (Not Multi-Stage) — RESOLVED

- **Severity:** Low
- **Location:** `backend/Dockerfile`
- **Resolution:** Dockerfile now has two stages: `FROM python:3.11-slim as builder` (installs dependencies) and `FROM python:3.11-slim as runtime` (copies only packages and app code, leaving build tools behind).

### DOCKER-NEW-3: Source Code Mounted Read-Only in Dev

- **Severity:** Low
- **Location:** `docker-compose.yml:77`
- **Problem:** `./backend/app:/app/app:ro` mounts the source code read-only. This prevents hot-reloading (uvicorn --reload) from working inside the container. Development workflow requires container rebuilds for code changes.
- **Fix:** Remove `:ro` for development, or add a separate `docker-compose.dev.yml` override.

### DOCKER-NEW-4: No Alembic Migration on Startup — RESOLVED

- **Severity:** Medium
- **Location:** `backend/Dockerfile:59,76`
- **Resolution:** `entrypoint.sh` copied into the image and set as `ENTRYPOINT`. Script runs `alembic upgrade head` before starting uvicorn.

---

## 18. Configuration

### CONFIG-NEW-1: No ENCRYPTION_KEY Separate from JWT_SECRET_KEY — RESOLVED

- **Severity:** Medium
- **Location:** `backend/app/core/config.py:43-44`, `backend/app/core/security.py:99`
- **Resolution:** Separate `ENCRYPTION_KEY` setting added (`Field(default="change-me-in-production")`). `_derive_fernet_key()` uses `settings.ENCRYPTION_KEY` instead of `JWT_SECRET_KEY`. Production validation checks both keys independently.

### CONFIG-NEW-2: No Redis Connection Pool Configuration

- **Severity:** Low
- **Status:** **RESOLVED** — Redis has been completely removed from the project. Rate limiting, event notifications, and batch job tracking now use in-memory alternatives. Dispatch idempotency uses PostgreSQL.

### CONFIG-NEW-3: Production Validation Only Warns on Missing Gmail Credentials

- **Severity:** Low
- **Location:** `backend/app/core/config.py:67-100`
- **Problem:** `validate_production()` checks `JWT_SECRET_KEY`, `ENCRYPTION_KEY`, `GEMINI_API_KEY`, and `DATABASE_URL` but does NOT check `GMAIL_CLIENT_ID` or `GMAIL_CLIENT_SECRET`. The app could start in production with no Gmail OAuth credentials.
- **Fix:** Add Gmail credential validation to `validate_production()`.

---

## 19. Accessibility

### A11Y-NEW-1: No Skip-to-Content Links

- **Severity:** Low
- **Location:** All pages
- **Problem:** No skip navigation links exist for keyboard users to jump past the sidebar/header to main content.
- **Fix:** Add a visually hidden "Skip to main content" link as the first focusable element.

### A11Y-NEW-2: Contact Cards Not Keyboard Accessible — RESOLVED

- **Severity:** Medium
- **Location:** `frontend/src/app/crm/page.tsx:46-59`
- **Resolution:** Contact cards now have `role="button"`, `tabIndex={0}`, and `onKeyDown` handler that triggers on Enter and Space keys.

### A11Y-NEW-3: Draft List Items Not Keyboard Accessible — RESOLVED

- **Severity:** Medium
- **Location:** `frontend/src/app/drafts/page.tsx:58-65`
- **Resolution:** `DraftListItem` now has `role="button"`, `tabIndex={0}`, and `onKeyDown` handler for Enter/Space keyboard navigation.

---

## 20. Miscellaneous

### MISC-NEW-1: `formatDate` Duplicated Across Pages — RESOLVED

- **Severity:** Low
- **Location:** `frontend/src/lib/date-utils.ts`
- **Resolution:** Shared `formatDate()`, `formatDateTime()`, and `getRelativeTime()` utilities extracted to `date-utils.ts` and imported in CRM, drafts, and other pages.

### MISC-NEW-2: `process_email` Commits Twice — RESOLVED

- **Severity:** Low
- **Location:** `backend/app/agent/graph.py`
- **Resolution:** The normal path uses `flush()` (not a commit — sends SQL within the transaction) followed by a single `commit()`. There is no double-commit pattern; the original concern was based on confusing `flush()` with `commit()`.

### MISC-NEW-3: No Graceful Shutdown for Background Agent Tasks

- **Severity:** Medium
- **Location:** `backend/app/main.py` and `backend/app/services/email_service.py`
- **Problem:** Background tasks (`_run_agent_pipeline`) are launched via FastAPI's `BackgroundTasks`. On server shutdown, these tasks are killed without waiting for completion. An email could be mid-processing when the server stops, leaving it stuck in `PROCESSING` status.
- **Fix:** Track active background tasks and wait for them during shutdown in the lifespan handler, or use a proper task queue (Celery/ARQ).

### MISC-NEW-4: Fernet Key Recreated on Every Call — RESOLVED

- **Severity:** Low
- **Location:** `backend/app/core/security.py:94-108`
- **Resolution:** Module-level `_fernet_instance = None` cached. `_get_fernet()` returns the cached instance or creates and caches a new one on first call.

### MISC-NEW-5: No Typing for Agent State

- **Severity:** Low
- **Location:** `backend/app/agent/state.py` (referenced by all nodes)
- **Problem:** `AgentState` is a `TypedDict` but many nodes access it via `.get()` with string keys and manual type assertions. This reduces type safety — typos in key names won't be caught by type checkers.
- **Fix:** Use typed accessors or validate state shape at node boundaries.

---

*Generated from application audit on 2026-02-20. Resolution review on 2026-02-21.*
