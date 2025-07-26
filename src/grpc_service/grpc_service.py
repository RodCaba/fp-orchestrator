import grpc
from concurrent import futures
from .orchestrator_servicer import OrchestratorServicer
import logging
import sys
from pathlib import Path

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


class GRPCServer:
    """
    gRPC server for handling orchestrator service requests.
    """

    def __init__(self, port: int = 50051, orchestrator_servicer: OrchestratorServicer = None):
        self.port = port
        self.server = grpc.server(
            futures.ThreadPoolExecutor(max_workers=10),
        )
        orchestrator_service_pb2_grpc.add_OrchestratorServiceServicer_to_server(
            orchestrator_servicer, self.server
        )

    def start(self):
        """
        Start the gRPC server.
        """
        self.server.add_insecure_port(f'[::]:{self.port}')
        self.server.start()
        logger.info(f'gRPC server started on port {self.port}')
    
    def stop(self):
        """
        Stop the gRPC server.
        """
        self.server.stop(0)
        logger.info('gRPC server stopped')