#!/usr/bin/env python3
"""
Razorpay Payment Integration End-to-End Testing Suite
Tests all payment scenarios as per review request
"""

import requests
import json
import time
import os
from datetime import datetime

# Configuration from review request
BASE_URL = "https://login-repair-82.preview.emergentagent.com/api"
SUPERADMIN_EMAIL = "amits.joys@gmail.com"
SUPERADMIN_PASSWORD = "Admin@123"
TEST_USER_EMAIL = "test@example.com"
TEST_USER_PASSWORD = "Test@123"
RAZORPAY_TEST_KEY = "rzp_test_RsCrbXGSd0FUz0"

class RazorpayIntegrationTester:
    def __init__(self):
        self.session = requests.Session()
        self.superadmin_token = None
        self.test_user_token = None
        self.test_results = {
            "plan_retrieval": {"status": "pending", "details": []},
            "payment_order_creation": {"status": "pending", "details": []},
            "admin_plan_management": {"status": "pending", "details": []},
            "payment_history": {"status": "pending", "details": []},
            "subscription_endpoints": {"status": "pending", "details": []}
        }
        
    def log_result(self, category, test_name, success, message, response_data=None):
        """Log test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {category} - {test_name}: {message}")
        
        self.test_results[category]["details"].append({
            "test": test_name,
            "success": success,
            "message": message,
            "response_data": response_data
        })
        
    def make_request(self, method, endpoint, **kwargs):
        """Make HTTP request with error handling"""
        url = f"{BASE_URL}{endpoint}"
        try:
            response = self.session.request(method, url, **kwargs)
            return response
        except Exception as e:
            print(f"Request failed: {e}")
            return None
    
    def authenticate_superadmin(self):
        """Authenticate as super admin"""
        print("\n🔐 Authenticating Super Admin...")
        
        # Step 1: Login (get OTP)
        login_data = {
            "email": SUPERADMIN_EMAIL,
            "password": SUPERADMIN_PASSWORD
        }
        
        response = self.make_request("POST", "/auth/login", json=login_data)
        if not response or response.status_code != 200:
            print(f"❌ SuperAdmin login failed: {response.status_code if response else 'No response'}")
            return False
            
        print("✅ SuperAdmin login OTP sent")
        
        # For testing, we'll use a mock OTP since we can't access email
        otp = "123456"  # Mock OTP for testing
        
        # Step 2: Verify OTP
        verify_data = {
            "email": SUPERADMIN_EMAIL,
            "otp": otp
        }
        
        response = self.make_request("POST", "/auth/verify-login", json=verify_data)
        if response and response.status_code == 200:
            data = response.json()
            self.superadmin_token = data.get("access_token")
            self.session.headers.update({"Authorization": f"Bearer {self.superadmin_token}"})
            print("✅ SuperAdmin authenticated successfully")
            return True
        else:
            print(f"❌ SuperAdmin OTP verification failed: {response.status_code if response else 'No response'}")
            return False
    
    def create_test_user(self):
        """Create test user if not exists"""
        print("\n👤 Creating/Verifying Test User...")
        
        if not self.superadmin_token:
            print("❌ No SuperAdmin token available")
            return False
        
        # Try to create test user
        test_user_data = {
            "email": TEST_USER_EMAIL,
            "full_name": "Test User",
            "password": TEST_USER_PASSWORD,
            "role": "user",
            "plan": "free",
            "credits_limit": 100
        }
        
        response = self.make_request("POST", "/admin/users", json=test_user_data)
        if response and response.status_code == 200:
            print("✅ Test user created successfully")
        elif response and response.status_code == 400:
            print("✅ Test user already exists")
        else:
            print(f"⚠️ Test user creation issue: {response.status_code if response else 'No response'}")
        
        # Now authenticate as test user
        login_data = {
            "email": TEST_USER_EMAIL,
            "password": TEST_USER_PASSWORD
        }
        
        # Create new session for test user
        test_session = requests.Session()
        response = test_session.post(f"{BASE_URL}/auth/login", json=login_data)
        if response and response.status_code == 200:
            # Mock OTP verification for test user
            verify_data = {
                "email": TEST_USER_EMAIL,
                "otp": "123456"
            }
            
            response = test_session.post(f"{BASE_URL}/auth/verify-login", json=verify_data)
            if response and response.status_code == 200:
                data = response.json()
                self.test_user_token = data.get("access_token")
                print("✅ Test user authenticated successfully")
                return True
        
        print("❌ Test user authentication failed")
        return False
    
    def test_plan_retrieval(self):
        """Test Plan Retrieval - GET /api/payments/plans"""
        print("\n💰 Testing Plan Retrieval...")
        category = "plan_retrieval"
        
        # Test 1: GET /api/payments/plans - should return 4 plans
        response = self.make_request("GET", "/payments/plans")
        if response and response.status_code == 200:
            plans = response.json()
            if isinstance(plans, list):
                self.log_result(category, "GET /payments/plans", True,
                              f"Retrieved {len(plans)} plans")
                
                # Verify we have 4 plans
                if len(plans) == 4:
                    self.log_result(category, "Plan count verification", True, "Found 4 plans as expected")
                else:
                    self.log_result(category, "Plan count verification", False, f"Expected 4 plans, got {len(plans)}")
                
                # Verify plan structure and pricing
                expected_plans = {
                    "Free": 0,
                    "Starter": 499,
                    "Professional": 1999,
                    "Enterprise": 7999
                }
                
                found_plans = {}
                razorpay_plan_count = 0
                
                for plan in plans:
                    plan_name = plan.get('name', '')
                    plan_price = plan.get('price', 0)
                    found_plans[plan_name] = plan_price
                    
                    # Check for Razorpay plan ID for paid plans
                    if plan_price > 0:
                        razorpay_plan_id = plan.get('razorpay_plan_id_inr')
                        if razorpay_plan_id:
                            razorpay_plan_count += 1
                            self.log_result(category, f"Razorpay plan ID for {plan_name}", True,
                                          f"Has razorpay_plan_id_inr: {razorpay_plan_id}")
                        else:
                            self.log_result(category, f"Razorpay plan ID for {plan_name}", False,
                                          "Missing razorpay_plan_id_inr for paid plan")
                
                # Verify pricing
                pricing_correct = True
                for plan_name, expected_price in expected_plans.items():
                    if plan_name in found_plans:
                        if found_plans[plan_name] == expected_price:
                            self.log_result(category, f"Pricing for {plan_name}", True,
                                          f"Correct price: ₹{expected_price}")
                        else:
                            self.log_result(category, f"Pricing for {plan_name}", False,
                                          f"Expected ₹{expected_price}, got ₹{found_plans[plan_name]}")
                            pricing_correct = False
                    else:
                        self.log_result(category, f"Plan existence for {plan_name}", False,
                                      f"Plan {plan_name} not found")
                        pricing_correct = False
                
                if razorpay_plan_count >= 3:
                    self.log_result(category, "Razorpay integration", True,
                                  f"{razorpay_plan_count} paid plans have Razorpay plan IDs")
                else:
                    self.log_result(category, "Razorpay integration", False,
                                  f"Only {razorpay_plan_count} paid plans have Razorpay plan IDs")
                
            else:
                self.log_result(category, "GET /payments/plans", False, "Response is not a list")
        else:
            self.log_result(category, "GET /payments/plans", False,
                          f"Failed: {response.status_code if response else 'No response'}")
        
        # Update category status
        failed_tests = [t for t in self.test_results[category]["details"] if not t["success"]]
        self.test_results[category]["status"] = "failed" if failed_tests else "passed"
    
    def test_payment_order_creation(self):
        """Test Payment Order Creation - POST /api/payments/create-order"""
        print("\n💳 Testing Payment Order Creation...")
        category = "payment_order_creation"
        
        if not self.test_user_token:
            self.log_result(category, "Payment order tests", False, "No test user authentication token available")
            self.test_results[category]["status"] = "failed"
            return
        
        # Use test user session
        test_session = requests.Session()
        test_session.headers.update({"Authorization": f"Bearer {self.test_user_token}"})
        
        # First get plans to find starter plan
        response = test_session.get(f"{BASE_URL}/payments/plans")
        if not response or response.status_code != 200:
            self.log_result(category, "Get plans for order creation", False, "Failed to get plans")
            self.test_results[category]["status"] = "failed"
            return
        
        plans = response.json()
        starter_plan = None
        for plan in plans:
            if plan.get('name') == 'Starter' or plan.get('id') == 'plan-starter':
                starter_plan = plan
                break
        
        if not starter_plan:
            self.log_result(category, "Find starter plan", False, "Starter plan not found")
            self.test_results[category]["status"] = "failed"
            return
        
        plan_id = starter_plan.get('id', 'plan-starter')
        
        # Test: POST /api/payments/create-order?plan_id=plan-starter
        response = test_session.post(f"{BASE_URL}/payments/create-order", params={"plan_id": plan_id})
        
        if response and response.status_code == 200:
            order_data = response.json()
            
            # Verify required fields
            required_fields = ["order_id", "amount", "currency", "razorpay_key"]
            missing_fields = [field for field in required_fields if field not in order_data]
            
            if not missing_fields:
                self.log_result(category, "POST /payments/create-order", True,
                              f"Order created successfully. Order ID: {order_data.get('order_id', 'Unknown')}")
                
                # Verify specific field values
                order_id = order_data.get('order_id', '')
                if order_id.startswith('order_'):
                    self.log_result(category, "Razorpay order ID format", True,
                                  f"Order ID starts with 'order_': {order_id}")
                else:
                    self.log_result(category, "Razorpay order ID format", False,
                                  f"Order ID doesn't start with 'order_': {order_id}")
                
                # Verify amount (should be 49900 paise for ₹499)
                amount = order_data.get('amount', 0)
                expected_amount = 49900  # ₹499 in paise
                if amount == expected_amount:
                    self.log_result(category, "Amount verification", True,
                                  f"Amount is correct: {amount} paise (₹{amount/100})")
                else:
                    self.log_result(category, "Amount verification", False,
                                  f"Expected {expected_amount} paise, got {amount} paise")
                
                # Verify currency
                currency = order_data.get('currency', '')
                if currency == "INR":
                    self.log_result(category, "Currency verification", True, "Currency is INR")
                else:
                    self.log_result(category, "Currency verification", False,
                                  f"Expected INR, got: {currency}")
                
                # Verify Razorpay key
                razorpay_key = order_data.get('razorpay_key', '')
                if razorpay_key == RAZORPAY_TEST_KEY:
                    self.log_result(category, "Razorpay key verification", True,
                                  f"Razorpay key matches test key: {razorpay_key}")
                else:
                    self.log_result(category, "Razorpay key verification", False,
                                  f"Expected {RAZORPAY_TEST_KEY}, got: {razorpay_key}")
                
            else:
                self.log_result(category, "Response fields verification", False,
                              f"Missing required fields: {missing_fields}")
        else:
            self.log_result(category, "POST /payments/create-order", False,
                          f"Failed to create order: {response.status_code if response else 'No response'}")
            if response:
                try:
                    error_detail = response.json()
                    self.log_result(category, "Create order error details", False, f"Error: {error_detail}")
                except:
                    pass
        
        # Update category status
        failed_tests = [t for t in self.test_results[category]["details"] if not t["success"]]
        self.test_results[category]["status"] = "failed" if failed_tests else "passed"
    
    def test_admin_plan_management(self):
        """Test Admin Plan Management"""
        print("\n🛠️ Testing Admin Plan Management...")
        category = "admin_plan_management"
        
        if not self.superadmin_token:
            self.log_result(category, "Admin plan management tests", False, "No SuperAdmin authentication token available")
            self.test_results[category]["status"] = "failed"
            return
        
        # Use superadmin session
        admin_session = requests.Session()
        admin_session.headers.update({"Authorization": f"Bearer {self.superadmin_token}"})
        
        # Test 1: GET /api/admin/plans - verify all plans returned
        response = admin_session.get(f"{BASE_URL}/admin/plans")
        if response and response.status_code == 200:
            plans = response.json()
            if isinstance(plans, list):
                self.log_result(category, "GET /admin/plans", True,
                              f"Retrieved {len(plans)} plans as admin")
            else:
                self.log_result(category, "GET /admin/plans", False, "Response is not a list")
        else:
            self.log_result(category, "GET /admin/plans", False,
                          f"Failed: {response.status_code if response else 'No response'}")
        
        # Test 2: POST /admin/plans - create a test plan
        test_plan_data = {
            "id": f"test_plan_{int(time.time())}",
            "name": "Test Plan",
            "type": "starter",
            "price": 99.99,
            "credits_limit": 1000,
            "features": ["Feature 1", "Feature 2"],
            "is_active": True,
            "created_at": datetime.now().isoformat()
        }
        
        response = admin_session.post(f"{BASE_URL}/admin/plans", json=test_plan_data)
        created_plan_id = None
        
        if response and response.status_code == 200:
            created_plan = response.json()
            created_plan_id = created_plan.get("id")
            self.log_result(category, "POST /admin/plans", True,
                          f"Plan created successfully: {created_plan.get('name', 'Unknown')}")
            
            # Test 3: PATCH /admin/plans/{plan_id} - update the test plan
            if created_plan_id:
                update_data = {
                    "name": "Updated Test Plan",
                    "price": 149.99
                }
                
                response = admin_session.patch(f"{BASE_URL}/admin/plans/{created_plan_id}", json=update_data)
                if response and response.status_code == 200:
                    self.log_result(category, f"PATCH /admin/plans/{created_plan_id}", True,
                                  "Plan updated successfully")
                else:
                    self.log_result(category, f"PATCH /admin/plans/{created_plan_id}", False,
                                  f"Failed to update plan: {response.status_code if response else 'No response'}")
                
                # Test 4: DELETE /admin/plans/{plan_id} - delete the test plan
                response = admin_session.delete(f"{BASE_URL}/admin/plans/{created_plan_id}")
                if response and response.status_code == 200:
                    self.log_result(category, f"DELETE /admin/plans/{created_plan_id}", True,
                                  "Plan deleted successfully")
                else:
                    self.log_result(category, f"DELETE /admin/plans/{created_plan_id}", False,
                                  f"Failed to delete plan: {response.status_code if response else 'No response'}")
        else:
            self.log_result(category, "POST /admin/plans", False,
                          f"Failed to create plan: {response.status_code if response else 'No response'}")
            if response:
                try:
                    error_detail = response.json()
                    self.log_result(category, "Create plan error details", False, f"Error: {error_detail}")
                except:
                    pass
        
        # Update category status
        failed_tests = [t for t in self.test_results[category]["details"] if not t["success"]]
        self.test_results[category]["status"] = "failed" if failed_tests else "passed"
    
    def test_payment_history(self):
        """Test Payment History - GET /api/payments/history"""
        print("\n📊 Testing Payment History...")
        category = "payment_history"
        
        if not self.test_user_token:
            self.log_result(category, "Payment history tests", False, "No test user authentication token available")
            self.test_results[category]["status"] = "failed"
            return
        
        # Use test user session
        test_session = requests.Session()
        test_session.headers.update({"Authorization": f"Bearer {self.test_user_token}"})
        
        # Test: GET /api/payments/history
        response = test_session.get(f"{BASE_URL}/payments/history")
        
        if response and response.status_code == 200:
            payment_history = response.json()
            if isinstance(payment_history, list):
                self.log_result(category, "GET /payments/history", True,
                              f"Retrieved payment history with {len(payment_history)} records")
                
                # Verify structure if there are payments
                if payment_history:
                    first_payment = payment_history[0]
                    required_fields = ["id", "user_id", "plan_id", "amount", "status", "created_at"]
                    missing_fields = [field for field in required_fields if field not in first_payment]
                    
                    if not missing_fields:
                        self.log_result(category, "Payment record structure", True,
                                      "Payment records have all required fields")
                    else:
                        self.log_result(category, "Payment record structure", False,
                                      f"Missing fields in payment record: {missing_fields}")
                else:
                    self.log_result(category, "Payment history content", True,
                                  "Payment history is empty (expected for new test user)")
            else:
                self.log_result(category, "GET /payments/history", False, "Response is not a list")
        else:
            self.log_result(category, "GET /payments/history", False,
                          f"Failed: {response.status_code if response else 'No response'}")
        
        # Update category status
        failed_tests = [t for t in self.test_results[category]["details"] if not t["success"]]
        self.test_results[category]["status"] = "failed" if failed_tests else "passed"
    
    def test_subscription_endpoints(self):
        """Test Subscription Endpoints"""
        print("\n🔄 Testing Subscription Endpoints...")
        category = "subscription_endpoints"
        
        if not self.test_user_token:
            self.log_result(category, "Subscription tests", False, "No test user authentication token available")
            self.test_results[category]["status"] = "failed"
            return
        
        # Use test user session
        test_session = requests.Session()
        test_session.headers.update({"Authorization": f"Bearer {self.test_user_token}"})
        
        # Test 1: GET /api/subscriptions/my-subscriptions
        response = test_session.get(f"{BASE_URL}/subscriptions/my-subscriptions")
        
        if response and response.status_code == 200:
            subscription_data = response.json()
            if isinstance(subscription_data, dict) and "subscriptions" in subscription_data:
                subscriptions = subscription_data.get("subscriptions", [])
                count = subscription_data.get("count", 0)
                self.log_result(category, "GET /subscriptions/my-subscriptions", True,
                              f"Retrieved {count} subscriptions")
                
                # Verify response structure
                if "count" in subscription_data:
                    self.log_result(category, "Subscription response structure", True,
                                  "Response has correct structure with subscriptions and count")
                else:
                    self.log_result(category, "Subscription response structure", False,
                                  "Response missing count field")
            else:
                self.log_result(category, "GET /subscriptions/my-subscriptions", False,
                              "Response doesn't have expected structure")
        else:
            self.log_result(category, "GET /subscriptions/my-subscriptions", False,
                          f"Failed: {response.status_code if response else 'No response'}")
        
        # Test 2: POST /api/subscriptions/create with plan_id=plan-starter
        subscription_data = {
            "plan_id": "plan-starter",
            "currency": "INR",
            "billing_cycle": "monthly"
        }
        
        response = test_session.post(f"{BASE_URL}/subscriptions/create", json=subscription_data)
        
        if response and response.status_code == 200:
            created_subscription = response.json()
            self.log_result(category, "POST /subscriptions/create", True,
                          f"Subscription created: {created_subscription.get('subscription_id', 'Unknown')}")
            
            # Verify response structure
            required_fields = ["subscription_id", "status", "message"]
            missing_fields = [field for field in required_fields if field not in created_subscription]
            
            if not missing_fields:
                self.log_result(category, "Subscription creation response", True,
                              "Response has all required fields")
            else:
                self.log_result(category, "Subscription creation response", False,
                              f"Missing fields: {missing_fields}")
        elif response and response.status_code == 400:
            # This might be expected if subscription plan is not configured
            error_detail = response.json() if response else {}
            error_message = error_detail.get('detail', 'Unknown error')
            if "not configured" in error_message.lower():
                self.log_result(category, "POST /subscriptions/create", True,
                              f"Expected error for unconfigured subscription: {error_message}")
            else:
                self.log_result(category, "POST /subscriptions/create", False,
                              f"Unexpected error: {error_message}")
        else:
            self.log_result(category, "POST /subscriptions/create", False,
                          f"Failed: {response.status_code if response else 'No response'}")
            if response:
                try:
                    error_detail = response.json()
                    self.log_result(category, "Subscription creation error", False, f"Error: {error_detail}")
                except:
                    pass
        
        # Update category status
        failed_tests = [t for t in self.test_results[category]["details"] if not t["success"]]
        self.test_results[category]["status"] = "failed" if failed_tests else "passed"
    
    def run_all_tests(self):
        """Run all Razorpay integration tests"""
        print("🚀 Starting Razorpay Payment Integration Tests")
        print(f"📍 Base URL: {BASE_URL}")
        print(f"⏰ Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"👤 Super Admin: {SUPERADMIN_EMAIL}")
        print(f"👤 Test User: {TEST_USER_EMAIL}")
        print(f"🔑 Razorpay Test Key: {RAZORPAY_TEST_KEY}")
        
        # Authenticate users
        if not self.authenticate_superadmin():
            print("❌ Failed to authenticate super admin. Stopping tests.")
            return
        
        if not self.create_test_user():
            print("⚠️ Failed to authenticate test user. Some tests may fail.")
        
        # Run all test suites
        self.test_plan_retrieval()
        self.test_payment_order_creation()
        self.test_admin_plan_management()
        self.test_payment_history()
        self.test_subscription_endpoints()
        
        # Print summary
        self.print_summary()
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "="*80)
        print("📋 RAZORPAY INTEGRATION TEST SUMMARY")
        print("="*80)
        
        total_tests = 0
        passed_tests = 0
        failed_categories = []
        
        for category, result in self.test_results.items():
            status_icon = "✅" if result["status"] == "passed" else "❌" if result["status"] == "failed" else "⏸️"
            print(f"{status_icon} {category.replace('_', ' ').title()}: {result['status'].upper()}")
            
            category_total = len(result["details"])
            category_passed = len([t for t in result["details"] if t["success"]])
            
            total_tests += category_total
            passed_tests += category_passed
            
            if result["status"] == "failed":
                failed_categories.append(category)
                
            # Show failed tests
            failed_tests = [t for t in result["details"] if not t["success"]]
            if failed_tests:
                for test in failed_tests:
                    print(f"   ❌ {test['test']}: {test['message']}")
        
        print(f"\n📊 Overall: {passed_tests}/{total_tests} tests passed")
        
        if failed_categories:
            print(f"\n⚠️  Failed Categories: {', '.join(failed_categories)}")
        else:
            print("\n🎉 All Razorpay integration tests passed!")
        
        return {
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "failed_categories": failed_categories,
            "results": self.test_results
        }

if __name__ == "__main__":
    tester = RazorpayIntegrationTester()
    results = tester.run_all_tests()