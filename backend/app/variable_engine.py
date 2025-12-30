"""
Variable Substitution Engine

Handles replacement of {{variable}} placeholders in system prompts for Simple challenges.
Supports basic, extended, and custom variables.
"""

import re
import json
from typing import Dict, List, Any, Optional
from .models import Challenge


# Reserved variable names that cannot be overridden by custom variables
RESERVED_VARIABLES = {
    # Basic variables
    "title",
    "description",
    "difficulty",
    "xp_reward",
    "passing_score",
    # Extended variables
    "estimated_time",
    "tags",
    "help_resources",
}


def get_available_variables(challenge: Challenge) -> Dict[str, Any]:
    """
    Get all available variables for a challenge.

    Returns:
        Dictionary of variable_name -> value including basic, extended, and custom variables
    """
    variables = {
        # Basic variables
        "title": challenge.title,
        "description": challenge.description,
        "difficulty": challenge.difficulty,
        "xp_reward": str(challenge.xp_reward),
        "passing_score": str(challenge.passing_score),

        # Extended variables
        "estimated_time": str(challenge.estimated_time_minutes),
        "tags": ", ".join(challenge.tags) if challenge.tags else "",
        "help_resources": json.dumps(challenge.help_resources) if challenge.help_resources else "[]",
    }

    # Add custom variables (if any)
    if challenge.custom_variables:
        for key, value in challenge.custom_variables.items():
            # Don't allow custom variables to override built-in ones
            if key not in RESERVED_VARIABLES:
                variables[key] = str(value)

    return variables


def extract_variables(template: str) -> List[str]:
    """
    Extract all {{variable}} placeholders from template using regex.

    Args:
        template: System prompt template string

    Returns:
        List of variable names found in the template
    """
    pattern = r"\{\{(\w+)\}\}"
    matches = re.findall(pattern, template)
    return list(set(matches))  # Remove duplicates


def validate_variables(template: str, challenge: Challenge) -> Dict[str, List[str]]:
    """
    Validate that all variables in template can be resolved.

    Args:
        template: System prompt template string
        challenge: Challenge model instance

    Returns:
        Dictionary with "valid" and "invalid" lists of variable names
    """
    template_vars = extract_variables(template)
    available_vars = get_available_variables(challenge)

    valid = []
    invalid = []

    for var in template_vars:
        if var in available_vars:
            valid.append(var)
        else:
            invalid.append(var)

    return {"valid": valid, "invalid": invalid}


def substitute_variables(
    template: str,
    challenge: Challenge,
    custom_vars: Optional[Dict[str, Any]] = None
) -> str:
    """
    Replace all {{variable}} placeholders in template with actual values.

    Args:
        template: System prompt template string
        challenge: Challenge model instance
        custom_vars: Optional override for custom_variables (useful for preview)

    Returns:
        Template with all variables substituted

    Raises:
        ValueError: If any variables cannot be resolved
    """
    # Get available variables
    variables = get_available_variables(challenge)

    # Override with provided custom_vars if specified
    if custom_vars:
        for key, value in custom_vars.items():
            if key not in RESERVED_VARIABLES:
                variables[key] = str(value)

    # Validate all variables can be resolved
    validation = validate_variables(template, challenge)
    if validation["invalid"]:
        raise ValueError(
            f"Cannot resolve variables: {', '.join(validation['invalid'])}. "
            f"Available variables: {', '.join(sorted(variables.keys()))}"
        )

    # Perform substitution
    result = template
    for var_name, var_value in variables.items():
        placeholder = f"{{{{{var_name}}}}}"
        result = result.replace(placeholder, var_value)

    return result


def validate_variable_name(name: str) -> tuple[bool, Optional[str]]:
    """
    Validate a custom variable name.

    Args:
        name: Variable name to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    # Must be alphanumeric + underscores
    if not re.match(r"^\w+$", name):
        return False, "Variable name must contain only letters, numbers, and underscores"

    # Cannot start with a number
    if name[0].isdigit():
        return False, "Variable name cannot start with a number"

    # Cannot be a reserved name
    if name in RESERVED_VARIABLES:
        return False, f"'{name}' is a reserved variable name and cannot be used"

    # Must be reasonable length
    if len(name) > 50:
        return False, "Variable name is too long (max 50 characters)"

    return True, None
