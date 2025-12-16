"""
Link Razorpay Subscription Plans (Monthly and Yearly) to Database Plans
This script creates Razorpay subscription plans for both monthly and yearly billing
"""
import asyncio
import razorpay
from motor.motor_asyncio import AsyncIOMotorClient
from config import settings

async def link_razorpay_subscriptions():
    """Create Razorpay subscription plans (monthly + yearly) and link them"""
    
    print("="*70)
    print("  RAZORPAY SUBSCRIPTION PLAN LINKER (MONTHLY + YEARLY)")
    print("="*70)
    
    # Check Razorpay credentials
    if not settings.RAZORPAY_KEY_ID or not settings.RAZORPAY_KEY_SECRET:
        print("\n✗ Error: Razorpay credentials not configured")
        print("  Please set RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET in .env file")
        return
    
    print(f"\n✓ Razorpay Key ID: {settings.RAZORPAY_KEY_ID}")
    print(f"✓ Using {'Test' if 'test' in settings.RAZORPAY_KEY_ID else 'Live'} Mode")
    
    # Initialize clients
    razorpay_client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
    mongo_client = AsyncIOMotorClient(settings.MONGO_URL)
    db = mongo_client[settings.DB_NAME]
    
    # Get all paid plans
    plans = await db.plans.find({"price": {"$gt": 0}}, {"_id": 0}).to_list(100)
    
    if not plans:
        print("\n✗ No paid plans found in database")
        mongo_client.close()
        return
    
    print(f"\n✓ Found {len(plans)} paid plan(s) to process\n")
    
    for plan in plans:
        print(f"\n{'='*70}")
        print(f"Processing: {plan['name']}")
        print(f"  Plan ID: {plan['id']}")
        print(f"  Monthly Price: ₹{plan['price']}")
        print(f"  Yearly Price: ₹{plan.get('yearly_price', 0)}")
        print(f"  Credits: {plan['credits_limit']}")
        
        # Create Monthly Subscription Plan
        if not plan.get('razorpay_plan_id_monthly'):
            try:
                monthly_plan_data = {
                    "period": "monthly",
                    "interval": 1,
                    "item": {
                        "name": f"{plan['name']} - Monthly",
                        "amount": int(plan['price'] * 100),  # Convert to paise
                        "currency": "INR",
                        "description": f"{plan['name']} Monthly - {plan['credits_limit']} verifications/month"
                    },
                    "notes": {
                        "plan_id": plan['id'],
                        "plan_type": plan['type'],
                        "billing_cycle": "monthly",
                        "credits": str(plan['credits_limit']),
                        "created_by": "link_razorpay_subscriptions.py"
                    }
                }
                
                print("\n  📅 Creating MONTHLY Razorpay subscription plan...")
                rz_monthly = razorpay_client.plan.create(data=monthly_plan_data)
                
                # Update database
                await db.plans.update_one(
                    {"id": plan['id']},
                    {"$set": {"razorpay_plan_id_monthly": rz_monthly['id'], "is_recurring": True}}
                )
                
                print(f"  ✓ Monthly Plan Created: {rz_monthly['id']}")
                
            except Exception as e:
                print(f"  ✗ Failed to create monthly plan: {str(e)}")
        else:
            print(f"\n  ⏭  Monthly plan already linked: {plan['razorpay_plan_id_monthly']}")
        
        # Create Yearly Subscription Plan
        yearly_price = plan.get('yearly_price')
        if yearly_price and yearly_price > 0:
            if not plan.get('razorpay_plan_id_yearly'):
                try:
                    yearly_plan_data = {
                        "period": "yearly",
                        "interval": 1,
                        "item": {
                            "name": f"{plan['name']} - Yearly",
                            "amount": int(yearly_price * 100),  # Convert to paise
                            "currency": "INR",
                            "description": f"{plan['name']} Yearly - {plan['credits_limit']} verifications/month"
                        },
                        "notes": {
                            "plan_id": plan['id'],
                            "plan_type": plan['type'],
                            "billing_cycle": "yearly",
                            "credits": str(plan['credits_limit']),
                            "created_by": "link_razorpay_subscriptions.py"
                        }
                    }
                    
                    print("\n  📆 Creating YEARLY Razorpay subscription plan...")
                    rz_yearly = razorpay_client.plan.create(data=yearly_plan_data)
                    
                    # Update database
                    await db.plans.update_one(
                        {"id": plan['id']},
                        {"$set": {"razorpay_plan_id_yearly": rz_yearly['id']}}
                    )
                    
                    print(f"  ✓ Yearly Plan Created: {rz_yearly['id']}")
                    
                except Exception as e:
                    print(f"  ✗ Failed to create yearly plan: {str(e)}")
            else:
                print(f"  ⏭  Yearly plan already linked: {plan['razorpay_plan_id_yearly']}")
        else:
            print("  ℹ  No yearly pricing configured for this plan")
    
    # Display final status
    print("\n" + "="*70)
    print("  FINAL STATUS - ALL PLANS")
    print("="*70)
    
    updated_plans = await db.plans.find({"price": {"$gt": 0}}, {"_id": 0}).to_list(100)
    for plan in updated_plans:
        monthly_status = "✓ Linked" if plan.get('razorpay_plan_id_monthly') else "✗ Not Linked"
        yearly_status = "✓ Linked" if plan.get('razorpay_plan_id_yearly') else "✗ Not Linked"
        
        print(f"\n{plan['name']}:")
        print(f"  Monthly: {monthly_status}")
        if plan.get('razorpay_plan_id_monthly'):
            print(f"    Razorpay Plan ID: {plan['razorpay_plan_id_monthly']}")
        print(f"  Yearly: {yearly_status}")
        if plan.get('razorpay_plan_id_yearly'):
            print(f"    Razorpay Plan ID: {plan['razorpay_plan_id_yearly']}")
    
    print("\n" + "="*70)
    print("✓ Subscription linking completed!")
    print("="*70)
    mongo_client.close()

if __name__ == "__main__":
    asyncio.run(link_razorpay_subscriptions())
