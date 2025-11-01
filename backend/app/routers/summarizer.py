from fastapi import APIRouter, File, UploadFile, Form, HTTPException
from fastapi.responses import JSONResponse
import os
import uuid
import shutil
import logging
from typing import Optional

from app.utils.summarize import transcribe_audio, summarize_text

logger = logging.getLogger("talkvault.summarizer_router")

# ⚡ Remove internal prefix — main.py already mounts it under /api/summarizer
router = APIRouter(tags=["Summarizer"])

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
    transcript: Optional[str] = Form(None)
):
    """
    Generate a summary:
    - If audio_file is provided → transcribe + summarize
    - If transcript text is provided → summarize directly
    """
    if not audio_file and not transcript:
        raise HTTPException(status_code=400, detail="Provide either an audio file or transcript text.")

    tmp_path = None
    try:
        # Case 1: Audio provided → transcribe first
        if audio_file:
            tmp_path = save_temp_file(audio_file)
            print("🎧 Transcribing audio:", tmp_path)
            logger.info(f"Uploaded audio saved: {tmp_path}")
            try:
                transcript_text = transcribe_audio(tmp_path)
            except Exception as e:
                logger.exception("Transcription failed: %s", e)
                raise HTTPException(status_code=500, detail=f"Transcription failed: {e}")
        else:
            # Case 2: Raw transcript provided
            transcript_text = transcript.strip()

        if not transcript_text:
            raise HTTPException(status_code=400, detail="Transcript text is empty or invalid.")

        # Summarize the text
        try:
            summary_text = summarize_text(transcript_text)
        except Exception as e:
            logger.exception("Summarization failed: %s", e)
            raise HTTPException(status_code=500, detail=f"Summarization failed: {e}")
        print("✅ Summary generated:", summary_text[:200])

        return JSONResponse({
            "transcript": transcript_text,
            "summary": summary_text
        })

    finally:
        # Clean up temp audio file
        if tmp_path and os.path.exists(tmp_path):
            os.remove(tmp_path)
            logger.info(f"Temporary file deleted: {tmp_path}")


@router.get("/test")
async def test_route():
    """Simple test endpoint to verify router mount"""
    return {"message": "Summarizer route is active"}
