"""CRM client factory."""

from __future__ import annotations

import logging
from typing import Any

from app.core.config import settings
from app.integrations.crm.base import CRMBase

logger = logging.getLogger(__name__)


def get_crm_client(credentials: dict[str, Any] | None = None) -> CRMBase:
    """Return the appropriate CRM client based on application environment."""
    from app.integrations.crm.mock_crm import MockCRM

    if not settings.is_production:
        logger.debug("CRM factory: returning MockCRM (APP_ENV=%s)", settings.APP_ENV)
        return MockCRM()

    logger.info("CRM factory: production environment - falling back to MockCRM")
    return MockCRM()
