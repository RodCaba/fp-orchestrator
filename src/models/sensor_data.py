from datetime import datetime
from pydantic import BaseModel
from typing import Optional
from typing import Dict, Any

class SensorData(BaseModel):
    """
    Represents the data from a sensor.
    """
    sensor_type: str
    device_id: Optional[str] = None
    data: Dict[str, Any]
    batch_id: Optional[str] = None