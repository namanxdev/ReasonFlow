"""EmbeddingService — wraps Google Gemini embeddings via LangChain."""

from __future__ import annotations

import logging

from langchain_google_genai import GoogleGenerativeAIEmbeddings
from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.config import settings

logger = logging.getLogger(__name__)

_EMBEDDING_MODEL = "models/embedding-001"


class EmbeddingService:
    """Generates 768-dimensional text embeddings using Google Gemini via LangChain.

    Uses ``models/embedding-001`` (768 dimensions) accessed through
    ``langchain-google-genai``.  The underlying client is initialised lazily
    so that importing this module in environments without a valid API key
    (e.g. unit tests) does not immediately raise.
    """

    def __init__(self, model: str = _EMBEDDING_MODEL) -> None:
        self._model = model
        self._client: GoogleGenerativeAIEmbeddings | None = None

    def _get_client(self) -> GoogleGenerativeAIEmbeddings:
        """Return (or lazily create) the LangChain embeddings client."""
        if self._client is None:
            self._client = GoogleGenerativeAIEmbeddings(
                model=self._model,
                google_api_key=settings.GEMINI_API_KEY,
            )
        return self._client

    async def create_embedding(self, text: str) -> list[float]:
        """Return a 768-dimensional embedding vector for *text*.

        Args:
            text: The input string to embed.

        Returns:
            A list of 768 floats representing the embedding.

        Raises:
            ValueError: If *text* is empty.
            Exception: Propagated from the Gemini API after retries are
                exhausted.
        """
        if not text or not text.strip():
            raise ValueError("Cannot embed empty text")

        logger.debug("EmbeddingService.create_embedding: len(text)=%d", len(text))
        vectors = await self._embed_with_retry([text])
        embedding: list[float] = vectors[0]
        logger.debug(
            "EmbeddingService.create_embedding: produced %d-dim vector", len(embedding)
        )
        return embedding

    async def create_embeddings_batch(self, texts: list[str]) -> list[list[float]]:
        """Return embeddings for a batch of texts.

        Empty strings within the batch are replaced with a single space so
        the Gemini API does not reject the request; the caller is still
        responsible for meaningful input.

        Args:
            texts: A list of input strings to embed.

        Returns:
            A list of 768-dimensional float vectors, one per input string.

        Raises:
            ValueError: If *texts* is empty.
            Exception: Propagated from the Gemini API after retries are
                exhausted.
        """
        if not texts:
            raise ValueError("Cannot embed an empty list of texts")

        # Replace blank strings with a single space to avoid API errors.
        sanitised = [t if t and t.strip() else " " for t in texts]

        logger.debug(
            "EmbeddingService.create_embeddings_batch: batch_size=%d", len(sanitised)
        )
        embeddings: list[list[float]] = await self._embed_with_retry(sanitised)
        logger.debug(
            "EmbeddingService.create_embeddings_batch: produced %d vectors",
            len(embeddings),
        )
        return embeddings

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
    )
    async def _embed_with_retry(self, texts: list[str]) -> list[list[float]]:
        """Call the LangChain embeddings client with retry logic.

        Args:
            texts: Pre-validated, non-empty list of strings.

        Returns:
            List of embedding vectors.
        """
        client = self._get_client()
        vectors: list[list[float]] = await client.aembed_documents(texts)
        return vectors
