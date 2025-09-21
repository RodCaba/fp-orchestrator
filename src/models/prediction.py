from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class PredictionRequest(BaseModel):
    pass

class PredictionResult(BaseModel):
    """
    Result of a prediction request.
    """
    predicted_label: str
    confidence: float
    timestamp: datetime = datetime.now()
    n_users: int = 0

class PredictionStatus(BaseModel):
    """
    Status of the prediction system
    """
    is_active: bool = False
    waiting_for_rfid: bool = True
    collecting_data: bool = False
    current_prediction: Optional[PredictionResult] = None
    data_collection_progress: float = 0.0