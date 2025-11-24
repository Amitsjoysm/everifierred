import hmac
import hashlib
import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from fastapi import HTTPException

from config import settings


logger = logging.getLogger(__name__)


def verify_razorpay_signature(
    order_id: str,
    payment_id: str,
    signature: str
) -> bool:
    """
    Verify Razorpay payment signature
    
    Args:
        order_id: Razorpay order ID
        payment_id: Razorpay payment ID  
        signature: Signature to verify
    
    Returns:
        True if signature is valid, False otherwise
    """
    try:
        body = order_id + "|" + payment_id
        expected_signature = hmac.new(
            key=settings.RAZORPAY_KEY_SECRET.encode('utf-8'),
            msg=body.encode('utf-8'),
            digestmod=hashlib.sha256
        ).hexdigest()
        
        is_valid = hmac.compare_digest(expected_signature, signature)
        
        if not is_valid:
            logger.warning(
                f"Invalid payment signature detected. "
                f"Order: {order_id}, Payment: {payment_id}"
            )
        
        return is_valid
    except Exception as e:
        logger.error(f"Error verifying payment signature: {str(e)}")
        return False


def verify_webhook_signature(
    webhook_body: str,
    webhook_signature: str,
    webhook_secret: str
) -> bool:
    """
    Verify Razorpay webhook signature
    
    Args:
        webhook_body: Raw webhook body as string
        webhook_signature: X-Razorpay-Signature header value
        webhook_secret: Webhook secret from Razorpay dashboard
    
    Returns:
        True if signature is valid, False otherwise
    """
    try:
        expected_signature = hmac.new(
            key=webhook_secret.encode('utf-8'),
            msg=webhook_body.encode('utf-8'),
            digestmod=hashlib.sha256
        ).hexdigest()
        
        is_valid = hmac.compare_digest(expected_signature, webhook_signature)
        
        if not is_valid:
            logger.warning("Invalid webhook signature detected")
        
        return is_valid
    except Exception as e:
        logger.error(f"Error verifying webhook signature: {str(e)}")
        return False


async def validate_payment_amount(
    db,
    plan_id: str,
    payment_amount: float,
    tolerance: float = 0.01
) -> bool:
    """
    Validate that payment amount matches plan price
    
    Args:
        db: Database connection
        plan_id: Plan ID to validate against
        payment_amount: Amount paid
        tolerance: Acceptable difference (for rounding)
    
    Returns:
        True if amount is valid, False otherwise
    """
    try:
        plan = await db.plans.find_one({"id": plan_id, "is_active": True}, {"_id": 0})
        
        if not plan:
            logger.warning(f"Plan not found for validation: {plan_id}")
            return False
        
        expected_amount = plan['price']
        amount_difference = abs(payment_amount - expected_amount)
        
        is_valid = amount_difference <= tolerance
        
        if not is_valid:
            logger.warning(
                f"Payment amount mismatch. Expected: {expected_amount}, "
                f"Got: {payment_amount}, Plan: {plan_id}"
            )
        
        return is_valid
    except Exception as e:
        logger.error(f"Error validating payment amount: {str(e)}")
        return False


async def log_payment_attempt(
    db,
    user_id: str,
    plan_id: str,
    amount: float,
    status: str,
    details: Optional[Dict[str, Any]] = None
):
    """
    Log payment attempt for audit trail
    
    Args:
        db: Database connection
        user_id: User ID
        plan_id: Plan ID
        amount: Payment amount
        status: Payment status (success, failed, pending)
        details: Additional details
    """
    try:
        log_entry = {
            "user_id": user_id,
            "plan_id": plan_id,
            "amount": amount,
            "status": status,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "details": details or {}
        }
        
        await db.payment_logs.insert_one(log_entry)
        
        logger.info(
            f"Payment attempt logged: User {user_id}, Plan {plan_id}, "
            f"Status {status}, Amount {amount}"
        )
    except Exception as e:
        logger.error(f"Error logging payment attempt: {str(e)}")


async def log_security_event(
    db,
    event_type: str,
    severity: str,
    description: str,
    details: Optional[Dict[str, Any]] = None
):
    """
    Log security event for monitoring
    
    Args:
        db: Database connection
        event_type: Type of security event
        severity: Event severity (low, medium, high, critical)
        description: Event description
        details: Additional details
    """
    try:
        log_entry = {
            "event_type": event_type,
            "severity": severity,
            "description": description,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "details": details or {}
        }
        
        await db.security_logs.insert_one(log_entry)
        
        logger.warning(
            f"Security event: {event_type} ({severity}) - {description}"
        )
    except Exception as e:
        logger.error(f"Error logging security event: {str(e)}")


def check_payment_idempotency(
    existing_payment: Optional[Dict],
    new_payment_id: str
) -> bool:
    """
    Check if payment is duplicate/already processed
    
    Args:
        existing_payment: Existing payment record
        new_payment_id: New payment ID to check
    
    Returns:
        True if payment is duplicate, False otherwise
    """
    if not existing_payment:
        return False
    
    # Check if payment already processed
    if existing_payment.get('status') == 'success':
        if existing_payment.get('razorpay_payment_id') == new_payment_id:
            logger.warning(
                f"Duplicate payment attempt detected: {new_payment_id}"
            )
            return True
    
    return False
