from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime
from .activity import Activity

class SystemStatus(BaseModel):
    """
    Represents the system status
    """
    orchestrator_ready: bool = False
    current_activity: Optional[Activity] = None
    sensors_connected: Dict[str, bool] = {
        "rfid": False,
        "imu": False,
        "audio": False,
    }
    total_batches_processed: int = 0
    s3_uploads_successful: int = 0
    error_count: int = 0
    session_start_time: datetime = datetime.now()
