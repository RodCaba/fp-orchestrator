import logging
import asyncio
from ..models import SystemStatus
from pathlib import Path
import sys
import grpc
from ..models import SensorData
from ..websocket_manager import WebSocketManager

logger = logging.getLogger(__name__)

grpc_dir = Path(__file__).parent.parent / "grpc"
# Add the grpc directory to sys.path temporarily
grpc_path_str = str(grpc_dir.absolute())
if grpc_path_str not in sys.path:
    sys.path.append(grpc_path_str)
try:
    import orchestrator_service_pb2  # type: ignore
    import orchestrator_service_pb2_grpc  # type: ignore
except ImportError as e:
    logger.error(f"Failed to import gRPC modules: {e}")
    raise RuntimeError("gRPC modules could not be loaded. Ensure they are generated correctly.")



class OrchestratorServicer(orchestrator_service_pb2_grpc.OrchestratorServiceServicer):
    """
    gRPC service for orchestrator operations.
    """
    def __init__(self, wsocket_manager: WebSocketManager):
        self.system_status = SystemStatus()
        self.sensor_stats = {
            "imu": { "batches_received": 0 },
            "audio": { "features_processed": 0 },
            "rfid": { "last_signal": None }
        }
        self.imu_buffer = []
        self.wsocket_manager = wsocket_manager   

    def HealthCheck(self, request, context):
        """
        Health check method to verify if the orchestrator is ready.
        """
        logger.info("Health check received")
        return orchestrator_service_pb2.HealthCheckResponse(status=True)

    def OrchestratorStatus(self, request, context):
        """
        Returns the current status of the orchestrator.
        """
        logger.info("Orchestrator status request received")

        current_activity_name = ""

        if self.system_status.current_activity:
            current_activity_name = self.system_status.current_activity.name

        response = orchestrator_service_pb2.OrchestratorStatusResponse(
            is_ready=self.system_status.orchestrator_ready,
            current_activity=current_activity_name
        )

        logger.info(f"Orchestrator status: {response.is_ready}, Current activity: {response.current_activity}")
        return response

    async def ReceiveIMUData(self, request, context):
        """
        Receives IMU data and updates the system status.
        """
        try:
            if not self.system_status.orchestrator_ready:
                logger.warning("Orchestrator is not ready to receive IMU data")
                return orchestrator_service_pb2.IMUPayloadResponse(
                    device_id=request.device_id,
                    status="rejected_not_ready"
                )
            # Process the IMU data
            imu_data = SensorData(
                device_id=request.device_id,
                timestamp=request.timestamp,
                data=request.data
            )
            logger.info(f"Received IMU data from {imu_data.device_id} at {imu_data.timestamp}")

            # Update stats
            self.sensor_stats["imu"]["batches_received"] += 1
            self.system_status.total_batches_processed += 1
            
            # Update sensor status
            asyncio.create_task(
                self.wsocket_manager.broadcast_sensor_status("imu", "connected", self.sensor_stats["imu"])
            )

            # Update stats
            asyncio.create_task(
                self.wsocket_manager.broadcast_stats_update(self.sensor_stats)
            )

            return orchestrator_service_pb2.IMUPayloadResponse(
                device_id=request.device_id,
                status="success"
            )

        except Exception as e:
            logger.error(f"Error checking orchestrator status: {e}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details("Internal server error")
            return orchestrator_service_pb2.IMUPayloadResponse(
                device_id=request.device_id,
                timestamp=request.timestamp,
                status="error"
            )