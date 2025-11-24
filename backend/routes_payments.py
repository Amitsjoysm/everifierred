from fastapi import APIRouter, Depends, HTTPException, Request, Header
from datetime import datetime, timezone
from typing import List, Optional
import razorpay
import hmac
import hashlib
import logging
import json

from database import get_db
from models import Plan, PlanType, Payment, User
from auth import get_current_user
from config import settings
from rate_limiter import rate_limiter
from payment_security import (
    verify_razorpay_signature,
    verify_webhook_signature,
    validate_payment_amount,
    log_payment_attempt,
    log_security_event,
    check_payment_idempotency
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Payments"])

# Initialize Razorpay client
razorpay_client = None
if settings.RAZORPAY_KEY_ID and settings.RAZORPAY_KEY_SECRET:
    razorpay_client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))


# ============= Public Plans =============

@router.get("/plans", response_model=List[Plan])
async def get_all_plans():
    """Get all active pricing plans"""
    db = await get_db()
    
    plans = await db.plans.find({"is_active": True}, {"_id": 0}).sort("price", 1).to_list(100)
    
    for plan in plans:
        if isinstance(plan.get('created_at'), str):
            plan['created_at'] = datetime.fromisoformat(plan['created_at'])
    
    return [Plan(**plan) for plan in plans]


@router.get("/plans/{plan_id}", response_model=Plan)
async def get_plan(plan_id: str):
    """Get specific plan"""
    db = await get_db()
    
    plan = await db.plans.find_one({"id": plan_id, "is_active": True}, {"_id": 0})
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    
    if isinstance(plan.get('created_at'), str):
        plan['created_at'] = datetime.fromisoformat(plan['created_at'])
    
    return Plan(**plan)


# ============= Payment Processing =============

@router.post("/payments/create-order")
async def create_payment_order(
    plan_id: str,
    current_user: User = Depends(get_current_user)
):
    """Create Razorpay order for plan subscription"""
    if not razorpay_client:
        raise HTTPException(status_code=503, detail="Payment service not configured")
    
    db = await get_db()
    
    # Get plan details
    plan = await db.plans.find_one({"id": plan_id, "is_active": True}, {"_id": 0})
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found or inactive")
    
    if plan['price'] == 0:
        raise HTTPException(status_code=400, detail="Free plan doesn't require payment")
    
    # Check if user already has a pending payment for same plan
    existing_pending = await db.payments.find_one({
        "user_id": current_user.id,
        "plan_id": plan_id,
        "status": "pending"
    })
    
    if existing_pending:
        # Return existing order if created within last 10 minutes
        created_at = datetime.fromisoformat(existing_pending['created_at']) if isinstance(existing_pending['created_at'], str) else existing_pending['created_at']
        time_diff = (datetime.now(timezone.utc) - created_at).total_seconds()
        
        if time_diff < 600:  # 10 minutes
            return {
                'order_id': existing_pending['razorpay_order_id'],
                'amount': int(plan['price'] * 100),
                'currency': 'INR',
                'razorpay_key': settings.RAZORPAY_KEY_ID,
                'message': 'Using existing pending order'
            }
        else:
            # Mark old order as expired
            await db.payments.update_one(
                {"id": existing_pending['id']},
                {"$set": {"status": "expired"}}
            )
    
    # Create Razorpay order
    try:
        order_data = {
            'amount': int(plan['price'] * 100),  # Convert to paise
            'currency': 'INR',
            'receipt': f"order_{current_user.id}_{int(datetime.now(timezone.utc).timestamp())}",
            'notes': {
                'user_id': current_user.id,
                'plan_id': plan_id,
                'plan_name': plan['name']
            }
        }
        
        razorpay_order = razorpay_client.order.create(data=order_data)
        
        # Store payment record
        payment = Payment(
            user_id=current_user.id,
            plan_id=plan_id,
            amount=plan['price'],
            razorpay_order_id=razorpay_order['id'],
            status='pending'
        )
        
        payment_dict = payment.model_dump()
        payment_dict['created_at'] = payment_dict['created_at'].isoformat()
        
        await db.payments.insert_one(payment_dict)
        
        return {
            'order_id': razorpay_order['id'],
            'amount': razorpay_order['amount'],
            'currency': razorpay_order['currency'],
            'razorpay_key': settings.RAZORPAY_KEY_ID
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create order: {str(e)}")


@router.post("/payments/verify")
async def verify_payment(
    razorpay_order_id: str,
    razorpay_payment_id: str,
    razorpay_signature: str,
    plan_id: str,
    current_user: User = Depends(get_current_user)
):
    """Verify Razorpay payment"""
    if not razorpay_client:
        raise HTTPException(status_code=503, detail="Payment service not configured")
    
    db = await get_db()
    
    # Check if payment record exists
    payment_record = await db.payments.find_one({
        "razorpay_order_id": razorpay_order_id,
        "user_id": current_user.id
    })
    
    if not payment_record:
        raise HTTPException(status_code=404, detail="Payment record not found")
    
    # Check if payment already processed
    if payment_record.get('status') == 'success':
        raise HTTPException(status_code=400, detail="Payment already processed")
    
    # Verify signature
    body = razorpay_order_id + "|" + razorpay_payment_id
    expected_signature = hmac.new(
        key=settings.RAZORPAY_KEY_SECRET.encode('utf-8'),
        msg=body.encode('utf-8'),
        digestmod=hashlib.sha256
    ).hexdigest()
    
    if expected_signature != razorpay_signature:
        # Mark payment as failed
        await db.payments.update_one(
            {"razorpay_order_id": razorpay_order_id},
            {"$set": {"status": "failed", "error_message": "Invalid signature"}}
        )
        raise HTTPException(status_code=400, detail="Invalid payment signature")
    
    # Verify payment status from Razorpay
    try:
        razorpay_payment = razorpay_client.payment.fetch(razorpay_payment_id)
        
        if razorpay_payment['status'] != 'captured' and razorpay_payment['status'] != 'authorized':
            await db.payments.update_one(
                {"razorpay_order_id": razorpay_order_id},
                {"$set": {"status": "failed", "error_message": f"Payment status: {razorpay_payment['status']}"}}
            )
            raise HTTPException(status_code=400, detail=f"Payment not successful. Status: {razorpay_payment['status']}")
    except Exception as e:
        await db.payments.update_one(
            {"razorpay_order_id": razorpay_order_id},
            {"$set": {"status": "failed", "error_message": str(e)}}
        )
        raise HTTPException(status_code=500, detail=f"Failed to verify payment with Razorpay: {str(e)}")
    
    # Get plan details
    plan = await db.plans.find_one({"id": plan_id, "is_active": True}, {"_id": 0})
    if not plan:
        await db.payments.update_one(
            {"razorpay_order_id": razorpay_order_id},
            {"$set": {"status": "failed", "error_message": "Plan not found"}}
        )
        raise HTTPException(status_code=404, detail="Plan not found or inactive")
    
    # Get current user data for credit transaction
    user_data = await db.users.find_one({"id": current_user.id}, {"_id": 0})
    current_credits_used = user_data.get('credits_used', 0)
    
    # Update payment record
    await db.payments.update_one(
        {"razorpay_order_id": razorpay_order_id},
        {
            "$set": {
                "razorpay_payment_id": razorpay_payment_id,
                "razorpay_signature": razorpay_signature,
                "status": "success",
                "completed_at": datetime.now(timezone.utc).isoformat()
            }
        }
    )
    
    # Update user plan and credits
    await db.users.update_one(
        {"id": current_user.id},
        {
            "$set": {
                "plan": plan['type'],
                "credits_limit": plan['credits_limit'],
                "credits_used": 0,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
        }
    )
    
    # Record credit reset transaction
    from utils import record_credit_transaction
    await record_credit_transaction(
        db=db,
        user_id=current_user.id,
        transaction_type="purchase",
        credits_change=-current_credits_used,  # Reset used credits
        description=f"Plan upgraded to {plan['name']} - Credits reset to {plan['credits_limit']}",
        reference_id=razorpay_order_id
    )
    
    return {
        "message": "Payment verified and plan upgraded successfully",
        "plan": plan['name'],
        "credits_limit": plan['credits_limit']
    }


@router.post("/payments/webhook")
async def razorpay_webhook(request: dict):
    """Handle Razorpay webhook events"""
    if not razorpay_client:
        raise HTTPException(status_code=503, detail="Payment service not configured")
    
    db = await get_db()
    
    # TODO: Verify webhook signature in production
    # For now, just log the event
    
    event = request.get('event')
    payload = request.get('payload', {})
    
    if event == 'payment.failed':
        payment_entity = payload.get('payment', {}).get('entity', {})
        order_id = payment_entity.get('order_id')
        
        if order_id:
            await db.payments.update_one(
                {"razorpay_order_id": order_id},
                {
                    "$set": {
                        "status": "failed",
                        "error_message": payment_entity.get('error_description', 'Payment failed'),
                        "updated_at": datetime.now(timezone.utc).isoformat()
                    }
                }
            )
    
    elif event == 'payment.captured':
        payment_entity = payload.get('payment', {}).get('entity', {})
        order_id = payment_entity.get('order_id')
        payment_id = payment_entity.get('id')
        
        if order_id and payment_id:
            # Get payment record
            payment_record = await db.payments.find_one({"razorpay_order_id": order_id})
            
            if payment_record and payment_record.get('status') != 'success':
                # Update payment status
                await db.payments.update_one(
                    {"razorpay_order_id": order_id},
                    {
                        "$set": {
                            "razorpay_payment_id": payment_id,
                            "status": "success",
                            "completed_at": datetime.now(timezone.utc).isoformat()
                        }
                    }
                )
                
                # Update user plan
                plan = await db.plans.find_one({"id": payment_record['plan_id']}, {"_id": 0})
                if plan:
                    await db.users.update_one(
                        {"id": payment_record['user_id']},
                        {
                            "$set": {
                                "plan": plan['type'],
                                "credits_limit": plan['credits_limit'],
                                "credits_used": 0
                            }
                        }
                    )
    
    return {"status": "ok"}


@router.post("/payments/cancel/{order_id}")
async def cancel_payment(
    order_id: str,
    current_user: User = Depends(get_current_user)
):
    """Cancel a pending payment"""
    db = await get_db()
    
    payment = await db.payments.find_one({
        "razorpay_order_id": order_id,
        "user_id": current_user.id,
        "status": "pending"
    })
    
    if not payment:
        raise HTTPException(status_code=404, detail="Pending payment not found")
    
    await db.payments.update_one(
        {"razorpay_order_id": order_id},
        {
            "$set": {
                "status": "cancelled",
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
        }
    )
    
    return {"message": "Payment cancelled successfully"}


@router.get("/payments/history", response_model=List[Payment])
async def get_payment_history(current_user: User = Depends(get_current_user)):
    """Get user's payment history"""
    db = await get_db()
    
    payments = await db.payments.find(
        {"user_id": current_user.id},
        {"_id": 0}
    ).sort("created_at", -1).to_list(100)
    
    for payment in payments:
        if isinstance(payment.get('created_at'), str):
            payment['created_at'] = datetime.fromisoformat(payment['created_at'])
    
    return [Payment(**payment) for payment in payments]
