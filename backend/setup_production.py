"""
Production Setup Script
- Create Super Admin
- Seed Plans
- Create Razorpay Subscription Plans (optional)
"""
import asyncio
import sys
from motor.motor_asyncio import AsyncIOMotorClient
from passlib.context import CryptContext
from datetime import datetime, timezone
import razorpay
from config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

async def create_super_admin():
    """Create super admin account"""
    client = AsyncIOMotorClient(settings.MONGO_URL)
    db = client[settings.DB_NAME]
    
    # Check if admin exists
    existing = await db.users.find_one({"email": "amits.joys@gmail.com"})
    if existing:
        print("✓ Super Admin already exists")
        client.close()
        return existing
    
    admin_user = {
        "id": "admin-001",
        "email": "amits.joys@gmail.com",
        "full_name": "Super Admin",
        "hashed_password": pwd_context.hash("Admin@123"),
        "role": "super_admin",
        "is_active": True,
        "is_verified": True,
        "plan": "enterprise",
        "credits_used": 0,
        "credits_limit": 25000,
        "api_calls_count": 0,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.users.insert_one(admin_user)
    print("✓ Super Admin created successfully")
    print(f"  Email: amits.joys@gmail.com")
    print(f"  Password: Admin@123")
    
    client.close()
    return admin_user


async def seed_plans():
    """Seed pricing plans"""
    client = AsyncIOMotorClient(settings.MONGO_URL)
    db = client[settings.DB_NAME]
    
    # Check if plans exist
    existing_count = await db.plans.count_documents({})
    if existing_count > 0:
        print(f"✓ Plans already exist ({existing_count} plans)")
        client.close()
        return
    
    plans = [
        {
            "id": "plan-free",
            "name": "Free Plan",
            "type": "free",
            "credits_limit": 100,
            "price": 0,
            "price_usd": 0,
            "currency": "INR",
            "billing_cycle": "monthly",
            "razorpay_plan_id": None,
            "razorpay_plan_id_inr": None,
            "razorpay_plan_id_usd": None,
            "is_recurring": False,
            "features": [
                "100 Email Verifications",
                "Basic Email Validation",
                "API Access",
                "Email Support"
            ],
            "is_active": True,
            "created_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": "plan-starter",
            "name": "Starter Plan",
            "type": "starter",
            "credits_limit": 1000,
            "price": 499,
            "price_usd": 6,
            "currency": "INR",
            "billing_cycle": "monthly",
            "razorpay_plan_id": None,
            "razorpay_plan_id_inr": None,
            "razorpay_plan_id_usd": None,
            "is_recurring": False,
            "features": [
                "1,000 Email Verifications",
                "Advanced Validation",
                "API Access",
                "Bulk Upload",
                "Priority Email Support",
                "Usage Analytics"
            ],
            "is_active": True,
            "created_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": "plan-professional",
            "name": "Professional Plan",
            "type": "professional",
            "credits_limit": 5000,
            "price": 1999,
            "price_usd": 24,
            "currency": "INR",
            "billing_cycle": "monthly",
            "razorpay_plan_id": None,
            "razorpay_plan_id_inr": None,
            "razorpay_plan_id_usd": None,
            "is_recurring": False,
            "features": [
                "5,000 Email Verifications",
                "Advanced Validation",
                "API Access",
                "Bulk Upload",
                "Priority Support",
                "Usage Analytics",
                "Webhook Integration",
                "Custom Rate Limits"
            ],
            "is_active": True,
            "created_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": "plan-enterprise",
            "name": "Enterprise Plan",
            "type": "enterprise",
            "credits_limit": 25000,
            "price": 7999,
            "price_usd": 96,
            "currency": "INR",
            "billing_cycle": "monthly",
            "razorpay_plan_id": None,
            "razorpay_plan_id_inr": None,
            "razorpay_plan_id_usd": None,
            "is_recurring": False,
            "features": [
                "25,000 Email Verifications",
                "Advanced Validation",
                "Unlimited API Access",
                "Bulk Upload",
                "24/7 Priority Support",
                "Advanced Analytics",
                "Webhook Integration",
                "Custom Rate Limits",
                "Dedicated Account Manager",
                "SLA Guarantee"
            ],
            "is_active": True,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
    ]
    
    await db.plans.insert_many(plans)
    print(f"✓ Seeded {len(plans)} plans successfully")
    
    client.close()


async def create_razorpay_plans():
    """Create Razorpay subscription plans (optional)"""
    if not settings.RAZORPAY_KEY_ID or not settings.RAZORPAY_KEY_SECRET:
        print("⚠ Razorpay credentials not configured. Skipping Razorpay plan creation.")
        return
    
    print("\n🔑 Creating Razorpay Subscription Plans...")
    print(f"Using Key: {settings.RAZORPAY_KEY_ID}")
    
    razorpay_client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
    client = AsyncIOMotorClient(settings.MONGO_URL)
    db = client[settings.DB_NAME]
    
    plans_to_create = await db.plans.find({"price": {"$gt": 0}}, {"_id": 0}).to_list(100)
    
    for plan in plans_to_create:
        try:
            # Create INR plan
            print(f"\n  Creating Razorpay plan for: {plan['name']}")
            
            razorpay_plan_data = {
                "period": "monthly",
                "interval": 1,
                "item": {
                    "name": plan['name'],
                    "amount": int(plan['price'] * 100),  # Convert to paise
                    "currency": "INR",
                    "description": f"{plan['name']} - {plan['credits_limit']} credits"
                },
                "notes": {
                    "plan_id": plan['id'],
                    "plan_type": plan['type'],
                    "credits": str(plan['credits_limit'])
                }
            }
            
            rz_plan = razorpay_client.plan.create(data=razorpay_plan_data)
            
            # Update plan with Razorpay plan ID
            await db.plans.update_one(
                {"id": plan['id']},
                {
                    "$set": {
                        "razorpay_plan_id_inr": rz_plan['id'],
                        "is_recurring": True
                    }
                }
            )
            
            print(f"    ✓ Created Razorpay Plan ID: {rz_plan['id']}")
            
        except Exception as e:
            print(f"    ✗ Failed to create Razorpay plan for {plan['name']}: {str(e)}")
    
    client.close()


async def display_status():
    """Display current setup status"""
    client = AsyncIOMotorClient(settings.MONGO_URL)
    db = client[settings.DB_NAME]
    
    print("\n" + "="*70)
    print("PRODUCTION SETUP STATUS")
    print("="*70)
    
    # Admin status
    admin = await db.users.find_one({"email": "amits.joys@gmail.com"})
    print("\n👤 SUPER ADMIN:")
    if admin:
        print(f"  ✓ Email: amits.joys@gmail.com")
        print(f"  ✓ Password: Admin@123")
        print(f"  ✓ Role: {admin['role']}")
        print(f"  ✓ Credits: {admin['credits_limit']}")
    else:
        print("  ✗ Not created")
    
    # Plans status
    print("\n📦 PRICING PLANS:")
    plans = await db.plans.find({}, {"_id": 0}).to_list(100)
    for plan in plans:
        print(f"\n  {plan['name']} ({plan['type']})")
        print(f"    Price: ₹{plan['price']} / ${plan.get('price_usd', 0)}")
        print(f"    Credits: {plan['credits_limit']}")
        print(f"    Razorpay Plan ID (INR): {plan.get('razorpay_plan_id_inr', 'Not linked')}")
        print(f"    Recurring: {plan.get('is_recurring', False)}")
    
    # Razorpay status
    print("\n💳 RAZORPAY CONFIGURATION:")
    print(f"  Key ID: {settings.RAZORPAY_KEY_ID}")
    print(f"  Key Secret: {'*' * len(settings.RAZORPAY_KEY_SECRET) if settings.RAZORPAY_KEY_SECRET else 'Not set'}")
    print(f"  Status: {'✓ Configured' if settings.RAZORPAY_KEY_ID and settings.RAZORPAY_KEY_SECRET else '✗ Not configured'}")
    
    print("\n" + "="*70)
    print("NEXT STEPS:")
    print("="*70)
    print("1. Login to admin panel: https://page-structure-fix.preview.emergentagent.com/login")
    print("   Email: amits.joys@gmail.com")
    print("   Password: Admin@123")
    print("\n2. Go to Admin Panel to manage plans")
    print("\n3. Test payment flow with test Razorpay credentials")
    print("="*70)
    
    client.close()


async def main():
    """Main setup function"""
    print("🚀 Starting Production Setup...\n")
    
    # Create super admin
    print("1️⃣ Creating Super Admin...")
    await create_super_admin()
    
    # Seed plans
    print("\n2️⃣ Seeding Plans...")
    await seed_plans()
    
    # Ask if user wants to create Razorpay plans
    print("\n3️⃣ Razorpay Subscription Plans")
    print("Note: One-time payments work without Razorpay subscription plans.")
    print("Subscription plans are needed only for recurring billing.")
    
    if len(sys.argv) > 1 and sys.argv[1] == "--create-razorpay-plans":
        await create_razorpay_plans()
    else:
        print("⏭  Skipping Razorpay plan creation (use --create-razorpay-plans flag to create)")
    
    # Display status
    await display_status()


if __name__ == "__main__":
    asyncio.run(main())
