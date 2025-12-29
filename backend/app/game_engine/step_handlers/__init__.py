"""
Step Handlers

Each step type has a dedicated handler that implements step-specific logic.
Handlers validate submissions and determine scoring or LEM evaluation needs.

Handler Types:
- BaseStepHandler: Interface all handlers implement
- MCQStepHandler: Multiple choice questions (SINGLE, MULTI, TRUE_FALSE)
- ChatStepHandler: Free-text with LEM evaluation
- GateStepHandler: Continue gates for narrative pacing
"""

from .base import BaseStepHandler, StepHandlerResult
from .mcq_handler import MCQStepHandler
from .chat_handler import ChatStepHandler
from .gate_handler import GateStepHandler

def get_handler_for_step_type(step_type: str) -> BaseStepHandler:
    """Factory function to get appropriate handler for step type."""
    handlers = {
        "MCQ_SINGLE": MCQStepHandler(),
        "MCQ_MULTI": MCQStepHandler(),
        "TRUE_FALSE": MCQStepHandler(),
        "CHAT": ChatStepHandler(),
        "CONTINUE_GATE": GateStepHandler(),
    }

    if step_type not in handlers:
        raise ValueError(f"Unknown step type: {step_type}")

    return handlers[step_type]

__all__ = [
    "BaseStepHandler",
    "StepHandlerResult",
    "MCQStepHandler",
    "ChatStepHandler",
    "GateStepHandler",
    "get_handler_for_step_type",
]
