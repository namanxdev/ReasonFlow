# Real-time Notifications (WebSocket)

ReasonFlow provides real-time notifications via WebSocket for email events, draft updates, and batch progress. This enables the frontend to show live updates without polling.

## Overview

The notification system uses:
- **Redis Pub/Sub** for event broadcasting
- **FastAPI WebSocket** endpoint for client connections
- **JWT Authentication** via first message protocol

## WebSocket Endpoint

```
ws://localhost:8000/api/v1/notifications/ws
```

For production with SSL:
```
wss://your-domain.com/api/v1/notifications/ws
```

## Connection Protocol

### 1. Connect

```javascript
const ws = new WebSocket('ws://localhost:8000/api/v1/notifications/ws');
```

### 2. Authenticate (First Message)

Must send authentication message immediately after connection:

```javascript
ws.onopen = () => {
  ws.send(JSON.stringify({
    token: '<jwt_access_token>'
  }));
};
```

### 3. Receive Connected Confirmation

```javascript
ws.onmessage = (event) => {
  const message = JSON.parse(event.data);
  
  if (message.type === 'connected') {
    console.log('Connected as user:', message.user_id);
    // Now you'll start receiving events
  }
};
```

### 4. Handle Events

```javascript
ws.onmessage = (event) => {
  const message = JSON.parse(event.data);
  
  switch (message.type) {
    case 'email_received':
      showToast(`New email: ${message.data.subject}`);
      updateInboxBadge();
      break;
    case 'draft_ready':
      showToast('Draft response ready for review');
      updateDraftsBadge();
      break;
    // ... handle other event types
  }
};
```

## Event Types

### EMAIL_RECEIVED

Triggered when a new email is fetched from Gmail.

```json
{
  "type": "email_received",
  "user_id": "uuid",
  "data": {
    "email_id": "uuid",
    "subject": "Meeting tomorrow",
    "sender": "John Doe <john@example.com>"
  },
  "timestamp": "2026-02-19T10:30:00+00:00"
}
```

### EMAIL_CLASSIFIED

Triggered when an email is classified by the AI agent.

```json
{
  "type": "email_classified",
  "user_id": "uuid",
  "data": {
    "email_id": "uuid",
    "classification": "meeting_request",
    "confidence": 0.95
  },
  "timestamp": "2026-02-19T10:30:05+00:00"
}
```

### DRAFT_READY

Triggered when a draft response is generated.

```json
{
  "type": "draft_ready",
  "user_id": "uuid",
  "data": {
    "draft_id": "uuid",
    "email_id": "uuid",
    "requires_approval": true
  },
  "timestamp": "2026-02-19T10:30:10+00:00"
}
```

### DRAFT_APPROVED

Triggered when a draft is approved by the user.

```json
{
  "type": "draft_approved",
  "user_id": "uuid",
  "data": {
    "draft_id": "uuid",
    "email_id": "uuid"
  },
  "timestamp": "2026-02-19T10:35:00+00:00"
}
```

### DRAFT_REJECTED

Triggered when a draft is rejected by the user.

```json
{
  "type": "draft_rejected",
  "user_id": "uuid",
  "data": {
    "draft_id": "uuid",
    "email_id": "uuid",
    "reason": null
  },
  "timestamp": "2026-02-19T10:35:00+00:00"
}
```

### EMAIL_SENT

Triggered when a draft is successfully sent via Gmail.

```json
{
  "type": "email_sent",
  "user_id": "uuid",
  "data": {
    "email_id": "uuid",
    "draft_id": "uuid"
  },
  "timestamp": "2026-02-19T10:35:05+00:00"
}
```

### BATCH_PROGRESS

Triggered during batch operations (sync, classify, process).

```json
{
  "type": "batch_progress",
  "user_id": "uuid",
  "data": {
    "job_id": "uuid",
    "processed": 10,
    "total": 50,
    "percentage": 20
  },
  "timestamp": "2026-02-19T10:30:00+00:00"
}
```

### BATCH_COMPLETE

Triggered when a batch operation completes.

```json
{
  "type": "batch_complete",
  "user_id": "uuid",
  "data": {
    "job_id": "uuid",
    "status": "completed",
    "succeeded": 50,
    "failed": 0
  },
  "timestamp": "2026-02-19T10:31:00+00:00"
}
```

## WebSocket Close Codes

| Code | Reason | Description |
|------|--------|-------------|
| 1000 | Normal closure | Clean disconnect |
| 4001 | Missing token | No token provided in first message |
| 4002 | Invalid token | Token is invalid or expired |
| 4000 | Server error | Internal server error |

## Reconnection Strategy

Implement exponential backoff for reconnection:

```typescript
class NotificationWebSocket {
  private ws: WebSocket | null = null;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 1000; // Start with 1s
  private token: string;

  constructor(token: string) {
    this.token = token;
  }

  connect() {
    this.ws = new WebSocket('ws://localhost:8000/api/v1/notifications/ws');

    this.ws.onopen = () => {
      this.reconnectAttempts = 0;
      this.reconnectDelay = 1000;
      this.ws?.send(JSON.stringify({ token: this.token }));
    };

    this.ws.onclose = (event) => {
      if (event.code === 4001 || event.code === 4002) {
        // Auth errors - don't retry
        console.error('WebSocket auth failed:', event.reason);
        return;
      }
      this.reconnect();
    };

    this.ws.onmessage = (event) => {
      const message = JSON.parse(event.data);
      this.handleMessage(message);
    };
  }

  private reconnect() {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.error('Max reconnection attempts reached');
      return;
    }

    this.reconnectAttempts++;
    setTimeout(() => {
      this.reconnectDelay *= 2; // Exponential backoff
      this.connect();
    }, this.reconnectDelay);
  }

  private handleMessage(message: any) {
    // Handle different event types
    switch (message.type) {
      case 'email_received':
        // Update inbox
        break;
      case 'draft_ready':
        // Update drafts
        break;
      // ... etc
    }
  }

  disconnect() {
    this.ws?.close(1000, 'Client disconnect');
  }
}
```

## Frontend Integration

### React Hook Example

```typescript
// hooks/useNotifications.ts
import { useEffect, useRef, useCallback } from 'react';
import { useAuthStore } from '@/stores/auth';

export function useNotifications(onEvent: (event: any) => void) {
  const wsRef = useRef<WebSocket | null>(null);
  const { token } = useAuthStore();

  useEffect(() => {
    if (!token) return;

    const ws = new WebSocket(process.env.NEXT_PUBLIC_WS_URL!);
    wsRef.current = ws;

    ws.onopen = () => {
      ws.send(JSON.stringify({ token }));
    };

    ws.onmessage = (event) => {
      const message = JSON.parse(event.data);
      if (message.type !== 'connected') {
        onEvent(message);
      }
    };

    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };

    return () => {
      ws.close(1000, 'Component unmount');
    };
  }, [token, onEvent]);

  return wsRef.current;
}
```

### Toast Notifications

```typescript
// components/NotificationProvider.tsx
import { useEffect } from 'react';
import { useToast } from '@/hooks/use-toast';
import { useNotifications } from '@/hooks/useNotifications';

export function NotificationProvider({ children }: { children: React.ReactNode }) {
  const { toast } = useToast();

  const handleEvent = useCallback((event: any) => {
    switch (event.type) {
      case 'email_received':
        toast({
          title: 'New Email',
          description: event.data.subject,
        });
        break;
      case 'draft_ready':
        toast({
          title: 'Draft Ready',
          description: 'A new draft response is ready for review',
        });
        break;
      case 'email_sent':
        toast({
          title: 'Email Sent',
          description: 'Your draft has been sent successfully',
        });
        break;
    }
  }, [toast]);

  useNotifications(handleEvent);

  return <>{children}</>;
}
```

### Live Badge Updates

```typescript
// stores/notificationBadge.ts
import { create } from 'zustand';

interface BadgeState {
  unreadEmails: number;
  pendingDrafts: number;
  incrementUnread: () => void;
  decrementUnread: () => void;
  incrementDrafts: () => void;
  decrementDrafts: () => void;
}

export const useBadgeStore = create<BadgeState>((set) => ({
  unreadEmails: 0,
  pendingDrafts: 0,
  incrementUnread: () => set((s) => ({ unreadEmails: s.unreadEmails + 1 })),
  decrementUnread: () => set((s) => ({ unreadEmails: Math.max(0, s.unreadEmails - 1) })),
  incrementDrafts: () => set((s) => ({ pendingDrafts: s.pendingDrafts + 1 })),
  decrementDrafts: () => set((s) => ({ pendingDrafts: Math.max(0, s.pendingDrafts - 1) })),
}));

// In your notification handler:
const { incrementUnread, incrementDrafts, decrementDrafts } = useBadgeStore();

// On email_received: incrementUnread()
// On draft_ready: incrementDrafts()
// On draft_approved/rejected: decrementDrafts()
```

## Backend Implementation

### Publishing Events

Events are published from services using `publish_event`:

```python
from app.core.events import publish_event, EventType

# In email_service.py after creating new email
await publish_event(
    user_id=user.id,
    event_type=EventType.EMAIL_RECEIVED,
    data={
        "email_id": str(email.id),
        "subject": email.subject,
        "sender": email.sender,
    }
)
```

### Redis Channel Format

Each user has their own channel:
```
events:{user_id}
```

Example:
```
events:123e4567-e89b-12d3-a456-426614174000
```

## Performance Considerations

1. **Connection Limits**: WebSocket connections are held per user. Consider connection pooling for high-traffic scenarios.

2. **Redis Memory**: Pub/Sub channels are lightweight but monitor Redis memory usage with many concurrent users.

3. **Event Size**: Keep event payloads minimal. Large payloads increase bandwidth and Redis memory usage.

4. **Reconnection Storm**: Implement jitter in reconnection logic to prevent thundering herd on server restart.

## Security

1. **Authentication**: All connections require valid JWT token sent as first message.

2. **Authorization**: Users only receive events for their own `user_id`.

3. **Channel Isolation**: Redis channels are user-specific; no cross-user event leakage.

4. **Token Expiry**: Expired tokens are rejected; clients must reconnect with fresh token.

## Testing

### Manual Testing with wscat

```bash
# Install wscat
npm install -g wscat

# Connect and authenticate
wscat -c ws://localhost:8000/api/v1/notifications/ws
> {"token": "<jwt_token>"}
< {"type": "connected", "user_id": "..."}
```

### Trigger Events via API

```bash
# Sync emails to trigger EMAIL_RECEIVED
curl -X POST http://localhost:8000/api/v1/emails/sync \
  -H "Authorization: Bearer <token>"

# Process email to trigger DRAFT_READY
curl -X POST http://localhost:8000/api/v1/emails/<id>/process \
  -H "Authorization: Bearer <token>"
```
