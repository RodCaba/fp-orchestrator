from dotenv import load_dotenv
import logging
from src import ProtoManager
import argparse

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()

COMMANDS = [
    'download_protos',
    'check_connection',
    'generate_grpc',
    'upload_protos'
]

def main():
    parser = argparse.ArgumentParser(
        description="Proto Manager CLI Tool - Manage Protocol Buffers",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
        Example usage:
        %(prog)s download_protos
        %(prog)s check_connection
        %(prog)s generate_grpc
        %(prog)s upload_protos
        """
    )

    subparsers = parser.add_subparsers(dest='command', required=True, help='Available commands')
    subparsers.add_parser('download_protos', help='Download .proto files from S3')
    subparsers.add_parser('check_connection', help='Check connection to S3 bucket')
    subparsers.add_parser('generate_grpc', help='Generate gRPC code from .proto files')
    subparsers.add_parser('upload_protos', help='Upload .proto files to S3')

    # Initialize ProtoManager
    proto_manager = ProtoManager()

    try:
        proto_manager.check_connection()
    except Exception as e:
        logger.error(f"Error checking connection: {e}")
        return

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    if args.command not in COMMANDS:
        logger.error(f"Invalid command: {args.command}. Available commands: {', '.join(COMMANDS)}")
        return
    
    if args.command == 'download_protos':
        try:
            downloaded_files = proto_manager.download_protos()
            logger.info(f"Downloaded files: {downloaded_files}")
        except Exception as e:
            logger.error(f"Error downloading protos: {e}")
    elif args.command == 'check_connection':
        try:
            if proto_manager.check_connection():
                logger.info("Successfully connected to S3 bucket.")
            else:
                logger.error("Failed to connect to S3 bucket.")
        except Exception as e:
            logger.error(f"Error checking connection: {e}")
    elif args.command == 'generate_grpc':
        try:
            proto_files = proto_manager.generate_grpc_code()
            logger.info(f"Generated gRPC code for files: {proto_files}")
        except Exception as e:
            logger.error(f"Error generating gRPC code: {e}")
    elif args.command == 'upload_protos':
        try:
            proto_manager.upload_protos()
            logger.info("Uploaded .proto files to S3 successfully.")
        except Exception as e:
            logger.error(f"Error uploading protos: {e}")
    else:
        logger.error(f"Unknown command: {args.command}. Available commands: {', '.join(COMMANDS)}")

    return 0
    

if __name__ == "__main__":
    main()
