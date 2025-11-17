from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime
from typing import List

from database import get_db
from models import User, APIKey, APIKeyCreate, APIKeyResponse
from auth import get_current_active_user, generate_api_key

router = APIRouter(prefix="/api-keys", tags=["API Keys"])


@router.post("", response_model=APIKeyResponse)
async def create_api_key(
    data: APIKeyCreate,
    current_user: User = Depends(get_current_active_user)
):
    """Create new API key"""
    db = await get_db()
    
    key = generate_api_key()
    
    api_key = APIKey(
        user_id=current_user.id,
        key=key,
        name=data.name
    )
    api_key_dict = api_key.model_dump()
    api_key_dict['created_at'] = api_key_dict['created_at'].isoformat()
    
    await db.api_keys.insert_one(api_key_dict)
    
    return APIKeyResponse(**api_key_dict)


@router.get("", response_model=List[APIKeyResponse])
async def get_api_keys(current_user: User = Depends(get_current_active_user)):
    """Get user's API keys"""
    db = await get_db()
    
    keys = await db.api_keys.find({"user_id": current_user.id}).to_list(100)
    
    for key in keys:
        if isinstance(key.get('created_at'), str):
            key['created_at'] = datetime.fromisoformat(key['created_at'])
        if key.get('last_used') and isinstance(key.get('last_used'), str):
            key['last_used'] = datetime.fromisoformat(key['last_used'])
    
    return [APIKeyResponse(**key) for key in keys]


@router.delete("/{key_id}")
async def delete_api_key(
    key_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """Delete API key"""
    db = await get_db()
    
    result = await db.api_keys.delete_one({"id": key_id, "user_id": current_user.id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="API key not found")
    
    return {"message": "API key deleted successfully"}
