# Admin Guide: Setting Up Progress Tracking

This guide explains how to configure progress tracking for Simple challenges using the admin interface.

## Overview

Progress tracking allows you to define how learners progress through Simple challenges. Choose from 4 modes based on your learning objectives.

## Accessing the Progress Tracking Editor

1. Navigate to the **Admin** panel
2. Click **Create Challenge** or edit an existing challenge
3. Select **Simple** as the Challenge Type
4. Scroll down to the **Progress Tracking** section (below Custom Variables)

## Progress Tracking Editor

### Enabling/Disabling

Use the **Off/On** toggle in the top-right corner of the Progress Tracking card to enable or disable progress tracking.

- **Off**: Challenge uses legacy progress tracking (phase + progressIncrement)
- **On**: Challenge uses one of the 4 new progress modes

### Selecting a Mode

Choose from 4 progress modes using the dropdown:

---

## Mode 1: Questions

**Best for**: Step-by-step learning with discrete Q&A interactions

### Configuration

1. Select **Questions** from the mode dropdown
2. Set **Total Questions** (1-20)
3. View the suggested points per question

### Example Setup

- **Mode**: Questions
- **Total Questions**: 5
- **Points per question**: 30 XP (for 150 XP total reward)

### How It Works

- LLM asks questions sequentially (1, 2, 3, 4, 5)
- Progress bar shows: Question 1 = 20%, Question 2 = 40%, etc.
- Challenge completes when all questions are answered correctly

### Best Practices

- Use 3-7 questions for most challenges
- More questions = better granularity, but longer challenge
- Ensure XP reward is divisible by total questions for even distribution

---

## Mode 2: Phases

**Best for**: Multi-stage learning journeys with distinct conceptual sections

### Configuration

1. Select **Phases** from the mode dropdown
2. Configure each phase:
   - **Phase Name**: e.g., "Introduction", "Practice", "Assessment"
   - **Description**: Brief description of phase objectives
3. Click **Add Phase** to add more phases
4. Click the trash icon to remove phases

### Example Setup

- **Mode**: Phases
- **Phase 1**: Introduction - Learn basic concepts
- **Phase 2**: Practice - Apply concepts with examples
- **Phase 3**: Assessment - Demonstrate mastery

### How It Works

- LLM manages progression through phases
- Each phase can have multiple Q&A exchanges
- Progress bar shows: Phase 1 = 33%, Phase 2 = 66%, Phase 3 = 100%
- LLM decides when to advance to next phase based on learner performance

### Best Practices

- Use 2-5 phases for most challenges
- Give each phase a clear, descriptive name
- Phases work best when they represent conceptual stages, not individual questions

---

## Mode 3: Milestones

**Best for**: Achievement-based learning with specific accomplishments

### Configuration

1. Select **Milestones** from the mode dropdown
2. Configure each milestone:
   - **Milestone ID**: Unique identifier (e.g., `understand_variables`)
   - **Milestone Name**: Human-readable name (e.g., "Understand Variables")
   - **Points**: XP awarded for this milestone
3. Click **Add Milestone** to add more milestones
4. Click the trash icon to remove milestones

**IMPORTANT**: Total milestone points should equal your challenge's XP reward. The editor shows a warning if they don't match.

### Example Setup

- **Mode**: Milestones
- **Milestone 1**: `understand_variables` - Understand Variables (25 points)
- **Milestone 2**: `write_function` - Write a Function (25 points)
- **Milestone 3**: `use_loops` - Use Loops (25 points)
- **Milestone 4**: `debug_code` - Debug Code (25 points)
- **Total**: 100 points ✓

### How It Works

- Milestones can be achieved in **any order** (non-linear)
- Progress bar shows: 1 milestone = 25%, 2 milestones = 50%, etc.
- LLM determines when learner has demonstrated required skill
- Challenge completes when all milestones are achieved

### Best Practices

- Use 3-6 milestones for most challenges
- Make milestones specific and measurable
- Balance points based on milestone difficulty
- Use descriptive IDs (snake_case recommended)

---

## Mode 4: Triggers

**Best for**: Conversation-driven learning with concept-based progression

### Configuration

1. Select **Triggers** from the mode dropdown
2. Configure each trigger:
   - **Trigger ID**: Concept identifier (e.g., `explain_transformers`)
3. Click **Add Trigger** to add more triggers
4. Click the trash icon to remove triggers

### Example Setup

- **Mode**: Triggers
- **Trigger 1**: `explain_transformers`
- **Trigger 2**: `identify_use_case`
- **Trigger 3**: `discuss_limitations`
- **Trigger 4**: `propose_application`

### How It Works

- LLM engages in natural conversation
- Triggers activate when learner demonstrates understanding of concepts
- Progress bar shows: 1 trigger = 25%, 2 triggers = 50%, etc.
- Triggers can activate in any order based on conversation flow
- Challenge completes when all triggers are activated

### Best Practices

- Use 3-6 triggers for most challenges
- Name triggers based on learning objectives, not literal keywords
- LLM activates triggers based on understanding, not keyword matching
- Works best for open-ended, exploratory learning

---

## Complete Setup Workflow

### 1. Create/Edit Challenge

Navigate to Admin → Create Challenge or click edit on an existing challenge.

### 2. Set Basic Details

- **Title**: Your challenge title
- **Description**: What learners will learn
- **Tags**: Categorize your challenge
- **Difficulty**: beginner, intermediate, or advanced
- **XP Reward**: Total points learners can earn (e.g., 150)
- **Passing Score**: Minimum percentage to pass (e.g., 70%)

### 3. Write System Prompt

Write your teaching instructions. Example:

```
You are an AI Ethics instructor teaching about ethical dimensions in AI systems.

Guide learners through understanding:
1. Rights-Impacting decisions (regulatory compliance, legal frameworks)
2. Goal-Advancing considerations (organizational objectives, efficiency)
3. Socially-Constructed norms (cultural values, social expectations)

For each concept, provide clear examples and ask thought-provoking questions.
Be encouraging and provide constructive feedback.
```

**Note**: You DON'T need to include metadata format instructions - the system adds them automatically based on your progress tracking configuration!

### 4. Configure Custom Variables (Optional)

Add any variables you want to use in your prompt (e.g., `course_name`, `instructor_name`).

### 5. Configure Progress Tracking

1. Toggle **On**
2. Select your mode (Questions, Phases, Milestones, or Triggers)
3. Configure mode-specific settings
4. Verify the preview shows correct progress percentages

### 6. Test Your Challenge

1. Click **Save**
2. Use the **Test Challenge** feature to verify:
   - LLM includes correct metadata fields
   - Progress calculations are accurate
   - Completion logic works correctly

### 7. Activate Challenge

Toggle **Active** to make the challenge available to learners.

---

## Configuration Examples

### Example 1: Python Fundamentals (Questions Mode)

```json
{
  "mode": "questions",
  "total_questions": 5
}
```

**System Prompt**:
```
You are a Python instructor teaching fundamental programming concepts.

Ask 5 questions covering:
1. Variables and data types
2. Conditional statements
3. Loops
4. Functions
5. Lists and dictionaries

Provide clear explanations and encourage learners with positive feedback.
```

**XP Reward**: 150 (30 points per question)

---

### Example 2: Machine Learning Journey (Phases Mode)

```json
{
  "mode": "phases",
  "phases": [
    {
      "number": 1,
      "name": "Foundation",
      "description": "Understand core ML concepts"
    },
    {
      "number": 2,
      "name": "Application",
      "description": "Apply ML to real problems"
    },
    {
      "number": 3,
      "name": "Evaluation",
      "description": "Assess model performance"
    }
  ]
}
```

**XP Reward**: 150 (50 points per phase)

---

### Example 3: Coding Skills (Milestones Mode)

```json
{
  "mode": "milestones",
  "milestones": [
    {"id": "read_code", "name": "Read and Understand Code", "points": 30},
    {"id": "write_function", "name": "Write a Function", "points": 40},
    {"id": "debug_code", "name": "Debug Code", "points": 30},
    {"id": "optimize_code", "name": "Optimize Code", "points": 50}
  ]
}
```

**XP Reward**: 150 (matches total milestone points)

---

### Example 4: AI Concepts Discussion (Triggers Mode)

```json
{
  "mode": "triggers",
  "triggers": [
    "explain_neural_networks",
    "discuss_training_data",
    "analyze_bias",
    "evaluate_applications"
  ]
}
```

**XP Reward**: 150 (~38 points per trigger)

---

## Troubleshooting

### Progress tracking not showing in Test Challenge

**Issue**: Metadata doesn't include progress fields

**Solutions**:
1. Ensure progress tracking is toggled **On**
2. Save the challenge after configuring
3. Verify Challenge Type is set to **Simple** (not Advanced)

### Milestone points don't match XP reward

**Issue**: Red warning showing point mismatch

**Solutions**:
1. Adjust individual milestone points to sum to XP reward
2. Or adjust XP reward to match milestone points total
3. The editor shows current total vs. expected

### LLM not following progress tracking

**Issue**: LLM responses don't include correct metadata

**Solutions**:
1. Check system prompt is not conflicting with instructions
2. Use Test Challenge to see actual LLM response
3. Try a more capable model (Claude Sonnet or GPT-4)
4. Ensure prompt isn't too long (metadata instructions added at end)

### Can't add progress tracking to Advanced challenge

**Issue**: Progress Tracking editor is grayed out

**Solution**: Progress tracking is only available for Simple challenges. Advanced challenges use step-based progression instead.

---

## Best Practices Summary

### ✅ DO

- Choose the mode that best fits your learning objectives
- Test your configuration before activating
- Provide clear, encouraging feedback in your system prompt
- Use descriptive names for phases, milestones, and triggers
- Balance XP points across all progress elements

### ❌ DON'T

- Mix multiple progress modes in one challenge
- Create too many or too few progress elements (aim for 3-6)
- Make progress elements too granular or too broad
- Forget to test with the Test Challenge feature
- Activate without verifying progress tracking works correctly

---

## Related Documentation

- [Progress Tracking System](./PROGRESS_TRACKING.md) - Technical documentation
- [Variable Substitution](./VARIABLES.md) - Using custom variables in prompts
- [Challenge Types](./CHALLENGE_TYPES.md) - Simple vs. Advanced challenges

---

## Support

For issues or questions:
1. Use Test Challenge to debug metadata issues
2. Check backend logs for validation errors
3. Refer to technical documentation for details
4. Contact support with specific error messages
