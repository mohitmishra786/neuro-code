"""
NeuroCode WebSocket Routes.

Real-time updates via WebSocket.
Requires Python 3.11+.
"""

import asyncio
import json
from typing import Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from pydantic import BaseModel

from utils.logger import get_logger

router = APIRouter()
logger = get_logger("api.websocket")


class WebSocketManager:
    """
    Manages WebSocket connections for real-time updates.

    Handles connection lifecycle and message broadcasting.
    """

    def __init__(self) -> None:
        """Initialize the WebSocket manager."""
        self._connections: set[WebSocket] = set()
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket) -> None:
        """
        Accept and register a new WebSocket connection.

        Args:
            websocket: The WebSocket connection to register
        """
        await websocket.accept()
        async with self._lock:
            self._connections.add(websocket)
        logger.info("websocket_connected", total_connections=len(self._connections))

    async def disconnect(self, websocket: WebSocket) -> None:
        """
        Unregister a WebSocket connection.

        Args:
            websocket: The WebSocket connection to unregister
        """
        async with self._lock:
            self._connections.discard(websocket)
        logger.info("websocket_disconnected", total_connections=len(self._connections))

    async def broadcast(self, message: dict[str, Any]) -> None:
        """
        Broadcast a message to all connected clients.

        Args:
            message: The message to broadcast
        """
        if not self._connections:
            return

        message_json = json.dumps(message)
        disconnected: set[WebSocket] = set()

        async with self._lock:
            for connection in self._connections:
                try:
                    await connection.send_text(message_json)
                except Exception as e:
                    logger.warning("broadcast_failed", error=str(e))
                    disconnected.add(connection)

            # Clean up disconnected clients
            self._connections -= disconnected

    async def send_to(self, websocket: WebSocket, message: dict[str, Any]) -> None:
        """
        Send a message to a specific client.

        Args:
            websocket: Target WebSocket connection
            message: The message to send
        """
        try:
            await websocket.send_text(json.dumps(message))
        except Exception as e:
            logger.warning("send_failed", error=str(e))

    @property
    def connection_count(self) -> int:
        """Get the number of active connections."""
        return len(self._connections)


# Global WebSocket manager instance
manager = WebSocketManager()


def get_manager() -> WebSocketManager:
    """Get the global WebSocket manager."""
    return manager


class FileChangeEvent(BaseModel):
    """Event for file changes."""

    type: str = "file_changed"
    path: str
    change_type: str  # created, modified, deleted


class GraphUpdateEvent(BaseModel):
    """Event for graph updates."""

    type: str = "graph_updated"
    added_count: int = 0
    modified_count: int = 0
    removed_count: int = 0
    affected_modules: list[str] = []


class HeartbeatEvent(BaseModel):
    """Heartbeat event to keep connection alive."""

    type: str = "heartbeat"
    timestamp: float


@router.websocket("")
async def websocket_endpoint(websocket: WebSocket) -> None:
    """
    Main WebSocket endpoint for real-time updates.

    Clients receive:
    - File change notifications
    - Graph update notifications
    - Heartbeat messages (every 30s)
    """
    await manager.connect(websocket)

    # Send initial connection confirmation
    await manager.send_to(websocket, {
        "type": "connected",
        "message": "Connected to NeuroCode WebSocket",
    })

    try:
        while True:
            # Wait for client messages (ping/pong, or custom commands)
            try:
                data = await asyncio.wait_for(
                    websocket.receive_text(),
                    timeout=30.0,  # 30 second timeout
                )

                # Handle client messages
                try:
                    message = json.loads(data)
                    await handle_client_message(websocket, message)
                except json.JSONDecodeError:
                    await manager.send_to(websocket, {
                        "type": "error",
                        "message": "Invalid JSON",
                    })

            except asyncio.TimeoutError:
                # Send heartbeat on timeout
                import time
                await manager.send_to(websocket, {
                    "type": "heartbeat",
                    "timestamp": time.time(),
                })

    except WebSocketDisconnect:
        await manager.disconnect(websocket)
    except Exception as e:
        logger.error("websocket_error", error=str(e))
        await manager.disconnect(websocket)


async def handle_client_message(websocket: WebSocket, message: dict[str, Any]) -> None:
    """
    Handle incoming client messages.

    Supported message types:
    - ping: Respond with pong
    - subscribe: Subscribe to specific events
    - unsubscribe: Unsubscribe from events
    """
    msg_type = message.get("type", "")

    if msg_type == "ping":
        await manager.send_to(websocket, {"type": "pong"})

    elif msg_type == "subscribe":
        # Handle subscription requests (future enhancement)
        topics = message.get("topics", [])
        await manager.send_to(websocket, {
            "type": "subscribed",
            "topics": topics,
        })

    elif msg_type == "unsubscribe":
        topics = message.get("topics", [])
        await manager.send_to(websocket, {
            "type": "unsubscribed",
            "topics": topics,
        })

    else:
        await manager.send_to(websocket, {
            "type": "error",
            "message": f"Unknown message type: {msg_type}",
        })


async def broadcast_file_change(path: str, change_type: str) -> None:
    """
    Broadcast a file change event to all clients.

    Called by the file watcher when files change.

    Args:
        path: Path to the changed file
        change_type: Type of change (created, modified, deleted)
    """
    await manager.broadcast({
        "type": "file_changed",
        "path": path,
        "change_type": change_type,
    })


async def broadcast_graph_update(
    added: int = 0,
    modified: int = 0,
    removed: int = 0,
    affected_modules: list[str] | None = None,
) -> None:
    """
    Broadcast a graph update event to all clients.

    Called after the graph has been updated.

    Args:
        added: Number of nodes added
        modified: Number of nodes modified
        removed: Number of nodes removed
        affected_modules: List of affected module paths
    """
    await manager.broadcast({
        "type": "graph_updated",
        "added_count": added,
        "modified_count": modified,
        "removed_count": removed,
        "affected_modules": affected_modules or [],
    })
