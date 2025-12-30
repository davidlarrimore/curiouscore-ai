"""
System Prompt Injection

Augments user-provided system prompts with structured metadata requirements
to ensure LLM responses are properly formatted for Simple challenges.
"""


def inject_metadata_requirements(
    user_prompt: str,
    challenge_title: str,
    xp_reward: int,
    passing_score: int
) -> str:
    """
    Append metadata structure requirements to user's system prompt.

    This ensures the LLM knows to:
    1. Include metadata in every response
    2. Use the correct XML tag format
    3. Follow the JSON schema
    4. Track progression appropriately

    Args:
        user_prompt: The user-provided system prompt
        challenge_title: Title of the challenge (for context)
        xp_reward: Maximum XP for the challenge
        passing_score: Percentage required to pass

    Returns:
        Enhanced system prompt with metadata requirements injected
    """

    metadata_template = f"""

---

CRITICAL: Response Format Requirements for "{challenge_title}"

You MUST include metadata in EVERY response using this EXACT format:

<metadata>
{{
  "questionType": "text" | "mcq" | "upload",
  "options": ["Option 1", "Option 2", "Option 3"],
  "correctAnswer": 0,
  "phase": 1,
  "progressIncrement": 10,
  "scoreChange": 10,
  "hint": "Optional hint text",
  "isComplete": false
}}
</metadata>

Metadata Field Definitions:

- "questionType": Type of interaction
  * "text" = Free-text response
  * "mcq" = Multiple choice question
  * "upload" = File upload request

- "options": Array of answer choices (REQUIRED for mcq, omit for text/upload)
  * Provide 3-5 clear, distinct options
  * Options should be specific, not vague

- "correctAnswer": Zero-based index of correct option (REQUIRED for mcq, omit for text/upload)
  * 0 = first option, 1 = second option, etc.

- "phase": Current learning phase (integer)
  * Start at 1, increment as learner progresses
  * Use phases to track which section of the challenge the learner is in

- "progressIncrement": Percentage contribution to overall progress (0-100)
  * Should total 100 across all questions
  * Example: For 5 questions, use 20 per question
  * Adjust based on question importance/difficulty

- "scoreChange": XP points awarded for this interaction (0-{xp_reward})
  * Total scoreChange across all questions should not exceed {xp_reward}
  * Award more points for harder or more important questions
  * Can be 0 for introductory messages or hints

- "hint": Optional hint text (string or null)
  * Provide if learner seems stuck
  * Use Socratic hints that guide without giving away the answer

- "isComplete": Challenge completion flag (boolean)
  * Set to true ONLY when challenge is completely finished
  * Learner must have scored at least {passing_score}% to pass
  * Keep false for all other messages

Strict Requirements:
1. Include metadata XML tags in EVERY response
2. Place metadata at the END of your response
3. Ensure JSON is valid (use double quotes, proper escaping)
4. Content outside metadata tags will be shown to the learner
5. Content inside metadata tags will be stripped and processed by the system

Example Response Structure:

[Your instructional content, question, or feedback here]

<metadata>
{{
  "questionType": "mcq",
  "options": ["Functions allow code reuse", "Functions are loops", "Functions are variables"],
  "correctAnswer": 0,
  "phase": 1,
  "progressIncrement": 25,
  "scoreChange": 25,
  "hint": "Think about the primary purpose of defining a function",
  "isComplete": false
}}
</metadata>

Remember:
- Be encouraging and supportive
- Provide clear, specific feedback
- Track progress accurately through phases
- Ensure total progressIncrement = 100
- Ensure total scoreChange ≤ {xp_reward}
- Only set isComplete=true when learner has completed the challenge
"""

    return user_prompt + metadata_template


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
