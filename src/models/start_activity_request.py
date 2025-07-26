from pydantic import BaseModel

class StartActivityRequest(BaseModel):
    """
    Represents a request to start an activity.
    """
    activity_name: str

