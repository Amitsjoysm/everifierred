"""
Create a super admin user for testing
"""

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from passlib.context import CryptContext
from datetime import datetime, timezone
from config import settings
import uuid

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


async def create_admin_user():
    """Create a super admin user"""
    client = AsyncIOMotorClient(settings.MONGO_URL)
    db = client[settings.DB_NAME]
    
    # Admin credentials
    email = "amits.joys@gmail.com"
    password = "Admin@123"
    full_name = "Super Admin"
    
    # Check if admin already exists
    existing = await db.users.find_one({"email": email})
    if existing:
        # Update existing user to be super_admin with correct plan
        await db.users.update_one(
            {"email": email},
            {"$set": {
                "role": "super_admin",
                "plan": "enterprise",
                "credits_limit": 25000,
                "is_active": True,
                "is_verified": True,
                "hashed_password": pwd_context.hash(password),
                "updated_at": datetime.now(timezone.utc).isoformat()
            }}
        )
        print(f"\n✅  Admin user updated!")
        print(f"\nEmail: {email}")
        print(f"Password: {password}")
        print(f"Role: super_admin")
        print(f"Plan: enterprise")
        client.close()
        return
    
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
    
    print("\n✅ Super Admin user created successfully!")
    print("\n" + "="*50)
    print("ADMIN CREDENTIALS")
    print("="*50)
    print(f"\nEmail:    {email}")
    print(f"Password: {password}")
    print(f"Role:     super_admin")
    print(f"Plan:     Enterprise")
    print("\n" + "="*50)
    print("\nYou can now login at:")
    print("https://login-repair-82.preview.emergentagent.com/login")
    print("\nAccess Admin Panel at:")
    print("https://login-repair-82.preview.emergentagent.com/admin")
    print("="*50 + "\n")
    
    client.close()


if __name__ == "__main__":
    asyncio.run(create_admin_user())
