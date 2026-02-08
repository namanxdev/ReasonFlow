# Agent Engine

## Overview

The agent engine is the core AI workflow built on LangGraph. It processes emails through a deterministic pipeline of nodes, each powered by Google Gemini via LangChain.

## Node Pipeline

### 1. Classification Node (`classify`)
- Calls `GeminiClient.classify_intent()` via LangChain
- Returns: intent category + confidence score
- Short-circuits spam emails with high confidence

### 2. Context Retrieval Node (`retrieve`)
- Embeds email text using Gemini embeddings (via LangChain)
- Searches pgvector for similar past emails
- Fetches CRM contact data and calendar events
- Returns: ranked list of context strings

### 3. Decision Node (`decide`)
- Analyzes classification + context
- Selects tools to invoke from available registry
- Returns: list of tools with parameters

### 4. Tool Execution Node (`execute_tools`)
- Iterates selected tools via ToolManager
- Each call logged to `tool_executions` table
- Failures isolated — one tool failing doesn't block others
- Returns: dict of tool results

### 5. Generation Node (`generate`)
- Generates email response using Gemini via LangChain
- Incorporates context + tool results
- Returns: draft response text + confidence

### 6. Review Node (`review`)
- Decides: auto-approve vs human review
- Threshold: confidence ≥ 0.8 → auto-approve
- Complaints always require human review
- Returns: `requires_approval` flag

### 7. Dispatch Node (`dispatch`)
- Sends approved response via Gmail API
- Updates email status to "sent"

## LangChain + Gemini Integration

All LLM calls use `langchain-google-genai`:
```python
from langchain_google_genai import ChatGoogleGenerativeAI

llm = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash",
    google_api_key=settings.GEMINI_API_KEY,
)
```

Embeddings use:
```python
from langchain_google_genai import GoogleGenerativeAIEmbeddings

embeddings = GoogleGenerativeAIEmbeddings(
    model="models/embedding-001",
    google_api_key=settings.GEMINI_API_KEY,
)
```

## Tool Registry

| Tool | Integration | Description |
|------|------------|-------------|
| send_email | Gmail | Send an email response |
| create_draft | Gmail | Create a draft for review |
| check_calendar | Calendar | Check availability |
| create_event | Calendar | Schedule a meeting |
| get_contact | CRM | Fetch contact info |
| update_contact | CRM | Update contact data |

## Observability

Every execution generates:
- `AgentLog` entries for each node (with full state I/O)
- `ToolExecution` entries for each tool call
- A `trace_id` to group all entries for one run
