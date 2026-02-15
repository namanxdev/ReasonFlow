"""CRM integration package."""

from __future__ import annotations

from app.integrations.crm.base import CRMBase
from app.integrations.crm.factory import get_crm_client
from app.integrations.crm.mock_crm import MockCRM

__all__ = ["CRMBase", "MockCRM", "get_crm_client"]
