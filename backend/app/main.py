# backend/app/main.py
# uvicorn app.main:app --reload
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import uvicorn

from app.config import settings
from app.database import connect_to_db, close_db_connection
from app.routers import auth, users, meetings, documents, summarizer

app = FastAPI(
    title="TalkVault API",
    description="AI-powered meeting management and document processing platform",
    version="1.0.0"
)

# ✅ CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173", 
        "http://127.0.0.1:5173"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ Mount uploads folder
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# ✅ Include routers with consistent prefix
# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["authentication"])
app.include_router(users.router, prefix="/api/users", tags=["users"])
app.include_router(meetings.router, prefix="/api/meetings", tags=["meetings"])
app.include_router(documents.router, prefix="/api/documents", tags=["documents"])
app.include_router(summarizer.router, prefix="/api", tags=["summarizer"])


# ✅ Startup & shutdown events
@app.on_event("startup")
async def startup_event():
    await connect_to_db()
    print("Connected to MongoDB")

@app.on_event("shutdown")
async def shutdown_event():
    await close_db_connection()
    print("Disconnected from MongoDB")

@app.get("/")
async def root():
    return {"message": "TalkVault API is running"}

@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "version": "1.0.0"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
