"""
Authentication endpoints with MongoDB
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from datetime import timedelta

from app.db.dbmongo import db  # MongoDB client instance
from app.schemas.schemas import UserCreate, UserLogin, Token, UserResponse
from app.core.security import verify_password, get_password_hash, create_access_token, verify_token
from app.core.config import settings

router = APIRouter()
security = HTTPBearer()

@router.post("/signup", response_model=Token)
async def signup(user_data: UserCreate):
    # Check if user exists by email
    existing_user = await db.users.find_one({"email": user_data.email})
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # Check if username taken
    existing_username = await db.users.find_one({"username": user_data.username})
    if existing_username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already taken"
        )

    hashed_password = get_password_hash(user_data.password)

    user_doc = {
        "email": user_data.email,
        "username": user_data.username,
        "full_name": user_data.full_name,
        "hashed_password": hashed_password,
        "is_active": True
    }
    result = await db.users.insert_one(user_doc)

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user_data.email}, expires_delta=access_token_expires
    )

    user_response = UserResponse(
        id=str(result.inserted_id),
        email=user_data.email,
        username=user_data.username,
        full_name=user_data.full_name,
        is_active=True
    )

    return Token(
        access_token=access_token,
        token_type="bearer",
        user=user_response
    )


@router.post("/login", response_model=Token)
async def login(user_credentials: UserLogin):
    user = await db.users.find_one({"email": user_credentials.email})

    if not user or not verify_password(user_credentials.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )

    if not user.get("is_active", True):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["email"]}, expires_delta=access_token_expires
    )

    user_response = UserResponse(
        id=str(user["_id"]),
        email=user["email"],
        username=user["username"],
        full_name=user.get("full_name"),
        is_active=user.get("is_active", True)
    )

    return Token(
        access_token=access_token,
        token_type="bearer",
        user=user_response
    )


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> UserResponse:
    token = credentials.credentials
    payload = verify_token(token)

    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials"
        )

    email: str = payload.get("sub")
    if email is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials"
        )

    user = await db.users.find_one({"email": email})
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )

    return UserResponse(
        id=str(user["_id"]),
        email=user["email"],
        username=user["username"],
        full_name=user.get("full_name"),
        is_active=user.get("is_active", True)
    )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: UserResponse = Depends(get_current_user)):
    return current_user
