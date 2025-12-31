# Docker Development Guide

This guide covers running CuriousCore locally with Docker for easier development and better log visibility.

## Quick Start

```bash
# Start all services (backend + frontend)
./scripts/docker-dev.sh

# View logs in real-time
./scripts/docker-logs.sh

# Check status
./scripts/docker-status.sh

# Stop all services
./scripts/docker-stop.sh
# or press Ctrl+C if running in foreground
```

## Prerequisites

- Docker Desktop installed and running
- `.env` file in the project root (optional, will use defaults if missing)

## Container Architecture

The setup includes three services:

### PostgreSQL Database
- **Port**: 5432
- **Container**: `curiouscore-postgres`
- **Image**: postgres:16-alpine
- **Storage**: Persistent volume (`postgres-data`)
- **Credentials**: Set via `.env` file (defaults: curiouscore/curiouscore_dev_password)
- **Health Check**: Automated pg_isready checks

### Backend (FastAPI)
- **Port**: 8000
- **Container**: `curiouscore-backend`
- **Hot Reload**: ✅ Enabled via volume mount
- **Database**: PostgreSQL (via asyncpg driver)
- **Logging**: Debug level with SQL queries, HTTP access logs
- **Wait Strategy**: Waits for PostgreSQL to be healthy before starting

### Frontend (Vite)
- **Port**: 8080
- **Container**: `curiouscore-frontend`
- **Hot Reload**: ✅ Enabled via volume mount
- **API URL**: http://localhost:8000
- **Logging**: Debug mode with verbose output

## Commands

### Starting Services

```bash
# Start in foreground (see logs immediately)
./scripts/docker-dev.sh

# Start in background (detached mode)
docker compose up -d

# Rebuild and start (after Dockerfile changes)
docker compose up --build
```

### Viewing Logs

```bash
# All services (color-coded, timestamped)
./scripts/docker-logs.sh

# Backend only
./scripts/docker-logs.sh backend

# Frontend only
./scripts/docker-logs.sh frontend

# Alternative: direct docker compose commands
docker compose logs -f                    # All logs
docker compose logs -f --tail=50 backend  # Last 50 backend logs
```

### Checking Status

```bash
# Comprehensive status with resource usage
./scripts/docker-status.sh

# Quick status
docker compose ps

# Resource monitoring
docker stats
```

### Stopping Services

```bash
# Stop all containers
./scripts/docker-stop.sh

# Or use docker compose directly
docker compose down

# Stop and remove volumes (reset database)
docker compose down -v
```

### Restarting Services

```bash
# Restart all
docker compose restart

# Restart specific service
docker compose restart backend
docker compose restart frontend

# Rebuild specific service
docker compose up --build -d backend
```

### Shell Access

```bash
# Backend (Python/bash)
docker compose exec backend bash

# Frontend (Node.js/sh)
docker compose exec frontend sh

# Run commands directly
docker compose exec backend python -m pytest tests/
docker compose exec frontend npm run lint
```

## Troubleshooting

### Logs Not Showing

If you don't see logs:
```bash
# Ensure containers are running
docker compose ps

# Check logs for errors
docker compose logs

# Restart with verbose output
docker compose up --build
```

### Port Already in Use

If ports 8000 or 8080 are occupied:
```bash
# Stop any non-Docker processes
./scripts/stop.sh

# Or change ports in docker-compose.yml
ports:
  - "8001:8000"  # Map host 8001 to container 8000
```

### Database Issues

```bash
# Reset database (WARNING: deletes all data)
./scripts/docker-db-reset.sh

# Or manually:
docker compose down -v
docker compose up

# Access PostgreSQL shell
./scripts/docker-db-shell.sh

# Or manually:
docker compose exec postgres psql -U curiouscore -d curiouscore

# View database logs
docker compose logs postgres

# Check database connection
docker compose exec backend python -c "from app.database import engine; print('Connected!')"
```

### Hot Reload Not Working

```bash
# Ensure volume mounts are correct
docker compose config

# Restart with rebuild
docker compose up --build

# On Mac/Windows: check Docker Desktop file sharing settings
```

### Container Won't Start

```bash
# Check logs for errors
docker compose logs backend
docker compose logs frontend

# Rebuild from scratch
docker compose down -v
docker compose build --no-cache
docker compose up
```

## Environment Variables

Environment variables are loaded from `.env` file in project root:

```bash
# PostgreSQL (for Docker)
POSTGRES_USER=curiouscore
POSTGRES_PASSWORD=curiouscore_dev_password
POSTGRES_DB=curiouscore
POSTGRES_PORT=5432

# Backend
SECRET_KEY=your-secret-key

# LLM Providers (at least one required)
OPENAI_API_KEY=sk-...
OPENAI_BASE_URL=https://api.openai.com/v1/
ANTHROPIC_API_KEY=sk-ant-...
ANTHROPIC_BASE_URL=https://api.anthropic.com

# Default LLM
DEFAULT_LLM_PROVIDER=openai
DEFAULT_LLM_MODEL=gpt-4o-mini

# Frontend
VITE_API_BASE_URL=http://localhost:8000
```

**Note**: When running in Docker, the backend automatically uses PostgreSQL. The `DATABASE_URL` in `.env` (SQLite) is only used when running local scripts without Docker.

Changes to `.env` require container restart:
```bash
docker compose restart
```

## Performance Tips

### Faster Builds

```bash
# Use BuildKit for faster builds
DOCKER_BUILDKIT=1 docker compose build

# Leverage layer caching - install deps before copying code
# (already configured in Dockerfiles)
```

### Disk Space

```bash
# Clean up unused images/volumes
docker system prune -a

# Remove specific volumes
docker volume ls
docker volume rm curiouscore-ai_backend-data
```

## Comparing Docker vs Local Scripts

| Feature | Docker | Local Scripts |
|---------|--------|---------------|
| **Setup** | One command | Multiple steps (venv, npm) |
| **Process Management** | Automatic | Manual/scripts |
| **Log Visibility** | Excellent (color-coded) | Good (with new logging) |
| **Hot Reload** | Good (~1-2s delay) | Excellent (instant) |
| **Isolation** | Complete | Shared system |
| **Cleanup** | Perfect (no orphans) | Manual (stop.sh) |
| **Team Onboarding** | Easy | Moderate |

**Recommendation**: Use Docker for most development. Use local scripts if you need fastest possible hot reload.

## Advanced Usage

### Running Tests in Docker

```bash
# Backend tests
docker compose exec backend python -m pytest tests/ -v

# With coverage
docker compose exec backend python -m pytest tests/ --cov=app --cov-report=html

# Frontend tests (if configured)
docker compose exec frontend npm test
```

### Database Management

```bash
# Access PostgreSQL shell
./scripts/docker-db-shell.sh

# Run SQL queries
./scripts/docker-db-shell.sh
# Then in psql:
# \dt                    -- List tables
# \d users               -- Describe users table
# SELECT * FROM users;   -- Query data

# Reset database (WARNING: deletes all data)
./scripts/docker-db-reset.sh

# Seed data
docker compose exec backend python seed_production_git.py

# Backup database
docker compose exec postgres pg_dump -U curiouscore curiouscore > backup.sql

# Restore database
docker compose exec -T postgres psql -U curiouscore curiouscore < backup.sql
```

### Production Simulation

For production-like environment:
```bash
# Create docker-compose.prod.yml with optimized settings
docker compose -f docker-compose.prod.yml up
```

## Switching Between Docker and Local

You can use both approaches:

```bash
# Use Docker
./scripts/docker-dev.sh

# Switch to local (stop Docker first)
./scripts/docker-stop.sh
./scripts/dev.sh

# Check what's running
./scripts/status.sh          # Local processes
./scripts/docker-status.sh   # Docker containers
```

## Next Steps

1. **Start services**: `./scripts/docker-dev.sh`
2. **Open browser**: http://localhost:8080
3. **View logs**: `./scripts/docker-logs.sh`
4. **Make changes**: Files auto-reload in containers
5. **Test API**: http://localhost:8000/challenges

For questions or issues, check the troubleshooting section above or the main README.md.
