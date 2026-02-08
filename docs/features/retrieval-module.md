# Retrieval Module

## Overview

The retrieval module provides semantic search over past emails, CRM data, and calendar events using Gemini embeddings stored in PostgreSQL with pgvector.

## Components

### EmbeddingService
Wraps Gemini embeddings via LangChain's `GoogleGenerativeAIEmbeddings`:
- `embed_text(text)` → 768-dimensional float vector
- `embed_batch(texts)` → list of vectors with rate limiting

### PgVectorStore
PostgreSQL-backed vector storage using pgvector extension:
- `store_embedding(text, embedding, metadata)` → INSERT with vector
- `search_similar(query_embedding, top_k=5)` → cosine similarity search
- IVFFlat index for fast approximate nearest neighbor queries

### ContextBuilder
Aggregates relevant context for email processing:

```python
class ContextBuilder:
    async def build_context(email, classification) -> list[str]:
        # 1. Embed the email text
        # 2. Search for similar past emails
        # 3. Fetch CRM contact data (if recognized sender)
        # 4. Get recent calendar events (if meeting-related)
        # 5. Rank and deduplicate
        # 6. Return top-k formatted context strings
```

## Embedding Model

Using Google Gemini's embedding model via LangChain:
- Model: `models/embedding-001`
- Dimensions: 768
- Accessed through `langchain-google-genai` package

## Vector Storage

PostgreSQL table `embeddings`:
- `embedding` column: `vector(768)` type
- Indexed with IVFFlat for cosine similarity
- Partitioned by `source_type` (email, crm, calendar)

## Search Algorithm

1. Generate query embedding from email text
2. Cosine similarity search in pgvector
3. Filter by user_id and optional source_type
4. Return top-k results with similarity scores
5. Format results as context strings for LLM prompt

## When Embeddings Are Created

- **Email sync**: Each new email is embedded on fetch
- **CRM updates**: Contact data re-embedded on changes
- **Calendar events**: Event descriptions embedded on sync
