# Docker Quick Start

## TL;DR

```bash
# Start everything
./scripts/docker-dev.sh

# View logs
./scripts/docker-logs.sh

# Stop everything
Ctrl+C (or ./scripts/docker-stop.sh)
```

## Essential Commands

| What | Command |
|------|---------|
| **Start services** | `./scripts/docker-dev.sh` |
| **View all logs** | `./scripts/docker-logs.sh` |
| **Backend logs only** | `./scripts/docker-logs.sh backend` |
| **Frontend logs only** | `./scripts/docker-logs.sh frontend` |
| **Check status** | `./scripts/docker-status.sh` |
| **Stop services** | `./scripts/docker-stop.sh` or `Ctrl+C` |
| **Restart** | `docker compose restart` |
| **Rebuild** | `docker compose up --build` |
| **Database shell** | `./scripts/docker-db-shell.sh` |
| **Reset database** | `./scripts/docker-db-reset.sh` |

## Troubleshooting One-Liners

```bash
# Nothing working?
docker compose down && docker compose up --build

# Database corrupted?
docker compose down -v && docker compose up

# Port already in use?
./scripts/stop.sh && docker compose up

# Need a clean slate?
docker compose down -v && docker system prune -f && docker compose up --build
```

## Shell Access

```bash
# Backend (Python)
docker compose exec backend bash

# Frontend (Node)
docker compose exec frontend sh

# PostgreSQL
./scripts/docker-db-shell.sh
# or
docker compose exec postgres psql -U curiouscore -d curiouscore

# Run tests
docker compose exec backend python -m pytest tests/ -v
```

## URLs

- Frontend: http://localhost:8080
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- PostgreSQL: localhost:5432 (user: curiouscore, db: curiouscore)

## Log Examples

What you'll see in the logs:

```
backend   | 11:23:45 - app.main - INFO - 🚀 Application startup
backend   | 11:23:45 - app.main - INFO - ➡️  POST /auth/login
frontend  | VITE v5.4.19  ready in 1234 ms
frontend  | ➜  Local:   http://localhost:8080/
```

## Database

Docker uses **PostgreSQL** (not SQLite). Data persists in a Docker volume.

```bash
# Access database
./scripts/docker-db-shell.sh

# Reset database (deletes all data)
./scripts/docker-db-reset.sh
```

## Full Documentation

- [DOCKER.md](./DOCKER.md) - Comprehensive Docker development guide
- [RAILWAY.md](./RAILWAY.md) - Railway deployment guide with PostgreSQL
