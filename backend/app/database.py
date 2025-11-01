from pymongo import MongoClient
from dotenv import load_dotenv
import os
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.collection import Collection

MONGO_URI = "mongodb://localhost:27017"
DB_NAME = "talkvault"

client: AsyncIOMotorClient | None = None
db = None

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")

client = MongoClient(MONGO_URI)
db = client["talkvault"]
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


# ✅ Get documents collection
def get_documents_collection() -> Collection:
    global db
    if db is None:
        raise RuntimeError("Database connection not initialized. Call connect_to_mongo() first.")
    return db["documents"]
def get_users_collection():
    if db is None:
        raise ConnectionError("❌ MongoDB not connected yet.")
    return db["users"]

def get_meetings_collection():
    if db is None:
        raise ConnectionError("❌ MongoDB not connected yet.")
    return db["meetings"]

def get_documents_collection():
    if db is None:
        raise ConnectionError("❌ MongoDB not connected yet.")
    return db["documents"]

def get_summaries_collection():
    if db is None:
        raise ConnectionError("❌ MongoDB not connected yet.")
    return db["summaries"]
