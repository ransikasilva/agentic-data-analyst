"""
FastAPI application entry point for the Autonomous Data Analyst Agent.

This module initializes the FastAPI app, configures CORS, sets up logging,
and registers all API routes and WebSocket endpoints.
"""

import os
import sys
from pathlib import Path
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logger.remove()  # Remove default handler
logger.add(
    sys.stdout,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    level="INFO"
)
logger.add(
    "logs/app.log",
    rotation="100 MB",
    retention="10 days",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
    level="DEBUG"
)

# Create logs directory
Path("logs").mkdir(exist_ok=True)

# Import routes and websocket handler
from api.routes import router
from api.websocket import websocket_endpoint


# Initialize FastAPI app
app = FastAPI(
    title="Autonomous Data Analyst API",
    description="Production-grade multi-agent AI system for autonomous data analysis",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS
cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

logger.info(f"[App] CORS enabled for origins: {cors_origins}")

# Register REST API routes
app.include_router(router)

logger.info("[App] REST API routes registered")


# Register WebSocket endpoint
@app.websocket("/ws/{session_id}")
async def websocket_route(websocket: WebSocket, session_id: str):
    """WebSocket endpoint for real-time agent streaming."""
    await websocket_endpoint(websocket, session_id)


# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize application on startup."""
    logger.info("=" * 60)
    logger.info("[App] Starting Autonomous Data Analyst API")
    logger.info("=" * 60)

    # Validate required environment variables
    required_vars = ["OPENAI_API_KEY"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]

    if missing_vars:
        logger.error(f"[App] Missing required environment variables: {missing_vars}")
        logger.error("[App] Please set them in your .env file")
        sys.exit(1)

    # Create necessary directories
    Path("uploads").mkdir(exist_ok=True)
    Path("output").mkdir(exist_ok=True)

    logger.info("[App] Environment validated")
    logger.info(f"[App] SQLite DB: {os.getenv('SQLITE_DB_PATH', './sessions.db')}")
    logger.info(f"[App] Max execution time: {os.getenv('MAX_EXECUTION_SECONDS', '30')}s")
    logger.info(f"[App] Max retry attempts: {os.getenv('MAX_RETRY_ATTEMPTS', '3')}")

    # Initialize agent graph (lazy loaded but log readiness)
    logger.info("[App] Agent graph ready (lazy initialization)")

    logger.info("[App] Startup complete")
    logger.info("=" * 60)


# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on application shutdown."""
    logger.info("[App] Shutting down Autonomous Data Analyst API")
    logger.info("[App] Cleanup complete")


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "service": "Autonomous Data Analyst API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
        "health": "/api/health",
        "endpoints": {
            "upload": "POST /api/upload",
            "analyze": "POST /api/analyze",
            "session": "GET /api/session/{session_id}",
            "websocket": "WS /ws/{session_id}"
        }
    }


# Run with uvicorn if executed directly
if __name__ == "__main__":
    import uvicorn

    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))

    logger.info(f"[App] Starting server on {host}:{port}")

    uvicorn.run(
        "backend.main:app",
        host=host,
        port=port,
        reload=True,  # Enable auto-reload for development
        log_level="info"
    )
