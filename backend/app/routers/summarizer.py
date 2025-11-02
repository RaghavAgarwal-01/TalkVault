# backend/app/routers/summarizer.py
from fastapi import APIRouter, File, UploadFile, Form, HTTPException
from fastapi.responses import JSONResponse
import os
import uuid
import shutil
import logging
from typing import Optional
from datetime import datetime
from bson import ObjectId

from app.utils.summarize import transcribe_audio, summarize_text
from app.database import get_summaries_collection  # existing helper in your project

logger = logging.getLogger("talkvault.summarizer_router")

# Keep router prefix in file — main.py mounts under /api/summarizer
router = APIRouter(
    prefix="/summarizer",
    tags=["summarizer"]
)

# Temporary upload folder
UPLOAD_DIR = os.path.join(os.getcwd(), "tmp_uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)


def save_temp_file(upload_file: UploadFile) -> str:
    """Save uploaded file temporarily and return its path."""
    ext = os.path.splitext(upload_file.filename)[1] or ".wav"
    tmp_path = os.path.join(UPLOAD_DIR, f"{uuid.uuid4().hex}{ext}")
    with open(tmp_path, "wb") as f:
        shutil.copyfileobj(upload_file.file, f)
    upload_file.file.close()
    return tmp_path


@router.post("/generate")
async def generate_summary(
    audio_file: Optional[UploadFile] = File(None),
    transcript: Optional[str] = Form(None),
    username: Optional[str] = Form(None),
):
    """
    Generate a summary:
    - If audio_file is provided → transcribe + summarize
    - If transcript text is provided → summarize directly
    - Optional `username` (string) to save author of the summary in DB
    """
    if not audio_file and not transcript:
        raise HTTPException(status_code=400, detail="Provide either an audio file or transcript text.")

    tmp_path = None
    try:
        # Case 1: Audio provided → transcribe first
        if audio_file:
            tmp_path = save_temp_file(audio_file)
            logger.info(f"Uploaded audio saved: {tmp_path}")
            try:
                transcript_text = transcribe_audio(tmp_path)
            except Exception as e:
                logger.exception("Transcription failed: %s", e)
                raise HTTPException(status_code=500, detail=f"Transcription failed: {e}")
        else:
            # Case 2: Raw transcript provided
            transcript_text = (transcript or "").strip()

        if not transcript_text:
            raise HTTPException(status_code=400, detail="Transcript text is empty or invalid.")

        # Summarize the text
        try:
            summary_text = summarize_text(transcript_text)
        except Exception as e:
            logger.exception("Summarization failed: %s", e)
            raise HTTPException(status_code=500, detail=f"Summarization failed: {e}")

        # Save to DB (if collection available)
        try:
            summaries_col = get_summaries_collection()
            if summaries_col is not None:
                doc = {
                    "username": username or "anonymous",
                    "original_text": transcript_text,
                    "summary_text": summary_text,
                    "created_at": datetime.utcnow()
                }
                res = await summaries_col.insert_one(doc)
                saved_id = str(res.inserted_id)
                logger.info("Saved summary id=%s user=%s", saved_id, username)
            else:
                saved_id = None
        except Exception as e:
            logger.exception("Failed to save summary to DB: %s", e)
            # do not fail the request if DB save fails; return summary anyway
            saved_id = None

        response_data = {
            "transcript": transcript_text,
            "summary": summary_text,
            "saved_id": saved_id
        }
        return JSONResponse(response_data)

    finally:
        # Clean up temp audio file
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
                logger.info(f"Temporary file deleted: {tmp_path}")
            except Exception:
                logger.warning("Failed to delete temp file: %s", tmp_path)


# History endpoints

@router.get("/history")
async def get_history(limit: int = 50, username: Optional[str] = None):
    """
    Return last `limit` summaries.
    If `username` provided, return summaries only for that user.
    """
    try:
        col = get_summaries_collection()
        query = {}
        if username:
            query["username"] = username
        cursor = col.find(query).sort("created_at", -1).limit(limit)
        items = []
        async for doc in cursor:
            items.append({
                "id": str(doc.get("_id")),
                "username": doc.get("username"),
                "original_text": doc.get("original_text"),
                "summary_text": doc.get("summary_text"),
                "created_at": doc.get("created_at").isoformat() if doc.get("created_at") else None
            })
        return JSONResponse({"items": items})
    except Exception as e:
        logger.exception("Failed to fetch history: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history/{summary_id}")
async def get_summary_detail(summary_id: str):
    """Return single saved summary by id."""
    try:
        col = get_summaries_collection()
        doc = await col.find_one({"_id": ObjectId(summary_id)})
        if not doc:
            raise HTTPException(status_code=404, detail="Summary not found")
        return JSONResponse({
            "id": str(doc.get("_id")),
            "username": doc.get("username"),
            "original_text": doc.get("original_text"),
            "summary_text": doc.get("summary_text"),
            "created_at": doc.get("created_at").isoformat() if doc.get("created_at") else None
        })
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Error fetching summary detail: %s", e)
        raise HTTPException(status_code=500, detail=str(e))
