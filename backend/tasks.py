from celery_app import celery_app
from email_verifier import verify_single_email
from motor.motor_asyncio import AsyncIOMotorClient
from config import settings
from models import VerificationStatus
import asyncio
import logging
from datetime import datetime, timezone
import openpyxl
from pathlib import Path
from collections import defaultdict
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


def get_db_sync():
    """Get database connection for Celery tasks"""
    client = AsyncIOMotorClient(settings.MONGO_URL)
    return client[settings.DB_NAME]


def extract_domain(email: str) -> str:
    """Extract domain from email address"""
    try:
        return email.split('@')[1].lower() if '@' in email else ''
    except:
        return ''


@celery_app.task(bind=True, name='tasks.verify_bulk_emails')
def verify_bulk_emails(self, job_id: str, emails: list, user_id: str):
    """Background task to verify bulk emails with domain-based rate limiting"""
    logger.info(f"Starting bulk verification job: {job_id}")
    
    async def process_emails():
        db = get_db_sync()
        
        try:
            # Update job status to processing
            await db.bulk_jobs.update_one(
                {"id": job_id},
                {"$set": {"status": VerificationStatus.PROCESSING}}
            )
            
            # Initialize results array with same length as emails to maintain order
            results = [None] * len(emails)
            processed = 0
            successful = 0
            failed = 0
            
            # Track last verification time per domain for rate limiting
            domain_last_verify = {}
            
            for index, email in enumerate(emails):
                try:
                    # Extract domain for rate limiting
                    domain = extract_domain(email)
                    
                    # Add delay if same domain was recently verified
                    if domain and domain in domain_last_verify:
                        # Wait 2 seconds between requests to same domain
                        time_since_last = asyncio.get_event_loop().time() - domain_last_verify[domain]
                        if time_since_last < 2.0:
                            await asyncio.sleep(2.0 - time_since_last)
                    
                    # Verify email
                    result = await verify_single_email(email)
                    
                    # Record verification time for this domain
                    if domain:
                        domain_last_verify[domain] = asyncio.get_event_loop().time()
                    
                    if result:
                        # Store individual result
                        result_dict = result.model_dump()
                        result_dict['verified_at'] = result_dict['verified_at'].isoformat()
                        result_dict['user_id'] = user_id
                        result_dict['job_id'] = job_id
                        
                        await db.email_verifications.insert_one(result_dict)
                        results[index] = result_dict  # Store at original index
                        successful += 1
                    else:
                        failed += 1
                        results[index] = {
                            "input": email,
                            "error": "Verification failed"
                        }
                    
                    processed += 1
                    
                    # Update progress
                    await db.bulk_jobs.update_one(
                        {"id": job_id},
                        {
                            "$set": {
                                "processed_emails": processed,
                                "successful": successful,
                                "failed": failed
                            }
                        }
                    )
                    
                    # Update task progress
                    self.update_state(
                        state='PROGRESS',
                        meta={'current': processed, 'total': len(emails)}
                    )
                    
                except Exception as e:
                    logger.error(f"Error verifying email {email}: {e}")
                    failed += 1
                    processed += 1
                    results[index] = {
                        "input": email,
                        "error": str(e)
                    }
            
            # Create Excel file with results
            result_file = create_result_excel(job_id, results)
            
            # Update job as completed
            await db.bulk_jobs.update_one(
                {"id": job_id},
                {
                    "$set": {
                        "status": VerificationStatus.COMPLETED,
                        "processed_emails": processed,
                        "successful": successful,
                        "failed": failed,
                        "result_url": result_file,
                        "completed_at": datetime.now(timezone.utc).isoformat()
                    }
                }
            )
            
            # Update user credits
            await db.users.update_one(
                {"id": user_id},
                {"$inc": {"credits_used": processed}}
            )
            
            # Record credit transaction
            from utils import record_credit_transaction
            await record_credit_transaction(
                db=db,
                user_id=user_id,
                transaction_type="bulk_job",
                credits_change=processed,
                description=f"Bulk email verification job ({processed} emails)",
                reference_id=job_id
            )
            
            logger.info(f"Bulk verification job {job_id} completed. Processed: {processed}, Successful: {successful}, Failed: {failed}")
            
        except Exception as e:
            logger.error(f"Bulk verification job {job_id} failed: {e}")
            await db.bulk_jobs.update_one(
                {"id": job_id},
                {
                    "$set": {
                        "status": VerificationStatus.FAILED,
                        "error_message": str(e)
                    }
                }
            )
    
    # Run async function
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(process_emails())
    loop.close()
    
    return {'job_id': job_id, 'status': 'completed'}


def create_result_excel(job_id: str, results: list) -> str:
    """Create Excel file with verification results maintaining original order"""
    try:
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Verification Results"
        
        # Headers
        headers = [
            "Email", "Is Reachable", "Confidence Score", "Valid Syntax",
            "Is Disposable", "Is Role Account", "Can Connect SMTP",
            "Is Deliverable", "Has Full Inbox", "Is Catch All",
            "Is Disabled", "Accepts Mail", "Domain", "Username",
            "Normalized Email", "MX Records", "Verified At"
        ]
        ws.append(headers)
        
        # Data - iterate through results in order (including None entries)
        for result in results:
            if result is None:
                # Handle case where verification didn't complete
                ws.append(["", "PENDING", "", "", "", "", "", "", "", "", "", "", "", "", "", "", ""])
            elif "error" in result:
                # Handle error case
                ws.append([result.get("input", ""), "ERROR", "", "", "", "", "", "", "", "", "", "", "", "", "", "", result.get("error", "")])
            else:
                # Handle successful verification
                ws.append([
                    result.get("input", ""),
                    result.get("is_reachable", ""),
                    result.get("confidence_score", ""),
                    result.get("is_valid_syntax", ""),
                    result.get("is_disposable", ""),
                    result.get("is_role_account", ""),
                    result.get("can_connect_smtp", ""),
                    result.get("is_deliverable", ""),
                    result.get("has_full_inbox", ""),
                    result.get("is_catch_all", ""),
                    result.get("is_disabled", ""),
                    result.get("accepts_mail", ""),
                    result.get("domain", ""),
                    result.get("username", ""),
                    result.get("normalized_email", ""),
                    ", ".join(result.get("mx_records", [])),
                    result.get("verified_at", "")
                ])
        
        # Save file
        result_path = settings.RESULTS_DIR / f"{job_id}.xlsx"
        wb.save(result_path)
        
        return str(result_path)
    except Exception as e:
        logger.error(f"Error creating Excel file: {e}")
        return ""


@celery_app.task(name='tasks.cleanup_expired_otps')
def cleanup_expired_otps():
    """Periodic task to clean up expired OTPs"""
    async def cleanup():
        db = get_db_sync()
        result = await db.otp_store.delete_many({
            "expires_at": {"$lt": datetime.now(timezone.utc).isoformat()}
        })
        logger.info(f"Cleaned up {result.deleted_count} expired OTPs")
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(cleanup())
    loop.close()
