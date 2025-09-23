from pydantic import BaseModel, EmailStr
from typing import Optional, List, Dict, Any
from datetime import datetime


# User schemas
class UserBase(BaseModel):
    email: EmailStr
    username: str
    full_name: Optional[str] = None


class UserCreate(UserBase):
    password: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: str  # MongoDB ObjectId as string
    email: str
    username: str
    full_name: Optional[str] = None
    is_active: bool


# Token schemas
class Token(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse


class TokenData(BaseModel):
    email: Optional[str] = None


# Meeting schemas
class MeetingBase(BaseModel):
    title: str
    description: Optional[str] = None


class MeetingCreate(MeetingBase):
    pass


class MeetingUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None


class MeetingResponse(BaseModel):
    id: str  # MongoDB ObjectId as string
    title: str
    description: Optional[str] = None
    status: str
    summary: Optional[str] = None
    action_items: Optional[List[Dict[str, Any]]] = None
    created_at: datetime
    processed_at: Optional[datetime] = None


# Action Item schemas
class ActionItemBase(BaseModel):
    task_description: str
    assigned_to: Optional[str] = None
    due_date: Optional[datetime] = None
    priority: str = "medium"


class ActionItemCreate(ActionItemBase):
    meeting_id: str  # MongoDB ObjectId as string


class ActionItem(ActionItemBase):
    id: str  # MongoDB ObjectId as string
    meeting_id: str
    status: str
    created_at: datetime
    updated_at: Optional[datetime] = None


# File upload schemas
class UploadResponse(BaseModel):
    message: str
    meeting_id: str  # MongoDB ObjectId as string
    file_path: str


# Processing status
class ProcessingStatus(BaseModel):
    meeting_id: str  # MongoDB ObjectId as string
    status: str
    message: Optional[str] = None
    progress: Optional[int] = None  # 0-100
