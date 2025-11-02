from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.collection import Collection
from dotenv import load_dotenv
import os

# ✅ Load environment variables
load_dotenv()

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DB_NAME = os.getenv("DB_NAME", "talkvault")

# Global client and db
client: AsyncIOMotorClient | None = None
db = None


# ✅ Connect to MongoDB
async def connect_to_mongo():
    global client, db
    client = AsyncIOMotorClient(MONGO_URI)
    db = client[DB_NAME]
    print("✅ Connected to MongoDB")


# ✅ Disconnect from MongoDB
async def close_mongo_connection():
    global client
    if client:
        client.close()
        print("❌ MongoDB connection closed")


# ✅ "get_db" — for compatibility with routers expecting a DB dependency
def get_db():
    global db
    if db is None:
        raise ConnectionError("❌ MongoDB not connected yet. Call connect_to_mongo() first.")
    return db


# ✅ Collection getters
def get_users_collection() -> Collection:
    return get_db()["users"]

def get_meetings_collection() -> Collection:
    return get_db()["meetings"]

def get_documents_collection() -> Collection:
    return get_db()["documents"]

def get_summaries_collection() -> Collection:
    return get_db()["summaries"]
