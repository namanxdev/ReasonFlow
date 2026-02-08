# API Reference

Base URL: `http://localhost:8000/api/v1`

All endpoints except `/auth/*` require `Authorization: Bearer <jwt_token>` header.

---

## Authentication

### POST /auth/register
Create a new user account.

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "securepassword"
}
```

**Response (201):**
```json
{
  "id": "uuid",
  "email": "user@example.com",
  "access_token": "jwt_token",
  "token_type": "bearer"
}
```

### POST /auth/login
Authenticate and get a JWT token.

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "securepassword"
}
```

**Response (200):**
```json
{
  "access_token": "jwt_token",
  "token_type": "bearer",
  "expires_in": 1800
}
```

### POST /auth/refresh
Refresh an expiring JWT token.

**Response (200):**
```json
{
  "access_token": "new_jwt_token",
  "token_type": "bearer"
}
```

---

## Gmail OAuth

### GET /auth/gmail/url
Get the Gmail OAuth consent URL.

**Response (200):**
```json
{
  "url": "https://accounts.google.com/o/oauth2/auth?..."
}
```

### POST /auth/gmail/callback
Exchange OAuth code for tokens.

**Request Body:**
```json
{
  "code": "oauth_authorization_code"
}
```

**Response (200):**
```json
{
  "status": "connected",
  "email": "user@gmail.com"
}
```

---

## Emails

### GET /emails
List emails with optional filters.

**Query Parameters:**
| Param | Type | Description |
|-------|------|-------------|
| status | string | Filter by status (pending, drafted, sent, etc.) |
| classification | string | Filter by classification |
| search | string | Search subject/sender |
| page | int | Page number (default: 1) |
| per_page | int | Items per page (default: 20) |

**Response (200):**
```json
{
  "items": [
    {
      "id": "uuid",
      "gmail_id": "msg_id",
      "subject": "Meeting Tomorrow",
      "sender": "alice@example.com",
      "received_at": "2026-02-06T10:00:00Z",
      "classification": "meeting_request",
      "confidence": 0.95,
      "status": "drafted"
    }
  ],
  "total": 100,
  "page": 1,
  "per_page": 20
}
```

### GET /emails/{id}
Get a single email with full details.

### POST /emails/{id}/process
Trigger agent processing for an email.

**Response (202):**
```json
{
  "trace_id": "uuid",
  "status": "processing"
}
```

### GET /emails/sync
Fetch and store new emails from Gmail.

---

## Drafts

### GET /drafts
List drafts awaiting review.

### POST /drafts/{id}/approve
Approve and send a draft.

### POST /drafts/{id}/reject
Reject a draft.

### PUT /drafts/{id}
Edit a draft before sending.

**Request Body:**
```json
{
  "content": "Updated response text..."
}
```

---

## Traces

### GET /traces
List recent agent execution traces.

**Response (200):**
```json
{
  "items": [
    {
      "trace_id": "uuid",
      "email_subject": "Meeting Tomorrow",
      "classification": "meeting_request",
      "total_latency_ms": 2340,
      "step_count": 6,
      "status": "completed",
      "created_at": "2026-02-06T10:01:00Z"
    }
  ]
}
```

### GET /traces/{trace_id}
Get detailed trace with all steps.

**Response (200):**
```json
{
  "trace_id": "uuid",
  "email": { ... },
  "steps": [
    {
      "step_name": "classify",
      "step_order": 1,
      "input_state": { ... },
      "output_state": { "classification": "meeting_request", "confidence": 0.95 },
      "latency_ms": 450,
      "tool_executions": []
    }
  ],
  "total_latency_ms": 2340
}
```

---

## Metrics

### GET /metrics/intents
Intent distribution over time.

### GET /metrics/latency
Agent response latency statistics.

### GET /metrics/tools
Tool execution success rates.

---

## Calendar

### GET /calendar/availability
Check free time slots.

**Query Parameters:**
| Param | Type | Description |
|-------|------|-------------|
| start | datetime | Start of range |
| end | datetime | End of range |

### POST /calendar/events
Create a calendar event.

---

## CRM

### GET /crm/contacts/{email}
Get contact information by email.

### PUT /crm/contacts/{email}
Update contact information.

---

## Common Response Codes

| Code | Description |
|------|-------------|
| 200 | Success |
| 201 | Created |
| 202 | Accepted (async processing started) |
| 400 | Bad request / validation error |
| 401 | Unauthorized (missing/invalid JWT) |
| 403 | Forbidden |
| 404 | Not found |
| 429 | Rate limited |
| 500 | Internal server error |
