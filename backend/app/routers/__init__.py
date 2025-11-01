# backend/app/routers/__init__.py
"""
Expose all routers from this package so that
`from app.routers import auth, users, meetings, documents, summarizer`
works reliably.
"""

from . import auth, users, meetings, documents, summarizer

__all__ = ["auth", "users", "meetings", "documents", "summarizer"]
