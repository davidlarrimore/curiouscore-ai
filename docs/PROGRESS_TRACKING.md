# Progress Tracking System for Simple Challenges

## Overview

The Progress Tracking System provides four distinct modes for measuring learner progression through Simple challenges. Each mode is optimized for different learning scenarios and provides clear, measurable progression criteria.

## Quick Start

### 1. Configure Progress Tracking

Add a `progress_tracking` configuration to your challenge's `custom_variables` field:

```json
{
  "custom_variables": {
    "progress_tracking": {
      "mode": "questions",
      "total_questions": 5
    }
  }
}
```

### 2. LLM Automatically Receives Instructions

The system automatically injects mode-specific instructions into the LLM's system prompt based on your configuration.

### 3. Metadata Includes Progress Fields

The LLM includes progress-specific fields in its metadata responses:

```json
{
  "questionType": "mcq",
  "options": ["Option A", "Option B", "Option C"],
  "correctAnswer": 0,
  "questionNumber": 1,
  "totalQuestions": 5,
  "isQuestionComplete": true,
  "progressPercent": 20,
  "scoreChange": 30,
  "isComplete": false
}
```

---

## Progress Modes

### Mode 1: QUESTIONS

**Best for**: Step-by-step learning with discrete Q&A interactions

**Configuration**:
```json
{
  "progress_tracking": {
    "mode": "questions",
    "total_questions": 5
  }
}
```

**How It Works**:
- Challenge has a fixed number of questions (e.g., 5)
- LLM asks questions sequentially (1, 2, 3, 4, 5)
- Progress = questions_answered / total_questions * 100
- Challenge completes when all questions are answered correctly

**Metadata Fields**:
| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `questionNumber` | integer | Current question (1-indexed) | `1` |
| `totalQuestions` | integer | Total questions in challenge | `5` |
| `isQuestionComplete` | boolean | Did learner answer correctly? | `true` |
| `progressPercent` | integer | Current progress percentage | `20` (1/5 * 100) |

**Example Metadata**:
```json
{
  "questionType": "mcq",
  "options": ["Rights-Impacting ⚖️", "Goal-Advancing ⚡", "Socially-Constructed 🤝"],
  "correctAnswer": 0,
  "questionNumber": 1,
  "totalQuestions": 5,
  "isQuestionComplete": true,
  "progressPercent": 20,
  "scoreChange": 30,
  "hint": "Consider which category focuses on regulatory compliance",
  "isComplete": false
}
```

**Progression Example**:
1. Question 1 correct → 20% progress
2. Question 2 correct → 40% progress
3. Question 3 correct → 60% progress
4. Question 4 correct → 80% progress
5. Question 5 correct → 100% progress (isComplete=true)

**Key Rules**:
- ✅ Only increment `questionNumber` when `isQuestionComplete=true`
- ✅ Can provide hints/feedback without advancing question number
- ✅ `progressPercent` must equal `(questionNumber / totalQuestions) * 100`
- ✅ `isComplete=true` only when `questionNumber == totalQuestions` AND `isQuestionComplete=true`

---

### Mode 2: PHASES

**Best for**: Multi-stage learning journeys with distinct conceptual sections

**Configuration**:
```json
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
```

**How It Works**:
- Challenge divided into named phases (e.g., Introduction, Practice, Assessment)
- Each phase can have multiple questions/interactions
- Progress = current_phase / total_phases * 100
- LLM decides when to advance to next phase

**Metadata Fields**:
| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `phase` | integer | Current phase number (1-indexed) | `1` |
| `totalPhases` | integer | Total phases in challenge | `3` |
| `phaseName` | string | Name of current phase | `"Introduction"` |
| `isPhaseComplete` | boolean | Is current phase finished? | `false` |
| `progressPercent` | integer | Current progress percentage | `33` (1/3 * 100) |

**Example Metadata**:
```json
{
  "questionType": "text",
  "phase": 1,
  "totalPhases": 3,
  "phaseName": "Introduction",
  "isPhaseComplete": false,
  "progressPercent": 33,
  "scoreChange": 15,
  "hint": "Think about the core principles",
  "isComplete": false
}
```

**Progression Example**:
1. Phase 1 (Introduction): Multiple interactions → Set `isPhaseComplete=true`
2. Phase 2 (Practice): Multiple interactions → Set `isPhaseComplete=true`
3. Phase 3 (Assessment): Complete final task → `isComplete=true`

**Key Rules**:
- ✅ Multiple interactions allowed within a single phase
- ✅ Set `isPhaseComplete=true` when phase objectives met
- ✅ Next response after `isPhaseComplete=true` should increment `phase`
- ✅ `progressPercent` must equal `(phase / totalPhases) * 100`
- ✅ `isComplete=true` only when `phase == totalPhases` AND `isPhaseComplete=true`

---

### Mode 3: MILESTONES

**Best for**: Achievement-based learning with specific accomplishments

**Configuration**:
```json
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
```

**How It Works**:
- Challenge has specific achievement milestones
- Milestones can be achieved in ANY order (non-linear)
- Progress = achieved_milestones / total_milestones * 100
- LLM determines when learner has demonstrated required skill

**Metadata Fields**:
| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `milestoneId` | string | ID of milestone being worked on | `"understand_variables"` |
| `milestoneName` | string | Human-readable milestone name | `"Understand Variables"` |
| `isMilestoneAchieved` | boolean | Did learner achieve this milestone? | `true` |
| `achievedMilestones` | array | All milestones achieved so far | `["understand_variables"]` |
| `totalMilestones` | integer | Total milestones in challenge | `4` |
| `progressPercent` | integer | Current progress percentage | `25` (1/4 * 100) |

**Example Metadata**:
```json
{
  "questionType": "text",
  "milestoneId": "understand_variables",
  "milestoneName": "Understand Variables",
  "isMilestoneAchieved": true,
  "achievedMilestones": ["understand_variables"],
  "totalMilestones": 4,
  "progressPercent": 25,
  "scoreChange": 25,
  "hint": null,
  "isComplete": false
}
```

**Progression Example** (non-linear):
1. Achieve "understand_variables" → 25% progress
2. Achieve "debug_code" (out of order!) → 50% progress
3. Achieve "write_function" → 75% progress
4. Achieve "use_loops" → 100% progress (isComplete=true)

**Key Rules**:
- ✅ Milestones can be achieved in ANY order
- ✅ NO duplicate achievements (check `achievedMilestones` array)
- ✅ `progressPercent` = `(achievedMilestones.length / totalMilestones) * 100`
- ✅ Award points based on milestone configuration
- ✅ `isComplete=true` only when all milestones achieved

---

### Mode 4: TRIGGERS

**Best for**: Conversation-driven learning with concept-based progression

**Configuration**:
```json
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
```

**How It Works**:
- Challenge has conceptual triggers to activate
- LLM engages in natural conversation
- Triggers activate when learner demonstrates understanding
- Progress = activated_triggers / total_triggers * 100

**Metadata Fields**:
| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `triggerId` | string | ID of trigger being activated | `"explain_transformers"` |
| `isTriggerActivated` | boolean | Did learner activate this trigger? | `true` |
| `activatedTriggers` | array | All triggers activated so far | `["explain_transformers"]` |
| `totalTriggers` | integer | Total triggers in challenge | `4` |
| `progressPercent` | integer | Current progress percentage | `25` (1/4 * 100) |

**Example Metadata**:
```json
{
  "questionType": "text",
  "triggerId": "explain_transformers",
  "isTriggerActivated": true,
  "activatedTriggers": ["explain_transformers"],
  "totalTriggers": 4,
  "progressPercent": 25,
  "scoreChange": 25,
  "hint": "Consider exploring tokenization next",
  "isComplete": false
}
```

**Progression Example**:
1. Natural conversation about transformers → Trigger "explain_transformers" activates → 25%
2. Discuss use cases → Trigger "identify_use_case" activates → 50%
3. Talk about limitations → Trigger "discuss_limitations" activates → 75%
4. Propose application → Trigger "propose_application" activates → 100% (isComplete=true)

**Key Rules**:
- ✅ Triggers activate based on demonstrated understanding (NOT keyword matching)
- ✅ Triggers can activate in ANY order based on conversation flow
- ✅ NO duplicate activations (check `activatedTriggers` array)
- ✅ `progressPercent` = `(activatedTriggers.length / totalTriggers) * 100`
- ✅ `isComplete=true` only when all triggers activated

---

## Common Fields Across All Modes

These fields are REQUIRED in all metadata responses regardless of progress mode:

| Field | Type | Description |
|-------|------|-------------|
| `questionType` | string | Type of interaction: `"text"`, `"mcq"`, or `"upload"` |
| `progressPercent` | integer | Current overall progress (0-100) |
| `scoreChange` | integer | XP points awarded for this interaction |
| `isComplete` | boolean | Is the entire challenge complete? |
| `hint` | string/null | Optional hint text if learner is stuck |

---

## Implementation Guide

### For Challenge Authors

**Step 1: Choose Your Progress Mode**

Consider your learning objectives:
- **Questions**: Clear, sequential Q&A format
- **Phases**: Conceptual journey with distinct stages
- **Milestones**: Achievement-based, non-linear progression
- **Triggers**: Conversational, concept-driven learning

**Step 2: Add Configuration**

Edit your challenge's `custom_variables` field in the admin panel:

```json
{
  "course_name": "AI Ethics 101",
  "progress_tracking": {
    "mode": "questions",
    "total_questions": 5
  }
}
```

**Step 3: Write Your System Prompt**

Focus on your teaching content. The system automatically injects progress tracking instructions:

```
You are an AI Ethics instructor teaching about ethical dimensions in AI systems.

Guide learners through understanding:
1. Rights-Impacting decisions
2. Goal-Advancing considerations
3. Socially-Constructed norms

Be encouraging and provide clear feedback on their answers.
```

The system adds the metadata format requirements automatically!

**Step 4: Test Your Challenge**

Use the "Test Challenge" feature in the admin panel to verify:
- ✅ Metadata includes correct progress fields
- ✅ Progress calculation is accurate
- ✅ Completion logic works correctly

---

### For Frontend Developers

**Display Progress Indicator**

The `uiResponse` includes progress information:

```typescript
// Progress bar
<Progress value={uiResponse.progress_percent} />

// Mode-specific display
{progressMode === 'questions' && (
  <p>Question {currentQuestion} of {totalQuestions}</p>
)}

{progressMode === 'phases' && (
  <p>Phase: {phaseName}</p>
)}

{progressMode === 'milestones' && (
  <p>{achievedMilestones.length} / {totalMilestones} Milestones</p>
)}

{progressMode === 'triggers' && (
  <p>{activatedTriggers.length} / {totalTriggers} Concepts Explored</p>
)}
```

---

## Validation & Error Handling

The backend validates progress metadata using `progress_tracking.py`:

```python
from app.progress_tracking import validate_progress_metadata, ProgressConfig

# Validate metadata against config
is_valid, error, updated_state = validate_progress_metadata(
    config=ProgressConfig(**challenge.custom_variables["progress_tracking"]),
    metadata=llm_metadata,
    current_progress_state=session.progress_state
)

if not is_valid:
    logger.warning(f"Progress validation error: {error}")
```

**Common Validation Errors**:
- `questionNumber` out of range
- `progressPercent` doesn't match calculation
- Duplicate milestones in `achievedMilestones`
- Invalid `milestoneId` or `triggerId`

---

## Testing Strategy

### Unit Tests

Test each progress mode independently:

```python
def test_questions_mode_progress():
    """Test questions mode advances correctly"""
    config = ProgressConfig(mode="questions", total_questions=5)

    # Question 1 correct
    metadata = {
        "questionNumber": 1,
        "isQuestionComplete": True,
        "progressPercent": 20
    }
    is_valid, error, state = validate_progress_metadata(config, metadata, {})
    assert is_valid
    assert state["questions_answered"] == 1

    # Question 2 correct
    metadata = {
        "questionNumber": 2,
        "isQuestionComplete": True,
        "progressPercent": 40
    }
    is_valid, error, state = validate_progress_metadata(config, metadata, state)
    assert is_valid
    assert state["questions_answered"] == 2
```

### Integration Tests

Test complete challenge flows:

1. Create challenge with progress config
2. Start session
3. Submit answers
4. Verify progress updates correctly
5. Verify completion logic

---

## Migration from Legacy Progress Tracking

Challenges without `progress_tracking` configuration continue to work with legacy progress tracking:

```json
{
  "questionType": "mcq",
  "phase": 1,
  "progressIncrement": 20,  // Legacy field
  "scoreChange": 25,
  "isComplete": false
}
```

To migrate:

1. Analyze your challenge's progression pattern
2. Choose the most appropriate mode
3. Add `progress_tracking` configuration
4. Test thoroughly

---

## Best Practices

### ✅ DO

- Choose the mode that best fits your learning objectives
- Test your configuration with the Test Challenge feature
- Provide clear, encouraging feedback to learners
- Award XP based on interaction difficulty/importance
- Set `isComplete=true` only when all criteria met

### ❌ DON'T

- Mix multiple progress modes in one challenge
- Create duplicate milestones or triggers
- Advance progress for incorrect answers
- Exceed `xp_reward` total across all interactions
- Set `isComplete=true` prematurely

---

## Examples

See `/docs/examples/` for complete challenge examples:

- `questions_mode_example.json` - 5-question AI Ethics challenge
- `phases_mode_example.json` - 3-phase Python learning journey
- `milestones_mode_example.json` - 4-milestone coding challenge
- `triggers_mode_example.json` - Conversational transformer discussion

---

## Support

For questions or issues:
- Check validation errors in backend logs
- Use Test Challenge feature for debugging
- Refer to `backend/app/progress_tracking.py` for validation logic
- See `backend/app/prompt_injection.py` for instruction templates
