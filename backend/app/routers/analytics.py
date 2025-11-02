from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from datetime import datetime
from app.database import get_meetings_collection, get_summaries_collection
from app.routers.auth import get_current_user

router = APIRouter(tags=["Analytics"])

@router.get("/analytics")
async def get_analytics(current_user: dict = Depends(get_current_user)):
    """Return analytics for the logged-in user:
    - total_meetings: meetings where the user is the organizer
    - total_summaries: number of saved summaries by username (falls back to user id)
    - upcoming_meetings: next 5 scheduled meetings (not done)
    """
    try:
        meetings_col = get_meetings_collection()
        summaries_col = get_summaries_collection()

        user_id = str(current_user["_id"]) if current_user.get("_id") else None
        username = current_user.get("username") or current_user.get("email") or user_id

        total_meetings = await meetings_col.count_documents({"organizer_id": user_id})

        # Count summaries by username (this is how summarizer stores them)
        total_summaries = await summaries_col.count_documents({"username": username})

        # Upcoming meetings: scheduled_time >= now and status != done
        now = datetime.utcnow()
        cursor = meetings_col.find({
            "organizer_id": user_id,
            "status": {"$ne": "done"},
            "scheduled_time": {"$gte": now}
        }).sort("scheduled_time", 1).limit(5)

        upcoming = []
        async for m in cursor:
            upcoming.append({
                "id": str(m.get("_id")),
                "title": m.get("title"),
                "scheduled_time": m.get("scheduled_time").isoformat() if m.get("scheduled_time") else None,
                "status": m.get("status"),
            })

        return JSONResponse({
            "total_meetings": total_meetings,
            "total_summaries": total_summaries,
            "upcoming_meetings": upcoming,
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))