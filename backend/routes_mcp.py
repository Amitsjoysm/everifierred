"""
MCP (Model Context Protocol) Server Routes
These routes allow LLMs to use MailGuard as a tool for email verification
"""

from fastapi import APIRouter, HTTPException, Header
from typing import Optional, List
from pydantic import BaseModel, EmailStr
import logging

from email_verifier import verify_single_email
from database import get_db
from models import EmailVerificationResult

router = APIRouter(prefix="/mcp", tags=["MCP"])
logger = logging.getLogger(__name__)


class MCPVerifyRequest(BaseModel):
    """MCP verification request"""
    email: EmailStr
    api_key: Optional[str] = None


class MCPBulkVerifyRequest(BaseModel):
    """MCP bulk verification request"""
    emails: List[EmailStr]
    api_key: Optional[str] = None


class MCPCapabilities(BaseModel):
    """MCP server capabilities"""
    name: str = "MailGuard Email Verifier"
    version: str = "1.0.0"
    description: str = "Professional email verification service for validating email addresses"
    capabilities: List[str] = [
        "verify_single_email",
        "verify_bulk_emails",
        "check_disposable",
        "validate_syntax",
        "smtp_verification",
        "mx_record_check"
    ]


@router.get("/capabilities", response_model=MCPCapabilities)
async def get_mcp_capabilities():
    """
    Get MCP server capabilities
    This endpoint describes what the MCP server can do
    """
    return MCPCapabilities()


@router.post("/verify")
async def mcp_verify_email(
    request: MCPVerifyRequest,
    x_api_key: Optional[str] = Header(None)
):
    """
    Verify a single email address via MCP
    
    This endpoint allows LLMs to verify email addresses as a tool.
    Requires API key authentication.
    """
    # Get API key from header or request body
    api_key = x_api_key or request.api_key
    
    if not api_key:
        raise HTTPException(
            status_code=401,
            detail="API key required. Provide via X-API-Key header or api_key field"
        )
    
    # Validate API key
    db = await get_db()
    api_key_doc = await db.api_keys.find_one({"key": api_key, "is_active": True})
    
    if not api_key_doc:
        raise HTTPException(status_code=401, detail="Invalid or inactive API key")
    
    # Verify email
    try:
        result = await verify_single_email(request.email)
        
        if not result:
            raise HTTPException(status_code=500, detail="Verification failed")
        
        # Update API key usage
        await db.api_keys.update_one(
            {"key": api_key},
            {
                "$inc": {"calls_count": 1},
                "$set": {"last_used": result.verified_at.isoformat()}
            }
        )
        
        # Update user credits
        await db.users.update_one(
            {"id": api_key_doc['user_id']},
            {"$inc": {"credits_used": 1, "api_calls_count": 1}}
        )
        
        # Store verification result
        result_dict = result.model_dump()
        result_dict['verified_at'] = result_dict['verified_at'].isoformat()
        result_dict['user_id'] = api_key_doc['user_id']
        result_dict['api_key_id'] = api_key_doc['id']
        result_dict['source'] = 'mcp'
        
        await db.email_verifications.insert_one(result_dict)
        
        return {
            "success": True,
            "email": request.email,
            "result": result.model_dump(),
            "message": f"Email verified successfully. Confidence: {result.confidence_score}%"
        }
        
    except Exception as e:
        logger.error(f"MCP verification error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/verify-bulk")
async def mcp_verify_bulk_emails(
    request: MCPBulkVerifyRequest,
    x_api_key: Optional[str] = Header(None)
):
    """
    Verify multiple email addresses via MCP
    
    This endpoint allows LLMs to verify multiple emails in one request.
    Requires API key authentication.
    """
    # Get API key from header or request body
    api_key = x_api_key or request.api_key
    
    if not api_key:
        raise HTTPException(
            status_code=401,
            detail="API key required. Provide via X-API-Key header or api_key field"
        )
    
    # Validate API key
    db = await get_db()
    api_key_doc = await db.api_keys.find_one({"key": api_key, "is_active": True})
    
    if not api_key_doc:
        raise HTTPException(status_code=401, detail="Invalid or inactive API key")
    
    # Limit bulk size
    if len(request.emails) > 100:
        raise HTTPException(
            status_code=400,
            detail="Maximum 100 emails per request. Use async bulk verification for larger lists."
        )
    
    # Verify emails
    results = []
    successful = 0
    failed = 0
    
    for email in request.emails:
        try:
            result = await verify_single_email(email)
            if result:
                results.append({
                    "email": email,
                    "success": True,
                    "result": result.model_dump()
                })
                successful += 1
                
                # Store verification result
                result_dict = result.model_dump()
                result_dict['verified_at'] = result_dict['verified_at'].isoformat()
                result_dict['user_id'] = api_key_doc['user_id']
                result_dict['api_key_id'] = api_key_doc['id']
                result_dict['source'] = 'mcp_bulk'
                
                await db.email_verifications.insert_one(result_dict)
            else:
                results.append({
                    "email": email,
                    "success": False,
                    "error": "Verification failed"
                })
                failed += 1
        except Exception as e:
            results.append({
                "email": email,
                "success": False,
                "error": str(e)
            })
            failed += 1
    
    # Update API key and user stats
    await db.api_keys.update_one(
        {"key": api_key},
        {"$inc": {"calls_count": len(request.emails)}}
    )
    
    await db.users.update_one(
        {"id": api_key_doc['user_id']},
        {"$inc": {"credits_used": successful, "api_calls_count": len(request.emails)}}
    )
    
    return {
        "success": True,
        "total": len(request.emails),
        "successful": successful,
        "failed": failed,
        "results": results
    }


@router.get("/info")
async def mcp_server_info():
    """
    Get MCP server information
    This endpoint provides information about how to use the MCP server
    """
    return {
        "name": "MailGuard MCP Server",
        "version": "1.0.0",
        "description": "Email verification service accessible to LLMs via MCP",
        "endpoints": {
            "/mcp/capabilities": "Get server capabilities",
            "/mcp/verify": "Verify a single email",
            "/mcp/verify-bulk": "Verify multiple emails (max 100)",
            "/mcp/info": "Get server information"
        },
        "authentication": {
            "type": "API Key",
            "methods": [
                "X-API-Key header",
                "api_key field in request body"
            ],
            "how_to_get": "Sign up at the platform and generate an API key from your dashboard"
        },
        "usage_example": {
            "verify_single": {
                "method": "POST",
                "url": "/api/mcp/verify",
                "headers": {
                    "X-API-Key": "your_api_key_here",
                    "Content-Type": "application/json"
                },
                "body": {
                    "email": "test@example.com"
                }
            }
        },
        "rate_limits": {
            "single_verification": "Based on your plan credits",
            "bulk_verification": "Max 100 emails per request"
        }
    }
