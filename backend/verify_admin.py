"""
Verify admin account setup
"""

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from config import settings


async def verify_admin():
    """Verify admin account is properly configured"""
    client = AsyncIOMotorClient(settings.MONGO_URL)
    db = client[settings.DB_NAME]
    
    email = "admin@mailguard.com"
    
    # Get admin user
    admin = await db.users.find_one({"email": email}, {"_id": 0})
    
    if not admin:
        print("❌ Admin user not found!")
        client.close()
        return
    
    print("\n" + "="*60)
    print("ADMIN ACCOUNT VERIFICATION")
    print("="*60)
    print(f"\nEmail:           {admin['email']}")
    print(f"Full Name:       {admin['full_name']}")
    print(f"Role:            {admin['role']}")
    print(f"Is Active:       {admin['is_active']}")
    print(f"Is Verified:     {admin['is_verified']}")
    print(f"Plan:            {admin['plan']}")
    print(f"Credits Limit:   {admin['credits_limit']}")
    print(f"Credits Used:    {admin['credits_used']}")
    print(f"2FA Enabled:     {admin['two_fa_enabled']}")
    
    # Check if everything is correct
    issues = []
    
    if not admin['is_active']:
        issues.append("Account is not active")
    
    if not admin['is_verified']:
        issues.append("Email is not verified")
    
    if admin['role'] != 'super_admin':
        issues.append("Role is not super_admin")
    
    if issues:
        print("\n⚠️  ISSUES FOUND:")
        for issue in issues:
            print(f"  - {issue}")
        
        # Fix issues
        print("\n🔧 Fixing issues...")
        await db.users.update_one(
            {"email": email},
            {
                "$set": {
                    "is_active": True,
                    "is_verified": True,
                    "role": "super_admin"
                }
            }
        )
        print("✅ All issues fixed!")
    else:
        print("\n✅ Admin account is properly configured!")
    
    print("\n" + "="*60)
    print("LOGIN CREDENTIALS")
    print("="*60)
    print(f"\nEmail:    admin@mailguard.com")
    print(f"Password: Admin@123456")
    print("\nLogin URL:")
    print("https://emailverify-sync.preview.emergentagent.com/login")
    print("\nAdmin Panel URL:")
    print("https://emailverify-sync.preview.emergentagent.com/admin")
    print("="*60 + "\n")
    
    client.close()


if __name__ == "__main__":
    asyncio.run(verify_admin())
