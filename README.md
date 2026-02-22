# ReasonFlow — Autonomous Inbox AI Agent

> Intelligent email processing powered by LangGraph + Gemini, with human-in-the-loop approval workflows.

## Overview

ReasonFlow is a full-stack autonomous inbox agent that:
- **Classifies** incoming emails by intent (inquiry, meeting request, complaint, etc.)
- **Retrieves** relevant context from past emails, CRM data, and calendar
- **Generates** draft responses using Google Gemini via LangChain
- **Routes** low-confidence drafts to humans for approval
- **Dispatches** approved responses automatically

## Tech Stack

| Layer | Technology |
|-------|-----------|
| **Backend** | FastAPI, LangGraph, LangChain + Gemini, SQLAlchemy |
| **Frontend** | Next.js 14 (App Router), shadcn/ui, Zustand, TanStack Query |
| **Database** | PostgreSQL + pgvector |
| **LLM** | Google Gemini API (via langchain-google-genai) |

## Architecture

```
┌─────────────┐     ┌──────────────────────────────────────────┐
│   Next.js   │────▶│              FastAPI Backend              │
│  Dashboard  │◀────│                                          │
└─────────────┘     │  ┌─────────┐  ┌──────────┐  ┌────────┐  │
                    │  │  Agent   │  │Retrieval │  │  APIs  │  │
                    │  │ Engine   │  │ Module   │  │        │  │
                    │  │(LangGraph│  │(pgvector)│  │Gmail   │  │
                    │  │+ Gemini) │  │          │  │Calendar│  │
                    │  └─────────┘  └──────────┘  │CRM     │  │
                    │                              └────────┘  │
                    └──────────────────────────────────────────┘
                                    │
                    ┌───────────────┼───────────────┐
                    │               │               │
               PostgreSQL        External
               + pgvector        APIs
```

## Agent Workflow

```
Email Input → Classification → Context Retrieval → Decision
    → Tool Execution → Response Generation → Human Review → Dispatch
```

Each step is a LangGraph node with full observability and state tracking.

## Quick Start

### Backend

```bash
cd backend
pip install -e ".[dev]"
cp .env.example .env
# Edit .env with your credentials
alembic upgrade head
uvicorn app.main:app --reload
```

### Frontend

```bash
cd frontend
npm install
cp .env.example .env.local
npm run dev
```

### Docker (Full Stack)

```bash
docker compose -f docker/docker-compose.yml up --build
```

## Project Structure

```
backend/
├── app/
│   ├── agent/          # LangGraph workflow engine
│   │   ├── nodes/      # Classification, retrieval, decision, generation, review
│   │   ├── state/      # Agent state definitions
│   │   └── tools/      # Tool manager + tool implementations
│   ├── api/            # FastAPI routes + middleware
│   ├── core/           # Config, database, security
│   ├── integrations/   # Gmail, Calendar, CRM clients
│   ├── llm/            # Gemini client + prompts (via LangChain)
│   ├── models/         # SQLAlchemy models
│   ├── retrieval/      # Embeddings + vector search
│   ├── schemas/        # Pydantic request/response schemas
│   └── services/       # Business logic layer
├── tests/
└── alembic/

frontend/
├── src/
│   ├── app/
│   │   ├── (auth)/     # Login, OAuth callback
│   │   └── (dashboard)/ # Inbox, Drafts, Metrics, Traces
│   ├── components/     # UI components per feature
│   ├── hooks/          # React Query hooks
│   ├── stores/         # Zustand state stores
│   ├── lib/            # API client, utilities
│   └── types/          # TypeScript interfaces
```

## Documentation

- [System Architecture](docs/architecture/system-overview.md)
- [Database Schema](docs/architecture/database-schema.md)
- [Agent Workflow](docs/architecture/agent-workflow.md)
- [API Reference](docs/architecture/api-reference.md)
- [Gmail Integration](docs/features/gmail-integration.md)
- [Agent Engine](docs/features/agent-engine.md)
- [Calendar Integration](docs/features/calendar-integration.md)
- [CRM Integration](docs/features/crm-integration.md)
- [Retrieval Module](docs/features/retrieval-module.md)
- [Inbox Dashboard](docs/features/inbox-dashboard.md)
- [Draft Review](docs/features/draft-review.md)
- [Metrics Dashboard](docs/features/metrics-dashboard.md)
- [Trace Viewer](docs/features/trace-viewer.md)

## Performance Targets

| Metric | Target |
|--------|--------|
| API latency | < 300ms |
| Agent full cycle | < 4s |
| Dashboard load | < 1s |

## License

MIT
