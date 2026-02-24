"""CRM client factory."""

from __future__ import annotations

import logging
import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.integrations.crm.base import CRMBase

logger = logging.getLogger(__name__)


def get_crm_client(
    credentials: dict[str, Any] | None = None,
    db: AsyncSession | None = None,
    user_id: uuid.UUID | None = None,
) -> CRMBase:
    """Return the appropriate CRM client.

    When db and user_id are provided, returns DatabaseCRM for persistent storage.
    Otherwise falls back to MockCRM.
    """
    if db is not None and user_id is not None:
        from app.integrations.crm.db_crm import DatabaseCRM
        logger.debug("CRM factory: returning DatabaseCRM for user=%s", user_id)
        return DatabaseCRM(db=db, user_id=user_id)

    from app.integrations.crm.mock_crm import MockCRM
    logger.debug("CRM factory: returning MockCRM (no db session provided)")
    return MockCRM()
