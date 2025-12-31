"""
System Prompt Injection

Augments user-provided system prompts with structured metadata requirements
to ensure LLM responses are properly formatted for Simple challenges.
"""

from typing import Optional, Dict, Any


def inject_metadata_requirements(
    user_prompt: str,
    challenge_title: str,
    xp_reward: int,
    passing_score: int,
    progress_config: Optional[Dict[str, Any]] = None
) -> str:
    """
    Append metadata structure requirements to user's system prompt.

    This ensures the LLM knows to:
    1. Include metadata in every response
    2. Use the correct XML tag format
    3. Follow the JSON schema
    4. Track progression appropriately based on progress mode

    Args:
        user_prompt: The user-provided system prompt
        challenge_title: Title of the challenge (for context)
        xp_reward: Maximum XP for the challenge
        passing_score: Percentage required to pass
        progress_config: Optional progress tracking configuration

    Returns:
        Enhanced system prompt with metadata requirements injected
    """

    # Get progress-specific instructions
    progress_instructions = _get_progress_instructions(progress_config, xp_reward) if progress_config else _get_legacy_progress_instructions(xp_reward)

    metadata_template = f"""

---

CRITICAL: Response Format Requirements for "{challenge_title}"

You MUST include metadata in EVERY response using this EXACT format:

<metadata>
{{
  "questionType": "text" | "mcq" | "continue" | "upload",
  "options": ["Option 1", "Option 2", "Option 3"],
  "correctAnswer": 0,
  {progress_instructions["example_fields"]}
  "progressPercent": 25,
  "scoreChange": 10,
  "hint": "Optional hint text",
  "isComplete": false
}}
</metadata>

Metadata Field Definitions:

- "questionType": Type of interaction
  * "text" = Free-text response
  * "mcq" = Multiple choice question
  * "continue" = Confirmation gate (shows "Continue" button, used for phase transitions)
  * "upload" = File upload request

- "options": Array of answer choices (REQUIRED for mcq, omit for text/upload)
  * Provide 3-5 clear, distinct options
  * Options should be specific, not vague
  * CRITICAL: Generate FRESH options for EACH question - never reuse options from previous questions
  * Each question must have options that are specific to that question's content

- "correctAnswer": Zero-based index of correct option (REQUIRED for mcq, omit for text/upload)
  * 0 = first option, 1 = second option, etc.

{progress_instructions["field_definitions"]}

- "progressPercent": Current overall progress (0-100)
  * {progress_instructions["progress_calculation"]}
  * This is the PRIMARY progress indicator shown to learners

- "scoreChange": XP points awarded for this interaction (0-{xp_reward})
  * Total scoreChange across all interactions should not exceed {xp_reward}
  * Award more points for harder or more important questions
  * Can be 0 for introductory messages or hints

- "hint": Optional hint text (string or null)
  * Provide if learner seems stuck
  * Use Socratic hints that guide without giving away the answer

- "isComplete": Challenge completion flag (boolean)
  * CRITICAL: Set to true ONLY when challenge is completely finished AND learner has passed
  * Learner must have scored at least {passing_score}% to pass
  * Keep false for all other messages, even congratulatory ones
  * When you set isComplete: true, the system will mark the session as complete and award XP

{progress_instructions["tracking_rules"]}

Strict Requirements:
1. Include metadata XML tags in EVERY response
2. Place metadata at the END of your response
3. Ensure JSON is valid (use double quotes, proper escaping)
4. Content outside metadata tags will be shown to the learner
5. Content inside metadata tags will be stripped and processed by the system

Example Response Structure:

[Your instructional content, question, or feedback here]

<metadata>
{progress_instructions["example_metadata"]}
</metadata>

Remember:
- Be encouraging and supportive
- Provide clear, specific feedback
{progress_instructions["additional_reminders"]}
- Ensure total scoreChange ≤ {xp_reward}
- Only set isComplete=true when learner has completed the challenge
"""

    return user_prompt + metadata_template


def _get_progress_instructions(config: Dict[str, Any], xp_reward: int) -> Dict[str, str]:
    """Get progress-specific instructions based on configured mode"""
    mode = config.get("mode", "questions")

    if mode == "questions":
        return _get_questions_mode_instructions(config, xp_reward)
    elif mode == "phases":
        return _get_phases_mode_instructions(config, xp_reward)
    elif mode == "milestones":
        return _get_milestones_mode_instructions(config, xp_reward)
    elif mode == "triggers":
        return _get_triggers_mode_instructions(config, xp_reward)
    else:
        return _get_legacy_progress_instructions(xp_reward)


def _get_questions_mode_instructions(config: Dict[str, Any], xp_reward: int) -> Dict[str, str]:
    """Instructions for questions-based progress tracking"""
    total_questions = config.get("total_questions", 5)
    points_per_question = xp_reward // total_questions

    return {
        "example_fields": f'"questionNumber": 1,\n  "totalQuestions": {total_questions},\n  "isQuestionComplete": true,',
        "field_definitions": f"""
- "questionNumber": Current question number (1-{total_questions})
  * Start at 1, increment for each new question
  * Track which question the learner is working on

- "totalQuestions": Total number of questions ({total_questions})
  * This is fixed for the entire challenge
  * Should always be {total_questions}

- "isQuestionComplete": Did learner answer this question correctly? (boolean)
  * Set to true when the learner provides a correct or acceptable answer
  * Set to false for incorrect answers or follow-up clarifications
  * Only advance questionNumber when this is true
""",
        "progress_calculation": f"Calculate as: (questionNumber / {total_questions}) * 100. Example: Question 2 of {total_questions} = {(2/total_questions)*100:.0f}%",
        "tracking_rules": f"""
Progress Tracking Rules (QUESTIONS Mode):
1. This challenge has exactly {total_questions} questions
2. Start with questionNumber=1, advance to 2, 3, etc.
3. Only increment questionNumber when isQuestionComplete=true
4. progressPercent should equal (questionNumber / {total_questions}) * 100
5. Award approximately {points_per_question} XP per question (can vary based on difficulty)
6. CRITICAL: Set isComplete=true ONLY in the response after answering Question {total_questions} correctly
   - Check: questionNumber={total_questions} AND isQuestionComplete=true
   - This signals the system to mark the challenge as complete and award XP
7. You can ask follow-up questions or provide hints without advancing questionNumber
""",
        "example_metadata": f"""{{
  "questionType": "mcq",
  "options": ["Option A", "Option B", "Option C"],
  "correctAnswer": 0,
  "questionNumber": 1,
  "totalQuestions": {total_questions},
  "isQuestionComplete": true,
  "progressPercent": {(1/total_questions)*100:.0f},
  "scoreChange": {points_per_question},
  "hint": "Consider the fundamental concept",
  "isComplete": false
}}""",
        "additional_reminders": f"- Track progress through {total_questions} distinct questions\n- Increment questionNumber only after correct answers"
    }


def _get_phases_mode_instructions(config: Dict[str, Any], xp_reward: int) -> Dict[str, str]:
    """Instructions for phases-based progress tracking"""
    phases = config.get("phases", [])
    total_phases = len(phases)

    phase_list = "\n".join([f"  * Phase {p['number']}: {p['name']} - {p.get('description', '')}" for p in phases])

    return {
        "example_fields": f'"phase": 1,\n  "totalPhases": {total_phases},\n  "phaseName": "{phases[0]["name"] if phases else "Introduction"}",\n  "isPhaseComplete": false,',
        "field_definitions": f"""
- "phase": Current learning phase (1-{total_phases})
  * {phase_list}
  * Advance to next phase when current phase objectives are met

- "totalPhases": Total number of phases ({total_phases})
  * This is fixed for the entire challenge

- "phaseName": Name of current phase (string)
  * Must match one of the configured phase names

- "isPhaseComplete": Is the current phase finished? (boolean)
  * Set to true when learner has completed phase objectives
  * Next response should increment phase number
  * Multiple interactions can occur within a single phase
""",
        "progress_calculation": f"Calculate as: (phase / {total_phases}) * 100. Example: Phase 2 of {total_phases} = {(2/total_phases)*100:.0f}%",
        "tracking_rules": f"""
Progress Tracking Rules (PHASES Mode):
1. This challenge has {total_phases} distinct phases
2. Start in phase 1, progress through phases sequentially
3. Each phase can have multiple questions/interactions
4. Set isPhaseComplete=true when phase objectives are met
5. progressPercent should equal (phase / {total_phases}) * 100
6. Award XP throughout each phase based on interaction quality
7. Set isComplete=true only when phase={total_phases} AND isPhaseComplete=true
""",
        "example_metadata": f"""{{
  "questionType": "text",
  "phase": 1,
  "totalPhases": {total_phases},
  "phaseName": "{phases[0]["name"] if phases else "Introduction"}",
  "isPhaseComplete": false,
  "progressPercent": {(1/total_phases)*100:.0f},
  "scoreChange": 15,
  "hint": "Think about the key concepts",
  "isComplete": false
}}""",
        "additional_reminders": f"- Guide learners through {total_phases} distinct learning phases\n- Multiple interactions per phase are encouraged"
    }


def _get_milestones_mode_instructions(config: Dict[str, Any], xp_reward: int) -> Dict[str, str]:
    """Instructions for milestones-based progress tracking"""
    milestones = config.get("milestones", [])
    total_milestones = len(milestones)

    milestone_list = "\n".join([f"  * {m['id']}: {m['name']} ({m.get('points', 25)} points)" for m in milestones])

    return {
        "example_fields": f'"milestoneId": "{milestones[0]["id"] if milestones else "milestone_1"}",\n  "milestoneName": "{milestones[0]["name"] if milestones else "First Milestone"}",\n  "isMilestoneAchieved": true,\n  "achievedMilestones": ["{milestones[0]["id"] if milestones else "milestone_1"}"],\n  "totalMilestones": {total_milestones},',
        "field_definitions": f"""
- "milestoneId": ID of milestone being worked on (string)
  * {milestone_list}
  * Can work on milestones in any order (non-linear progression)

- "milestoneName": Human-readable milestone name (string)
  * Must match the name for the given milestoneId

- "isMilestoneAchieved": Did learner achieve this milestone? (boolean)
  * Set to true when learner demonstrates the required skill/knowledge
  * Each milestone can only be achieved once

- "achievedMilestones": Array of all milestone IDs achieved so far
  * Accumulates throughout the challenge
  * No duplicates allowed

- "totalMilestones": Total number of milestones ({total_milestones})
  * This is fixed for the entire challenge
""",
        "progress_calculation": f"Calculate as: (achievedMilestones.length / {total_milestones}) * 100",
        "tracking_rules": f"""
Progress Tracking Rules (MILESTONES Mode):
1. This challenge has {total_milestones} achievement milestones
2. Milestones can be achieved in any order (non-linear)
3. Each milestone can only be achieved once (check achievedMilestones list)
4. progressPercent = (achievedMilestones.length / {total_milestones}) * 100
5. Award points based on milestone difficulty (see milestone definitions)
6. Set isComplete=true only when all {total_milestones} milestones are achieved
""",
        "example_metadata": f"""{{
  "questionType": "text",
  "milestoneId": "{milestones[0]["id"] if milestones else "milestone_1"}",
  "milestoneName": "{milestones[0]["name"] if milestones else "First Milestone"}",
  "isMilestoneAchieved": true,
  "achievedMilestones": ["{milestones[0]["id"] if milestones else "milestone_1"}"],
  "totalMilestones": {total_milestones},
  "progressPercent": {(1/total_milestones)*100:.0f},
  "scoreChange": {milestones[0].get("points", 25) if milestones else 25},
  "hint": null,
  "isComplete": false
}}""",
        "additional_reminders": f"- Guide learners to achieve {total_milestones} milestones\n- Milestones can be achieved in any order\n- Prevent duplicate milestone achievements"
    }


def _get_triggers_mode_instructions(config: Dict[str, Any], xp_reward: int) -> Dict[str, str]:
    """Instructions for triggers-based progress tracking"""
    triggers = config.get("triggers", [])
    total_triggers = len(triggers)
    points_per_trigger = xp_reward // total_triggers

    trigger_list = "\n".join([f"  * {t}" for t in triggers])

    return {
        "example_fields": f'"triggerId": "{triggers[0] if triggers else "trigger_1"}",\n  "isTriggerActivated": true,\n  "activatedTriggers": ["{triggers[0] if triggers else "trigger_1"}"],\n  "totalTriggers": {total_triggers},',
        "field_definitions": f"""
- "triggerId": ID of trigger being activated (string)
  * {trigger_list}
  * Activate triggers based on learner's demonstrated understanding

- "isTriggerActivated": Did learner activate this trigger? (boolean)
  * Set to true when learner demonstrates understanding of the concept
  * Based on conversation analysis, not explicit keywords

- "activatedTriggers": Array of all trigger IDs activated so far
  * Accumulates throughout the challenge
  * No duplicates allowed
  * Can be in any order based on conversation flow

- "totalTriggers": Total number of triggers ({total_triggers})
  * This is fixed for the entire challenge
""",
        "progress_calculation": f"Calculate as: (activatedTriggers.length / {total_triggers}) * 100",
        "tracking_rules": f"""
Progress Tracking Rules (TRIGGERS Mode):
1. This challenge has {total_triggers} concept triggers
2. Engage in natural conversation, activate triggers when concepts emerge
3. Triggers activate when learner demonstrates understanding (not by keyword matching)
4. Each trigger can only activate once (check activatedTriggers list)
5. Triggers can activate in any order based on conversation flow
6. progressPercent = (activatedTriggers.length / {total_triggers}) * 100
7. Award approximately {points_per_trigger} XP per trigger
8. Set isComplete=true only when all {total_triggers} triggers are activated
""",
        "example_metadata": f"""{{
  "questionType": "text",
  "triggerId": "{triggers[0] if triggers else "trigger_1"}",
  "isTriggerActivated": true,
  "activatedTriggers": ["{triggers[0] if triggers else "trigger_1"}"],
  "totalTriggers": {total_triggers},
  "progressPercent": {(1/total_triggers)*100:.0f},
  "scoreChange": {points_per_trigger},
  "hint": "Consider exploring this concept further",
  "isComplete": false
}}""",
        "additional_reminders": f"- Guide natural conversation to activate {total_triggers} triggers\n- Trigger activation is based on demonstrated understanding\n- Prevent duplicate trigger activations"
    }


def _get_legacy_progress_instructions(xp_reward: int) -> Dict[str, str]:
    """Legacy progress instructions (for challenges without progress_config)"""
    return {
        "example_fields": '"phase": 1,\n  "progressIncrement": 10,',
        "field_definitions": """
- "phase": Current learning phase (integer)
  * Start at 1, increment as learner progresses
  * Use phases to track which section of the challenge the learner is in

- "progressIncrement": Percentage contribution to overall progress (0-100)
  * Should total 100 across all questions
  * Example: For 5 questions, use 20 per question
  * Adjust based on question importance/difficulty
""",
        "progress_calculation": "Sum of all progressIncrement values from previous interactions",
        "tracking_rules": """
Progress Tracking Rules (LEGACY Mode):
1. Use phases to organize the challenge into sections
2. Award progressIncrement based on question importance
3. Ensure total progressIncrement = 100 across all interactions
""",
        "example_metadata": f"""{{
  "questionType": "mcq",
  "options": ["Functions allow code reuse", "Functions are loops", "Functions are variables"],
  "correctAnswer": 0,
  "phase": 1,
  "progressIncrement": 25,
  "scoreChange": 25,
  "hint": "Think about the primary purpose of defining a function",
  "isComplete": false
}}""",
        "additional_reminders": "- Track progress through phases\n- Ensure total progressIncrement = 100"
    }


def get_metadata_example(question_type: str = "mcq") -> str:
    """
    Get a formatted example of metadata for documentation or preview.

    Args:
        question_type: Type of question ("mcq", "text", or "upload")

    Returns:
        JSON string with example metadata
    """
    examples = {
        "mcq": """{
  "questionType": "mcq",
  "options": ["Option A", "Option B", "Option C"],
  "correctAnswer": 0,
  "phase": 1,
  "progressIncrement": 33,
  "scoreChange": 30,
  "hint": "Consider the fundamental concept",
  "isComplete": false
}""",
        "text": """{
  "questionType": "text",
  "phase": 2,
  "progressIncrement": 34,
  "scoreChange": 35,
  "hint": "Think about the specific requirements",
  "isComplete": false
}""",
        "upload": """{
  "questionType": "upload",
  "phase": 3,
  "progressIncrement": 33,
  "scoreChange": 35,
  "hint": null,
  "isComplete": true
}"""
    }

    return examples.get(question_type, examples["mcq"])
