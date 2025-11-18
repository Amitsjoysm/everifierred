#!/usr/bin/env python3
"""
Debug payment endpoint issue
"""

import requests
import json
import asyncio
import sys
import os
sys.path.append('/app/backend')

BASE_URL = "https://verify-flow-fix-1.preview.emergentagent.com/api"
ADMIN_EMAIL = "admin@mailguard.com"
ADMIN_PASSWORD = "Admin@123456"

async def get_latest_otp():
    """Get the latest OTP from database"""
    from motor.motor_asyncio import AsyncIOMotorClient
    from config import settings
    
    client = AsyncIOMotorClient(settings.MONGO_URL)
    db = client[settings.DB_NAME]
    
    otp_record = await db.otp_store.find_one(
        {'email': ADMIN_EMAIL, 'purpose': 'login', 'is_used': False},
        sort=[('created_at', -1)]
    )
    
    client.close()
    
    if otp_record:
        return otp_record['otp']
    return None

async def test_payment_endpoint():
    session = requests.Session()
    
    # Step 1: Login
    print("1. Logging in...")
    login_data = {"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
    response = session.post(f"{BASE_URL}/auth/login", json=login_data)
    
    if response.status_code != 200:
        print(f"Login failed: {response.status_code}")
        return
    
    # Step 2: Get OTP and verify
    print("2. Getting OTP...")
    await asyncio.sleep(1)
    otp = await get_latest_otp()
    
    if not otp:
        print("Could not get OTP")
        return
    
    print(f"3. Verifying OTP: {otp}")
    verify_data = {"email": ADMIN_EMAIL, "otp": otp}
    response = session.post(f"{BASE_URL}/auth/verify-login", json=verify_data)
    
    if response.status_code != 200:
        print(f"OTP verification failed: {response.status_code}")
        print(response.text)
        return
    
    # Get token
    data = response.json()
    token = data.get("access_token")
    session.headers.update({"Authorization": f"Bearer {token}"})
    
    print("4. Authentication successful")
    
    # Step 3: Test payment endpoint
    print("5. Testing payment create-order endpoint...")
    plan_id = "9ad1886b-29fa-4595-b4eb-ff9803688a0e"  # Starter plan
    
    response = session.post(f"{BASE_URL}/payments/create-order", params={"plan_id": plan_id})
    
    print(f"Status Code: {response.status_code}")
    print(f"Response Headers: {dict(response.headers)}")
    print(f"Response Text: {response.text}")
    
    if response.status_code == 200:
        print("✅ Payment endpoint working!")
    else:
        print("❌ Payment endpoint failed")

if __name__ == "__main__":
    asyncio.run(test_payment_endpoint())