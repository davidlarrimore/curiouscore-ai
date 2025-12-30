"""
CHAT Step Handler

Handles free-text chat steps that require LEM evaluation.
Full implementation in Week 3.
"""

from typing import Any, Optional
from .base import BaseStepHandler, StepHandlerResult
from ..state import SessionState
from ...models import ChallengeStep


class ChatStepHandler(BaseStepHandler):
    """
    Handler for CHAT-type steps.
    Requires LEM evaluation for scoring.
    """

    def handle_submission(
        self,
        step: ChallengeStep,
        answer: Any,
        state: SessionState
    ) -> StepHandlerResult:
        """
        Handle chat answer submission.

        For Simple challenges (detected by metadata in gm_context),
        send answer back to teaching LLM for feedback.

        For Advanced challenges, use LEM evaluation.
        """
        # Convert numbers to strings (for MCQ indices)
        if isinstance(answer, (int, float)):
            answer = str(int(answer))

        # Validate answer format
        is_valid, error = self.validate_answer(step, answer)
        if not is_valid:
            return StepHandlerResult(
                requires_lem=False,
                score=0,
                passed=False,
                feedback=f"Invalid answer format: {error}",
                advance_step=False
            )

        # Detect if this is a Simple challenge
        is_simple_challenge = (
            step.gm_context and
            isinstance(step.gm_context, str) and
            "<metadata>" in step.gm_context and
            len(step.gm_context) > 1000
        )

        if is_simple_challenge:
            # For Simple challenges: send answer to teaching LLM
            llm_tasks = [{
                "task_type": "GM_NARRATE",
                "step_index": state.current_step_index,
                "context": step.gm_context,
                "step_title": step.title,
                "step_instruction": step.instruction,
                "user_answer": answer  # Include user's answer
            }]

            return StepHandlerResult(
                requires_lem=False,
                llm_tasks=llm_tasks
            )
        else:
            # For Advanced challenges: use LEM evaluation
            llm_tasks = [{
                "task_type": "LEM_EVALUATE",
                "step_index": state.current_step_index,
                "answer": answer,
                "rubric": step.rubric,
                "max_score": step.points_possible
            }]

            return StepHandlerResult(
                requires_lem=True,
                llm_tasks=llm_tasks
            )

    def handle_entry(
        self,
        step: ChallengeStep,
        state: SessionState
    ) -> StepHandlerResult:
        """
        Handle entering a CHAT step.
        Request GM narration if enabled.
        """
        llm_tasks = []

        if step.auto_narrate and step.gm_context:
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
        Validate chat answer format.
        For Simple challenges, accept numbers (MCQ indices) and convert to string.
        """
        # Convert numbers to strings (for MCQ indices in Simple challenges)
        if isinstance(answer, (int, float)):
            answer = str(answer)

        if not isinstance(answer, str):
            return False, "Answer must be a string or number"

        if len(answer.strip()) == 0:
            return False, "Answer cannot be empty"

        if len(answer) > 5000:
            return False, "Answer too long (max 5000 characters)"

        return True, None
