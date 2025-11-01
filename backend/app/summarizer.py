# backend/app/summarizer.py
from typing import Optional, Dict, Any
import os
import re
from cryptography.fernet import Fernet
from datetime import datetime
# Optional dependencies: openai, transformers (local summarizer)
try:
    import openai
except Exception:
    openai = None
try:
    from transformers import pipeline
except Exception:
    pipeline = None
from app.config import settings
# Initialize encryption
ENCRYPTION_KEY = os.getenv('PII_ENCRYPTION_KEY') or None
if ENCRYPTION_KEY:
    fernet = Fernet(ENCRYPTION_KEY.encode())
else:
    fernet = None
# Basic PII regexes (extend as needed)
PII_PATTERNS = {
    'email': r'[\w\.-]+@[\w\.-]+',
    'password_like': r"(?i)password\s*[:=]\s*\S+",
    'ssn': r'\b\d{3}-\d{2}-\d{4}\b',
    'credit_card': r'\b(?:\d[ -]*?){13,16}\b',
    'phone': r'\+?\d[\d\-() ]{7,}\d'
}
def detect_pii(text: str):
    matches = []
    for label, pattern in PII_PATTERNS.items():
        for m in re.finditer(pattern, text):
            matches.append({
                'label': label,
                'start': m.start(),
                'end': m.end(),
                'text': m.group(0)
                })
    return matches
def encrypt_pii_in_text(text: str):
    """Replace detected PII substrings with encrypted tokens and return
    mapping."""
    if not fernet:
        # return original text and empty map if no key provided
        return text, {}
    mapping = {}
    # To avoid overlapping index problems, process matches left->right
    matches = detect_pii(text)
    matches = sorted(matches, key=lambda x: x['start'])
    out = []
    last = 0
    for m in matches:
        out.append(text[last:m['start']])
        token = f"[PII:{m['label']}:{len(mapping)}]"
        encrypted = fernet.encrypt(m['text'].encode()).decode()
        mapping[token] = {'encrypted': encrypted, 'label': m['label']}
        out.append(token)
        last = m['end']
    out.append(text[last:])
    return ''.join(out), mapping
class Summarizer:
    def __init__(self):
        self.provider = os.getenv('SUMMARIZER_PROVIDER', 'openai')
        if self.provider == 'openai' and openai is None:
            raise RuntimeError('openai package not installed or OPENAI_API_KEY missing')
        if self.provider == 'local' and pipeline is None:
            raise RuntimeError('transformers not installed; install for local summarization')
        # initialize local pipeline lazily
        self._local_pipeline = None
    def _init_local(self):
        if self._local_pipeline is None:
            self._local_pipeline = pipeline('summarization', model='sshleifer/distilbart-cnn-12-6')
    def summarize(self, text: str, max_length: int = 200) -> Dict[str, Any]:
        """Return a summary dict: {text, model, created_at}"""
        provider = self.provider
        if provider == 'openai':
            openai.api_key = os.getenv('OPENAI_API_KEY')
            prompt = ("Summarize the following meeting transcript. Produce a clear concise summary with bullet points, action items, and decisions. "
                "Also identify any private information found and mark where it occurred using tokens.\n\n" + text)
            resp = openai.ChatCompletion.create(
                model=os.getenv('OPENAI_MODEL', 'gpt-4o-mini'),
                messages=[{'role': 'user', 'content': prompt}],
                temperature=0.2,
                max_tokens=800)
            summary_text = resp['choices'][0]['message']['content'].strip()
            return {'text': summary_text, 'model': 'openai', 'created_at':
datetime.utcnow().isoformat()}
        elif provider == 'local':
            self._init_local()
            # transformers summarizer expects shorter input — split if needed
            summary = self._local_pipeline(text, max_length=max_length,
min_length=30, do_sample=False)
            return {'text': summary[0]['summary_text'], 'model':
'local_transformers', 'created_at': datetime.utcnow().isoformat()}
        else:
            raise RuntimeError('Unknown summarizer provider')
# convenience singleton
summarizer = Summarizer()