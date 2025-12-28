# CuriousCore AI

React + FastAPI challenge platform with an interactive AI instructor. Users authenticate against the FastAPI API, work through challenges via a chat workflow backed by a model gateway, track progress/XP, and manage badges and challenges through the admin view. The repo is structured as a monorepo with `frontend/` and `backend/`.

## Stack
- Vite + React 18 + TypeScript
- Tailwind CSS with shadcn/ui components and lucide icons
- React Router + TanStack Query for routing and data fetching
- FastAPI backend (Python) with SQLAlchemy; SQLite in development, Postgres in production
- AI gateway integration for instructor chat (HTTP endpoint and API key driven)

## Getting Started
1) Install prerequisites: Node.js 18+, npm, and Python 3.11+.  
2) Install frontend deps (from the `frontend/` directory):
```sh
cd frontend
npm install
```
3) Install backend deps:
```sh
python -m venv .venv
source .venv/bin/activate  # or .venv\\Scripts\\activate on Windows
pip install -r backend/requirements.txt
```
4) Create a `.env` in the repo root (used by the backend), and optionally a `frontend/.env` for Vite overrides:
```sh
VITE_API_BASE_URL=http://localhost:8000
DATABASE_URL=sqlite+aiosqlite:///./backend/app.db
SECRET_KEY=change-me
AI_GATEWAY_URL=https://your-model-gateway-endpoint
AI_GATEWAY_API_KEY=your-api-key
```
5) Start the FastAPI backend:
```sh
uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000
```
6) Start the frontend (uses port 8080 per Vite config):
```sh
cd frontend
npm run dev
```
The app runs at http://localhost:8080 in development.

## Available Scripts (run from `frontend/`)
- `npm run dev` – start Vite in development mode.
- `npm run build` – create a production build.
- `npm run build:dev` – build using the development mode flags.
- `npm run preview` – serve the production build locally.
- `npm run lint` – run ESLint across the repo.

## Project Structure
- `frontend/` – React app code.  
  - `frontend/src/pages/` – route-level screens (Dashboard, Auth, Challenge, Profile, Admin).  
  - `frontend/src/components/` – shared UI with shadcn/ui primitives under `components/ui/`.  
  - `frontend/src/hooks/` – auth, profile, and challenge data hooks backed by the FastAPI backend.  
  - `frontend/public/` – static assets.
- `backend/` – FastAPI app (see `backend/app/main.py`) plus `backend/requirements.txt`.

## Environment & Services
- Backend database: set `DATABASE_URL` to `sqlite+aiosqlite:///./backend/app.db` (dev) or a Postgres URI (`postgresql+asyncpg://user:pass@host/dbname`) for production.
- API auth: `SECRET_KEY` secures JWT signing; `VITE_API_BASE_URL` points the frontend at the FastAPI server (set via `frontend/.env` or CLI).
- AI gateway: set `AI_GATEWAY_URL` and `AI_GATEWAY_API_KEY` for the instructor chat route.

## Notes
- Tailwind utilities and the `cn` helper (`frontend/src/lib/utils.ts`) handle conditional classes.
- The UI uses shadcn/ui styling defaults; follow the existing patterns when adding components.
