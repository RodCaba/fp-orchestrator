from src.storage.s3 import S3Service, S3Config
import os
from dotenv import load_dotenv
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()

def main():
    config = S3Config(
        access_key=os.getenv("AWS_ACCESS_KEY_ID"),
        secret_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
        bucket_name=os.getenv("S3_BUCKET_NAME"),
        region=os.getenv("AWS_REGION")
    )
    s3_service = S3Service(config)

    if s3_service.is_connected():
        logger.info("Connected to S3 bucket successfully.")
    else:
        logger.error("Failed to connect to S3 bucket.")
        exit(1)

    objects = s3_service.list_objects(prefix=os.getenv("S3_PROTO_PREFIX", ""))
    logger.info(f"Objects in bucket: {objects}")

if __name__ == "__main__":
    main()
