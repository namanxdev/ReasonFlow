# Health Check Endpoint

## Overview

The health check endpoint provides a comprehensive status report of all critical system components. It's designed for monitoring systems, load balancers, and development debugging.

## API Endpoint

### `GET /health`

Returns the current health status of the ReasonFlow application and its dependencies.

#### Response Schema

```json
{
  "status": "healthy" | "unhealthy",
  "checks": {
    "database": {
      "status": "ok" | "error",
      "latency_ms": 12.34,
      "error": null | "error message"
    },
    "redis": {
      "status": "ok" | "error",
      "latency_ms": 5.67,
      "error": null | "error message"
    },
    "gemini_api": {
      "status": "ok" | "not_configured",
      "error": null
    }
  },
  "timestamp": "2026-02-19T10:30:00+00:00"
}
```

#### HTTP Status Codes

| Status Code | Meaning |
|-------------|---------|
| 200 OK | All critical systems are healthy |
| 503 Service Unavailable | One or more critical systems (DB, Redis) are failing |

#### Subsystem Details

| Subsystem | Description | Critical? |
|-----------|-------------|-----------|
| `database` | PostgreSQL connectivity via `SELECT 1` | Yes |
| `redis` | Redis connectivity via `PING` | Yes |
| `gemini_api` | GEMINI_API_KEY presence check | No |

## Production Configuration Validation

### Startup Validation

On application startup in production mode (`APP_ENV=production`), the system validates:

1. **JWT_SECRET_KEY** - Must not be the default value (`"change-me-in-production"`) or empty
2. **GEMINI_API_KEY** - Must be configured
3. **DATABASE_URL** - Must be set and non-empty

If any validation fails, the application raises a `ValueError` and refuses to start.

### Manual Validation

You can validate configuration programmatically:

```python
from app.core.config import settings

# Raises ValueError if production config is invalid
settings.validate_production()
```

## Frontend Requirements

### Status Indicator Component

The frontend should display a status indicator based on the health endpoint:

```typescript
interface HealthStatus {
  status: 'healthy' | 'unhealthy';
  checks: {
    database: { status: 'ok' | 'error'; latency_ms?: number };
    redis: { status: 'ok' | 'error'; latency_ms?: number };
    gemini_api: { status: 'ok' | 'not_configured' };
  };
  timestamp: string;
}
```

### Recommended UI Elements

1. **Header Status Dot**: Green/Red indicator in the app header
   - Green: `status === 'healthy'`
   - Red: `status === 'unhealthy'`
   - Gray: Loading or error fetching health

2. **Tooltip/Popover**: On hover, show:
   - Database latency (green if < 100ms, yellow if < 500ms, red otherwise)
   - Redis latency
   - Gemini API configuration status

3. **Auto-refresh**: Poll `/health` every 30 seconds

### Example React Component

```tsx
const HealthIndicator: React.FC = () => {
  const { data: health, isLoading } = useQuery({
    queryKey: ['health'],
    queryFn: fetchHealth,
    refetchInterval: 30000, // 30 seconds
  });

  if (isLoading) return <span className="status-dot gray" />;
  if (!health) return <span className="status-dot gray" />;

  const color = health.status === 'healthy' ? 'green' : 'red';
  
  return (
    <div className="health-indicator" title={`DB: ${health.checks.database.latency_ms}ms`}>
      <span className={`status-dot ${color}`} />
    </div>
  );
};
```

## Monitoring Integration

### Kubernetes Liveness/Readiness Probes

```yaml
livenessProbe:
  httpGet:
    path: /health
    port: 8000
  initialDelaySeconds: 10
  periodSeconds: 30

readinessProbe:
  httpGet:
    path: /health
    port: 8000
  initialDelaySeconds: 5
  periodSeconds: 10
```

### Docker HEALTHCHECK

```dockerfile
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1
```

## Development Notes

- Database latency is measured in milliseconds using `time.perf_counter()` for high precision
- Redis ping also measures round-trip latency
- Gemini API check only validates key presence, not actual API connectivity (to avoid API rate limits)
- All timestamps are returned in ISO 8601 format with UTC timezone
