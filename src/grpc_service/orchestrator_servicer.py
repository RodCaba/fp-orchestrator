import logging
import asyncio
from ..models import SystemStatus
from pathlib import Path
import sys
import grpc
from ..models import create_sensor_data
from ..websocket_manager import WebSocketManager
from ..buffer import Buffer
from datetime import datetime
import time
import threading

logger = logging.getLogger(__name__)

grpc_dir = Path(__file__).parent.parent / "grpc"
# Add the grpc directory to sys.path temporarily
grpc_path_str = str(grpc_dir.absolute())
if grpc_path_str not in sys.path:
    sys.path.append(grpc_path_str)
try:
    import orchestrator_service_pb2  # type: ignore
    import orchestrator_service_pb2_grpc  # type: ignore
    import imu_service_pb2  # type: ignore  
    import rfid_service_pb2  # type: ignore
    import audio_service_pb2  # type: ignore
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
        self.buffer = Buffer(size=5000, wsocket_manager=wsocket_manager)
        self.wsocket_manager = wsocket_manager   
        self.current_users = 0

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

    def ReceiveIMUData(self, request, context):
        """
        Receives IMU data and updates the system status.
        """
        try:
            if not self.system_status.orchestrator_ready or self.current_users == 0:
                logger.warning("Orchestrator is not ready to receive IMU data")
                return imu_service_pb2.IMUPayloadResponse(
                    device_id=request.device_id,
                    status="rejected_not_ready"
                )
            # Process the IMU data
            imu_data = self._proto_to_sensor_imu_data(request)

            # Update stats
            self.sensor_stats["imu"]["batches_received"] += 1
            self.system_status.total_batches_processed += 1

            # Add to buffer
            self._handle_buffer_upload(imu_data)
            
            # Update sensor status
            self._handle_imu_websocket_updates()

            return imu_service_pb2.IMUPayloadResponse(
                device_id=request.device_id,
                status="success"
            )

        except Exception as e:
            logger.error(f"Error checking orchestrator status: {e}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details("Internal server error")
            return imu_service_pb2.IMUPayloadResponse(
                device_id=request.device_id,
                status="error"
            )

    def ReceiveRFIDData(self, request, context):
        """
        Receives RFID data and updates the system status.
        """
        try:
            # Process the RFID data
            self.sensor_stats["rfid"]["last_signal"] = datetime.now().isoformat()

            # Update stats
            self.system_status.total_batches_processed += 1
            self.current_users = request.current_tags or 0

            # Broadcast RFID data via WebSocket
            self._handle_rfid_websocket_updates()

            return rfid_service_pb2.RFIDPayloadResponse(
                device_id=request.device_id,
                status="success"
            )

        except Exception as e:
            logger.error(f"Error processing RFID data: {e}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details("Internal server error")
            return rfid_service_pb2.RFIDPayloadResponse(
                device_id=request.device_id,
                status="error"
            )

    def ReceiveAudioData(self, request, context):
        """
        Receives audio data and updates the system status.
        """
        try:
            if not self.system_status.orchestrator_ready or self.current_users == 0:
                logger.warning("Orchestrator is not ready to receive audio data")
                return audio_service_pb2.AudioPayloadResponse(
                    session_id=request.session_id,
                    status="rejected_not_ready"
                )
            # Process the audio data
            self.sensor_stats["audio"]["features_processed"] += 1
            self.system_status.total_batches_processed += 1
            
            # Broadcast audio data via WebSocket
            self._handle_audio_websocket_updates()
            audio_data = self._proto_to_sensor_audio_data(request)
            logger.info(f"Processed audio data {audio_data}")

            # Add to buffer
            self._handle_buffer_upload(audio_data)

            return audio_service_pb2.AudioPayloadResponse(
                session_id=request.session_id,
                status="success"
            )

        except Exception as e:
            logger.error(f"Error processing audio data: {e}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details("Internal server error")
            return audio_service_pb2.AudioPayloadResponse(
                session_id=request.session_id,
                status="error"
            )
        
    def _handle_buffer_upload(self, data: dict):
        """
        Handles data upload to the buffer.
        """
        self.buffer.add(data)

        if self.buffer.current_size() >= self.buffer.size:
            logger.info(f"Buffer size exceeded threshold, uploading {self.buffer.current_size()} items to S3")
            self.buffer.upload_to_s3_async(
                label=self.system_status.current_activity.name,
                n_users=self.current_users
            )

    def _proto_to_sensor_imu_data(self, request):
        """
        Converts a protobuf IMU payload to a object.
        """
        if request.data.values.HasField("standard"):
            sensor_values = {
                "x": request.data.values.standard.x,
                "y": request.data.values.standard.y,
                "z": request.data.values.standard.z
            }
        elif request.data.values.HasField("orientation"):
            sensor_values = {
                "qx": request.data.values.orientation.qx,
                "qy": request.data.values.orientation.qy,
                "qz": request.data.values.orientation.qz,
                "qw": request.data.values.orientation.qw,
                "roll": request.data.values.orientation.roll,
                "pitch": request.data.values.orientation.pitch,
                "yaw": request.data.values.orientation.yaw
            }
        else:
            sensor_values = {}
        return create_sensor_data(
            device_id=request.device_id,
            sensor_type="imu",
            data=sensor_values,
            batch_id=f"batch_{int(time.time() * 1000)}"
        )

    def _proto_to_sensor_audio_data(self, request):
        """
        Converts a protobuf audio payload to a object.
        """
        audio_features = {
            "feature_type": request.features.feature_type,
            "feature_shape": request.features.feature_shape,
            "feature_data": request.features.feature_data,
            "feature_parameters": {
                "n_ftt": request.features.feature_parameters.parameters.n_ftt,
                "hop_length": request.features.feature_parameters.parameters.hop_length,
                "n_mels": request.features.feature_parameters.parameters.n_mels,
                "f_min": request.features.feature_parameters.parameters.f_min,
                "f_max": request.features.feature_parameters.parameters.f_max,
                "target_sample_rate": request.features.feature_parameters.parameters.target_sample_rate,
                "power": request.features.feature_parameters.parameters.power
            }
        }

        processing_parameters = {
            "target_sample_rate": request.parameters.target_sample_rate,
            "target_length": request.parameters.target_length,
            "normalize": request.parameters.normalize,
            "normalization_method": request.parameters.normalization_method,
            "trim_strategy": request.parameters.trim_strategy,
        }
        return create_sensor_data(
            device_id=request.session_id,
            sensor_type="audio",
            data={
                "channels": request.channels,
                "sample_rate": request.sample_rate,
                "features": audio_features,
                "parameters": processing_parameters
            },
            batch_id=f"batch_{int(time.time() * 1000)}"
        )
    
    def _handle_imu_websocket_updates(self):
        """
        Handles WebSocket updates for IMU data.
        """
        def run_async_updates():
            loop = None
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

                loop.run_until_complete(
                    self.wsocket_manager.broadcast_sensor_status("imu", "connected", self.sensor_stats["imu"])
                )
                loop.run_until_complete(
                    self.wsocket_manager.broadcast_stats_update(self.sensor_stats)
                )
            except Exception as e:
                logger.error(f"Error broadcasting IMU data: {e}")

            finally:
                if loop:
                    loop.close()
        thread = threading.Thread(target=run_async_updates, daemon=True)
        thread.start()

    def _handle_rfid_websocket_updates(self):
        """
        Handles WebSocket updates for RFID data.
        """
        def run_async_updates():
            loop = None
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

                loop.run_until_complete(
                    self.wsocket_manager.broadcast_sensor_status("rfid", "connected", {
                        "last_signal": self.sensor_stats["rfid"]["last_signal"],
                        "current_users": self.current_users
                    })
                )
            except Exception as e:
                logger.error(f"Error broadcasting RFID data: {e}")

            finally:
                if loop:
                    loop.close()
        thread = threading.Thread(target=run_async_updates, daemon=True)
        thread.start()

    def _handle_audio_websocket_updates(self):
        """
        Handles WebSocket updates for audio data.
        """
        def run_async_updates():
            loop = None
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

                loop.run_until_complete(
                    self.wsocket_manager.broadcast_sensor_status("audio", "connected", self.sensor_stats["audio"])
                )
            except Exception as e:
                logger.error(f"Error broadcasting audio data: {e}")

            finally:
                if loop:
                    loop.close()
        thread = threading.Thread(target=run_async_updates, daemon=True)
        thread.start()
