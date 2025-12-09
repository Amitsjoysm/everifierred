#!/usr/bin/env python3
"""
MailGuard Backend API Testing Suite - Production Readiness Testing
Tests critical fixes and features as per review request
"""

import requests
import json
import time
import os
import subprocess
from datetime import datetime

# Configuration - Updated for review request
BASE_URL = "https://razorpay-integration.preview.emergentagent.com/api"
SUPERADMIN_EMAIL = "amits.joys@gmail.com"
SUPERADMIN_PASSWORD = "Admin@123"

class ProductionReadinessTester:
    def __init__(self):
        self.session = requests.Session()
        self.superadmin_token = None
        self.test_results = {
            "superadmin_login": {"status": "pending", "details": []},
            "create_user_functionality": {"status": "pending", "details": []},
            "plans_crud_operations": {"status": "pending", "details": []},
            "payment_subscription_fix": {"status": "pending", "details": []},
            "system_health": {"status": "pending", "details": []}
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
            
    def test_superadmin_login(self):
        """Test SuperAdmin Login with specific credentials"""
        print("\n🔐 Testing SuperAdmin Login...")
        category = "superadmin_login"
        
        # Step 1: Login (get OTP)
        login_data = {
            "email": SUPERADMIN_EMAIL,
            "password": SUPERADMIN_PASSWORD
        }
        
        response = self.make_request("POST", "/auth/login", json=login_data)
        if not response or response.status_code != 200:
            self.log_result(category, "POST /auth/login", False, 
                          f"SuperAdmin login failed: {response.status_code if response else 'No response'}")
            self.test_results[category]["status"] = "failed"
            return False
            
        self.log_result(category, "POST /auth/login", True, "SuperAdmin login OTP sent")
        
        # For testing, we'll use a mock OTP since we can't access email
        # In production, this would require actual OTP from email
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
            
            # Verify user details
            user_data = data.get("user", {})
            role = user_data.get("role")
            plan = user_data.get("plan")
            credits_limit = user_data.get("credits_limit")
            
            # Check expected values
            if role == "super_admin":
                self.log_result(category, "Role verification", True, f"Role is super_admin: {role}")
            else:
                self.log_result(category, "Role verification", False, f"Expected super_admin, got: {role}")
                
            if plan == "enterprise":
                self.log_result(category, "Plan verification", True, f"Plan is enterprise: {plan}")
            else:
                self.log_result(category, "Plan verification", False, f"Expected enterprise, got: {plan}")
                
            if credits_limit == 25000:
                self.log_result(category, "Credits verification", True, f"Credits limit is 25000: {credits_limit}")
            else:
                self.log_result(category, "Credits verification", False, f"Expected 25000, got: {credits_limit}")
                
            self.log_result(category, "SuperAdmin authentication", True, "SuperAdmin authentication successful")
            
            # Update category status
            failed_tests = [t for t in self.test_results[category]["details"] if not t["success"]]
            self.test_results[category]["status"] = "failed" if failed_tests else "passed"
            return True
        else:
            self.log_result(category, "POST /auth/verify-login", False,
                          f"OTP verification failed: {response.status_code if response else 'No response'}")
            self.test_results[category]["status"] = "failed"
            return False
        
    def test_create_user_functionality(self):
        """Test Create User Functionality (NEW FEATURE)"""
        print("\n👤 Testing Create User Functionality...")
        category = "create_user_functionality"
        
        if not self.superadmin_token:
            self.log_result(category, "Create user tests", False, "No SuperAdmin authentication token available")
            self.test_results[category]["status"] = "failed"
            return
            
        # Test 1: POST /api/admin/users - Create new user
        test_user_data = {
            "email": "testuser@example.com",
            "full_name": "Test User",
            "password": "Test@123",
            "role": "user",
            "plan": "free",
            "credits_limit": 100
        }
        
        response = self.make_request("POST", "/admin/users", json=test_user_data)
        if response and response.status_code == 200:
            user_data = response.json()
            self.log_result(category, "POST /admin/users", True,
                          f"User created successfully: {user_data.get('email', 'Unknown')}")
            
            # Test 2: GET /api/admin/users - Verify new user appears in list
            response = self.make_request("GET", "/admin/users")
            if response and response.status_code == 200:
                users = response.json()
                if isinstance(users, list):
                    # Check if our test user is in the list
                    test_user_found = any(user.get('email') == test_user_data['email'] for user in users)
                    if test_user_found:
                        self.log_result(category, "GET /admin/users verification", True,
                                      f"New user found in users list. Total users: {len(users)}")
                    else:
                        self.log_result(category, "GET /admin/users verification", False,
                                      "New user not found in users list")
                else:
                    self.log_result(category, "GET /admin/users verification", False, "Response is not a list")
            else:
                self.log_result(category, "GET /admin/users verification", False,
                              f"Failed to get users list: {response.status_code if response else 'No response'}")
        else:
            self.log_result(category, "POST /admin/users", False,
                          f"Failed to create user: {response.status_code if response else 'No response'}")
            if response:
                try:
                    error_detail = response.json()
                    self.log_result(category, "Create user error details", False, f"Error: {error_detail}")
                except:
                    pass
            
        # Update category status
        failed_tests = [t for t in self.test_results[category]["details"] if not t["success"]]
        self.test_results[category]["status"] = "failed" if failed_tests else "passed"
        
    def test_plans_crud_operations(self):
        """Test Plans CRUD Operations"""
        print("\n📋 Testing Plans CRUD Operations...")
        category = "plans_crud_operations"
        
        if not self.superadmin_token:
            self.log_result(category, "Plans CRUD tests", False, "No SuperAdmin authentication token available")
            self.test_results[category]["status"] = "failed"
            return
            
        # Test 1: GET /api/admin/plans - Get all plans
        response = self.make_request("GET", "/admin/plans")
        if response and response.status_code == 200:
            plans = response.json()
            if isinstance(plans, list):
                self.log_result(category, "GET /admin/plans", True,
                              f"Retrieved {len(plans)} plans")
                
                # Store plan for later tests
                test_plan_id = None
                if plans:
                    test_plan_id = plans[0].get("id")
                    
                # Test 2: POST /api/admin/plans - Create new plan (if endpoint works)
                new_plan_data = {
                    "id": f"test_plan_{int(time.time())}",
                    "name": "Test Plan",
                    "type": "starter",
                    "price": 99.99,
                    "credits_limit": 1000,
                    "features": ["Feature 1", "Feature 2"],
                    "is_active": True,
                    "created_at": datetime.now().isoformat()
                }
                
                response = self.make_request("POST", "/admin/plans", json=new_plan_data)
                if response and response.status_code == 200:
                    created_plan = response.json()
                    created_plan_id = created_plan.get("id")
                    self.log_result(category, "POST /admin/plans", True,
                                  f"Plan created successfully: {created_plan.get('name', 'Unknown')}")
                    
                    # Test 3: PATCH /api/admin/plans/{plan_id} - Update plan
                    if created_plan_id:
                        update_data = {
                            "name": "Updated Test Plan",
                            "price": 149.99
                        }
                        
                        response = self.make_request("PATCH", f"/admin/plans/{created_plan_id}", json=update_data)
                        if response and response.status_code == 200:
                            self.log_result(category, f"PATCH /admin/plans/{created_plan_id}", True,
                                          "Plan updated successfully")
                        else:
                            self.log_result(category, f"PATCH /admin/plans/{created_plan_id}", False,
                                          f"Failed to update plan: {response.status_code if response else 'No response'}")
                        
                        # Test 4: DELETE /api/admin/plans/{plan_id} - Delete plan
                        response = self.make_request("DELETE", f"/admin/plans/{created_plan_id}")
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
            else:
                self.log_result(category, "GET /admin/plans", False, "Response is not a list")
        else:
            self.log_result(category, "GET /admin/plans", False,
                          f"Failed: {response.status_code if response else 'No response'}")
            
        # Update category status
        failed_tests = [t for t in self.test_results[category]["details"] if not t["success"]]
        self.test_results[category]["status"] = "failed" if failed_tests else "passed"
        
    def test_payment_subscription_fix(self):
        """Test Payment Subscription Fix"""
        print("\n💰 Testing Payment Subscription Fix...")
        category = "payment_subscription_fix"
        
        if not self.superadmin_token:
            self.log_result(category, "Payment subscription tests", False, "No SuperAdmin authentication token available")
            self.test_results[category]["status"] = "failed"
            return
            
        # Test 1: GET /api/plans - Get available plans
        response = self.make_request("GET", "/plans")
        if response and response.status_code == 200:
            plans = response.json()
            if isinstance(plans, list) and plans:
                self.log_result(category, "GET /plans", True, f"Retrieved {len(plans)} plans")
                
                # Find a paid plan for testing
                paid_plan = None
                for plan in plans:
                    if plan.get("price", 0) > 0:
                        paid_plan = plan
                        break
                
                if paid_plan:
                    plan_id = paid_plan.get("id")
                    
                    # Test 2: POST /api/payments/create-order?plan_id={plan_id}
                    response = self.make_request("POST", "/payments/create-order", params={"plan_id": plan_id})
                    if response and response.status_code == 200:
                        order_data = response.json()
                        
                        # Verify response contains required fields
                        required_fields = ["order_id", "amount", "currency", "razorpay_key"]
                        missing_fields = [field for field in required_fields if field not in order_data]
                        
                        if not missing_fields:
                            self.log_result(category, "POST /payments/create-order", True,
                                          f"Order created successfully. Order ID: {order_data.get('order_id', 'Unknown')}")
                            self.log_result(category, "Response fields verification", True,
                                          f"All required fields present: {required_fields}")
                            
                            # Verify specific field values
                            if order_data.get("currency") == "INR":
                                self.log_result(category, "Currency verification", True, "Currency is INR")
                            else:
                                self.log_result(category, "Currency verification", False, 
                                              f"Expected INR, got: {order_data.get('currency')}")
                                
                            if order_data.get("razorpay_key"):
                                self.log_result(category, "Razorpay key verification", True, "Razorpay key present")
                            else:
                                self.log_result(category, "Razorpay key verification", False, "Razorpay key missing")
                                
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
                else:
                    self.log_result(category, "Paid plan availability", False, "No paid plans available for testing")
            else:
                self.log_result(category, "GET /plans", False, "No plans available or response is not a list")
        else:
            self.log_result(category, "GET /plans", False,
                          f"Failed to get plans: {response.status_code if response else 'No response'}")
            
        # Update category status
        failed_tests = [t for t in self.test_results[category]["details"] if not t["success"]]
        self.test_results[category]["status"] = "failed" if failed_tests else "passed"
        
    def test_system_health(self):
        """Test System Health"""
        print("\n🏥 Testing System Health...")
        category = "system_health"
        
        # Test 1: Redis ping
        try:
            result = subprocess.run(['redis-cli', 'ping'], capture_output=True, text=True, timeout=5)
            if result.returncode == 0 and 'PONG' in result.stdout:
                self.log_result(category, "Redis ping", True, "Redis is running (PONG response)")
            else:
                self.log_result(category, "Redis ping", False, f"Redis ping failed: {result.stdout}")
        except Exception as e:
            self.log_result(category, "Redis ping", False, f"Redis ping error: {str(e)}")
            
        # Test 2: Celery workers check
        try:
            result = subprocess.run(['pgrep', '-f', 'celery.*worker'], capture_output=True, text=True, timeout=5)
            if result.returncode == 0 and result.stdout.strip():
                worker_pids = result.stdout.strip().split('\n')
                self.log_result(category, "Celery workers", True, f"Celery workers active: {len(worker_pids)} processes")
            else:
                self.log_result(category, "Celery workers", False, "No Celery worker processes found")
        except Exception as e:
            self.log_result(category, "Celery workers", False, f"Celery check error: {str(e)}")
            
        # Test 3: Backend health endpoint
        response = self.make_request("GET", "/health")
        if response and response.status_code == 200:
            health_data = response.json()
            if health_data.get("status") == "healthy":
                self.log_result(category, "GET /health", True, "Backend health endpoint returns healthy")
            else:
                self.log_result(category, "GET /health", False, f"Backend health status: {health_data.get('status', 'Unknown')}")
        else:
            self.log_result(category, "GET /health", False,
                          f"Health endpoint failed: {response.status_code if response else 'No response'}")
            
        # Test 4: Critical endpoints accessibility
        critical_endpoints = [
            ("/", "Root endpoint"),
            ("/plans", "Plans endpoint"),
            ("/content/blogs", "Blogs endpoint"),
            ("/content/faqs", "FAQs endpoint")
        ]
        
        accessible_count = 0
        for endpoint, description in critical_endpoints:
            response = self.make_request("GET", endpoint)
            if response and response.status_code == 200:
                accessible_count += 1
                self.log_result(category, f"Accessibility: {description}", True, f"GET {endpoint} accessible")
            else:
                self.log_result(category, f"Accessibility: {description}", False,
                              f"GET {endpoint} failed: {response.status_code if response else 'No response'}")
                
        self.log_result(category, "Critical endpoints summary", True,
                      f"{accessible_count}/{len(critical_endpoints)} critical endpoints accessible")
            
        # Update category status
        failed_tests = [t for t in self.test_results[category]["details"] if not t["success"]]
        self.test_results[category]["status"] = "failed" if failed_tests else "passed"
        
    # Removed old test methods - replaced with production readiness tests
        
    def run_all_tests(self):
        """Run all production readiness test suites"""
        print("🚀 Starting MailGuard Production Readiness Tests")
        print(f"📍 Base URL: {BASE_URL}")
        print(f"⏰ Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"👤 SuperAdmin: {SUPERADMIN_EMAIL}")
        
        # Run all test suites in order
        self.test_superadmin_login()
        self.test_create_user_functionality()
        self.test_plans_crud_operations()
        self.test_payment_subscription_fix()
        self.test_system_health()
        
        # Print summary
        self.print_summary()
        
    def print_summary(self):
        """Print test summary"""
        print("\n" + "="*80)
        print("📋 TEST SUMMARY")
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
            print("\n🎉 All test categories passed!")
            
        return {
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "failed_categories": failed_categories,
            "results": self.test_results
        }

if __name__ == "__main__":
    tester = MailGuardTester()
    results = tester.run_all_tests()