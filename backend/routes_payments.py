from fastapi import APIRouter, Depends, HTTPException, Request, Header
from datetime import datetime, timezone, timedelta
from typing import List, Optional
import razorpay
import hmac
import hashlib
import logging
import json

from database import get_db
from models import Plan, Payment, User, PaymentVerifyRequest, Subscription
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

router = APIRouter(prefix="/payments", tags=["Payments"])

# Initialize Razorpay client
razorpay_client = None
if settings.RAZORPAY_KEY_ID and settings.RAZORPAY_KEY_SECRET:
    razorpay_client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))


# ============= Public Plans =============

@router.get("/plans", response_model=List[Plan])
async def get_all_plans():
    """Get all active pricing plans with monthly and yearly pricing"""
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


# ============= Subscription Creation =============

@router.post("/create-subscription")
async def create_subscription(
    plan_id: str,
    billing_cycle: str = "monthly",
    request: Request = None,
    current_user: User = Depends(get_current_user)
):
    """Create Razorpay subscription for recurring payments with fraud prevention"""
    # Rate limit: 5 requests per minute
    allowed, remaining = await rate_limiter.is_allowed(
        identifier=current_user.id,
        max_requests=5,
        window_seconds=60
    )
    
    if not allowed:
        await log_security_event(
            db=await get_db(),
            event_type="rate_limit_exceeded",
            severity="medium",
            description=f"User {current_user.id} exceeded subscription creation rate limit",
            details={"plan_id": plan_id}
        )
        raise HTTPException(
            status_code=429,
            detail="Too many subscription requests. Please try again in 1 minute.",
            headers={"Retry-After": "60"}
        )
    
    if not razorpay_client:
        raise HTTPException(status_code=503, detail="Payment service not configured")
    
    if billing_cycle not in ["monthly", "yearly"]:
        raise HTTPException(status_code=400, detail="Invalid billing cycle. Must be 'monthly' or 'yearly'")
    
    db = await get_db()
    
    # Get plan details
    plan = await db.plans.find_one({"id": plan_id, "is_active": True}, {"_id": 0})
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found or inactive")
    
    if plan['price'] == 0:
        raise HTTPException(status_code=400, detail="Free plan doesn't require payment")
    
    # Check if user already has an active subscription
    existing_subscription = await db.subscriptions.find_one({
        "user_id": current_user.id,
        "status": {"$in": ["active", "authenticated", "created"]}
    })
    
    if existing_subscription:
        raise HTTPException(
            status_code=400,
            detail="You already have an active subscription. Please cancel it before subscribing to a new plan."
        )
    
    # Get the appropriate Razorpay plan ID based on billing cycle
    razorpay_plan_id = plan.get(f'razorpay_plan_id_{billing_cycle}')
    if not razorpay_plan_id:
        raise HTTPException(
            status_code=400,
            detail=f"Subscription not available for {billing_cycle} billing cycle. Please contact support."
        )
    
    # Determine amount based on billing cycle
    amount = plan['yearly_price'] if billing_cycle == 'yearly' else plan['price']
    
    try:
        # Create Razorpay subscription
        subscription_data = {
            "plan_id": razorpay_plan_id,
            "customer_notify": 1,
            "total_count": 0,  # 0 means subscription continues until cancelled
            "notes": {
                "user_id": current_user.id,
                "plan_id": plan_id,
                "plan_name": plan['name'],
                "billing_cycle": billing_cycle
            }
        }
        
        razorpay_subscription = razorpay_client.subscription.create(subscription_data)
        subscription_id = razorpay_subscription['id']
        
        # Calculate next billing date
        if billing_cycle == 'yearly':
            next_billing = datetime.now(timezone.utc) + timedelta(days=365)
        else:
            next_billing = datetime.now(timezone.utc) + timedelta(days=30)
        
        # Store subscription record
        subscription = Subscription(
            user_id=current_user.id,
            plan_id=plan_id,
            razorpay_subscription_id=subscription_id,
            status='created',  # Will become 'active' after first payment
            billing_cycle=billing_cycle,
            amount=amount,
            currency='INR',
            next_billing_date=next_billing
        )
        
        subscription_dict = subscription.model_dump()
        subscription_dict['start_date'] = subscription_dict['start_date'].isoformat()
        subscription_dict['next_billing_date'] = subscription_dict['next_billing_date'].isoformat()
        subscription_dict['created_at'] = subscription_dict['created_at'].isoformat()
        subscription_dict['updated_at'] = subscription_dict['updated_at'].isoformat()
        
        await db.subscriptions.insert_one(subscription_dict)
        
        # Log subscription creation
        await log_payment_attempt(
            db=db,
            user_id=current_user.id,
            plan_id=plan_id,
            amount=amount,
            status='subscription_created',
            details={
                'subscription_id': subscription_id,
                'billing_cycle': billing_cycle
            }
        )
        
        logger.info(f"Subscription created: {subscription_id} for user {current_user.id}, billing: {billing_cycle}")
        
        # Return subscription details for Razorpay Checkout
        return {
            'subscription_id': subscription_id,
            'razorpay_key': settings.RAZORPAY_KEY_ID,
            'amount': int(amount * 100),  # In paise
            'currency': 'INR',
            'plan_name': plan['name'],
            'billing_cycle': billing_cycle,
            'is_subscription': True
        }
        
    except Exception as e:
        logger.error(f"Failed to create subscription: {str(e)}")
        await log_payment_attempt(
            db=db,
            user_id=current_user.id,
            plan_id=plan_id,
            amount=amount,
            status='subscription_creation_failed',
            details={'error': str(e), 'billing_cycle': billing_cycle}
        )
        raise HTTPException(status_code=500, detail=f"Failed to create subscription: {str(e)}")


# ============= Payment Verification =============

@router.post("/verify-subscription")
async def verify_subscription_payment(
    verify_request: PaymentVerifyRequest,
    request: Request = None,
    current_user: User = Depends(get_current_user)
):
    """Verify subscription payment and activate user's plan with comprehensive security"""
    razorpay_payment_id = verify_request.razorpay_payment_id
    razorpay_signature = verify_request.razorpay_signature
    plan_id = verify_request.plan_id
    billing_cycle = verify_request.billing_cycle
    
    # For subscriptions, we need subscription_id instead of order_id
    subscription_id = verify_request.razorpay_order_id  # Frontend sends subscription_id here
    
    logger.info(
        f"Subscription payment verification started - User: {current_user.id}, "
        f"Subscription: {subscription_id}, Payment: {razorpay_payment_id}, Plan: {plan_id}"
    )
    
    # Rate limit: 10 requests per minute
    allowed, remaining = await rate_limiter.is_allowed(
        identifier=current_user.id,
        max_requests=10,
        window_seconds=60
    )
    
    if not allowed:
        await log_security_event(
            db=await get_db(),
            event_type="rate_limit_exceeded",
            severity="medium",
            description=f"User {current_user.id} exceeded payment verification rate limit",
            details={"subscription_id": subscription_id}
        )
        raise HTTPException(
            status_code=429,
            detail="Too many verification requests. Please try again in 1 minute.",
            headers={"Retry-After": "60"}
        )
    
    if not razorpay_client:
        raise HTTPException(status_code=503, detail="Payment service not configured")
    
    db = await get_db()
    
    # Check if subscription record exists
    subscription_record = await db.subscriptions.find_one({
        "razorpay_subscription_id": subscription_id,
        "user_id": current_user.id
    })
    
    if not subscription_record:
        await log_security_event(
            db=db,
            event_type="subscription_verification_failed",
            severity="high",
            description="Subscription record not found during verification",
            details={
                "subscription_id": subscription_id,
                "user_id": current_user.id,
                "payment_id": razorpay_payment_id
            }
        )
        raise HTTPException(status_code=404, detail="Subscription record not found")
    
    # Verify signature for subscription payment
    # For subscriptions: razorpay_payment_id + "|" + razorpay_subscription_id
    body = razorpay_payment_id + "|" + subscription_id
    expected_signature = hmac.new(
        key=settings.RAZORPAY_KEY_SECRET.encode('utf-8'),
        msg=body.encode('utf-8'),
        digestmod=hashlib.sha256
    ).hexdigest()
    
    is_valid = hmac.compare_digest(expected_signature, razorpay_signature)
    
    if not is_valid:
        await db.subscriptions.update_one(
            {"razorpay_subscription_id": subscription_id},
            {"$set": {"status": "failed"}}
        )
        
        await log_security_event(
            db=db,
            event_type="invalid_subscription_signature",
            severity="critical",
            description="Invalid subscription payment signature detected",
            details={
                "subscription_id": subscription_id,
                "payment_id": razorpay_payment_id,
                "user_id": current_user.id
            }
        )
        
        raise HTTPException(status_code=400, detail="Invalid payment signature")
    
    # Verify payment status from Razorpay
    try:
        logger.info(f"Fetching payment details from Razorpay: {razorpay_payment_id}")
        razorpay_payment = razorpay_client.payment.fetch(razorpay_payment_id)
        
        logger.info(f"Razorpay payment status: {razorpay_payment.get('status')} for payment {razorpay_payment_id}")
        
        if razorpay_payment['status'] != 'captured' and razorpay_payment['status'] != 'authorized':
            error_msg = f"Payment status: {razorpay_payment['status']}"
            await db.subscriptions.update_one(
                {"razorpay_subscription_id": subscription_id},
                {"$set": {"status": "failed"}}
            )
            logger.warning(f"Subscription payment verification failed: {error_msg}")
            raise HTTPException(status_code=400, detail=f"Payment not successful. Status: {razorpay_payment['status']}")
    except HTTPException:
        raise
    except Exception as e:
        error_msg = f"Failed to verify payment with Razorpay: {str(e)}"
        logger.error(f"{error_msg} - Subscription: {subscription_id}, Payment: {razorpay_payment_id}")
        
        await db.subscriptions.update_one(
            {"razorpay_subscription_id": subscription_id},
            {"$set": {"status": "failed"}}
        )
        raise HTTPException(status_code=500, detail=error_msg)
    
    # Get plan details
    plan = await db.plans.find_one({"id": plan_id, "is_active": True}, {"_id": 0})
    if not plan:
        await db.subscriptions.update_one(
            {"razorpay_subscription_id": subscription_id},
            {"$set": {"status": "failed"}}
        )
        raise HTTPException(status_code=404, detail="Plan not found or inactive")
    
    # Validate payment amount matches plan price
    expected_amount = plan['yearly_price'] if billing_cycle == 'yearly' else plan['price']
    amount_paid = razorpay_payment['amount'] / 100  # Convert from paise to rupees
    
    if abs(amount_paid - expected_amount) > 0.01:  # Allow 1 paise tolerance
        await db.subscriptions.update_one(
            {"razorpay_subscription_id": subscription_id},
            {"$set": {"status": "failed"}}
        )
        
        await log_security_event(
            db=db,
            event_type="payment_amount_mismatch",
            severity="critical",
            description="Payment amount does not match plan price",
            details={
                "subscription_id": subscription_id,
                "payment_id": razorpay_payment_id,
                "user_id": current_user.id,
                "expected_amount": expected_amount,
                "actual_amount": amount_paid
            }
        )
        
        raise HTTPException(status_code=400, detail="Payment amount mismatch")
    
    # Update subscription status to active
    await db.subscriptions.update_one(
        {"razorpay_subscription_id": subscription_id},
        {
            "$set": {
                "status": "active",
                "successful_payments": subscription_record.get('successful_payments', 0) + 1,
                "total_payments": subscription_record.get('total_payments', 0) + 1,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
        }
    )
    
    # Update user plan and credits - ONLY FOR SUCCESSFUL PAYMENTS
    await db.users.update_one(
        {"id": current_user.id},
        {
            "$set": {
                "plan": plan['type'],
                "credits_limit": plan['credits_limit'],
                "credits_used": 0,  # Reset credits on new subscription
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
        }
    )
    
    # Record payment in payments collection
    payment = Payment(
        user_id=current_user.id,
        plan_id=plan_id,
        amount=amount_paid,
        currency='INR',
        billing_cycle=billing_cycle,
        razorpay_payment_id=razorpay_payment_id,
        razorpay_subscription_id=subscription_id,
        status='success',
        is_recurring=True,
        completed_at=datetime.now(timezone.utc)
    )
    
    payment_dict = payment.model_dump()
    payment_dict['created_at'] = payment_dict['created_at'].isoformat()
    payment_dict['completed_at'] = payment_dict['completed_at'].isoformat()
    
    await db.payments.insert_one(payment_dict)
    
    # Record credit transaction
    from utils import record_credit_transaction
    await record_credit_transaction(
        db=db,
        user_id=current_user.id,
        transaction_type="subscription",
        credits_change=plan['credits_limit'],
        description=f"Subscription activated: {plan['name']} ({billing_cycle}) - {plan['credits_limit']} credits",
        reference_id=subscription_id
    )
    
    # Log successful subscription payment
    await log_payment_attempt(
        db=db,
        user_id=current_user.id,
        plan_id=plan_id,
        amount=amount_paid,
        status='subscription_activated',
        details={
            'subscription_id': subscription_id,
            'payment_id': razorpay_payment_id,
            'billing_cycle': billing_cycle
        }
    )
    
    logger.info(
        f"Subscription activated successfully: Subscription {subscription_id}, "
        f"Payment {razorpay_payment_id}, User {current_user.id}"
    )
    
    return {
        "message": "Subscription activated successfully",
        "plan": plan['name'],
        "credits_limit": plan['credits_limit'],
        "billing_cycle": billing_cycle,
        "next_billing_date": subscription_record.get('next_billing_date')
    }


# ============= Subscription Management =============

@router.get("/subscription/status")
async def get_subscription_status(current_user: User = Depends(get_current_user)):
    """Get current user's subscription status"""
    db = await get_db()
    
    subscription = await db.subscriptions.find_one(
        {"user_id": current_user.id, "status": "active"},
        {"_id": 0}
    )
    
    if not subscription:
        return {"has_subscription": False}
    
    # Get plan details
    plan = await db.plans.find_one({"id": subscription['plan_id']}, {"_id": 0})
    
    return {
        "has_subscription": True,
        "subscription_id": subscription['razorpay_subscription_id'],
        "plan_name": plan['name'] if plan else "Unknown",
        "billing_cycle": subscription['billing_cycle'],
        "status": subscription['status'],
        "next_billing_date": subscription.get('next_billing_date'),
        "amount": subscription['amount']
    }


@router.post("/subscription/cancel")
async def cancel_subscription(current_user: User = Depends(get_current_user)):
    """Cancel active subscription"""
    if not razorpay_client:
        raise HTTPException(status_code=503, detail="Payment service not configured")
    
    db = await get_db()
    
    subscription = await db.subscriptions.find_one({
        "user_id": current_user.id,
        "status": "active"
    })
    
    if not subscription:
        raise HTTPException(status_code=404, detail="No active subscription found")
    
    try:
        # Cancel subscription on Razorpay
        razorpay_subscription_id = subscription['razorpay_subscription_id']
        razorpay_client.subscription.cancel(razorpay_subscription_id, {
            "cancel_at_cycle_end": 0  # Cancel immediately
        })
        
        # Update subscription status in database
        await db.subscriptions.update_one(
            {"razorpay_subscription_id": razorpay_subscription_id},
            {
                "$set": {
                    "status": "cancelled",
                    "cancelled_at": datetime.now(timezone.utc).isoformat(),
                    "updated_at": datetime.now(timezone.utc).isoformat()
                }
            }
        )
        
        logger.info(f"Subscription cancelled: {razorpay_subscription_id} for user {current_user.id}")
        
        return {
            "message": "Subscription cancelled successfully",
            "subscription_id": razorpay_subscription_id
        }
        
    except Exception as e:
        logger.error(f"Failed to cancel subscription: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to cancel subscription: {str(e)}")


# ============= Webhooks =============

@router.post("/webhook")
async def razorpay_webhook(
    request: Request,
    x_razorpay_signature: Optional[str] = Header(None)
):
    """Handle Razorpay webhook events with signature verification"""
    if not razorpay_client:
        raise HTTPException(status_code=503, detail="Payment service not configured")
    
    db = await get_db()
    
    # Get raw body for signature verification
    body = await request.body()
    body_str = body.decode('utf-8')
    
    # Verify webhook signature (CRITICAL SECURITY)
    webhook_secret = settings.RAZORPAY_KEY_SECRET
    
    if x_razorpay_signature:
        if not verify_webhook_signature(body_str, x_razorpay_signature, webhook_secret):
            await log_security_event(
                db=db,
                event_type="invalid_webhook_signature",
                severity="critical",
                description="Invalid Razorpay webhook signature detected",
                details={"body_preview": body_str[:100]}
            )
            raise HTTPException(status_code=401, detail="Invalid webhook signature")
        
        logger.info("Webhook signature verified successfully")
    else:
        await log_security_event(
            db=db,
            event_type="missing_webhook_signature",
            severity="high",
            description="Webhook received without signature",
            details={"body_preview": body_str[:100]}
        )
        logger.warning("Webhook received without signature header")
    
    # Parse webhook data
    try:
        webhook_data = json.loads(body_str)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON in webhook")
    
    event = webhook_data.get('event')
    payload = webhook_data.get('payload', {})
    
    # Handle subscription events
    if event == 'subscription.activated':
        await handle_subscription_activated(db, payload)
    elif event == 'subscription.charged':
        await handle_subscription_charged(db, payload)
    elif event == 'subscription.cancelled':
        await handle_subscription_cancelled(db, payload)
    elif event == 'subscription.paused':
        await handle_subscription_paused(db, payload)
    elif event == 'subscription.resumed':
        await handle_subscription_resumed(db, payload)
    elif event == 'subscription.completed':
        await handle_subscription_completed(db, payload)
    elif event == 'subscription.pending':
        await handle_subscription_pending(db, payload)
    elif event == 'subscription.halted':
        await handle_subscription_halted(db, payload)
    elif event == 'payment.failed':
        await handle_payment_failed(db, payload)
    
    return {"status": "ok"}


async def handle_subscription_activated(db, payload):
    """Handle subscription.activated webhook"""
    subscription_entity = payload.get('subscription', {}).get('entity', {})
    subscription_id = subscription_entity.get('id')
    
    if subscription_id:
        await db.subscriptions.update_one(
            {"razorpay_subscription_id": subscription_id},
            {
                "$set": {
                    "status": "active",
                    "updated_at": datetime.now(timezone.utc).isoformat()
                }
            }
        )
        logger.info(f"Subscription activated via webhook: {subscription_id}")


async def handle_subscription_charged(db, payload):
    """Handle subscription.charged webhook - recurring payment success"""
    payment_entity = payload.get('payment', {}).get('entity', {})
    subscription_entity = payload.get('subscription', {}).get('entity', {})
    
    subscription_id = subscription_entity.get('id')
    payment_id = payment_entity.get('id')
    amount_paid = payment_entity.get('amount', 0) / 100
    
    if subscription_id:
        # Get subscription record
        subscription_record = await db.subscriptions.find_one({"razorpay_subscription_id": subscription_id})
        
        if subscription_record:
            # Update subscription
            await db.subscriptions.update_one(
                {"razorpay_subscription_id": subscription_id},
                {
                    "$set": {
                        "status": "active",
                        "updated_at": datetime.now(timezone.utc).isoformat()
                    },
                    "$inc": {
                        "successful_payments": 1,
                        "total_payments": 1
                    }
                }
            )
            
            # Reset user credits for new billing cycle
            await db.users.update_one(
                {"id": subscription_record['user_id']},
                {"$set": {"credits_used": 0}}
            )
            
            # Record payment
            payment = Payment(
                user_id=subscription_record['user_id'],
                plan_id=subscription_record['plan_id'],
                amount=amount_paid,
                currency='INR',
                billing_cycle=subscription_record['billing_cycle'],
                razorpay_payment_id=payment_id,
                razorpay_subscription_id=subscription_id,
                status='success',
                is_recurring=True,
                completed_at=datetime.now(timezone.utc)
            )
            
            payment_dict = payment.model_dump()
            payment_dict['created_at'] = payment_dict['created_at'].isoformat()
            payment_dict['completed_at'] = payment_dict['completed_at'].isoformat()
            
            await db.payments.insert_one(payment_dict)
            
            logger.info(f"Subscription charged via webhook: {subscription_id}, payment: {payment_id}")


async def handle_subscription_cancelled(db, payload):
    """Handle subscription.cancelled webhook"""
    subscription_entity = payload.get('subscription', {}).get('entity', {})
    subscription_id = subscription_entity.get('id')
    
    if subscription_id:
        await db.subscriptions.update_one(
            {"razorpay_subscription_id": subscription_id},
            {
                "$set": {
                    "status": "cancelled",
                    "cancelled_at": datetime.now(timezone.utc).isoformat(),
                    "updated_at": datetime.now(timezone.utc).isoformat()
                }
            }
        )
        logger.info(f"Subscription cancelled via webhook: {subscription_id}")


async def handle_subscription_paused(db, payload):
    """Handle subscription.paused webhook"""
    subscription_entity = payload.get('subscription', {}).get('entity', {})
    subscription_id = subscription_entity.get('id')
    
    if subscription_id:
        await db.subscriptions.update_one(
            {"razorpay_subscription_id": subscription_id},
            {"$set": {"status": "paused", "updated_at": datetime.now(timezone.utc).isoformat()}}
        )
        logger.info(f"Subscription paused via webhook: {subscription_id}")


async def handle_subscription_resumed(db, payload):
    """Handle subscription.resumed webhook"""
    subscription_entity = payload.get('subscription', {}).get('entity', {})
    subscription_id = subscription_entity.get('id')
    
    if subscription_id:
        await db.subscriptions.update_one(
            {"razorpay_subscription_id": subscription_id},
            {"$set": {"status": "active", "updated_at": datetime.now(timezone.utc).isoformat()}}
        )
        logger.info(f"Subscription resumed via webhook: {subscription_id}")


async def handle_subscription_completed(db, payload):
    """Handle subscription.completed webhook"""
    subscription_entity = payload.get('subscription', {}).get('entity', {})
    subscription_id = subscription_entity.get('id')
    
    if subscription_id:
        await db.subscriptions.update_one(
            {"razorpay_subscription_id": subscription_id},
            {"$set": {"status": "completed", "updated_at": datetime.now(timezone.utc).isoformat()}}
        )
        logger.info(f"Subscription completed via webhook: {subscription_id}")


async def handle_subscription_pending(db, payload):
    """Handle subscription.pending webhook"""
    subscription_entity = payload.get('subscription', {}).get('entity', {})
    subscription_id = subscription_entity.get('id')
    
    if subscription_id:
        await db.subscriptions.update_one(
            {"razorpay_subscription_id": subscription_id},
            {"$set": {"status": "pending", "updated_at": datetime.now(timezone.utc).isoformat()}}
        )
        logger.info(f"Subscription pending via webhook: {subscription_id}")


async def handle_subscription_halted(db, payload):
    """Handle subscription.halted webhook - payment failed multiple times"""
    subscription_entity = payload.get('subscription', {}).get('entity', {})
    subscription_id = subscription_entity.get('id')
    
    if subscription_id:
        subscription_record = await db.subscriptions.find_one({"razorpay_subscription_id": subscription_id})
        
        if subscription_record:
            await db.subscriptions.update_one(
                {"razorpay_subscription_id": subscription_id},
                {
                    "$set": {"status": "halted", "updated_at": datetime.now(timezone.utc).isoformat()},
                    "$inc": {"failed_payments": 1}
                }
            )
            
            # Optionally downgrade user to free plan
            await db.users.update_one(
                {"id": subscription_record['user_id']},
                {
                    "$set": {
                        "plan": "free",
                        "credits_limit": 100,
                        "credits_used": 0
                    }
                }
            )
            
            logger.warning(f"Subscription halted via webhook: {subscription_id}")


async def handle_payment_failed(db, payload):
    """Handle payment.failed webhook"""
    payment_entity = payload.get('payment', {}).get('entity', {})
    subscription_id = payment_entity.get('subscription_id')
    payment_id = payment_entity.get('id')
    
    if subscription_id:
        subscription_record = await db.subscriptions.find_one({"razorpay_subscription_id": subscription_id})
        
        if subscription_record:
            await db.subscriptions.update_one(
                {"razorpay_subscription_id": subscription_id},
                {"$inc": {"failed_payments": 1, "total_payments": 1}}
            )
            
            # Log failed payment
            await log_payment_attempt(
                db=db,
                user_id=subscription_record['user_id'],
                plan_id=subscription_record['plan_id'],
                amount=subscription_record['amount'],
                status='failed_webhook',
                details={
                    'subscription_id': subscription_id,
                    'payment_id': payment_id,
                    'error': payment_entity.get('error_description')
                }
            )
            
            logger.warning(f"Payment failed for subscription {subscription_id}: {payment_id}")


# ============= Payment History =============

@router.get("/history", response_model=List[Payment])
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
        if isinstance(payment.get('completed_at'), str):
            payment['completed_at'] = datetime.fromisoformat(payment['completed_at'])
        if isinstance(payment.get('next_billing_date'), str):
            payment['next_billing_date'] = datetime.fromisoformat(payment['next_billing_date'])
    
    return [Payment(**payment) for payment in payments]
