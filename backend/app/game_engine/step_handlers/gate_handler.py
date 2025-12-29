"""
CONTINUE_GATE Step Handler

Handles narrative gates - pauses where user must click to continue.
Full implementation in Week 4.
"""

from typing import Any, Optional
from .base import BaseStepHandler, StepHandlerResult
from ..state import SessionState
from ...models import ChallengeStep


class GateStepHandler(BaseStepHandler):
    """
    Handler for CONTINUE_GATE-type steps.
    No scoring, just narrative pacing.
    """

    def handle_submission(
        self,
        step: ChallengeStep,
        answer: Any,
        state: SessionState
    ) -> StepHandlerResult:
        """
        Handle continue action.
        Simply advance to next step.
        """
        return StepHandlerResult(
            requires_lem=False,
            score=0,  # No points for gates
            passed=True,  # Always pass
            feedback=None,
            advance_step=True
        )

    def handle_entry(
        self,
        step: ChallengeStep,
        state: SessionState
    ) -> StepHandlerResult:
        """
        Handle entering a gate step.
        Always request GM narration for gates.
        """
        llm_tasks = []

        # Gates always narrate (provide context/summary)
        if step.gm_context:
            llm_tasks.append({
                "task_type": "GM_NARRATE",
                "step_index": state.current_step_index,
                "context": step.gm_context,
                "step_title": step.title,
                "step_instruction": step.instruction
            })

        return StepHandlerResult(
            requires_lem=False,
            llm_tasks=llm_tasks
        )

    def validate_answer(
        self,
        step: ChallengeStep,
        answer: Any
    ) -> tuple[bool, Optional[str]]:
        """
        Validate continue action.
        Answer should be "continue" or True.
        """
        if isinstance(answer, bool) and answer is True:
            return True, None

        if isinstance(answer, str) and answer.lower() == "continue":
            return True, None

        return False, "Invalid continue action"
