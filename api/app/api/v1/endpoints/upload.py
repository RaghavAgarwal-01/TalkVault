"""
File upload endpoints with MongoDB
"""
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
import os
import uuid
import shutil
from typing import Optional

from app.db.db_mongo import db  # MongoDB client
from app.schemas.schemas import UploadResponse
from app.api.v1.endpoints.auth import get_current_user
from app.services.nlp_service import process_meeting_async

router = APIRouter()


ALLOWED_EXTENSIONS = {'.mp3', '.wav', '.m4a', '.txt', '.docx'}
UPLOAD_DIR = "uploads"


def allowed_file(filename: str) -> bool:
    return '.' in filename and \
           os.path.splitext(filename.lower())[1] in ALLOWED_EXTENSIONS


@router.post("/file", response_model=UploadResponse)
async def upload_file(
    file: UploadFile = File(...),
    title: str = Form(...),
    description: Optional[str] = Form(None),
    current_user = Depends(get_current_user),
):
    """Upload meeting file (audio or text)"""
    
    if not allowed_file(file.filename):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type not allowed. Allowed types: {', '.join(ALLOWED_EXTENSIONS)}"
        )
    
    # Generate unique filename
    file_extension = os.path.splitext(file.filename)[1].lower()
    unique_filename = f"{uuid.uuid4()}{file_extension}"
    file_path = os.path.join(UPLOAD_DIR, unique_filename)
    
    # Save file
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Could not save file: {str(e)}"
        )
    
    # Determine file type
    file_type = "text" if file_extension in ['.txt', '.docx'] else "audio"
    
    # Create meeting record in MongoDB
    meeting_doc = {
        "title": title,
        "description": description,
        "file_path": file_path,
        "file_type": file_type,
        "owner_id": current_user.id,
        "status": "pending",
        "transcript": None
    }
    result = await db.meetings.insert_one(meeting_doc)
    meeting_id = str(result.inserted_id)
    
    # Start async processing
    try:
        await process_meeting_async(meeting_id, file_path, file_type, db)
    except Exception as e:
        # Update status to failed
        await db.meetings.update_one({"_id": result.inserted_id}, {"$set": {"status": "failed"}})
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Processing failed: {str(e)}"
        )
    
    return UploadResponse(
        message="File uploaded and processing started",
        meeting_id=meeting_id,
        file_path=file_path
    )


@router.post("/text", response_model=UploadResponse)
async def upload_text(
    title: str = Form(...),
    content: str = Form(...),
    description: Optional[str] = Form(None),
    current_user = Depends(get_current_user),
):
    """Upload meeting text directly"""
    
    # Generate unique filename for text content
    unique_filename = f"{uuid.uuid4()}.txt"
    file_path = os.path.join(UPLOAD_DIR, unique_filename)
    
    # Save text content
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Could not save text: {str(e)}"
        )
    
    # Create meeting record in MongoDB with transcript stored
    meeting_doc = {
        "title": title,
        "description": description,
        "file_path": file_path,
        "file_type": "text",
        "transcript": content,
        "owner_id": current_user.id,
        "status": "pending"
    }
    result = await db.meetings.insert_one(meeting_doc)
    meeting_id = str(result.inserted_id)
    
    # Start async processing
    try:
        await process_meeting_async(meeting_id, file_path, "text", db)
    except Exception as e:
        await db.meetings.update_one({"_id": result.inserted_id}, {"$set": {"status": "failed"}})
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Processing failed: {str(e)}"
        )
    
    return UploadResponse(
        message="Text uploaded and processing started",
        meeting_id=meeting_id,
        file_path=file_path
    )
