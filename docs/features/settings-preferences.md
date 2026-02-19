# Settings/Preferences System

## Overview

The Settings/Preferences system allows users to customize ReasonFlow behavior through configurable options like auto-approval thresholds, sync frequency, and notification preferences.

## API Endpoints

### Get Current Settings

```
GET /api/v1/settings
```

Returns the current user's preferences. Creates default preferences if none exist.

**Response (200 OK):**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "user_id": "550e8400-e29b-41d4-a716-446655440001",
  "auto_approval_threshold": 0.9,
  "email_sync_frequency_minutes": 15,
  "notification_settings": {
    "email": true,
    "push": false,
    "digest": true
  },
  "timezone": "UTC",
  "daily_digest_enabled": true,
  "auto_classify_on_sync": true,
  "max_auto_responses_per_day": 50,
  "created_at": "2026-02-19T10:30:00Z",
  "updated_at": "2026-02-19T10:30:00Z"
}
```

### Update Settings

```
PUT /api/v1/settings
```

Partially or fully updates user preferences. Only fields provided in the request body are modified.

**Request Body:**
```json
{
  "auto_approval_threshold": 0.85,
  "email_sync_frequency_minutes": 10,
  "daily_digest_enabled": false
}
```

All fields are optional. Available fields:

| Field | Type | Range | Description |
|-------|------|-------|-------------|
| `auto_approval_threshold` | float | 0.0 - 1.0 | Confidence level required for auto-approving AI-generated responses |
| `email_sync_frequency_minutes` | int | 1 - 1440 | How often to sync emails from Gmail (in minutes) |
| `notification_settings` | object | - | Notification preferences with `email`, `push`, `digest` boolean fields |
| `timezone` | string | - | IANA timezone identifier (e.g., "America/New_York", "Europe/London") |
| `daily_digest_enabled` | boolean | - | Whether to send daily summary emails |
| `auto_classify_on_sync` | boolean | - | Automatically classify new emails during Gmail sync |
| `max_auto_responses_per_day` | int | 0 - 1000 | Maximum number of auto-approved responses per day |

**Response (200 OK):**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "user_id": "550e8400-e29b-41d4-a716-446655440001",
  "auto_approval_threshold": 0.85,
  "email_sync_frequency_minutes": 10,
  "notification_settings": {
    "email": true,
    "push": false,
    "digest": true
  },
  "timezone": "UTC",
  "daily_digest_enabled": false,
  "auto_classify_on_sync": true,
  "max_auto_responses_per_day": 50,
  "created_at": "2026-02-19T10:30:00Z",
  "updated_at": "2026-02-19T14:45:00Z"
}
```

**Error Responses:**
- `401 Unauthorized` - Invalid or missing authentication token
- `422 Unprocessable Entity` - Validation error (e.g., threshold > 1.0)

## Default Values

New users get these default settings automatically:

| Setting | Default | Rationale |
|---------|---------|-----------|
| `auto_approval_threshold` | 0.9 | High confidence required to minimize errors |
| `email_sync_frequency_minutes` | 15 | Balance between freshness and API quota |
| `notification_settings.email` | true | Email notifications enabled |
| `notification_settings.push` | false | Push notifications disabled by default |
| `notification_settings.digest` | true | Daily digest enabled |
| `timezone` | "UTC" | Safe default, user should customize |
| `daily_digest_enabled` | true | Help users stay informed |
| `auto_classify_on_sync` | true | Immediate value from AI classification |
| `max_auto_responses_per_day` | 50 | Reasonable limit to prevent over-automation |

## Frontend Requirements

### Settings Page Components

1. **Auto-Approval Threshold Slider**
   - Range: 0.0 to 1.0
   - Step: 0.05
   - Visual indicator for confidence levels (Low/Medium/High)
   - Help text explaining what this controls

2. **Sync Frequency Selector**
   - Dropdown with common intervals: 5, 10, 15, 30, 60 minutes
   - Or numeric input with min=1, max=1440

3. **Timezone Selector**
   - Dropdown with IANA timezone list
   - Group by region (America, Europe, Asia, etc.)
   - Default to browser timezone detection

4. **Notification Toggles**
   - Email notifications (on/off)
   - Push notifications (on/off)
   - Daily digest (on/off)

5. **Automation Settings**
   - Auto-classify on sync (toggle)
   - Max auto-responses per day (numeric input, 0-1000)

### UX Considerations

- Auto-save on change or explicit "Save" button
- Show loading state during API calls
- Toast notifications for success/error feedback
- Form validation with clear error messages
- Reset to defaults option
