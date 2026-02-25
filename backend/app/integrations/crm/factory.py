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
    """Return the appropriate CRM client based on configuration.

    The CRM provider is determined by the CRM_PROVIDER setting:
    - "database": Uses DatabaseCRM for PostgreSQL storage (default)
    - "hubspot": Uses HubSpotCRM for HubSpot integration
    - "mock": Uses MockCRM for testing

    Args:
        credentials: Optional CRM credentials (used for HubSpot)
        db: Database session (required for DatabaseCRM)
        user_id: User ID (required for DatabaseCRM)

    Returns:
        CRMBase: Configured CRM client

    Raises:
        ValueError: If required configuration is missing
    """
    provider = settings.CRM_PROVIDER.lower()

    if provider == "hubspot":
        from app.integrations.crm.hubspot_crm import HubSpotCRM
        logger.debug("CRM factory: returning HubSpotCRM")
        return HubSpotCRM()

    if provider == "mock":
        from app.integrations.crm.mock_crm import MockCRM
        logger.debug("CRM factory: returning MockCRM")
        return MockCRM()

    # Default to database CRM
    if db is not None and user_id is not None:
        from app.integrations.crm.db_crm import DatabaseCRM
        logger.debug("CRM factory: returning DatabaseCRM for user=%s", user_id)
        return DatabaseCRM(db=db, user_id=user_id)

    from app.integrations.crm.mock_crm import MockCRM
    logger.debug("CRM factory: returning MockCRM (no db session provided)")
    return MockCRM()
