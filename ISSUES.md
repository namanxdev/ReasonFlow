# ReasonFlow — Application Audit & Issues Report

> Comprehensive audit of the ReasonFlow application covering security, rate limiting, validation, error handling, CRM integration, WebSocket, and frontend completeness.
>
> **Audit Date:** 2026-02-20

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

### SEC-1: Rate Limiting Defined but Not Applied

- **Severity:** Critical
- **Location:** `backend/app/api/middleware/rate_limit.py`
- **Problem:** A Redis-based sliding-window rate limiter is fully implemented (60 req/min default, configurable via `RATE_LIMIT_PER_MINUTE`). However, **no route or router uses `Depends(rate_limit)`**. The middleware is imported in `__init__.py` but never applied.
- **Impact:** Zero request throttling — the application is vulnerable to brute-force attacks, credential stuffing, and abuse.
- **Fix:** Apply `rate_limit` as a dependency on the main API router in `backend/app/api/router.py`, or at minimum on sensitive endpoints (`/auth/login`, `/auth/register`, `/emails/sync`, batch operations).

### SEC-2: Missing Security Headers

- **Severity:** Critical
- **Location:** `backend/app/main.py`
- **Problem:** No security headers are configured. Missing:
  - `X-Content-Type-Options: nosniff`
  - `X-Frame-Options: DENY`
  - `X-XSS-Protection: 1; mode=block`
  - `Strict-Transport-Security` (HSTS)
  - `Content-Security-Policy` (CSP)
  - `Referrer-Policy`
- **Impact:** Vulnerable to clickjacking, MIME-type sniffing, and XSS attacks.
- **Fix:** Add a custom middleware or use `starlette.middleware` to inject these headers on every response.

### SEC-3: JWT Token Stored in localStorage

- **Severity:** Critical
- **Location:** `frontend/src/lib/api.ts`
- **Problem:** Access tokens are stored in `localStorage`, which is accessible to any JavaScript running on the page. If an XSS vulnerability exists anywhere in the frontend, tokens can be stolen.
- **Impact:** Token theft via XSS attacks.
- **Fix:** Use `httpOnly` cookies for token storage with `SameSite=Strict` and `Secure` flags. Alternatively, keep tokens in memory only with a refresh token in an httpOnly cookie.

### SEC-4: CORS Configuration Too Permissive

- **Severity:** Medium
- **Location:** `backend/app/main.py:51-57`
- **Problem:** CORS middleware uses `allow_methods=["*"]` and `allow_headers=["*"]`. While origins are properly restricted, the wildcard methods/headers expand the attack surface unnecessarily.
- **Fix:** Restrict to specific methods (`GET, POST, PUT, DELETE, OPTIONS`) and specific headers (`Content-Type, Authorization`).

### SEC-5: Password Validation Mismatch

- **Severity:** Medium
- **Location:** Frontend `frontend/src/app/(auth)/login/page.tsx` vs backend registration schema
- **Problem:** Frontend login form validates password as minimum 6 characters, but backend registration requires minimum 8 characters. This creates an inconsistent user experience and a potential bypass path.
- **Fix:** Align both to 8 characters minimum.

### SEC-6: Default JWT Secret in Config

- **Severity:** Medium
- **Location:** `backend/app/core/config.py`
- **Problem:** `JWT_SECRET_KEY` defaults to `"change-me-in-production"`. While a production validator warns about this, the application still starts with the insecure default.
- **Fix:** Fail hard (raise exception) in production if `JWT_SECRET_KEY` is the default value, rather than just logging a warning.

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
| Implementation | Done | `backend/app/api/middleware/rate_limit.py` — Redis-based sliding window |
| Default limit | 60 req/min | Configurable via `RATE_LIMIT_PER_MINUTE` setting |
| Per-user tracking | Done | Uses user ID from JWT, falls back to IP for unauthenticated |
| 429 Response | Done | Returns `Retry-After` header |
| **Applied to routes** | **NOT DONE** | **No route uses `Depends(rate_limit)`** |

### What Needs to Happen

| ID | Task | Priority |
|---|---|---|
| RL-1 | Apply rate limiting globally to the API router | Critical |
| RL-2 | Add stricter limits on auth endpoints (e.g., 10 req/min for login) | High |
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
| ERR-3 | **No timeout handling** | Medium | Long-running agent processes have no timeout — can block indefinitely |
| ERR-4 | **No structured logging** | Medium | No request ID tracking, no correlation between related log entries |
| ERR-5 | **WebSocket errors unstructured** | Low | WebSocket notifications use raw text errors, not standardized format |

---

## 6. Missing Features

| ID | Feature | Severity | Details |
|---|---|---|---|
| FEAT-1 | **Empty Zustand stores** | Medium | `frontend/src/stores/` directory exists but is empty — no centralized auth state management, relies entirely on localStorage |
| FEAT-2 | **No WebSocket heartbeat** | Medium | `backend/app/api/routes/notifications.py` — long-lived connections can silently die without ping/pong frames |
| FEAT-3 | **No WebSocket reconnection** | Medium | Frontend has no exponential backoff reconnection logic for dropped connections |
| FEAT-4 | **Health check incomplete** | Low | `GET /health` only checks database — should also check Redis connectivity (critical for WebSocket and rate limiting) |
| FEAT-5 | **Forgot password flow not implemented** | Medium | Frontend login page has a "Forgot password?" link but it leads nowhere — no backend endpoint or email flow exists |
| FEAT-6 | **No idempotency keys** | Medium | Email dispatch has no idempotency protection — retries could send duplicate emails |
| FEAT-7 | **No request ID tracking** | Low | No middleware to generate/propagate request IDs for distributed tracing |
| FEAT-8 | **No OAuth token refresh rotation** | Medium | Gmail OAuth refresh tokens are stored but no automatic rotation or expiry check mechanism exists |
| FEAT-9 | **No event persistence** | Low | WebSocket events are ephemeral — if client disconnects, events are lost (no message queue/replay) |
| FEAT-10 | **No API versioning strategy** | Low | Routes use `/api/v1` prefix but no v2 migration plan or deprecation strategy exists |

---

## 7. Frontend Issues

| ID | Issue | Severity | Location |
|---|---|---|---|
| FE-1 | **No proactive token expiration check** | Medium | `frontend/src/lib/api.ts` — only refreshes on 401 response, doesn't check expiry before requests |
| FE-2 | **Silent auth failure redirect** | Low | Token refresh failures redirect to `/login` with no error message — users don't know why they were logged out |
| FE-3 | **No centralized auth state** | Medium | No Zustand store for auth — token, user info, and auth status scattered across localStorage and component state |
| FE-4 | **CRM update doesn't invalidate list** | Low | `frontend/src/hooks/use-crm.ts` — `useUpdateContact` only invalidates single contact cache, not the contacts list cache |

---

## 8. Production Readiness

### Checklist

| Area | Status | Notes |
|---|---|---|
| JWT Authentication | Partial | Working but default secret, no CSRF |
| Password Hashing | Done | bcrypt implementation |
| OAuth Token Encryption | Done | Fernet symmetric encryption |
| Rate Limiting | **Not Applied** | Implementation exists, not wired to routes |
| Security Headers | **Missing** | No X-Frame-Options, CSP, HSTS |
| Input Validation | Mostly Done | Minor gaps listed above |
| Error Handling | Mostly Done | Missing specific handlers |
| Health Check | Partial | DB only, no Redis |
| Logging | Basic | No structured logging or request IDs |
| Monitoring | **Missing** | No Prometheus/StatsD integration |
| Graceful Shutdown | **Missing** | No cleanup for background tasks |
| Database Migrations | Done | Alembic configured |
| Docker | Done | docker-compose available |
| CI/CD | Done | GitHub Actions configured |
| Tests | Good | Unit + integration tests for major features |

---

## Issue Summary Table

| ID | Issue | Severity | Category |
|---|---|---|---|
| SEC-1 | Rate limiting not applied to routes | **Critical** | Security |
| SEC-2 | Missing security headers | **Critical** | Security |
| SEC-3 | JWT in localStorage (XSS risk) | **Critical** | Security |
| SEC-4 | CORS too permissive | Medium | Security |
| SEC-5 | Password validation mismatch | Medium | Security |
| SEC-6 | Default JWT secret in config | Medium | Security |
| SEC-7 | No CSRF protection | Medium | Security |
| CRM-1 | No production CRM adapter | Medium | CRM |
| CRM-2 | No CRM config in settings | Low | CRM |
| CRM-3 | CRM email param not validated | Low | CRM |
| CRM-4 | Auto-populated contacts lack enrichment | Low | CRM |
| RL-1 | Rate limiting not wired to router | **Critical** | Rate Limiting |
| RL-2 | No stricter limits on auth endpoints | High | Rate Limiting |
| RL-3 | No email sending rate limits | Medium | Rate Limiting |
| VAL-1 | Timezone field unvalidated | Low | Validation |
| VAL-2 | CRM email path unvalidated | Low | Validation |
| VAL-3 | Batch emails ownership unchecked | Medium | Validation |
| VAL-4 | No email body size limit | Low | Validation |
| ERR-1 | No database error handlers | Medium | Error Handling |
| ERR-2 | No OAuth/Gmail error handlers | Medium | Error Handling |
| ERR-3 | No timeout handling | Medium | Error Handling |
| ERR-4 | No structured logging | Medium | Error Handling |
| FEAT-1 | Empty Zustand stores | Medium | Frontend |
| FEAT-2 | No WebSocket heartbeat | Medium | WebSocket |
| FEAT-3 | No WebSocket reconnection | Medium | WebSocket |
| FEAT-4 | Health check incomplete | Low | Infrastructure |
| FEAT-5 | Forgot password not implemented | Medium | Auth |
| FEAT-6 | No idempotency keys | Medium | Email |
| FEAT-7 | No request ID tracking | Low | Observability |
| FEAT-8 | No OAuth token refresh rotation | Medium | Auth |
| FEAT-9 | No event persistence | Low | WebSocket |
| FEAT-10 | No API versioning strategy | Low | Architecture |
| FE-1 | No proactive token expiry check | Medium | Frontend |
| FE-2 | Silent auth failure redirect | Low | Frontend |
| FE-3 | No centralized auth state store | Medium | Frontend |
| FE-4 | CRM cache invalidation incomplete | Low | Frontend |

---

**Total Issues (Phase 1): 34**
- Critical: 4
- High: 1
- Medium: 18
- Low: 11

---

# Phase 2: Deep System-Wide Audit

> Extended audit covering frontend performance, data fetching patterns, backend runtime bugs, database design, agent workflow, Gmail integration, testing gaps, Docker, and accessibility.
>
> **Audit Date:** 2026-02-20

---

## Table of Contents (Phase 2)

- [9. Critical Runtime Bugs](#9-critical-runtime-bugs)
- [10. Frontend Performance & UX](#10-frontend-performance--ux)
- [11. Frontend Data Fetching](#11-frontend-data-fetching)
- [12. Backend API Design](#12-backend-api-design)
- [13. Database Design](#13-database-design)
- [14. Agent Workflow](#14-agent-workflow)
- [15. Gmail Integration](#15-gmail-integration)
- [16. Testing Gaps](#16-testing-gaps)
- [17. Docker & Deployment](#17-docker--deployment)
- [18. Configuration](#18-configuration)
- [19. Accessibility](#19-accessibility)
- [20. Miscellaneous](#20-miscellaneous)
- [Combined Summary Table](#combined-summary-table)

---

## 9. Critical Runtime Bugs

These are bugs that would cause **runtime failures** in production.

### BE-NEW-1: GmailClient Instantiated Without Credentials

- **Severity:** Critical
- **Location:** `backend/app/agent/nodes/dispatch.py:63,98` and `backend/app/agent/tools/registry.py:78,107`
- **Problem:** In `dispatch_node`, `GmailClient()` is called with no arguments:
  ```python
  # dispatch.py line 63
  client = GmailClient()
  ```
  But `GmailClient.__init__` requires `credentials: dict[str, Any]` (`backend/app/integrations/gmail/client.py:21`). This will raise a `TypeError` at runtime. Same issue in `registry.py` for `send_email`, `create_draft`, `check_calendar`, and `create_event` tools.
- **Impact:** All auto-approved email dispatch and all agent tool executions fail immediately.
- **Fix:** Pass user OAuth credentials through the agent state or resolve from the database using `user_id` from the email record.

### BE-NEW-2: Token Refresh Flow is Completely Broken

- **Severity:** Critical
- **Location:** `backend/app/services/auth_service.py:68-75` (login) and `frontend/src/lib/api.ts:60-74` (refresh)
- **Problem:** Two compounding issues:
  1. **Login never issues a refresh token.** `auth_service.login()` only calls `create_access_token()` (line 69) — it never calls `create_refresh_token()`. The `TokenResponse` only contains an access token.
  2. **Frontend sends the access token to `/auth/refresh`.** The API interceptor (line 60-66) sends the current `rf_access_token` (which is an access token with `type: "access"`) to the refresh endpoint.
  3. **Backend rejects it.** `auth_service.refresh_token()` explicitly checks `payload.get("type") != "refresh"` (line 93) and rejects access tokens.

  Result: Users can never refresh their tokens. After the JWT expires (30 min default), they are silently logged out.
- **Fix:** Have `login()` also return a refresh token. Store it separately in the frontend (ideally in an httpOnly cookie). Send the refresh token (not access token) to `/auth/refresh`.

### BE-NEW-3: WebSocket Auth Parses Email as UUID

- **Severity:** Critical
- **Location:** `backend/app/api/routes/notifications.py:73-76`
- **Problem:** The JWT `sub` claim contains the user's **email address** (set in `auth_service.py:68` as `{"sub": user.email}`). But the WebSocket handler does:
  ```python
  user_id_str = payload.get("sub")
  user_id = UUID(user_id_str)  # line 76
  ```
  `UUID("user@example.com")` always raises `ValueError`, which is caught and closes the connection with `WS_CLOSE_INVALID_TOKEN`.
- **Impact:** Real-time notifications are completely non-functional for all users.
- **Fix:** Either change the JWT `sub` claim to use `user.id` (UUID), or change the WebSocket handler to use the email as-is and look up the user.

---

## 10. Frontend Performance & UX

### FE-NEW-1: No Search Debouncing on CRM Page

- **Severity:** Medium
- **Location:** `frontend/src/app/crm/page.tsx:61-67`
- **Problem:** CRM search triggers on form submit only (not on keystroke), but the contacts list (`useContacts()` on line 52) loads ALL contacts on mount with no pagination. For large contact databases, this will be slow and transfer excessive data.
- **Why it matters:** Unlike the Inbox page which has proper 300ms debounce (line 56-66), the CRM page has no debounced type-ahead search — users must click "Look Up" or press Enter.
- **Fix:** Add debounced search that passes the query to `useContacts(debouncedQuery)`, which already accepts an optional `query` parameter.

### FE-NEW-2: Inbox Search Debounce is Good but Missing Cancellation

- **Severity:** Low
- **Location:** `frontend/src/app/inbox/page.tsx:56-66`
- **Problem:** The inbox has a proper 300ms debounce via `setTimeout`/`clearTimeout`. However, there's no cancellation of in-flight API requests when new keystrokes arrive. With TanStack Query, previous queries keep running until the new one starts.
- **Fix:** Use `queryClient.cancelQueries()` before triggering a new search, or use `keepPreviousData: true` to prevent UI flicker.

### FE-NEW-3: Stats Computed from Current Page Only

- **Severity:** Medium
- **Location:** `frontend/src/app/inbox/page.tsx:163-164`
- **Problem:** Inbox stats (pending count, needs review count) are computed from the current page of emails only:
  ```typescript
  const pendingCount = emails.filter(e => e.status === "pending").length;
  const needsReviewCount = emails.filter(e => e.status === "needs_review").length;
  ```
  If the user has 500 emails but is viewing page 1 of 25, the stats only reflect those 25 emails, not the full dataset.
- **Fix:** Add status counts to the backend paginated response or create a dedicated stats endpoint.

### FE-NEW-4: No Error Boundaries

- **Severity:** Medium
- **Location:** All page components
- **Problem:** No React error boundaries exist anywhere in the application. If any component throws during rendering (e.g., accessing a property on undefined data), the entire page crashes with a blank screen. Only the Drafts page has a `Suspense` fallback (`drafts/page.tsx:302`), but that only handles loading, not errors.
- **Fix:** Add an `ErrorBoundary` component wrapping the main layout or each page section.

### FE-NEW-5: No Memoization on Contact List Items

- **Severity:** Low
- **Location:** `frontend/src/app/crm/page.tsx:167-207`
- **Problem:** Contact card items in the CRM grid are inline JSX, not wrapped in `React.memo`. When any state changes (search, edit form, etc.), all contact cards re-render even if their data hasn't changed.
- **Fix:** Extract the contact card into a memoized component.

### FE-NEW-6: Drafts Page Uses URL Search Params Without Validation

- **Severity:** Low
- **Location:** `frontend/src/app/drafts/page.tsx:102`
- **Problem:** `emailId` is read directly from `searchParams.get("emailId")` and used to filter drafts without validation. A malformed or injected query param won't cause a security issue but could produce confusing UI states.
- **Fix:** Validate that `emailId` is a valid UUID format before using it.

### FE-NEW-7: Traces Page Has No Search or Filtering

- **Severity:** Low
- **Location:** `frontend/src/app/traces/page.tsx`
- **Problem:** The traces page only has pagination — no search, no date range filter, no status filter. Users cannot find specific traces without scrolling through pages.
- **Fix:** Add at minimum a date range filter and search by email subject.

### FE-NEW-8: Calendar Page Missing from Audit (No Navigation)

- **Severity:** Low
- **Location:** `frontend/src/app/calendar/page.tsx`
- **Problem:** The calendar page exists but may not be accessible from the main navigation depending on sidebar configuration. Should verify it's linked in the app shell.

### FE-NEW-9: Motion/Framer Animations on Every Page Load

- **Severity:** Low
- **Location:** All pages using `StaggerContainer`/`StaggerItem`
- **Problem:** Every page uses stagger animations on load. While visually appealing, this adds latency to perceived content display and can feel sluggish on slower devices. There's no `prefers-reduced-motion` media query check.
- **Fix:** Respect `prefers-reduced-motion` by conditionally disabling animations.

---

## 11. Frontend Data Fetching

### FE-NEW-10: QueryClient Has No `gcTime` Configured

- **Severity:** Low
- **Location:** `frontend/src/providers/query-provider.tsx:9-15`
- **Problem:** The QueryClient only sets `staleTime: 30_000` and `retry: 1`. The default `gcTime` (garbage collection time, formerly `cacheTime`) is 5 minutes. For a real-time inbox application, stale data is shown for 30 seconds which is acceptable, but there's no `refetchOnWindowFocus` override — it defaults to `true`, which means every tab switch triggers API calls.
- **Fix:** Consider setting `refetchOnWindowFocus: false` for non-critical queries (traces, metrics) to reduce API load, or increase `staleTime` for slow-changing data.

### FE-NEW-11: CRM Contact Update Doesn't Invalidate Contacts List

- **Severity:** Medium
- **Location:** `frontend/src/hooks/use-crm.ts:47-50`
- **Problem:** `useUpdateContact` only invalidates the individual contact cache:
  ```typescript
  queryClient.invalidateQueries({
    queryKey: ["crm", "contact", variables.email],
  });
  ```
  The contacts list cache (`["crm", "contacts"]`) is NOT invalidated. After editing a contact's name or company, the contacts grid still shows the old data until the user manually refreshes.
- **Fix:** Add `queryClient.invalidateQueries({ queryKey: ["crm", "contacts"] });` to the `onSuccess` handler.

### FE-NEW-12: No Polling or WebSocket Integration for Inbox

- **Severity:** Medium
- **Location:** `frontend/src/hooks/use-emails.ts`
- **Problem:** The inbox relies entirely on manual sync button clicks to fetch new emails. There's no polling interval and no WebSocket consumer for real-time updates. The backend publishes `EMAIL_RECEIVED` events via WebSocket, but no frontend code subscribes to them.
- **Fix:** Either add `refetchInterval` to the emails query or implement a WebSocket client that invalidates the emails query when `EMAIL_RECEIVED` events arrive.

---

## 12. Backend API Design

### BE-NEW-4: Inefficient Email Count Query

- **Severity:** Medium
- **Location:** `backend/app/services/email_service.py:56-71`
- **Problem:** The count query fetches ALL matching rows into memory, then counts them in Python:
  ```python
  count_result = await db.execute(count_query)
  total = len(count_result.scalars().all())  # line 71
  ```
  This loads every matching `Email` ORM object just to count them. For 10,000+ emails, this is extremely wasteful.
- **Fix:** Use `select(func.count()).select_from(Email).where(...)` for a SQL-level COUNT query.

### BE-NEW-5: Gmail Email Fetch Has No Pagination

- **Severity:** Medium
- **Location:** `backend/app/integrations/gmail/client.py:57-77`
- **Problem:** `fetch_emails()` fetches up to `max_results=50` messages, then fetches each one individually in a serial loop (line 71-75). This makes 51 sequential HTTP requests (1 list + 50 detail). No batch API or parallelism is used.
- **Fix:** Use `asyncio.gather()` or `asyncio.Semaphore` to fetch message details concurrently, and support Gmail's `nextPageToken` for pagination beyond 50.

### BE-NEW-6: Email Deduplication is N+1

- **Severity:** Medium
- **Location:** `backend/app/services/email_service.py:178-181`
- **Problem:** During email sync, each email is deduplicated with a separate SELECT query:
  ```python
  for raw in raw_emails:
      existing_result = await db.execute(
          select(Email).where(Email.gmail_id == gmail_id)
      )
  ```
  For 50 emails, this executes 50 individual SELECT queries.
- **Fix:** Batch fetch all existing `gmail_id`s in one query: `select(Email.gmail_id).where(Email.gmail_id.in_(gmail_ids))`.

### BE-NEW-7: Graph Rebuilds on Every Email Process

- **Severity:** Low
- **Location:** `backend/app/agent/graph.py:326`
- **Problem:** `_build_graph(db=db_session)` is called inside `process_email()` for every single email. The graph is compiled from scratch each time. While `functools.partial` is lightweight, LangGraph compilation has overhead.
- **Fix:** Consider caching the compiled graph or making the db session injectable at invocation time rather than build time.

---

## 13. Database Design

### DB-NEW-1: No Index on Email `status` Column

- **Severity:** High
- **Location:** `backend/app/models/email.py:59-63`
- **Problem:** The `status` column on the `Email` model has no index:
  ```python
  status: Mapped[EmailStatus] = mapped_column(
      Enum(EmailStatus, ...),
      default=EmailStatus.PENDING,
      nullable=False,
  )
  ```
  But status is used as a filter in `list_emails()`, `classify_unclassified_emails()`, and the drafts listing. Without an index, these queries do full table scans.
- **Fix:** Add `index=True` to the `status` mapped_column.

### DB-NEW-2: No Index on Email `classification` Column

- **Severity:** Medium
- **Location:** `backend/app/models/email.py:54-57`
- **Problem:** Similar to status — `classification` is filtered frequently but has no index.
- **Fix:** Add `index=True` to the `classification` mapped_column.

### DB-NEW-3: No Index on Email `received_at` Column

- **Severity:** Medium
- **Location:** `backend/app/models/email.py:51-53`
- **Problem:** `received_at` is the default sort column for email listings but has no index. Sorting on an unindexed column is O(n log n) per query.
- **Fix:** Add `index=True` to the `received_at` mapped_column.

### DB-NEW-4: No Composite Index for Common Query Pattern

- **Severity:** Medium
- **Location:** `backend/app/models/email.py`
- **Problem:** The most common query pattern is `WHERE user_id = ? AND status = ? ORDER BY received_at DESC`. This needs a composite index `(user_id, status, received_at)` for optimal performance.
- **Fix:** Add a `__table_args__` with `Index('ix_emails_user_status_received', 'user_id', 'status', 'received_at')`.

### DB-NEW-5: No Soft Deletes

- **Severity:** Low
- **Location:** All models
- **Problem:** No model has soft delete capability. Deleting a template, email, or user is a hard DELETE with no audit trail or recovery option.
- **Fix:** Add a `deleted_at: Mapped[datetime | None]` column to models that need it, with a default query filter.

---

## 14. Agent Workflow

### AGENT-NEW-1: No Timeout on LLM Calls

- **Severity:** High
- **Location:** `backend/app/llm/client.py:49-56`
- **Problem:** The `_invoke()` method has retry logic (3 attempts, exponential backoff) but **no timeout** on individual LLM calls:
  ```python
  response = await self.llm.ainvoke(messages)
  ```
  If Gemini is slow or hangs, the agent pipeline blocks indefinitely. The retry logic will wait up to 10 seconds between retries but each call itself has no upper bound.
- **Fix:** Add `timeout` parameter to the `ChatGoogleGenerativeAI` constructor or wrap calls with `asyncio.wait_for()`.

### AGENT-NEW-2: No Input Truncation for Long Emails

- **Severity:** Medium
- **Location:** `backend/app/agent/nodes/classify.py`, `generate.py`, `decide.py`
- **Problem:** The classify step truncates to 2000 chars (`email_service.py:284`), but the generate and decide nodes send the full email body to Gemini without truncation. Very long emails could exceed Gemini's context window or produce degraded output.
- **Fix:** Add consistent truncation across all LLM-calling nodes, or calculate token count and truncate to fit within model limits.

### AGENT-NEW-3: No Error Recovery Between Nodes

- **Severity:** Medium
- **Location:** `backend/app/agent/graph.py:328-340`
- **Problem:** If any node in the pipeline fails, the entire graph execution fails with a generic exception. The catch block (line 330) sets status to `NEEDS_REVIEW` but doesn't record which node failed or allow partial retry. There's no checkpoint mechanism.
- **Fix:** Add per-node error handling that allows the pipeline to continue to the next meaningful state (e.g., if tool execution fails, still generate a response without tool context).

### AGENT-NEW-4: Gemini Client is a Non-Thread-Safe Singleton

- **Severity:** Medium
- **Location:** `backend/app/llm/client.py:160-168`
- **Problem:** `get_gemini_client()` uses a module-level global singleton. If multiple emails are processed concurrently (via FastAPI background tasks), they share the same `GeminiClient` instance. While `ainvoke` is async-safe, the singleton pattern means config changes (e.g., API key rotation) require a restart.
- **Fix:** Use a factory pattern per-request or use `contextvars` for isolation.

---

## 15. Gmail Integration

### GMAIL-NEW-1: Token Refresh Always Called Before Every API Request

- **Severity:** Medium
- **Location:** `backend/app/integrations/gmail/client.py:30-55`
- **Problem:** `_refresh_if_needed()` is called before every Gmail API call, but it **always** attempts a refresh regardless of whether the current token is expired:
  ```python
  async def _refresh_if_needed(self, client: httpx.AsyncClient) -> None:
      refresh_token = self._credentials.get("refresh_token")
      if not refresh_token:
          return
      response = await client.post(...)  # Always refreshes
  ```
  This wastes a network round-trip per API call. Google may also rate-limit or revoke tokens that are refreshed too aggressively.
- **Fix:** Track token expiry time and only refresh when the token is expired or close to expiring.

### GMAIL-NEW-2: No Gmail API Rate Limit Handling

- **Severity:** Medium
- **Location:** `backend/app/integrations/gmail/client.py`
- **Problem:** Gmail API has rate limits (250 quota units/second per user). The client has no rate limiting, no exponential backoff on 429 responses, and no quota tracking. If a user triggers a large sync, the app could hit rate limits and lose data.
- **Fix:** Add retry logic with exponential backoff for 429 responses, and respect the `Retry-After` header.

### GMAIL-NEW-3: No Attachment Handling

- **Severity:** Low
- **Location:** `backend/app/integrations/gmail/client.py:135-149`
- **Problem:** `_decode_body()` only extracts text content from emails. Attachments are completely ignored — no metadata, no storage, no indication to the user that an attachment exists. The agent has no context about attachments when generating responses.
- **Fix:** At minimum, extract attachment metadata (filename, MIME type, size) and include it in the email record.

### GMAIL-NEW-4: Email HTML Not Sanitized

- **Severity:** Medium
- **Location:** `backend/app/integrations/gmail/client.py:135-149`
- **Problem:** `_decode_body()` decodes the raw email body which may contain HTML. This HTML is stored directly in the database and could be rendered in the frontend. No sanitization (DOMPurify, bleach) is applied at any point.
- **Fix:** Sanitize HTML before storage or before frontend display. At minimum, strip HTML tags for the agent's text input.

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
  - Existing test files cover: agent nodes (7 files), services (5 files), gmail client (1 file), CRM routes (1 file)
  - Missing: auth routes, email routes, draft routes, trace routes, metrics routes, template routes, settings routes, batch routes, WebSocket
- **Fix:** Add API endpoint tests using `httpx.AsyncClient` with `app` for each route group.

### TEST-NEW-3: No Load/Performance Tests

- **Severity:** Low
- **Location:** N/A
- **Problem:** No load testing setup exists. Given that the app makes external API calls (Gmail, Gemini) and runs background agent pipelines, performance characteristics under load are unknown.
- **Fix:** Add k6 or Locust load test scripts for critical paths.

---

## 17. Docker & Deployment

### DOCKER-NEW-1: No Frontend Container in Docker Compose

- **Severity:** Medium
- **Location:** `docker-compose.yml`
- **Problem:** Docker Compose only defines `db`, `redis`, and `backend` services. The Next.js frontend has no container definition, meaning local development with Docker still requires running the frontend separately.
- **Fix:** Add a `frontend` service with the Next.js dev server or a production build.

### DOCKER-NEW-2: Backend Dockerfile is Single-Stage

- **Severity:** Low
- **Location:** `backend/Dockerfile`
- **Problem:** Despite the comment "Multi-stage build for optimized production image", it's actually a single-stage build. The `as base` alias is unused. Build tools (gcc, libpq-dev) remain in the final image, increasing its size.
- **Fix:** Add a proper second stage that copies only the installed packages and application code, leaving build tools behind.

### DOCKER-NEW-3: Source Code Mounted Read-Only in Dev

- **Severity:** Low
- **Location:** `docker-compose.yml:77`
- **Problem:** `./backend/app:/app/app:ro` mounts the source code read-only. This prevents hot-reloading (uvicorn --reload) from working inside the container. Development workflow requires container rebuilds for code changes.
- **Fix:** Remove `:ro` for development, or add a separate `docker-compose.dev.yml` override.

### DOCKER-NEW-4: No Alembic Migration on Startup

- **Severity:** Medium
- **Location:** `backend/Dockerfile:50`
- **Problem:** The CMD only runs uvicorn. Database migrations (`alembic upgrade head`) are not executed on container startup. The database could be out of sync with the application models.
- **Fix:** Add a startup script that runs migrations before starting the server, or use a Docker entrypoint script.

---

## 18. Configuration

### CONFIG-NEW-1: No ENCRYPTION_KEY Separate from JWT_SECRET_KEY

- **Severity:** Medium
- **Location:** `backend/app/core/security.py:82-85`
- **Problem:** The Fernet encryption key for OAuth tokens is derived from `JWT_SECRET_KEY` via SHA-256:
  ```python
  def _derive_fernet_key() -> bytes:
      digest = hashlib.sha256(settings.JWT_SECRET_KEY.encode()).digest()
      return base64.urlsafe_b64encode(digest)
  ```
  If `JWT_SECRET_KEY` is rotated (e.g., for security), ALL stored OAuth tokens become undecryptable. These are two different concerns that should use independent keys.
- **Fix:** Add a separate `ENCRYPTION_KEY` setting for Fernet encryption.

### CONFIG-NEW-2: No Redis Connection Pool Configuration

- **Severity:** Low
- **Location:** `backend/app/core/config.py`
- **Problem:** Redis URL is configured but there's no pool size, timeout, or retry configuration. Under load, Redis connections could exhaust.
- **Fix:** Add `REDIS_POOL_SIZE`, `REDIS_TIMEOUT` settings.

### CONFIG-NEW-3: Production Validation Only Warns on Missing Gmail Credentials

- **Severity:** Low
- **Location:** `backend/app/core/config.py:67-87`
- **Problem:** `validate_production()` checks `JWT_SECRET_KEY`, `GEMINI_API_KEY`, and `DATABASE_URL` but does NOT check `GMAIL_CLIENT_ID` or `GMAIL_CLIENT_SECRET`. The app could start in production with no Gmail OAuth credentials, causing all OAuth flows to fail silently.
- **Fix:** Add Gmail credential validation to `validate_production()`.

---

## 19. Accessibility

### A11Y-NEW-1: No Skip-to-Content Links

- **Severity:** Low
- **Location:** All pages
- **Problem:** No skip navigation links exist for keyboard users to jump past the sidebar/header to main content.
- **Fix:** Add a visually hidden "Skip to main content" link as the first focusable element.

### A11Y-NEW-2: Contact Cards Not Keyboard Accessible

- **Severity:** Medium
- **Location:** `frontend/src/app/crm/page.tsx:168-207`
- **Problem:** Contact cards use `<div onClick={...}>` without keyboard support. They have `cursor-pointer` but no `tabIndex`, `role="button"`, or `onKeyDown` handler. Keyboard-only users cannot select contacts.
- **Fix:** Use `<button>` elements or add `role="button"`, `tabIndex={0}`, and `onKeyDown` handler for Enter/Space.

### A11Y-NEW-3: Draft List Items Not Keyboard Accessible

- **Severity:** Medium
- **Location:** `frontend/src/app/drafts/page.tsx:70-97`
- **Problem:** Same as A11Y-NEW-2 — `DraftListItem` uses `<div onClick={...}>` without keyboard event handling or ARIA roles.
- **Fix:** Same approach — use semantic `<button>` or add appropriate ARIA attributes and keyboard handlers.

---

## 20. Miscellaneous

### MISC-NEW-1: `formatDate` Duplicated Across Pages

- **Severity:** Low
- **Location:** `frontend/src/app/crm/page.tsx:29-38`, `frontend/src/app/drafts/page.tsx:24-38`
- **Problem:** Date formatting utilities (`formatDate`, `getRelativeTime`) are implemented inline in individual page components rather than shared from a utility module.
- **Fix:** Extract to `frontend/src/lib/date-utils.ts` and import where needed.

### MISC-NEW-2: `process_email` Commits Twice

- **Severity:** Low
- **Location:** `backend/app/agent/graph.py:381-384` and `backend/app/core/database.py:35`
- **Problem:** `process_email()` explicitly calls `await db_session.commit()` at line 381, but the `get_db()` dependency already auto-commits on success (line 35). For emails processed via background tasks (which use their own session), this is fine, but the double-commit pattern is confusing and could mask issues.
- **Fix:** Document this clearly or standardize on one commit pattern.

### MISC-NEW-3: No Graceful Shutdown for Background Agent Tasks

- **Severity:** Medium
- **Location:** `backend/app/main.py:28-36` and `backend/app/services/email_service.py:319-358`
- **Problem:** Background tasks (`_run_agent_pipeline`) are launched via FastAPI's `BackgroundTasks`. On server shutdown, these tasks are killed without waiting for completion. An email could be mid-processing when the server stops, leaving it stuck in `PROCESSING` status. While there's recovery logic (line 339-357), it only runs within the same task — if the process is killed, the email stays stuck.
- **Fix:** Track active background tasks and wait for them during shutdown in the lifespan handler, or use a proper task queue (Celery/ARQ).

### MISC-NEW-4: Fernet Key Recreated on Every Call

- **Severity:** Low
- **Location:** `backend/app/core/security.py:88-89`
- **Problem:** `_get_fernet()` creates a new `Fernet` instance on every encrypt/decrypt call, deriving the key from scratch via SHA-256 each time.
- **Fix:** Cache the Fernet instance at module level (the key won't change during runtime).

### MISC-NEW-5: No Typing for Agent State

- **Severity:** Low
- **Location:** `backend/app/agent/state.py` (referenced by all nodes)
- **Problem:** `AgentState` is a `TypedDict` but many nodes access it via `.get()` with string keys and manual type assertions. This reduces type safety — typos in key names won't be caught by type checkers.
- **Fix:** Use typed accessors or validate state shape at node boundaries.

---

## Combined Summary Table

### Phase 1 Issues (34)

| ID | Issue | Severity | Category |
|---|---|---|---|
| SEC-1 | Rate limiting not applied to routes | **Critical** | Security |
| SEC-2 | Missing security headers | **Critical** | Security |
| SEC-3 | JWT in localStorage (XSS risk) | **Critical** | Security |
| SEC-4 | CORS too permissive | Medium | Security |
| SEC-5 | Password validation mismatch | Medium | Security |
| SEC-6 | Default JWT secret in config | Medium | Security |
| SEC-7 | No CSRF protection | Medium | Security |
| CRM-1 | No production CRM adapter | Medium | CRM |
| CRM-2 | No CRM config in settings | Low | CRM |
| CRM-3 | CRM email param not validated | Low | CRM |
| CRM-4 | Auto-populated contacts lack enrichment | Low | CRM |
| RL-1 | Rate limiting not wired to router | **Critical** | Rate Limiting |
| RL-2 | No stricter limits on auth endpoints | High | Rate Limiting |
| RL-3 | No email sending rate limits | Medium | Rate Limiting |
| VAL-1 | Timezone field unvalidated | Low | Validation |
| VAL-2 | CRM email path unvalidated | Low | Validation |
| VAL-3 | Batch emails ownership unchecked | Medium | Validation |
| VAL-4 | No email body size limit | Low | Validation |
| ERR-1 | No database error handlers | Medium | Error Handling |
| ERR-2 | No OAuth/Gmail error handlers | Medium | Error Handling |
| ERR-3 | No timeout handling | Medium | Error Handling |
| ERR-4 | No structured logging | Medium | Error Handling |
| FEAT-1 | Empty Zustand stores | Medium | Frontend |
| FEAT-2 | No WebSocket heartbeat | Medium | WebSocket |
| FEAT-3 | No WebSocket reconnection | Medium | WebSocket |
| FEAT-4 | Health check incomplete | Low | Infrastructure |
| FEAT-5 | Forgot password not implemented | Medium | Auth |
| FEAT-6 | No idempotency keys | Medium | Email |
| FEAT-7 | No request ID tracking | Low | Observability |
| FEAT-8 | No OAuth token refresh rotation | Medium | Auth |
| FEAT-9 | No event persistence | Low | WebSocket |
| FEAT-10 | No API versioning strategy | Low | Architecture |
| FE-1 | No proactive token expiry check | Medium | Frontend |
| FE-2 | Silent auth failure redirect | Low | Frontend |
| FE-3 | No centralized auth state store | Medium | Frontend |
| FE-4 | CRM cache invalidation incomplete | Low | Frontend |

### Phase 2 Issues (39)

| ID | Issue | Severity | Category |
|---|---|---|---|
| BE-NEW-1 | GmailClient instantiated without credentials | **Critical** | Runtime Bug |
| BE-NEW-2 | Token refresh flow completely broken | **Critical** | Runtime Bug |
| BE-NEW-3 | WebSocket parses email as UUID | **Critical** | Runtime Bug |
| BE-NEW-4 | Inefficient email count query (loads all rows) | Medium | Backend |
| BE-NEW-5 | Gmail fetch: 51 serial HTTP requests, no pagination | Medium | Backend |
| BE-NEW-6 | Email deduplication is N+1 | Medium | Backend |
| BE-NEW-7 | LangGraph recompiled per email | Low | Backend |
| DB-NEW-1 | No index on Email `status` column | High | Database |
| DB-NEW-2 | No index on Email `classification` column | Medium | Database |
| DB-NEW-3 | No index on Email `received_at` column | Medium | Database |
| DB-NEW-4 | No composite index for user+status+received_at | Medium | Database |
| DB-NEW-5 | No soft deletes on any model | Low | Database |
| AGENT-NEW-1 | No timeout on LLM calls | High | Agent |
| AGENT-NEW-2 | No input truncation in generate/decide nodes | Medium | Agent |
| AGENT-NEW-3 | No per-node error recovery | Medium | Agent |
| AGENT-NEW-4 | Gemini singleton is not config-rotation safe | Medium | Agent |
| GMAIL-NEW-1 | Token refresh called on every API request | Medium | Gmail |
| GMAIL-NEW-2 | No Gmail API rate limit handling | Medium | Gmail |
| GMAIL-NEW-3 | No attachment handling | Low | Gmail |
| GMAIL-NEW-4 | Email HTML not sanitized | Medium | Gmail |
| TEST-NEW-1 | Zero frontend tests | High | Testing |
| TEST-NEW-2 | No API route/integration tests | Medium | Testing |
| TEST-NEW-3 | No load/performance tests | Low | Testing |
| DOCKER-NEW-1 | No frontend container in docker-compose | Medium | Docker |
| DOCKER-NEW-2 | Dockerfile is single-stage (not multi-stage) | Low | Docker |
| DOCKER-NEW-3 | Source mounted read-only breaks hot-reload | Low | Docker |
| DOCKER-NEW-4 | No Alembic migration on container startup | Medium | Docker |
| CONFIG-NEW-1 | Encryption key tied to JWT secret | Medium | Config |
| CONFIG-NEW-2 | No Redis pool configuration | Low | Config |
| CONFIG-NEW-3 | Missing Gmail credential validation in prod | Low | Config |
| A11Y-NEW-1 | No skip-to-content links | Low | Accessibility |
| A11Y-NEW-2 | CRM contact cards not keyboard accessible | Medium | Accessibility |
| A11Y-NEW-3 | Draft list items not keyboard accessible | Medium | Accessibility |
| MISC-NEW-1 | Date utils duplicated across pages | Low | Code Quality |
| MISC-NEW-2 | Double commit pattern in process_email | Low | Code Quality |
| MISC-NEW-3 | No graceful shutdown for background tasks | Medium | Reliability |
| MISC-NEW-4 | Fernet instance recreated on every call | Low | Performance |
| MISC-NEW-5 | Agent state lacks strong typing | Low | Code Quality |
| FE-NEW-1 | No debounced search on CRM page | Medium | Frontend UX |
| FE-NEW-2 | No in-flight request cancellation on search | Low | Frontend UX |
| FE-NEW-3 | Inbox stats computed from current page only | Medium | Frontend UX |
| FE-NEW-4 | No React error boundaries | Medium | Frontend UX |
| FE-NEW-5 | No memoization on contact list | Low | Frontend Perf |
| FE-NEW-6 | Draft emailId param not validated | Low | Frontend |
| FE-NEW-7 | Traces page has no search/filtering | Low | Frontend UX |
| FE-NEW-8 | Calendar page may not be in nav | Low | Frontend UX |
| FE-NEW-9 | No prefers-reduced-motion support | Low | Accessibility |
| FE-NEW-10 | QueryClient missing gcTime/refetchOnWindowFocus | Low | Frontend Perf |
| FE-NEW-11 | CRM contact update doesn't invalidate list | Medium | Frontend |
| FE-NEW-12 | No real-time inbox updates (no polling/WS consumer) | Medium | Frontend |

---

## Grand Total

**Total Issues: 83**

| Severity | Phase 1 | Phase 2 | Total |
|---|---|---|---|
| **Critical** | 4 | 3 | **7** |
| **High** | 1 | 3 | **4** |
| **Medium** | 18 | 22 | **40** |
| **Low** | 11 | 21 | **32** |

### Priority Fix Order

1. **Critical runtime bugs** (BE-NEW-1, BE-NEW-2, BE-NEW-3) — These prevent core features from working at all
2. **Critical security** (SEC-1, SEC-2, SEC-3, RL-1) — Application is unprotected
3. **High severity** (DB-NEW-1, AGENT-NEW-1, TEST-NEW-1, RL-2) — Performance and reliability blockers
4. **Medium issues** — Address by category during feature sprints
5. **Low issues** — Address opportunistically

---

*Generated from application audit on 2026-02-20*
