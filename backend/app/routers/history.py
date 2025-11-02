from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse

router = APIRouter()

@router.get("/history")
async def get_history(username: str = Query(...)):
    try:
        # placeholder until we connect DB
        dummy_history = [
            {"id": 1, "summary": "Meeting summary 1...", "timestamp": "2025-11-01T18:00:00"},
            {"id": 2, "summary": "Meeting summary 2...", "timestamp": "2025-11-01T18:10:00"},
        ]
        return dummy_history
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)
