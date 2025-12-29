"""
LLM Orchestrator

Routes LLM tasks to the appropriate handler with correct prompting and parameters.
The orchestrator is a tool for the engine - LLMs provide signals, never authority.

Key Principles:
- Engine requests LLM tasks; orchestrator executes them
- Each task type has bounded purpose and specific temperature
- LLMs never update state or make decisions
- All outputs are validated and enforced by the engine

Task Types:
1. GM_NARRATE: Creative storytelling and coaching (temperature: 0.7)
2. LEM_EVALUATE: Rubric-based assessment (temperature: 0.0)
3. TEACH_HINTS: Instructional guidance (temperature: 0.5, Week 4)
"""

import json
from typing import Optional, Any
from pydantic import BaseModel, ValidationError

from ..llm_router import llm_router
from ..schemas import LLMChatRequest, LLMProvider, LLMMessage
from ..config import settings


class LEMEvaluation(BaseModel):
    """
    Structured output from LEM evaluation.
    Engine enforces these constraints - LEM only provides signals.
    """
    raw_score: int  # LEM's suggested score
    rationale: str  # Explanation of scoring
    criteria_scores: dict[str, int]  # Individual criterion scores
    passed: bool  # LEM's assessment (engine enforces threshold)


class LLMOrchestrator:
    """
    Orchestrates LLM calls for different game engine tasks.
    Each task type has specific configuration and constraints.
    """

    def __init__(self):
        """Initialize orchestrator with default provider/model from settings."""
        self.default_provider = settings.default_llm_provider or "anthropic"
        self.default_model = settings.default_llm_model or "claude-3-5-sonnet-20241022"

    async def narrate_gm(
        self,
        context: dict[str, Any],
        provider: Optional[str] = None,
        model: Optional[str] = None
    ) -> str:
        """
        Generate GM narration for a step.

        Args:
            context: Context dict with step info, state summary, etc.
            provider: LLM provider (defaults to config)
            model: Model name (defaults to config)

        Returns:
            Narration text from GM
        """
        # Build system prompt
        system_prompt = """You are the Game Master for an educational challenge.

Your role:
- Narrate the learning journey with encouragement and guidance
- Provide context and motivation for each step
- Coach the learner through challenges
- NEVER decide scores or outcomes (the engine owns that)
- NEVER claim authority over progression

Keep narration:
- Concise (2-3 sentences)
- Encouraging and supportive
- Focused on learning, not entertainment"""

        # Build user message from context
        user_message = self._build_gm_message(context)

        # Make LLM call
        request = LLMChatRequest(
            provider=LLMProvider(provider or self.default_provider),
            model=model or self.default_model,
            messages=[LLMMessage(role="user", content=user_message)],
            system_prompt=system_prompt,
            temperature=0.7,  # Creative
            max_tokens=300
        )

        content = await llm_router.chat(request)
        return content.strip()

    async def evaluate_lem(
        self,
        answer: str,
        rubric: dict[str, Any],
        context: dict[str, Any],
        provider: Optional[str] = None,
        model: Optional[str] = None
    ) -> LEMEvaluation:
        """
        Evaluate a free-text answer using a rubric.

        Args:
            answer: User's answer to evaluate
            rubric: Rubric with criteria and point values
            context: Context dict with step info, question, etc.
            provider: LLM provider (defaults to config)
            model: Model name (defaults to config)

        Returns:
            LEMEvaluation with raw score and rationale

        Raises:
            ValueError: If LEM returns invalid JSON
        """
        # Build system prompt
        system_prompt = """You are a precise evaluation assistant for educational content.

Your role:
- Evaluate answers ONLY based on the provided rubric
- Return ONLY valid JSON (no other text)
- NEVER decide final scores (only provide assessment signals)
- Be fair and consistent in evaluation

You must respond with valid JSON matching this schema:
{
  "raw_score": <total points>,
  "rationale": "<brief explanation>",
  "criteria_scores": {
    "<criterion_name>": <points>,
    ...
  },
  "passed": <true/false>
}"""

        # Build user message with rubric and answer
        user_message = self._build_lem_message(answer, rubric, context)

        # Make LLM call
        request = LLMChatRequest(
            provider=LLMProvider(provider or self.default_provider),
            model=model or self.default_model,
            messages=[LLMMessage(role="user", content=user_message)],
            system_prompt=system_prompt,
            temperature=0.0,  # Deterministic
            max_tokens=500
        )

        content = await llm_router.chat(request)

        # Parse and validate JSON response
        try:
            # Extract JSON from response (in case LLM adds extra text)
            json_str = self._extract_json(content)
            data = json.loads(json_str)
            evaluation = LEMEvaluation(**data)
            return evaluation
        except (json.JSONDecodeError, ValidationError) as e:
            raise ValueError(f"LEM returned invalid JSON: {e}\nResponse: {content}")

    async def generate_hint(
        self,
        context: dict[str, Any],
        provider: Optional[str] = None,
        model: Optional[str] = None
    ) -> str:
        """
        Generate a hint for the current step.
        (Week 4 implementation)

        Args:
            context: Context dict with step info, state summary, etc.
            provider: LLM provider (defaults to config)
            model: Model name (defaults to config)

        Returns:
            Hint text
        """
        system_prompt = """You are an instructional guide providing hints for educational challenges.

Your role:
- Provide helpful hints without giving away the answer
- Use Socratic questioning to guide learning
- Adapt to the learner's previous attempts
- NEVER solve the problem for them

Keep hints:
- Concise (1-2 sentences)
- Focused on method, not solution
- Encouraging"""

        user_message = self._build_hint_message(context)

        request = LLMChatRequest(
            provider=LLMProvider(provider or self.default_provider),
            model=model or self.default_model,
            messages=[LLMMessage(role="user", content=user_message)],
            system_prompt=system_prompt,
            temperature=0.5,  # Balanced
            max_tokens=200
        )

        content = await llm_router.chat(request)
        return content.strip()

    # ========================================================================
    # Helper Methods - Build Prompts from Context
    # ========================================================================

    def _build_gm_message(self, context: dict[str, Any]) -> str:
        """Build user message for GM narration."""
        step_title = context.get("step_title", "")
        step_instruction = context.get("step_instruction", "")
        gm_context = context.get("gm_context", "")
        state_summary = context.get("state_summary", "")
        current_score = context.get("current_score", 0)
        max_score = context.get("max_score", 100)
        step_index = context.get("step_index", 0)
        total_steps = context.get("total_steps", 1)

        message = f"""Step {step_index + 1} of {total_steps}: {step_title}

Instruction: {step_instruction}

Current score: {current_score}/{max_score}

Context: {gm_context}

State summary: {state_summary}

Provide brief narration to introduce this step and motivate the learner."""

        return message

    def _build_lem_message(
        self,
        answer: str,
        rubric: dict[str, Any],
        context: dict[str, Any]
    ) -> str:
        """Build user message for LEM evaluation."""
        question = context.get("step_instruction", "")
        step_title = context.get("step_title", "")

        # Format rubric
        rubric_text = json.dumps(rubric, indent=2)

        message = f"""Question: {step_title}
{question}

Student's Answer:
{answer}

Rubric:
{rubric_text}

Evaluate the answer according to the rubric and return valid JSON with:
- raw_score: Total points earned
- rationale: Brief explanation (2-3 sentences)
- criteria_scores: Points for each criterion
- passed: Whether answer meets passing threshold

Remember: Return ONLY valid JSON, no other text."""

        return message

    def _build_hint_message(self, context: dict[str, Any]) -> str:
        """Build user message for hint generation."""
        step_title = context.get("step_title", "")
        step_instruction = context.get("step_instruction", "")
        state_summary = context.get("state_summary", "")
        hints_used = context.get("hints_used", 0)
        step_type = context.get("step_type", "")

        message = f"""Step: {step_title}
Instruction: {step_instruction}
Type: {step_type}
Hints used so far: {hints_used}

Progress summary: {state_summary}

Provide a helpful hint to guide the learner."""

        return message

    def _extract_json(self, text: str) -> str:
        """
        Extract JSON from LLM response.
        Handles cases where LLM adds extra text around the JSON.
        """
        text = text.strip()

        # If it starts with {, assume it's clean JSON
        if text.startswith("{"):
            # Find the matching closing brace
            brace_count = 0
            for i, char in enumerate(text):
                if char == "{":
                    brace_count += 1
                elif char == "}":
                    brace_count -= 1
                    if brace_count == 0:
                        return text[:i + 1]

        # Otherwise, try to find JSON between braces
        start = text.find("{")
        if start == -1:
            raise ValueError("No JSON object found in response")

        brace_count = 0
        for i in range(start, len(text)):
            if text[i] == "{":
                brace_count += 1
            elif text[i] == "}":
                brace_count -= 1
                if brace_count == 0:
                    return text[start:i + 1]

        raise ValueError("Unmatched braces in JSON")
