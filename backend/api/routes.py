"""
REST API routes for the data analyst agent.

Provides endpoints for file upload, analysis execution, and session management.
"""

import os
import uuid
import asyncio
from pathlib import Path
from typing import Optional
from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from loguru import logger

from utils.file_parser import parse_file, FileParserError
from agent.graph import get_agent_graph
from api.websocket import manager as ws_manager


# Initialize router
router = APIRouter(prefix="/api")


# Request/Response models
class AnalyzeRequest(BaseModel):
    """Request body for analysis endpoint."""
    session_id: str
    goal: str


class AnalyzeResponse(BaseModel):
    """Response for analysis endpoint."""
    job_id: str
    status: str
    message: str


class UploadResponse(BaseModel):
    """Response for file upload endpoint."""
    session_id: str
    filename: str
    dataset_preview: dict
    message: str


class SessionResponse(BaseModel):
    """Response for session status endpoint."""
    session_id: str
    status: str
    plan: Optional[list]
    insights: Optional[str]
    charts: Optional[list]
    error: Optional[str]


# File upload directory
UPLOAD_DIR = Path("./uploads")
UPLOAD_DIR.mkdir(exist_ok=True)


@router.post("/upload", response_model=UploadResponse)
async def upload_file(file: UploadFile = File(...)) -> UploadResponse:
    """
    Upload a CSV or Excel file for analysis.

    Args:
        file: Uploaded file (CSV, XLSX, or XLS)

    Returns:
        UploadResponse with session_id and dataset preview

    Raises:
        HTTPException: If file validation or parsing fails
    """
    logger.info(f"[API] File upload request: {file.filename}")

    # Validate file extension
    allowed_extensions = {".csv", ".xlsx", ".xls"}
    file_ext = Path(file.filename).suffix.lower()

    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {file_ext}. "
            f"Allowed types: {', '.join(allowed_extensions)}"
        )

    # Generate session ID
    session_id = str(uuid.uuid4())

    # Save uploaded file
    file_path = UPLOAD_DIR / f"{session_id}_{file.filename}"

    try:
        contents = await file.read()
        with open(file_path, "wb") as f:
            f.write(contents)

        logger.info(f"[API] Saved file to {file_path}")

    except Exception as e:
        logger.error(f"[API] Failed to save uploaded file: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to save file: {str(e)}"
        )

    # Parse file and generate preview
    try:
        df, metadata = parse_file(str(file_path))

        logger.info(
            f"[API] Parsed file: {metadata['shape'][0]} rows, "
            f"{metadata['shape'][1]} columns"
        )

    except FileParserError as e:
        # Clean up file
        file_path.unlink(missing_ok=True)
        raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:
        # Clean up file
        file_path.unlink(missing_ok=True)
        logger.error(f"[API] File parsing failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to parse file: {str(e)}"
        )

    return UploadResponse(
        session_id=session_id,
        filename=file.filename,
        dataset_preview=metadata,
        message="File uploaded successfully"
    )


@router.post("/analyze", response_model=AnalyzeResponse)
async def start_analysis(request: AnalyzeRequest) -> AnalyzeResponse:
    """
    Start an analysis job for an uploaded dataset.

    This endpoint starts the agent graph execution in a background task.

    Args:
        request: AnalyzeRequest with session_id and goal

    Returns:
        AnalyzeResponse with job_id

    Raises:
        HTTPException: If session not found or analysis fails to start
    """
    session_id = request.session_id
    goal = request.goal

    logger.info(f"[API] Analysis request for session {session_id}")
    logger.debug(f"[API] Goal: {goal}")

    # Find the uploaded file
    upload_files = list(UPLOAD_DIR.glob(f"{session_id}_*"))

    if not upload_files:
        raise HTTPException(
            status_code=404,
            detail=f"No uploaded file found for session {session_id}"
        )

    dataset_path = str(upload_files[0].absolute())

    # Initialize agent state
    initial_state = {
        "dataset_path": dataset_path,
        "user_goal": goal,
        "session_id": session_id,
        "plan": [],
        "current_step": 0,
        "generated_code": "",
        "code_history": [],
        "execution_result": None,
        "execution_error": None,
        "retry_count": 0,
        "charts": [],
        "insights": "",
        "messages": []
    }

    # Start analysis in background task
    asyncio.create_task(_run_analysis(session_id, initial_state))

    return AnalyzeResponse(
        job_id=session_id,
        status="started",
        message="Analysis started successfully"
    )


async def _run_analysis(session_id: str, initial_state: dict):
    """
    Background task to run the agent graph.

    Args:
        session_id: Session identifier
        initial_state: Initial agent state
    """
    logger.info(f"[API] _run_analysis called for session {session_id}")
    logger.debug(f"[API] Initial state: {initial_state}")

    try:
        logger.info(f"[API] Starting agent graph for session {session_id}")

        # Send initial message
        await ws_manager.send_message(session_id, {
            "type": "analysis_started",
            "message": "Analysis started"
        })

        # Get compiled graph (async)
        graph = await get_agent_graph()

        # Run graph with async execution
        # Note: LangGraph nodes are async and use AsyncSqliteSaver
        config = {"configurable": {"thread_id": session_id}}

        async for event in graph.astream(initial_state, config):
            logger.info(f"[API] Graph event: {list(event.keys())}")

            # Stream events to WebSocket
            for node_name, node_output in event.items():
                logger.info(f"[API] Sending WS step for node: {node_name}")
                await ws_manager.send_agent_step(
                    session_id=session_id,
                    node=node_name,
                    status="running",
                    message=f"Executing {node_name}",
                    code=node_output.get("generated_code"),
                    result=node_output.get("execution_result")
                )
                logger.info(f"[API] WS step sent for: {node_name}")

        logger.info(f"[API] Analysis completed for session {session_id}")

        await ws_manager.send_message(session_id, {
            "type": "analysis_complete",
            "message": "Analysis completed successfully"
        })

    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        logger.error(f"[API] Analysis failed for session {session_id}: {e}")
        logger.error(f"[API] Full traceback:\n{error_trace}")

        await ws_manager.send_message(session_id, {
            "type": "analysis_error",
            "message": f"Analysis failed: {str(e)}"
        })


@router.get("/session/{session_id}", response_model=SessionResponse)
async def get_session(session_id: str) -> SessionResponse:
    """
    Get the current state of an analysis session.

    Args:
        session_id: Session identifier

    Returns:
        SessionResponse with current session state

    Raises:
        HTTPException: If session not found
    """
    logger.info(f"[API] Session status request: {session_id}")

    try:
        graph = await get_agent_graph()
        config = {"configurable": {"thread_id": session_id}}

        # Get current state from checkpointer
        state = await graph.aget_state(config)

        if not state or not state.values:
            raise HTTPException(
                status_code=404,
                detail=f"Session {session_id} not found"
            )

        values = state.values

        insights = values.get("insights")
        charts = values.get("charts", [])

        logger.info(f"[API] Session {session_id} - Insights: {len(insights) if insights else 0} chars, Charts: {len(charts)}")

        return SessionResponse(
            session_id=session_id,
            status="completed" if insights else "running",
            plan=values.get("plan"),
            insights=insights,
            charts=charts,
            error=values.get("execution_error")
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[API] Failed to get session state: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve session: {str(e)}"
        )


@router.get("/health")
async def health_check():
    """
    Health check endpoint.

    Returns:
        Simple status dict
    """
    return {
        "status": "healthy",
        "service": "autonomous-data-analyst",
        "version": "1.0.0"
    }
