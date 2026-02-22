# System Architecture Overview

## High-Level Architecture

ReasonFlow is a full-stack autonomous inbox agent composed of three main layers:

```
┌──────────────────────────────────────────────────────────┐
│                    FRONTEND (Next.js)                     │
│  ┌──────────┐ ┌──────────┐ ┌─────────┐ ┌─────────────┐  │
│  │  Inbox   │ │  Draft   │ │ Metrics │ │   Trace     │  │
│  │Dashboard │ │  Review  │ │Dashboard│ │   Viewer    │  │
│  └──────────┘ └──────────┘ └─────────┘ └─────────────┘  │
│            TanStack Query + Zustand + shadcn/ui           │
└──────────────────────┬───────────────────────────────────┘
                       │ REST API (JSON)
┌──────────────────────▼───────────────────────────────────┐
│                  BACKEND (FastAPI)                         │
│                                                           │
│  ┌─────────────────────────────────────────────────────┐  │
│  │                 API Layer                            │  │
│  │  Auth │ Emails │ Drafts │ Traces │ Metrics │ Gmail  │  │
│  │                + JWT + Rate Limiting                 │  │
│  └─────────────────────┬───────────────────────────────┘  │
│                        │                                  │
│  ┌─────────────┐ ┌─────▼───────┐ ┌──────────────────┐    │
│  │  LLM Module │ │   Agent     │ │  Integrations    │    │
│  │  (LangChain │ │   Engine    │ │  ┌─────────────┐ │    │
│  │  + Gemini)  │ │ (LangGraph) │ │  │ Gmail       │ │    │
│  │             │ │             │ │  │ Calendar    │ │    │
│  │ classify()  │ │ classify    │ │  │ CRM         │ │    │
│  │ generate()  │ │ retrieve    │ │  └─────────────┘ │    │
│  │ extract()   │ │ decide      │ │                  │    │
│  │ embed()     │ │ execute     │ └──────────────────┘    │
│  └─────────────┘ │ generate    │                         │
│                  │ review      │  ┌──────────────────┐    │
│                  └─────────────┘  │ Retrieval Module │    │
│                                   │ Embeddings       │    │
│                                   │ Vector Search    │    │
│                                   │ Context Builder  │    │
│                                   └──────────────────┘    │
└──────────────────────┬───────────────────────────────────┘
                       │
┌──────────────────────▼───────────────────────────────────┐
│                    DATA LAYER                              │
│  ┌────────────────────┐                                   │
│  │  PostgreSQL         │    In-memory services:            │
│  │  + pgvector         │    - Rate limiting (sliding       │
│  │  - Users            │      window)                      │
│  │  - Emails           │    - Event bus (asyncio.Queue)    │
│  │  - Agent Logs       │    - Batch job tracking           │
│  │  - Tool Executions  │                                   │
│  │  - Embeddings       │                                   │
│  └────────────────────┘                                   │
└──────────────────────────────────────────────────────────┘
```

## Technology Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| Backend Framework | FastAPI | Async REST API with dependency injection |
| Agent Orchestration | LangGraph | Deterministic workflow graphs with state |
| LLM Framework | LangChain + Gemini | Prompt management, tool wrappers |
| LLM Provider | Google Gemini API | Classification, generation, embeddings |
| Database | PostgreSQL + pgvector | Persistent storage + vector search |
| In-memory Services | asyncio / dict | Rate limiting, event bus, batch tracking |
| Frontend | Next.js 14 (App Router) | SSR dashboard |
| UI Components | shadcn/ui, Aceternity, Magic UI, HeroUI, Fancy Components | Rich interactive UI |
| State Management | Zustand + TanStack Query | Client state + server state |

## Data Flow

1. **Email Ingestion**: Gmail API → Backend → PostgreSQL
2. **Agent Processing**: Email → LangGraph workflow → Classification → Context → Tools → Draft
3. **Human Review**: Low-confidence drafts → Dashboard → Approve/Reject
4. **Dispatch**: Approved drafts → Gmail send
5. **Observability**: Every step logged to agent_logs + tool_executions

## Performance Targets

| Metric | Target | Strategy |
|--------|--------|----------|
| API latency | < 300ms | Async I/O, connection pooling |
| Agent full cycle | < 4s | Parallel tool execution, optimized prompts |
| Dashboard load | < 1s | SSR, React Query prefetching |

## Security Architecture

- JWT-based authentication with configurable expiration
- OAuth2 token encryption at rest
- In-memory rate limiting (sliding window)
- Input validation via Pydantic on all endpoints
- CORS restricted to frontend origin
- Secrets stored exclusively in environment variables
