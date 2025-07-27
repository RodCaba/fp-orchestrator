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


def create_sensor_data(
    sensor_type: str,
    device_id: str = None,
    data: dict = None,
    batch_id: str = None
) -> dict:
    """
    Create a new dictionary of sensor data.
    """
    return {
        "sensor_type": sensor_type,
        "device_id": device_id,
        "data": data or {},
        "batch_id": batch_id,
    }
