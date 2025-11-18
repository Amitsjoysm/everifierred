from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from fastapi.responses import FileResponse
from datetime import datetime, timezone
from typing import List, Optional
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
    from utils import record_credit_transaction
    
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
    
    # Update credits
    await db.users.update_one(
        {"id": current_user.id},
        {"$inc": {"credits_used": 1}}
    )
    
    # Record transaction
    await record_credit_transaction(
        db=db,
        user_id=current_user.id,
        transaction_type="verification",
        credits_change=1,
        description=f"Single email verification: {request.email}",
        reference_id=result_dict.get('id')
    )
    
    return result


@router.post("/bulk", response_model=BulkVerificationJob)
async def verify_bulk_emails_endpoint(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user)
):
    """Upload file for bulk email verification"""
    db = await get_db()
    
    # Validate file size (max 10MB)
    content = await file.read()
    file_size_mb = len(content) / (1024 * 1024)
    
    if file_size_mb > 10:
        raise HTTPException(
            status_code=400, 
            detail=f"File too large ({file_size_mb:.2f}MB). Maximum size is 10MB"
        )
    
    # Validate file type
    if not (file.filename.endswith('.csv') or 
            file.filename.endswith(('.xlsx', '.xls')) or 
            file.filename.endswith('.txt')):
        raise HTTPException(
            status_code=400, 
            detail="Unsupported file type. Use CSV, Excel (.xlsx, .xls), or TXT"
        )
    
    # Extract emails
    try:
        if file.filename.endswith('.csv'):
            emails = extract_emails_from_csv(content)
        elif file.filename.endswith(('.xlsx', '.xls')):
            emails = extract_emails_from_excel(content)
        elif file.filename.endswith('.txt'):
            emails = extract_emails_from_text(content.decode('utf-8'))
    except Exception as e:
        raise HTTPException(
            status_code=400, 
            detail=f"Error reading file: {str(e)}"
        )
    
    if not emails:
        raise HTTPException(status_code=400, detail="No valid emails found in file")
    
    # Remove duplicates
    emails = list(set(emails))
    
    # Validate email count
    if len(emails) > 10000:
        raise HTTPException(
            status_code=400,
            detail=f"Too many emails ({len(emails)}). Maximum 10,000 emails per job"
        )
    
    # Check if user has sufficient credits
    if current_user.credits_used + len(emails) > current_user.credits_limit:
        raise HTTPException(
            status_code=403,
            detail=f"Insufficient credits. Need {len(emails)}, available {current_user.credits_limit - current_user.credits_used}. Please upgrade your plan."
        )
    
    # Check for concurrent jobs
    active_jobs = await db.bulk_jobs.count_documents({
        "user_id": current_user.id,
        "status": {"$in": [VerificationStatus.PENDING, VerificationStatus.PROCESSING]}
    })
    
    if active_jobs >= 3:
        raise HTTPException(
            status_code=429,
            detail="Too many active jobs. Please wait for existing jobs to complete."
        )
    
    # Create job
    job = BulkVerificationJob(
        user_id=current_user.id,
        total_emails=len(emails),
        status=VerificationStatus.PENDING
    )
    job_dict = job.model_dump()
    job_dict['created_at'] = job_dict['created_at'].isoformat()
    await db.bulk_jobs.insert_one(job_dict)
    
    # Start background task
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


@router.get("/template")
async def download_template():
    """Download template file for bulk email verification"""
    import openpyxl
    from config import settings
    
    # Create template file
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Email Template"
    
    # Add instructions
    ws['A1'] = "MailGuard - Bulk Email Verification Template"
    ws['A1'].font = openpyxl.styles.Font(bold=True, size=14)
    
    ws['A3'] = "Instructions:"
    ws['A3'].font = openpyxl.styles.Font(bold=True)
    ws['A4'] = "1. Add one email address per row in column A (starting from row 8)"
    ws['A5'] = "2. You can add up to 10,000 email addresses"
    ws['A6'] = "3. Save the file and upload it to MailGuard for verification"
    
    # Add header row
    ws['A8'] = "Email Address"
    ws['A8'].font = openpyxl.styles.Font(bold=True)
    ws['A8'].fill = openpyxl.styles.PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
    ws['A8'].font = openpyxl.styles.Font(bold=True, color="FFFFFF")
    
    # Add sample emails
    sample_emails = [
        "example1@domain.com",
        "example2@domain.com",
        "example3@domain.com"
    ]
    
    for idx, email in enumerate(sample_emails, start=9):
        ws[f'A{idx}'] = email
        ws[f'A{idx}'].font = openpyxl.styles.Font(italic=True, color="999999")
    
    # Set column width
    ws.column_dimensions['A'].width = 40
    
    # Save template
    template_path = settings.RESULTS_DIR / "email_verification_template.xlsx"
    wb.save(template_path)
    
    return FileResponse(
        template_path,
        filename="email_verification_template.xlsx",
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )



@router.get("/history", response_model=List[EmailVerificationResult])
async def get_verification_history(
    current_user: User = Depends(get_current_active_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100)
):
    """Get user's verification history with pagination"""
    db = await get_db()
    
    verifications = await db.email_verifications.find(
        {"user_id": current_user.id},
        {"_id": 0}
    ).sort("verified_at", -1).skip(skip).limit(limit).to_list(limit)
    
    for verification in verifications:
        if isinstance(verification.get('verified_at'), str):
            verification['verified_at'] = datetime.fromisoformat(verification['verified_at'])
    
    return [EmailVerificationResult(**v) for v in verifications]


@router.get("/stats")
async def get_verification_stats(current_user: User = Depends(get_current_active_user)):
    """Get user's verification statistics and credit usage"""
    db = await get_db()
    
    # Get current user data
    user_data = await db.users.find_one({"id": current_user.id}, {"_id": 0})
    
    # Get total verifications
    total_verifications = await db.email_verifications.count_documents({"user_id": current_user.id})
    
    # Get verifications this month
    month_start = datetime.now(timezone.utc).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    verifications_this_month = await db.email_verifications.count_documents({
        "user_id": current_user.id,
        "verified_at": {"$gte": month_start.isoformat()}
    })
    
    # Get bulk jobs count
    total_bulk_jobs = await db.bulk_jobs.count_documents({"user_id": current_user.id})
    completed_bulk_jobs = await db.bulk_jobs.count_documents({
        "user_id": current_user.id,
        "status": VerificationStatus.COMPLETED
    })
    
    # Calculate credit usage percentage
    credits_used = user_data.get('credits_used', 0)
    credits_limit = user_data.get('credits_limit', 100)
    credit_usage_percentage = (credits_used / credits_limit * 100) if credits_limit > 0 else 0
    
    return {
        "credits_used": credits_used,
        "credits_limit": credits_limit,
        "credits_remaining": credits_limit - credits_used,
        "credit_usage_percentage": round(credit_usage_percentage, 2),
        "total_verifications": total_verifications,
        "verifications_this_month": verifications_this_month,
        "total_bulk_jobs": total_bulk_jobs,
        "completed_bulk_jobs": completed_bulk_jobs,
        "current_plan": user_data.get('plan', 'free')
    }


@router.post("/job/{job_id}/cancel")
async def cancel_verification_job(
    job_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """Cancel a pending or processing bulk verification job"""
    db = await get_db()
    
    job = await db.bulk_jobs.find_one({"id": job_id, "user_id": current_user.id})
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    if job['status'] not in [VerificationStatus.PENDING, VerificationStatus.PROCESSING]:
        raise HTTPException(
            status_code=400, 
            detail=f"Cannot cancel job with status: {job['status']}"
        )
    
    # Update job status to cancelled
    await db.bulk_jobs.update_one(
        {"id": job_id},
        {
            "$set": {
                "status": "cancelled",
                "completed_at": datetime.now(timezone.utc).isoformat()
            }
        }
    )
    
    return {"message": "Job cancelled successfully"}



@router.get("/credit-history")
async def get_credit_history(
    current_user: User = Depends(get_current_active_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100)
):
    """Get user's credit transaction history"""
    from models import CreditTransaction
    
    db = await get_db()
    
    transactions = await db.credit_transactions.find(
        {"user_id": current_user.id},
        {"_id": 0}
    ).sort("created_at", -1).skip(skip).limit(limit).to_list(limit)
    
    for transaction in transactions:
        if isinstance(transaction.get('created_at'), str):
            transaction['created_at'] = datetime.fromisoformat(transaction['created_at'])
    
    return transactions

    credits_limit = user_data.get('credits_limit', 100)
    credit_usage_percentage = (credits_used / credits_limit * 100) if credits_limit > 0 else 0
    
    return {
        "credits_used": credits_used,
        "credits_limit": credits_limit,
        "credits_remaining": credits_limit - credits_used,
        "credit_usage_percentage": round(credit_usage_percentage, 2),
        "total_verifications": total_verifications,
        "verifications_this_month": verifications_this_month,
        "total_bulk_jobs": total_bulk_jobs,
        "completed_bulk_jobs": completed_bulk_jobs,
        "current_plan": user_data.get('plan', 'free')
    }
