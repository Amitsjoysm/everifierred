"""
Link Razorpay Subscription Plans to Database Plans
This script creates Razorpay subscription plans and links them to database plans
"""
import asyncio
import razorpay
from motor.motor_asyncio import AsyncIOMotorClient
from config import settings

async def link_razorpay_plans():
    """Create Razorpay subscription plans and link them"""
    
    print("="*70)
    print("  RAZORPAY SUBSCRIPTION PLAN LINKER")
    print("="*70)
    
    # Check Razorpay credentials
    if not settings.RAZORPAY_KEY_ID or not settings.RAZORPAY_KEY_SECRET:
        print("\n✗ Error: Razorpay credentials not configured")
        print("  Please set RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET in .env file")
        return
    
    print(f"\n✓ Razorpay Key ID: {settings.RAZORPAY_KEY_ID}")
    print(f"✓ Using Test Mode")
    
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
        print(f"\nProcessing: {plan['name']}")
        print(f"  Plan ID: {plan['id']}")
        print(f"  Price: ₹{plan['price']}")
        print(f"  Credits: {plan['credits_limit']}")
        
        # Check if already linked
        if plan.get('razorpay_plan_id_inr'):
            print(f"  ⏭  Already linked to Razorpay: {plan['razorpay_plan_id_inr']}")
            continue
        
        try:
            # Create Razorpay subscription plan
            razorpay_plan_data = {
                "period": "monthly",
                "interval": 1,
                "item": {
                    "name": plan['name'],
                    "amount": int(plan['price'] * 100),  # Convert to paise
                    "currency": "INR",
                    "description": f"{plan['name']} - {plan['credits_limit']} email verifications"
                },
                "notes": {
                    "plan_id": plan['id'],
                    "plan_type": plan['type'],
                    "credits": str(plan['credits_limit']),
                    "created_by": "link_razorpay_plans.py"
                }
            }
            
            print("  Creating Razorpay subscription plan...")
            rz_plan = razorpay_client.plan.create(data=razorpay_plan_data)
            
            # Update database plan
            await db.plans.update_one(
                {"id": plan['id']},
                {
                    "$set": {
                        "razorpay_plan_id_inr": rz_plan['id'],
                        "is_recurring": True
                    }
                }
            )
            
            print(f"  ✓ Created and linked Razorpay Plan: {rz_plan['id']}")
            
        except Exception as e:
            print(f"  ✗ Failed: {str(e)}")
    
    # Display final status
    print("\n" + "="*70)
    print("  FINAL STATUS")
    print("="*70)
    
    updated_plans = await db.plans.find({"price": {"$gt": 0}}, {"_id": 0}).to_list(100)
    for plan in updated_plans:
        status = "✓ Linked" if plan.get('razorpay_plan_id_inr') else "✗ Not Linked"
        print(f"\n{plan['name']}:")
        print(f"  Status: {status}")
        if plan.get('razorpay_plan_id_inr'):
            print(f"  Razorpay Plan ID: {plan['razorpay_plan_id_inr']}")
    
    print("\n" + "="*70)
    mongo_client.close()

if __name__ == "__main__":
    asyncio.run(link_razorpay_plans())
