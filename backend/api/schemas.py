from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class ReadingCreate(BaseModel):
    station_id: str
    timestamp: Optional[datetime] = None
    temperature: float
    pressure: float
    humidity: float
    rainfall: Optional[float] = None
    wind_speed: Optional[float] = None
    wind_direction: Optional[float] = None
    solar_radiation: Optional[float] = None
    cloud_cover: Optional[float] = None

class LoginRequest(BaseModel):
    username: str
    password: str

class AlertActionRequest(BaseModel):
    action: str # acknowledge, quarantine, resolve
