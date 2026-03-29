"""
Planner agent node.

This node analyzes the dataset schema and user goal, then generates
a structured plan of executable sub-tasks for the analysis.
"""

import json
import pandas as pd
from typing import Dict, Any
from loguru import logger

from agent.state import AgentState
from utils.file_parser import get_dataset_schema_summary
from models.openai_client import get_completion


async def planner_node(state: AgentState) -> Dict[str, Any]:
    """
    Planner node: Analyzes dataset and generates execution plan.

    This node:
    1. Reads the dataset and extracts schema information
    2. Sends dataset schema + user goal to GPT-4o
    3. Requests a structured JSON plan of 3-6 executable sub-tasks
    4. Validates and parses the plan
    5. Updates state with the plan

    Args:
        state: Current agent state containing dataset_path and user_goal

    Returns:
        State updates containing the plan and initialized step counter
    """
    dataset_path = state["dataset_path"]
    user_goal = state["user_goal"]
    session_id = state["session_id"]

    logger.info(f"[Planner] Starting planning for session {session_id}")
    logger.debug(f"[Planner] User goal: {user_goal}")

    # Read dataset and generate schema summary
    try:
        df = pd.read_csv(dataset_path)  # Assuming CSV for now
        schema_summary = get_dataset_schema_summary(df)
        logger.debug(f"[Planner] Dataset schema:\n{schema_summary}")
    except Exception as e:
        logger.error(f"[Planner] Failed to read dataset: {e}")
        return {
            "plan": [],
            "current_step": 0,
            "execution_error": f"Failed to read dataset: {str(e)}",
            "messages": [{
                "role": "system",
                "content": f"Planner failed: Could not read dataset - {str(e)}"
            }]
        }

    # Build prompt for GPT-4o
    system_prompt = """You are a data analysis planning expert. Your job is to create a detailed,
executable plan for analyzing a dataset based on the user's goal.

Rules:
1. Return ONLY a JSON array of strings, nothing else
2. Each task must be specific and executable in Python
3. Tasks should be concrete (e.g., "Group by Month and sum Revenue") not vague (e.g., "analyze data")
4. Include 3-6 tasks total
5. If visualization is relevant, include specific chart types (bar chart, line plot, scatter, etc.)
6. Tasks should build on each other logically
7. The last task should typically be a summary or key finding

Example output format:
["Load the CSV and print shape and column names", "Check for missing values in all columns", "Group by Category and calculate mean Price", "Create a bar chart of average Price by Category saved as chart_1.png", "Find the top 3 categories by total sales"]
"""

    user_prompt = f"""Dataset Schema:
{schema_summary}

User Goal:
{user_goal}

Generate a detailed execution plan as a JSON array of task strings."""

    # Call OpenAI API
    try:
        response = await get_completion(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            model="gpt-4o",
            temperature=0.2,
            max_tokens=1000
        )

        logger.debug(f"[Planner] GPT-4o response: {response}")

    except Exception as e:
        logger.error(f"[Planner] OpenAI API call failed: {e}")
        return {
            "plan": [],
            "current_step": 0,
            "execution_error": f"Planning failed: {str(e)}",
            "messages": [{
                "role": "system",
                "content": f"Planner failed: OpenAI API error - {str(e)}"
            }]
        }

    # Parse JSON response
    plan = _parse_plan_response(response)

    if not plan:
        logger.error("[Planner] Failed to parse plan from GPT-4o response")
        return {
            "plan": [],
            "current_step": 0,
            "execution_error": "Planning failed: Could not parse plan from LLM response",
            "messages": [{
                "role": "system",
                "content": "Planner failed: Invalid plan format received"
            }]
        }

    logger.info(f"[Planner] Generated plan with {len(plan)} steps")
    for i, task in enumerate(plan, 1):
        logger.info(f"[Planner]   Step {i}: {task}")

    # Return state updates
    return {
        "plan": plan,
        "current_step": 0,
        "code_history": [],
        "retry_count": 0,
        "messages": [{
            "role": "system",
            "content": f"Planner created {len(plan)}-step plan: {json.dumps(plan)}"
        }]
    }


def _parse_plan_response(response: str) -> list[str]:
    """
    Parse the plan from GPT-4o response.

    Attempts to extract a JSON array from the response, handling cases where
    the model includes markdown formatting or extra text.

    Args:
        response: Raw text response from GPT-4o

    Returns:
        List of task strings, or empty list if parsing fails
    """
    # Try direct JSON parse first
    try:
        plan = json.loads(response)
        if isinstance(plan, list) and all(isinstance(task, str) for task in plan):
            return plan
    except json.JSONDecodeError:
        pass

    # Try extracting JSON from markdown code block
    if "```json" in response:
        try:
            json_start = response.index("```json") + 7
            json_end = response.index("```", json_start)
            json_str = response[json_start:json_end].strip()
            plan = json.loads(json_str)
            if isinstance(plan, list) and all(isinstance(task, str) for task in plan):
                return plan
        except (ValueError, json.JSONDecodeError):
            pass

    # Try extracting JSON array from anywhere in response
    try:
        start_idx = response.index("[")
        end_idx = response.rindex("]") + 1
        json_str = response[start_idx:end_idx]
        plan = json.loads(json_str)
        if isinstance(plan, list) and all(isinstance(task, str) for task in plan):
            return plan
    except (ValueError, json.JSONDecodeError):
        pass

    logger.error("[Planner] All parsing attempts failed")
    return []
