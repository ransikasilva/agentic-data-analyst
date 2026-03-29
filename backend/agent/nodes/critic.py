"""
Critic / Debugger agent node.

This node handles code execution errors by deciding whether to retry
with fixes or escalate after max retries.
"""

import os
from typing import Dict, Any
from loguru import logger

from agent.state import AgentState


async def critic_node(state: AgentState) -> Dict[str, Any]:
    """
    Critic node: Analyzes execution errors and decides on retry strategy.

    This node:
    1. Checks if there was an execution error
    2. Verifies retry count against MAX_RETRY_ATTEMPTS
    3. Either:
       - Allows retry by preserving error for coder to fix
       - Or escalates by writing error message to insights

    Args:
        state: Current agent state with execution_error and retry_count

    Returns:
        State updates with incremented retry_count and routing decision
    """
    execution_error = state.get("execution_error")
    retry_count = state.get("retry_count", 0)
    current_step = state["current_step"]
    plan = state["plan"]
    session_id = state["session_id"]

    max_retries = int(os.getenv("MAX_RETRY_ATTEMPTS", "3"))

    current_task = plan[current_step] if current_step < len(plan) else "Unknown"

    logger.info(
        f"[Critic] Session {session_id}, Step {current_step + 1}: "
        f"Analyzing error (retry {retry_count}/{max_retries})"
    )

    # If no error, this node shouldn't have been called
    if not execution_error:
        logger.warning("[Critic] Called with no execution error")
        return {
            "messages": [{
                "role": "system",
                "content": "Critic called but no error found"
            }]
        }

    # Clean and log the error
    cleaned_error = _clean_traceback(execution_error)
    logger.error(f"[Critic] Error to analyze:\n{cleaned_error}")

    # Add helpful hint for KeyError (usually wrong column names)
    error_hint = ""
    if "KeyError:" in cleaned_error:
        error_hint = "\n\nHINT: This is a KeyError - check if you're using the EXACT column names from the dataset. Column names are case-sensitive!"

    # Check if we can retry
    if retry_count < max_retries:
        new_retry_count = retry_count + 1
        logger.info(
            f"[Critic] Allowing retry {new_retry_count}/{max_retries} "
            f"for step {current_step + 1}"
        )

        return {
            "retry_count": new_retry_count,
            "execution_error": cleaned_error + error_hint,  # Preserve for coder with hint
            "messages": [{
                "role": "system",
                "content": f"Critic: Retry {new_retry_count}/{max_retries} - {cleaned_error[:200]}"
            }]
        }

    # Max retries exceeded - escalate
    logger.error(
        f"[Critic] Max retries ({max_retries}) exceeded for step {current_step + 1}. "
        f"Escalating error."
    )

    error_message = f"""# Analysis Failed

**Task:** {current_task}

**Error:** The system attempted to complete this task {max_retries} times but encountered persistent errors.

**Last Error:**
```
{cleaned_error}
```

**Recommendation:** This task could not be completed automatically. The error suggests:
{_get_error_suggestion(cleaned_error)}

Please review the task requirements and data format, then try again with a modified goal.
"""

    return {
        "insights": error_message,
        "execution_error": cleaned_error,
        "messages": [{
            "role": "system",
            "content": f"Critic: Max retries exceeded. Analysis failed at step {current_step + 1}"
        }]
    }


def _clean_traceback(error: str) -> str:
    """
    Clean and simplify error tracebacks for better readability.

    Args:
        error: Raw error string / traceback

    Returns:
        Cleaned error message
    """
    # Limit length
    max_length = 2000
    if len(error) > max_length:
        error = error[-max_length:]  # Keep last N chars (most relevant)

    # Remove temp file paths for cleaner display
    lines = error.split("\n")
    cleaned_lines = []

    for line in lines:
        # Skip lines with temp file references
        if "/tmp/" in line or "tmpfile" in line.lower():
            continue
        cleaned_lines.append(line)

    return "\n".join(cleaned_lines).strip()


def _get_error_suggestion(error: str) -> str:
    """
    Provide helpful suggestions based on error type.

    Args:
        error: Error message

    Returns:
        Human-readable suggestion
    """
    error_lower = error.lower()

    if "keyerror" in error_lower:
        return "- A column referenced in the code does not exist in the dataset. Check column names for typos or case sensitivity."

    if "filenotfounderror" in error_lower:
        return "- The dataset file could not be found. Ensure the file path is correct."

    if "typeerror" in error_lower:
        return "- There's a data type mismatch. Some columns may need type conversion before the operation."

    if "valueerror" in error_lower:
        return "- Invalid values encountered. Check for unexpected null values or incompatible data."

    if "importerror" in error_lower or "modulenotfounderror" in error_lower:
        return "- A required Python library is missing. Contact support to add this dependency."

    if "timeouterror" in error_lower:
        return "- The code took too long to execute. Try simplifying the analysis or working with a smaller dataset."

    if "memoryerror" in error_lower:
        return "- The dataset is too large for available memory. Try analyzing a subset of the data."

    # Generic suggestion
    return "- Review the error details above and adjust the analysis goal to avoid the problematic operation."
