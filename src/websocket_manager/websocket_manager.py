from fastapi import WebSocket, WebSocketDisconnect
import logging
from typing import List, Dict, Any
import json

logger = logging.getLogger(__name__)

class WebSocketManager:
    """
    Manages WebSocket connections and message handling.
    """

    def __init__(self):
        self.connections: List[WebSocket] = []

    async def add_connection(self, connection: WebSocket):
        """
        Add a new WebSocket connection.
        """
        await connection.accept()
        self.connections.append(connection)

    def remove_connection(self, connection: WebSocket):
        """
        Remove a WebSocket connection.
        """
        if connection in self.connections:
            self.connections.remove(connection)
            logger.info(f"Connection {connection.client} removed")
        else:
            logger.warning(f"Attempted to remove a connection that does not exist: {connection.client}")

    async def broadcast(self, message: Dict[str, Any]):
        """
        Broadcast a message to all connected WebSocket clients.
        """
        if not self.connections:
            logger.warning("No active WebSocket connections to broadcast to.")
            return
        
        message_str = json.dumps(message)
        disconnected_connections = []

        for conn in self.connections:
            try:
                await conn.send_text(message_str)
            except WebSocketDisconnect:
                disconnected_connections.append(conn)
            except Exception as e:
                logger.error(f"Error sending message to {conn.client}: {e}")

        for conn in disconnected_connections:
            self.remove_connection(conn)

    async def broadcast_activity_update(self, action: str, activity_name: str):
        """
        Broadcast an activity update to all connected WebSocket clients.
        """
        message = {
            "type": "activity_update",
            "action": action,
            "activity_name": activity_name
        }
        await self.broadcast(message)
        logger.info(f"Broadcasted activity update: {action} - {activity_name}")

    async def broadcast_sensor_status(self, sensor_type: str, status: str, data: Dict[str, Any]):
        """
        Broadcast a sensor status update to all connected WebSocket clients.
        """
        message = {
            "type": "sensor_status",
            "sensor_type": sensor_type,
            "status": status,
            "data": data or {}
        }
        await self.broadcast(message)
        logger.info(f"Broadcasted sensor status update: {sensor_type} - {status}")

    async def broadcast_orchestrator_status(self, status: str, message: str):
        """
        Broadcast the orchestrator status to all connected WebSocket clients.
        """
        message = {
            "type": "orchestrator_status",
            "status": status,
            "message": message
        }
        await self.broadcast(message)
        logger.info(f"Broadcasted orchestrator status: {status} - {message}")

    async def broadcast_stats_update(self, stats: Dict[str, Any]):
        """
        Broadcast a sensor statistics update to all connected WebSocket clients.
        """
        message = {
            "type": "stats_update",
            "stats": stats
        }
        await self.broadcast(message)
        logger.info(f"Broadcasted stats update for {stats}")