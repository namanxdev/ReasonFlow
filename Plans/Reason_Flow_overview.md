# Autonomous Inbox AI Agent

## Technical Stack & Architecture Specification (v1.1)

---

# 11. Technology Stack Definition

## 11.1 Backend Platform

### Core Framework

* **FastAPI**

  * Primary API layer
  * Async request handling
  * Dependency injection
  * WebSocket support for streaming responses

### Agent Orchestration

* **LangChain**

  * Prompt templates
  * Tool wrappers
  * Output parsers
  * Memory abstractions

* **LangGraph**

  * Deterministic agent workflow graphs
  * State transitions
  * Retry nodes
  * Human-in-the-loop branching
  * Observability of agent steps

### LLM Provider

* **Google Gemini API**

  * Intent classification
  * Response generation
  * Tool decision reasoning
  * Structured JSON outputs

### Supporting Python Libraries

* Pydantic — schema validation
* SQLAlchemy / Prisma Client Python — DB ORM
* Redis — optional caching & queues
* Celery / RQ — async task execution
* httpx — async API calls
* Tenacity — retry policies

---

## 11.2 Frontend Platform

### Framework

* **Next.js (App Router)**

  * SSR for performance
  * API route proxying
  * Streaming UI support

### UI Libraries

* **shadcn/ui**

  * Core component system

* **Aceternity UI**

  * Hero animations
  * Interactive layouts

* **Magic UI**

  * Advanced visual widgets

* **HeroUI**

  * Productivity dashboard components

* **Fancy Components**

  * Data visualization and overlays

### State & Data

* React Query / TanStack Query
* Zustand (light state management)

### Styling

* TailwindCSS

---

## 11.3 Database Layer

### Primary Storage

* **PostgreSQL**

Stores:

* Email metadata
* Agent outputs
* Tool execution logs
* User configuration
* Metrics data

### Optional Extensions

* pgvector

  * Embedding similarity search

---

## 11.4 Embedding / Retrieval

* Gemini embeddings or open embedding model
* Vector storage:

  * PostgreSQL pgvector
  * or external vector DB (optional)

---

## 11.5 External Integrations

* Gmail API
* Google Calendar API
* CRM abstraction module

---

# 12. System Architecture

## 12.1 Backend Modules

### API Layer

Handles:

* Auth
* Request validation
* Routing

---

### Agent Engine

LangGraph workflow managing:

1. Email ingestion
2. Intent classification
3. Context retrieval
4. Tool selection
5. Response generation
6. Human review branching

---

### Tool Manager

Encapsulates external actions:

* Calendar scheduling
* CRM writes
* Email sending

---

### Retrieval Module

* Embedding generation
* Vector search
* Context ranking

---

### Evaluation Module

Tracks:

* Decision confidence
* Latency
* Tool accuracy

---

# 13. Agent Workflow Graph

## Node Sequence

Email Input
→ Classification Node
→ Context Retrieval Node
→ Decision Node
→ Tool Invocation Node
→ Response Generation Node
→ Human Approval Node
→ Dispatch Node

Each node maintains state and logs transitions.

---

# 14. Frontend Feature Modules

## Inbox Dashboard

* Email list
* Classification tags
* Status indicators

## Draft Review Panel

* Generated reply preview
* Editable text
* Accept / Reject

## Metrics Dashboard

* Intent distribution
* Latency graphs
* Tool success rate

## Agent Trace Viewer

* Visualization of LangGraph steps
* Debug capability

---

# 15. Deployment Targets

### Backend

* Docker container
* Deploy on:

  * Railway / Render / AWS

### Frontend

* Vercel

### Database

* Supabase / Neon

---

# 16. Observability & Logging

* Structured logs
* Agent step tracing
* Tool execution records
* Token usage tracking

---

# 17. Security Requirements

* OAuth token encryption
* Secrets in env vault
* Rate limiting
* Request validation
* Scoped API access

---

# 18. Performance Targets

* API latency < 300ms
* Agent full cycle < 4s
* Dashboard load < 1s

---

# End of Technical Stack Specification
