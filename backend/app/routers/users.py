# backend/app/routers/users.py

from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from bson import ObjectId
from datetime import datetime

from app.database import get_users_collection
from app.models.user import UserResponse, UserUpdate, User
from app.routers.auth import get_current_user

router = APIRouter()

@router.get("/", response_model=List[UserResponse])
async def get_users(
    skip: int = 0, 
    limit: int = 50,
    current_user: User = Depends(get_current_user)
):
    """Get all users (admin only or public profiles)"""
    users_collection = get_users_collection()
    
    cursor = users_collection.find({"is_active": True}).skip(skip).limit(limit)
    users = []
    async for user in cursor:
        users.append(UserResponse(**user, id=str(user["_id"])))
    
    return users

@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get user by ID"""
    users_collection = get_users_collection()
    
    if not ObjectId.is_valid(user_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user ID"
        )
    
    user = await users_collection.find_one({"_id": ObjectId(user_id)})
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return UserResponse(**user, id=str(user["_id"]))

@router.put("/me", response_model=UserResponse)
async def update_current_user(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_user)
):
    """Update current user's profile"""
    users_collection = get_users_collection()
    
    update_data = {}
    if user_update.email is not None:
        # Check if email is already taken by another user
        existing_user = await users_collection.find_one({
            "email": user_update.email,
            "_id": {"$ne": current_user.id}
        })
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already in use"
            )
        update_data["email"] = user_update.email
    
    if user_update.username is not None:
        # Check if username is already taken by another user
        existing_user = await users_collection.find_one({
            "username": user_update.username,
            "_id": {"$ne": current_user.id}
        })
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already taken"
            )
        update_data["username"] = user_update.username
    
    if user_update.full_name is not None:
        update_data["full_name"] = user_update.full_name
    
    if user_update.is_active is not None:
        update_data["is_active"] = user_update.is_active
    
    if update_data:
        update_data["updated_at"] = datetime.utcnow()
        await users_collection.update_one(
            {"_id": current_user.id},
            {"$set": update_data}
        )
    
    # Get updated user
    updated_user = await users_collection.find_one({"_id": current_user.id})
    return UserResponse(**updated_user, id=str(updated_user["_id"]))

@router.delete("/me")
async def delete_current_user(current_user: User = Depends(get_current_user)):
    """Delete current user's account"""
    users_collection = get_users_collection()
    
    # Soft delete by setting is_active to False
    await users_collection.update_one(
        {"_id": current_user.id},
        {"$set": {"is_active": False, "updated_at": datetime.utcnow()}}
    )
    
    return {"message": "Account successfully deleted"}

@router.get("/search/{query}", response_model=List[UserResponse])
async def search_users(
    query: str,
    skip: int = 0,
    limit: int = 20,
    current_user: User = Depends(get_current_user)
):
    """Search users by username or full name"""
    users_collection = get_users_collection()
    
    search_filter = {
        "$and": [
            {"is_active": True},
            {
                "$or": [
                    {"username": {"$regex": query, "$options": "i"}},
                    {"full_name": {"$regex": query, "$options": "i"}}
                ]
            }
        ]
    }
    
    cursor = users_collection.find(search_filter).skip(skip).limit(limit)
    users = []
    async for user in cursor:
        users.append(UserResponse(**user, id=str(user["_id"])))
    
    return users
