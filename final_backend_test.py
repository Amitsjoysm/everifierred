#!/usr/bin/env python3
"""
Final comprehensive backend test for MailGuard
Tests all critical endpoints and provides detailed results
"""

import requests
import json
import asyncio
import sys
import os
sys.path.append('/app/backend')

BASE_URL = "https://service-restarter.preview.emergentagent.com/api"
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

class ComprehensiveTester:
    def __init__(self):
        self.session = requests.Session()
        self.admin_token = None
        self.results = {}
        
    def log_test(self, category, test_name, success, message, details=None):
        """Log test result"""
        if category not in self.results:
            self.results[category] = {"tests": [], "passed": 0, "total": 0}
        
        self.results[category]["tests"].append({
            "name": test_name,
            "success": success,
            "message": message,
            "details": details
        })
        
        self.results[category]["total"] += 1
        if success:
            self.results[category]["passed"] += 1
            
        status = "✅" if success else "❌"
        print(f"{status} {category} - {test_name}: {message}")
        
    async def authenticate(self):
        """Authenticate as admin"""
        print("\n🔐 Authenticating...")
        
        # Login
        login_data = {"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
        response = self.session.post(f"{BASE_URL}/auth/login", json=login_data)
        
        if response.status_code != 200:
            return False
            
        # Get OTP
        await asyncio.sleep(1)
        otp = await get_latest_otp()
        if not otp:
            return False
            
        # Verify OTP
        verify_data = {"email": ADMIN_EMAIL, "otp": otp}
        response = self.session.post(f"{BASE_URL}/auth/verify-login", json=verify_data)
        
        if response.status_code == 200:
            data = response.json()
            self.admin_token = data.get("access_token")
            self.session.headers.update({"Authorization": f"Bearer {self.admin_token}"})
            print("✅ Authentication successful")
            return True
        return False
        
    def test_blog_faq_apis(self):
        """Test Blog and FAQ APIs"""
        print("\n📝 Testing Blog and FAQ APIs...")
        
        # Test blogs endpoint
        response = self.session.get(f"{BASE_URL}/content/blogs")
        if response.status_code == 200:
            blogs = response.json()
            self.log_test("Blog and FAQ APIs", "GET /content/blogs", True, 
                         f"Retrieved {len(blogs)} blogs", {"count": len(blogs)})
            
            # Test specific blog
            if blogs:
                slug = blogs[0].get("slug")
                response = self.session.get(f"{BASE_URL}/content/blogs/{slug}")
                success = response.status_code == 200
                self.log_test("Blog and FAQ APIs", f"GET /content/blogs/{slug}", success,
                             "Blog detail retrieved" if success else f"Failed: {response.status_code}")
        else:
            self.log_test("Blog and FAQ APIs", "GET /content/blogs", False, 
                         f"Failed: {response.status_code}")
            
        # Test FAQs endpoint
        response = self.session.get(f"{BASE_URL}/content/faqs")
        if response.status_code == 200:
            faqs = response.json()
            self.log_test("Blog and FAQ APIs", "GET /content/faqs", True,
                         f"Retrieved {len(faqs)} FAQs", {"count": len(faqs)})
        else:
            self.log_test("Blog and FAQ APIs", "GET /content/faqs", False,
                         f"Failed: {response.status_code}")
            
    def test_credit_mechanism(self):
        """Test Credit Mechanism"""
        print("\n💳 Testing Credit Mechanism...")
        
        if not self.admin_token:
            self.log_test("Credit Mechanism", "Authentication", False, "No auth token")
            return
            
        # Test stats endpoint
        response = self.session.get(f"{BASE_URL}/verify/stats")
        if response.status_code == 200:
            stats = response.json()
            expected_fields = ["credits_used", "credits_limit", "total_verifications"]
            has_fields = all(field in stats for field in expected_fields)
            self.log_test("Credit Mechanism", "GET /verify/stats", has_fields,
                         f"Stats retrieved with all fields" if has_fields else "Missing fields",
                         stats)
        else:
            self.log_test("Credit Mechanism", "GET /verify/stats", False,
                         f"Failed: {response.status_code}")
            
        # Test single verification
        verify_data = {"email": "test@example.com"}
        response = self.session.post(f"{BASE_URL}/verify/single", json=verify_data)
        success = response.status_code == 200
        self.log_test("Credit Mechanism", "POST /verify/single", success,
                     "Email verification successful" if success else f"Failed: {response.status_code}")
        
        # Test credit history
        response = self.session.get(f"{BASE_URL}/verify/credit-history")
        if response.status_code == 200:
            history = response.json()
            self.log_test("Credit Mechanism", "GET /verify/credit-history", True,
                         f"Retrieved {len(history)} credit transactions")
        else:
            self.log_test("Credit Mechanism", "GET /verify/credit-history", False,
                         f"Failed: {response.status_code}")
            
        # Test verification history
        response = self.session.get(f"{BASE_URL}/verify/history")
        if response.status_code == 200:
            history = response.json()
            self.log_test("Credit Mechanism", "GET /verify/history", True,
                         f"Retrieved {len(history)} verification records")
        else:
            self.log_test("Credit Mechanism", "GET /verify/history", False,
                         f"Failed: {response.status_code}")
            
    def test_payment_edge_cases(self):
        """Test Payment Edge Cases"""
        print("\n💰 Testing Payment Edge Cases...")
        
        # Test plans endpoint (public)
        response = self.session.get(f"{BASE_URL}/plans")
        if response.status_code == 200:
            plans = response.json()
            self.log_test("Payment Edge Cases", "GET /plans", True,
                         f"Retrieved {len(plans)} plans", {"count": len(plans)})
        else:
            self.log_test("Payment Edge Cases", "GET /plans", False,
                         f"Failed: {response.status_code}")
            
        if not self.admin_token:
            self.log_test("Payment Edge Cases", "Authenticated tests", False, "No auth token")
            return
            
        # Test payment order creation (expected to fail with test credentials)
        plan_id = "9ad1886b-29fa-4595-b4eb-ff9803688a0e"  # Starter plan
        response = self.session.post(f"{BASE_URL}/payments/create-order", params={"plan_id": plan_id})
        
        # This should fail with test credentials, which is expected behavior
        if response.status_code == 500 and "Authentication failed" in response.text:
            self.log_test("Payment Edge Cases", "POST /payments/create-order", True,
                         "Properly rejects invalid Razorpay credentials (expected)")
        elif response.status_code == 200:
            self.log_test("Payment Edge Cases", "POST /payments/create-order", True,
                         "Payment order created successfully")
        else:
            self.log_test("Payment Edge Cases", "POST /payments/create-order", False,
                         f"Unexpected error: {response.status_code}")
            
        # Test payment history
        response = self.session.get(f"{BASE_URL}/payments/history")
        if response.status_code == 200:
            history = response.json()
            self.log_test("Payment Edge Cases", "GET /payments/history", True,
                         f"Retrieved {len(history)} payment records")
        else:
            self.log_test("Payment Edge Cases", "GET /payments/history", False,
                         f"Failed: {response.status_code}")
            
    def test_bulk_verification(self):
        """Test Bulk Verification"""
        print("\n📁 Testing Bulk Verification...")
        
        if not self.admin_token:
            self.log_test("Bulk Verification", "Authentication", False, "No auth token")
            return
            
        # Test jobs endpoint
        response = self.session.get(f"{BASE_URL}/verify/jobs")
        if response.status_code == 200:
            jobs = response.json()
            self.log_test("Bulk Verification", "GET /verify/jobs", True,
                         f"Retrieved {len(jobs)} bulk jobs")
        else:
            self.log_test("Bulk Verification", "GET /verify/jobs", False,
                         f"Failed: {response.status_code}")
            
    def test_authentication_flow(self):
        """Test Authentication Flow"""
        print("\n🔐 Testing Authentication Flow...")
        
        # Test registration
        test_email = f"test_{int(__import__('time').time())}@example.com"
        register_data = {
            "email": test_email,
            "password": "TestPassword123!",
            "full_name": "Test User"
        }
        
        response = self.session.post(f"{BASE_URL}/auth/register", json=register_data)
        success = response.status_code == 200
        self.log_test("Authentication Flow", "POST /auth/register", success,
                     "Registration OTP sent" if success else f"Failed: {response.status_code}")
        
        # Test login
        login_data = {"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
        response = self.session.post(f"{BASE_URL}/auth/login", json=login_data)
        success = response.status_code == 200
        self.log_test("Authentication Flow", "POST /auth/login", success,
                     "Login OTP sent" if success else f"Failed: {response.status_code}")
        
    async def run_all_tests(self):
        """Run all tests"""
        print("🚀 Starting Comprehensive MailGuard Backend Tests")
        print(f"📍 Base URL: {BASE_URL}")
        
        # Authenticate
        await self.authenticate()
        
        # Run all tests
        self.test_blog_faq_apis()
        self.test_authentication_flow()
        self.test_credit_mechanism()
        self.test_payment_edge_cases()
        self.test_bulk_verification()
        
        # Print summary
        self.print_summary()
        
    def print_summary(self):
        """Print comprehensive summary"""
        print("\n" + "="*80)
        print("📋 COMPREHENSIVE TEST SUMMARY")
        print("="*80)
        
        total_tests = 0
        total_passed = 0
        
        for category, data in self.results.items():
            passed = data["passed"]
            total = data["total"]
            total_tests += total
            total_passed += passed
            
            status = "✅" if passed == total else "❌" if passed == 0 else "⚠️"
            print(f"{status} {category}: {passed}/{total} tests passed")
            
            # Show failed tests
            failed_tests = [t for t in data["tests"] if not t["success"]]
            if failed_tests:
                for test in failed_tests:
                    print(f"   ❌ {test['name']}: {test['message']}")
                    
        print(f"\n📊 Overall: {total_passed}/{total_tests} tests passed")
        
        if total_passed == total_tests:
            print("\n🎉 All tests passed!")
        else:
            print(f"\n⚠️ {total_tests - total_passed} tests failed")
            
        return self.results

async def main():
    tester = ComprehensiveTester()
    results = await tester.run_all_tests()
    return results

if __name__ == "__main__":
    results = asyncio.run(main())