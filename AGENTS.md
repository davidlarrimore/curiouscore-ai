# Repository Guidelines

## Project Structure & Module Organization
- `frontend/` contains the React app.
  - `frontend/src/pages/` holds route-level screens (Dashboard, Auth, Challenge, Profile, Admin).
  - `frontend/src/components/` hosts reusable UI, with shadcn/ui primitives under `frontend/src/components/ui/`.
  - `frontend/src/hooks/` contains custom React hooks for auth and data fetching.
  - `frontend/src/lib/api.ts` provides the frontend API client to the FastAPI backend.
  - `frontend/public/` stores static assets.
- `backend/` hosts the FastAPI app, models, and configuration.

## Build, Test, and Development Commands
- Frontend: from `frontend/` run `npm i`, `npm run dev`, `npm run build`, `npm run build:dev`, `npm run preview`, `npm run lint`.
- Backend: create a virtualenv and install `pip install -r backend/requirements.txt`; run with `uvicorn backend.app.main:app --reload --port 8000`.

## Coding Style & Naming Conventions
- TypeScript + React with 2-space indentation, double quotes, and semicolons (match existing files).
- Prefer functional components and hooks; keep UI in `frontend/src/components/` and pages in `frontend/src/pages/`.
- Use the `@/` alias for imports from `frontend/src/` (configured in Vite/TS).
- Tailwind CSS is the primary styling method; use `cn()` from `frontend/src/lib/utils.ts` for conditional classes.

## Testing Guidelines
- There are no automated test scripts in `package.json` today.
- If you add tests, document how to run them and keep naming consistent (e.g., `*.test.tsx`).

## Commit & Pull Request Guidelines
- Commit history uses short, imperative summaries (e.g., "Fix challenge auth tokens"). No strict convention enforced.
- PRs should include: a clear description, the motivation or linked issue, and screenshots for UI changes.
- Note any backend API or schema changes in the PR description.

## Configuration & Environment
- Required env vars: `VITE_API_BASE_URL`, `DATABASE_URL`, `SECRET_KEY`, `AI_GATEWAY_URL`, `AI_GATEWAY_API_KEY` (create a local `.env`; add a `frontend/.env` for Vite overrides if needed).
- FastAPI listens on port 8000 by default; frontend dev server on 8080.
