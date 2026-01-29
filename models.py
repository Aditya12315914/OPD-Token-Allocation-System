from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import datetime

class TokenSource(BaseModel):
    type: Literal["online_booking", "walk_in", "paid_priority", "follow_up", "emergency"]
    patient_name: str
    patient_id: Optional[str] = None
    contact: Optional[str] = None

class TimeSlot(BaseModel):
    slot_time: str
    max_capacity: int = 10
    
class Doctor(BaseModel):
    doctor_id: str
    name: str
    specialization: str
    time_slots: list[TimeSlot]
    
class TokenRequest(BaseModel):
    doctor_id: str
    slot_time: str
    source: TokenSource
    
class Token(BaseModel):
    token_number: int
    doctor_id: str
    slot_time: str
    patient_name: str
    source_type: str
    priority_level: int
    status: str = "active"
    created_at: datetime = Field(default_factory=datetime.now)
    
class CancelTokenRequest(BaseModel):
    token_number: int
    doctor_id: str
    slot_time: str
    reason: Optional[str] = "cancelled"
