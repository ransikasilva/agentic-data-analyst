"""
Coder agent node.

This node takes a specific task from the plan and generates executable
Python code to accomplish it.
"""

from typing import Dict, Any
from loguru import logger
import pandas as pd

from agent.state import AgentState
from models.openai_client import get_completion


async def coder_node(state: AgentState) -> Dict[str, Any]:
    """
    Coder node: Generates Python code for the current task in the plan.

    This node:
    1. Gets the current task from the plan
    2. Considers previous errors if retrying
    3. Prompts GPT-4o to write Python code
    4. Returns the generated code

    Args:
        state: Current agent state with plan, current_step, and optional error info

    Returns:
        State updates with generated_code and updated code_history
    """
    plan = state["plan"]
    current_step = state["current_step"]
    dataset_path = state["dataset_path"]
    session_id = state["session_id"]
    execution_error = state.get("execution_error")
    code_history = state.get("code_history", [])

    # Validate current step
    if current_step >= len(plan):
        logger.error(f"[Coder] Invalid step index {current_step} for plan of length {len(plan)}")
        return {
            "execution_error": f"Invalid step: {current_step} exceeds plan length {len(plan)}",
            "messages": [{
                "role": "system",
                "content": "Coder failed: Invalid step index"
            }]
        }

    current_task = plan[current_step]
    logger.info(f"[Coder] Session {session_id}, Step {current_step + 1}/{len(plan)}: {current_task}")

    # Determine if this is a retry
    is_retry = execution_error is not None
    previous_code = code_history[-1] if code_history else None

    # Build system prompt
    system_prompt = """You are an expert Python data analyst code generator.

Your job is to write EXECUTABLE Python code that accomplishes the given task.

CRITICAL RULES:
1. Use the DATASET_PATH variable (already defined) to load the data
2. Save all charts to the current directory with filenames: chart_1.png, chart_2.png, etc.
3. Print all final results to stdout
4. Use pandas, numpy, matplotlib, and plotly as needed
5. Return ONLY the Python code, no markdown fences, no explanations
6. DO NOT include ```python or ``` in your response
7. The code will run in a sandboxed environment with limited execution time
8. Assume the dataset is a CSV file unless told otherwise

Available libraries: pandas, numpy, matplotlib, plotly, seaborn

Example task: "Group by Month and calculate total Revenue"
Example code:
import pandas as pd
df = pd.read_csv(DATASET_PATH)
monthly = df.groupby('Month')['Revenue'].sum()
print("Monthly Revenue:")
print(monthly)
"""

    # Get dataset schema to provide column information
    dataset_path = state["dataset_path"]
    try:
        df = pd.read_csv(dataset_path)
        columns_info = f"Dataset columns: {list(df.columns)}\nDataset dtypes: {df.dtypes.to_dict()}"
        logger.debug(f"[Coder] {columns_info}")
    except Exception as e:
        logger.warning(f"[Coder] Could not read dataset schema: {e}")
        columns_info = "Note: Could not read dataset columns, check file path"

    # Get previous step's output for context
    previous_result = state.get("execution_result", "")
    context_info = ""
    if previous_result and current_step > 0:
        context_info = f"\n\nPREVIOUS STEP OUTPUT (use this data if needed):\n{previous_result}\n"

    # Build user prompt
    if is_retry:
        user_prompt = f"""Task: {current_task}

{columns_info}{context_info}

PREVIOUS CODE (which failed):
{previous_code}

ERROR RECEIVED:
{execution_error}

Please write CORRECTED code that fixes this error. Use the EXACT column names from the dataset. Return only the Python code, no markdown."""
    else:
        user_prompt = f"""Task: {current_task}

{columns_info}{context_info}

Write Python code to accomplish this task. Use the EXACT column names from the dataset.
IMPORTANT: If the previous step filtered or processed data, use those results instead of starting from scratch.
Return only the Python code, no markdown."""

    # Call OpenAI API
    try:
        code = await get_completion(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            model="gpt-4o",
            temperature=0.1,  # Low temperature for code generation
            max_tokens=2000
        )

        # Clean up code (remove markdown fences if present despite instructions)
        code = _clean_code(code)

        logger.debug(f"[Coder] Generated code:\n{code}")

    except Exception as e:
        logger.error(f"[Coder] OpenAI API call failed: {e}")
        return {
            "execution_error": f"Code generation failed: {str(e)}",
            "messages": [{
                "role": "system",
                "content": f"Coder failed: OpenAI API error - {str(e)}"
            }]
        }

    # Update code history
    updated_history = code_history + [code]

    logger.info(f"[Coder] Successfully generated code ({len(code)} chars)")

    return {
        "generated_code": code,
        "code_history": updated_history,
        "execution_error": None,  # Clear previous error
        "messages": [{
            "role": "system",
            "content": f"Coder generated code for step {current_step + 1}: {current_task[:100]}..."
        }]
    }


def _clean_code(code: str) -> str:
    """
    Clean generated code by removing markdown fences and extra whitespace.

    Args:
        code: Raw code from LLM

    Returns:
        Cleaned code string
    """
    code = code.strip()

    # Remove markdown code fences
    if code.startswith("```python"):
        code = code[len("```python"):].strip()
    elif code.startswith("```"):
        code = code[3:].strip()

    if code.endswith("```"):
        code = code[:-3].strip()

    return code
