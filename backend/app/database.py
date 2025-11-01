# backend/app/database.py

from motor.motor_asyncio import AsyncIOMotorClient
from app.config import settings
import logging
from motor.motor_asyncio import AsyncIOMotorClient
import os
from typing import Optional

_db_client: Optional[AsyncIOMotorClient] = None
_db = None
async def connect_to_db():
    global _db_client, _db
    mongo_uri = os.getenv('MONGO_URI') or 'mongodb://localhost:27017'
    _db_client = AsyncIOMotorClient(mongo_uri)
    _db = _db_client[os.getenv('MONGO_DB_NAME','talkvault')]
async def close_db_connection():
    global _db_client
    if _db_client:
        _db_client.close()
def get_documents_collection():
    return _db['documents'] 
logger = logging.getLogger(__name__)
def get_summaries_collection():
    return _db['summaries']
class MongoDB:
    client: AsyncIOMotorClient = None
    database = None

db = MongoDB()

async def connect_to_db():
    """Create database connection"""
    try:
        db.client = AsyncIOMotorClient(settings.MONGODB_URL)
        db.database = db.client[settings.DATABASE_NAME]
        
        # Test the connection
        await db.client.admin.command('ismaster')
        logger.info(f"Connected to MongoDB at {settings.MONGODB_URL}")
        
    except Exception as e:
        logger.error(f"Could not connect to MongoDB: {e}")
        raise e

async def close_db_connection():
    """Close database connection"""
    if db.client:
        db.client.close()
        logger.info("Disconnected from MongoDB")

def get_database():
    """Get database instance"""
    return db.database

# Collection getters
def get_users_collection():
    return db.database.users

def get_meetings_collection():
    return db.database.meetings

def get_documents_collection():
    return db.database.documents