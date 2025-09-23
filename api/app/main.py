"""
Talk Vault - Main FastAPI Application
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from contextlib import asynccontextmanager

from app.core.config import settings
from app.api.v1.endpoints import auth, meetings, upload


@asynccontextmanager
async def lifespan(app: FastAPI):
    # MongoDB does not require explicit table creation
    # Optionally, add MongoDB connection checks here if needed
    yield
    # Optionally add cleanup/shutdown logic here


app = FastAPI(
    title="Talk Vault API",
    description="AI-powered meeting summarization system",
    version="1.0.0",
    lifespan=lifespan
)


# Set up CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_HOSTS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Include API routers with their prefixes and tags
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(meetings.router, prefix="/api/v1/meetings", tags=["Meetings"])
app.include_router(upload.router, prefix="/api/v1/upload", tags=["Upload"])


@app.get("/")
async def root():
    return {"message": "Talk Vault API is running"}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
