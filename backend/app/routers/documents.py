# backend/app/routers/documents.py

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from fastapi.responses import FileResponse
from typing import List, Optional
from bson import ObjectId
from datetime import datetime
import os
import uuid
import mimetypes

from app.config import settings
from app.database import get_documents_collection
from app.models.document import DocumentCreate, DocumentUpdate, DocumentResponse, DocumentSearch, DocumentType, ProcessingStatus
from app.models.user import User
from app.routers.auth import get_current_user

router = APIRouter()

def get_document_type(filename: str) -> DocumentType:
    """Determine document type based on file extension"""
    ext = os.path.splitext(filename)[1].lower()
    
    if ext in ['.pdf']:
        return DocumentType.PDF
    elif ext in ['.doc', '.docx']:
        return DocumentType.WORD
    elif ext in ['.txt']:
        return DocumentType.TEXT
    elif ext in ['.mp3', '.wav', '.m4a', '.aac']:
        return DocumentType.AUDIO
    elif ext in ['.mp4', '.avi', '.mov', '.mkv']:
        return DocumentType.VIDEO
    else:
        return DocumentType.OTHER

async def save_uploaded_file(file: UploadFile) -> tuple:
    """Save uploaded file and return file info"""
    # Create uploads directory if it doesn't exist
    uploads_dir = "uploads"
    os.makedirs(uploads_dir, exist_ok=True)
    
    # Generate unique filename
    file_ext = os.path.splitext(file.filename)[1]
    unique_filename = f"{uuid.uuid4()}{file_ext}"
    file_path = os.path.join(uploads_dir, unique_filename)
    
    # Save file
    with open(file_path, "wb") as buffer:
        content = await file.read()
        buffer.write(content)
    
    file_size = len(content)
    mime_type = mimetypes.guess_type(file.filename)[0] or "application/octet-stream"
    
    return unique_filename, file_path, file_size, mime_type

@router.post("/upload", response_model=DocumentResponse)
async def upload_document(
    file: UploadFile = File(...),
    title: Optional[str] = None,
    description: Optional[str] = None,
    meeting_id: Optional[str] = None,
    tags: Optional[str] = None,
    is_public: bool = False,
    current_user: User = Depends(get_current_user)
):
    """Upload a new document"""
    # Validate file size
    if file.size and file.size > settings.MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File size exceeds maximum allowed size of {settings.MAX_FILE_SIZE} bytes"
        )
    
    # Validate file type
    file_ext = os.path.splitext(file.filename)[1].lower()
    if file_ext not in settings.ALLOWED_FILE_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type {file_ext} not allowed. Allowed types: {', '.join(settings.ALLOWED_FILE_TYPES)}"
        )
    
    # Validate meeting_id if provided
    if meeting_id and not ObjectId.is_valid(meeting_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid meeting ID"
        )
    
    try:
        # Save file
        filename, file_path, file_size, mime_type = await save_uploaded_file(file)
        
        # Parse tags
        tag_list = [tag.strip() for tag in tags.split(",")] if tags else []
        
        # Create document record
        documents_collection = get_documents_collection()
        document_dict = {
            "filename": filename,
            "original_filename": file.filename,
            "file_path": file_path,
            "file_size": file_size,
            "file_type": get_document_type(file.filename),
            "mime_type": mime_type,
            "owner_id": str(current_user.id),
            "meeting_id": meeting_id,
            "title": title or file.filename,
            "description": description,
            "tags": tag_list,
            "is_public": is_public,
            "processing_status": ProcessingStatus.PENDING,
            "keywords": [],
            "metadata": {},
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        result = await documents_collection.insert_one(document_dict)
        
        # Get created document
        created_document = await documents_collection.find_one({"_id": result.inserted_id})
        return DocumentResponse(**created_document, id=str(created_document["_id"]))
        
    except Exception as e:
        # Clean up file if document creation failed
        if 'file_path' in locals() and os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload document: {str(e)}"
        )

@router.get("/", response_model=List[DocumentResponse])
async def get_documents(
    skip: int = 0,
    limit: int = 50,
    meeting_id: Optional[str] = None,
    file_type: Optional[DocumentType] = None,
    current_user: User = Depends(get_current_user)
):
    """Get documents for current user"""
    documents_collection = get_documents_collection()
    
    # Base filter: user's documents or public documents
    filter_query = {
        "$or": [
            {"owner_id": str(current_user.id)},
            {"is_public": True}
        ]
    }
    
    # Add optional filters
    if meeting_id:
        filter_query["meeting_id"] = meeting_id
    if file_type:
        filter_query["file_type"] = file_type
    
    cursor = documents_collection.find(filter_query).sort("created_at", -1).skip(skip).limit(limit)
    documents = []
    async for document in cursor:
        documents.append(DocumentResponse(**document, id=str(document["_id"])))
    
    return documents

@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get document by ID"""
    if not ObjectId.is_valid(document_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid document ID"
        )
    
    documents_collection = get_documents_collection()
    document = await documents_collection.find_one({"_id": ObjectId(document_id)})
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    # Check if user has access
    if document["owner_id"] != str(current_user.id) and not document.get("is_public", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this document"
        )
    
    return DocumentResponse(**document, id=str(document["_id"]))

@router.get("/{document_id}/download")
async def download_document(
    document_id: str,
    current_user: User = Depends(get_current_user)
):
    """Download document file"""
    if not ObjectId.is_valid(document_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid document ID"
        )
    
    documents_collection = get_documents_collection()
    document = await documents_collection.find_one({"_id": ObjectId(document_id)})
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    # Check if user has access
    if document["owner_id"] != str(current_user.id) and not document.get("is_public", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this document"
        )
    
    file_path = document["file_path"]
    if not os.path.exists(file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found on server"
        )
    
    return FileResponse(
        path=file_path,
        filename=document["original_filename"],
        media_type=document["mime_type"]
    )

@router.put("/{document_id}", response_model=DocumentResponse)
async def update_document(
    document_id: str,
    document_update: DocumentUpdate,
    current_user: User = Depends(get_current_user)
):
    """Update document metadata (owner only)"""
    if not ObjectId.is_valid(document_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid document ID"
        )
    
    documents_collection = get_documents_collection()
    document = await documents_collection.find_one({"_id": ObjectId(document_id)})
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    # Check if user is owner
    if document["owner_id"] != str(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only document owner can update the document"
        )
    
    # Prepare update data
    update_data = {"updated_at": datetime.utcnow()}
    
    if document_update.title is not None:
        update_data["title"] = document_update.title
    if document_update.description is not None:
        update_data["description"] = document_update.description
    if document_update.content is not None:
        update_data["content"] = document_update.content
    if document_update.summary is not None:
        update_data["summary"] = document_update.summary
    if document_update.keywords is not None:
        update_data["keywords"] = document_update.keywords
    if document_update.processing_status is not None:
        update_data["processing_status"] = document_update.processing_status
    if document_update.processing_error is not None:
        update_data["processing_error"] = document_update.processing_error
    if document_update.tags is not None:
        update_data["tags"] = document_update.tags
    if document_update.is_public is not None:
        update_data["is_public"] = document_update.is_public
    
    await documents_collection.update_one(
        {"_id": ObjectId(document_id)},
        {"$set": update_data}
    )
    
    # Get updated document
    updated_document = await documents_collection.find_one({"_id": ObjectId(document_id)})
    return DocumentResponse(**updated_document, id=str(updated_document["_id"]))

@router.delete("/{document_id}")
async def delete_document(
    document_id: str,
    current_user: User = Depends(get_current_user)
):
    """Delete document (owner only)"""
    if not ObjectId.is_valid(document_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid document ID"
        )
    
    documents_collection = get_documents_collection()
    document = await documents_collection.find_one({"_id": ObjectId(document_id)})
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    # Check if user is owner
    if document["owner_id"] != str(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only document owner can delete the document"
        )
    
    # Delete file from filesystem
    file_path = document["file_path"]
    if os.path.exists(file_path):
        os.remove(file_path)
    
    # Delete document record
    await documents_collection.delete_one({"_id": ObjectId(document_id)})
    return {"message": "Document deleted successfully"}

@router.post("/search", response_model=List[DocumentResponse])
async def search_documents(
    search: DocumentSearch,
    skip: int = 0,
    limit: int = 50,
    current_user: User = Depends(get_current_user)
):
    """Search documents"""
    documents_collection = get_documents_collection()
    
    # Base filter: user's documents or public documents
    filter_query = {
        "$or": [
            {"owner_id": str(current_user.id)},
            {"is_public": True}
        ]
    }
    
    # Text search
    if search.query:
        filter_query["$and"] = [{
            "$or": [
                {"title": {"$regex": search.query, "$options": "i"}},
                {"description": {"$regex": search.query, "$options": "i"}},
                {"content": {"$regex": search.query, "$options": "i"}},
                {"keywords": {"$in": [search.query]}},
                {"tags": {"$in": [search.query]}}
            ]
        }]
    
    # Additional filters
    if search.file_type:
        filter_query["file_type"] = search.file_type
    if search.tags:
        filter_query["tags"] = {"$in": search.tags}
    if search.meeting_id:
        filter_query["meeting_id"] = search.meeting_id
    if search.owner_id:
        filter_query["owner_id"] = search.owner_id
    
    cursor = documents_collection.find(filter_query).sort("created_at", -1).skip(skip).limit(limit)
    documents = []
    async for document in cursor:
        documents.append(DocumentResponse(**document, id=str(document["_id"])))
    
    return documents
