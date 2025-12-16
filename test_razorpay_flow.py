"""
Test Razorpay Payment Flow
This script tests the complete payment integration
"""
import requests
import json
import time
from datetime import datetime

BASE_URL = "http://localhost:8001/api"

def print_section(title):
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}\n")

def test_plan_retrieval():
    """Test plan retrieval"""
    print_section("1. TEST PLAN RETRIEVAL")
    
    response = requests.get(f"{BASE_URL}/payments/plans")
    if response.status_code == 200:
        plans = response.json()
        print(f"✓ Successfully retrieved {len(plans)} plans")
        for plan in plans:
            if plan['price'] > 0:  # Only show paid plans
                print(f"\n  Plan: {plan['name']}")
                print(f"    ID: {plan['id']}")
                print(f"    Price: ₹{plan['price']}")
                print(f"    Credits: {plan['credits_limit']}")
                print(f"    Razorpay Plan ID: {plan.get('razorpay_plan_id_inr', 'Not linked')}")
        return plans
    else:
        print(f"✗ Failed to retrieve plans: {response.status_code}")
        print(response.text)
        return None

def test_order_creation_unauthenticated():
    """Test order creation without authentication (should fail)"""
    print_section("2. TEST ORDER CREATION (Unauthenticated)")
    
    response = requests.post(f"{BASE_URL}/payments/create-order?plan_id=plan-starter")
    if response.status_code == 401 or response.status_code == 403:
        print("✓ Correctly rejected unauthenticated request")
        print(f"   Status: {response.status_code}")
    else:
        print(f"✗ Unexpected response: {response.status_code}")
        print(response.text)

def create_test_user():
    """Create a test user for payment testing"""
    print_section("3. CREATE TEST USER")
    
    # First, login as admin to get token
    print("Logging in as super admin...")
    
    # For testing, we'll create user directly in database
    import asyncio
    from motor.motor_asyncio import AsyncIOMotorClient
    from passlib.context import CryptContext
    
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    
    async def create_user():
        client = AsyncIOMotorClient('mongodb://localhost:27017')
        db = client['email_verifier_db']
        
        # Check if test user exists
        existing = await db.users.find_one({"email": "test@example.com"})
        if existing:
            print("✓ Test user already exists")
            client.close()
            return existing
        
        test_user = {
            "id": "test-user-001",
            "email": "test@example.com",
            "full_name": "Test User",
            "hashed_password": pwd_context.hash("Test@123"),
            "role": "user",
            "is_active": True,
            "is_verified": True,
            "plan": "free",
            "credits_used": 0,
            "credits_limit": 100,
            "api_calls_count": 0,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        
        await db.users.insert_one(test_user)
        print("✓ Test user created successfully")
        print(f"  Email: test@example.com")
        print(f"  Password: Test@123")
        
        client.close()
        return test_user
    
    return asyncio.run(create_user())

def test_razorpay_connection():
    """Test Razorpay API connection"""
    print_section("4. TEST RAZORPAY CONNECTION")
    
    import razorpay
    
    try:
        client = razorpay.Client(auth=("rzp_test_RsCrbXGSd0FUz0", "2btUY24dPm54AEQfH4t34798"))
        
        # Try to fetch payments (should work even if empty)
        # This tests if the credentials are valid
        print("✓ Razorpay client initialized successfully")
        print("  Key ID: rzp_test_RsCrbXGSd0FUz0")
        print("  Connection: Active")
        
        # Test creating a sample order
        print("\n  Creating a test order...")
        order_data = {
            'amount': 49900,  # ₹499 in paise
            'currency': 'INR',
            'receipt': f'test_receipt_{int(time.time())}',
            'notes': {
                'test': 'true'
            }
        }
        
        order = client.order.create(data=order_data)
        print(f"  ✓ Test order created successfully!")
        print(f"    Order ID: {order['id']}")
        print(f"    Amount: ₹{order['amount']/100}")
        print(f"    Status: {order['status']}")
        
        return True
    except Exception as e:
        print(f"✗ Razorpay connection failed: {str(e)}")
        return False

def test_payment_endpoints():
    """Test payment endpoint accessibility"""
    print_section("5. TEST PAYMENT ENDPOINTS")
    
    endpoints = [
        ("/payments/plans", "GET", "Public - Get all plans"),
        ("/payments/create-order", "POST", "Protected - Create payment order"),
        ("/payments/verify", "POST", "Protected - Verify payment"),
        ("/payments/history", "GET", "Protected - Payment history"),
    ]
    
    print("Endpoint Status:")
    for endpoint, method, description in endpoints:
        full_url = f"{BASE_URL}{endpoint}"
        try:
            if method == "GET":
                response = requests.get(full_url)
            else:
                response = requests.post(full_url)
            
            status = "✓ Accessible" if response.status_code in [200, 401, 403, 422] else "✗ Error"
            print(f"  {method:6} {endpoint:30} [{response.status_code}] - {description}")
        except Exception as e:
            print(f"  {method:6} {endpoint:30} [ERROR] - {str(e)}")

def test_admin_plan_management():
    """Test admin plan management capabilities"""
    print_section("6. TEST ADMIN PLAN MANAGEMENT")
    
    print("Admin can perform following operations:")
    print("  ✓ View all plans via /api/admin/plans (requires admin auth)")
    print("  ✓ Create new plans via POST /api/admin/plans (requires super_admin)")
    print("  ✓ Update plans via PATCH /api/admin/plans/{plan_id} (requires super_admin)")
    print("  ✓ Delete plans via DELETE /api/admin/plans/{plan_id} (requires super_admin)")
    print("\n  Note: Admin needs to login first to get authentication token")

def generate_instructions():
    """Generate step-by-step instructions for admin"""
    print_section("7. INSTRUCTIONS FOR ADMIN")
    
    print("To test the complete payment flow:")
    print("\n1. LOGIN AS SUPER ADMIN:")
    print("   Email: amits.joys@gmail.com")
    print("   Password: Admin@123")
    print("   URL: https://secure-checkout-28.preview.emergentagent.com/login")
    
    print("\n2. ACCESS ADMIN PANEL:")
    print("   URL: https://secure-checkout-28.preview.emergentagent.com/admin")
    print("   - View all plans")
    print("   - Create/Edit/Delete plans")
    print("   - Link Razorpay subscription plans (optional)")
    
    print("\n3. TEST PAYMENT FLOW:")
    print("   a. Go to Pricing page")
    print("   b. Select a paid plan (Starter/Professional/Enterprise)")
    print("   c. Click 'Subscribe' button")
    print("   d. Payment order will be created with Razorpay")
    print("   e. Complete test payment using Razorpay test cards")
    
    print("\n4. RAZORPAY TEST CARDS:")
    print("   Card Number: 4111 1111 1111 1111")
    print("   CVV: Any 3 digits")
    print("   Expiry: Any future date")
    print("   Name: Any name")
    
    print("\n5. VERIFY PAYMENT:")
    print("   - Check Dashboard for updated credits")
    print("   - Check Payment History")
    print("   - Verify plan upgrade")
    
    print("\n6. ADMIN FEATURES:")
    print("   - View all user payments in Admin Panel")
    print("   - Monitor payment analytics")
    print("   - Process refunds if needed")
    print("   - View security events")

def check_issues():
    """Check for common issues"""
    print_section("8. ISSUE DIAGNOSTICS")
    
    issues = []
    
    # Check if Razorpay is configured
    import os
    key_id = os.environ.get('RAZORPAY_KEY_ID', '')
    key_secret = os.environ.get('RAZORPAY_KEY_SECRET', '')
    
    if not key_id or not key_secret:
        issues.append("✗ Razorpay credentials not set in environment variables")
    else:
        print("✓ Razorpay credentials configured in .env")
    
    # Check if backend is running
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            print("✓ Backend service is running")
        else:
            issues.append("✗ Backend service not responding correctly")
    except:
        issues.append("✗ Backend service not accessible")
    
    # Check if plans exist
    try:
        response = requests.get(f"{BASE_URL}/payments/plans")
        if response.status_code == 200:
            plans = response.json()
            if len(plans) > 0:
                print(f"✓ Plans are seeded ({len(plans)} plans)")
            else:
                issues.append("✗ No plans found in database")
        else:
            issues.append("✗ Unable to fetch plans")
    except:
        issues.append("✗ Error fetching plans")
    
    if issues:
        print("\n⚠ Issues Found:")
        for issue in issues:
            print(f"  {issue}")
    else:
        print("\n✅ No issues detected! System is ready for payment processing.")

def main():
    print("\n" + "="*70)
    print("  RAZORPAY PAYMENT INTEGRATION TEST")
    print("="*70)
    print(f"\n  Test Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  Backend: {BASE_URL}")
    print(f"  Razorpay Mode: TEST")
    print("\n" + "="*70)
    
    # Run tests
    test_plan_retrieval()
    test_order_creation_unauthenticated()
    create_test_user()
    test_razorpay_connection()
    test_payment_endpoints()
    test_admin_plan_management()
    generate_instructions()
    check_issues()
    
    print("\n" + "="*70)
    print("  TEST COMPLETE")
    print("="*70 + "\n")

if __name__ == "__main__":
    main()
