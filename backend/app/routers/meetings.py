from fastapi import APIRouter, HTTPException, Path
from pydantic import BaseModel
from datetime import datetime
from bson import ObjectId
from typing import Optional, List, Union
from ..database import get_meetings_collection

router = APIRouter()

# -----------------------------
# ✅ Flexible models for MongoDB
# -----------------------------
class MeetingCreate(BaseModel):
    title: str
    datetime: str
    duration: Optional[int] = 0
    participants: Union[int, str, List[str], None] = 0
    summary: Optional[str] = ""


class MeetingOut(BaseModel):
    id: str
    title: str
    datetime: str
    duration: int
    participants: Union[int, str, List[str], None]
    summary: Optional[str]
    is_done: bool = False


# -----------------------------
# ✅ Serializer handles Mongo types safely
# -----------------------------
def serialize_meeting(meeting) -> dict:
    participants = meeting.get("participants", 0)
    # Normalize participants field
    if isinstance(participants, str) and participants.isdigit():
        participants = int(participants)
    elif isinstance(participants, list):
        participants = [str(p) for p in participants]
    elif not isinstance(participants, (int, str, list)):
        participants = 0

    dt = meeting.get("datetime")
    if isinstance(dt, datetime):
        dt_str = dt.isoformat()
    else:
        dt_str = str(dt)

    return {
        "id": str(meeting.get("_id")),
        "title": meeting.get("title", ""),
        "datetime": dt_str,
        "duration": meeting.get("duration", 0),
        "participants": participants,
        "summary": meeting.get("summary", ""),
        "is_done": meeting.get("is_done", False),
    }


# -----------------------------
# ✅ Routes
# -----------------------------
from datetime import datetime, timezone, timedelta

@router.post("/meetings", response_model=MeetingOut)
async def create_meeting(meeting: MeetingCreate):
    meetings_collection = get_meetings_collection()
    data = meeting.dict()
    print("📥 Received meeting data:", data)

    try:
        dt_str = data.get("datetime", "").strip()
        parsed_dt = None

        # Parse user-sent datetime
        for fmt in ("%Y-%m-%d %H:%M", "%Y-%m-%dT%H:%M", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d", "%Y-%m-%dT%H:%M:%S.%fZ"):
            try:
                parsed_dt = datetime.strptime(dt_str, fmt)
                break
            except ValueError:
                continue

        if not parsed_dt:
            print(f"⚠️ Could not parse datetime string '{dt_str}', using current time")
            parsed_dt = datetime.now()

        # 🕒 Convert from UTC → IST (+5:30)
        ist_offset = timedelta(hours=5, minutes=30)
        parsed_dt = parsed_dt + ist_offset

        data["datetime"] = parsed_dt
        data["is_done"] = False

        result = await meetings_collection.insert_one(data)
        created_meeting = await meetings_collection.find_one({"_id": result.inserted_id})
        return serialize_meeting(created_meeting)

    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error creating meeting: {str(e)}")


@router.get("/meetings", response_model=List[MeetingOut])
async def get_meetings():
    try:
        meetings_collection = get_meetings_collection()
        meetings = await meetings_collection.find().sort("datetime", 1).to_list(length=None)
        return [serialize_meeting(m) for m in meetings]
    except Exception as e:
        print("🔥 Error fetching meetings:", e)
        raise HTTPException(status_code=500, detail=f"Error fetching meetings: {str(e)}")


@router.put("/meetings/{meeting_id}/done", response_model=MeetingOut)
async def mark_meeting_done(meeting_id: str):
    try:
        meetings_collection = get_meetings_collection()
        result = await meetings_collection.update_one(
            {"_id": ObjectId(meeting_id)},
            {"$set": {"is_done": True}}
        )
        if result.modified_count == 0:
            raise HTTPException(status_code=404, detail="Meeting not found")

        meeting = await meetings_collection.find_one({"_id": ObjectId(meeting_id)})
        return serialize_meeting(meeting)

    except Exception as e:
        print("🔥 Error updating meeting:", e)
        raise HTTPException(status_code=500, detail=f"Error updating meeting: {str(e)}")
@router.get("/analytics")
async def get_analytics():
    """
    Return total meetings, total summaries, and next 2 upcoming meetings.
    Works correctly with MongoDB (counts summaries properly).
    """
    try:
        meetings_collection = get_meetings_collection()

        # Fetch all meetings
        all_meetings = await meetings_collection.find().to_list(length=None)
        total_meetings = len(all_meetings)

        # If you store summaries separately:
        from ..database import get_summaries_collection
        summaries_collection = get_summaries_collection()
        total_summaries = await summaries_collection.count_documents({})

        # Otherwise (if summaries stored within meetings), fallback:
        if total_summaries == 0:
            total_summaries = sum(1 for m in all_meetings if m.get("summary"))

        # Find upcoming meetings (not done + in future)
        now = datetime.utcnow()
        upcoming = await meetings_collection.find({
            "is_done": False,
            "datetime": {"$gte": now}
        }).sort("datetime", 1).to_list(length=5)

        upcoming_serialized = [serialize_meeting(m) for m in upcoming]

        return {
            "total_meetings": total_meetings,
            "total_summaries": total_summaries,
            "upcoming_meetings": upcoming_serialized
        }

    except Exception as e:
        print("🔥 Error generating analytics:", e)
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/meetings/{meeting_id}")
async def delete_meeting(meeting_id: str = Path(..., description="Meeting ID to delete")):
    """
    Delete a meeting by its ID from MongoDB (supports both ObjectId and string _id).
    """
    try:
        meetings_collection = get_meetings_collection()

        # Try both ways — ObjectId and plain string
        query = {"_id": ObjectId(meeting_id)} if ObjectId.is_valid(meeting_id) else {"_id": meeting_id}

        result = await meetings_collection.delete_one(query)

        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail=f"Meeting with id {meeting_id} not found")

        return {"message": "Meeting deleted successfully"}
    except Exception as e:
        print("🔥 Error deleting meeting:", e)
        raise HTTPException(status_code=500, detail=str(e))