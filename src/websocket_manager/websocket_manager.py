from fastapi import WebSocket, WebSocketDisconnect
import logging
from typing import List, Dict, Any
import json
from ..models.prediction import PredictionResult

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

    async def broadcast_s3_stats_update(self, s3_stats: Dict[str, Any]):
        """
        Broadcast S3 statistics update to all connected WebSocket clients.
        """
        message = {
            "type": "s3_stats_update",
            "s3_stats": s3_stats
        }
        await self.broadcast(message)
        logger.info(f"Broadcasted S3 stats update: {s3_stats}")
    
    async def broadcast_prediction_progress(self, progress: float):
        """
        Broadcast prediction progress to all connected WebSocket clients.
        """
        message = {
            "type": "prediction_progress",
            "data": {
                "progress": progress
            }
        }
        await self.broadcast(message)
        logger.info(f"Broadcasted prediction progress: {progress*100:.2f}%")

    async def broadcast_prediction_status(self, status):
        """
        Broadcast prediction status to all connected WebSocket clients.
        """
        logger.info(f"Prediction status: {status}")
        message = {
            "type": "prediction_status",
            "data": {
                "is_active": status.is_active,
                "waiting_for_rfid": status.waiting_for_rfid,
                "collecting_data": status.collecting_data,
                "data_collection_progress": status.data_collection_progress,
                "current_prediction": status.current_prediction.dict() if status.current_prediction else None
            }
        }
        await self.broadcast(message)
        logger.info(f"Broadcasted prediction status: active={status.is_active}")

    async def broadcast_prediction_result(self, result: PredictionResult):
        """
        Broadcast a prediction result to all connected WebSocket clients.
        """
        message = {
            "type": "prediction_result",
            "data": {
                "predicted_label": result.predicted_label,
                "confidence": result.confidence,
                "timestamp": result.timestamp.isoformat(),
                "n_users": result.n_users
            }
        }
        await self.broadcast(message)
        logger.info(f"Broadcasted prediction result: {result.predicted_label} with confidence {result.confidence}")