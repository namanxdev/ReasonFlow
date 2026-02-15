"""PgVectorStore — PostgreSQL vector similarity search via pgvector."""

from __future__ import annotations

import logging
import uuid
from typing import Any

from sqlalchemy import delete, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.embedding import Embedding

logger = logging.getLogger(__name__)

# Cosine *distance* threshold.  pgvector returns 0 (identical) → 2 (opposite),
# so we convert the caller-supplied similarity threshold (0→1) with:
#   distance_threshold = 1 - similarity_threshold
_DEFAULT_LIMIT = 5
_DEFAULT_SIMILARITY_THRESHOLD = 0.7


class PgVectorStore:
    """Store and retrieve embeddings from PostgreSQL using the pgvector extension.

    All operations accept an ``AsyncSession`` so they can participate in the
    caller's unit-of-work transaction.

    Cosine *distance* is used for similarity search.  The embeddings table
    stores vectors in a JSON column when pgvector is unavailable (development
    mode) and in a native ``vector(768)`` column when the extension is
    installed (production).  This class handles both cases gracefully.
    """

    # ------------------------------------------------------------------
    # Write
    # ------------------------------------------------------------------

    async def store_embedding(
        self,
        user_id: uuid.UUID | str,
        source_type: str,
        source_id: str,
        text_content: str,
        embedding: list[float],
        metadata: dict[str, Any] | None = None,
        db: AsyncSession | None = None,
    ) -> Embedding:
        """Persist a text embedding to the ``embeddings`` table.

        If a row with the same ``(user_id, source_type, source_id)`` already
        exists it is *replaced* (delete-then-insert) to keep the table
        idempotent for re-sync operations.

        Args:
            user_id:      UUID of the owning user.
            source_type:  One of ``"email"``, ``"crm"``, or ``"calendar"``.
            source_id:    The identifier within the source system (e.g. Gmail
                          message ID).
            text_content: The original text that was embedded.
            embedding:    768-dimensional float vector.
            metadata:     Optional JSON-serialisable dict with extra context.
            db:           AsyncSession to use.  *Required* — included as a
                          keyword argument to mirror the ``ContextBuilder``
                          calling convention.

        Returns:
            The newly created :class:`~app.models.embedding.Embedding` ORM
            instance.

        Raises:
            ValueError: If *db* is not provided.
        """
        if db is None:
            raise ValueError("An AsyncSession must be provided via the 'db' argument")

        uid = uuid.UUID(str(user_id)) if not isinstance(user_id, uuid.UUID) else user_id

        # Upsert: remove any existing row for the same (user, source_type, source_id).
        await db.execute(
            delete(Embedding).where(
                Embedding.user_id == uid,
                Embedding.source_type == source_type,
                Embedding.source_id == source_id,
            )
        )

        record = Embedding(
            user_id=uid,
            source_type=source_type,
            source_id=source_id,
            text_content=text_content,
            embedding=embedding,
            metadata_=metadata or {},
        )
        db.add(record)
        await db.flush()  # assign PK without committing the outer transaction

        logger.debug(
            "PgVectorStore.store_embedding: stored id=%s source_type=%s source_id=%s",
            record.id,
            source_type,
            source_id,
        )
        return record

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------

    async def search_similar(
        self,
        query_embedding: list[float],
        user_id: uuid.UUID | str,
        limit: int = _DEFAULT_LIMIT,
        threshold: float = _DEFAULT_SIMILARITY_THRESHOLD,
        source_type: str | None = None,
        db: AsyncSession | None = None,
    ) -> list[dict[str, Any]]:
        """Search for embeddings similar to *query_embedding*.

        Uses cosine *distance* (``<=>`` operator) when the pgvector extension
        is available.  Falls back to an in-Python brute-force cosine similarity
        scan when the operator is not available (e.g. SQLite in unit tests).

        Args:
            query_embedding: 768-dimensional float vector to search against.
            user_id:         Filter results to this user.
            limit:           Maximum number of results to return.
            threshold:       Minimum *similarity* score (0–1) for inclusion.
                             Results below this threshold are excluded.
            source_type:     If provided, restrict search to this source type.
            db:              AsyncSession to use.  *Required*.

        Returns:
            A list of dicts, each containing:
            - ``id`` (str): UUID of the embedding row.
            - ``source_type`` (str)
            - ``source_id`` (str)
            - ``text_content`` (str)
            - ``metadata`` (dict)
            - ``similarity`` (float): cosine similarity score in [0, 1].

        Raises:
            ValueError: If *db* is not provided.
        """
        if db is None:
            raise ValueError("An AsyncSession must be provided via the 'db' argument")

        uid = uuid.UUID(str(user_id)) if not isinstance(user_id, uuid.UUID) else user_id

        # Attempt pgvector cosine-distance query.
        try:
            results = await self._search_with_pgvector(
                query_embedding=query_embedding,
                uid=uid,
                limit=limit,
                threshold=threshold,
                source_type=source_type,
                db=db,
            )
            logger.debug(
                "PgVectorStore.search_similar: pgvector returned %d results (user=%s)",
                len(results),
                uid,
            )
            return results
        except Exception as pgvector_exc:
            logger.warning(
                "PgVectorStore.search_similar: pgvector search unavailable (%s), "
                "falling back to in-memory scan",
                pgvector_exc,
            )

        # Fallback: load all embeddings for the user and compute similarity in Python.
        return await self._search_with_fallback(
            query_embedding=query_embedding,
            uid=uid,
            limit=limit,
            threshold=threshold,
            source_type=source_type,
            db=db,
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    async def _search_with_pgvector(
        self,
        query_embedding: list[float],
        uid: uuid.UUID,
        limit: int,
        threshold: float,
        source_type: str | None,
        db: AsyncSession,
    ) -> list[dict[str, Any]]:
        """Run a native pgvector cosine-distance query."""
        vector_literal = f"[{','.join(str(v) for v in query_embedding)}]"

        # Build the optional source_type filter using a bound parameter to
        # avoid any risk of SQL injection even though source_type values are
        # controlled internally.
        if source_type:
            sql = text(
                """
                SELECT
                    id,
                    source_type,
                    source_id,
                    text_content,
                    metadata,
                    1 - (embedding <=> :qv::vector) AS similarity
                FROM embeddings
                WHERE user_id = :uid
                  AND source_type = :stype
                  AND 1 - (embedding <=> :qv::vector) >= :min_sim
                ORDER BY embedding <=> :qv::vector
                LIMIT :lim
                """
            )
            params: dict[str, Any] = {
                "qv": vector_literal,
                "uid": str(uid),
                "stype": source_type,
                "min_sim": threshold,
                "lim": limit,
            }
        else:
            sql = text(
                """
                SELECT
                    id,
                    source_type,
                    source_id,
                    text_content,
                    metadata,
                    1 - (embedding <=> :qv::vector) AS similarity
                FROM embeddings
                WHERE user_id = :uid
                  AND 1 - (embedding <=> :qv::vector) >= :min_sim
                ORDER BY embedding <=> :qv::vector
                LIMIT :lim
                """
            )
            params = {
                "qv": vector_literal,
                "uid": str(uid),
                "min_sim": threshold,
                "lim": limit,
            }

        result = await db.execute(sql, params)
        rows = result.fetchall()
        return [
            {
                "id": str(row.id),
                "source_type": row.source_type,
                "source_id": row.source_id,
                "text_content": row.text_content,
                "metadata": row.metadata or {},
                "similarity": float(row.similarity),
            }
            for row in rows
        ]

    async def _search_with_fallback(
        self,
        query_embedding: list[float],
        uid: uuid.UUID,
        limit: int,
        threshold: float,
        source_type: str | None,
        db: AsyncSession,
    ) -> list[dict[str, Any]]:
        """Python-level cosine similarity fallback for non-pgvector environments."""
        stmt = select(Embedding).where(Embedding.user_id == uid)
        if source_type:
            stmt = stmt.where(Embedding.source_type == source_type)

        result = await db.execute(stmt)
        rows = result.scalars().all()

        scored: list[tuple[float, Embedding]] = []
        for row in rows:
            if not row.embedding:
                continue
            sim = _cosine_similarity(query_embedding, row.embedding)
            if sim >= threshold:
                scored.append((sim, row))

        scored.sort(key=lambda x: x[0], reverse=True)
        top = scored[:limit]

        return [
            {
                "id": str(row.id),
                "source_type": row.source_type,
                "source_id": row.source_id,
                "text_content": row.text_content,
                "metadata": row.metadata_ or {},
                "similarity": float(sim),
            }
            for sim, row in top
        ]


# ---------------------------------------------------------------------------
# Pure-Python utility
# ---------------------------------------------------------------------------


def _cosine_similarity(a: list[float], b: list[float]) -> float:
    """Compute cosine similarity between two equal-length float vectors.

    Returns a value in [-1, 1], clipped to [0, 1] for practical use.
    Returns 0.0 if either vector has zero magnitude.
    """
    if len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    mag_a = sum(x * x for x in a) ** 0.5
    mag_b = sum(x * x for x in b) ** 0.5
    if mag_a == 0.0 or mag_b == 0.0:
        return 0.0
    return max(0.0, min(1.0, dot / (mag_a * mag_b)))
