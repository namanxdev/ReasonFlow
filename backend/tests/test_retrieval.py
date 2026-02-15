"""Tests for the retrieval module.

Uses unittest.mock to avoid calling real Gemini APIs or hitting a live
database.  All async tests run under pytest-asyncio (asyncio_mode = "auto").
"""

from __future__ import annotations

import uuid
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.retrieval import search_similar
from app.retrieval.context_builder import ContextBuilder, _build_context_strings
from app.retrieval.embeddings import EmbeddingService
from app.retrieval.vector_store import PgVectorStore, _cosine_similarity


# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------


def _make_vector(value: float = 0.5, dims: int = 768) -> list[float]:
    """Return a constant unit-like vector for deterministic tests."""
    return [value] * dims


# ---------------------------------------------------------------------------
# EmbeddingService
# ---------------------------------------------------------------------------


class TestEmbeddingService:
    """Tests for EmbeddingService."""

    @pytest.fixture
    def mock_lc_embeddings(self):
        """Patch GoogleGenerativeAIEmbeddings so no real API call is made."""
        with patch(
            "app.retrieval.embeddings.GoogleGenerativeAIEmbeddings"
        ) as MockCls:
            instance = MagicMock()
            instance.aembed_documents = AsyncMock(
                return_value=[_make_vector(0.1)]
            )
            MockCls.return_value = instance
            yield instance

    async def test_create_embedding_returns_vector(self, mock_lc_embeddings):
        svc = EmbeddingService()
        result = await svc.create_embedding("Hello world")
        assert isinstance(result, list)
        assert len(result) == 768
        mock_lc_embeddings.aembed_documents.assert_awaited_once_with(["Hello world"])

    async def test_create_embedding_raises_on_empty_string(self, mock_lc_embeddings):
        svc = EmbeddingService()
        with pytest.raises(ValueError, match="empty text"):
            await svc.create_embedding("")

    async def test_create_embedding_raises_on_whitespace(self, mock_lc_embeddings):
        svc = EmbeddingService()
        with pytest.raises(ValueError, match="empty text"):
            await svc.create_embedding("   ")

    async def test_create_embeddings_batch_returns_list(self, mock_lc_embeddings):
        mock_lc_embeddings.aembed_documents = AsyncMock(
            return_value=[_make_vector(0.1), _make_vector(0.2)]
        )
        svc = EmbeddingService()
        results = await svc.create_embeddings_batch(["first", "second"])
        assert len(results) == 2
        assert all(len(v) == 768 for v in results)

    async def test_create_embeddings_batch_raises_on_empty_list(self, mock_lc_embeddings):
        svc = EmbeddingService()
        with pytest.raises(ValueError, match="empty list"):
            await svc.create_embeddings_batch([])

    async def test_create_embeddings_batch_sanitises_blank_strings(
        self, mock_lc_embeddings
    ):
        """Blank strings in the batch should be replaced with a space."""
        mock_lc_embeddings.aembed_documents = AsyncMock(
            return_value=[_make_vector(0.3)]
        )
        svc = EmbeddingService()
        await svc.create_embeddings_batch([""])
        call_args = mock_lc_embeddings.aembed_documents.call_args[0][0]
        assert call_args == [" "]

    async def test_client_lazily_initialised(self, mock_lc_embeddings):
        """The LangChain client must not be created until the first call."""
        svc = EmbeddingService()
        assert svc._client is None
        await svc.create_embedding("lazy init test")
        assert svc._client is not None

    async def test_custom_model_passed_to_langchain(self):
        """Model name supplied to EmbeddingService is forwarded to LangChain."""
        with patch(
            "app.retrieval.embeddings.GoogleGenerativeAIEmbeddings"
        ) as MockCls:
            instance = MagicMock()
            instance.aembed_documents = AsyncMock(return_value=[_make_vector()])
            MockCls.return_value = instance

            svc = EmbeddingService(model="models/text-embedding-004")
            await svc.create_embedding("test")

            call_kwargs = MockCls.call_args[1]
            assert call_kwargs["model"] == "models/text-embedding-004"


# ---------------------------------------------------------------------------
# _cosine_similarity (pure helper)
# ---------------------------------------------------------------------------


class TestCosineSimilarity:
    """Unit tests for the _cosine_similarity utility."""

    def test_identical_vectors_return_one(self):
        v = [1.0, 0.0, 0.0]
        assert _cosine_similarity(v, v) == pytest.approx(1.0)

    def test_orthogonal_vectors_return_zero(self):
        assert _cosine_similarity([1.0, 0.0], [0.0, 1.0]) == pytest.approx(0.0)

    def test_opposite_vectors_clipped_to_zero(self):
        # Cosine similarity of opposite vectors is -1; clipped to 0.
        result = _cosine_similarity([1.0, 0.0], [-1.0, 0.0])
        assert result == pytest.approx(0.0)

    def test_zero_vector_returns_zero(self):
        assert _cosine_similarity([0.0, 0.0], [1.0, 1.0]) == 0.0

    def test_mismatched_lengths_return_zero(self):
        assert _cosine_similarity([1.0, 2.0], [1.0]) == 0.0

    def test_known_similarity(self):
        a = [1.0, 1.0, 0.0]
        b = [1.0, 0.0, 0.0]
        # cos(45°) ≈ 0.7071
        assert _cosine_similarity(a, b) == pytest.approx(0.7071, abs=1e-4)


# ---------------------------------------------------------------------------
# PgVectorStore
# ---------------------------------------------------------------------------


class TestPgVectorStore:
    """Tests for PgVectorStore."""

    @pytest.fixture
    def uid(self) -> uuid.UUID:
        return uuid.uuid4()

    @pytest.fixture
    def mock_db(self) -> AsyncMock:
        session = AsyncMock()
        session.execute = AsyncMock()
        session.flush = AsyncMock()
        session.add = MagicMock()
        return session

    # --- store_embedding ---

    async def test_store_embedding_raises_without_db(self, uid):
        store = PgVectorStore()
        with pytest.raises(ValueError, match="AsyncSession"):
            await store.store_embedding(
                user_id=uid,
                source_type="email",
                source_id="msg-001",
                text_content="test text",
                embedding=_make_vector(),
            )

    async def test_store_embedding_adds_record(self, uid, mock_db):
        store = PgVectorStore()
        record = await store.store_embedding(
            user_id=uid,
            source_type="email",
            source_id="msg-001",
            text_content="hello world",
            embedding=_make_vector(0.5),
            metadata={"key": "value"},
            db=mock_db,
        )
        mock_db.add.assert_called_once()
        mock_db.flush.assert_awaited_once()
        assert record.source_type == "email"
        assert record.source_id == "msg-001"
        assert record.text_content == "hello world"
        assert record.metadata_ == {"key": "value"}

    async def test_store_embedding_accepts_string_user_id(self, uid, mock_db):
        store = PgVectorStore()
        record = await store.store_embedding(
            user_id=str(uid),
            source_type="crm",
            source_id="contact-1",
            text_content="crm text",
            embedding=_make_vector(0.3),
            db=mock_db,
        )
        assert record.user_id == uid

    async def test_store_embedding_sets_empty_dict_when_no_metadata(self, uid, mock_db):
        store = PgVectorStore()
        record = await store.store_embedding(
            user_id=uid,
            source_type="email",
            source_id="msg-002",
            text_content="text",
            embedding=_make_vector(),
            db=mock_db,
        )
        assert record.metadata_ == {}

    # --- search_similar ---

    async def test_search_similar_raises_without_db(self, uid):
        store = PgVectorStore()
        with pytest.raises(ValueError, match="AsyncSession"):
            await store.search_similar(
                query_embedding=_make_vector(),
                user_id=uid,
            )

    async def test_search_similar_falls_back_when_pgvector_unavailable(
        self, uid, mock_db
    ):
        """When the raw SQL query fails, the fallback path is used."""
        # Raw SQL raises (simulates missing pgvector extension).
        mock_db.execute.side_effect = [
            Exception("operator does not exist: json <=> json"),
            # Second call for the fallback SELECT.
            _make_scalars_result([]),
        ]

        store = PgVectorStore()
        results = await store.search_similar(
            query_embedding=_make_vector(),
            user_id=uid,
            db=mock_db,
        )
        assert results == []

    async def test_search_similar_returns_sorted_by_similarity(self, uid):
        """Fallback path returns results sorted by descending similarity."""
        store = PgVectorStore()
        user_id = uid

        # Build two fake Embedding ORM objects.
        emb_high = _make_embedding(uid=user_id, text="high similarity", vec=[1.0] * 768)
        emb_low = _make_embedding(uid=user_id, text="low similarity", vec=[0.0] * 767 + [1.0])

        mock_db = AsyncMock()
        # pgvector attempt raises → fallback.
        mock_db.execute.side_effect = [
            Exception("no pgvector"),
            _make_scalars_result([emb_high, emb_low]),
        ]

        query_vec = [1.0] * 768
        results = await store.search_similar(
            query_embedding=query_vec,
            user_id=user_id,
            limit=5,
            threshold=0.0,
            db=mock_db,
        )
        # emb_high (all-ones against all-ones) → similarity = 1.0
        assert results[0]["text_content"] == "high similarity"
        assert results[0]["similarity"] == pytest.approx(1.0)

    async def test_search_similar_filters_by_threshold(self, uid):
        """Records below the similarity threshold must be excluded."""
        store = PgVectorStore()

        # Orthogonal vector → similarity = 0.0 with a [1,0,...] query.
        emb_low = _make_embedding(
            uid=uid,
            text="orthogonal",
            vec=[0.0] + [1.0] + [0.0] * 766,
        )

        mock_db = AsyncMock()
        mock_db.execute.side_effect = [
            Exception("no pgvector"),
            _make_scalars_result([emb_low]),
        ]

        results = await store.search_similar(
            query_embedding=[1.0] + [0.0] * 767,
            user_id=uid,
            threshold=0.7,
            db=mock_db,
        )
        assert results == []

    async def test_search_similar_skips_embeddings_without_vector(self, uid):
        """Rows with a null embedding are silently skipped in the fallback."""
        store = PgVectorStore()
        emb_null = _make_embedding(uid=uid, text="no vector", vec=None)

        mock_db = AsyncMock()
        mock_db.execute.side_effect = [
            Exception("no pgvector"),
            _make_scalars_result([emb_null]),
        ]

        results = await store.search_similar(
            query_embedding=_make_vector(),
            user_id=uid,
            db=mock_db,
        )
        assert results == []

    async def test_search_similar_respects_limit(self, uid):
        """Fallback path must honour the *limit* parameter."""
        store = PgVectorStore()
        embeddings = [
            _make_embedding(uid=uid, text=f"doc {i}", vec=[1.0] * 768)
            for i in range(10)
        ]

        mock_db = AsyncMock()
        mock_db.execute.side_effect = [
            Exception("no pgvector"),
            _make_scalars_result(embeddings),
        ]

        results = await store.search_similar(
            query_embedding=[1.0] * 768,
            user_id=uid,
            limit=3,
            threshold=0.0,
            db=mock_db,
        )
        assert len(results) == 3


# ---------------------------------------------------------------------------
# ContextBuilder
# ---------------------------------------------------------------------------


class TestContextBuilder:
    """Tests for ContextBuilder."""

    @pytest.fixture
    def uid(self) -> uuid.UUID:
        return uuid.uuid4()

    @pytest.fixture
    def mock_db(self) -> AsyncMock:
        return AsyncMock()

    @pytest.fixture
    def email(self, uid: uuid.UUID) -> dict[str, Any]:
        return {
            "subject": "Hello there",
            "body": "Can we schedule a meeting?",
            "sender": "alice@example.com",
            "classification": "inquiry",
            "user_id": str(uid),
        }

    # --- Happy-path ---

    async def test_build_context_returns_expected_keys(
        self, uid, mock_db, email
    ):
        embedding_svc = AsyncMock(spec=EmbeddingService)
        embedding_svc.create_embedding = AsyncMock(return_value=_make_vector())

        vector_store = AsyncMock(spec=PgVectorStore)
        vector_store.search_similar = AsyncMock(return_value=[])

        builder = ContextBuilder(
            embedding_service=embedding_svc,
            vector_store=vector_store,
        )

        with patch("app.retrieval.context_builder.get_crm_client") as mock_crm_factory:
            mock_crm = AsyncMock()
            mock_crm.get_contact = AsyncMock(return_value=None)
            mock_crm_factory.return_value = mock_crm

            ctx = await builder.build_context(
                email=email, user_id=uid, db_session=mock_db
            )

        assert "similar_emails" in ctx
        assert "crm_contact" in ctx
        assert "calendar_events" in ctx
        assert "context_strings" in ctx

    async def test_build_context_includes_similar_emails(
        self, uid, mock_db, email
    ):
        similar = [
            {
                "id": str(uuid.uuid4()),
                "source_type": "email",
                "source_id": "msg-old",
                "text_content": "Previous thread content",
                "metadata": {},
                "similarity": 0.85,
            }
        ]

        embedding_svc = AsyncMock(spec=EmbeddingService)
        embedding_svc.create_embedding = AsyncMock(return_value=_make_vector())
        vector_store = AsyncMock(spec=PgVectorStore)
        vector_store.search_similar = AsyncMock(return_value=similar)

        builder = ContextBuilder(
            embedding_service=embedding_svc, vector_store=vector_store
        )

        with patch("app.retrieval.context_builder.get_crm_client") as mock_crm_factory:
            mock_crm = AsyncMock()
            mock_crm.get_contact = AsyncMock(return_value=None)
            mock_crm_factory.return_value = mock_crm

            ctx = await builder.build_context(
                email=email, user_id=uid, db_session=mock_db
            )

        assert ctx["similar_emails"] == similar
        assert any("Past email" in s for s in ctx["context_strings"])

    async def test_build_context_includes_crm_contact(
        self, uid, mock_db, email
    ):
        embedding_svc = AsyncMock(spec=EmbeddingService)
        embedding_svc.create_embedding = AsyncMock(return_value=_make_vector())
        vector_store = AsyncMock(spec=PgVectorStore)
        vector_store.search_similar = AsyncMock(return_value=[])

        crm_data = {
            "name": "Alice Smith",
            "company": "Acme Corp",
            "title": "VP Engineering",
            "notes": "Interested in enterprise",
            "tags": ["prospect"],
        }

        builder = ContextBuilder(
            embedding_service=embedding_svc, vector_store=vector_store
        )

        with patch("app.retrieval.context_builder.get_crm_client") as mock_crm_factory:
            mock_crm = AsyncMock()
            mock_crm.get_contact = AsyncMock(return_value=crm_data)
            mock_crm_factory.return_value = mock_crm

            ctx = await builder.build_context(
                email=email, user_id=uid, db_session=mock_db
            )

        assert ctx["crm_contact"] == crm_data
        assert any("CRM Contact" in s for s in ctx["context_strings"])
        assert any("Alice Smith" in s for s in ctx["context_strings"])

    async def test_build_context_calendar_skipped_for_non_meeting_email(
        self, uid, mock_db, email
    ):
        """Calendar lookup must not run for non-meeting classifications."""
        embedding_svc = AsyncMock(spec=EmbeddingService)
        embedding_svc.create_embedding = AsyncMock(return_value=_make_vector())
        vector_store = AsyncMock(spec=PgVectorStore)
        vector_store.search_similar = AsyncMock(return_value=[])

        builder = ContextBuilder(
            embedding_service=embedding_svc, vector_store=vector_store
        )

        with patch("app.retrieval.context_builder.get_crm_client") as mock_crm_factory:
            mock_crm = AsyncMock()
            mock_crm.get_contact = AsyncMock(return_value=None)
            mock_crm_factory.return_value = mock_crm

            with patch("app.retrieval.context_builder.CalendarClient") as MockCal:
                ctx = await builder.build_context(
                    email=email, user_id=uid, db_session=mock_db
                )
                MockCal.assert_not_called()

        assert ctx["calendar_events"] == []

    async def test_build_context_calendar_fetched_for_meeting_request(
        self, uid, mock_db
    ):
        """Calendar lookup runs for meeting_request emails that supply credentials."""
        meeting_email = {
            "subject": "Let's meet",
            "body": "Are you free Thursday?",
            "sender": "bob@example.com",
            "classification": "meeting_request",
            "user_credentials": {"access_token": "tok", "refresh_token": "ref"},
        }

        embedding_svc = AsyncMock(spec=EmbeddingService)
        embedding_svc.create_embedding = AsyncMock(return_value=_make_vector())
        vector_store = AsyncMock(spec=PgVectorStore)
        vector_store.search_similar = AsyncMock(return_value=[])

        free_slots = [
            {
                "start": "2026-02-15T09:00:00+00:00",
                "end": "2026-02-15T10:00:00+00:00",
                "duration_minutes": 60,
            }
        ]

        builder = ContextBuilder(
            embedding_service=embedding_svc, vector_store=vector_store
        )

        with patch("app.retrieval.context_builder.get_crm_client") as mock_crm_factory:
            mock_crm = AsyncMock()
            mock_crm.get_contact = AsyncMock(return_value=None)
            mock_crm_factory.return_value = mock_crm

            with patch("app.retrieval.context_builder.CalendarClient") as MockCal:
                mock_cal_instance = AsyncMock()
                mock_cal_instance.get_free_slots = AsyncMock(return_value=free_slots)
                MockCal.return_value = mock_cal_instance

                ctx = await builder.build_context(
                    email=meeting_email, user_id=uid, db_session=mock_db
                )

        assert ctx["calendar_events"] == free_slots
        assert any("calendar" in s.lower() for s in ctx["context_strings"])

    # --- Resilience ---

    async def test_build_context_continues_when_vector_search_fails(
        self, uid, mock_db, email
    ):
        embedding_svc = AsyncMock(spec=EmbeddingService)
        embedding_svc.create_embedding = AsyncMock(
            side_effect=Exception("Gemini API error")
        )
        vector_store = AsyncMock(spec=PgVectorStore)

        builder = ContextBuilder(
            embedding_service=embedding_svc, vector_store=vector_store
        )

        with patch("app.retrieval.context_builder.get_crm_client") as mock_crm_factory:
            mock_crm = AsyncMock()
            mock_crm.get_contact = AsyncMock(return_value={"name": "Test User"})
            mock_crm_factory.return_value = mock_crm

            ctx = await builder.build_context(
                email=email, user_id=uid, db_session=mock_db
            )

        # Vector search failed but CRM data should still be present.
        assert ctx["similar_emails"] == []
        assert ctx["crm_contact"] is not None

    async def test_build_context_continues_when_crm_fails(
        self, uid, mock_db, email
    ):
        embedding_svc = AsyncMock(spec=EmbeddingService)
        embedding_svc.create_embedding = AsyncMock(return_value=_make_vector())
        vector_store = AsyncMock(spec=PgVectorStore)
        vector_store.search_similar = AsyncMock(return_value=[])

        builder = ContextBuilder(
            embedding_service=embedding_svc, vector_store=vector_store
        )

        with patch("app.retrieval.context_builder.get_crm_client") as mock_crm_factory:
            mock_crm_factory.side_effect = Exception("CRM unavailable")

            ctx = await builder.build_context(
                email=email, user_id=uid, db_session=mock_db
            )

        assert ctx["crm_contact"] is None

    async def test_build_context_skips_vector_search_when_body_is_empty(
        self, uid, mock_db
    ):
        empty_email = {
            "subject": "",
            "body": "",
            "sender": "test@example.com",
            "classification": "inquiry",
        }

        embedding_svc = AsyncMock(spec=EmbeddingService)
        embedding_svc.create_embedding = AsyncMock(return_value=_make_vector())
        vector_store = AsyncMock(spec=PgVectorStore)

        builder = ContextBuilder(
            embedding_service=embedding_svc, vector_store=vector_store
        )

        with patch("app.retrieval.context_builder.get_crm_client") as mock_crm_factory:
            mock_crm = AsyncMock()
            mock_crm.get_contact = AsyncMock(return_value=None)
            mock_crm_factory.return_value = mock_crm

            ctx = await builder.build_context(
                email=empty_email, user_id=uid, db_session=mock_db
            )

        embedding_svc.create_embedding.assert_not_awaited()
        assert ctx["similar_emails"] == []


# ---------------------------------------------------------------------------
# _build_context_strings helper
# ---------------------------------------------------------------------------


class TestBuildContextStrings:
    """Tests for the _build_context_strings pure helper."""

    def test_empty_inputs_return_empty_list(self):
        assert _build_context_strings([], None, []) == []

    def test_similar_emails_formatted(self):
        items = [
            {"text_content": "Email body text", "similarity": 0.9, "source_id": "x"}
        ]
        result = _build_context_strings(items, None, [])
        assert len(result) == 1
        assert "Past email 1" in result[0]
        assert "0.90" in result[0]
        assert "Email body text" in result[0]

    def test_crm_contact_formatted(self):
        contact = {
            "name": "Alice Smith",
            "company": "Acme",
            "title": "CEO",
            "notes": "VIP",
            "tags": ["vip"],
        }
        result = _build_context_strings([], contact, [])
        assert len(result) == 1
        assert "CRM Contact" in result[0]
        assert "Alice Smith" in result[0]
        assert "Acme" in result[0]

    def test_crm_contact_skips_empty_fields(self):
        contact = {"name": "Bob", "company": ""}
        result = _build_context_strings([], contact, [])
        assert "Bob" in result[0]
        assert "company" not in result[0].lower()

    def test_calendar_events_formatted(self):
        events = [
            {"start": "2026-02-16T09:00", "end": "2026-02-16T10:00", "title": "Standup"}
        ]
        result = _build_context_strings([], None, events)
        assert len(result) == 1
        assert "Upcoming calendar events" in result[0]
        assert "Standup" in result[0]

    def test_calendar_event_uses_summary_when_no_title(self):
        events = [{"start": "2026-02-16T09:00", "end": "2026-02-16T10:00", "summary": "Sync"}]
        result = _build_context_strings([], None, events)
        assert "Sync" in result[0]

    def test_empty_text_content_skipped_in_similar_emails(self):
        items = [{"text_content": "", "similarity": 0.8, "source_id": "x"}]
        result = _build_context_strings(items, None, [])
        assert result == []

    def test_all_sources_combined(self):
        similar = [{"text_content": "Past email", "similarity": 0.75, "source_id": "a"}]
        crm = {"name": "Jane"}
        calendar = [{"start": "t1", "end": "t2", "title": "Meeting"}]
        result = _build_context_strings(similar, crm, calendar)
        assert len(result) == 3


# ---------------------------------------------------------------------------
# search_similar convenience function
# ---------------------------------------------------------------------------


class TestSearchSimilar:
    """Tests for the module-level search_similar convenience wrapper."""

    async def test_returns_empty_list_when_db_is_none(self):
        result = await search_similar(text="test", user_id=uuid.uuid4(), db=None)
        assert result == []

    async def test_returns_empty_list_for_empty_text(self):
        result = await search_similar(
            text="", user_id=uuid.uuid4(), db=AsyncMock()
        )
        assert result == []

    async def test_returns_empty_list_for_whitespace_text(self):
        result = await search_similar(
            text="   ", user_id=uuid.uuid4(), db=AsyncMock()
        )
        assert result == []

    async def test_delegates_to_embedding_and_vector_store(self):
        uid = uuid.uuid4()
        expected = [{"text_content": "result", "similarity": 0.9}]

        mock_emb_svc = AsyncMock(spec=EmbeddingService)
        mock_emb_svc.create_embedding = AsyncMock(return_value=_make_vector())
        mock_vec_store = AsyncMock(spec=PgVectorStore)
        mock_vec_store.search_similar = AsyncMock(return_value=expected)

        # Patch the module-level singletons.
        with (
            patch("app.retrieval._get_embedding_service", return_value=mock_emb_svc),
            patch("app.retrieval._get_vector_store", return_value=mock_vec_store),
        ):
            result = await search_similar(
                text="find me something similar",
                user_id=uid,
                top_k=3,
                threshold=0.6,
                db=AsyncMock(),
            )

        assert result == expected
        mock_emb_svc.create_embedding.assert_awaited_once_with(
            "find me something similar"
        )
        mock_vec_store.search_similar.assert_awaited_once()

    async def test_returns_empty_list_on_exception(self):
        """When an internal error occurs the caller gets [] instead of a traceback."""
        mock_emb_svc = AsyncMock(spec=EmbeddingService)
        mock_emb_svc.create_embedding = AsyncMock(
            side_effect=RuntimeError("unexpected")
        )

        with patch("app.retrieval._get_embedding_service", return_value=mock_emb_svc):
            result = await search_similar(
                text="crash test",
                user_id=uuid.uuid4(),
                db=AsyncMock(),
            )

        assert result == []


# ---------------------------------------------------------------------------
# Private test helpers
# ---------------------------------------------------------------------------


def _make_embedding(
    uid: uuid.UUID,
    text: str,
    vec: list[float] | None,
    source_type: str = "email",
    source_id: str = "msg-test",
) -> Any:
    """Build a minimal Embedding-like object without importing the ORM."""
    obj = MagicMock()
    obj.id = uuid.uuid4()
    obj.user_id = uid
    obj.source_type = source_type
    obj.source_id = source_id
    obj.text_content = text
    obj.embedding = vec
    obj.metadata_ = {}
    return obj


def _make_scalars_result(rows: list[Any]) -> Any:
    """Build a mock execute() return value whose .scalars().all() returns *rows*."""
    scalars_mock = MagicMock()
    scalars_mock.all.return_value = rows
    result_mock = MagicMock()
    result_mock.scalars.return_value = scalars_mock
    return result_mock
