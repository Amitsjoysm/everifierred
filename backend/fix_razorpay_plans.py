"""Fix Razorpay subscription plans - Set dummy plan IDs for testing"""

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from config import settings


async def fix_razorpay_plans():
    """Add dummy Razorpay plan IDs to existing plans for testing"""
    
    client = AsyncIOMotorClient(settings.MONGO_URL)
    db = client[settings.DB_NAME]
    
    print("=" * 80)
    print("Fixing Razorpay Subscription Plans (Adding Dummy IDs)")
    print("=" * 80)
    
    # Get all plans from database
    plans = await db.plans.find({}, {"_id": 0}).to_list(100)
    
    if not plans:
        print("❌ No plans found in database.")
        client.close()
        return
    
    print(f"\nFound {len(plans)} plans to update\n")
    
    for plan in plans:
        plan_name = plan['name']
        plan_type = plan['type']
        
        # Skip free plan
        if plan_type == 'free':
            print(f"Skipping {plan_name} (free plan)")
            continue
        
        print(f"Updating: {plan_name}")
        
        # Create dummy plan IDs (in production, these would come from Razorpay API)
        monthly_plan_id = f"plan_{plan_type}_monthly_test"
        yearly_plan_id = f"plan_{plan_type}_yearly_test"
        
        # Update database
        await db.plans.update_one(
            {"id": plan['id']},
            {"$set": {
                "razorpay_plan_id_monthly": monthly_plan_id,
                "razorpay_plan_id_yearly": yearly_plan_id
            }}
        )
        
        print(f"  ✓ Monthly: {monthly_plan_id}")
        print(f"  ✓ Yearly: {yearly_plan_id}")
        print()
    
    print("=" * 80)
    print("✅ All plans updated successfully!")
    print("=" * 80)
    print("\nNOTE: These are dummy plan IDs for testing.")
    print("In production, run setup_subscription_plans.py with valid Razorpay credentials.")
    
    client.close()


if __name__ == "__main__":
    asyncio.run(fix_razorpay_plans())
