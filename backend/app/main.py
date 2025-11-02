# uvicorn app.main:app --reload

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import connect_to_mongo, close_mongo_connection
from app.routers import auth, summarizer, history,meetings,frontend_meetings, analytics


app = FastAPI(title="TalkVault API")

# CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Lifespan events
@app.on_event("startup")
async def startup_db_client():
    await connect_to_mongo()

@app.on_event("shutdown")
async def shutdown_db_client():
    await close_mongo_connection()

# include routers
app.include_router(auth.router, prefix="/api/auth", tags=["Auth"])
app.include_router(summarizer.router, prefix="/api", tags=["Summarizer"])
app.include_router(meetings.router, prefix="/api", tags=["Meetings"])  # ✅ only one router for meetings
app.include_router(analytics.router, prefix="/api", tags=["Analytics"])
app.include_router(history.router, prefix="/api", tags=["History"])

@app.get("/api")
async def root():
    return {"message": "TalkVault API is live!"}