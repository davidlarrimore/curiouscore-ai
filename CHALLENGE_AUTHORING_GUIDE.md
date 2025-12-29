# Challenge Authoring Guide

A comprehensive guide for creating educational challenges in the CuriousCore Game Master architecture.

---

## Table of Contents

1. [Overview](#overview)
2. [Challenge Structure](#challenge-structure)
3. [Step Types](#step-types)
4. [Creating Rubrics](#creating-rubrics)
5. [Narrative Design](#narrative-design)
6. [Best Practices](#best-practices)
7. [Examples](#examples)

---

## Overview

### What is a Challenge?

A challenge is a structured learning experience that guides users through a topic using:
- **Mixed question types** (MCQ, free-text, gates)
- **Narrative pacing** with GM narration
- **Rubric-based evaluation** for free-text answers
- **Event sourcing** for deterministic replay

### Architecture Principles

**The Engine is Authoritative**:
- LLMs provide signals (evaluation) and content (narration)
- Engine makes all final decisions on scoring and progression
- No LLM has authority over game state

**Event-Driven Execution**:
- All state changes flow through immutable events
- State can be replayed deterministically

**Declarative UI Control**:
- Backend declares which UI input is allowed
- Frontend renders based on backend declaration

---

## Challenge Structure

### Challenge Metadata

```python
Challenge(
    id=str(uuid.uuid4()),
    title="Clear, Descriptive Title",
    description="2-3 sentences explaining what learners will master",
    tags=["difficulty", "topic", "category"],
    difficulty="beginner|intermediate|advanced",
    system_prompt="High-level description for context",
    estimated_time_minutes=15-30,
    xp_reward=50-200,
    passing_score=60-75,  # Percentage
    is_active=True
)
```

**Difficulty Guidelines**:
- **Beginner**: Fundamental concepts, gentle rubrics, 60-70% passing
- **Intermediate**: Applied knowledge, practical scenarios, 70% passing
- **Advanced**: Expert-level, precise rubrics, 75% passing

**Point Distribution**:
- Beginner: 100 points total
- Intermediate: 150 points total
- Advanced: 200 points total

---

## Step Types

### 1. CONTINUE_GATE

**Purpose**: Narrative pacing, transitions, building engagement

**When to Use**:
- Welcome messages
- Transitions between topics
- Building anticipation
- Celebrating progress

**Configuration**:
```python
ChallengeStep(
    step_type="CONTINUE_GATE",
    title="Welcome to Functions",
    instruction="Your narrative text here. Address the learner directly.",
    points_possible=0,  # Always 0 for gates
    passing_threshold=0,
    auto_narrate=True,  # Optional: GM narrates the instruction
    gm_context="Guidance for GM tone: encouraging, professional, etc."
)
```

**Best Practices**:
- Keep narrative concise (2-3 sentences)
- Build momentum, don't slow it down
- Use gates sparingly (not between every step)
- Make instructions welcoming and engaging

---

### 2. MCQ_SINGLE

**Purpose**: Validate understanding of specific concepts

**When to Use**:
- Testing definitions
- Identifying best practices
- Concept validation

**Configuration**:
```python
ChallengeStep(
    step_type="MCQ_SINGLE",
    title="What is a function?",
    instruction="Clear question with context",
    options=[
        "Correct answer",  # Index 0
        "Wrong answer 1",
        "Wrong answer 2",
        "Wrong answer 3"
    ],
    correct_answer=0,  # Index of correct answer
    points_possible=20-30,
    passing_threshold=100,  # Usually 100% for MCQ
    auto_narrate=False
)
```

**Best Practices**:
- Provide 3-4 options
- Make wrong answers plausible (test understanding, not guessing)
- Keep options concise
- Avoid "all of the above" or "none of the above"
- Put correct answer at index 0 for clarity

---

### 3. MCQ_MULTI

**Purpose**: Test comprehensive understanding of multi-faceted concepts

**When to Use**:
- Identifying multiple characteristics
- Selecting all applicable items
- Testing thorough knowledge

**Configuration**:
```python
ChallengeStep(
    step_type="MCQ_MULTI",
    title="Function components",
    instruction="Select ALL correct answers:",
    options=[
        "Component 1",  # Correct
        "Component 2",  # Correct
        "Wrong answer",
        "Component 3"   # Correct
    ],
    correct_answers=[0, 1, 3],  # Indices of all correct answers
    points_possible=30-35,
    passing_threshold=75,  # Can be < 100% for partial credit
    auto_narrate=False
)
```

**Scoring**: Partial credit based on percentage correct
- 3/3 correct = 100% of points
- 2/3 correct = 67% of points
- Must meet passing_threshold to advance

**Best Practices**:
- Have 2-4 correct answers out of 4-6 total
- Make it clear they should select ALL that apply
- Set passing_threshold to 75-100% depending on difficulty

---

### 4. TRUE_FALSE

**Purpose**: Test nuanced understanding or common misconceptions

**When to Use**:
- Validating understanding of edge cases
- Testing for common misconceptions
- Quick knowledge checks

**Configuration**:
```python
ChallengeStep(
    step_type="TRUE_FALSE",
    title="Return statements",
    instruction="True or False: Every function must return a value",
    correct_answer=False,  # or True
    points_possible=20,
    passing_threshold=100,
    auto_narrate=False
)
```

**Best Practices**:
- Use for important nuances, not trivial facts
- Statement should be clearly true or false (not ambiguous)
- Good for testing misconceptions
- Keep statement concise

---

### 5. CHAT (with LEM Evaluation)

**Purpose**: Deep understanding, explanation, application

**When to Use**:
- Explaining concepts in own words
- Demonstrating understanding
- Applying knowledge to scenarios
- Design or problem-solving tasks

**Configuration**:
```python
ChallengeStep(
    step_type="CHAT",
    title="Why use functions?",
    instruction="Clear prompt with specific requirements. Mention what to include.",
    rubric={
        "total_points": 30-50,
        "criteria": {
            "criterion_1": {
                "description": "Specific, measurable criterion",
                "points": 10-15
            },
            "criterion_2": {
                "description": "Another measurable criterion",
                "points": 10-15
            },
            "criterion_3": {
                "description": "Third criterion",
                "points": 10-15
            }
        },
        "passing_threshold": 60-65  # Percentage
    },
    points_possible=30-50,  # Should match rubric total_points
    passing_threshold=60-65,  # Should match rubric passing_threshold
    auto_narrate=True,  # GM provides feedback
    gm_context="Guidance for GM: what to emphasize, tone, etc."
)
```

**Best Practices**:
- See "Creating Rubrics" section below
- Keep rubric criteria objective and measurable
- Provide clear expectations in instruction
- Use GM narration to provide encouraging feedback

---

## Creating Rubrics

### Structure

```json
{
  "total_points": 40,
  "criteria": {
    "criterion_name": {
      "description": "What this criterion evaluates",
      "points": 10
    }
  },
  "passing_threshold": 60
}
```

### Guidelines

**Number of Criteria**: 2-4 criteria per rubric
- Too few: Not enough granularity
- Too many: Overwhelming, hard to evaluate fairly

**Point Distribution**: Distribute points meaningfully
- Each criterion: 5-16 points
- Higher points for more important criteria
- Total: 30-50 points for CHAT steps

**Passing Threshold**:
- Beginner: 60% (encouraging)
- Intermediate: 60-65% (balanced)
- Advanced: 65% (higher bar)

### Writing Criteria

**Good Criteria** (Objective, Measurable):
```json
{
  "reusability": {
    "description": "Explains that functions allow code reuse and avoid repetition",
    "points": 15
  }
}
```

**Bad Criteria** (Subjective, Vague):
```json
{
  "quality": {
    "description": "Answer is good",
    "points": 15
  }
}
```

**Criteria Should**:
- Be specific and measurable
- Test understanding, not writing style
- Focus on content, not length
- Be independent (not overlapping)

**Examples of Good Criteria Types**:
- **Concept explanation**: "Explains that X does Y"
- **Example provision**: "Provides at least one specific example"
- **Practical application**: "Describes a real-world use case"
- **Completeness**: "Addresses all aspects of the question"
- **Technical accuracy**: "Uses correct terminology"

---

## Narrative Design

### GM Narration

**Purpose**: Build engagement, provide context, encourage learners

**When to Use**:
- Welcome gates: Set expectations
- Transitions: Connect concepts
- CHAT feedback: Respond to answers
- Celebration: Acknowledge progress

**Tone Guidelines**:

**Beginner**:
```python
gm_context="Encouraging, supportive tone. Make it feel achievable."
```

**Intermediate**:
```python
gm_context="Professional but supportive. Emphasize real-world relevance."
```

**Advanced**:
```python
gm_context="Expert-level, high-bar tone. This is professional knowledge."
```

### Narrative Flow

**Good Challenge Flow**:
1. CONTINUE_GATE - Welcome (set expectations)
2. MCQ_SINGLE - Warmup (build confidence)
3. CHAT - Deep understanding (with GM feedback)
4. CONTINUE_GATE - Transition (connect concepts)
5. MCQ_MULTI - Comprehensive check
6. CHAT - Application (final demonstration)

**Avoid**:
- Too many gates (interrupts flow)
- All MCQ (no depth)
- All CHAT (too demanding)
- Random ordering (no progression)

---

## Best Practices

### Challenge Design

**Progressive Difficulty**:
- Start with easier questions (build confidence)
- Increase complexity as you go
- End with comprehensive application

**Balanced Question Types**:
- MCQ for validation (40-50%)
- CHAT for depth (30-40%)
- Gates for pacing (10-20%)

**Clear Learning Objectives**:
- Define 3-5 specific objectives
- Map each objective to 1-2 steps
- Ensure rubrics test those objectives

### Point Distribution

**Total Points by Difficulty**:
- Beginner: 100 points (70% = 70 to pass)
- Intermediate: 150 points (70% = 105 to pass)
- Advanced: 200 points (75% = 150 to pass)

**Point Allocation**:
- CONTINUE_GATE: 0 points (always)
- MCQ_SINGLE: 20-30 points
- MCQ_MULTI: 30-35 points
- TRUE_FALSE: 20 points
- CHAT: 30-50 points

### Writing Instructions

**Good Instruction**:
```
"In your own words, explain what a Git commit represents.
What does it capture, and why is it important for version control?
Include at least one specific benefit."
```

**Bad Instruction**:
```
"Explain commits."
```

**Tips**:
- Be specific about requirements
- Ask clear questions
- Mention what to include
- Give context when needed
- Keep it concise (2-3 sentences max)

### Testing Your Challenge

**Checklist**:
- [ ] Can be completed in estimated time
- [ ] Instructions are clear
- [ ] Rubrics are fair and measurable
- [ ] Point distribution makes sense
- [ ] Passing score is appropriate
- [ ] Narrative flows well
- [ ] All step types work correctly

---

## Examples

### Example 1: Beginner Challenge

**Topic**: Introduction to Variables

**Structure**:
- Total: 100 points, 70% passing
- 6 steps: 2 gates, 2 MCQ, 1 CHAT, 1 T/F

```python
# Step 0: Welcome gate
step_type="CONTINUE_GATE"
title="Welcome to Variables"
instruction="Variables are like labeled containers..."
auto_narrate=True

# Step 1: Definition check
step_type="MCQ_SINGLE"
title="What is a variable?"
points_possible=30

# Step 2: Deep understanding
step_type="CHAT"
title="Why use variables?"
points_possible=40
rubric={
    "criteria": {
        "storage": {"points": 15, "description": "Explains data storage"},
        "naming": {"points": 10, "description": "Mentions naming"},
        "purpose": {"points": 15, "description": "Describes why useful"}
    },
    "passing_threshold": 60
}

# Step 3: Transition
step_type="CONTINUE_GATE"
instruction="Great! Now let's explore types..."

# Step 4: Application
step_type="MCQ_SINGLE"
title="Variable naming"
points_possible=30
```

### Example 2: Advanced Challenge

**Topic**: API Design

**Structure**:
- Total: 200 points, 75% passing
- 7 steps: 2 gates, 2 MCQ, 3 CHAT

```python
# Step 0: High-bar introduction
step_type="CONTINUE_GATE"
instruction="This is expert-level knowledge..."
gm_context="Set professional, high-bar tone"

# Step 1: Deep conceptual understanding
step_type="CHAT"
title="Explain REST principles"
points_possible=40
rubric={
    "criteria": {
        "resources": {"points": 13, "description": "Resources not actions"},
        "http_methods": {"points": 13, "description": "Standard methods"},
        "stateless": {"points": 14, "description": "Stateless communication"}
    },
    "passing_threshold": 60
}

# Step 2: Knowledge check
step_type="MCQ_SINGLE"
title="HTTP method for updating"
points_possible=30

# Step 3: Design task
step_type="CHAT"
title="Design RESTful URLs"
points_possible=50
rubric={
    "criteria": {
        "plural_nouns": {"points": 13},
        "path_params": {"points": 12},
        "no_verbs": {"points": 13},
        "explanation": {"points": 12}
    },
    "passing_threshold": 65
}

# ... continue pattern
```

---

## Common Pitfalls to Avoid

### ❌ Don't

- Create all-MCQ challenges (no depth)
- Use subjective rubric criteria ("answer is good")
- Make gates too frequent (interrupts flow)
- Set passing scores too high (90%+)
- Create rubrics with < 2 or > 5 criteria
- Use vague instructions ("explain X")
- Make challenges too long (> 30 min)

### ✅ Do

- Mix question types for engagement
- Write objective, measurable criteria
- Use gates for pacing and transitions
- Set appropriate passing scores (60-75%)
- Create 2-4 focused criteria per rubric
- Write clear, specific instructions
- Keep challenges focused and achievable

---

## Summary

**Great challenges have**:
- Clear learning objectives
- Progressive difficulty
- Mixed question types
- Fair, objective rubrics
- Engaging narrative flow
- Appropriate passing scores
- Realistic time estimates

**The key is balance**: Validate understanding (MCQ), test depth (CHAT), and create engagement (gates).

Happy challenge authoring!
