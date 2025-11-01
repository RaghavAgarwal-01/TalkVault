from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from datetime import datetime
import re
from transformers import pipeline
from app.database import get_database
from typing import Optional

router = APIRouter(prefix="/summarizer", tags=["Summarizer"])

# Choose a lightweight summarization model
summarizer = pipeline("summarization", model="sshleifer/distilbart-cnn-12-6")

# --- Utility ---
def sanitize_text(text: str) -> str:
    if not text:
        return ""
    text = re.sub(r'[\x00-\x1f\x7f-\x9f]', ' ', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


@router.post("/generate")
async def generate_summary(
    file: Optional[UploadFile] = File(None),
    text: Optional[str] = Form(""),
    username: Optional[str] = Form("")
):
    """
    Accepts either:
      - text (as FormData)
      - or file upload (.txt, .docx, .mp3, etc.)
    and returns the summary.
    """

    # --- Read input content ---
    try:
        if file:
            raw_bytes = await file.read()
            try:
                content = raw_bytes.decode("utf-8", errors="ignore")
            except Exception:
                raise HTTPException(status_code=400, detail="Unable to decode uploaded file.")
        elif text:
            content = text
        else:
            raise HTTPException(status_code=400, detail="No text or file provided.")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error reading input: {str(e)}")

    clean_text = sanitize_text(content)
    if not clean_text:
        raise HTTPException(status_code=400, detail="Text unreadable after sanitization")

    db = get_database()  # sync client; if async, make this `await get_database()`

    # --- Chunked summarization ---
    try:
        words = clean_text.split()
        chunk_size = 400
        chunks = [" ".join(words[i:i + chunk_size]) for i in range(0, len(words), chunk_size)]

        partial_summaries = []
        for i, chunk in enumerate(chunks):
            try:
                out = summarizer(chunk, max_length=120, min_length=30, do_sample=False, truncation=True)
                if out and isinstance(out, list) and "summary_text" in out[0]:
                    partial_summaries.append(out[0]["summary_text"])
            except Exception as e:
                print(f"Chunk summarization failed (chunk {i}): {e}")
                continue

        if not partial_summaries:
            raise HTTPException(status_code=500, detail="Failed to generate partial summaries")

        # Merge groups progressively
        group_size = 5
        grouped = [" ".join(partial_summaries[i:i + group_size]) for i in range(0, len(partial_summaries), group_size)]

        section_summaries = []
        for section in grouped:
            try:
                out = summarizer(section, max_length=200, min_length=60, do_sample=False, truncation=True)
                section_summaries.append(out[0]["summary_text"])
            except Exception as e:
                print("Section summarization error:", e)

        final_input = " ".join(section_summaries)
        final_out = summarizer(final_input, max_length=250, min_length=80, do_sample=False, truncation=True)
        final_summary = final_out[0]["summary_text"]

    except Exception as e:
        print("❌ Summarization error:", e)
        raise HTTPException(status_code=500, detail=f"Summarization failed: {str(e)}")

    # --- Store in DB if username present ---
    if username:
        try:
            await db["summaries"].insert_one({
                "username": username,
                "summary": final_summary,
                "created_at": datetime.utcnow()
            })
        except Exception as e:
            print("DB insert error:", e)

    return {"summary": final_summary, "username": username}


@router.get("/previous/{username}")
async def get_previous(username: str):
    db = get_database()
    summaries = await db["summaries"].find({"username": username}).to_list(50)
    for s in summaries:
        s["_id"] = str(s["_id"])
    return summaries
