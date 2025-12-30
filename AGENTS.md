# Repository Guidelines

## Project Structure & Module Organization
- `frontend/` is the React 18 + Vite app. Key paths: `src/pages/` (Index, Dashboard, Auth, ChallengeNew session UI, Profile, Admin, NotFound), `src/components/` (MCQ/TrueFalse inputs, ChatMessage, shadcn primitives under `components/ui`), `src/hooks/` (`useGameSession`, `useAuth`, `useChallenges`, etc.), `src/lib/api.ts` (fetch client), and `public/` for static assets.
- `backend/` is the FastAPI service. Key modules: `app/main.py` (auth/profile/progress APIs and admin routes), `app/session_endpoints.py` (Game Master session lifecycle), `app/game_engine/` (engine, events, state, step handlers, LLM orchestrator), `app/event_store.py` (event sourcing + snapshots), `app/llm_router.py` (OpenAI/Anthropic/Gemini), `app/models.py`/`schemas.py`, and `backend/tests/` for pytest suites. Seed scripts live at `backend/seed_production_*.py` plus older week seeds. `scripts/verify.sh` builds frontend, compiles backend imports, and checks LLM connectivity.

## Build, Test, and Development Commands
- Frontend (from `frontend/`): `npm install`, `npm run dev` (port 8080), `npm run build`, `npm run build:dev`, `npm run preview`, `npm run lint`.
- Backend (from `backend/`): create a venv, `pip install -r requirements.txt`, run `uvicorn app.main:app --reload --port 8000`.
- Seeds: `python seed_production_functions.py`, `seed_production_git.py`, `seed_production_api.py` (optional week seeds also available).
- Repo-level check: `scripts/verify.sh` (needs Node + Python; LLM connectivity steps require provider API keys).

## Coding Style & Naming Conventions
- TypeScript + React with 2-space indentation and semicolons; follow surrounding quote style (mostly double quotes).
- Keep pages in `frontend/src/pages/`, shared UI in `frontend/src/components/`, hooks in `frontend/src/hooks/`, and use the `@/` alias for imports from `frontend/src/`.
- Tailwind CSS + shadcn/ui; use `cn()` from `frontend/src/lib/utils.ts` for conditional classes.
- Game Master flow: frontend relies on `useGameSession` and `/sessions` API responses for UI mode (MCQ_SINGLE, MCQ_MULTI, TRUE_FALSE, CHAT, CONTINUE_GATE). Keep game logic on the backend; avoid client-side inference of progression or scoring.

## Testing Guidelines
- Backend tests use pytest. From `backend/` run `pytest tests -v` (integration: `tests/test_week6_integration.py` and `test_api_regression.py`; engine unit tests under `tests/game_engine/`; connectivity tests require LLM keys).
- Frontend currently ships linting only (`npm run lint`); no Jest/RTL tests are present.
- `scripts/verify.sh` builds the frontend, compiles backend modules, and runs LLM connectivity checks plus `backend.tests.test_llm_connectivity` (requires API keys).

## Commit & Pull Request Guidelines
- Commits are short, imperative summaries (e.g., "Fix challenge auth tokens"). No strict convention enforced.
- PRs should include a clear description, motivation or linked issue, and screenshots for UI changes. Call out any backend API or schema changes.

## Configuration & Environment
- Backend `.env` (reads from `backend/.env` or repo root): `DATABASE_URL`, `SECRET_KEY`, `ALGORITHM` (HS256 default), `ACCESS_TOKEN_EXPIRES_MINUTES` (default set), optional `AI_GATEWAY_URL`/`AI_GATEWAY_API_KEY`, LLM keys (`OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `GEMINI_API_KEY`, with optional base URLs), `DEFAULT_LLM_PROVIDER`, `DEFAULT_LLM_MODEL`, `CORS_ORIGINS`. At least one LLM key is needed for GM/LEM/hints; defaults fall back to Anthropic Sonnet.
- Frontend: `VITE_API_BASE_URL` (defaults to `http://localhost:8000` if unset).
- FastAPI defaults to port 8000; Vite dev server uses 8080 (CORS allows 8080 and 5173 by default).
