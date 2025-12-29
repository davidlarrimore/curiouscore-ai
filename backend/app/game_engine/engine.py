"""
Game Engine - Core Orchestrator

The GameEngine is the authoritative component that:
- Receives events and applies them to state
- Emits derived events based on state changes
- Determines scoring and progression (never delegates to LLM)
- Requests LLM tasks when needed (GM narration, LEM evaluation)
- Builds UI responses declaring what frontend should render

Key Principles:
- Engine owns all outcomes
- LLMs provide signals or content, never decisions
- Event application is deterministic
- UI behavior is explicitly declared, never inferred
"""

from typing import List, Optional, Any
from datetime import datetime
from pydantic import BaseModel

from .events import Event, EventType
from .state import SessionState, StepScore, DisplayMessage
from ..models import ChallengeStep


class EngineResult(BaseModel):
    """
    Result of applying an event to state.
    Contains new state, derived events, LLM tasks, and UI response.
    """
    new_state: SessionState
    derived_events: List[Event] = []
    llm_tasks: List[dict[str, Any]] = []
    ui_response: dict[str, Any]

    class Config:
        arbitrary_types_allowed = True


class GameEngine:
    """
    Authoritative game engine.
    Orchestrates all state transitions, scoring, and progression.
    """

    def __init__(self, challenge_steps: List[ChallengeStep]):
        """
        Initialize engine with challenge steps.

        Args:
            challenge_steps: List of steps for this challenge, sorted by step_index
        """
        self.steps = sorted(challenge_steps, key=lambda s: s.step_index)
        self.total_steps = len(self.steps)

    def apply_event(self, state: SessionState, event: Event) -> EngineResult:
        """
        Apply an event to the current state.
        This is the main entry point for all state changes.

        Args:
            state: Current session state
            event: Event to apply

        Returns:
            EngineResult with new state, derived events, LLM tasks, and UI response

        Raises:
            ValueError: If event type is unknown
        """
        # Route to appropriate handler based on event type
        if event.event_type == EventType.SESSION_STARTED:
            return self._handle_session_started(state, event)
        elif event.event_type == EventType.USER_SUBMITTED_ANSWER:
            return self._handle_user_submission(state, event)
        elif event.event_type == EventType.USER_CONTINUED:
            return self._handle_user_continued(state, event)
        elif event.event_type == EventType.USER_REQUESTED_HINT:
            return self._handle_hint_request(state, event)
        elif event.event_type == EventType.LEM_EVALUATED:
            return self._handle_lem_result(state, event)
        elif event.event_type == EventType.GM_NARRATED:
            return self._handle_gm_narration(state, event)
        else:
            raise ValueError(f"Unknown event type: {event.event_type}")

    # ========================================================================
    # Event Handlers (Week 1: Stubs, Week 2: Full Implementation)
    # ========================================================================

    def _handle_session_started(self, state: SessionState, event: Event) -> EngineResult:
        """
        Handle SESSION_STARTED event.
        Enter first step and optionally request GM narration.
        """
        first_step = self.steps[0]

        # Update state
        new_state = state.model_copy(deep=True)
        new_state.status = "active"
        new_state.current_step_index = 0
        new_state.current_ui_mode = first_step.step_type
        new_state.update_context_summary(f"Starting challenge with {self.total_steps} steps")

        # Derived event: STEP_ENTERED
        derived_events = [
            Event(
                event_type=EventType.STEP_ENTERED,
                session_id=state.session_id,
                sequence_number=event.sequence_number + 1,
                timestamp=datetime.utcnow(),
                data={
                    "step_index": 0,
                    "step_type": first_step.step_type,
                    "ui_mode": first_step.step_type
                }
            )
        ]

        # LLM tasks: GM narration if enabled
        llm_tasks = []
        if first_step.auto_narrate:
            llm_tasks.append({
                "task_type": "GM_NARRATE",
                "step_index": 0,
                "context": self._build_gm_context(new_state, first_step)
            })

        return EngineResult(
            new_state=new_state,
            derived_events=derived_events,
            llm_tasks=llm_tasks,
            ui_response=self._build_ui_response(new_state, first_step)
        )

    def _handle_user_submission(self, state: SessionState, event: Event) -> EngineResult:
        """
        Handle USER_SUBMITTED_ANSWER event.
        Route to appropriate step handler (implemented in Week 2).
        """
        # Week 1: Stub implementation
        # Week 2: Full implementation with step handlers
        step = self.steps[state.current_step_index]

        new_state = state.model_copy(deep=True)

        # Add user message to display
        new_state.add_message(
            role="user",
            content=str(event.data.get("answer", "")),
            timestamp=event.timestamp.isoformat()
        )

        return EngineResult(
            new_state=new_state,
            derived_events=[],
            llm_tasks=[],
            ui_response=self._build_ui_response(new_state, step)
        )

    def _handle_user_continued(self, state: SessionState, event: Event) -> EngineResult:
        """
        Handle USER_CONTINUED event (for CONTINUE_GATE steps).
        Advance to next step.
        """
        # Week 1: Stub
        # Week 4: Full implementation with gate handler
        new_state = state.model_copy(deep=True)

        # Advance to next step
        if state.current_step_index < self.total_steps - 1:
            new_state.current_step_index += 1
            next_step = self.steps[new_state.current_step_index]
            new_state.current_ui_mode = next_step.step_type

        return EngineResult(
            new_state=new_state,
            derived_events=[],
            llm_tasks=[],
            ui_response=self._build_ui_response(new_state, self.steps[new_state.current_step_index])
        )

    def _handle_hint_request(self, state: SessionState, event: Event) -> EngineResult:
        """
        Handle USER_REQUESTED_HINT event.
        Request hint from LLM orchestrator.
        """
        # Week 1: Stub
        # Week 4: Full implementation with TEACH_HINTS task
        new_state = state.model_copy(deep=True)
        new_state.hints_used += 1

        step = self.steps[state.current_step_index]

        llm_tasks = [{
            "task_type": "TEACH_HINTS",
            "step_index": state.current_step_index,
            "context": self._build_hint_context(new_state, step)
        }]

        return EngineResult(
            new_state=new_state,
            derived_events=[],
            llm_tasks=llm_tasks,
            ui_response=self._build_ui_response(new_state, step)
        )

    def _handle_lem_result(self, state: SessionState, event: Event) -> EngineResult:
        """
        Handle LEM_EVALUATED event.
        Engine enforces score clamping and thresholds.
        """
        # Week 1: Stub
        # Week 3: Full implementation with enforcement
        step = self.steps[state.current_step_index]
        lem_data = event.data

        # Engine enforcement: clamp score
        raw_score = lem_data.get("raw_score", 0)
        clamped_score = max(0, min(raw_score, step.points_possible))

        passed = (clamped_score / step.points_possible) >= (step.passing_threshold / 100)

        new_state = state.model_copy(deep=True)
        new_state.step_scores.append(StepScore(
            step_index=state.current_step_index,
            score=clamped_score,
            max_possible=step.points_possible,
            passed=passed,
            attempts=1
        ))
        new_state.total_score += clamped_score

        # Add feedback message
        feedback = lem_data.get("rationale", "Answer evaluated.")
        new_state.add_message(
            role="gm",
            content=feedback,
            timestamp=datetime.utcnow().isoformat(),
            metadata={"score": clamped_score, "max": step.points_possible}
        )

        # Derived events
        derived_events = []

        if passed:
            # Step complete - advance or finish
            if state.current_step_index < self.total_steps - 1:
                new_state.current_step_index += 1
                next_step = self.steps[new_state.current_step_index]
                new_state.current_ui_mode = next_step.step_type
            else:
                new_state.status = "completed"

        return EngineResult(
            new_state=new_state,
            derived_events=derived_events,
            llm_tasks=[],
            ui_response=self._build_ui_response(new_state, step)
        )

    def _handle_gm_narration(self, state: SessionState, event: Event) -> EngineResult:
        """
        Handle GM_NARRATED event.
        Add GM message to display.
        """
        new_state = state.model_copy(deep=True)
        gm_content = event.data.get("content", "")

        new_state.add_message(
            role="gm",
            content=gm_content,
            timestamp=event.timestamp.isoformat()
        )

        step = self.steps[state.current_step_index]

        return EngineResult(
            new_state=new_state,
            derived_events=[],
            llm_tasks=[],
            ui_response=self._build_ui_response(new_state, step)
        )

    # ========================================================================
    # Helper Methods
    # ========================================================================

    def _build_ui_response(self, state: SessionState, current_step: ChallengeStep) -> dict[str, Any]:
        """
        Build UI response declaring what frontend should render.
        Backend controls UI behavior explicitly.
        """
        ui_data = {
            "ui_mode": state.current_ui_mode,
            "step_index": state.current_step_index,
            "total_steps": self.total_steps,
            "step_title": current_step.title,
            "step_instruction": current_step.instruction,
            "messages": [m.model_dump() for m in state.messages],
            "score": state.total_score,
            "max_score": state.max_possible_score,
            "status": state.status,
            "progress_percentage": state.calculate_final_percentage()
        }

        # Add mode-specific data
        if state.current_ui_mode in ["MCQ_SINGLE", "MCQ_MULTI"]:
            ui_data["options"] = current_step.options
        elif state.current_ui_mode == "TRUE_FALSE":
            ui_data["options"] = ["True", "False"]

        return ui_data

    def _build_gm_context(self, state: SessionState, step: ChallengeStep) -> dict[str, Any]:
        """
        Build context for GM narration LLM call.
        Engine provides bounded context, never raw chat history.
        """
        return {
            "step_title": step.title,
            "step_instruction": step.instruction,
            "gm_context": step.gm_context or "",
            "state_summary": state.context_summary,
            "current_score": state.total_score,
            "max_score": state.max_possible_score,
            "step_index": state.current_step_index,
            "total_steps": self.total_steps
        }

    def _build_hint_context(self, state: SessionState, step: ChallengeStep) -> dict[str, Any]:
        """Build context for hint generation."""
        return {
            "step_title": step.title,
            "step_instruction": step.instruction,
            "state_summary": state.context_summary,
            "hints_used": state.hints_used,
            "step_type": step.step_type
        }
