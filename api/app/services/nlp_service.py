import asyncio
from datetime import datetime
import os
from bson import ObjectId

# Import or adjust sys.path for NLP modules as before
import sys
sys.path.append('..')

from nlp.src.talkvault_nlp.summarizer import MeetingSummarizer
from nlp.src.talkvault_nlp.action_extractor import ActionExtractor
from nlp.src.talkvault_nlp.pii_redactor import PIIRedactor

class NLPProcessor:
    def __init__(self):
        self.summarizer = MeetingSummarizer()
        self.action_extractor = ActionExtractor()
        self.pii_redactor = PIIRedactor()
    
    async def process_meeting(self, meeting_id: str, file_path: str, file_type: str, db):
        """Process meeting file through NLP pipeline"""
        try:
            oid = ObjectId(meeting_id)
            # Update status to processing
            await db.meetings.update_one({"_id": oid}, {"$set": {"status": "processing"}})

            # Read content
            content = await self._read_file_content(file_path, file_type)

            # Process NLP pipeline asynchronously
            summary = await self.summarizer.summarize(content)
            action_items = await self.action_extractor.extract_actions(content)
            redacted_content = await self.pii_redactor.redact_pii(content)

            # Update meeting with results
            await db.meetings.update_one(
                {"_id": oid},
                {
                    "$set": {
                        "transcript": content,
                        "summary": summary,
                        "action_items": action_items,
                        "redacted_content": redacted_content,
                        "status": "completed",
                        "processed_at": datetime.utcnow()
                    }
                }
            )
        except Exception as e:
            oid = ObjectId(meeting_id)
            await db.meetings.update_one({"_id": oid}, {"$set": {"status": "failed"}})
            raise e
    
    async def _read_file_content(self, file_path: str, file_type: str) -> str:
        """Read content from file based on type"""
        if file_type == "text":
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        elif file_type == "audio":
            # Placeholder for speech-to-text integration
            return "This is a placeholder transcript for audio file processing. Implement speech-to-text integration here."
        else:
            raise ValueError(f"Unsupported file type: {file_type}")

# Global processor instance
nlp_processor = NLPProcessor()

async def process_meeting_async(meeting_id: str, file_path: str, file_type: str, db):
    """Async wrapper for meeting processing"""
    await nlp_processor.process_meeting(meeting_id, file_path, file_type, db)
