"""
Summarizer agent node.

This node generates a final natural language summary of all findings
after the analysis is complete.
"""

from typing import Dict, Any
from loguru import logger

from agent.state import AgentState
from models.openai_client import get_completion


async def summarizer_node(state: AgentState) -> Dict[str, Any]:
    """
    Summarizer node: Generates final insights from all execution results.

    This node:
    1. Collects all execution results from the plan steps
    2. Notes which charts were generated
    3. Sends everything to GPT-4o for natural language summarization
    4. Returns markdown-formatted insights

    Args:
        state: Complete agent state with all execution results

    Returns:
        State updates with final insights
    """
    plan = state["plan"]
    code_history = state.get("code_history", [])
    user_goal = state["user_goal"]
    charts = state.get("charts", [])
    session_id = state["session_id"]

    logger.info(f"[Summarizer] Generating insights for session {session_id}")

    # Build execution summary
    execution_summary = _build_execution_summary(plan, code_history, state)

    # Build system prompt
    system_prompt = """You are a data analyst summarizing analysis results for a non-technical audience.

Your job is to create a clear, actionable summary of the findings.

Rules:
1. Write in markdown format
2. Start with a brief overview (2-3 sentences)
3. List 3-5 key findings as bullet points
4. If charts were generated, reference them (e.g., "See chart_1.png")
5. End with 2-3 actionable recommendations
6. Be specific and use numbers from the results
7. Avoid technical jargon
8. Keep it concise (200-400 words)

Structure:
## Summary
[Brief overview]

## Key Findings
- [Finding 1]
- [Finding 2]
- [Finding 3]

## Recommendations
- [Recommendation 1]
- [Recommendation 2]
"""

    # Build user prompt
    user_prompt = f"""Original Goal: {user_goal}

Analysis Results:
{execution_summary}

Number of charts generated: {len(charts)}

Please provide a clear summary of the findings and actionable recommendations."""

    # Call OpenAI API
    try:
        insights = await get_completion(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            model="gpt-4o",
            temperature=0.3,
            max_tokens=1500
        )

        logger.info(f"[Summarizer] Generated insights ({len(insights)} chars)")
        logger.debug(f"[Summarizer] Insights:\n{insights}")

    except Exception as e:
        logger.error(f"[Summarizer] OpenAI API call failed: {e}")
        # Provide fallback summary
        insights = _create_fallback_summary(plan, user_goal, len(charts))

    return {
        "insights": insights,
        "messages": [{
            "role": "system",
            "content": "Summarizer completed: Final insights generated"
        }]
    }


def _build_execution_summary(
    plan: list[str],
    code_history: list[str],
    state: AgentState
) -> str:
    """
    Build a summary of execution results for the summarizer.

    Args:
        plan: List of tasks
        code_history: List of code versions executed
        state: Full agent state

    Returns:
        Formatted string summarizing what was executed and found
    """
    lines = []

    for i, task in enumerate(plan):
        lines.append(f"\n**Step {i + 1}:** {task}")

        # Try to find execution result for this step
        # Note: This is simplified - in a real implementation, we'd track
        # results per step more explicitly
        if i < len(code_history):
            lines.append(f"  Code executed successfully")

    # Add any final execution results
    if state.get("execution_result"):
        lines.append(f"\n**Final Output:**\n{state['execution_result']}")

    return "\n".join(lines)


def _create_fallback_summary(plan: list[str], user_goal: str, chart_count: int) -> str:
    """
    Create a basic fallback summary when OpenAI API fails.

    Args:
        plan: List of tasks executed
        user_goal: Original user goal
        chart_count: Number of charts generated

    Returns:
        Basic markdown summary
    """
    summary = f"""## Analysis Summary

Goal: {user_goal}

### Tasks Completed
"""

    for i, task in enumerate(plan, 1):
        summary += f"{i}. {task}\n"

    summary += f"\n### Outputs\n- Generated {chart_count} visualization(s)\n"

    summary += "\n### Note\nFull insights could not be generated. Please review the execution results above.\n"

    return summary
