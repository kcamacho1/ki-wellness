from pydantic import BaseModel
from typing import List, Optional
from datetime import date

class OnboardUser(BaseModel):
    name: str
    dob: date
    weight: Optional[float]
    height: Optional[float]
    diet_type: Optional[List[str]] = []
    restrictions: Optional[List[str]] = []
    sleep_schedule: Optional[str]
    physical_ailments: Optional[List[str]] = []
    spiritual_belief: Optional[str]
    self_connection_methods: Optional[List[str]] = []
    environment_connection_methods: Optional[List[str]] = []
    group_safety: Optional[List[str]] = []
    stress_coping_methods: Optional[List[str]] = []
    goals: Optional[str]
