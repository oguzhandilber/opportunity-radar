from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict, List
import json
import asyncio
from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)

# Event types
EVENT_APP_UPDATED = "app_updated"
EVENT_SCORE_CHANGED = "score_changed"
EVENT_NEW_MATCH = "new_match"
EVENT_VIRAL_ALERT = "viral_alert"
EVENT_TREND_FORECAST = "trend_forecast"


class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}
        self.app_connections: Dict[int, List[WebSocket]] = {}
        self.alert_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()
        self.active_connections.setdefault(client_id, []).append(websocket)
        logger.info(
            f"Client {client_id} connected. Total connections: {len(self.active_connections)}"
        )

    async def connect_to_app(self, websocket: WebSocket, app_id: int):
        await websocket.accept()
        self.app_connections.setdefault(app_id, []).append(websocket)
        logger.info(
            f"Client connected to app {app_id}. Total app connections: {len(self.app_connections)}"
        )

    async def connect_to_alerts(self, websocket: WebSocket):
        await websocket.accept()
        self.alert_connections.append(websocket)
        logger.info(
            f"Client connected to alerts. Total alert connections: {len(self.alert_connections)}"
        )

    def disconnect(self, websocket: WebSocket, client_id: str = None):
        # Remove from client connections
        if client_id and client_id in self.active_connections:
            if websocket in self.active_connections[client_id]:
                self.active_connections[client_id].remove(websocket)
            if not self.active_connections[client_id]:
                del self.active_connections[client_id]

        # Remove from app connections
        for app_id, connections in self.app_connections.items():
            if websocket in connections:
                connections.remove(websocket)
                if not connections:
                    del self.app_connections[app_id]
                break

        # Remove from alert connections
        if websocket in self.alert_connections:
            self.alert_connections.remove(websocket)

        logger.info("Client disconnected")

    async def broadcast_to_client(self, client_id: str, message: dict):
        """Send message to all connections for a specific client"""
        formatted_message = {
            "type": message.get("type"),
            "payload": message.get("payload", {}),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        disconnected_websockets = []
        for connection in self.active_connections.get(client_id, []):
            try:
                await connection.send_json(formatted_message)
            except Exception as e:
                logger.error(f"Error sending to client {client_id}: {e}")
                disconnected_websockets.append(connection)

        # Clean up dead connections
        for ws in disconnected_websockets:
            self.disconnect(ws, client_id)

    async def broadcast_to_app(self, app_id: int, message: dict):
        """Send message to all connections monitoring a specific app"""
        formatted_message = {
            "type": message.get("type"),
            "payload": message.get("payload", {}),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        disconnected_websockets = []
        for connection in self.app_connections.get(app_id, []):
            try:
                await connection.send_json(formatted_message)
            except Exception as e:
                logger.error(f"Error sending to app {app_id}: {e}")
                disconnected_websockets.append(connection)

        # Clean up dead connections
        for ws in disconnected_websockets:
            self.disconnect(ws)

    async def broadcast_alert(self, message: dict):
        """Send alert to all connected alert clients"""
        formatted_message = {
            "type": message.get("type"),
            "payload": message.get("payload", {}),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        disconnected_websockets = []
        for connection in self.alert_connections:
            try:
                await connection.send_json(formatted_message)
            except Exception as e:
                logger.error(f"Error sending alert: {e}")
                disconnected_websockets.append(connection)

        # Clean up dead connections
        for ws in disconnected_websockets:
            self.disconnect(ws)

    async def broadcast_to_all(self, message: dict):
        """Send message to all connected clients"""
        await self.broadcast_alert(message)

        for client_id in self.active_connections:
            await self.broadcast_to_client(client_id, message)

        for app_id in self.app_connections:
            await self.broadcast_to_app(app_id, message)


# Global connection manager instance
manager = ConnectionManager()


# Event broadcasting functions
async def notify_app_updated(app_id: int, app_data: dict):
    """Notify clients that an app has been updated"""
    message = {
        "type": EVENT_APP_UPDATED,
        "payload": {"app_id": app_id, "app_data": app_data},
    }
    await manager.broadcast_to_app(app_id, message)


async def notify_score_changed(
    app_id: int, new_score: float, previous_score: float = None
):
    """Notify clients that an app's score has changed"""
    message = {
        "type": EVENT_SCORE_CHANGED,
        "payload": {
            "app_id": app_id,
            "new_score": new_score,
            "previous_score": previous_score,
        },
    }
    await manager.broadcast_to_app(app_id, message)


async def notify_new_match(match_data: dict):
    """Notify clients about a new opportunity match"""
    message = {"type": EVENT_NEW_MATCH, "payload": match_data}
    await manager.broadcast_alert(message)


async def notify_viral_alert(alert_data: dict):
    """Notify clients about a viral trend alert"""
    message = {"type": EVENT_VIRAL_ALERT, "payload": alert_data}
    await manager.broadcast_alert(message)


async def notify_trend_forecast(forecast_data: dict):
    """Notify clients about trend forecast updates"""
    message = {"type": EVENT_TREND_FORECAST, "payload": forecast_data}
    await manager.broadcast_alert(message)
