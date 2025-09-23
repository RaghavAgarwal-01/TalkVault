"""
Meetings management endpoints with MongoDB
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional
import os
from bson import ObjectId

from app.db.db_mongo import db  # MongoDB client instance
from app.schemas.schemas import MeetingResponse, MeetingUpdate, ProcessingStatus
from app.api.v1.endpoints.auth import get_current_user

router = APIRouter()


def obj_id(id_str: str):
    try:
        return ObjectId(id_str)
    except Exception:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid ID format")


@router.get("/", response_model=List[MeetingResponse])
async def get_meetings(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    current_user = Depends(get_current_user),
):
    """Get all meetings for current user"""
    cursor = db.meetings.find({"owner_id": current_user.id}).skip(skip).limit(limit)
    meetings = await cursor.to_list(length=limit)

    return [
        MeetingResponse(
            id=str(meeting["_id"]),
            title=meeting.get("title"),
            description=meeting.get("description"),
            status=meeting.get("status"),
            summary=meeting.get("summary"),
            action_items=meeting.get("action_items"),
            created_at=meeting.get("created_at"),
            processed_at=meeting.get("processed_at")
        )
        for meeting in meetings
    ]


@router.get("/{meeting_id}", response_model=MeetingResponse)
async def get_meeting(
    meeting_id: str,
    current_user = Depends(get_current_user),
):
    """Get specific meeting details"""
    meeting = await db.meetings.find_one({"_id": obj_id(meeting_id), "owner_id": current_user.id})

    if not meeting:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Meeting not found"
        )

    return MeetingResponse(
        id=str(meeting["_id"]),
        title=meeting.get("title"),
        description=meeting.get("description"),
        status=meeting.get("status"),
        summary=meeting.get("summary"),
        action_items=meeting.get("action_items"),
        created_at=meeting.get("created_at"),
        processed_at=meeting.get("processed_at")
    )


@router.get("/{meeting_id}/transcript")
async def get_meeting_transcript(
    meeting_id: str,
    current_user = Depends(get_current_user),
):
    """Get meeting transcript"""
    meeting = await db.meetings.find_one({"_id": obj_id(meeting_id), "owner_id": current_user.id})

    if not meeting:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Meeting not found"
        )

    return {
        "meeting_id": str(meeting["_id"]),
        "transcript": meeting.get("transcript"),
        "redacted_content": meeting.get("redacted_content")
    }


@router.get("/{meeting_id}/status", response_model=ProcessingStatus)
async def get_processing_status(
    meeting_id: str,
    current_user = Depends(get_current_user),
):
    """Get meeting processing status"""
    meeting = await db.meetings.find_one({"_id": obj_id(meeting_id), "owner_id": current_user.id})

    if not meeting:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Meeting not found"
        )

    progress = 0
    if meeting.get("status") == "processing":
        progress = 50
    elif meeting.get("status") == "completed":
        progress = 100

    return ProcessingStatus(
        meeting_id=str(meeting["_id"]),
        status=meeting.get("status"),
        message=f"Meeting is {meeting.get('status')}",
        progress=progress
    )


@router.put("/{meeting_id}", response_model=MeetingResponse)
async def update_meeting(
    meeting_id: str,
    meeting_update: MeetingUpdate,
    current_user = Depends(get_current_user),
):
    """Update meeting details"""
    meeting = await db.meetings.find_one({"_id": obj_id(meeting_id), "owner_id": current_user.id})

    if not meeting:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Meeting not found"
        )

    update_data = {}
    if meeting_update.title is not None:
        update_data["title"] = meeting_update.title
    if meeting_update.description is not None:
        update_data["description"] = meeting_update.description

    if update_data:
        await db.meetings.update_one(
            {"_id": obj_id(meeting_id)},
            {"$set": update_data}
        )

    # Fetch updated document
    meeting = await db.meetings.find_one({"_id": obj_id(meeting_id)})

    return MeetingResponse(
        id=str(meeting["_id"]),
        title=meeting.get("title"),
        description=meeting.get("description"),
        status=meeting.get("status"),
        summary=meeting.get("summary"),
        action_items=meeting.get("action_items"),
        created_at=meeting.get("created_at"),
        processed_at=meeting.get("processed_at")
    )


@router.delete("/{meeting_id}")
async def delete_meeting(
    meeting_id: str,
    current_user = Depends(get_current_user),
):
    """Delete meeting"""
    meeting = await db.meetings.find_one({"_id": obj_id(meeting_id), "owner_id": current_user.id})

    if not meeting:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Meeting not found"
        )

    # Delete file if exists
    if meeting.get("file_path") and os.path.exists(meeting.get("file_path")):
        os.remove(meeting.get("file_path"))

    await db.meetings.delete_one({"_id": obj_id(meeting_id)})

    return {"message": "Meeting deleted successfully"}
