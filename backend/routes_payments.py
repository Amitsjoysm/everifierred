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

router = APIRouter(prefix="/payments", tags=["Payments"])

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

@router.post("/create-order")
async def create_payment_order(
    plan_id: str,
    request: Request,
    current_user: User = Depends(get_current_user)
):
    """Create Razorpay order for plan subscription with rate limiting"""
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
            description=f"User {current_user.id} exceeded payment creation rate limit",
            details={"plan_id": plan_id}
        )
        raise HTTPException(
            status_code=429,
            detail="Too many payment requests. Please try again in 1 minute.",
            headers={"Retry-After": "60"}
        )
    
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
        
        # Log payment attempt
        await log_payment_attempt(
            db=db,
            user_id=current_user.id,
            plan_id=plan_id,
            amount=plan['price'],
            status='order_created',
            details={'order_id': razorpay_order['id']}
        )
        
        logger.info(f"Payment order created: {razorpay_order['id']} for user {current_user.id}")
        
        return {
            'order_id': razorpay_order['id'],
            'amount': razorpay_order['amount'],
            'currency': razorpay_order['currency'],
            'razorpay_key': settings.RAZORPAY_KEY_ID
        }
    except Exception as e:
        logger.error(f"Failed to create payment order: {str(e)}")
        await log_payment_attempt(
            db=db,
            user_id=current_user.id,
            plan_id=plan_id,
            amount=plan['price'],
            status='order_creation_failed',
            details={'error': str(e)}
        )
        raise HTTPException(status_code=500, detail=f"Failed to create order: {str(e)}")


@router.post("/payments/verify")
async def verify_payment(
    razorpay_order_id: str,
    razorpay_payment_id: str,
    razorpay_signature: str,
    plan_id: str,
    request: Request,
    current_user: User = Depends(get_current_user)
):
    """Verify Razorpay payment with enhanced security"""
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
            details={"order_id": razorpay_order_id}
        )
        raise HTTPException(
            status_code=429,
            detail="Too many verification requests. Please try again in 1 minute.",
            headers={"Retry-After": "60"}
        )
    
    if not razorpay_client:
        raise HTTPException(status_code=503, detail="Payment service not configured")
    
    db = await get_db()
    
    # Check if payment record exists
    payment_record = await db.payments.find_one({
        "razorpay_order_id": razorpay_order_id,
        "user_id": current_user.id
    })
    
    if not payment_record:
        await log_security_event(
            db=db,
            event_type="payment_verification_failed",
            severity="high",
            description="Payment record not found during verification",
            details={
                "order_id": razorpay_order_id,
                "user_id": current_user.id,
                "payment_id": razorpay_payment_id
            }
        )
        raise HTTPException(status_code=404, detail="Payment record not found")
    
    # Check idempotency - prevent duplicate processing
    if check_payment_idempotency(payment_record, razorpay_payment_id):
        await log_security_event(
            db=db,
            event_type="duplicate_payment_attempt",
            severity="high",
            description="Duplicate payment processing attempt detected",
            details={
                "order_id": razorpay_order_id,
                "payment_id": razorpay_payment_id,
                "user_id": current_user.id
            }
        )
        raise HTTPException(status_code=400, detail="Payment already processed")
    
    # Verify signature using security module
    if not verify_razorpay_signature(razorpay_order_id, razorpay_payment_id, razorpay_signature):
        # Mark payment as failed
        await db.payments.update_one(
            {"razorpay_order_id": razorpay_order_id},
            {"$set": {"status": "failed", "error_message": "Invalid signature"}}
        )
        
        await log_security_event(
            db=db,
            event_type="invalid_payment_signature",
            severity="critical",
            description="Invalid payment signature detected",
            details={
                "order_id": razorpay_order_id,
                "payment_id": razorpay_payment_id,
                "user_id": current_user.id
            }
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
    
    # Validate payment amount matches plan price
    if not await validate_payment_amount(db, plan_id, payment_record['amount']):
        await db.payments.update_one(
            {"razorpay_order_id": razorpay_order_id},
            {"$set": {"status": "failed", "error_message": "Payment amount mismatch"}}
        )
        
        await log_security_event(
            db=db,
            event_type="payment_amount_mismatch",
            severity="critical",
            description="Payment amount does not match plan price",
            details={
                "order_id": razorpay_order_id,
                "payment_id": razorpay_payment_id,
                "user_id": current_user.id,
                "expected_amount": plan['price'],
                "actual_amount": payment_record['amount']
            }
        )
        
        raise HTTPException(status_code=400, detail="Payment amount mismatch")
    
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
    
    # Log successful payment
    await log_payment_attempt(
        db=db,
        user_id=current_user.id,
        plan_id=plan_id,
        amount=plan['price'],
        status='success',
        details={
            'order_id': razorpay_order_id,
            'payment_id': razorpay_payment_id
        }
    )
    
    logger.info(
        f"Payment verified successfully: Order {razorpay_order_id}, "
        f"Payment {razorpay_payment_id}, User {current_user.id}"
    )
    
    return {
        "message": "Payment verified and plan upgraded successfully",
        "plan": plan['name'],
        "credits_limit": plan['credits_limit']
    }


@router.post("/payments/webhook")
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
    webhook_secret = settings.RAZORPAY_KEY_SECRET  # Use same secret or separate webhook secret
    
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
        # Log missing signature but don't fail (for backward compatibility)
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
    
    if event == 'payment.failed':
        payment_entity = payload.get('payment', {}).get('entity', {})
        order_id = payment_entity.get('order_id')
        payment_id = payment_entity.get('id')
        
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
            
            # Log failed payment
            payment_record = await db.payments.find_one({"razorpay_order_id": order_id})
            if payment_record:
                await log_payment_attempt(
                    db=db,
                    user_id=payment_record['user_id'],
                    plan_id=payment_record['plan_id'],
                    amount=payment_record['amount'],
                    status='failed_webhook',
                    details={
                        'order_id': order_id,
                        'payment_id': payment_id,
                        'error': payment_entity.get('error_description')
                    }
                )
            
            logger.warning(f"Payment failed via webhook: {order_id}")
    
    elif event == 'payment.captured':
        payment_entity = payload.get('payment', {}).get('entity', {})
        order_id = payment_entity.get('order_id')
        payment_id = payment_entity.get('id')
        amount_paid = payment_entity.get('amount', 0) / 100  # Convert from paise to rupees
        
        if order_id and payment_id:
            # Get payment record
            payment_record = await db.payments.find_one({"razorpay_order_id": order_id})
            
            if payment_record:
                # Validate amount
                if not await validate_payment_amount(db, payment_record['plan_id'], amount_paid):
                    await log_security_event(
                        db=db,
                        event_type="webhook_amount_mismatch",
                        severity="critical",
                        description="Webhook payment amount does not match expected",
                        details={
                            "order_id": order_id,
                            "payment_id": payment_id,
                            "expected_amount": payment_record['amount'],
                            "actual_amount": amount_paid
                        }
                    )
                    logger.error(f"Webhook amount mismatch for order {order_id}")
                    return {"status": "error", "message": "Amount mismatch"}
                
                if payment_record.get('status') != 'success':
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
                        
                        # Log successful payment via webhook
                        await log_payment_attempt(
                            db=db,
                            user_id=payment_record['user_id'],
                            plan_id=payment_record['plan_id'],
                            amount=payment_record['amount'],
                            status='success_webhook',
                            details={
                                'order_id': order_id,
                                'payment_id': payment_id
                            }
                        )
                        
                        logger.info(f"Payment captured via webhook: {order_id}")
    
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
