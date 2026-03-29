"""
LangGraph state graph for the autonomous data analyst agent.

This module wires together all agent nodes into a state machine with
conditional routing, retry loops, and checkpointing.
"""

import os
from typing import Dict, Any, Literal
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from loguru import logger
import aiosqlite

from agent.state import AgentState
from agent.nodes.planner import planner_node
from agent.nodes.coder import coder_node
from agent.nodes.critic import critic_node
from agent.nodes.summarizer import summarizer_node
from agent.tools.executor import execute_code, get_output_files, read_output_file
import base64


# Node names as constants
NODE_PLANNER = "planner"
NODE_CODER = "coder"
NODE_EXECUTOR = "executor"
NODE_CRITIC = "critic"
NODE_SUMMARIZER = "summarizer"


async def executor_node(state: AgentState) -> Dict[str, Any]:
    """
    Executor node: Runs the generated code in a sandbox.

    This is a wrapper around the execute_code tool that integrates
    with the LangGraph state.

    Args:
        state: Current agent state with generated_code

    Returns:
        State updates with execution_result or execution_error
    """
    generated_code = state["generated_code"]
    dataset_path = state["dataset_path"]
    session_id = state["session_id"]
    current_step = state["current_step"]

    logger.info(f"[Executor] Running code for session {session_id}, step {current_step + 1}")

    # Execute the code
    stdout, stderr, exit_code = execute_code(
        code=generated_code,
        dataset_path=dataset_path,
        session_id=session_id
    )

    if exit_code == 0:
        logger.info(f"[Executor] Code executed successfully")
        logger.debug(f"[Executor] Output:\n{stdout}")

        # Collect any NEW chart files (only charts created in this step)
        existing_chart_count = len(state.get("charts", []))
        chart_files = get_output_files(session_id)
        charts_base64 = []

        for chart_path in chart_files:
            if chart_path.endswith(('.png', '.jpg', '.jpeg')):
                try:
                    chart_bytes = read_output_file(chart_path)
                    chart_b64 = base64.b64encode(chart_bytes).decode('utf-8')

                    # Only add if this chart is new (not already in state)
                    existing_charts = state.get("charts", [])
                    if chart_b64 not in existing_charts:
                        charts_base64.append(chart_b64)
                        logger.info(f"[Executor] Collected new chart: {chart_path}")
                    else:
                        logger.debug(f"[Executor] Skipping duplicate chart: {chart_path}")
                except Exception as e:
                    logger.warning(f"[Executor] Failed to read chart {chart_path}: {e}")

        return {
            "execution_result": stdout,
            "execution_error": None,
            "charts": state.get("charts", []) + charts_base64,
            "messages": [{
                "role": "system",
                "content": f"Executor: Code ran successfully (step {current_step + 1})"
            }]
        }
    else:
        logger.error(f"[Executor] Code execution failed with exit code {exit_code}")
        logger.error(f"[Executor] Error:\n{stderr}")

        return {
            "execution_result": None,
            "execution_error": stderr,
            "messages": [{
                "role": "system",
                "content": f"Executor: Code failed (step {current_step + 1}) - {stderr[:100]}"
            }]
        }


def should_retry(state: AgentState) -> Literal["critic", "next_step"]:
    """
    Conditional router: Decides if execution failed and needs retry.

    Args:
        state: Current agent state

    Returns:
        "critic" if error occurred (triggers retry loop)
        "next_step" if successful (continues to next step)
    """
    execution_error = state.get("execution_error")

    if execution_error:
        logger.debug("[Router] Execution failed, routing to critic")
        return "critic"
    else:
        logger.debug("[Router] Execution successful, routing to next step")
        return "next_step"


def next_step_router(state: AgentState) -> Literal["coder", "summarizer"]:
    """
    Conditional router: Decides if more steps remain or analysis is complete.

    Args:
        state: Current agent state

    Returns:
        "coder" if more steps remain
        "summarizer" if all steps complete
    """
    plan = state["plan"]
    current_step = state["current_step"]

    # Check if current step is within plan bounds
    if current_step < len(plan):
        logger.debug(f"[Router] Executing step {current_step + 1}/{len(plan)}")
        return "coder"
    else:
        logger.debug("[Router] All steps complete, routing to summarizer")
        return "summarizer"


async def advance_step_node(state: AgentState) -> Dict[str, Any]:
    """
    Helper node: Advances to the next step and resets retry count.

    Args:
        state: Current agent state

    Returns:
        State updates with incremented current_step and reset retry_count
    """
    current_step = state["current_step"]
    new_step = current_step + 1

    logger.info(f"[AdvanceStep] Moving from step {current_step + 1} to {new_step + 1}")

    return {
        "current_step": new_step,
        "retry_count": 0,  # Reset retry counter for new step
        "execution_error": None,  # Clear previous errors
    }


async def create_agent_graph() -> StateGraph:
    """
    Create and compile the LangGraph state graph.

    Graph flow:
    START → planner → coder → executor → [success?]
                                            ├─ yes → advance_step → [more steps?]
                                            │                         ├─ yes → coder (loop)
                                            │                         └─ no → summarizer → END
                                            └─ no → critic → [can retry?]
                                                              ├─ yes → coder (retry)
                                                              └─ no → END (error)

    Returns:
        Compiled StateGraph with AsyncSQLite checkpointing
    """
    # Initialize graph
    graph = StateGraph(AgentState)

    # Add all nodes
    graph.add_node(NODE_PLANNER, planner_node)
    graph.add_node(NODE_CODER, coder_node)
    graph.add_node(NODE_EXECUTOR, executor_node)
    graph.add_node(NODE_CRITIC, critic_node)
    graph.add_node(NODE_SUMMARIZER, summarizer_node)
    graph.add_node("advance_step", advance_step_node)

    # Set entry point
    graph.set_entry_point(NODE_PLANNER)

    # Add edges
    graph.add_edge(NODE_PLANNER, NODE_CODER)
    graph.add_edge(NODE_CODER, NODE_EXECUTOR)

    # Conditional: executor → critic or next_step
    graph.add_conditional_edges(
        NODE_EXECUTOR,
        should_retry,
        {
            "critic": NODE_CRITIC,
            "next_step": "advance_step"
        }
    )

    # Conditional: advance_step → coder or summarizer
    graph.add_conditional_edges(
        "advance_step",
        next_step_router,
        {
            "coder": NODE_CODER,
            "summarizer": NODE_SUMMARIZER
        }
    )

    # Conditional: critic → coder (retry) or END (max retries)
    def critic_router(state: AgentState) -> Literal["coder", "end"]:
        """Route from critic based on retry count."""
        max_retries = int(os.getenv("MAX_RETRY_ATTEMPTS", "3"))
        retry_count = state.get("retry_count", 0)

        if retry_count < max_retries:
            return "coder"  # Retry
        else:
            return "end"  # Give up

    graph.add_conditional_edges(
        NODE_CRITIC,
        critic_router,
        {
            "coder": NODE_CODER,
            "end": END
        }
    )

    # Summarizer ends the flow
    graph.add_edge(NODE_SUMMARIZER, END)

    # Initialize AsyncSQLite checkpointer for session persistence
    db_path = os.getenv("SQLITE_DB_PATH", "./sessions.db")
    logger.info(f"[Graph] Initializing AsyncSQLite checkpointer at {db_path}")

    # Create async connection and checkpointer
    # We need to create the connection and pass it to AsyncSqliteSaver
    conn = await aiosqlite.connect(db_path)
    checkpointer = AsyncSqliteSaver(conn)

    # Compile graph with async checkpointing
    compiled_graph = graph.compile(checkpointer=checkpointer)

    logger.info("[Graph] Agent graph compiled successfully")

    return compiled_graph


# Global graph instance
agent_graph = None


async def get_agent_graph() -> StateGraph:
    """
    Get or create the global agent graph instance.

    Returns:
        Compiled agent graph
    """
    global agent_graph

    if agent_graph is None:
        agent_graph = await create_agent_graph()

    return agent_graph
