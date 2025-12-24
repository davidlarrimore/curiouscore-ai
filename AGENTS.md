# Repository Guidelines

## Project Structure & Module Organization
- `src/` contains the React app.
- `src/pages/` holds route-level screens (Dashboard, Auth, Challenge, Profile, Admin).
- `src/components/` hosts reusable UI, with shadcn/ui primitives under `src/components/ui/`.
- `src/hooks/` contains custom React hooks for auth and data fetching.
- `src/integrations/supabase/` holds the Supabase client and generated types.
- `supabase/` includes backend config, migrations, and edge functions.
- `public/` stores static assets.

## Build, Test, and Development Commands
- `npm i` installs dependencies.
- `npm run dev` starts the Vite dev server.
- `npm run build` creates the production build.
- `npm run build:dev` builds with development mode flags.
- `npm run preview` serves the production build locally.
- `npm run lint` runs ESLint across the repo.

## Coding Style & Naming Conventions
- TypeScript + React with 2-space indentation, double quotes, and semicolons (match existing files).
- Prefer functional components and hooks; keep UI in `src/components/` and pages in `src/pages/`.
- Use the `@/` alias for imports from `src/` (configured in Vite/TS).
- Tailwind CSS is the primary styling method; use `cn()` from `src/lib/utils.ts` for conditional classes.

## Testing Guidelines
- There are no automated test scripts in `package.json` today.
- If you add tests, document how to run them and keep naming consistent (e.g., `*.test.tsx`).

## Commit & Pull Request Guidelines
- Commit history uses short, imperative summaries (e.g., "Fix challenge auth tokens"). No strict convention enforced.
- PRs should include: a clear description, the motivation or linked issue, and screenshots for UI changes.
- Note any Supabase changes (migrations, edge functions) in the PR description.

## Configuration & Environment
- Required env vars: `VITE_SUPABASE_URL`, `VITE_SUPABASE_PUBLISHABLE_KEY` (create a local `.env`).
- Supabase edge functions live under `supabase/functions/`; update `supabase/config.toml` when adding one.
