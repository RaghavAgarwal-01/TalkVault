from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from typing import List, Optional
from datetime import datetime
from bson import ObjectId

from app.database import get_meetings_collection
from app.routers.auth import get_current_user

router = APIRouter()

@router.get("/meetings")
async def list_meetings(limit: int = 50, current_user: dict = Depends(get_current_user)):
    """List meetings for the current user (organizer or participant)."""
    try:
        col = get_meetings_collection()
        user_id = str(current_user["_id"])

        # Find meetings where user is organizer or participant
        cursor = col.find({
            "$or": [
                {"organizer_id": user_id},
                {"participants.user_id": user_id}
            ]
        }).sort("scheduled_time", 1).limit(limit)

        items = []
        async for m in cursor:
            items.append({
                "id": str(m.get("_id")),
                "title": m.get("title"),
                "description": m.get("description"),
                "scheduled_time": m.get("scheduled_time").isoformat() if m.get("scheduled_time") else None,
                "duration_minutes": m.get("duration_minutes"),
                "status": m.get("status"),
                "organizer_id": m.get("organizer_id"),
                "participants": m.get("participants", []),
            })
        return JSONResponse({"items": items})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/meetings")
async def create_meeting(payload: dict, current_user: dict = Depends(get_current_user)):
    """Create a new meeting. Expected JSON payload keys:
    - title (str), description (str, optional)
    - scheduled_time (ISO string) e.g. "2025-11-02T15:00:00"
    - duration_minutes (int, optional)
    - participants (optional) list of emails or dicts {name, email}
    - tags (optional) list of strings
    """
    try:
        col = get_meetings_collection()
        user_id = str(current_user["_id"])

        title = payload.get("title")
        if not title:
            raise HTTPException(status_code=400, detail="title is required")

        scheduled_time_raw = payload.get("scheduled_time")
        try:
            scheduled_time = datetime.fromisoformat(scheduled_time_raw) if scheduled_time_raw else None
        except Exception:
            raise HTTPException(status_code=400, detail="scheduled_time must be an ISO timestamp")

        participants_raw = payload.get("participants", [])
        parsed_participants = []
        for p in participants_raw:
            if isinstance(p, str):
                parsed_participants.append({"name": None, "email": p, "user_id": None})
            elif isinstance(p, dict):
                parsed_participants.append({
                    "name": p.get("name"),
                    "email": p.get("email"),
                    "user_id": p.get("user_id")
                })

        doc = {
            "title": title,
            "description": payload.get("description"),
            "organizer_id": user_id,
            "participants": parsed_participants,
            "scheduled_time": scheduled_time,
            "duration_minutes": payload.get("duration_minutes", 60),
            "status": "scheduled",
            "created_at": datetime.utcnow(),
            "tags": payload.get("tags", []),
        }

        res = await col.insert_one(doc)
        doc["id"] = str(res.inserted_id)
        # convert scheduled_time to iso
        if doc.get("scheduled_time"):
            doc["scheduled_time"] = doc["scheduled_time"].isoformat()

        return JSONResponse(doc)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/meetings/{meeting_id}/done")
async def mark_meeting_done(meeting_id: str, current_user: dict = Depends(get_current_user)):
    """Mark meeting status as 'done' (only organizer can do this)."""
    try:
        col = get_meetings_collection()
        if not ObjectId.is_valid(meeting_id):
            raise HTTPException(status_code=400, detail="invalid meeting id")

        m = await col.find_one({"_id": ObjectId(meeting_id)})
        if not m:
            raise HTTPException(status_code=404, detail="meeting not found")

        if str(current_user["_id"]) != m.get("organizer_id"):
            raise HTTPException(status_code=403, detail="only organizer can mark done")

        await col.update_one({"_id": ObjectId(meeting_id)}, {"$set": {"status": "done"}})
        return JSONResponse({"message": "marked done"})
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))