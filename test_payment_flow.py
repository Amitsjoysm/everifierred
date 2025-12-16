#!/usr/bin/env python3
"""
Test script to verify payment flow and identify issues
"""
import asyncio
import sys
sys.path.insert(0, '/app/backend')

from database import get_db
from datetime import datetime

async def check_payment_flow():
    db = await get_db()
    
    print("=" * 80)
    print("PAYMENT FLOW DIAGNOSTICS")
    print("=" * 80)
    
    # 1. Check plans
    print("\n1. ACTIVE PLANS:")
    plans = await db.plans.find({"is_active": True}, {"_id": 0}).to_list(10)
    for plan in plans:
        print(f"   - {plan.get('name')} (ID: {plan.get('id')})")
        print(f"     Price: ₹{plan.get('price')}, Credits: {plan.get('credits_limit')}")
        print(f"     Type: {plan.get('type')}, Razorpay: {plan.get('razorpay_plan_id', 'N/A')}")
    
    # 2. Check recent payments
    print("\n2. RECENT PAYMENTS (Last 10):")
    payments = await db.payments.find({}, {"_id": 0}).sort("created_at", -1).limit(10).to_list(10)
    if payments:
        for i, p in enumerate(payments, 1):
            print(f"\n   Payment #{i}:")
            print(f"   - User: {p.get('user_id')}")
            print(f"   - Plan: {p.get('plan_id')}")
            print(f"   - Status: {p.get('status')}")
            print(f"   - Amount: ₹{p.get('amount')}")
            print(f"   - Order ID: {p.get('razorpay_order_id')}")
            print(f"   - Payment ID: {p.get('razorpay_payment_id', 'N/A')}")
            print(f"   - Created: {p.get('created_at')}")
            if p.get('error_message'):
                print(f"   - Error: {p.get('error_message')}")
    else:
        print("   No payments found")
    
    # 3. Check payment logs
    print("\n3. PAYMENT LOGS (Last 10):")
    logs = await db.payment_logs.find({}, {"_id": 0}).sort("timestamp", -1).limit(10).to_list(10)
    if logs:
        for i, log in enumerate(logs, 1):
            print(f"\n   Log #{i}:")
            print(f"   - User: {log.get('user_id')}")
            print(f"   - Status: {log.get('status')}")
            print(f"   - Amount: ₹{log.get('amount')}")
            print(f"   - Timestamp: {log.get('timestamp')}")
            if log.get('details'):
                print(f"   - Details: {log.get('details')}")
    else:
        print("   No payment logs found")
    
    # 4. Check security events related to payments
    print("\n4. SECURITY EVENTS (Last 5):")
    events = await db.security_logs.find({}, {"_id": 0}).sort("timestamp", -1).limit(5).to_list(5)
    if events:
        for i, event in enumerate(events, 1):
            print(f"\n   Event #{i}:")
            print(f"   - Type: {event.get('event_type')}")
            print(f"   - Severity: {event.get('severity')}")
            print(f"   - Description: {event.get('description')}")
            print(f"   - Timestamp: {event.get('timestamp')}")
            if event.get('details'):
                print(f"   - Details: {event.get('details')}")
    else:
        print("   No security events found")
    
    # 5. Check users with paid plans
    print("\n5. USERS WITH PAID PLANS:")
    users = await db.users.find({"plan": {"$ne": "free"}}, {"_id": 0, "password_hash": 0}).limit(10).to_list(10)
    if users:
        for user in users:
            print(f"\n   - Email: {user.get('email')}")
            print(f"     Plan: {user.get('plan')}")
            print(f"     Credits: {user.get('credits_used', 0)}/{user.get('credits_limit', 0)}")
            print(f"     Updated: {user.get('updated_at', 'N/A')}")
    else:
        print("   No users with paid plans found")
    
    print("\n" + "=" * 80)
    print("DIAGNOSTICS COMPLETE")
    print("=" * 80)

if __name__ == "__main__":
    asyncio.run(check_payment_flow())
