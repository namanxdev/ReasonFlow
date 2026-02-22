# ReasonFlow Implementation Plan

> **Use this when your rate limit resets.** Run tasks sequentially or in parallel groups as marked.

---

## What's Done vs What's Left

### ✅ DONE: Folder Structure
The agents created all directories before the rate limit hit:
```
backend/app/agent/nodes/     backend/app/integrations/gmail/
backend/app/agent/state/     backend/app/integrations/calendar/
backend/app/agent/tools/     backend/app/integrations/crm/
backend/app/api/routes/      backend/app/retrieval/
backend/app/api/middleware/  backend/app/evaluation/
backend/app/core/            backend/app/models/
backend/app/schemas/         backend/app/services/
backend/tests/               backend/alembic/versions/

frontend/src/app/(dashboard)/   frontend/src/components/inbox/
frontend/src/app/(auth)/        frontend/src/components/draft-review/
frontend/src/app/api/           frontend/src/components/metrics/
frontend/src/components/ui/     frontend/src/components/trace-viewer/
frontend/src/hooks/             frontend/src/stores/
frontend/src/lib/               frontend/src/types/

docker/  .github/workflows/  docs/features/  docs/architecture/
```

### ❌ NOT DONE: All code files
**Every folder is empty.** No .py, .ts, .tsx, .json, or config files were created.
**You need to start from Task 1.1 (Phase 1).**

---

## Overview

**App:** Autonomous Inbox AI Agent  
**Stack:** FastAPI + LangGraph + Gemini (backend) | Next.js + shadcn (frontend) | PostgreSQL + pgvector (database)

---

## Phase 1: Foundation (Sequential - Do First)

### Task 1.1: Project Setup
```
/agent Builder-Agent

Set up the Python backend project:
- Create pyproject.toml with dependencies: fastapi, langchain, langgraph, google-generativeai, pydantic, sqlalchemy, asyncpg, redis, httpx, tenacity
- Create app/main.py with FastAPI app
- Create app/core/config.py for settings (Pydantic BaseSettings)
- Create .env.example with: DATABASE_URL, GEMINI_API_KEY, GMAIL_CLIENT_ID, GMAIL_CLIENT_SECRET
- Create Dockerfile for backend

Test: `uvicorn app.main:app --reload` runs without errors
```

### Task 1.2: Database Models
```
/agent Builder-Agent

Create SQLAlchemy models in app/models/:
- user.py: User (id, email, oauth_token_encrypted, created_at)
- email.py: Email (id, user_id, gmail_id, subject, body, sender, received_at, classification, status)
- agent_log.py: AgentLog (id, email_id, step_name, input_state, output_state, latency_ms, created_at)
- tool_execution.py: ToolExecution (id, agent_log_id, tool_name, params, result, success, created_at)

Create alembic migrations.
Test: Migrations run, tables created.
```

### Task 1.3: Frontend Setup
```
/agent Builder-Agent

Set up Next.js frontend:
- npx create-next-app@latest frontend --typescript --tailwind --app
- Install: shadcn/ui, zustand, @tanstack/react-query, axios
- Create src/lib/api.ts for API client
- Create src/providers/query-provider.tsx
- Set up basic layout with sidebar

Test: `npm run dev` runs, shows blank dashboard
```

---

## Phase 2: Core Features (Parallel Group A)

> **Run these 3 in parallel** - they don't share files

### Task 2.1: Gmail Integration (Terminal 1)
```
/agent Builder-Agent

Build Gmail OAuth + email fetching in app/integrations/gmail/:
- oauth.py: OAuth2 flow (get_auth_url, exchange_code, refresh_token)
- client.py: GmailClient class with:
  - fetch_emails(max_results=50) → List[Email]
  - send_email(to, subject, body)
  - create_draft(to, subject, body)
- schemas.py: Pydantic models for Gmail API responses

API routes in app/api/routes/gmail.py:
- GET /auth/gmail/url → returns OAuth URL
- POST /auth/gmail/callback → exchanges code
- GET /emails → fetches recent emails
- POST /emails/send
- POST /emails/draft

Test: Can authenticate and fetch emails from test Gmail account
```

### Task 2.2: LangGraph Agent Engine (Terminal 2)
```
/agent Builder-Agent

Build the agent workflow in app/agent/:
- state.py: AgentState TypedDict with email, classification, context, draft, tools_used, requires_approval
- nodes/classify.py: ClassificationNode - calls Gemini to classify intent (inquiry, meeting_request, complaint, etc.)
- nodes/retrieve.py: RetrievalNode - fetches relevant context
- nodes/decide.py: DecisionNode - picks tools to use
- nodes/generate.py: GenerationNode - generates email response
- nodes/review.py: ReviewNode - routes to human approval if confidence < 0.8
- graph.py: Build LangGraph StateGraph connecting all nodes

Test: Can process a sample email through the full graph
```

### Task 2.3: Gemini LLM Service (Terminal 3)
```
/agent Builder-Agent

Build Gemini integration in app/llm/:
- client.py: GeminiClient class wrapping google.generativeai
  - classify_intent(email_body) → {"intent": str, "confidence": float}
  - generate_response(email, context) → str
  - extract_entities(text) → {"dates": [], "people": [], "topics": []}
- prompts.py: All prompt templates
- schemas.py: Pydantic models for LLM outputs

Test: Each method returns valid structured output
```

---

## Phase 2: Tests (Parallel Group B - After Group A)

> **Run after Group A completes**

### Task 2.4: Backend Tests (Terminal 1)
```
/agent test-generator

Write tests for:
- app/integrations/gmail/client.py (mock Gmail API)
- app/agent/nodes/*.py (each node)
- app/llm/client.py (mock Gemini responses)

Use pytest with pytest-asyncio. Mock external APIs.
```

### Task 2.5: Review Group A (Terminal 2)
```
/agent pr-security-reviewer

Review all code from Phase 2 Group A:
- Check for hardcoded secrets
- OAuth token handling security
- SQL injection in queries
- Input validation on API routes
```

---

## Phase 3: Retrieval & Vector Search (Sequential)

### Task 3.1: Embedding + Vector Storage
```
/agent Builder-Agent

Build retrieval module in app/retrieval/:
- embeddings.py: EmbeddingService using Gemini embeddings API
- vector_store.py: PgVectorStore class
  - store_embedding(text, metadata)
  - search_similar(query, top_k=5)
- context_builder.py: ContextBuilder
  - build_context(email) → relevant past emails + CRM data

Database: Add pgvector extension, create embeddings table

Test: Can embed text and retrieve similar items
```

---

## Phase 4: Additional Integrations (Parallel Group C)

### Task 4.1: Calendar Integration (Terminal 1)
```
/agent Builder-Agent

Build Google Calendar integration in app/integrations/calendar/:
- client.py: CalendarClient
  - get_free_slots(start, end) → List[TimeSlot]
  - create_event(title, start, end, attendees)
  - check_conflicts(proposed_time) → bool

API routes:
- GET /calendar/availability
- POST /calendar/events

Test: Can check availability and create events
```

### Task 4.2: CRM Integration (Terminal 2)
```
/agent Builder-Agent

Build CRM abstraction in app/integrations/crm/:
- base.py: CRMBase abstract class
- mock_crm.py: MockCRM for testing
- client.py: get_contact(email), update_contact(email, data)

API routes:
- GET /crm/contacts/{email}
- POST /crm/contacts/{email}

Test: Can fetch and update contact data
```

---

## Phase 5: Frontend Dashboard (Parallel Group D)

### Task 5.1: Inbox Dashboard (Terminal 1)
```
/agent Builder-Agent

Build inbox UI in frontend/src/app/(dashboard)/inbox/:
- page.tsx: Email list with classification badges
- components/email-list.tsx: Sortable/filterable list
- components/email-card.tsx: Single email preview
- hooks/use-emails.ts: React Query hook for fetching

Features:
- Show classification tag (Meeting, Inquiry, Complaint, etc.)
- Status indicator (Pending, Drafted, Sent, Needs Review)
- Click to open detail panel
```

### Task 5.2: Draft Review Panel (Terminal 2)
```
/agent Builder-Agent

Build draft review UI in frontend/src/app/(dashboard)/draft/:
- page.tsx: Draft editor with AI-generated response
- components/draft-editor.tsx: Rich text editor
- components/approval-buttons.tsx: Accept/Edit/Reject buttons
- hooks/use-draft.ts: Mutation for approving/rejecting

Features:
- Show original email
- Show AI draft
- Edit before sending
- One-click approve
```

### Task 5.3: Metrics Dashboard (Terminal 3)
```
/agent Builder-Agent

Build metrics UI in frontend/src/app/(dashboard)/metrics/:
- page.tsx: Dashboard with charts
- components/intent-chart.tsx: Pie chart of classifications
- components/latency-chart.tsx: Line chart of response times
- components/accuracy-chart.tsx: Tool success rate

Use: recharts or similar charting library
```

---

## Phase 6: Agent Trace Viewer (Sequential)

### Task 6.1: Trace UI
```
/agent Builder-Agent

Build agent trace viewer in frontend/src/app/(dashboard)/traces/:
- page.tsx: List of recent agent runs
- [traceId]/page.tsx: Detail view of single run
- components/trace-graph.tsx: Visualize LangGraph steps as flowchart
- components/step-detail.tsx: Show input/output of each node

Backend API:
- GET /traces → List[Trace]
- GET /traces/{id} → single trace with all steps
```

---

## Phase 7: Polish & Security (Sequential)

### Task 7.1: Auth Middleware
```
/agent Builder-Agent

Add authentication in app/api/middleware/:
- auth.py: JWT validation middleware
- rate_limit.py: Rate limiting middleware (use Redis)

Apply to all routes except /auth/*
```

### Task 7.2: Final Security Review
```
/agent pr-security-reviewer

Full security audit:
- OAuth token encryption at rest
- API rate limiting
- Input validation on all endpoints
- No secrets in code
- CORS configuration
```

---

## Phase 8: Deployment (Sequential)

### Task 8.1: Docker + CI/CD
```
/agent Builder-Agent

Create deployment configs:
- docker-compose.yml (backend, postgres, redis)
- .github/workflows/ci.yml (lint, test, build)
- .github/workflows/deploy.yml (deploy to Railway/Render)
- frontend/vercel.json

Test: `docker-compose up` runs full stack locally
```

---

## Quick Reference

| Phase | Tasks | Parallel? | Est. Time |
|-------|-------|-----------|-----------|
| 1 | 1.1, 1.2, 1.3 | No | 1-2 hours |
| 2A | 2.1, 2.2, 2.3 | **Yes** | 2-3 hours |
| 2B | 2.4, 2.5 | **Yes** | 30 min |
| 3 | 3.1 | No | 1 hour |
| 4 | 4.1, 4.2 | **Yes** | 1 hour |
| 5 | 5.1, 5.2, 5.3 | **Yes** | 2-3 hours |
| 6 | 6.1 | No | 1 hour |
| 7 | 7.1, 7.2 | No | 1 hour |
| 8 | 8.1 | No | 30 min |

**Total: ~10-12 hours**

---

## Rate Limit Tips

1. **Don't run more than 3 agents in parallel** - you burned through your limit fast
2. **Run sequential phases... sequentially** - don't rush
3. **Use Haiku agents (tester, reviewer, fixer) for small tasks** - cheaper
4. **Save Opus (architect) for big planning only** - expensive

---

## Commands Cheat Sheet

```bash
# Plan something big
/agent architect-opus

# Build a feature
/agent Builder-Agent

# Write tests
/agent test-generator

# Review code
/agent pr-security-reviewer

# Fix small issues
/agent quick-fixer
```
