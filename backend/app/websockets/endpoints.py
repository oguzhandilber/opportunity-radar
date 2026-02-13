from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from app.websockets.dashboard import (
    manager,
    notify_app_updated,
    notify_score_changed,
    notify_new_match,
    notify_viral_alert,
    notify_trend_forecast,
    EVENT_APP_UPDATED,
    EVENT_SCORE_CHANGED,
    EVENT_NEW_MATCH,
    EVENT_VIRAL_ALERT,
    EVENT_TREND_FORECAST,
)
import logging
import json

logger = logging.getLogger(__name__)
websocket_router = APIRouter()


@websocket_router.websocket("/ws/dashboard/{client_id}")
async def websocket_dashboard(websocket: WebSocket, client_id: str):
    """WebSocket endpoint for dashboard subscriptions"""
    await manager.connect(websocket, client_id)

    try:
        while True:
            data = await websocket.receive_text()
            try:
                message = json.loads(data)

                # Handle client messages (e.g., subscription preferences)
                if message.get("type") == "subscribe":
                    payload = message.get("payload", {})
                    # Handle subscription logic here
                    logger.info(f"Client {client_id} subscribed to: {payload}")

                # Echo back for testing
                await websocket.send_json(
                    {
                        "type": "echo",
                        "payload": {"received": message},
                        "timestamp": "now",
                    }
                )

            except json.JSONDecodeError:
                await websocket.send_json(
                    {
                        "type": "error",
                        "payload": {"message": "Invalid JSON format"},
                        "timestamp": "now",
                    }
                )

    except WebSocketDisconnect:
        manager.disconnect(websocket, client_id)
        logger.info(f"Client {client_id} disconnected from dashboard")
    except Exception as e:
        logger.error(f"Error in dashboard WebSocket: {e}")
        manager.disconnect(websocket, client_id)


@websocket_router.websocket("/ws/app/{app_id}")
async def websocket_app(websocket: WebSocket, app_id: int):
    """WebSocket endpoint for real-time app updates"""
    await manager.connect_to_app(websocket, app_id)

    try:
        # Send initial app data if needed
        await websocket.send_json(
            {
                "type": "connected",
                "payload": {"app_id": app_id, "message": "Connected to app updates"},
                "timestamp": "now",
            }
        )

        while True:
            data = await websocket.receive_text()
            try:
                message = json.loads(data)

                # Handle app-specific messages
                if message.get("type") == "get_status":
                    # Respond with current app status
                    await websocket.send_json(
                        {
                            "type": "status_update",
                            "payload": {"app_id": app_id, "status": "monitoring"},
                            "timestamp": "now",
                        }
                    )

            except json.JSONDecodeError:
                await websocket.send_json(
                    {
                        "type": "error",
                        "payload": {"message": "Invalid JSON format"},
                        "timestamp": "now",
                    }
                )

    except WebSocketDisconnect:
        manager.disconnect(websocket)
        logger.info(f"Client disconnected from app {app_id}")
    except Exception as e:
        logger.error(f"Error in app WebSocket: {e}")
        manager.disconnect(websocket)


@websocket_router.websocket("/ws/alerts")
async def websocket_alerts(websocket: WebSocket):
    """WebSocket endpoint for real-time alerts"""
    await manager.connect_to_alerts(websocket)

    try:
        # Send initial connection confirmation
        await websocket.send_json(
            {
                "type": "connected",
                "payload": {"message": "Connected to alert stream"},
                "timestamp": "now",
            }
        )

        while True:
            data = await websocket.receive_text()
            try:
                message = json.loads(data)

                # Handle alert-specific messages
                if message.get("type") == "acknowledge":
                    # Handle alert acknowledgment
                    alert_id = message.get("payload", {}).get("alert_id")
                    if alert_id:
                        logger.info(f"Alert {alert_id} acknowledged")
                        await websocket.send_json(
                            {
                                "type": "acknowledged",
                                "payload": {"alert_id": alert_id},
                                "timestamp": "now",
                            }
                        )

            except json.JSONDecodeError:
                await websocket.send_json(
                    {
                        "type": "error",
                        "payload": {"message": "Invalid JSON format"},
                        "timestamp": "now",
                    }
                )

    except WebSocketDisconnect:
        manager.disconnect(websocket)
        logger.info("Client disconnected from alerts")
    except Exception as e:
        logger.error(f"Error in alerts WebSocket: {e}")
        manager.disconnect(websocket)
