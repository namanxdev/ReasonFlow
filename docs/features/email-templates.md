# Email Templates System

The Email Templates System provides reusable response templates with variable substitution for ReasonFlow users.

## Overview

Email templates allow users to create pre-defined response templates with dynamic variables. This speeds up the email drafting process by providing a library of common responses that can be customized with specific values.

## Features

- **CRUD Operations**: Create, read, update, and delete email templates
- **Variable Substitution**: Use `{{variable_name}}` syntax for dynamic content
- **Categorization**: Organize templates by category (e.g., "sales", "support")
- **Template Rendering**: Preview rendered templates with actual values

## API Reference

### Base URL
```
/api/v1/templates
```

### Endpoints

#### List Templates
```http
GET /api/v1/templates?category={category}&skip={skip}&limit={limit}
```

Query Parameters:
- `category` (optional): Filter by template category
- `skip` (optional, default: 0): Number of records to skip
- `limit` (optional, default: 100, max: 1000): Maximum records to return

**Response (200 OK):**
```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "user_id": "550e8400-e29b-41d4-a716-446655440001",
    "name": "Welcome Email",
    "subject_template": "Welcome, {{customer_name}}!",
    "body_template": "Hi {{customer_name}},\n\nWelcome to our service. Your order {{order_id}} has been received.",
    "category": "onboarding",
    "variables": ["customer_name", "order_id"],
    "is_active": true,
    "created_at": "2026-02-19T10:00:00Z",
    "updated_at": "2026-02-19T10:00:00Z"
  }
]
```

#### Create Template
```http
POST /api/v1/templates
```

**Request Body:**
```json
{
  "name": "Welcome Email",
  "subject_template": "Welcome, {{customer_name}}!",
  "body_template": "Hi {{customer_name}},\n\nWelcome to our service. Your order {{order_id}} has been received.",
  "category": "onboarding",
  "variables": ["customer_name", "order_id"],
  "is_active": true
}
```

**Response (201 Created):**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "user_id": "550e8400-e29b-41d4-a716-446655440001",
  "name": "Welcome Email",
  "subject_template": "Welcome, {{customer_name}}!",
  "body_template": "Hi {{customer_name}},\n\nWelcome to our service. Your order {{order_id}} has been received.",
  "category": "onboarding",
  "variables": ["customer_name", "order_id"],
  "is_active": true,
  "created_at": "2026-02-19T10:00:00Z",
  "updated_at": "2026-02-19T10:00:00Z"
}
```

Notes:
- Variables are automatically extracted from `subject_template` and `body_template` if not provided
- `subject_template` max length: 998 characters (RFC 2822)
- `name` max length: 200 characters
- `category` max length: 50 characters

#### Get Single Template
```http
GET /api/v1/templates/{template_id}
```

**Response (200 OK):**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "user_id": "550e8400-e29b-41d4-a716-446655440001",
  "name": "Welcome Email",
  "subject_template": "Welcome, {{customer_name}}!",
  "body_template": "Hi {{customer_name}},\n\nWelcome to our service.",
  "category": "onboarding",
  "variables": ["customer_name"],
  "is_active": true,
  "created_at": "2026-02-19T10:00:00Z",
  "updated_at": "2026-02-19T10:00:00Z"
}
```

#### Update Template
```http
PUT /api/v1/templates/{template_id}
```

**Request Body:**
```json
{
  "name": "Updated Welcome Email",
  "subject_template": "Welcome aboard, {{customer_name}}!",
  "is_active": true
}
```

**Response (200 OK):**
Returns the updated template object.

Notes:
- Only provided fields are updated (partial update)
- Variables are re-extracted automatically if templates are modified
- Extra fields are rejected (422 error)

#### Delete Template
```http
DELETE /api/v1/templates/{template_id}
```

**Response (204 No Content)**

Notes:
- Templates are soft-deleted (deactivated) and remain in the database
- Inactive templates are excluded from list results

#### Render Template
```http
POST /api/v1/templates/{template_id}/render
```

**Request Body:**
```json
{
  "variables": {
    "customer_name": "John Doe",
    "order_id": "ORD-12345"
  }
}
```

**Response (200 OK):**
```json
{
  "subject": "Welcome, John Doe!",
  "body": "Hi John Doe,\n\nWelcome to our service. Your order ORD-12345 has been received."
}
```

**Error Response (400 Bad Request):**
```json
{
  "detail": "Missing required variables: ['order_id']"
}
```

## Variable Syntax

Templates use double curly braces for variable placeholders:

```
Hello {{customer_name}},

Your order {{order_id}} has been {{status}}.
```

### Rules

1. **Variable Names**: Must contain only word characters (letters, numbers, underscore)
2. **Case Sensitive**: `{{CustomerName}}` is different from `{{customer_name}}`
3. **Missing Variables**: Rendering fails with 400 error if required variables are not provided
4. **Auto-Extraction**: Variables are automatically detected from template content

### Supported Variable Types

All variable values are converted to strings during rendering:

```json
{
  "variables": {
    "customer_name": "John Doe",      // String
    "order_id": "ORD-12345",          // String
    "total": 99.99,                    // Number (converted to string)
    "is_vip": true                     // Boolean (converted to "True"/"False")
  }
}
```

## Common Use Cases

### Welcome Email
```json
{
  "name": "New Customer Welcome",
  "category": "onboarding",
  "subject_template": "Welcome to {{company_name}}, {{customer_name}}!",
  "body_template": "Hi {{customer_name}},\n\nThank you for joining {{company_name}}. We're excited to have you on board!\n\nYour account manager is {{account_manager}}.\n\nBest regards,\nThe {{company_name}} Team"
}
```

### Order Confirmation
```json
{
  "name": "Order Confirmation",
  "category": "sales",
  "subject_template": "Order {{order_id}} Confirmation",
  "body_template": "Dear {{customer_name}},\n\nThank you for your order!\n\nOrder ID: {{order_id}}\nTotal: ${{total}}\nExpected Delivery: {{delivery_date}}\n\nIf you have any questions, please contact us."
}
```

### Meeting Request
```json
{
  "name": "Meeting Request",
  "category": "meetings",
  "subject_template": "Meeting Request: {{topic}}",
  "body_template": "Hi {{recipient_name}},\n\nI'd like to schedule a meeting to discuss {{topic}}.\n\nProposed times:\n{{proposed_times}}\n\nPlease let me know which works best for you.\n\nBest,\n{{sender_name}}"
}
```

## Frontend Integration Requirements

### Template List Page
- Display templates in a table or card grid
- Filter by category
- Search by name
- Sort by name, category, or updated date
- Actions: Edit, Delete, Preview

### Template Editor
- Form with fields:
  - Name (required, max 200 chars)
  - Category (optional, max 50 chars)
  - Subject Template (required, max 998 chars)
  - Body Template (required, textarea)
  - Variables (auto-extracted, display as tags)
  - Active Status (toggle)
- Real-time variable extraction display
- Character count for subject (warn near 998 limit)

### Template Picker in Draft View
- Dropdown/picker in draft composition area
- Filter/search templates
- Preview on hover
- One-click insert with variable mapping:
  - Auto-map known variables (email sender → customer_name)
  - Show input fields for unmapped variables
  - Live preview before insertion

### Template Preview Modal
- Render template with sample data
- Input fields for each variable
- Real-time preview of subject and body
- Copy to clipboard or insert into draft

## Error Handling

| Status Code | Scenario |
|------------|----------|
| 400 | Missing required variables during render |
| 401 | Unauthorized (invalid/missing JWT) |
| 404 | Template not found or doesn't belong to user |
| 422 | Invalid request data (validation error) |

## Database Schema

```sql
CREATE TABLE email_templates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    name VARCHAR(200) NOT NULL,
    subject_template VARCHAR(998) NOT NULL,
    body_template TEXT NOT NULL,
    category VARCHAR(50),
    variables JSON DEFAULT '[]',
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX ix_email_templates_user_id_category ON email_templates(user_id, category);
```

## Related Files

- **Model**: `backend/app/models/email_template.py`
- **Schema**: `backend/app/schemas/template.py`
- **Service**: `backend/app/services/template_service.py`
- **API Routes**: `backend/app/api/routes/templates.py`
- **Migration**: `backend/alembic/versions/003_email_templates.py`
