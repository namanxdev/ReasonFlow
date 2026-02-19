# CI/CD Pipelines

This document describes the continuous integration and continuous deployment (CI/CD) setup for ReasonFlow.

## Overview

ReasonFlow uses GitHub Actions for automated testing, linting, type checking, and Docker image builds. The CI/CD pipelines ensure code quality and enable automated deployments.

## Workflows

### `test.yml` — Continuous Integration

**Triggers:** Push and pull request events to any branch.

This workflow runs three parallel jobs to validate code quality:

#### Lint Job
- Runs `ruff` to check Python code style and formatting
- Fails if any linting errors are found

#### Type-Check Job
- Installs backend dependencies with dev extras
- Runs `mypy` for static type checking on the `app` package
- Catches type errors before runtime

#### Test Job
- Runs the full test suite with pytest
- Includes service containers for integration testing:
  - **PostgreSQL** (`pgvector/pgvector:pg16`) — Database with pgvector extension
  - **Redis** (`redis:7-alpine`) — Cache and session store
- Generates coverage reports in XML format
- Sets required environment variables for test execution

### `build.yml` — Continuous Deployment

**Triggers:** Push to `main` branch or version tags (`v*`)

This workflow builds and publishes Docker images:

1. **Login** to GitHub Container Registry (GHCR)
2. **Generate metadata** for image tags:
   - Branch name (e.g., `main`)
   - Semantic version from git tags (e.g., `v1.2.3`)
   - Short SHA commit hash
3. **Build and push** Docker image from `./backend` context

Published images are available at:
```
ghcr.io/{owner}/{repository}:{tag}
```

## Required Secrets

| Secret | Description | Required By |
|--------|-------------|-------------|
| `GITHUB_TOKEN` | Auto-provided by GitHub Actions for GHCR authentication | `build.yml` |

No additional secrets are required. The `GITHUB_TOKEN` is automatically available in workflow runs.

## Branch Protection Recommendations

To maintain code quality, enable these branch protection rules for `main`:

1. **Require pull request reviews** before merging
2. **Require status checks to pass**:
   - `lint`
   - `type-check`
   - `test`
3. **Require branches to be up to date** before merging
4. **Restrict pushes** to authorized users only

Configure in: **Settings → Branches → Add rule**

## Local Testing Commands

Before pushing, run these commands locally to ensure CI will pass:

```bash
# Linting
cd backend
ruff check .

# Type checking
cd backend
mypy app

# Run tests (requires local PostgreSQL and Redis)
cd backend
pytest -v

# Or with coverage
cd backend
pytest -v --cov=app --cov-report=html
```

### Using Docker for Local Testing

To test in an environment closer to CI:

```bash
# Start services
docker-compose up -d postgres redis

# Run tests in container
docker-compose run --rm backend pytest -v

# Or run all checks
docker-compose run --rm backend sh -c "ruff check . && mypy app && pytest -v"
```

## Troubleshooting

### Common Issues

**Tests fail in CI but pass locally:**
- Check database migrations are applied in CI
- Verify environment variables match between local and CI

**Docker build fails:**
- Ensure `backend/Dockerfile` exists and is valid
- Check that `pyproject.toml` includes all dependencies

**GHCR push permission denied:**
- Verify `packages: write` permission in workflow
- Check repository has GitHub Packages enabled in Settings

## Related Documentation

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [GitHub Container Registry](https://docs.github.com/en/packages/working-with-a-github-packages-registry/working-with-the-container-registry)
- [Docker Build Push Action](https://github.com/docker/build-push-action)
