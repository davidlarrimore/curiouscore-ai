"""
Progress Tracking System for Simple Challenges

Defines four progress tracking modes with clear criteria and validation rules.
Each mode provides different ways to measure learner progression through a challenge.
"""

from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field, field_validator


class ProgressMode(str):
    """Progress tracking mode identifiers"""
    QUESTIONS = "questions"
    PHASES = "phases"
    MILESTONES = "milestones"
    TRIGGERS = "triggers"


class ProgressConfig(BaseModel):
    """
    Configuration for progress tracking in a Simple challenge.
    Stored in Challenge.custom_variables["progress_tracking"]
    """
    mode: str = Field(..., description="Progress tracking mode: questions, phases, milestones, or triggers")

    # Questions mode
    total_questions: Optional[int] = Field(None, description="Total questions for 'questions' mode (e.g., 5)")

    # Phases mode
    phases: Optional[List[Dict[str, Any]]] = Field(None, description="Phase definitions for 'phases' mode")

    # Milestones mode
    milestones: Optional[List[Dict[str, Any]]] = Field(None, description="Milestone definitions for 'milestones' mode")

    # Triggers mode
    triggers: Optional[List[str]] = Field(None, description="Trigger keywords for 'triggers' mode")

    @field_validator('mode')
    @classmethod
    def validate_mode(cls, v):
        valid_modes = [ProgressMode.QUESTIONS, ProgressMode.PHASES, ProgressMode.MILESTONES, ProgressMode.TRIGGERS]
        if v not in valid_modes:
            raise ValueError(f"mode must be one of {valid_modes}")
        return v


"""
======================================================================================
PROGRESS TRACKING MODE DEFINITIONS
======================================================================================

Mode 1: QUESTIONS
-----------------
**Best for**: Step-by-step learning with discrete Q&A interactions
**Criteria**:
  - Challenge author defines total_questions (e.g., 5)
  - LLM asks questions sequentially
  - Progress = questions_answered / total_questions * 100
  - Challenge completes when all questions answered correctly

**Example Config**:
{
  "progress_tracking": {
    "mode": "questions",
    "total_questions": 5
  }
}

**LLM Metadata Format**:
{
  "questionType": "mcq",
  "options": [...],
  "correctAnswer": 0,
  "questionNumber": 1,           # Current question number (1-indexed)
  "totalQuestions": 5,            # Total questions in challenge
  "isQuestionComplete": true,     # Did learner answer this question correctly?
  "progressPercent": 20,          # Auto-calculated: (1/5) * 100
  "scoreChange": 20,              # XP awarded for this question
  "isComplete": false             # Challenge complete when all questions done
}

**Validation Rules**:
  - questionNumber must be between 1 and total_questions
  - isQuestionComplete=true should award scoreChange > 0
  - progressPercent should equal (questionNumber / totalQuestions) * 100
  - isComplete=true only when questionNumber == totalQuestions and isQuestionComplete=true

**Testing Strategy**:
  - Create challenge with total_questions=3
  - Verify progress increments: 0% → 33% → 66% → 100%
  - Verify completion only after question 3 answered correctly
  - Verify incorrect answers don't advance questionNumber


Mode 2: PHASES
--------------
**Best for**: Multi-stage learning journeys with distinct conceptual sections
**Criteria**:
  - Challenge author defines phases with names and descriptions
  - LLM manages progression through phases
  - Progress = current_phase / total_phases * 100
  - Each phase can have multiple interactions before advancing

**Example Config**:
{
  "progress_tracking": {
    "mode": "phases",
    "phases": [
      {"number": 1, "name": "Introduction", "description": "Learn basic concepts"},
      {"number": 2, "name": "Practice", "description": "Apply concepts with examples"},
      {"number": 3, "name": "Assessment", "description": "Demonstrate mastery"}
    ]
  }
}

**LLM Metadata Format**:
{
  "questionType": "text",
  "phase": 1,                     # Current phase number (1-indexed)
  "totalPhases": 3,               # Total phases in challenge
  "phaseName": "Introduction",    # Name of current phase
  "isPhaseComplete": false,       # Is this phase finished?
  "progressPercent": 33,          # Auto-calculated: (phase / totalPhases) * 100
  "scoreChange": 10,              # XP awarded for this interaction
  "isComplete": false             # Challenge complete when final phase done
}

**Validation Rules**:
  - phase must be between 1 and totalPhases
  - isPhaseComplete=true should trigger phase increment in next message
  - progressPercent should equal (phase / totalPhases) * 100
  - isComplete=true only when phase == totalPhases and isPhaseComplete=true
  - LLM can have multiple Q&A exchanges within a single phase

**Testing Strategy**:
  - Create challenge with 3 phases
  - Verify progress increments: 0% → 33% → 66% → 100%
  - Verify multiple interactions can occur within a phase
  - Verify phase only advances when isPhaseComplete=true


Mode 3: MILESTONES
------------------
**Best for**: Achievement-based learning with specific accomplishments
**Criteria**:
  - Challenge author defines milestones with names and criteria
  - LLM tracks which milestones learner has achieved
  - Progress = milestones_achieved / total_milestones * 100
  - Milestones can be achieved in any order (non-linear)

**Example Config**:
{
  "progress_tracking": {
    "mode": "milestones",
    "milestones": [
      {"id": "understand_variables", "name": "Understand Variables", "points": 25},
      {"id": "write_function", "name": "Write a Function", "points": 25},
      {"id": "use_loops", "name": "Use Loops", "points": 25},
      {"id": "debug_code", "name": "Debug Code", "points": 25}
    ]
  }
}

**LLM Metadata Format**:
{
  "questionType": "text",
  "milestoneId": "understand_variables",  # ID of milestone being worked on
  "milestoneName": "Understand Variables", # Human-readable name
  "isMilestoneAchieved": true,             # Did learner achieve this milestone?
  "achievedMilestones": ["understand_variables"], # All milestones achieved so far
  "totalMilestones": 4,                     # Total milestones in challenge
  "progressPercent": 25,                    # (1/4) * 100
  "scoreChange": 25,                        # XP for this milestone
  "isComplete": false                       # All milestones achieved?
}

**Validation Rules**:
  - milestoneId must match one of the configured milestone IDs
  - achievedMilestones list must not contain duplicates
  - isMilestoneAchieved=true should add milestone to achievedMilestones
  - progressPercent = (achievedMilestones.length / totalMilestones) * 100
  - scoreChange should match configured milestone points
  - isComplete=true only when all milestones achieved

**Testing Strategy**:
  - Create challenge with 4 milestones
  - Verify milestones can be achieved in different orders
  - Verify progress increments correctly: 0% → 25% → 50% → 75% → 100%
  - Verify duplicate milestone achievements are prevented
  - Verify completion only when all 4 milestones achieved


Mode 4: TRIGGERS
----------------
**Best for**: Conversation-driven learning with keyword-based progression
**Criteria**:
  - Challenge author defines trigger keywords/phrases
  - LLM engages in natural conversation
  - Progress = triggers_activated / total_triggers * 100
  - Triggers activate when learner demonstrates understanding of concepts

**Example Config**:
{
  "progress_tracking": {
    "mode": "triggers",
    "triggers": [
      "explain_transformers",
      "identify_use_case",
      "discuss_limitations",
      "propose_application"
    ]
  }
}

**LLM Metadata Format**:
{
  "questionType": "text",
  "triggerId": "explain_transformers",     # ID of trigger being activated
  "isTriggerActivated": true,              # Did learner activate this trigger?
  "activatedTriggers": ["explain_transformers"], # All triggers activated so far
  "totalTriggers": 4,                       # Total triggers in challenge
  "progressPercent": 25,                    # (1/4) * 100
  "scoreChange": 25,                        # XP for activating trigger
  "isComplete": false                       # All triggers activated?
}

**Validation Rules**:
  - triggerId must match one of the configured trigger IDs
  - activatedTriggers list must not contain duplicates
  - isTriggerActivated=true should add trigger to activatedTriggers
  - progressPercent = (activatedTriggers.length / totalTriggers) * 100
  - Triggers should activate based on learner's demonstrated understanding
  - isComplete=true only when all triggers activated

**Testing Strategy**:
  - Create challenge with 4 triggers
  - Verify triggers activate based on conversation content
  - Verify progress increments: 0% → 25% → 50% → 75% → 100%
  - Verify triggers can activate in any order
  - Verify duplicate trigger activations are prevented

======================================================================================
COMMON FIELDS ACROSS ALL MODES
======================================================================================

All metadata responses must include:
- "questionType": Type of interaction (text, mcq, upload)
- "progressPercent": Current overall progress (0-100)
- "scoreChange": XP points awarded for this interaction (can be 0)
- "isComplete": Boolean indicating if entire challenge is complete
- "hint": Optional hint text if learner is stuck

Mode-specific progress fields are added based on the configured mode.
"""


def validate_progress_metadata(
    config: ProgressConfig,
    metadata: Dict[str, Any],
    current_progress_state: Dict[str, Any]
) -> tuple[bool, Optional[str], Dict[str, Any]]:
    """
    Validate progress metadata from LLM against configured mode.

    Args:
        config: Progress configuration from challenge
        metadata: Metadata from LLM response
        current_progress_state: Current progress tracking state

    Returns:
        (is_valid, error_message, updated_progress_state)
    """
    mode = config.mode

    if mode == ProgressMode.QUESTIONS:
        return _validate_questions_mode(config, metadata, current_progress_state)
    elif mode == ProgressMode.PHASES:
        return _validate_phases_mode(config, metadata, current_progress_state)
    elif mode == ProgressMode.MILESTONES:
        return _validate_milestones_mode(config, metadata, current_progress_state)
    elif mode == ProgressMode.TRIGGERS:
        return _validate_triggers_mode(config, metadata, current_progress_state)
    else:
        return False, f"Unknown progress mode: {mode}", current_progress_state


def _validate_questions_mode(
    config: ProgressConfig,
    metadata: Dict[str, Any],
    state: Dict[str, Any]
) -> tuple[bool, Optional[str], Dict[str, Any]]:
    """Validate questions mode metadata"""
    total_questions = config.total_questions
    question_number = metadata.get("questionNumber", 0)
    is_complete = metadata.get("isQuestionComplete", False)

    if question_number < 1 or question_number > total_questions:
        return False, f"questionNumber must be between 1 and {total_questions}", state

    # Track questions answered
    questions_answered = state.get("questions_answered", 0)
    if is_complete and question_number > questions_answered:
        questions_answered = question_number

    # Calculate expected progress
    expected_progress = (questions_answered / total_questions) * 100
    actual_progress = metadata.get("progressPercent", 0)

    # Allow small rounding differences
    if abs(expected_progress - actual_progress) > 1:
        return False, f"progressPercent should be {expected_progress:.0f}%, got {actual_progress}%", state

    new_state = {
        "questions_answered": questions_answered,
        "total_questions": total_questions
    }

    return True, None, new_state


def _validate_phases_mode(
    config: ProgressConfig,
    metadata: Dict[str, Any],
    state: Dict[str, Any]
) -> tuple[bool, Optional[str], Dict[str, Any]]:
    """Validate phases mode metadata"""
    total_phases = len(config.phases) if config.phases else 0
    phase = metadata.get("phase", 0)
    is_phase_complete = metadata.get("isPhaseComplete", False)

    if phase < 1 or phase > total_phases:
        return False, f"phase must be between 1 and {total_phases}", state

    # Track current phase
    current_phase = state.get("current_phase", 1)
    if is_phase_complete and phase == current_phase:
        current_phase = min(phase + 1, total_phases)

    # Calculate expected progress
    expected_progress = (current_phase / total_phases) * 100
    actual_progress = metadata.get("progressPercent", 0)

    if abs(expected_progress - actual_progress) > 1:
        return False, f"progressPercent should be {expected_progress:.0f}%, got {actual_progress}%", state

    new_state = {
        "current_phase": current_phase,
        "total_phases": total_phases
    }

    return True, None, new_state


def _validate_milestones_mode(
    config: ProgressConfig,
    metadata: Dict[str, Any],
    state: Dict[str, Any]
) -> tuple[bool, Optional[str], Dict[str, Any]]:
    """Validate milestones mode metadata"""
    milestone_ids = [m["id"] for m in config.milestones] if config.milestones else []
    total_milestones = len(milestone_ids)

    milestone_id = metadata.get("milestoneId")
    is_achieved = metadata.get("isMilestoneAchieved", False)
    achieved_milestones = metadata.get("achievedMilestones", [])

    if milestone_id and milestone_id not in milestone_ids:
        return False, f"milestoneId '{milestone_id}' not in configured milestones", state

    # Track achieved milestones
    current_achieved = set(state.get("achieved_milestones", []))
    if is_achieved and milestone_id:
        current_achieved.add(milestone_id)

    # Check for duplicates
    if len(achieved_milestones) != len(set(achieved_milestones)):
        return False, "achievedMilestones contains duplicates", state

    # Calculate expected progress
    expected_progress = (len(current_achieved) / total_milestones) * 100
    actual_progress = metadata.get("progressPercent", 0)

    if abs(expected_progress - actual_progress) > 1:
        return False, f"progressPercent should be {expected_progress:.0f}%, got {actual_progress}%", state

    new_state = {
        "achieved_milestones": list(current_achieved),
        "total_milestones": total_milestones
    }

    return True, None, new_state


def _validate_triggers_mode(
    config: ProgressConfig,
    metadata: Dict[str, Any],
    state: Dict[str, Any]
) -> tuple[bool, Optional[str], Dict[str, Any]]:
    """Validate triggers mode metadata"""
    trigger_ids = config.triggers or []
    total_triggers = len(trigger_ids)

    trigger_id = metadata.get("triggerId")
    is_activated = metadata.get("isTriggerActivated", False)
    activated_triggers = metadata.get("activatedTriggers", [])

    if trigger_id and trigger_id not in trigger_ids:
        return False, f"triggerId '{trigger_id}' not in configured triggers", state

    # Track activated triggers
    current_activated = set(state.get("activated_triggers", []))
    if is_activated and trigger_id:
        current_activated.add(trigger_id)

    # Check for duplicates
    if len(activated_triggers) != len(set(activated_triggers)):
        return False, "activatedTriggers contains duplicates", state

    # Calculate expected progress
    expected_progress = (len(current_activated) / total_triggers) * 100
    actual_progress = metadata.get("progressPercent", 0)

    if abs(expected_progress - actual_progress) > 1:
        return False, f"progressPercent should be {expected_progress:.0f}%, got {actual_progress}%", state

    new_state = {
        "activated_triggers": list(current_activated),
        "total_triggers": total_triggers
    }

    return True, None, new_state
