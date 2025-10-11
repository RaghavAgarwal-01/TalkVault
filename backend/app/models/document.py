# backend/app/models/document.py

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

class DocumentType(str, Enum):
    PDF = "pdf"
    WORD = "word"
    TEXT = "text"
    AUDIO = "audio"
    VIDEO = "video"
    OTHER = "other"

class ProcessingStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class Document(BaseModel):
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    filename: str
    original_filename: str
    file_path: str
    file_size: int
    file_type: DocumentType
    mime_type: str
    owner_id: str
    meeting_id: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    content: Optional[str] = None  # Extracted text content
    summary: Optional[str] = None
    keywords: List[str] = []
    processing_status: ProcessingStatus = ProcessingStatus.PENDING
    processing_error: Optional[str] = None
    metadata: Dict[str, Any] = {}
    tags: List[str] = []
    is_public: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

class DocumentCreate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    meeting_id: Optional[str] = None
    tags: List[str] = []
    is_public: bool = False

class DocumentUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    content: Optional[str] = None
    summary: Optional[str] = None
    keywords: Optional[List[str]] = None
    processing_status: Optional[ProcessingStatus] = None
    processing_error: Optional[str] = None
    tags: Optional[List[str]] = None
    is_public: Optional[bool] = None

class DocumentResponse(BaseModel):
    id: str = Field(..., alias="_id")
    filename: str
    original_filename: str
    file_size: int
    file_type: DocumentType
    owner_id: str
    meeting_id: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    summary: Optional[str] = None
    keywords: List[str] = []
    processing_status: ProcessingStatus
    tags: List[str] = []
    is_public: bool
    created_at: datetime
    
    class Config:
        allow_population_by_field_name = True

class DocumentSearch(BaseModel):
    query: str
    file_type: Optional[DocumentType] = None
    tags: Optional[List[str]] = None
    meeting_id: Optional[str] = None
    owner_id: Optional[str] = None
