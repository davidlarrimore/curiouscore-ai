# CuriousCore AI - Game Master Edition

An interactive learning platform powered by the **Game Master architecture** - an event-driven, authoritative game engine that orchestrates educational challenges with LLM-powered narration and evaluation.

**Status**: ✅ **Production Ready MVP**

---

## Overview

CuriousCore AI transforms traditional learning platforms into engaging, narrative-driven educational experiences. The Game Master architecture ensures:

- **Authoritative Game Engine** - LLMs provide guidance and evaluation; the engine makes all decisions
- **Event Sourcing** - Complete audit trail with deterministic state replay
- **Mixed Question Types** - MCQ, free-text (CHAT), and narrative gates for comprehensive learning
- **Rubric-Based Evaluation** - Fair, objective assessment of free-text answers
- **Narrative Pacing** - GM narration creates engaging, story-driven challenges

### Key Features

🎮 **5 Step Types**:
- **MCQ_SINGLE** - Multiple choice (single answer)
- **MCQ_MULTI** - Multiple choice (select all that apply)
- **TRUE_FALSE** - Boolean questions
- **CHAT** - Free-text answers with LLM evaluation
- **CONTINUE_GATE** - Narrative pacing and transitions

🤖 **LLM Integration**:
- **GM (Game Master)** - Creative narration and encouragement
- **LEM (Learning Evaluation Module)** - Rubric-based assessment
- **TEACH_HINTS** - On-demand instructional guidance

📊 **Comprehensive Tracking**:
- Event-sourced state with snapshots
- Score tracking and progress visualization
- XP rewards and challenge completion

🎯 **Production Ready**:
- 3 complete challenges (Beginner → Advanced)
- Comprehensive testing (20 tests)
- Full documentation and deployment guides

---

## Quick Start

### Prerequisites

- **Node.js** 18+
- **Python** 3.10+
- **LLM API Key** (Anthropic Claude, OpenAI GPT, or Google Gemini)

### Installation

**1. Clone and install dependencies**:
```bash
# Frontend
cd frontend
npm install

# Backend
cd ../backend
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

**2. Configure environment variables**:

Create `backend/.env`:
```bash
# Database
DATABASE_URL=sqlite+aiosqlite:///./app.db

# Authentication
SECRET_KEY=your-secret-key-here  # Generate: openssl rand -hex 32
ALGORITHM=HS256

# LLM Provider (choose at least one)
ANTHROPIC_API_KEY=sk-ant-...
# OPENAI_API_KEY=sk-...
# GEMINI_API_KEY=...

# CORS
CORS_ORIGINS=http://localhost:8080
```

Create `frontend/.env`:
```bash
VITE_API_BASE_URL=http://localhost:8000
```

**3. Seed production challenges**:
```bash
cd backend
source .venv/bin/activate
python seed_production_functions.py
python seed_production_git.py
python seed_production_api.py
```

**4. Start the servers**:
```bash
# Terminal 1 - Backend
cd backend
source .venv/bin/activate
uvicorn app.main:app --reload --port 8000

# Terminal 2 - Frontend
cd frontend
npm run dev
```

**5. Access the app**:
Open http://localhost:8080

---

## Architecture

### Game Master Principles

The architecture follows five core principles from the Game Master whitepaper:

**1. The Game Engine is Authoritative**
- LLMs propose; the engine decides
- No LLM has authority over scoring or progression
- Engine enforces all rules and constraints

**2. Event-Driven Execution**
- All state changes flow through immutable events
- Complete audit trail
- Deterministic replay from event log

**3. Explicit State Over Implicit Memory**
- Chat history is NOT the source of truth
- State maintained in structured SessionState
- Context summaries generated for LLMs (bounded context)

**4. Declarative UI Control**
- Backend declares which UI mode to show
- Frontend renders based on backend declaration
- No client-side inference of game logic

**5. LLMs are Tools, Not Agents**
- Each LLM call has a bounded, specific purpose
- No autonomous multi-step agents
- No LLM calls another LLM

### System Components

```
┌─────────────┐
│   Frontend  │  React SPA with session-based UI
│   (React)   │  Renders based on backend-declared mode
└──────┬──────┘
       │ HTTP (Session API)
┌──────▼──────┐
│   Backend   │  FastAPI with session endpoints
│  (FastAPI)  │  Orchestrates engine and LLM tasks
└──────┬──────┘
       │
   ┌───▼────────────┬─────────────┐
   │                │             │
┌──▼──────┐  ┌─────▼─────┐  ┌───▼────┐
│  Game   │  │    LLM    │  │ Event  │
│ Engine  │  │Orchestrator│  │ Store  │
└─────────┘  └───────────┘  └────────┘
   │              │              │
   │         ┌────▼────┐    ┌────▼────┐
   │         │ GM/LEM  │    │  Events │
   │         │Provider │    │Snapshots│
   │         └─────────┘    └─────────┘
   │
┌──▼─────────┐
│ Challenge  │
│   Steps    │
└────────────┘
```

### Event Flow

```
User Action (submit answer, continue, hint)
  ↓
Create Event (USER_SUBMITTED_ANSWER, USER_CONTINUED, etc.)
  ↓
Append Event to Database
  ↓
Hydrate State (from snapshot + events)
  ↓
Engine.apply_event(state, event) → EngineResult
  ↓
Save Derived Events (STEP_ENTERED, SCORE_AWARDED, etc.)
  ↓
Execute LLM Tasks (if any: GM_NARRATE, LEM_EVALUATE, TEACH_HINTS)
  ↓
Apply LLM Results Back Through Engine
  ↓
Save Snapshot (every 5 events)
  ↓
Return UI Response to Frontend
```

---

## Project Structure

```
curiouscore-ai/
├── frontend/                    # React SPA
│   ├── src/
│   │   ├── pages/
│   │   │   └── ChallengeNew.tsx # Session-based challenge UI
│   │   ├── hooks/
│   │   │   └── useGameSession.ts # Session lifecycle management
│   │   ├── components/
│   │   │   ├── ChatMessage.tsx   # Markdown + Mermaid rendering
│   │   │   ├── MCQ*.tsx          # Question type components
│   │   │   └── ui/               # shadcn/ui components
│   │   └── lib/
│   │       └── api.ts            # API client
│   └── package.json
│
├── backend/                     # FastAPI backend
│   ├── app/
│   │   ├── main.py             # FastAPI app with endpoints
│   │   ├── models.py           # SQLAlchemy models
│   │   ├── session_endpoints.py # Session API
│   │   ├── game_engine/        # Core game engine
│   │   │   ├── engine.py       # Authoritative GameEngine
│   │   │   ├── events.py       # Event types
│   │   │   ├── state.py        # SessionState model
│   │   │   └── llm_orchestrator.py # LLM task routing
│   │   └── database.py         # Database setup
│   ├── tests/
│   │   ├── test_week6_integration.py # Integration tests
│   │   └── test_game_engine.py       # Unit tests
│   ├── seed_production_*.py    # Production challenge seeds
│   └── requirements.txt
│
├── docs/                        # Documentation
│   ├── CHALLENGE_AUTHORING_GUIDE.md # How to create challenges
│   ├── DEPLOYMENT_GUIDE.md          # Production deployment
│   ├── WEEK1_SUMMARY.md - WEEK6_SUMMARY.md # Implementation history
│   └── game-master-whitepaper.md    # Architecture principles
│
└── README.md                    # This file
```

---

## Documentation

### For Challenge Authors
📘 **[Challenge Authoring Guide](CHALLENGE_AUTHORING_GUIDE.md)**
- How to create challenges
- Step type documentation
- Rubric creation guidelines
- Best practices and examples

### For Deployment
🚀 **[Deployment Guide](DEPLOYMENT_GUIDE.md)**
- Environment configuration
- Database setup
- Backend/Frontend deployment options
- LLM configuration
- Performance optimization
- Monitoring and security

### Implementation History
📝 **Weekly Summaries**:
- [Week 1: Event Sourcing Foundation](WEEK1_SUMMARY.md)
- [Week 2: MCQ Flow with Session API](WEEK2_SUMMARY.md)
- [Week 3: LLM Integration (GM & LEM)](WEEK3_SUMMARY.md)
- [Week 4: Continue Gates & Hints](WEEK4_SUMMARY.md)
- [Week 5: Production Challenges](WEEK5_SUMMARY.md)
- [Week 6: Testing & Production Readiness](WEEK6_SUMMARY.md)

### Architecture
🏗️ **[Game Master Whitepaper](game-master-whitepaper.md)**
- Core architectural principles
- Design philosophy
- Implementation patterns

---

## Testing

### Run Tests

**Integration Tests** (8 tests - full session lifecycle):
```bash
cd backend
source .venv/bin/activate
pytest tests/test_week6_integration.py -v
```

**Unit Tests** (12 tests - engine logic):
```bash
pytest tests/test_game_engine.py -v
```

**All Tests**:
```bash
pytest tests/ -v
```

### Test Coverage

- ✅ Complete session lifecycle
- ✅ All step types (MCQ_SINGLE, MCQ_MULTI, TRUE_FALSE, CONTINUE_GATE, CHAT)
- ✅ Event sourcing and replay
- ✅ Scoring calculations
- ✅ Error handling
- ✅ State management

---

## Development

### Available Commands

**Frontend** (from `frontend/`):
```bash
npm run dev       # Start dev server (port 8080)
npm run build     # Production build
npm run preview   # Preview production build
npm run lint      # ESLint
```

**Backend** (from `backend/`):
```bash
# Start server
uvicorn app.main:app --reload --port 8000

# Run tests
pytest tests/ -v

# Seed challenges
python seed_production_functions.py
python seed_production_git.py
python seed_production_api.py
```

### Creating a New Challenge

1. **Create a seed script** (see `backend/seed_production_*.py` as examples)
2. **Define challenge metadata** (title, description, difficulty, points)
3. **Create steps** using the 5 step types
4. **Write rubrics** for CHAT steps (see [Challenge Authoring Guide](CHALLENGE_AUTHORING_GUIDE.md))
5. **Run the seed script** to add to database
6. **Test the challenge** end-to-end

**Example**:
```python
# Step 0: Welcome gate
ChallengeStep(
    step_type="CONTINUE_GATE",
    title="Welcome",
    instruction="Welcome to this challenge!",
    points_possible=0,
    auto_narrate=True
)

# Step 1: MCQ validation
ChallengeStep(
    step_type="MCQ_SINGLE",
    title="Check Understanding",
    instruction="Which answer is correct?",
    options=["Correct", "Wrong 1", "Wrong 2"],
    correct_answer=0,
    points_possible=30
)

# Step 2: Deep understanding
ChallengeStep(
    step_type="CHAT",
    title="Explain the Concept",
    instruction="In your own words, explain...",
    rubric={
        "total_points": 50,
        "criteria": {
            "understanding": {
                "description": "Demonstrates understanding",
                "points": 25
            },
            "clarity": {
                "description": "Explains clearly",
                "points": 25
            }
        },
        "passing_threshold": 60
    },
    points_possible=50
)
```

---

## Production Challenges

### Available Challenges

**1. Introduction to Functions** (Beginner)
- 6 steps, 100 points, 70% passing
- Topics: function definition, benefits, components
- Estimated time: 20 minutes
- Challenge ID: `45abf20e-a5dd-427a-bf59-18d22e77c2fb`

**2. Git Basics: Commits & Branches** (Intermediate)
- 7 steps, 150 points, 70% passing
- Topics: commits, messages, branches, workflows
- Estimated time: 25 minutes
- Challenge ID: `2084ff7f-6b98-4bfd-ba2f-49c4647962f2`

**3. API Design Principles** (Advanced)
- 7 steps, 200 points, 75% passing
- Topics: REST, HTTP methods, URLs, status codes
- Estimated time: 30 minutes
- Challenge ID: `efcbf33c-4f80-4af4-aa2f-251f467fd5a6`

**Total Content**: 18 steps, 450 points, ~75 minutes

---

## Performance

### Response Times (Targets)

| Operation | Target | Status |
|-----------|--------|--------|
| Session creation | < 100ms | ✅ |
| Session start | < 500ms | ✅ |
| MCQ submission | < 200ms | ✅ |
| CHAT with LEM | < 3s | ✅ |
| State retrieval | < 200ms | ✅ |

### Cost Estimate

**LLM API Costs**:
- ~$0.05-$0.10 per challenge completion
- ~$100/month for 1,000 completions

**Optimization**:
- Efficient token usage (bounded context)
- Timeout handling (30s max)
- Graceful fallbacks on errors

---

## Tech Stack

### Frontend
- **React 18** + **TypeScript** + **Vite**
- **Tailwind CSS** + **shadcn/ui** components
- **React Router** v6 for routing
- **TanStack Query** for state management
- **React Markdown** + **Mermaid** for rich content

### Backend
- **FastAPI** (Python 3.10+)
- **SQLAlchemy** 2.0 (async ORM)
- **PostgreSQL** (production) or **SQLite** (dev)
- **Pydantic** v2 for validation
- **LLM Integration**: Anthropic Claude, OpenAI GPT, Google Gemini

### Architecture
- **Event Sourcing** with immutable event log
- **State Snapshots** for performance
- **Session-Based API** (stateless backend)
- **Authoritative Game Engine**

---

## Deployment

See **[Deployment Guide](DEPLOYMENT_GUIDE.md)** for complete instructions.

### Quick Deploy

**Recommended Stack**:
- **Backend**: Railway (with PostgreSQL)
- **Frontend**: Vercel
- **Database**: Railway PostgreSQL or Supabase

**Environment Variables Required**:
- `DATABASE_URL` (PostgreSQL connection string)
- `SECRET_KEY` (JWT signing key)
- `ANTHROPIC_API_KEY` or `OPENAI_API_KEY` or `GEMINI_API_KEY`
- `CORS_ORIGINS` (frontend URL)

---

## Contributing

### Development Workflow

1. **Create a feature branch** from `main`
2. **Make your changes** with clear commit messages
3. **Run tests** to ensure nothing breaks
4. **Update documentation** if needed
5. **Submit a pull request**

### Code Style

- **Frontend**: ESLint + TypeScript strict mode
- **Backend**: Type hints everywhere, docstrings for public APIs
- **Testing**: Write tests for new features
- **Documentation**: Update guides for significant changes

---

## License

[Your License Here]

---

## Acknowledgments

Built with the **Game Master architecture** - an event-driven approach to educational content that ensures fairness, transparency, and engaging learning experiences.

**Key Technologies**:
- FastAPI by Sebastián Ramírez
- React by Meta
- shadcn/ui by shadcn
- Anthropic Claude, OpenAI GPT, Google Gemini

---

## Support

For questions, issues, or feature requests:
- Review the [Challenge Authoring Guide](CHALLENGE_AUTHORING_GUIDE.md)
- Check the [Deployment Guide](DEPLOYMENT_GUIDE.md)
- See the weekly summaries for implementation details
- Open an issue on GitHub

---

**Status**: Production Ready MVP ✅

The Game Master architecture is fully implemented with comprehensive testing, documentation, and production deployment support.
