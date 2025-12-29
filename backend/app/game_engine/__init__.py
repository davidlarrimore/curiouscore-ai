"""
Game Master Architecture - Core Game Engine

This module implements the authoritative game engine for the Game Master update.
The engine orchestrates event-driven challenge progression with LLM integration.

Key Principles:
- Engine owns all scoring and progression decisions
- LLMs provide signals (LEM) or content (GM) but NEVER authority
- Deterministic replay from event log
- No LLM calls another LLM
- No UI logic inferred client-side

Components:
- engine: Core GameEngine class
- events: Event type definitions
- state: SessionState model
- step_handlers: Step-specific logic
- llm_orchestrator: LLM task routing
"""

from .engine import GameEngine
from .events import Event, EventType
from .state import SessionState

__all__ = ["GameEngine", "Event", "EventType", "SessionState"]
