from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime, timezone

from database import get_db
from models import EmailVerificationRequest, EmailVerificationResult
from auth import verify_api_key
from email_verifier import verify_single_email

router = APIRouter(prefix="/external", tags=["External API"])


@router.post("/verify", response_model=EmailVerificationResult)
async def external_verify_email(
    request: EmailVerificationRequest,
    api_key_data: dict = Depends(verify_api_key)
):
    """External API: Verify single email using API key"""
    db = await get_db()
    
    user = await db.users.find_one({"id": api_key_data['user_id']})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if user['credits_used'] >= user['credits_limit']:
        raise HTTPException(status_code=403, detail="Credit limit exceeded")
    
    result = await verify_single_email(request.email)
    if not result:
        raise HTTPException(status_code=500, detail="Email verification failed")
    
    result_dict = result.model_dump()
    result_dict['verified_at'] = result_dict['verified_at'].isoformat()
    result_dict['user_id'] = user['id']
    await db.email_verifications.insert_one(result_dict)
    
    await db.users.update_one(
        {"id": user['id']},
        {"$inc": {"credits_used": 1, "api_calls_count": 1}}
    )
    
    return result


@router.post("/mcp/verify")
async def mcp_verify_email(
    request: EmailVerificationRequest,
    api_key_data: dict = Depends(verify_api_key)
):
    """MCP Server: Verify email for LLM integration"""
    db = await get_db()
    
    user = await db.users.find_one({"id": api_key_data['user_id']})
    if not user or user['credits_used'] >= user['credits_limit']:
        return {
            "error": "Credit limit exceeded",
            "status": "failed"
        }
    
    result = await verify_single_email(request.email)
    if not result:
        return {
            "error": "Verification failed",
            "status": "failed"
        }
    
    result_dict = result.model_dump()
    result_dict['verified_at'] = result_dict['verified_at'].isoformat()
    result_dict['user_id'] = user['id']
    await db.email_verifications.insert_one(result_dict)
    
    await db.users.update_one(
        {"id": user['id']},
        {"$inc": {"credits_used": 1, "api_calls_count": 1}}
    )
    
    return {
        "email": result.input,
        "is_valid": result.is_reachable == "safe",
        "confidence_score": result.confidence_score,
        "is_deliverable": result.is_deliverable,
        "is_disposable": result.is_disposable,
        "status": "success"
    }
