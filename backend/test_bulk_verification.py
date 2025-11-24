"""
Test bulk verification to ensure it's working
"""

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from config import settings
from tasks import verify_bulk_emails
import uuid

async def test_bulk_verification():
    """Test bulk verification with a small job"""
    client = AsyncIOMotorClient(settings.MONGO_URL)
    db = client[settings.DB_NAME]
    
    # Get a test user (the superadmin we created)
    user = await db.users.find_one({"email": "amits.joys@gmail.com"})
    
    if not user:
        print("❌ Test user not found!")
        client.close()
        return
    
    print(f"✅ Found test user: {user['email']}")
    print(f"   Credits: {user.get('credits_limit', 0) - user.get('credits_used', 0)} available")
    
    # Create a test job
    job_id = str(uuid.uuid4())
    test_emails = ["test1@example.com", "test2@example.com"]
    
    job = {
        "id": job_id,
        "user_id": user["id"],
        "total_emails": len(test_emails),
        "processed_emails": 0,
        "successful": 0,
        "failed": 0,
        "status": "pending",
        "created_at": asyncio.get_event_loop().time(),
        "result_url": None
    }
    
    await db.bulk_jobs.insert_one(job)
    print(f"\n✅ Created test job: {job_id}")
    
    # Trigger the Celery task
    print(f"🚀 Triggering Celery task...")
    result = verify_bulk_emails.delay(job_id, test_emails, user["id"])
    print(f"✅ Task queued: {result.id}")
    
    # Wait a bit for processing
    print("\n⏳ Waiting for task to complete (10 seconds)...")
    await asyncio.sleep(10)
    
    # Check job status
    updated_job = await db.bulk_jobs.find_one({"id": job_id})
    
    if updated_job:
        print(f"\n📊 Job Status:")
        print(f"   Status: {updated_job.get('status', 'unknown')}")
        print(f"   Total emails: {updated_job.get('total_emails', 0)}")
        print(f"   Processed: {updated_job.get('processed_emails', 0)}")
        print(f"   Successful: {updated_job.get('successful', 0)}")
        print(f"   Failed: {updated_job.get('failed', 0)}")
        print(f"   Result file: {updated_job.get('result_url', 'Not generated')}")
        
        if updated_job.get('status') == 'completed':
            print("\n✅ BULK VERIFICATION IS WORKING!")
        elif updated_job.get('status') == 'processing':
            print("\n⏳ Job still processing... (this is normal for larger jobs)")
        elif updated_job.get('status') == 'failed':
            print(f"\n❌ Job failed: {updated_job.get('error_message', 'Unknown error')}")
        else:
            print(f"\n⚠️  Job status: {updated_job.get('status', 'unknown')}")
    else:
        print("\n❌ Job not found after processing!")
    
    client.close()

if __name__ == "__main__":
    print("="*60)
    print("TESTING BULK EMAIL VERIFICATION")
    print("="*60)
    asyncio.run(test_bulk_verification())
    print("="*60)
