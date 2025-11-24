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
import uuid

logger = logging.getLogger(__name__)


def get_db_sync():
    """Get database connection for Celery tasks"""
    client = AsyncIOMotorClient(settings.MONGO_URL)
    return client[settings.DB_NAME]


@celery_app.task(bind=True, name='tasks.verify_bulk_emails')
def verify_bulk_emails(self, job_id: str, emails: list, user_id: str):
    """Background task to verify bulk emails"""
    logger.info(f"Starting bulk verification job: {job_id}")
    
    async def process_emails():
        db = get_db_sync()
        
        try:
            # Update job status to processing
            await db.bulk_jobs.update_one(
                {"id": job_id},
                {"$set": {"status": VerificationStatus.PROCESSING}}
            )
            
            results = []
            processed = 0
            successful = 0
            failed = 0
            
            for email in emails:
                try:
                    # Verify email
                    result = await verify_single_email(email)
                    
                    if result:
                        # Store individual result
                        result_dict = result.model_dump()
                        result_dict['verified_at'] = result_dict['verified_at'].isoformat()
                        result_dict['user_id'] = user_id
                        result_dict['job_id'] = job_id
                        
                        await db.email_verifications.insert_one(result_dict)
                        results.append(result_dict)
                        successful += 1
                    else:
                        failed += 1
                        results.append({
                            "input": email,
                            "error": "Verification failed"
                        })
                    
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
                    results.append({
                        "input": email,
                        "error": str(e)
                    })
            
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
            credit_transaction = {
                "id": str(uuid.uuid4()),
                "user_id": user_id,
                "transaction_type": "bulk_job",
                "credits_change": processed,
                "balance_after": 0,  # Will be updated in next query
                "description": f"Bulk email verification job ({processed} emails)",
                "reference_id": job_id,
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            
            # Get updated balance
            user = await db.users.find_one({"id": user_id})
            if user:
                credit_transaction["balance_after"] = user.get("credits_limit", 0) - user.get("credits_used", 0)
            
            await db.credit_transactions.insert_one(credit_transaction)
            
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
    """Create Excel file with verification results"""
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
        
        # Data
        for result in results:
            if "error" in result:
                ws.append([result.get("input", ""), "ERROR", "", "", "", "", "", "", "", "", "", "", "", "", "", "", ""])
            else:
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
