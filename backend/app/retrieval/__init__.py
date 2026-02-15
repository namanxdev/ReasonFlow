"""Retrieval module — semantic search and context aggregation.

Public API
----------
- :class:`EmbeddingService` — create Gemini embeddings for arbitrary text.
- :class:`PgVectorStore`   — store and cosine-search embeddings in PostgreSQL.
- :class:`ContextBuilder`  — aggregate context from emails, CRM, and calendar.
- :func:`search_similar`   — convenience wrapper used by the agent pipeline.
"""

from __future__ import annotations

import logging
from typing import Any

from app.retrieval.context_builder import ContextBuilder
from app.retrieval.embeddings import EmbeddingService
from app.retrieval.vector_store import PgVectorStore

__all__ = [
    "ContextBuilder",
    "EmbeddingService",
    "PgVectorStore",
    "search_similar",
]

logger = logging.getLogger(__name__)

# Module-level singletons reused across calls to avoid repeated construction.
_embedding_service: EmbeddingService | None = None
_vector_store: PgVectorStore | None = None


def _get_embedding_service() -> EmbeddingService:
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = EmbeddingService()
    return _embedding_service


def _get_vector_store() -> PgVectorStore:
    global _vector_store
    if _vector_store is None:
        _vector_store = PgVectorStore()
    return _vector_store


async def search_similar(
    text: str,
    user_id: Any,
    top_k: int = 5,
    threshold: float = 0.7,
    source_type: str | None = None,
    db: Any = None,
) -> list[dict[str, Any]]:
    """Embed *text* and return the most similar stored documents.

    This is a convenience wrapper around :class:`EmbeddingService` and
    :class:`PgVectorStore` intended for use by the agent pipeline
    (``retrieve_node``).

    Args:
        text:        The query text to embed and search against.
        user_id:     Scope search to this user's embeddings.
        top_k:       Maximum number of results to return.
        threshold:   Minimum cosine similarity score (0–1).
        source_type: Optionally restrict to ``"email"``, ``"crm"``, or
                     ``"calendar"``.
        db:          SQLAlchemy :class:`~sqlalchemy.ext.asyncio.AsyncSession`.
                     When ``None`` the function returns an empty list so the
                     caller can treat the retrieval module as optional.

    Returns:
        A list of dicts (see :meth:`PgVectorStore.search_similar`) sorted by
        descending similarity.  Returns ``[]`` when *db* is ``None`` or when
        embedding/search raises an unrecoverable error.
    """
    if db is None:
        logger.debug("search_similar: no db session provided, returning empty results")
        return []

    if not text or not text.strip():
        logger.debug("search_similar: empty query text, returning empty results")
        return []

    try:
        embedding_svc = _get_embedding_service()
        vector_str = _get_vector_store()

        query_embedding = await embedding_svc.create_embedding(text)
        results = await vector_str.search_similar(
            query_embedding=query_embedding,
            user_id=user_id,
            limit=top_k,
            threshold=threshold,
            source_type=source_type,
            db=db,
        )
        logger.debug(
            "search_similar: returned %d results for user=%s", len(results), user_id
        )
        return results
    except Exception as exc:
        logger.warning("search_similar: failed — %s", exc)
        return []
