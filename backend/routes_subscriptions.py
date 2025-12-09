"""
Subscription Management Routes
Handle recurring subscriptions with Razorpay
"""
from fastapi import APIRouter, Depends, HTTPException, Request
from datetime import datetime, timezone
from typing import List, Optional
import razorpay
import logging
from pydantic import BaseModel

from database import get_db
from models import User
from auth import get_current_user, get_current_admin_user
from config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/subscriptions", tags=["Subscriptions"])

# Initialize Razorpay client
razorpay_client = None
if settings.RAZORPAY_KEY_ID and settings.RAZORPAY_KEY_SECRET:
    razorpay_client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))


class SubscriptionCreate(BaseModel):
    plan_id: str
    currency: str = "INR"  # INR or USD
    billing_cycle: str = "monthly"  # monthly or yearly


class SubscriptionAction(BaseModel):
    subscription_id: str
    action: str  # pause, resume, cancel


@router.post("/create")
async def create_subscription(
    data: SubscriptionCreate,
    current_user: User = Depends(get_current_user)
):
    """Create a new subscription"""
    if not razorpay_client:
        raise HTTPException(status_code=503, detail="Payment service not configured")
    
    db = await get_db()
    
    # Get plan details
    plan = await db.plans.find_one({"id": data.plan_id, "is_active": True}, {"_id": 0})
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    
    # Get appropriate Razorpay plan ID based on currency
    razorpay_plan_id = None
    if data.currency == "INR":
        razorpay_plan_id = plan.get('razorpay_plan_id_inr')
    elif data.currency == "USD":
        razorpay_plan_id = plan.get('razorpay_plan_id_usd')
    
    if not razorpay_plan_id:
        raise HTTPException(
            status_code=400, 
            detail=f"Subscription plan not configured for {data.currency}. Please use one-time payment instead."
        )
    
    try:
        # Create subscription in Razorpay
        subscription_data = {
            "plan_id": razorpay_plan_id,
            "customer_notify": 1,
            "total_count": 12 if data.billing_cycle == "yearly" else 120,  # 120 months = 10 years
            "notes": {
                "user_id": current_user.id,
                "plan_id": data.plan_id,
                "currency": data.currency,
                "billing_cycle": data.billing_cycle
            }
        }
        
        razorpay_subscription = razorpay_client.subscription.create(data=subscription_data)
        
        # Store subscription record
        subscription_record = {
            "id": str(uuid.uuid4()),
            "user_id": current_user.id,
            "plan_id": data.plan_id,
            "razorpay_subscription_id": razorpay_subscription['id'],
            "razorpay_plan_id": razorpay_plan_id,
            "status": razorpay_subscription['status'],
            "currency": data.currency,
            "billing_cycle": data.billing_cycle,
            "current_start": razorpay_subscription.get('current_start'),
            "current_end": razorpay_subscription.get('current_end'),
            "created_at": datetime.now(timezone.utc).isoformat(),
            "total_count": subscription_data['total_count'],
            "paid_count": 0
        }
        
        await db.subscriptions.insert_one(subscription_record)
        
        logger.info(f"Subscription created: {razorpay_subscription['id']} for user {current_user.id}")
        
        return {
            "subscription_id": razorpay_subscription['id'],
            "status": razorpay_subscription['status'],
            "short_url": razorpay_subscription.get('short_url'),
            "message": "Subscription created successfully. Please complete payment."
        }
        
    except Exception as e:
        logger.error(f"Failed to create subscription: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create subscription: {str(e)}")


@router.get("/my-subscriptions")
async def get_user_subscriptions(current_user: User = Depends(get_current_user)):
    """Get user's active subscriptions"""
    db = await get_db()
    
    subscriptions = await db.subscriptions.find(
        {"user_id": current_user.id},
        {"_id": 0}
    ).sort("created_at", -1).to_list(100)
    
    # Enrich with plan information
    for sub in subscriptions:
        plan = await db.plans.find_one({"id": sub.get('plan_id')}, {"_id": 0, "name": 1, "type": 1})
        if plan:
            sub['plan_name'] = plan.get('name')
            sub['plan_type'] = plan.get('type')
    
    return {
        "subscriptions": subscriptions,
        "count": len(subscriptions)
    }


@router.post("/manage")
async def manage_subscription(
    action_data: SubscriptionAction,
    current_user: User = Depends(get_current_user)
):
    """Pause, resume, or cancel subscription"""
    if not razorpay_client:
        raise HTTPException(status_code=503, detail="Payment service not configured")
    
    db = await get_db()
    
    # Find subscription
    subscription = await db.subscriptions.find_one({
        "razorpay_subscription_id": action_data.subscription_id,
        "user_id": current_user.id
    })
    
    if not subscription:
        raise HTTPException(status_code=404, detail="Subscription not found")
    
    try:
        if action_data.action == "pause":
            razorpay_client.subscription.pause(action_data.subscription_id)
            await db.subscriptions.update_one(
                {"razorpay_subscription_id": action_data.subscription_id},
                {"$set": {"status": "paused"}}
            )
            message = "Subscription paused successfully"
            
        elif action_data.action == "resume":
            razorpay_client.subscription.resume(action_data.subscription_id)
            await db.subscriptions.update_one(
                {"razorpay_subscription_id": action_data.subscription_id},
                {"$set": {"status": "active"}}
            )
            message = "Subscription resumed successfully"
            
        elif action_data.action == "cancel":
            razorpay_client.subscription.cancel(action_data.subscription_id)
            await db.subscriptions.update_one(
                {"razorpay_subscription_id": action_data.subscription_id},
                {"$set": {"status": "cancelled", "cancelled_at": datetime.now(timezone.utc).isoformat()}}
            )
            message = "Subscription cancelled successfully"
        else:
            raise HTTPException(status_code=400, detail="Invalid action")
        
        logger.info(f"Subscription {action_data.action}: {action_data.subscription_id}")
        
        return {"message": message}
        
    except Exception as e:
        logger.error(f"Failed to {action_data.action} subscription: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to {action_data.action} subscription: {str(e)}")


@router.get("/admin/all", response_model=List[dict])
async def get_all_subscriptions(
    status: Optional[str] = None,
    current_user: User = Depends(get_current_admin_user)
):
    """Get all subscriptions (Admin only)"""
    db = await get_db()
    
    query = {}
    if status:
        query["status"] = status
    
    subscriptions = await db.subscriptions.find(
        query,
        {"_id": 0}
    ).sort("created_at", -1).to_list(1000)
    
    # Enrich with user and plan information
    for sub in subscriptions:
        user = await db.users.find_one(
            {"id": sub.get('user_id')},
            {"_id": 0, "email": 1, "full_name": 1}
        )
        if user:
            sub['user_email'] = user.get('email')
            sub['user_name'] = user.get('full_name')
        
        plan = await db.plans.find_one(
            {"id": sub.get('plan_id')},
            {"_id": 0, "name": 1, "type": 1}
        )
        if plan:
            sub['plan_name'] = plan.get('name')
            sub['plan_type'] = plan.get('type')
    
    return subscriptions


import uuid
