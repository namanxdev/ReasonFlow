"""Database-backed CRM implementation."""

from __future__ import annotations

import logging
import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.integrations.crm.base import CRMBase
from app.models.contact import Contact
from app.models.email import Email

logger = logging.getLogger(__name__)


class DatabaseCRM(CRMBase):
    """CRM backed by PostgreSQL via the Contact model."""

    def __init__(self, db: AsyncSession, user_id: uuid.UUID) -> None:
        self._db = db
        self._user_id = user_id

    def _contact_to_dict(self, contact: Contact) -> dict[str, Any]:
        return {
            "email": contact.email,
            "name": contact.name,
            "company": contact.company,
            "title": contact.title,
            "phone": contact.phone,
            "notes": contact.notes,
            "tags": contact.tags or [],
            "metadata": contact.metadata_ or {},
            "last_contacted_at": contact.last_contacted_at.isoformat() if contact.last_contacted_at else None,
            "last_interaction": contact.last_contacted_at.isoformat() if contact.last_contacted_at else None,
            "created_at": contact.created_at.isoformat() if contact.created_at else None,
            "updated_at": contact.updated_at.isoformat() if contact.updated_at else None,
        }

    async def get_contact(self, email: str) -> dict[str, Any] | None:
        result = await self._db.execute(
            select(Contact).where(
                Contact.user_id == self._user_id,
                Contact.email == email.lower(),
            )
        )
        contact = result.scalars().first()
        if contact is None:
            return None
        return self._contact_to_dict(contact)

    async def update_contact(self, email: str, data: dict[str, Any]) -> dict[str, Any]:
        email_lower = email.lower()
        result = await self._db.execute(
            select(Contact).where(
                Contact.user_id == self._user_id,
                Contact.email == email_lower,
            )
        )
        contact = result.scalars().first()

        if contact is None:
            contact = Contact(
                user_id=self._user_id,
                email=email_lower,
            )
            self._db.add(contact)

        for field in ("name", "company", "title", "phone", "notes", "tags"):
            if field in data:
                setattr(contact, field, data[field])
        if "metadata" in data:
            contact.metadata_ = data["metadata"]
        contact.last_contacted_at = datetime.now(UTC)

        await self._db.flush()
        return self._contact_to_dict(contact)

    async def search_contacts(self, query: str) -> list[dict[str, Any]]:
        stmt = select(Contact).where(Contact.user_id == self._user_id)
        if query:
            pattern = f"%{query}%"
            stmt = stmt.where(
                or_(
                    Contact.name.ilike(pattern),
                    Contact.email.ilike(pattern),
                    Contact.company.ilike(pattern),
                    Contact.notes.ilike(pattern),
                )
            )
        stmt = stmt.order_by(Contact.updated_at.desc())
        result = await self._db.execute(stmt)
        return [self._contact_to_dict(c) for c in result.scalars().all()]

    async def list_contacts_paginated(
        self, page: int = 1, per_page: int = 25, query: str | None = None
    ) -> tuple[list[dict[str, Any]], int]:
        base = select(Contact).where(Contact.user_id == self._user_id)
        count_base = select(func.count()).select_from(Contact).where(Contact.user_id == self._user_id)

        if query:
            pattern = f"%{query}%"
            filter_clause = or_(
                Contact.name.ilike(pattern),
                Contact.email.ilike(pattern),
                Contact.company.ilike(pattern),
                Contact.notes.ilike(pattern),
            )
            base = base.where(filter_clause)
            count_base = count_base.where(filter_clause)

        total_result = await self._db.execute(count_base)
        total = total_result.scalar() or 0

        offset = (page - 1) * per_page
        items_result = await self._db.execute(
            base.order_by(Contact.updated_at.desc()).offset(offset).limit(per_page)
        )
        items = [self._contact_to_dict(c) for c in items_result.scalars().all()]
        return items, total

    async def get_contact_emails(
        self, contact_email: str, limit: int = 20
    ) -> list[dict[str, Any]]:
        result = await self._db.execute(
            select(Email)
            .where(
                Email.user_id == self._user_id,
                or_(
                    Email.sender.ilike(f"%{contact_email}%"),
                    Email.recipient.ilike(f"%{contact_email}%"),
                ),
            )
            .order_by(Email.received_at.desc())
            .limit(limit)
        )
        emails = result.scalars().all()
        return [
            {
                "id": str(e.id),
                "subject": e.subject,
                "sender": e.sender,
                "recipient": e.recipient,
                "received_at": e.received_at.isoformat() if e.received_at else None,
                "classification": e.classification.value if e.classification else None,
                "status": e.status.value if e.status else None,
            }
            for e in emails
        ]
