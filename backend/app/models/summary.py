from mongoengine import Document, StringField, DateTimeField
from datetime import datetime

class Summary(Document):
    username = StringField(required=True)
    original_text = StringField(required=True)
    summary_text = StringField(required=True)
    created_at = DateTimeField(default=datetime.utcnow)
