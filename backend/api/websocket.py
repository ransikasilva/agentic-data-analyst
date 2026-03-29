"""
WebSocket handler for real-time agent streaming.

This module handles WebSocket connections and streams agent execution
updates to the frontend in real-time.
"""

import asyncio
import json
from datetime import datetime
from typing import Dict, Set
from fastapi import WebSocket, WebSocketDisconnect
from loguru import logger


# Global registry of active WebSocket connections
# Maps session_id -> set of WebSocket connections
_active_connections: Dict[str, Set[WebSocket]] = {}

# Message queues for each session
# Maps session_id -> asyncio.Queue
_message_queues: Dict[str, asyncio.Queue] = {}


class ConnectionManager:
    """Manages WebSocket connections for agent streaming."""

    @staticmethod
    async def connect(websocket: WebSocket, session_id: str):
        """
        Accept a new WebSocket connection and register it.

        Args:
            websocket: WebSocket connection to accept
            session_id: Session identifier
        """
        await websocket.accept()

        # Initialize session structures if needed
        if session_id not in _active_connections:
            _active_connections[session_id] = set()

        if session_id not in _message_queues:
            _message_queues[session_id] = asyncio.Queue()

        # Add connection
        _active_connections[session_id].add(websocket)

        logger.info(
            f"[WebSocket] New connection for session {session_id}. "
            f"Total connections: {len(_active_connections[session_id])}"
        )

    @staticmethod
    async def disconnect(websocket: WebSocket, session_id: str):
        """
        Remove a WebSocket connection.

        Args:
            websocket: WebSocket connection to remove
            session_id: Session identifier
        """
        if session_id in _active_connections:
            _active_connections[session_id].discard(websocket)

            # Clean up if no more connections
            if not _active_connections[session_id]:
                del _active_connections[session_id]
                if session_id in _message_queues:
                    del _message_queues[session_id]

        logger.info(
            f"[WebSocket] Connection closed for session {session_id}. "
            f"Remaining: {len(_active_connections.get(session_id, []))}"
        )

    @staticmethod
    async def send_message(session_id: str, message: dict):
        """
        Send a message to all connected clients for a session.

        Args:
            session_id: Session identifier
            message: Dictionary message to send (will be JSON serialized)
        """
        if session_id not in _active_connections:
            logger.debug(f"[WebSocket] No connections for session {session_id}")
            return

        # Add timestamp if not present
        if "timestamp" not in message:
            message["timestamp"] = datetime.utcnow().isoformat() + "Z"

        # Serialize message
        message_json = json.dumps(message)

        # Send to all connections
        connections = list(_active_connections[session_id])
        disconnected = []

        for websocket in connections:
            try:
                await websocket.send_text(message_json)
            except Exception as e:
                logger.error(f"[WebSocket] Send failed for session {session_id}: {type(e).__name__}: {e}")
                disconnected.append(websocket)

        # Clean up failed connections
        for ws in disconnected:
            await ConnectionManager.disconnect(ws, session_id)

    @staticmethod
    async def send_agent_step(
        session_id: str,
        node: str,
        status: str,
        message: str,
        code: str = None,
        result: str = None,
        retry_count: int = 0
    ):
        """
        Send an agent step update to connected clients.

        Args:
            session_id: Session identifier
            node: Node name (planner, coder, executor, critic, summarizer)
            status: Status (running, success, error)
            message: Human-readable message
            code: Generated code (if applicable)
            result: Execution result (if applicable)
            retry_count: Retry count (if applicable)
        """
        step_message = {
            "type": "agent_step",
            "node": node,
            "status": status,
            "data": {
                "message": message,
                "retry_count": retry_count
            }
        }

        # Add optional fields
        if code:
            step_message["data"]["code"] = code

        if result:
            step_message["data"]["result"] = result

        await ConnectionManager.send_message(session_id, step_message)

        logger.info(
            f"[WebSocket] Sent {node} step ({status}) to session {session_id}"
        )


manager = ConnectionManager()


async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """
    WebSocket endpoint handler for agent streaming.

    This is the main WebSocket route that handles connections and
    message streaming for a session.

    Args:
        websocket: WebSocket connection
        session_id: Session identifier from URL path
    """
    await manager.connect(websocket, session_id)

    try:
        # Send initial connection confirmation
        await manager.send_message(session_id, {
            "type": "connected",
            "session_id": session_id,
            "message": "WebSocket connected successfully"
        })

        # Keep connection alive and listen for client messages
        while True:
            try:
                # Receive messages from client (if any)
                # In this implementation, client messages are mostly for heartbeat
                data = await websocket.receive_text()

                # Parse client message
                try:
                    client_message = json.loads(data)

                    # Handle ping/heartbeat
                    if client_message.get("type") == "ping":
                        await manager.send_message(session_id, {
                            "type": "pong",
                            "timestamp": datetime.utcnow().isoformat() + "Z"
                        })

                except json.JSONDecodeError:
                    logger.warning(f"[WebSocket] Invalid JSON from client: {data}")

            except WebSocketDisconnect:
                logger.info(f"[WebSocket] Client disconnected: {session_id}")
                break

            except Exception as e:
                logger.error(f"[WebSocket] Error in receive loop: {e}")
                break

    except Exception as e:
        logger.error(f"[WebSocket] Connection error for {session_id}: {e}")

    finally:
        await manager.disconnect(websocket, session_id)


def queue_agent_message(session_id: str, message: dict):
    """
    Queue an agent message to be sent via WebSocket.

    This is called from the agent graph nodes (which run synchronously)
    to bridge to the async WebSocket.

    Args:
        session_id: Session identifier
        message: Message dictionary to send
    """
    if session_id in _message_queues:
        try:
            _message_queues[session_id].put_nowait(message)
        except asyncio.QueueFull:
            logger.warning(f"[WebSocket] Message queue full for session {session_id}")
    else:
        logger.debug(f"[WebSocket] No queue for session {session_id}, will create on connect")


async def process_queued_messages(session_id: str):
    """
    Background task to process queued messages for a session.

    This runs as a background task and drains the message queue,
    sending messages via WebSocket.

    Args:
        session_id: Session identifier
    """
    if session_id not in _message_queues:
        return

    queue = _message_queues[session_id]

    while session_id in _active_connections:
        try:
            # Wait for message with timeout
            message = await asyncio.wait_for(queue.get(), timeout=1.0)

            # Send message
            await manager.send_message(session_id, message)

        except asyncio.TimeoutError:
            # No messages, continue waiting
            continue

        except Exception as e:
            logger.error(f"[WebSocket] Error processing queued message: {e}")
            break

    logger.debug(f"[WebSocket] Stopped processing messages for {session_id}")
