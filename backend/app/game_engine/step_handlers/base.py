"""
Base Step Handler Interface

Step handlers implement step-specific logic for different UI modes.
Each step type (MCQ, CHAT, CONTINUE_GATE) has its own handler.

Key Principles:
- Handlers determine if LEM evaluation is needed
- Handlers provide scoring logic (for deterministic types like MCQ)
- Handlers never mutate state directly (return results)
- Engine orchestrates all state changes
"""

from abc import ABC, abstractmethod
from typing import Any, Optional, List
from pydantic import BaseModel

from ..events import Event
from ..state import SessionState
from ...models import ChallengeStep


class StepHandlerResult(BaseModel):
    """
    Result from a step handler.
    Tells the engine what to do next.
    """
    # Scoring
    requires_lem: bool = False  # Does this need LEM evaluation?
    score: Optional[int] = None  # Direct score (for MCQ)
    passed: Optional[bool] = None  # Did user pass this step?

    # Feedback
    feedback: Optional[str] = None  # Message to show user

    # Next steps
    advance_step: bool = False  # Should we move to next step?
    complete_session: bool = False  # Is challenge complete?

    # LLM tasks
    llm_tasks: List[dict[str, Any]] = []

    # Derived events (besides STEP_COMPLETED)
    derived_events: List[Event] = []


class BaseStepHandler(ABC):
    """
    Base interface for step handlers.
    Each step type implements this interface.
    """

    @abstractmethod
    def handle_submission(
        self,
        step: ChallengeStep,
        answer: Any,
        state: SessionState
    ) -> StepHandlerResult:
        """
        Handle a user's answer submission for this step.

        Args:
            step: The challenge step configuration
            answer: User's answer (type varies by step)
            state: Current session state

        Returns:
            StepHandlerResult telling engine what to do
        """
        pass

    @abstractmethod
    def handle_entry(
        self,
        step: ChallengeStep,
        state: SessionState
    ) -> StepHandlerResult:
        """
        Handle entering this step.
        Used for auto-narration, initial setup, etc.

        Args:
            step: The challenge step configuration
            state: Current session state

        Returns:
            StepHandlerResult with any LLM tasks needed
        """
        pass

    @abstractmethod
    def validate_answer(
        self,
        step: ChallengeStep,
        answer: Any
    ) -> tuple[bool, Optional[str]]:
        """
        Validate that the answer format is correct.

        Args:
            step: The challenge step configuration
            answer: User's answer

        Returns:
            (is_valid, error_message)
        """
        pass
