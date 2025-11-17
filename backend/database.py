from motor.motor_asyncio import AsyncIOMotorClient
from config import settings
import logging

logger = logging.getLogger(__name__)

client = None
db = None


async def connect_to_mongo():
    global client, db
    try:
        client = AsyncIOMotorClient(settings.MONGO_URL)
        db = client[settings.DB_NAME]
        # Test connection
        await client.admin.command('ping')
        logger.info("Connected to MongoDB successfully")
        
        # Create indexes
        await create_indexes()
    except Exception as e:
        logger.error(f"Could not connect to MongoDB: {e}")
        raise


async def close_mongo_connection():
    global client
    if client:
        client.close()
        logger.info("Closed MongoDB connection")


async def get_db():
    return db


async def create_indexes():
    """Create database indexes for better performance"""
    try:
        # Users
        await db.users.create_index("email", unique=True)
        await db.users.create_index("id", unique=True)
        
        # API Keys
        await db.api_keys.create_index("key", unique=True)
        await db.api_keys.create_index("user_id")
        
        # OTP Store
        await db.otp_store.create_index("email")
        await db.otp_store.create_index("expires_at", expireAfterSeconds=0)
        
        # Email Verifications
        await db.email_verifications.create_index("user_id")
        await db.email_verifications.create_index("input")
        await db.email_verifications.create_index("verified_at")
        
        # Bulk Jobs
        await db.bulk_jobs.create_index("user_id")
        await db.bulk_jobs.create_index("status")
        
        # Blogs
        await db.blogs.create_index("slug", unique=True)
        await db.blogs.create_index("is_published")
        
        # Payments
        await db.payments.create_index("user_id")
        await db.payments.create_index("razorpay_order_id")
        
        logger.info("Database indexes created successfully")
    except Exception as e:
        logger.error(f"Error creating indexes: {e}")
