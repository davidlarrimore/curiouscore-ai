# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

CuriousCore AI is an interactive learning platform built with React, TypeScript, and Supabase. The application provides AI-powered educational challenges where users progress through structured learning experiences with real-time chat interaction.

## Key Technologies

- **Frontend**: React 18 + TypeScript + Vite
- **UI Framework**: shadcn/ui (Radix UI primitives) + Tailwind CSS
- **Backend**: Supabase (PostgreSQL database + Auth + Edge Functions)
- **State Management**: TanStack Query (React Query)
- **Routing**: React Router v6

## Common Development Commands

```bash
# Install dependencies
npm i

# Start development server (runs on http://localhost:8080)
npm run dev

# Build for production
npm run build

# Build for development mode
npm run build:dev

# Lint code
npm run lint

# Preview production build
npm run preview
```

## Architecture

### Application Structure

The app uses a standard React SPA architecture with the following key directories:

- `src/pages/` - Top-level route components (Dashboard, Auth, Challenge, Profile, Admin)
- `src/components/` - Reusable UI components (primarily shadcn/ui components in `ui/` subdirectory)
- `src/hooks/` - Custom React hooks for business logic and data fetching
- `src/integrations/supabase/` - Supabase client configuration and auto-generated types
- `supabase/` - Backend configuration, migrations, and edge functions

### Authentication & Authorization

Authentication is managed through a custom `AuthProvider` context (src/hooks/useAuth.tsx) that wraps the entire application. Key features:

- Email/password authentication via Supabase Auth
- Session persistence in localStorage
- Role-based access control using `user_roles` table (separate from `profiles` for security)
- Admin role checking with `isAdmin` flag in auth context

The auth flow automatically redirects unauthenticated users to `/auth` route.

### Data Flow

1. **TanStack Query** is used for all data fetching and caching (configured in App.tsx)
2. **Custom hooks** encapsulate data operations:
   - `useChallenges()` - Fetches active challenges
   - `useUserProgress()` - Manages user progress on challenges
   - `useProfile()` - Handles user profile and XP management
3. **Supabase client** (src/integrations/supabase/client.ts) provides typed database access

### Challenge System

The core feature is an interactive challenge system:

- **Challenges** are stored in the `challenges` table with system prompts, difficulty levels, and XP rewards
- **User Progress** tracks completion status, score, messages, current phase, and mistakes
- **Chat Interface** (Challenge.tsx) streams responses from the `chat-instructor` edge function
- Messages include metadata for question types (text/MCQ), hints, and progress tracking

The chat flow:
1. User starts a challenge → creates/updates progress record
2. Messages sent to `/functions/v1/chat-instructor` edge function
3. Edge function uses OpenAI API to generate instructor responses with structured metadata
4. Frontend updates progress, score, and XP based on metadata

### Supabase Edge Functions

Edge functions are located in `supabase/functions/` and configured in `supabase/config.toml`.

**chat-instructor** (JWT verification enabled):
- Handles AI instructor chat interactions
- Validates request inputs (message count, length, phase bounds)
- Streams OpenAI responses with structured metadata for progress tracking
- Returns question types, hints, scoring information, and completion status

### Database Schema

Key tables:
- `profiles` - User data (username, avatar, XP, level)
- `user_roles` - Role assignments (admin/user) - separate for security
- `challenges` - Learning challenges with prompts and configuration
- `user_progress` - Tracks user state through challenges (messages, score, phase)
- `badges` & `user_badges` - Achievement system
- `leaderboard` - Performance tracking
- `activity_logs` - User action history

Enums:
- `app_role`: admin, user
- `badge_type`: milestone, category_mastery, streak, achievement
- `difficulty_level`: beginner, intermediate, advanced, expert

### Path Aliases

The project uses `@/` as an alias for the `src/` directory (configured in vite.config.ts and tsconfig.json).

## Environment Variables

Required environment variables (stored in `.env`):
- `VITE_SUPABASE_URL` - Supabase project URL
- `VITE_SUPABASE_PUBLISHABLE_KEY` - Supabase anon/public key

## Database Migrations

Migrations are in `supabase/migrations/`. The initial migration sets up the complete schema including RLS policies, functions, and triggers.

When working with the database:
- Use Supabase Studio for schema changes during development
- Generate migrations for version control
- RLS policies are enforced - users can only access their own data

## Styling

The project uses Tailwind CSS with a custom theme configuration (tailwind.config.ts). UI components follow the shadcn/ui design system with customizable CSS variables for theming.

Component styling pattern:
- Use Tailwind utility classes
- Leverage `class-variance-authority` for variant-based styling
- Use `cn()` utility from `lib/utils.ts` for conditional classes
