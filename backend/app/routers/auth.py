# backend/app/routers/auth.py

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from datetime import datetime, timedelta
from typing import Optional
import jwt
from passlib.context import CryptContext
from bson import ObjectId
from app.config import settings
from app.database import get_users_collection
from app.models.user import UserCreate, UserLogin, UserResponse, User

# --- Router and Security ---
router = APIRouter( tags=["Auth"])
security = HTTPBearer()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# --- Helper functions ---
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create JWT token"""
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


# --- Dependency ---
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify JWT and return user"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(credentials.credentials, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except jwt.PyJWTError:
        raise credentials_exception

    users_collection = get_users_collection()
    user = await users_collection.find_one({"_id": ObjectId(user_id)})
    if user is None:
        raise credentials_exception

    return user  # return dict, not Pydantic model (fixes serialization issues)


# --- Routes ---
@router.post("/register", response_model=dict)
async def register(user: UserCreate):
    """Register a new user"""
    users_collection = get_users_collection()

    # Check if user already exists
    if await users_collection.find_one({"email": user.email}):
        raise HTTPException(status_code=400, detail="User with this email already exists")
    if await users_collection.find_one({"username": user.username}):
        raise HTTPException(status_code=400, detail="Username already taken")

    # Hash password
    hashed_password = get_password_hash(user.password)
    user_dict = {
        "email": user.email,
        "username": user.username,
        "hashed_password": hashed_password,
        "full_name": user.full_name,
        "is_active": True,
        "is_verified": False,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
    }

    result = await users_collection.insert_one(user_dict)
    return {"message": "User registered successfully", "user_id": str(result.inserted_id)}


@router.post("/login", response_model=dict)
async def login(user_credentials: UserLogin):
    """Authenticate and return token"""
    users_collection = get_users_collection()
    user = await users_collection.find_one({"email": user_credentials.email})

    if not user or not verify_password(user_credentials.password, user["hashed_password"]):
        raise HTTPException(status_code=401, detail="Incorrect email or password")

    if not user.get("is_active"):
        raise HTTPException(status_code=400, detail="Inactive user")

    # Generate token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(data={"sub": str(user["_id"])}, expires_delta=access_token_expires)

    user_data = user.copy()
    user_data["id"] = str(user_data.pop("_id"))

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": UserResponse(**user_data),
    }


@router.get("/me", response_model=UserResponse)
async def read_users_me(current_user: dict = Depends(get_current_user)):
    """Get the current logged-in user's info"""
    user_dict = dict(current_user)
    if "_id" in user_dict and isinstance(user_dict["_id"], ObjectId):
        user_dict["_id"] = str(user_dict["_id"])
    return user_dict


@router.post("/logout")
async def logout():
    """Logout endpoint (client-side just deletes token)"""
    return {"message": "Successfully logged out"}
