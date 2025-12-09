"""
Admin Payment Management Routes
Production-ready Razorpay administration and monitoring
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from datetime import datetime, timezone, timedelta
from typing import List, Optional, Dict, Any
import razorpay
import logging
from pydantic import BaseModel
from pathlib import Path

from database import get_db
from models import User, Payment
from auth import get_current_admin_user
from config import settings
from invoice_generator import InvoiceGenerator, generate_invoice_number

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin/payments", tags=["Payment Admin"])

# Initialize Razorpay client
razorpay_client = None
if settings.RAZORPAY_KEY_ID and settings.RAZORPAY_KEY_SECRET:
    razorpay_client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))


# ============= Pydantic Models =============

class RefundRequest(BaseModel):
    payment_id: str
    amount: Optional[float] = None  # None means full refund
    reason: str


class WebhookConfig(BaseModel):
    webhook_secret: str
    enabled: bool = True


class PaymentRetryRequest(BaseModel):
    payment_id: str
    notify_user: bool = True


# ============= Payment Dashboard =============

@router.get("/dashboard")
async def get_payment_dashboard(
    days: int = Query(default=30, ge=1, le=365),
    current_user: User = Depends(get_current_admin_user)
):
    """Get comprehensive payment dashboard statistics"""
    db = await get_db()
    
    # Calculate date range
    end_date = datetime.now(timezone.utc)
    start_date = end_date - timedelta(days=days)
    
    # Convert to ISO format for MongoDB query
    start_date_iso = start_date.isoformat()
    end_date_iso = end_date.isoformat()
    
    # Total payments
    all_payments = await db.payments.find({}, {"_id": 0}).to_list(10000)
    
    # Filter by date range
    period_payments = [
        p for p in all_payments
        if start_date_iso <= p.get('created_at', '') <= end_date_iso
    ]
    
    # Calculate statistics
    total_revenue = sum(p.get('amount', 0) for p in all_payments if p.get('status') == 'success')
    period_revenue = sum(p.get('amount', 0) for p in period_payments if p.get('status') == 'success')
    
    total_transactions = len(all_payments)
    successful_payments = len([p for p in all_payments if p.get('status') == 'success'])
    failed_payments = len([p for p in all_payments if p.get('status') == 'failed'])
    pending_payments = len([p for p in all_payments if p.get('status') == 'pending'])
    
    period_successful = len([p for p in period_payments if p.get('status') == 'success'])
    period_failed = len([p for p in period_payments if p.get('status') == 'failed'])
    
    # Conversion rate
    conversion_rate = (successful_payments / total_transactions * 100) if total_transactions > 0 else 0
    
    # Average transaction value
    avg_transaction = total_revenue / successful_payments if successful_payments > 0 else 0
    
    # Revenue by plan
    revenue_by_plan = {}
    for payment in all_payments:
        if payment.get('status') == 'success':
            plan_id = payment.get('plan_id', 'unknown')
            revenue_by_plan[plan_id] = revenue_by_plan.get(plan_id, 0) + payment.get('amount', 0)
    
    # Daily revenue trend (last 30 days)
    daily_revenue = {}
    for i in range(min(days, 30)):
        day = (end_date - timedelta(days=i)).strftime('%Y-%m-%d')
        daily_revenue[day] = 0
    
    for payment in period_payments:
        if payment.get('status') == 'success':
            payment_date = payment.get('created_at', '')[:10]
            if payment_date in daily_revenue:
                daily_revenue[payment_date] += payment.get('amount', 0)
    
    # Top customers by revenue
    customer_revenue = {}
    for payment in all_payments:
        if payment.get('status') == 'success':
            user_id = payment.get('user_id')
            customer_revenue[user_id] = customer_revenue.get(user_id, 0) + payment.get('amount', 0)
    
    top_customers = sorted(
        [{'user_id': k, 'revenue': v} for k, v in customer_revenue.items()],
        key=lambda x: x['revenue'],
        reverse=True
    )[:10]
    
    # Security events count
    security_events = await db.security_logs.count_documents({
        'timestamp': {'$gte': start_date_iso, '$lte': end_date_iso}
    })
    
    # Failed payment reasons
    failed_reasons = {}
    for payment in all_payments:
        if payment.get('status') == 'failed':
            reason = payment.get('error_message', 'Unknown')
            failed_reasons[reason] = failed_reasons.get(reason, 0) + 1
    
    return {
        "overview": {
            "total_revenue": round(total_revenue, 2),
            "period_revenue": round(period_revenue, 2),
            "total_transactions": total_transactions,
            "successful_payments": successful_payments,
            "failed_payments": failed_payments,
            "pending_payments": pending_payments,
            "conversion_rate": round(conversion_rate, 2),
            "average_transaction_value": round(avg_transaction, 2)
        },
        "period_stats": {
            "days": days,
            "successful": period_successful,
            "failed": period_failed,
            "revenue": round(period_revenue, 2)
        },
        "revenue_by_plan": revenue_by_plan,
        "daily_revenue": dict(sorted(daily_revenue.items())),
        "top_customers": top_customers,
        "security_events": security_events,
        "failed_payment_reasons": failed_reasons
    }


@router.get("/transactions")
async def get_all_transactions(
    status: Optional[str] = Query(None, regex="^(success|failed|pending|cancelled|expired)$"),
    limit: int = Query(default=50, ge=1, le=500),
    skip: int = Query(default=0, ge=0),
    current_user: User = Depends(get_current_admin_user)
):
    """Get all payment transactions with filtering"""
    db = await get_db()
    
    # Build query
    query = {}
    if status:
        query["status"] = status
    
    # Fetch payments
    payments = await db.payments.find(
        query,
        {"_id": 0}
    ).sort("created_at", -1).skip(skip).limit(limit).to_list(limit)
    
    # Get total count
    total_count = await db.payments.count_documents(query)
    
    # Enrich with user information
    for payment in payments:
        user = await db.users.find_one(
            {"id": payment.get('user_id')},
            {"_id": 0, "email": 1, "full_name": 1}
        )
        if user:
            payment['user_email'] = user.get('email')
            payment['user_name'] = user.get('full_name')
    
    return {
        "payments": payments,
        "total": total_count,
        "limit": limit,
        "skip": skip,
        "has_more": total_count > (skip + limit)
    }


# ============= Refund Management =============

@router.post("/refund")
async def process_refund(
    refund_data: RefundRequest,
    current_user: User = Depends(get_current_admin_user)
):
    """Process payment refund"""
    if not razorpay_client:
        raise HTTPException(status_code=503, detail="Payment service not configured")
    
    db = await get_db()
    
    # Find payment record
    payment = await db.payments.find_one({"id": refund_data.payment_id}, {"_id": 0})
    
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    
    if payment.get('status') != 'success':
        raise HTTPException(status_code=400, detail="Can only refund successful payments")
    
    # Check if already refunded
    if payment.get('refund_status') == 'refunded':
        raise HTTPException(status_code=400, detail="Payment already refunded")
    
    razorpay_payment_id = payment.get('razorpay_payment_id')
    if not razorpay_payment_id:
        raise HTTPException(status_code=400, detail="Payment ID not found")
    
    # Calculate refund amount
    refund_amount = refund_data.amount if refund_data.amount else payment.get('amount', 0)
    refund_amount_paise = int(refund_amount * 100)
    
    try:
        # Create refund in Razorpay
        refund = razorpay_client.payment.refund(
            razorpay_payment_id,
            {
                "amount": refund_amount_paise,
                "notes": {
                    "reason": refund_data.reason,
                    "admin_id": current_user.id
                }
            }
        )
        
        # Update payment record
        await db.payments.update_one(
            {"id": refund_data.payment_id},
            {
                "$set": {
                    "refund_status": "refunded" if refund_amount == payment.get('amount') else "partial_refund",
                    "refund_amount": refund_amount,
                    "refund_id": refund['id'],
                    "refund_reason": refund_data.reason,
                    "refunded_at": datetime.now(timezone.utc).isoformat(),
                    "refunded_by": current_user.id
                }
            }
        )
        
        # Deduct credits from user if they were added
        user_id = payment.get('user_id')
        plan = await db.plans.find_one({"id": payment.get('plan_id')}, {"_id": 0})
        
        if plan:
            # Reset user to free plan
            await db.users.update_one(
                {"id": user_id},
                {
                    "$set": {
                        "plan": "free",
                        "credits_limit": 100,  # Free plan credits
                        "updated_at": datetime.now(timezone.utc).isoformat()
                    }
                }
            )
        
        # Log refund
        await db.refund_logs.insert_one({
            "refund_id": refund['id'],
            "payment_id": refund_data.payment_id,
            "razorpay_payment_id": razorpay_payment_id,
            "amount": refund_amount,
            "reason": refund_data.reason,
            "admin_id": current_user.id,
            "admin_email": current_user.email,
            "created_at": datetime.now(timezone.utc).isoformat()
        })
        
        logger.info(f"Refund processed: {refund['id']} for payment {refund_data.payment_id}")
        
        return {
            "message": "Refund processed successfully",
            "refund_id": refund['id'],
            "amount": refund_amount,
            "status": refund['status']
        }
        
    except Exception as e:
        logger.error(f"Refund failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Refund failed: {str(e)}")


@router.get("/refunds")
async def get_refunds(
    limit: int = Query(default=50, ge=1, le=500),
    current_user: User = Depends(get_current_admin_user)
):
    """Get all refund records"""
    db = await get_db()
    
    refunds = await db.refund_logs.find(
        {},
        {"_id": 0}
    ).sort("created_at", -1).limit(limit).to_list(limit)
    
    return {
        "refunds": refunds,
        "count": len(refunds)
    }


# ============= Fraud Detection & Security =============

@router.get("/security-events")
async def get_security_events(
    severity: Optional[str] = Query(None, regex="^(low|medium|high|critical)$"),
    days: int = Query(default=7, ge=1, le=90),
    limit: int = Query(default=100, ge=1, le=1000),
    current_user: User = Depends(get_current_admin_user)
):
    """Get security events and fraud alerts"""
    db = await get_db()
    
    # Calculate date range
    start_date = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
    
    # Build query
    query = {
        "timestamp": {"$gte": start_date}
    }
    if severity:
        query["severity"] = severity
    
    # Fetch events
    events = await db.security_logs.find(
        query,
        {"_id": 0}
    ).sort("timestamp", -1).limit(limit).to_list(limit)
    
    # Count by severity
    severity_counts = {
        "low": 0,
        "medium": 0,
        "high": 0,
        "critical": 0
    }
    
    for event in events:
        sev = event.get('severity', 'low')
        severity_counts[sev] = severity_counts.get(sev, 0) + 1
    
    # Count by event type
    event_type_counts = {}
    for event in events:
        event_type = event.get('event_type', 'unknown')
        event_type_counts[event_type] = event_type_counts.get(event_type, 0) + 1
    
    return {
        "events": events,
        "count": len(events),
        "severity_breakdown": severity_counts,
        "event_type_breakdown": event_type_counts,
        "period_days": days
    }


@router.get("/fraud-analysis")
async def fraud_analysis(
    current_user: User = Depends(get_current_admin_user)
):
    """Analyze payment patterns for fraud detection"""
    db = await get_db()
    
    # Get all payments
    payments = await db.payments.find({}, {"_id": 0}).to_list(10000)
    
    # Failed payment rate by user
    user_failure_rate = {}
    for payment in payments:
        user_id = payment.get('user_id')
        if user_id not in user_failure_rate:
            user_failure_rate[user_id] = {"total": 0, "failed": 0}
        
        user_failure_rate[user_id]["total"] += 1
        if payment.get('status') == 'failed':
            user_failure_rate[user_id]["failed"] += 1
    
    # Identify suspicious users (high failure rate)
    suspicious_users = []
    for user_id, stats in user_failure_rate.items():
        if stats["total"] >= 3:  # At least 3 attempts
            failure_rate = stats["failed"] / stats["total"] * 100
            if failure_rate >= 70:  # 70% or more failures
                user_data = await db.users.find_one(
                    {"id": user_id},
                    {"_id": 0, "email": 1, "full_name": 1, "created_at": 1}
                )
                if user_data:
                    suspicious_users.append({
                        "user_id": user_id,
                        "email": user_data.get('email'),
                        "full_name": user_data.get('full_name'),
                        "total_attempts": stats["total"],
                        "failed_attempts": stats["failed"],
                        "failure_rate": round(failure_rate, 2)
                    })
    
    # Multiple payments in short time (potential card testing)
    rapid_payments = {}
    sorted_payments = sorted(payments, key=lambda x: x.get('created_at', ''))
    
    for i in range(len(sorted_payments) - 1):
        current_payment = sorted_payments[i]
        next_payment = sorted_payments[i + 1]
        
        if current_payment.get('user_id') == next_payment.get('user_id'):
            try:
                time_diff = datetime.fromisoformat(next_payment.get('created_at', '')) - \
                           datetime.fromisoformat(current_payment.get('created_at', ''))
                
                if time_diff.total_seconds() < 60:  # Within 1 minute
                    user_id = current_payment.get('user_id')
                    rapid_payments[user_id] = rapid_payments.get(user_id, 0) + 1
            except:
                pass
    
    # Amount anomalies (unusually high amounts)
    successful_amounts = [p.get('amount', 0) for p in payments if p.get('status') == 'success']
    if successful_amounts:
        avg_amount = sum(successful_amounts) / len(successful_amounts)
        anomalous_payments = [
            {
                "payment_id": p.get('id'),
                "user_id": p.get('user_id'),
                "amount": p.get('amount'),
                "avg_amount": round(avg_amount, 2),
                "created_at": p.get('created_at')
            }
            for p in payments
            if p.get('status') == 'success' and p.get('amount', 0) > avg_amount * 3
        ]
    else:
        anomalous_payments = []
    
    return {
        "suspicious_users": sorted(suspicious_users, key=lambda x: x['failure_rate'], reverse=True),
        "rapid_payment_attempts": [
            {"user_id": k, "attempts_within_minute": v}
            for k, v in rapid_payments.items()
            if v >= 2
        ],
        "anomalous_high_payments": anomalous_payments[:10],
        "total_fraud_indicators": len(suspicious_users) + len(rapid_payments) + len(anomalous_payments)
    }


# ============= Webhook Configuration =============

@router.get("/webhook-config")
async def get_webhook_config(
    current_user: User = Depends(get_current_admin_user)
):
    """Get webhook configuration"""
    db = await get_db()
    
    config = await db.webhook_config.find_one({}, {"_id": 0})
    
    if not config:
        return {
            "webhook_secret": "",
            "enabled": True,
            "webhook_url": f"{settings.APP_URL}/api/payments/webhook"
        }
    
    return {
        "webhook_secret": config.get('webhook_secret', ''),
        "enabled": config.get('enabled', True),
        "webhook_url": f"{settings.APP_URL}/api/payments/webhook"
    }


@router.post("/webhook-config")
async def update_webhook_config(
    config_data: WebhookConfig,
    current_user: User = Depends(get_current_admin_user)
):
    """Update webhook configuration"""
    db = await get_db()
    
    config_dict = {
        "webhook_secret": config_data.webhook_secret,
        "enabled": config_data.enabled,
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "updated_by": current_user.id
    }
    
    await db.webhook_config.update_one(
        {},
        {"$set": config_dict},
        upsert=True
    )
    
    logger.info(f"Webhook configuration updated by {current_user.email}")
    
    return {
        "message": "Webhook configuration updated successfully",
        "config": config_dict
    }


# ============= Payment Analytics =============

@router.get("/analytics/revenue")
async def revenue_analytics(
    period: str = Query(default="month", regex="^(week|month|quarter|year)$"),
    current_user: User = Depends(get_current_admin_user)
):
    """Get detailed revenue analytics"""
    db = await get_db()
    
    # Determine date range
    end_date = datetime.now(timezone.utc)
    if period == "week":
        start_date = end_date - timedelta(days=7)
        interval_days = 1
    elif period == "month":
        start_date = end_date - timedelta(days=30)
        interval_days = 1
    elif period == "quarter":
        start_date = end_date - timedelta(days=90)
        interval_days = 7
    else:  # year
        start_date = end_date - timedelta(days=365)
        interval_days = 30
    
    start_date_iso = start_date.isoformat()
    end_date_iso = end_date.isoformat()
    
    # Fetch successful payments in period
    payments = await db.payments.find(
        {
            "status": "success",
            "created_at": {"$gte": start_date_iso, "$lte": end_date_iso}
        },
        {"_id": 0}
    ).to_list(10000)
    
    # Calculate metrics
    total_revenue = sum(p.get('amount', 0) for p in payments)
    total_transactions = len(payments)
    avg_transaction_value = total_revenue / total_transactions if total_transactions > 0 else 0
    
    # Group by plan
    plan_breakdown = {}
    for payment in payments:
        plan_id = payment.get('plan_id', 'unknown')
        if plan_id not in plan_breakdown:
            plan_breakdown[plan_id] = {"count": 0, "revenue": 0}
        plan_breakdown[plan_id]["count"] += 1
        plan_breakdown[plan_id]["revenue"] += payment.get('amount', 0)
    
    # Time series data
    time_series = []
    current = start_date
    while current <= end_date:
        period_end = current + timedelta(days=interval_days)
        current_iso = current.isoformat()
        period_end_iso = period_end.isoformat()
        
        period_payments = [
            p for p in payments
            if current_iso <= p.get('created_at', '') < period_end_iso
        ]
        
        period_revenue = sum(p.get('amount', 0) for p in period_payments)
        
        time_series.append({
            "date": current.strftime('%Y-%m-%d'),
            "revenue": round(period_revenue, 2),
            "transactions": len(period_payments)
        })
        
        current = period_end
    
    return {
        "period": period,
        "start_date": start_date.strftime('%Y-%m-%d'),
        "end_date": end_date.strftime('%Y-%m-%d'),
        "summary": {
            "total_revenue": round(total_revenue, 2),
            "total_transactions": total_transactions,
            "average_transaction_value": round(avg_transaction_value, 2)
        },
        "plan_breakdown": plan_breakdown,
        "time_series": time_series
    }


# ============= Transaction Reconciliation =============

@router.get("/reconciliation")
async def payment_reconciliation(
    days: int = Query(default=7, ge=1, le=90),
    current_user: User = Depends(get_current_admin_user)
):
    """Reconcile payments with Razorpay"""
    if not razorpay_client:
        raise HTTPException(status_code=503, detail="Payment service not configured")
    
    db = await get_db()
    
    # Calculate date range
    start_date = datetime.now(timezone.utc) - timedelta(days=days)
    start_timestamp = int(start_date.timestamp())
    
    try:
        # Fetch payments from Razorpay
        razorpay_payments = razorpay_client.payment.all({
            "from": start_timestamp,
            "count": 100
        })
        
        # Fetch our database payments
        db_payments = await db.payments.find(
            {"created_at": {"$gte": start_date.isoformat()}},
            {"_id": 0}
        ).to_list(1000)
        
        # Create lookup maps
        db_payment_map = {p.get('razorpay_payment_id'): p for p in db_payments if p.get('razorpay_payment_id')}
        razorpay_payment_map = {p['id']: p for p in razorpay_payments.get('items', [])}
        
        # Find discrepancies
        missing_in_db = []
        status_mismatches = []
        amount_mismatches = []
        
        for rp_id, rp in razorpay_payment_map.items():
            if rp_id not in db_payment_map:
                missing_in_db.append({
                    "razorpay_payment_id": rp_id,
                    "amount": rp.get('amount', 0) / 100,
                    "status": rp.get('status'),
                    "created_at": datetime.fromtimestamp(rp.get('created_at')).isoformat()
                })
            else:
                db_payment = db_payment_map[rp_id]
                
                # Check status mismatch
                rp_status = "success" if rp.get('status') == 'captured' else rp.get('status')
                if db_payment.get('status') != rp_status:
                    status_mismatches.append({
                        "payment_id": rp_id,
                        "db_status": db_payment.get('status'),
                        "razorpay_status": rp_status
                    })
                
                # Check amount mismatch
                rp_amount = rp.get('amount', 0) / 100
                db_amount = db_payment.get('amount', 0)
                if abs(rp_amount - db_amount) > 0.01:
                    amount_mismatches.append({
                        "payment_id": rp_id,
                        "db_amount": db_amount,
                        "razorpay_amount": rp_amount
                    })
        
        return {
            "period_days": days,
            "total_razorpay_payments": len(razorpay_payments.get('items', [])),
            "total_db_payments": len(db_payments),
            "discrepancies": {
                "missing_in_db": missing_in_db,
                "status_mismatches": status_mismatches,
                "amount_mismatches": amount_mismatches
            },
            "total_discrepancies": len(missing_in_db) + len(status_mismatches) + len(amount_mismatches)
        }
        
    except Exception as e:
        logger.error(f"Reconciliation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Reconciliation failed: {str(e)}")


# ============= Failed Payment Retry =============

@router.post("/retry-payment")
async def retry_failed_payment(
    retry_data: PaymentRetryRequest,
    current_user: User = Depends(get_current_admin_user)
):
    """Retry a failed payment"""
    db = await get_db()
    
    # Find payment
    payment = await db.payments.find_one({"id": retry_data.payment_id}, {"_id": 0})
    
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    
    if payment.get('status') not in ['failed', 'expired']:
        raise HTTPException(status_code=400, detail="Can only retry failed or expired payments")
    
    # Mark for retry
    await db.payments.update_one(
        {"id": retry_data.payment_id},
        {
            "$set": {
                "retry_scheduled": True,
                "retry_scheduled_at": datetime.now(timezone.utc).isoformat(),
                "retry_scheduled_by": current_user.id
            }
        }
    )
    
    # If notification enabled, could send email to user here
    if retry_data.notify_user:
        user = await db.users.find_one({"id": payment.get('user_id')}, {"_id": 0, "email": 1})
        if user:
            # TODO: Send retry notification email
            logger.info(f"Retry notification would be sent to {user.get('email')}")
    
    logger.info(f"Payment retry scheduled: {retry_data.payment_id}")
    
    return {
        "message": "Payment marked for retry",
        "payment_id": retry_data.payment_id,
        "user_notified": retry_data.notify_user
    }


@router.get("/payment-logs")
async def get_payment_logs(


# ============= Invoice Generation =============

@router.post("/generate-invoice/{payment_id}")
async def generate_invoice(
    payment_id: str,
    current_user: User = Depends(get_current_admin_user)
):
    """Generate PDF invoice for a successful payment"""
    db = await get_db()
    
    # Fetch payment
    payment = await db.payments.find_one({"id": payment_id}, {"_id": 0})
    
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    
    if payment.get('status') != 'success':
        raise HTTPException(status_code=400, detail="Can only generate invoices for successful payments")
    
    # Fetch user data
    user = await db.users.find_one({"id": payment.get('user_id')}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Fetch plan data
    plan = await db.plans.find_one({"id": payment.get('plan_id')}, {"_id": 0})
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    
    # Generate invoice number
    invoice_number = generate_invoice_number(payment.get('id'), payment.get('created_at'))
    
    try:
        # Generate invoice
        invoice_gen = InvoiceGenerator()
        invoice_path = invoice_gen.generate_invoice(
            payment_data=payment,
            user_data=user,
            plan_data=plan,
            invoice_number=invoice_number
        )
        
        # Store invoice reference in database
        await db.payments.update_one(
            {"id": payment_id},
            {
                "$set": {
                    "invoice_number": invoice_number,
                    "invoice_path": invoice_path,
                    "invoice_generated_at": datetime.now(timezone.utc).isoformat(),
                    "invoice_generated_by": current_user.id
                }
            }
        )
        
        logger.info(f"Invoice generated: {invoice_number} for payment {payment_id}")
        
        return {
            "message": "Invoice generated successfully",
            "invoice_number": invoice_number,
            "invoice_path": invoice_path
        }
        
    except Exception as e:
        logger.error(f"Invoice generation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Invoice generation failed: {str(e)}")


@router.get("/download-invoice/{payment_id}")
async def download_invoice(
    payment_id: str,
    current_user: User = Depends(get_current_admin_user)
):
    """Download invoice PDF"""
    db = await get_db()
    
    # Fetch payment with invoice
    payment = await db.payments.find_one({"id": payment_id}, {"_id": 0})
    
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    
    invoice_path = payment.get('invoice_path')
    invoice_number = payment.get('invoice_number')
    
    if not invoice_path or not Path(invoice_path).exists():
        # Try to generate invoice if not exists
        if payment.get('status') == 'success':
            user = await db.users.find_one({"id": payment.get('user_id')}, {"_id": 0})
            plan = await db.plans.find_one({"id": payment.get('plan_id')}, {"_id": 0})
            
            if user and plan:
                invoice_number = generate_invoice_number(payment.get('id'), payment.get('created_at'))
                invoice_gen = InvoiceGenerator()
                invoice_path = invoice_gen.generate_invoice(
                    payment_data=payment,
                    user_data=user,
                    plan_data=plan,
                    invoice_number=invoice_number
                )
                
                # Update database
                await db.payments.update_one(
                    {"id": payment_id},
                    {
                        "$set": {
                            "invoice_number": invoice_number,
                            "invoice_path": invoice_path,
                            "invoice_generated_at": datetime.now(timezone.utc).isoformat(),
                            "invoice_generated_by": current_user.id
                        }
                    }
                )
        else:
            raise HTTPException(status_code=404, detail="Invoice not found and cannot be generated")
    
    # Return PDF file
    return FileResponse(
        path=invoice_path,
        media_type='application/pdf',
        filename=f"invoice_{invoice_number}.pdf"
    )


@router.get("/invoices")
async def get_all_invoices(
    limit: int = Query(default=50, ge=1, le=500),
    current_user: User = Depends(get_current_admin_user)
):
    """Get all generated invoices"""
    db = await get_db()
    
    # Fetch payments with invoices
    payments_with_invoices = await db.payments.find(
        {
            "invoice_number": {"$exists": True},
            "status": "success"
        },
        {"_id": 0}
    ).sort("invoice_generated_at", -1).limit(limit).to_list(limit)
    
    # Enrich with user info
    for payment in payments_with_invoices:
        user = await db.users.find_one(
            {"id": payment.get('user_id')},
            {"_id": 0, "email": 1, "full_name": 1}
        )
        if user:
            payment['user_email'] = user.get('email')
            payment['user_name'] = user.get('full_name')
    
    return {
        "invoices": payments_with_invoices,
        "count": len(payments_with_invoices)
    }


@router.post("/bulk-generate-invoices")
async def bulk_generate_invoices(
    days: int = Query(default=30, ge=1, le=365),
    current_user: User = Depends(get_current_admin_user)
):
    """Generate invoices for all successful payments in period that don't have invoices"""
    db = await get_db()
    
    # Calculate date range
    start_date = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
    
    # Find successful payments without invoices
    payments = await db.payments.find(
        {
            "status": "success",
            "created_at": {"$gte": start_date},
            "invoice_number": {"$exists": False}
        },
        {"_id": 0}
    ).to_list(1000)
    
    generated_count = 0
    failed_count = 0
    
    invoice_gen = InvoiceGenerator()
    
    for payment in payments:
        try:
            # Fetch user and plan
            user = await db.users.find_one({"id": payment.get('user_id')}, {"_id": 0})
            plan = await db.plans.find_one({"id": payment.get('plan_id')}, {"_id": 0})
            
            if not user or not plan:
                failed_count += 1
                continue
            
            # Generate invoice
            invoice_number = generate_invoice_number(payment.get('id'), payment.get('created_at'))
            invoice_path = invoice_gen.generate_invoice(
                payment_data=payment,
                user_data=user,
                plan_data=plan,
                invoice_number=invoice_number
            )
            
            # Update database
            await db.payments.update_one(
                {"id": payment.get('id')},
                {
                    "$set": {
                        "invoice_number": invoice_number,
                        "invoice_path": invoice_path,
                        "invoice_generated_at": datetime.now(timezone.utc).isoformat(),
                        "invoice_generated_by": current_user.id
                    }
                }
            )
            
            generated_count += 1
            
        except Exception as e:
            logger.error(f"Failed to generate invoice for payment {payment.get('id')}: {str(e)}")
            failed_count += 1
    
    return {
        "message": f"Bulk invoice generation completed",
        "total_payments": len(payments),
        "generated": generated_count,
        "failed": failed_count
    }

    days: int = Query(default=7, ge=1, le=90),
    limit: int = Query(default=100, ge=1, le=1000),
    current_user: User = Depends(get_current_admin_user)
):
    """Get payment attempt logs"""
    db = await get_db()
    
    start_date = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
    
    logs = await db.payment_logs.find(
        {"timestamp": {"$gte": start_date}},
        {"_id": 0}
    ).sort("timestamp", -1).limit(limit).to_list(limit)
    
    return {
        "logs": logs,
        "count": len(logs),
        "period_days": days
    }
