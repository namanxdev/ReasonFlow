# Docker Setup for ReasonFlow

## Overview

This guide covers the Docker-based deployment setup for the ReasonFlow backend. The Docker configuration provides a containerized environment with all required services (backend API and PostgreSQL database with pgvector) for consistent and reproducible development and deployment.

## Architecture

The Docker setup consists of two services:

```
┌─────────────────────────────────────────────┐
│                Docker Compose Stack               │
├─────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────────┐   │
│  │   Backend    │  │   PostgreSQL     │   │
│  │  (FastAPI)   │◄─┤   (pgvector)     │   │
│  │   Port: 8000 │  │    Port: 5432    │   │
│  └──────────────┘  └──────────────────┘   │
└─────────────────────────────────────────────┘
```

### Services

| Service | Image | Purpose | Port |
|---------|-------|---------|------|
| **backend** | Custom (Python 3.11) | FastAPI application server | 8000 |
| **db** | pgvector/pgvector:pg16 | PostgreSQL with vector extension | 5432 |

## Prerequisites

Before you begin, ensure you have the following installed:

- **Docker** (version 20.10+): [Install Docker](https://docs.docker.com/get-docker/)
- **Docker Compose** (version 2.0+): Usually included with Docker Desktop

Verify your installation:

```bash
docker --version
docker compose version
```

## Environment Setup

### 1. Create Environment File

The backend service requires environment variables for configuration. These are loaded from `backend/.env`.

```bash
# Copy the example environment file
cp backend/.env.example backend/.env

# Edit the file with your actual values
# Note: For Docker, the DATABASE_URL is automatically
# overridden in docker-compose.yml to use Docker service names
```

### 2. Required Environment Variables

Ensure your `backend/.env` file contains at least these required variables:

```bash
# Database (will be overridden in Docker to use 'db' service)
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/reasonflow

# Google Gemini API (required for AI features)
GEMINI_API_KEY=your-gemini-api-key-here

# Gmail OAuth (required for email integration)
GMAIL_CLIENT_ID=your-gmail-client-id
GMAIL_CLIENT_SECRET=your-gmail-client-secret
GMAIL_REDIRECT_URI=http://localhost:8000/api/v1/auth/gmail/callback

# JWT (required for authentication)
JWT_SECRET_KEY=your-super-secret-jwt-key-change-in-production
JWT_ALGORITHM=HS256
JWT_EXPIRATION_MINUTES=30

# CORS
CORS_ORIGINS=["http://localhost:3000"]

# App Settings
APP_ENV=development
APP_DEBUG=true
```

## Commands

### Start All Services

Build and start all services in detached mode:

```bash
docker compose up --build -d
```

Or using the Makefile:

```bash
make docker-up
```

This command will:
1. Build the backend Docker image (if not already built or if Dockerfile changed)
2. Start PostgreSQL and wait for it to be healthy
3. Start the backend service

### Stop All Services

Stop and remove containers:

```bash
docker compose down
```

Or using the Makefile:

```bash
make docker-down
```

To also remove volumes (⚠️ **this will delete all data**):

```bash
docker compose down -v
```

### View Logs

Follow logs from all services:

```bash
docker compose logs -f
```

Or using the Makefile:

```bash
make docker-logs
```

View logs for a specific service:

```bash
docker compose logs -f backend
docker compose logs -f db
```

### Database Migrations

Run Alembic migrations to set up the database schema:

```bash
docker compose exec backend alembic upgrade head
```

Or using the Makefile:

```bash
make docker-migrate
```

Create a new migration:

```bash
docker compose exec backend alembic revision --autogenerate -m "description"
```

### Other Useful Commands

Restart a specific service:

```bash
docker compose restart backend
```

Execute a command in the backend container:

```bash
docker compose exec backend python -c "print('Hello from container')"
```

Access the database shell:

```bash
docker compose exec db psql -U postgres -d reasonflow
```

## Service Descriptions

### Backend Service

- **Build**: Multi-stage build using `python:3.11-slim`
- **User**: Runs as non-root `appuser` for security
- **Port**: Exposes 8000 for API access
- **Healthcheck**: HTTP check on `/health` endpoint
- **Volumes**: Mounts `app/` directory as read-only for development

### Database Service (PostgreSQL + pgvector)

- **Image**: `pgvector/pgvector:pg16` (PostgreSQL 16 with pgvector extension)
- **Port**: Exposes 5432 for external access (optional)
- **Volumes**: Persistent storage in `pgdata` volume
- **Healthcheck**: Uses `pg_isready` to verify database availability
- **Credentials**: Username `postgres`, password `postgres`, database `reasonflow`

## Network Configuration

All services communicate over a custom Docker bridge network named `reasonflow-network`. Service names are used as hostnames:

- Backend connects to database at: `db:5432`

## Troubleshooting

### Services Won't Start

**Issue**: `docker compose up` fails or services exit immediately

**Solution**:
```bash
# Check for port conflicts
netstat -an | findstr "8000"
netstat -an | findstr "5432"

# View detailed logs
docker compose logs

# Restart with fresh build
docker compose down
docker compose up --build
```

### Database Connection Errors

**Issue**: Backend fails to connect to database

**Solution**:
```bash
# Check database health
docker compose ps

# Verify database is ready
docker compose exec db pg_isready -U postgres

# Check logs
docker compose logs db
```

### Migration Failures

**Issue**: Alembic migrations fail to run

**Solution**:
```bash
# Ensure database is healthy first
docker compose ps

# Run migrations with verbose output
docker compose exec backend alembic upgrade head -v

# Check migration history
docker compose exec backend alembic history
```

### Permission Denied Errors

**Issue**: Permission errors when running commands

**Solution**: On Linux/macOS, you may need to adjust file permissions:
```bash
# Fix ownership (Linux only)
sudo chown -R $USER:$USER .
```

### Environment Variables Not Loading

**Issue**: Backend not recognizing environment variables

**Solution**:
- Verify `.env` file exists in `backend/` directory
- Check that variables are not commented out
- Ensure no spaces around `=` in `.env` file
- Restart services after modifying `.env`:
  ```bash
  docker compose down
  docker compose up -d
  ```

## Performance Tips

### For Development

1. **Volume Mounts**: The backend service mounts the `app/` directory as read-only for hot-reloading during development
2. **Build Cache**: Docker caches layers; use `docker compose build --no-cache` only when necessary
3. **Detached Mode**: Use `-d` flag to run services in background

### For Production

1. **Remove Volume Mounts**: Remove the read-only volume mount for production builds
2. **Environment Variables**: Set `APP_ENV=production` and `APP_DEBUG=false`
3. **Secrets**: Use Docker secrets or external secret management for sensitive values
4. **Resources**: Set memory and CPU limits in `docker-compose.yml`:
   ```yaml
   deploy:
     resources:
       limits:
         cpus: '1.0'
         memory: 512M
   ```

## See Also

- [System Architecture](../architecture/system-overview.md)
- [Database Schema](../architecture/database-schema.md)
- [API Reference](../architecture/api-reference.md)
