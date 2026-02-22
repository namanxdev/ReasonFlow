# ReasonFlow — Agent Guide

This document provides comprehensive information for AI coding agents working on the ReasonFlow project.

## Project Overview

**ReasonFlow** is an autonomous inbox AI agent that helps professionals manage email overload. Unlike standard email clients that simply list unread messages, ReasonFlow actively works on emails by:

- **Classifying** incoming emails by intent (inquiry, meeting request, complaint, etc.)
- **Retrieving** relevant context from past emails, CRM data, and calendar
- **Generating** draft responses using Google Gemini via LangChain
- **Routing** low-confidence drafts to humans for approval
- **Dispatching** approved responses automatically

The core philosophy: *"Stop writing emails. Start approving them."*

## Technology Stack

### Backend
| Component | Technology | Version |
|-----------|------------|---------|
| Framework | FastAPI | 0.104.0+ |
| Agent Engine | LangGraph | 0.2.0+ |
| LLM Framework | LangChain + Google GenAI | 0.2.0+ / 1.0.0+ |
| LLM Provider | Google Gemini API | Latest |
| Database | PostgreSQL + pgvector | 14+ |
| ORM | SQLAlchemy (async) | 2.0.23+ |
| Migrations | Alembic | 1.13.0+ |
| Auth | JWT + bcrypt | - |

### Frontend
| Component | Technology | Version |
|-----------|------------|---------|
| Framework | Next.js | 16.1.6 |
| Language | TypeScript | 5.x |
| Styling | Tailwind CSS | 4.x |
| UI Components | shadcn/ui + Radix UI | Latest |
| State Management | Zustand | 5.x |
| Data Fetching | TanStack Query | 5.x |
| Charts | Recharts | 3.x |
| Animations | Framer Motion | 12.x |

## Project Structure

```
ReasonFlow/
├── backend/                    # FastAPI backend
│   ├── app/
│   │   ├── agent/              # LangGraph workflow engine
│   │   │   ├── nodes/          # Classification, retrieval, decision, generation, review
│   │   │   ├── state/          # Agent state definitions (TypedDict)
│   │   │   └── tools/          # Tool manager + tool implementations
│   │   ├── api/                # FastAPI routes + middleware
│   │   │   ├── middleware/     # Error handling, rate limiting
│   │   │   └── routes/         # Auth, emails, drafts, traces, metrics, calendar, CRM
│   │   ├── core/               # Config, database, security, dependencies
│   │   ├── integrations/       # Gmail, Calendar, CRM clients
│   │   │   ├── calendar/
│   │   │   ├── crm/
│   │   │   └── gmail/
│   │   ├── llm/                # Gemini client + prompts (via LangChain)
│   │   ├── models/             # SQLAlchemy models
│   │   ├── retrieval/          # Embeddings + vector search
│   │   ├── schemas/            # Pydantic request/response schemas
│   │   └── services/           # Business logic layer
│   ├── alembic/                # Database migrations
│   ├── tests/                  # Test suite
│   │   ├── integrations/       # Integration tests
│   │   └── services/           # Service unit tests
│   ├── pyproject.toml          # Project metadata and dependencies
│   ├── requirements.txt        # Dependency list
│   └── .env.example            # Environment variable template
│
├── frontend/                   # Next.js 14+ frontend
│   ├── src/
│   │   ├── app/                # App Router pages
│   │   │   ├── (auth)/         # Login, register
│   │   │   ├── (dashboard)/    # Inbox, drafts, metrics, traces
│   │   │   ├── auth/gmail/callback/  # OAuth callback
│   │   │   └── [feature]/      # Feature pages (inbox, drafts, calendar, crm, traces)
│   │   ├── components/         # UI components per feature
│   │   │   ├── draft-review/
│   │   │   ├── inbox/
│   │   │   ├── layout/
│   │   │   ├── metrics/
│   │   │   ├── trace-viewer/
│   │   │   └── ui/             # shadcn/ui base components
│   │   ├── hooks/              # React Query hooks
│   │   ├── lib/                # API client, utilities
│   │   ├── providers/          # QueryProvider, theme providers
│   │   ├── stores/             # Zustand state stores
│   │   └── types/              # TypeScript interfaces
│   ├── components.json         # shadcn/ui configuration
│   ├── next.config.ts          # Next.js configuration
│   └── package.json            # NPM dependencies
│
├── docs/                       # Documentation
│   ├── architecture/           # System design docs
│   └── features/               # Feature specifications
│
├── Makefile                    # Build and dev commands
└── README.md                   # Project overview
```

## Build and Development Commands

### Quick Start

```bash
# Start both backend and frontend concurrently
make dev
```

### Individual Services

```bash
# Backend only
make backend
# Or directly:
cd backend && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Frontend only
make frontend
# Or directly:
cd frontend && npm run dev
```

### Installation

```bash
# Install all dependencies
make install

# Or install separately:
# Backend
cd backend && pip install -e ".[dev]"

# Frontend
cd frontend && npm install
```

### Database Migrations

```bash
cd backend

# Create a new migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback one revision
alembic downgrade -1

# View current version
alembic current
```

### Cleanup

```bash
# Kill running dev processes (Windows)
make clean
```

## Testing

### Backend Tests

```bash
cd backend

# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_node_classify.py

# Run with verbose output
pytest -v
```

### Test Structure

- `tests/conftest.py` — Shared pytest fixtures
- `tests/test_*.py` — Unit tests for individual components
- `tests/services/` — Service layer tests
- `tests/integrations/` — Integration tests for external services

### Key Fixtures

- `sample_email` — Minimal email dict for agent testing
- `base_state` — Minimal AgentState for node tests
- `mock_db` — Async-compatible SQLAlchemy session mock

## Code Style Guidelines

### Python (Backend)

We use **Ruff** for linting and formatting with these settings:

```toml
[tool.ruff]
target-version = "py311"
line-length = 100

[tool.ruff.lint]
select = ["E", "F", "I", "N", "W", "UP"]
```

Key conventions:
- **Line length**: 100 characters
- **Imports**: Sorted with `isort` rules (E, F, I, N, W, UP)
- **Type hints**: Use `from __future__ import annotations` for forward references
- **Async**: Prefer `async`/`await` for I/O operations
- **Docstrings**: Google-style docstrings for public functions

Run linting:
```bash
cd backend
ruff check .
ruff check . --fix  # Auto-fix issues
```

### TypeScript (Frontend)

- **Strict mode**: Enabled in `tsconfig.json`
- **Components**: Use functional components with explicit return types
- **Imports**: Use `@/` alias for project imports
- **Formatting**: Follow shadcn/ui conventions

## Environment Setup

### Required Environment Variables

Create `backend/.env` from `backend/.env.example`:

```bash
# Database
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/reasonflow

# Google Gemini API
GEMINI_API_KEY=your-gemini-api-key-here

# Gmail OAuth
GMAIL_CLIENT_ID=your-gmail-client-id
GMAIL_CLIENT_SECRET=your-gmail-client-secret
GMAIL_REDIRECT_URI=http://localhost:8000/api/v1/auth/gmail/callback

# JWT
JWT_SECRET_KEY=your-super-secret-jwt-key-change-in-production
JWT_ALGORITHM=HS256
JWT_EXPIRATION_MINUTES=30

# CORS
CORS_ORIGINS=["http://localhost:3000"]

# App
APP_ENV=development
APP_DEBUG=true
```

Create `frontend/.env.local` from `frontend/.env.example`:

```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### External Services Required

1. **PostgreSQL** with pgvector extension
2. **Google Gemini API** key
3. **Gmail OAuth** credentials (for email integration)

## Architecture Overview

### Agent Workflow (LangGraph)

The core email processing pipeline consists of 7 nodes:

```
START → classify → retrieve → decide → [execute] → generate → review → [dispatch/human_queue] → END
```

1. **classify** — Classify email intent (inquiry, meeting_request, complaint, etc.)
2. **retrieve** — Fetch relevant context from vector store
3. **decide** — Decide which tools to invoke
4. **execute** — Execute selected tools (optional, based on decision)
5. **generate** — Generate draft response using Gemini
6. **review** — Review confidence and determine if human approval needed
7. **dispatch** — Send approved responses OR **human_queue** — Queue for review

Conditional routing:
- Spam with confidence >= 0.8 → short-circuit to END
- No tools selected → skip execute node
- requires_approval=True → route to human_queue

### Database Schema

**Core Tables**:
- `users` — User accounts with OAuth tokens
- `emails` — Emails from Gmail with classification and status
- `agent_logs` — Step-by-step execution traces
- `tool_executions` — Individual tool call records
- `embeddings` — Vector embeddings for similarity search (pgvector)

**Email Status Enum**:
`pending` → `processing` → `drafted`/`needs_review` → `approved` → `sent`

### API Structure

All API routes under `/api/v1/`:

| Route | Description |
|-------|-------------|
| `/auth/*` | Authentication (register, login, Gmail OAuth) |
| `/emails/*` | Email CRUD and processing |
| `/drafts/*` | Draft review workflow |
| `/traces/*` | Agent execution traces |
| `/metrics/*` | Analytics metrics |
| `/calendar/*` | Google Calendar integration |
| `/crm/*` | CRM contacts management |

### Frontend Structure

**Routing** (Next.js App Router):
- `/` → redirects to `/inbox`
- `/inbox` — Email inbox view
- `/drafts` — Draft review queue
- `/traces` — Execution traces list
- `/traces/[traceId]` — Individual trace viewer
- `/metrics` — Analytics dashboard
- `/calendar` — Calendar integration view
- `/crm` — CRM contacts view
- `/login`, `/register` — Authentication

**State Management**:
- **Zustand**: Client-side UI state (auth, filters, modals)
- **TanStack Query**: Server state (emails, drafts, metrics, traces)

## Security Considerations

1. **Authentication**: JWT-based with configurable expiration
2. **Authorization**: OAuth tokens encrypted at rest using Fernet
3. **Rate Limiting**: In-memory sliding window (60 req/min default)
4. **Input Validation**: Pydantic on all API endpoints
5. **CORS**: Restricted to configured origins
6. **Secrets**: Stored exclusively in environment variables
7. **SQL Injection**: Prevented via SQLAlchemy ORM

### Security Headers

FastAPI includes security middleware:
- CORS validation
- Rate limiting per IP/user
- Request size limits

## Common Tasks

### Adding a New Agent Node

1. Create file in `backend/app/agent/nodes/my_node.py`
2. Implement async function: `async def my_node(state: AgentState) -> dict[str, Any]`
3. Add to `backend/app/agent/nodes/__init__.py`
4. Register in `backend/app/agent/graph.py`:
   - Add import
   - Add `graph.add_node("my_node", my_node)`
   - Add edges with `graph.add_edge()` or `graph.add_conditional_edges()`
5. Add tests in `backend/tests/test_node_my_node.py`

### Adding a New API Endpoint

1. Create or edit file in `backend/app/api/routes/`
2. Add Pydantic schemas in `backend/app/schemas/`
3. Include router in `backend/app/api/router.py`
4. Add tests in `backend/tests/services/` or `backend/tests/integrations/`

### Adding a Frontend Page

1. Create route directory in `frontend/src/app/my-page/`
2. Add `page.tsx` with component
3. Add API hooks in `frontend/src/hooks/`
4. Add components in `frontend/src/components/my-page/`
5. Update navigation in layout components

### Adding a Database Migration

```bash
cd backend
alembic revision --autogenerate -m "add new table"
# Edit generated migration if needed
alembic upgrade head
```

## Performance Targets

| Metric | Target | Strategy |
|--------|--------|----------|
| API latency | < 300ms | Async I/O, connection pooling |
| Agent full cycle | < 4s | Parallel tool execution, optimized prompts |
| Dashboard load | < 1s | SSR, React Query prefetching |

## Troubleshooting

### Common Issues

**Database connection errors**:
- Verify PostgreSQL is running
- Check `DATABASE_URL` in `.env`
- Ensure pgvector extension is installed

**Gemini API errors**:
- Verify `GEMINI_API_KEY` is set and valid
- Check Google Cloud Console for quota limits

**OAuth failures**:
- Verify Gmail OAuth credentials
- Check redirect URI matches exactly

### Debug Mode

Set `APP_DEBUG=true` in backend `.env` to enable:
- Swagger UI at `/docs`
- ReDoc at `/redoc`
- Detailed error messages

## Resources

- [System Architecture](docs/architecture/system-overview.md)
- [Database Schema](docs/architecture/database-schema.md)
- [Agent Workflow](docs/architecture/agent-workflow.md)
- [API Reference](docs/architecture/api-reference.md)
- [FastAPI Docs](https://fastapi.tiangolo.com/)
- [LangGraph Docs](https://langchain-ai.github.io/langgraph/)
- [Next.js Docs](https://nextjs.org/docs)
- [shadcn/ui Docs](https://ui.shadcn.com/)

---

*Last updated: 2026-02-19*
