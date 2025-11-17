from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import FileResponse
from datetime import datetime, timezone
from typing import List
from pathlib import Path

from database import get_db
from models import (
    User, EmailVerificationRequest, EmailVerificationResult,
    BulkVerificationJob, VerificationStatus
)
from auth import get_current_active_user, verify_api_key
from email_verifier import verify_single_email
from utils import extract_emails_from_csv, extract_emails_from_excel, extract_emails_from_text
from tasks import verify_bulk_emails

router = APIRouter(prefix="/verify", tags=["Email Verification"])


@router.post("/single", response_model=EmailVerificationResult)
async def verify_email_endpoint(
    request: EmailVerificationRequest,
    current_user: User = Depends(get_current_active_user)
):
    """Verify a single email address"""
    db = await get_db()
    
    if current_user.credits_used >= current_user.credits_limit:
        raise HTTPException(status_code=403, detail="Credit limit exceeded. Please upgrade your plan")
    
    result = await verify_single_email(request.email)
    if not result:
        raise HTTPException(status_code=500, detail="Email verification failed")
    
    result_dict = result.model_dump()
    result_dict['verified_at'] = result_dict['verified_at'].isoformat()
    result_dict['user_id'] = current_user.id
    await db.email_verifications.insert_one(result_dict)
    
    await db.users.update_one(
        {"id": current_user.id},
        {"$inc": {"credits_used": 1}}
    )
    
    return result


@router.post("/bulk", response_model=BulkVerificationJob)
async def verify_bulk_emails_endpoint(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user)
):
    """Upload file for bulk email verification"""
    db = await get_db()
    
    content = await file.read()
    
    if file.filename.endswith('.csv'):
        emails = extract_emails_from_csv(content)
    elif file.filename.endswith(('.xlsx', '.xls')):
        emails = extract_emails_from_excel(content)
    elif file.filename.endswith('.txt'):
        emails = extract_emails_from_text(content.decode('utf-8'))
    else:
        raise HTTPException(status_code=400, detail="Unsupported file type. Use CSV, Excel, or TXT")
    
    if not emails:
        raise HTTPException(status_code=400, detail="No valid emails found in file")
    
    emails = list(set(emails))
    
    if current_user.credits_used + len(emails) > current_user.credits_limit:
        raise HTTPException(
            status_code=403,
            detail=f"Insufficient credits. Need {len(emails)}, available {current_user.credits_limit - current_user.credits_used}"
        )
    
    job = BulkVerificationJob(
        user_id=current_user.id,
        total_emails=len(emails),
        status=VerificationStatus.PENDING
    )
    job_dict = job.model_dump()
    job_dict['created_at'] = job_dict['created_at'].isoformat()
    await db.bulk_jobs.insert_one(job_dict)
    
    verify_bulk_emails.delay(job.id, emails, current_user.id)
    
    return job


@router.get("/jobs", response_model=List[BulkVerificationJob])
async def get_verification_jobs(
    current_user: User = Depends(get_current_active_user)
):
    """Get user's bulk verification jobs"""
    db = await get_db()
    
    jobs = await db.bulk_jobs.find({"user_id": current_user.id}).sort("created_at", -1).to_list(100)
    
    for job in jobs:
        if isinstance(job.get('created_at'), str):
            job['created_at'] = datetime.fromisoformat(job['created_at'])
        if job.get('completed_at') and isinstance(job['completed_at'], str):
            job['completed_at'] = datetime.fromisoformat(job['completed_at'])
    
    return [BulkVerificationJob(**job) for job in jobs]


@router.get("/job/{job_id}", response_model=BulkVerificationJob)
async def get_verification_job(
    job_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """Get specific bulk verification job"""
    db = await get_db()
    
    job = await db.bulk_jobs.find_one({"id": job_id, "user_id": current_user.id})
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    if isinstance(job.get('created_at'), str):
        job['created_at'] = datetime.fromisoformat(job['created_at'])
    if job.get('completed_at') and isinstance(job['completed_at'], str):
        job['completed_at'] = datetime.fromisoformat(job['completed_at'])
    
    return BulkVerificationJob(**job)


@router.get("/download/{job_id}")
async def download_verification_results(
    job_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """Download verification results"""
    db = await get_db()
    
    job = await db.bulk_jobs.find_one({"id": job_id, "user_id": current_user.id})
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    if job['status'] != VerificationStatus.COMPLETED:
        raise HTTPException(status_code=400, detail="Job not completed yet")
    
    result_file = job.get('result_url')
    if not result_file or not Path(result_file).exists():
        raise HTTPException(status_code=404, detail="Result file not found")
    
    return FileResponse(
        result_file,
        filename=f"verification_results_{job_id}.xlsx",
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
