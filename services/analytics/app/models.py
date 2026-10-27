from datetime import datetime
from pydantic import BaseModel

class Measurement(BaseModel):
    device_id: int
    temperature: float
    timestamp: datetime
