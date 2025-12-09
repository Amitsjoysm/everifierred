"""
Create a custom super admin user
"""

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from passlib.context import CryptContext
from datetime import datetime, timezone
from config import settings
import uuid
import sys

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


async def create_custom_admin(email: str, password: str, full_name: str = "Super Admin"):
    """Create a custom super admin user"""
    client = AsyncIOMotorClient(settings.MONGO_URL)
    db = client[settings.DB_NAME]
    
    # Check if user already exists
    existing = await db.users.find_one({"email": email})
    if existing:
        print(f"\n⚠️  User with email {email} already exists!")
        print(f"\n✅ Updating password for existing user...")
        
        # Update password
        hashed_password = pwd_context.hash(password)
        await db.users.update_one(
            {"email": email},
            {
                "$set": {
                    "hashed_password": hashed_password,
                    "role": "super_admin",
                    "is_active": True,
                    "is_verified": True,
                    "plan": "enterprise",
                    "credits_limit": 25000,
                    "updated_at": datetime.now(timezone.utc).isoformat()
                }
            }
        )
        print(f"\n✅ Password updated successfully for {email}!")
    else:
        # Hash password
        hashed_password = pwd_context.hash(password)
        
        # Create admin user
        admin_user = {
            "id": str(uuid.uuid4()),
            "email": email,
            "full_name": full_name,
            "role": "super_admin",
            "is_active": True,
            "is_verified": True,
            "plan": "enterprise",
            "credits_used": 0,
            "credits_limit": 25000,
            "api_calls_count": 0,
            "hashed_password": hashed_password,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "last_login": None,
            "two_fa_enabled": False,
            "two_fa_secret": None
        }
        
        await db.users.insert_one(admin_user)
        print(f"\n✅ Super Admin user created successfully!")
    
    print("\n" + "="*60)
    print("SUPER ADMIN CREDENTIALS")
    print("="*60)
    print(f"\nEmail:    {email}")
    print(f"Password: {password}")
    print(f"Role:     super_admin")
    print(f"Plan:     Enterprise")
    print(f"Credits:  25,000")
    print("\n" + "="*60)
    print("\nYou can now login at:")
    print("https://razorpay-integration.preview.emergentagent.com/login")
    print("\nAccess Admin Panel at:")
    print("https://razorpay-integration.preview.emergentagent.com/admin")
    print("="*60 + "\n")
    
    client.close()


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python create_custom_admin.py <email> <password>")
        sys.exit(1)
    
    email = sys.argv[1]
    password = sys.argv[2]
    
    asyncio.run(create_custom_admin(email, password))
