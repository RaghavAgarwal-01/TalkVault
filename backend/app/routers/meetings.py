# backend/app/routers/meetings.py

from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
from bson import ObjectId
from datetime import datetime

from app.database import get_meetings_collection, get_users_collection
from app.models.meeting import MeetingCreate, MeetingUpdate, MeetingResponse, Meeting, MeetingStatus, Participant
from app.models.user import User
from app.routers.auth import get_current_user

router = APIRouter()

@router.post("/", response_model=MeetingResponse)
async def create_meeting(
    meeting: MeetingCreate,
    current_user: User = Depends(get_current_user)
):
    """Create a new meeting"""
    meetings_collection = get_meetings_collection()
    users_collection = get_users_collection()
    
    # Validate participant user IDs
    participants = []
    for user_id in meeting.participants:
        if not ObjectId.is_valid(user_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid user ID: {user_id}"
            )
        
        user = await users_collection.find_one({"_id": ObjectId(user_id)})
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User not found: {user_id}"
            )
        
        participants.append(Participant(
            user_id=str(user["_id"]),
            username=user["username"],
            email=user["email"]
        ))
    
    # Create meeting document
    meeting_dict = {
        "title": meeting.title,
        "description": meeting.description,
        "organizer_id": str(current_user["_id"]),
        "participants": [p.dict() for p in participants],
        "scheduled_time": meeting.scheduled_time,
        "duration_minutes": meeting.duration_minutes,
        "status": MeetingStatus.SCHEDULED,
        "tags": meeting.tags,
        "action_items": [],
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    
    result = await meetings_collection.insert_one(meeting_dict)
    
    # Get the created meeting
    created_meeting = await meetings_collection.find_one({"_id": result.inserted_id})
    return MeetingResponse(**created_meeting, id=str(created_meeting["_id"]))

@router.get("/", response_model=List[MeetingResponse])
async def get_meetings(
    skip: int = 0,
    limit: int = 50,
    status: Optional[MeetingStatus] = None,
    current_user: User = Depends(get_current_user)
):
    """Get meetings for current user"""
    meetings_collection = get_meetings_collection()
    
    # Filter for meetings where user is organizer or participant
    user_id_str = str(current_user["_id"])
    filter_query = {
        "$or": [
            {"organizer_id": user_id_str},
            {"participants.user_id": user_id_str}
        ]
    }
    
    if status:
        filter_query["status"] = status
    
    cursor = meetings_collection.find(filter_query).sort("scheduled_time", -1).skip(skip).limit(limit)
    meetings = []
    async for meeting in cursor:
        meetings.append(MeetingResponse(**meeting, id=str(meeting["_id"])))
    
    return meetings

@router.get("/{meeting_id}", response_model=MeetingResponse)
async def get_meeting(
    meeting_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get meeting by ID"""
    if not ObjectId.is_valid(meeting_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid meeting ID"
        )
    
    meetings_collection = get_meetings_collection()
    meeting = await meetings_collection.find_one({"_id": ObjectId(meeting_id)})
    
    if not meeting:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Meeting not found"
        )
    
    # Check if user has access to this meeting
    user_id_str = str(current_user["_id"])
    if (meeting["organizer_id"] != user_id_str and 
        not any(p["user_id"] == user_id_str for p in meeting.get("participants", []))):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this meeting"
        )
    
    return MeetingResponse(**meeting, id=str(meeting["_id"]))

@router.put("/{meeting_id}", response_model=MeetingResponse)
async def update_meeting(
    meeting_id: str,
    meeting_update: MeetingUpdate,
    current_user: User = Depends(get_current_user)
):
    """Update meeting (organizer only)"""
    if not ObjectId.is_valid(meeting_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid meeting ID"
        )
    
    meetings_collection = get_meetings_collection()
    meeting = await meetings_collection.find_one({"_id": ObjectId(meeting_id)})
    
    if not meeting:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Meeting not found"
        )
    
    # Check if user is organizer
    if meeting["organizer_id"] != str(current_user["_id"]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only meeting organizer can update the meeting"
        )
    
    # Prepare update data
    update_data = {"updated_at": datetime.utcnow()}
    
    if meeting_update.title is not None:
        update_data["title"] = meeting_update.title
    if meeting_update.description is not None:
        update_data["description"] = meeting_update.description
    if meeting_update.scheduled_time is not None:
        update_data["scheduled_time"] = meeting_update.scheduled_time
    if meeting_update.duration_minutes is not None:
        update_data["duration_minutes"] = meeting_update.duration_minutes
    if meeting_update.status is not None:
        update_data["status"] = meeting_update.status
    if meeting_update.transcript is not None:
        update_data["transcript"] = meeting_update.transcript
    if meeting_update.summary is not None:
        update_data["summary"] = meeting_update.summary
    if meeting_update.action_items is not None:
        update_data["action_items"] = meeting_update.action_items
    if meeting_update.tags is not None:
        update_data["tags"] = meeting_update.tags
    
    await meetings_collection.update_one(
        {"_id": ObjectId(meeting_id)},
        {"$set": update_data}
    )
    
    # Get updated meeting
    updated_meeting = await meetings_collection.find_one({"_id": ObjectId(meeting_id)})
    return MeetingResponse(**updated_meeting, id=str(updated_meeting["_id"]))

@router.delete("/{meeting_id}")
async def delete_meeting(
    meeting_id: str,
    current_user: User = Depends(get_current_user)
):
    """Delete meeting (organizer only)"""
    if not ObjectId.is_valid(meeting_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid meeting ID"
        )
    
    meetings_collection = get_meetings_collection()
    meeting = await meetings_collection.find_one({"_id": ObjectId(meeting_id)})
    
    if not meeting:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Meeting not found"
        )
    
    # Check if user is organizer
    if meeting["organizer_id"] != str(current_user["_id"]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only meeting organizer can delete the meeting"
        )
    
    await meetings_collection.delete_one({"_id": ObjectId(meeting_id)})
    return {"message": "Meeting deleted successfully"}
