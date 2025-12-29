"""
MCQ Step Handler

Handles multiple choice question steps:
- MCQ_SINGLE: Select one option
- MCQ_MULTI: Select multiple options
- TRUE_FALSE: Boolean choice (special case of MCQ_SINGLE)

These are deterministic - no LEM needed.
"""

from typing import Any, Optional
from .base import BaseStepHandler, StepHandlerResult
from ..state import SessionState
from ...models import ChallengeStep


class MCQStepHandler(BaseStepHandler):
    """
    Handler for MCQ-type steps.
    Provides immediate, deterministic scoring.
    """

    def handle_submission(
        self,
        step: ChallengeStep,
        answer: Any,
        state: SessionState
    ) -> StepHandlerResult:
        """
        Handle MCQ answer submission.
        Scores immediately without LLM.
        """
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

        # Check correctness
        is_correct = self._check_answer(step, answer)

        # Award points
        score = step.points_possible if is_correct else 0
        passed = (score / step.points_possible) >= (step.passing_threshold / 100)

        # Build feedback
        if is_correct:
            feedback = f"Correct! You earned {score}/{step.points_possible} points."
        else:
            feedback = f"Incorrect. You earned {score}/{step.points_possible} points."

        return StepHandlerResult(
            requires_lem=False,
            score=score,
            passed=passed,
            feedback=feedback,
            advance_step=passed,  # Move to next step if passed
            complete_session=False  # Engine determines if last step
        )

    def handle_entry(
        self,
        step: ChallengeStep,
        state: SessionState
    ) -> StepHandlerResult:
        """
        Handle entering an MCQ step.
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
        Validate MCQ answer format.
        """
        if step.step_type == "MCQ_SINGLE" or step.step_type == "TRUE_FALSE":
            # Answer should be an integer (option index)
            if not isinstance(answer, int):
                return False, "Answer must be an integer (option index)"

            # Check bounds
            if step.options and (answer < 0 or answer >= len(step.options)):
                return False, f"Answer index out of range (0-{len(step.options) - 1})"

            return True, None

        elif step.step_type == "MCQ_MULTI":
            # Answer should be a list of integers
            if not isinstance(answer, list):
                return False, "Answer must be a list of integers (option indices)"

            if len(answer) == 0:
                return False, "Must select at least one option"

            # Check all are integers and within bounds
            for idx in answer:
                if not isinstance(idx, int):
                    return False, "All answer indices must be integers"

                if step.options and (idx < 0 or idx >= len(step.options)):
                    return False, f"Answer index {idx} out of range (0-{len(step.options) - 1})"

            return True, None

        return False, f"Unknown step type: {step.step_type}"

    def _check_answer(self, step: ChallengeStep, answer: Any) -> bool:
        """
        Check if answer is correct.
        """
        if step.step_type == "MCQ_SINGLE" or step.step_type == "TRUE_FALSE":
            return answer == step.correct_answer

        elif step.step_type == "MCQ_MULTI":
            # Sort both lists to compare
            correct = sorted(step.correct_answers or [])
            submitted = sorted(answer)
            return correct == submitted

        return False
