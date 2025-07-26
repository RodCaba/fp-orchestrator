from ..models import Activity
from typing import List
from pathlib import Path
import json
from datetime import datetime

DEFAULT_ACTIVITIES = [
    Activity.create(name="Cooking", description="Household is cooking together"),
    Activity.create(name="Cleaning", description="Household is cleaning the kitchen"),
    Activity.create(name="Eating", description="Household is eating together"),
    Activity.create(name="Playing", description="Household is playing a game together"),
    Activity.create(name="Watching TV", description="Household is watching TV together"),
    Activity.create(name="Talking", description="Household is just talking"),
]
class ActivityManager:
    """A class to manage activities in a JSON file."""
    def __init__(
            self,
            activities_file: str = "activities.json"
        ):
        self.activities_file = Path(activities_file)
        self.activities: List[Activity] = []
        self.load_activities()

    def load_activities(self):
        """Load activities from the JSON file."""
        if self.activities_file.exists():
            try:
                with open(self.activities_file, 'r') as file:
                    activities_data = json.load(file)
                    self.activities = [Activity(**activity) for activity in activities_data]
            except (json.JSONDecodeError, TypeError) as e:
                print(f"Error loading activities: {e}")
                self.activities = []
        else:
            # Create the file if it does not exist
            self.activities = DEFAULT_ACTIVITIES
            self.save_activities()

    def get_by_name(self, name: str) -> Activity:
        """Get an activity by its name."""
        for activity in self.activities:
            if activity.name.lower() == name.lower():
                return activity
        raise ValueError(f"Activity '{name}' not found.")

    def save_activities(self):
        """Save activities to the JSON file."""
        try:
            with open(self.activities_file, 'w') as file:
                json.dump([activity.model_dump() for activity in self.activities], file, indent=2)
        except Exception as e:
            print(f"Error saving activities: {e}")

    def add_activity(self, activity: Activity) -> Activity:
        """Add a new activity to the list and save it. Raises an error if the activity already exists."""
        if any(
            existing_activity.name.lower() == activity.name.lower() for existing_activity in self.activities
        ):
            raise ValueError(f"Activity '{activity.name}' already exists.")
        self.activities.append(activity)
        self.save_activities()
        return activity

    def get_activities(self):
        return self.activities

    def clear_activities(self):
        self.activities.clear()