"""
Three-Tier Verification Engine for Simple Challenge System Prompts

Tier 1: Heuristic Checks (instant, no API cost)
Tier 2: LLM Validation (optional, uses API tokens)
Tier 3: Test Run (user-initiated, full LLM interaction)
"""

import re
from typing import Optional, List
from pydantic import BaseModel

from .llm_router import LLMRouter
from .schemas import LLMChatRequest


class HeuristicResult(BaseModel):
    """Result from Tier 1 heuristic checks"""
    score: int  # 0-100
    passed: bool
    issues: List[str]  # Critical problems
    warnings: List[str]  # Suggestions for improvement


class LLMValidationResult(BaseModel):
    """Result from Tier 2 LLM validation"""
    feedback: str
    suggestions: List[str]
    confidence: int  # 0-100


class VerificationResult(BaseModel):
    """Combined result from all verification tiers"""
    tier1_heuristics: HeuristicResult
    tier2_llm: Optional[LLMValidationResult] = None
    tier3_test_available: bool = True
    overall_recommendation: str  # "approve", "review", or "reject"


# Assessment keywords that should appear in educational prompts
ASSESSMENT_KEYWORDS = [
    "question", "quiz", "test", "assess", "evaluate",
    "check", "answer", "explain", "describe", "solve"
]

# Learning keywords
LEARNING_KEYWORDS = [
    "learn", "understand", "teach", "instruct", "guide",
    "practice", "master", "explore", "discover"
]

# Metadata keywords
METADATA_KEYWORDS = [
    "metadata", "questionType", "phase", "progressIncrement",
    "scoreChange", "isComplete"
]


def verify_heuristics(system_prompt: str) -> HeuristicResult:
    """
    Tier 1: Perform fast heuristic checks on system prompt.

    Checks:
    - Minimum length
    - Contains assessment keywords
    - Mentions learning objectives
    - Has reasonable structure

    Args:
        system_prompt: The system prompt to verify

    Returns:
        HeuristicResult with score, pass/fail, issues, and warnings
    """
    score = 100
    issues = []
    warnings = []

    # Check 1: Minimum length (should be at least 100 characters)
    if len(system_prompt) < 100:
        score -= 30
        issues.append("Prompt is too short (minimum 100 characters recommended)")

    # Check 2: Contains assessment keywords
    prompt_lower = system_prompt.lower()
    has_assessment = any(keyword in prompt_lower for keyword in ASSESSMENT_KEYWORDS)
    if not has_assessment:
        score -= 20
        warnings.append(
            "Prompt doesn't mention assessment/questions. "
            "Consider adding keywords like 'question', 'quiz', 'evaluate', etc."
        )

    # Check 3: Contains learning keywords
    has_learning = any(keyword in prompt_lower for keyword in LEARNING_KEYWORDS)
    if not has_learning:
        score -= 10
        warnings.append(
            "Prompt doesn't mention learning objectives. "
            "Consider adding keywords like 'learn', 'teach', 'understand', etc."
        )

    # Check 4: Reasonable length (too long might confuse LLM)
    if len(system_prompt) > 5000:
        score -= 10
        warnings.append(
            "Prompt is very long (>5000 characters). "
            "Consider breaking into multiple phases or simplifying."
        )

    # Check 5: Has structure (multiple paragraphs or sections)
    paragraphs = [p.strip() for p in system_prompt.split("\n\n") if p.strip()]
    if len(paragraphs) < 2:
        score -= 5
        warnings.append(
            "Prompt appears to be a single block of text. "
            "Consider adding structure with paragraphs or sections."
        )

    # Check 6: Mentions progression/phases
    has_progression = any(
        word in prompt_lower
        for word in ["phase", "step", "part", "section", "progress"]
    )
    if not has_progression:
        score -= 10
        warnings.append(
            "Prompt doesn't mention progression/phases. "
            "This helps learners understand their journey through the challenge."
        )

    # Check 7: Includes context about difficulty or audience
    has_context = any(
        word in prompt_lower
        for word in ["beginner", "intermediate", "advanced", "learner", "student"]
    )
    if not has_context:
        score -= 5
        warnings.append(
            "Prompt doesn't specify target audience or difficulty level. "
            "This helps calibrate challenge difficulty."
        )

    # Ensure score doesn't go below 0
    score = max(0, score)

    # Determine pass/fail
    passed = score >= 60 and len(issues) == 0

    return HeuristicResult(
        score=score,
        passed=passed,
        issues=issues,
        warnings=warnings
    )


async def verify_llm(
    system_prompt: str,
    challenge_title: str,
    difficulty: str,
    llm_router: LLMRouter,
    provider: str = "anthropic",
    model: str = "claude-sonnet-4-5-20250929"
) -> LLMValidationResult:
    """
    Tier 2: Use LLM to validate prompt quality.

    The LLM evaluates:
    - Clarity of instructions
    - Alignment with stated difficulty
    - Pedagogical soundness
    - Potential issues or ambiguities

    Args:
        system_prompt: The system prompt to validate
        challenge_title: Title of the challenge
        difficulty: Difficulty level (beginner/intermediate/advanced)
        llm_router: LLM router instance for making API calls
        provider: LLM provider to use
        model: LLM model to use

    Returns:
        LLMValidationResult with feedback, suggestions, and confidence score
    """

    validation_prompt = f"""You are an expert instructional designer reviewing a system prompt for an educational AI challenge.

Challenge Title: "{challenge_title}"
Difficulty Level: {difficulty}

System Prompt to Review:
---
{system_prompt}
---

Please evaluate this system prompt on the following criteria:

1. Clarity: Are the instructions clear and unambiguous?
2. Difficulty Alignment: Does the content match the stated difficulty level ({difficulty})?
3. Pedagogical Soundness: Does it follow good teaching practices?
4. Assessment Quality: Are the learning objectives and assessment methods clear?
5. Engagement: Will this be engaging and motivating for learners?

Provide your response in this EXACT JSON format:
{{
  "feedback": "2-3 sentence overall assessment",
  "suggestions": ["suggestion 1", "suggestion 2", "suggestion 3"],
  "confidence": 85
}}

Where:
- feedback: Overall assessment of the prompt quality
- suggestions: List of 2-4 concrete improvements
- confidence: Your confidence in the prompt's effectiveness (0-100)

Return ONLY valid JSON, no other text."""

    try:
        # Make LLM call
        request = LLMChatRequest(
            provider=provider,
            model=model,
            messages=[{"role": "user", "content": validation_prompt}],
            system_prompt="You are a helpful instructional design expert. Return only valid JSON.",
            temperature=0.3,  # More deterministic
            max_tokens=800
        )

        response_text = await llm_router.chat(request)

        # Extract JSON (handle cases where LLM adds extra text)
        import json
        # Try to find JSON object in response
        json_match = re.search(r'\{[\s\S]*\}', response_text)
        if json_match:
            result_json = json.loads(json_match.group())
        else:
            # Fallback if no JSON found
            raise ValueError("No JSON found in LLM response")

        return LLMValidationResult(
            feedback=result_json.get("feedback", "Unable to parse feedback"),
            suggestions=result_json.get("suggestions", []),
            confidence=result_json.get("confidence", 50)
        )

    except Exception as e:
        # Graceful fallback if LLM validation fails
        return LLMValidationResult(
            feedback=f"LLM validation failed: {str(e)}",
            suggestions=["Consider running heuristic checks and manual review"],
            confidence=0
        )


async def verify_system_prompt(
    system_prompt: str,
    challenge_title: str,
    difficulty: str,
    run_llm: bool = True,
    llm_router: Optional[LLMRouter] = None
) -> VerificationResult:
    """
    Run comprehensive verification on a system prompt.

    Runs:
    - Tier 1 (always): Heuristic checks
    - Tier 2 (optional): LLM validation
    - Tier 3 (flagged): Test run availability

    Args:
        system_prompt: The system prompt to verify
        challenge_title: Title of the challenge
        difficulty: Difficulty level
        run_llm: Whether to run Tier 2 LLM validation
        llm_router: LLM router instance (required if run_llm=True)

    Returns:
        VerificationResult with all tier results and recommendation
    """

    # Tier 1: Always run heuristics
    tier1_result = verify_heuristics(system_prompt)

    # Tier 2: Optionally run LLM validation
    tier2_result = None
    if run_llm and llm_router:
        tier2_result = await verify_llm(
            system_prompt,
            challenge_title,
            difficulty,
            llm_router
        )

    # Determine overall recommendation
    recommendation = "approve"

    if tier1_result.score < 40 or len(tier1_result.issues) > 2:
        recommendation = "reject"
    elif tier1_result.score < 70 or len(tier1_result.issues) > 0:
        recommendation = "review"
    elif tier2_result and tier2_result.confidence < 50:
        recommendation = "review"

    return VerificationResult(
        tier1_heuristics=tier1_result,
        tier2_llm=tier2_result,
        tier3_test_available=True,  # Always available via separate endpoint
        overall_recommendation=recommendation
    )
