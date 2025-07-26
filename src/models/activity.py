from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class Activity(BaseModel):
    """
    Represents an activity with a name, description, and creation timestamp.
    """
    name: str
    description: Optional[str] = None
    created_at: str = datetime.now().isoformat()

    @classmethod
    def create(cls, name: str, description: Optional[str] = None) -> "Activity":
        """
        Create a new activity instance.
        """
        return cls(name=name, description=description)