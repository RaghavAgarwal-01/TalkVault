# backend/app/models/meeting.py

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from bson import ObjectId
from enum import Enum

class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid objectid")
        return ObjectId(v)

    @classmethod
    def __modify_schema__(cls, field_schema):
        field_schema.update(type="string")

class MeetingStatus(str, Enum):
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class Participant(BaseModel):
    user_id: str
    username: str
    email: str
    joined_at: Optional[datetime] = None
    left_at: Optional[datetime] = None

class Meeting(BaseModel):
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    title: str
    description: Optional[str] = None
    organizer_id: str
    participants: List[Participant] = []
    scheduled_time: datetime
    duration_minutes: Optional[int] = None
    status: MeetingStatus = MeetingStatus.SCHEDULED
    meeting_link: Optional[str] = None
    recording_url: Optional[str] = None
    transcript: Optional[str] = None
    summary: Optional[str] = None
    action_items: List[str] = []
    tags: List[str] = []
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

class MeetingCreate(BaseModel):
    title: str
    description: Optional[str] = None
    participants: List[str] = []  # List of user IDs
    scheduled_time: datetime
    duration_minutes: Optional[int] = 60
    tags: List[str] = []

class MeetingUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    scheduled_time: Optional[datetime] = None
    duration_minutes: Optional[int] = None
    status: Optional[MeetingStatus] = None
    transcript: Optional[str] = None
    summary: Optional[str] = None
    action_items: Optional[List[str]] = None
    tags: Optional[List[str]] = None

class MeetingResponse(BaseModel):
    id: str = Field(..., alias="_id")
    title: str
    description: Optional[str] = None
    organizer_id: str
    participants: List[Participant] = []
    scheduled_time: datetime
    duration_minutes: Optional[int] = None
    status: MeetingStatus
    meeting_link: Optional[str] = None
    recording_url: Optional[str] = None
    transcript: Optional[str] = None
    summary: Optional[str] = None
    action_items: List[str] = []
    tags: List[str] = []
    created_at: datetime
    
    class Config:
        allow_population_by_field_name = True