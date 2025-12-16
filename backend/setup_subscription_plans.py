"""
Setup Razorpay subscription plans for all pricing tiers
This script creates subscription plans on Razorpay and updates the database
"""

import asyncio
import razorpay
from motor.motor_asyncio import AsyncIOMotorClient
from config import settings
import sys

# Initialize Razorpay client
razorpay_client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))


async def create_subscription_plans():
    """Create Razorpay subscription plans and update database"""
    
    client = AsyncIOMotorClient(settings.MONGO_URL)
    db = client[settings.DB_NAME]
    
    print("=" * 80)
    print("Setting up Razorpay Subscription Plans")
    print("=" * 80)
    
    # Get all paid plans from database
    plans = await db.plans.find({"type": {"$ne": "free"}}, {"_id": 0}).to_list(100)
    
    if not plans:
        print("❌ No paid plans found in database. Please run seed_data.py first.")
        client.close()
        return
    
    print(f"\nFound {len(plans)} paid plans to configure\n")
    
    for plan in plans:
        plan_name = plan['name']
        print(f"\n{'=' * 60}")
        print(f"Configuring: {plan_name}")
        print(f"{'=' * 60}")
        
        # Create MONTHLY subscription plan
        try:
            monthly_price_paise = int(plan['price'] * 100)
            
            monthly_plan_data = {
                "period": "monthly",
                "interval": 1,
                "item": {
                    "name": f"{plan_name} - Monthly",
                    "description": f"{plan['credits_limit']} email verifications per month",
                    "amount": monthly_price_paise,
                    "currency": "INR"
                },
                "notes": {
                    "plan_id": plan['id'],
                    "plan_type": plan['type'],
                    "billing_cycle": "monthly",
                    "credits_limit": str(plan['credits_limit'])
                }
            }
            
            print(f"\n📅 Creating MONTHLY subscription plan...")
            print(f"   Amount: ₹{plan['price']}/month")
            
            razorpay_monthly = razorpay_client.plan.create(monthly_plan_data)
            monthly_plan_id = razorpay_monthly['id']
            
            print(f"   ✓ Created: {monthly_plan_id}")
            
            # Update database with monthly plan ID
            await db.plans.update_one(
                {"id": plan['id']},
                {"$set": {"razorpay_plan_id_monthly": monthly_plan_id}}
            )
            
        except Exception as e:
            print(f"   ❌ Failed to create monthly plan: {str(e)}")
            monthly_plan_id = None
        
        # Create YEARLY subscription plan
        try:
            yearly_price_paise = int(plan['yearly_price'] * 100)
            
            yearly_plan_data = {
                "period": "yearly",
                "interval": 1,
                "item": {
                    "name": f"{plan_name} - Yearly",
                    "description": f"{plan['credits_limit']} email verifications per month (billed yearly)",
                    "amount": yearly_price_paise,
                    "currency": "INR"
                },
                "notes": {
                    "plan_id": plan['id'],
                    "plan_type": plan['type'],
                    "billing_cycle": "yearly",
                    "credits_limit": str(plan['credits_limit'])
                }
            }
            
            print(f"\n📅 Creating YEARLY subscription plan...")
            print(f"   Amount: ₹{plan['yearly_price']}/year")
            print(f"   Effective: ₹{plan['yearly_price']/12:.0f}/month")
            
            razorpay_yearly = razorpay_client.plan.create(yearly_plan_data)
            yearly_plan_id = razorpay_yearly['id']
            
            print(f"   ✓ Created: {yearly_plan_id}")
            
            # Update database with yearly plan ID
            await db.plans.update_one(
                {"id": plan['id']},
                {"$set": {"razorpay_plan_id_yearly": yearly_plan_id}}
            )
            
        except Exception as e:
            print(f"   ❌ Failed to create yearly plan: {str(e)}")
            yearly_plan_id = None
        
        print(f"\n✓ {plan_name} configured successfully")
    
    print("\n" + "=" * 80)
    print("Subscription Plans Setup Complete!")
    print("=" * 80)
    
    # Display summary
    print("\n📊 SUMMARY:")
    updated_plans = await db.plans.find({}, {"_id": 0}).to_list(100)
    
    for plan in updated_plans:
        print(f"\n{plan['name']}:")
        print(f"  Type: {plan['type']}")
        if plan['type'] != 'free':
            print(f"  Monthly: ₹{plan['price']} (Plan ID: {plan.get('razorpay_plan_id_monthly', 'Not set')})")
            print(f"  Yearly: ₹{plan['yearly_price']} (Plan ID: {plan.get('razorpay_plan_id_yearly', 'Not set')})")
        else:
            print(f"  Price: FREE (No subscription required)")
    
    client.close()


if __name__ == "__main__":
    if not settings.RAZORPAY_KEY_ID or not settings.RAZORPAY_KEY_SECRET:
        print("❌ Error: Razorpay credentials not found in environment variables")
        print("Please set RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET")
        sys.exit(1)
    
    asyncio.run(create_subscription_plans())
