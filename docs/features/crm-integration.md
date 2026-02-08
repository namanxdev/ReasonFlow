# CRM Integration

## Overview

ReasonFlow includes an abstract CRM layer with a mock implementation for development and a pluggable adapter pattern for production CRM systems.

## Architecture

```
CRMBase (Abstract)
├── MockCRM       (in-memory dict, for dev/testing)
├── SalesforceCRM (future)
└── HubSpotCRM    (future)
```

## CRMBase Interface

```python
class CRMBase(ABC):
    async def get_contact(email: str) -> Contact | None
    async def update_contact(email: str, data: dict) -> Contact
    async def search_contacts(query: str) -> list[Contact]
```

## MockCRM

Pre-loaded with sample contacts for development:
- In-memory dictionary storage
- Supports all CRUD operations
- Seeded with test data on initialization

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | /crm/contacts/{email} | Get contact by email |
| PUT | /crm/contacts/{email} | Update contact data |

## Agent Integration

CRM tools registered in ToolManager:
- `get_contact` — fetches sender information before generating response
- `update_contact` — updates contact record after interaction

## Contact Schema

```json
{
  "email": "alice@example.com",
  "name": "Alice Smith",
  "company": "Acme Corp",
  "title": "VP of Engineering",
  "last_interaction": "2026-01-20T10:00:00Z",
  "notes": "Interested in enterprise plan",
  "tags": ["prospect", "enterprise"]
}
```
