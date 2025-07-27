from ..models import SensorData
from ..websocket_manager import WebSocketManager
from fp_orchestrator_utils import S3Config, S3Service
import os
import time
import logging
import asyncio
import threading
import json
from copy import deepcopy
from concurrent.futures import ThreadPoolExecutor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Buffer:
    def __init__(self, size, wsocket_manager: WebSocketManager):
        """
        Initializes the buffer with a specific size and WebSocket manager.
        """
        self.size = size
        self.data: list[SensorData] = []
        self.wsocket_manager = wsocket_manager
        self._lock = threading.Lock()

        s3_config = S3Config(
            access_key=os.getenv('S3_ACCESS_KEY'),
            secret_key=os.getenv('S3_SECRET_KEY'),
            bucket_name=os.getenv('S3_BUCKET_NAME'),
            region=os.getenv('S3_REGION', 'us-east-1'),
        )
        self.s3_prefix = os.getenv('S3_DATA_PREFIX', 'orchestrator_data/')
        self.s3_service = S3Service(s3_config)

        # Thread pool for async operations
        self.upload_executor = ThreadPoolExecutor(max_workers=5, thread_name_prefix='BufferUploadExecutor')
        self.upload_stats = {
            'totalUploads': 0,
            'totalErrors': 0,
            'pendingUploads': 0,
            'lastUploadTime': None,
        }

    def add(self, item: SensorData):
        """ Add an item to the buffer."""
        with self._lock:
          self.data.append(item)

    def _clear(self):
        """Clear the buffer."""
        with self._lock:
            self.data.clear()

    def current_size(self):
        """Returns the current size of the buffer."""
        with self._lock:
            return len(self.data)

    def upload_to_s3_async(self, label: str, n_users: int):
        """ Uploads the buffer data to S3 asynchronously """
        with self._lock:
          if not self.data:
              logger.info("Buffer is empty, nothing to upload.")
              return
          
          # Create data snapshot
          data_snapshot = deepcopy(self.data)
          self.data.clear()  # Clear the buffer after taking a snapshot

          logger.info(f"Starting async upload of {len(data_snapshot)} items to S3 with label '{label}' and n_users {n_users}")

        future = self.upload_executor.submit(
            self._upload_data_to_s3,
            data_snapshot,
            label,
            n_users
        )

        self.upload_stats['pendingUploads'] += 1
        self.upload_stats['lastUploadTime'] = time.time()
        future.add_done_callback(self._upload_completed_callback)

        return future

    def _upload_data_to_s3(
            self,
            data_snapshot: list[SensorData],
            label: str,
            n_users: int
    ):
        """
        Uploads a snapshot of data to S3 asynchronously.
        """
        upload_id = int(time.time() * 1000)

        try:
            data_to_upload = [item.to_dict() for item in data_snapshot]
            data_ob = {
                'upload_id': upload_id,
                'label': label,
                'n_users': n_users,
                'data': data_to_upload
            }
            
            timestamp = time.strftime('%Y%m%d_%H%M%S', time.gmtime())
            key = f"{self.s3_prefix}{timestamp}_{upload_id}.json"

            logger.info(f"Uploading data to S3 with key: {key}")

            self.s3_service.save(data_ob, key)

            return {
                "success": True,
                "key": key,
                "upload_id": upload_id,
                "data_count": len(data_snapshot)
            }
        except Exception as e:
            logger.error(f"Error uploading data to S3: {e}")

            self._handle_upload_failure(data_snapshot, label, n_users, e)
            return {
                "success": False,
                "error": str(e),
                "upload_id": upload_id
            }
        
    def _upload_completed_callback(self, future):
        """
        Callback for when the upload future is completed.
        """
        try:
            result = future.result()
            self.upload_stats['pendingUploads'] -= 1

            if result['success']:
                self.upload_stats['totalUploads'] += 1
                logger.info(f"Successfully uploaded {result['data_count']} items to S3 with key {result['key']}")
            else:
                self.upload_stats['totalErrors'] += 1
                logger.error(f"Failed to upload data: {result['error']}")
        except Exception as e:
            self.upload_stats['totalErrors'] += 1
            logger.error(f"Error in upload callback: {e}")
        finally:
            self._handle_s3_websocket_updates()
        
    def _handle_upload_failure(
            self,
            failed_data: list[SensorData],
            label: str,
            n_users: int,
            error: Exception
        ):
        """
        Handles the failure of data by backup
        """
        backup_file = f"backup_{int(time.time())}.json"
        try:
            os.makedirs('backup', exist_ok=True)
            backup_data = {
                'label': label,
                'n_users': n_users,
                'data': [item.to_dict() for item in failed_data],
                'error': str(error),
                'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
            }
            with open(os.path.join('backup', backup_file), 'w') as f:
                json.dump(backup_data, f)
        except Exception as e:
            logger.error(f"Error creating backup file: {e}")

    def _handle_s3_websocket_updates(self):
        """Handles updates from S3 and WebSocket."""
        def run_async_updates():
            loop = None
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

                loop.run_until_complete(
                    self.wsocket_manager.broadcast_stats_update(self.upload_stats)
                )
            except Exception as e:
                logger.error(f"Error broadcasting IMU data: {e}")

            finally:
                if loop:
                    loop.close()
        thread = threading.Thread(target=run_async_updates, daemon=True)
        thread.start()