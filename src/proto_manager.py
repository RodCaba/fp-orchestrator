import os
from dotenv import load_dotenv
from src.storage.s3 import S3Service, S3Config
import logging
from pathlib import Path

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ProtoManager:
    """
    Manages the protocol buffer files for the project.
    """
    def __init__(self):
        """
        Initializes the ProtoManager with S3 configuration.
        """
        self.config = S3Config(
            access_key=os.getenv("AWS_ACCESS_KEY_ID"),
            secret_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
            bucket_name=os.getenv("S3_BUCKET_NAME"),
            region=os.getenv("AWS_REGION")
        )
        self.proto_prefix = os.getenv("S3_PROTO_PREFIX", "")
        self.proto_local_dir = Path(os.getenv("PROTO_LOCAL_DIR", "./proto"))
        self.grpc_output_dir = Path(os.getenv("PROTO_GRPC_OUTPUT_DIR", "./src/grpc"))
        self.s3_service = S3Service(self.config)

        # Ensure local directories exist
        self.proto_local_dir.mkdir(parents=True, exist_ok=True)
        self.grpc_output_dir.mkdir(parents=True, exist_ok=True)

        # Create __init__.py files on grpc output directory
        (self.grpc_output_dir / "__init__.py").touch(exist_ok=True)

    def check_connection(self) -> bool:
        """
        Checks if the S3 service is connected.
        :return: True if connected, False otherwise.
        """
        return self.s3_service.is_connected()

    def download_protos(self) -> list[str]:
        """
        Downloads .proto files from S3 and updates the local directory.
        :return: List of downloaded file paths.
        """
        objects = self.s3_service.list_objects(prefix=self.proto_prefix)
        logger.info(f"Objects in bucket: {objects}")
        files = []

        for obj in objects:
            if not obj.endswith('.proto'):
                logger.info(f"Skipping non-proto file: {obj}")
                continue
            try:
                filename = obj.replace(self.proto_prefix, "").lstrip('/')
                file_path = os.path.join(self.proto_local_dir, filename)
                self.s3_service.download(obj, file_path)
                logger.info(f"Downloaded {obj} to {file_path}")
                files.append(file_path)
            except Exception as e:
                logger.error(f"Error loading {obj}: {e}")

        return files
    
    def upload_protos(self, files: list[str] | None = None):
        """
        Uploads .proto files to S3.
        :param proto_files: List of paths to .proto files. If None, uploads all in the local directory.
        """
        # If no proto files are provided, upload all .proto files in the local directory
        if files is None:
            proto_files = [os.path.join(self.proto_local_dir, f) for f in os.listdir(self.proto_local_dir) if f.endswith('.proto')]
        else:
            proto_files = [Path(f) for f in files if f.endswith('.proto')]

        logger.info(f"Uploading {len(proto_files)} proto files to S3.")

        for proto_file in proto_files:
            if not proto_file.exists():
                logger.error(f"File {proto_file} does not exist.")
                continue
            try:
                key = f"{self.proto_prefix}{proto_file.name}"
                self.s3_service.upload(proto_file, key)
                logger.info(f"Uploaded {proto_file} to S3 with key {key}")
            except Exception as e:
                logger.error(f"Error uploading {proto_file}: {e}")
    
    def generate_grpc_code(self, proto_files: list[str] | None = None):
        """
        Generates gRPC code from the downloaded .proto files.
        :param proto_files: List of paths to .proto files.
        """
        if proto_files is None:
            proto_files = [os.path.join(self.proto_local_dir, f) for f in os.listdir(self.proto_local_dir) if f.endswith('.proto')]

        for proto_file in proto_files:
            try:
                command = f"python -m grpc_tools.protoc -I{self.proto_local_dir} --python_out={self.grpc_output_dir} --grpc_python_out={self.grpc_output_dir} {proto_file}"
                os.system(command)
                logger.info(f"Generated gRPC code for {proto_file}")
            except Exception as e:
                logger.error(f"Error generating gRPC code for {proto_file}: {e}")
        