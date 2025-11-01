# uvicorn app.main:app --reload
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import auth, summarizer
from app.database import connect_to_mongo, close_mongo_connection

app = FastAPI(title="TalkVault API")

# CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # You can restrict later
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# Connect to MongoDB on startup
@app.on_event("startup")
async def startup_event():
    await connect_to_mongo()

@app.on_event("shutdown")
async def shutdown_event():
    await close_mongo_connection()

# Routers
app.include_router(auth.router, prefix="/api/auth", tags=["Auth"])
app.include_router(summarizer.router, prefix="/api/summarizer", tags=["Summarizer"])
@app.get("/meetings")
async def get_meetings(limit: int = 5):
    return {"meetings": []}

@app.get("/documents")
async def get_documents(limit: int = 5):
    return {"documents": []}

@app.get("/api")
async def root():
    return {"message": "TalkVault API is live!"}
