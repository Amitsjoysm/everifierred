#!/usr/bin/env python3
"""
MailGuard Admin Panel Testing Suite
Tests all admin panel functionality for production readiness
"""

import requests
import json
import time
import uuid
from datetime import datetime
from typing import Dict, Any, List

# Configuration - Updated for review request
BASE_URL = "https://blogging-crud.preview.emergentagent.com/api"
ADMIN_EMAIL = "amits.joys@gmail.com"
ADMIN_PASSWORD = "Admin@123"

class AdminPanelTester:
    def __init__(self):
        self.session = requests.Session()
        self.admin_token = None
        self.test_results = {
            "authentication": {"status": "pending", "details": []},
            "users_crud": {"status": "pending", "details": []},
            "plans_crud": {"status": "pending", "details": []},
            "blogs_crud": {"status": "pending", "details": []},
            "faqs_crud": {"status": "pending", "details": []},
            "analytics": {"status": "pending", "details": []},
            "payments": {"status": "pending", "details": []}
        }
        self.created_resources = {
            "plans": [],
            "blogs": [],
            "faqs": []
        }
        
    def log_result(self, category: str, test_name: str, success: bool, message: str, response_data: Any = None):
        """Log test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {category} - {test_name}: {message}")
        
        self.test_results[category]["details"].append({
            "test": test_name,
            "success": success,
            "message": message,
            "response_data": response_data
        })
        
    def make_request(self, method: str, endpoint: str, **kwargs) -> requests.Response:
        """Make HTTP request with error handling"""
        url = f"{BASE_URL}{endpoint}"
        try:
            response = self.session.request(method, url, timeout=30, **kwargs)
            return response
        except Exception as e:
            print(f"Request failed: {e}")
            return None
            
    def authenticate_admin(self) -> bool:
        """Authenticate as admin user"""
        print("\n🔐 Authenticating as admin...")
        category = "authentication"
        
        # Step 1: Login (get OTP)
        login_data = {
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        }
        
        response = self.make_request("POST", "/auth/login", json=login_data)
        if not response or response.status_code != 200:
            self.log_result(category, "POST /auth/login", False, 
                          f"Login failed: {response.status_code if response else 'No response'}")
            return False
            
        self.log_result(category, "POST /auth/login", True, "OTP sent to admin email")
        
        # For testing, we'll use a mock OTP since we can't access email
        # In production, this would require actual OTP from email
        otp = "123456"  # Mock OTP for testing
        
        # Step 2: Verify OTP
        verify_data = {
            "email": ADMIN_EMAIL,
            "otp": otp
        }
        
        response = self.make_request("POST", "/auth/verify-login", json=verify_data)
        if response and response.status_code == 200:
            data = response.json()
            self.admin_token = data.get("access_token")
            self.session.headers.update({"Authorization": f"Bearer {self.admin_token}"})
            self.log_result(category, "POST /auth/verify-login", True, "Admin authentication successful")
            
            # Update category status
            failed_tests = [t for t in self.test_results[category]["details"] if not t["success"]]
            self.test_results[category]["status"] = "failed" if failed_tests else "passed"
            return True
        else:
            self.log_result(category, "POST /auth/verify-login", False,
                          f"OTP verification failed: {response.status_code if response else 'No response'}")
            # Try direct authentication bypass for testing
            return self.try_direct_auth()
            
    def try_direct_auth(self) -> bool:
        """Try to get user info without OTP (for testing)"""
        print("🔄 Attempting direct authentication...")
        category = "authentication"
        
        # Check if there's an existing session or try to get user info
        response = self.make_request("GET", "/auth/me")
        if response and response.status_code == 200:
            user_data = response.json()
            if user_data.get("role") in ["admin", "super_admin"]:
                self.log_result(category, "Direct authentication", True, "Direct authentication successful")
                # Update category status
                failed_tests = [t for t in self.test_results[category]["details"] if not t["success"]]
                self.test_results[category]["status"] = "failed" if failed_tests else "passed"
                return True
            
        self.log_result(category, "Authentication", False, "Authentication failed - continuing with unauthenticated tests")
        self.test_results[category]["status"] = "failed"
        return False
        
    def test_users_crud(self):
        """Test Users CRUD operations"""
        print("\n👥 Testing Users CRUD...")
        category = "users_crud"
        
        if not self.admin_token:
            self.log_result(category, "Users CRUD", False, "No authentication token available")
            self.test_results[category]["status"] = "failed"
            return
            
        # Test 1: GET /api/admin/users (list all users)
        response = self.make_request("GET", "/admin/users")
        if response and response.status_code == 200:
            users = response.json()
            if isinstance(users, list):
                self.log_result(category, "GET /admin/users", True, 
                              f"Retrieved {len(users)} users", {"count": len(users)})
                
                # Test 2: GET /api/admin/users/{user_id} (get user by ID)
                if users:
                    first_user = users[0]
                    user_id = first_user.get("id")
                    if user_id:
                        response = self.make_request("GET", f"/admin/users/{user_id}")
                        if response and response.status_code == 200:
                            user_detail = response.json()
                            self.log_result(category, f"GET /admin/users/{user_id}", True,
                                          f"Retrieved user: {user_detail.get('email', 'Unknown')}")
                            
                            # Test 3: PATCH /api/admin/users/{user_id}/activate
                            response = self.make_request("PATCH", f"/admin/users/{user_id}/activate")
                            if response and response.status_code == 200:
                                self.log_result(category, f"PATCH /admin/users/{user_id}/activate", True,
                                              "User activation successful")
                            else:
                                self.log_result(category, f"PATCH /admin/users/{user_id}/activate", False,
                                              f"User activation failed: {response.status_code if response else 'No response'}")
                            
                            # Test 4: PATCH /api/admin/users/{user_id}/deactivate
                            response = self.make_request("PATCH", f"/admin/users/{user_id}/deactivate")
                            if response and response.status_code == 200:
                                self.log_result(category, f"PATCH /admin/users/{user_id}/deactivate", True,
                                              "User deactivation successful")
                            else:
                                self.log_result(category, f"PATCH /admin/users/{user_id}/deactivate", False,
                                              f"User deactivation failed: {response.status_code if response else 'No response'}")
                            
                            # Test 5: DELETE /api/admin/users/{user_id} (super admin only)
                            # Note: This is destructive, so we'll test with a non-existent user
                            fake_user_id = str(uuid.uuid4())
                            response = self.make_request("DELETE", f"/admin/users/{fake_user_id}")
                            if response:
                                if response.status_code == 404:
                                    self.log_result(category, f"DELETE /admin/users/{fake_user_id}", True,
                                                  "User deletion properly returns 404 for non-existent user")
                                elif response.status_code == 403:
                                    self.log_result(category, f"DELETE /admin/users/{fake_user_id}", True,
                                                  "User deletion properly requires super_admin role (403)")
                                else:
                                    self.log_result(category, f"DELETE /admin/users/{fake_user_id}", False,
                                                  f"Unexpected status: {response.status_code}")
                            else:
                                self.log_result(category, "DELETE user test", False, "No response")
                        else:
                            self.log_result(category, f"GET /admin/users/{user_id}", False,
                                          f"Failed to get user by ID: {response.status_code if response else 'No response'}")
                else:
                    self.log_result(category, "User operations", False, "No users available to test operations")
            else:
                self.log_result(category, "GET /admin/users", False, "Response is not a list")
        else:
            self.log_result(category, "GET /admin/users", False, 
                          f"Failed: {response.status_code if response else 'No response'}")
            
        # Update category status
        failed_tests = [t for t in self.test_results[category]["details"] if not t["success"]]
        self.test_results[category]["status"] = "failed" if failed_tests else "passed"
        
    def test_plans_crud(self):
        """Test Plans CRUD operations"""
        print("\n💰 Testing Plans CRUD...")
        category = "plans_crud"
        
        if not self.admin_token:
            self.log_result(category, "Plans CRUD", False, "No authentication token available")
            self.test_results[category]["status"] = "failed"
            return
            
        # Test 1: GET /api/admin/plans (list all plans)
        response = self.make_request("GET", "/admin/plans")
        if response and response.status_code == 200:
            plans = response.json()
            if isinstance(plans, list):
                self.log_result(category, "GET /admin/plans", True, 
                              f"Retrieved {len(plans)} plans (expected 4)", {"count": len(plans)})
                
                # Test 2: POST /api/admin/plans (create new plan - super admin only)
                test_plan = {
                    "id": str(uuid.uuid4()),
                    "name": "Test Plan",
                    "type": "test",
                    "price": 99.99,
                    "credits_limit": 1000,
                    "features": ["Test feature 1", "Test feature 2"],
                    "is_active": True,
                    "created_at": datetime.now().isoformat()
                }
                
                response = self.make_request("POST", "/admin/plans", json=test_plan)
                if response:
                    if response.status_code == 201 or response.status_code == 200:
                        created_plan = response.json()
                        self.created_resources["plans"].append(created_plan.get("id", test_plan["id"]))
                        self.log_result(category, "POST /admin/plans", True,
                                      f"Plan created successfully: {created_plan.get('name', 'Unknown')}")
                        
                        # Test 3: PATCH /api/admin/plans/{plan_id} (update plan - super admin only)
                        plan_id = created_plan.get("id", test_plan["id"])
                        update_data = {"name": "Updated Test Plan", "price": 149.99}
                        
                        response = self.make_request("PATCH", f"/admin/plans/{plan_id}", json=update_data)
                        if response and response.status_code == 200:
                            self.log_result(category, f"PATCH /admin/plans/{plan_id}", True,
                                          "Plan update successful")
                        else:
                            self.log_result(category, f"PATCH /admin/plans/{plan_id}", False,
                                          f"Plan update failed: {response.status_code if response else 'No response'}")
                        
                        # Test 4: DELETE /api/admin/plans/{plan_id} (delete plan - super admin only)
                        response = self.make_request("DELETE", f"/admin/plans/{plan_id}")
                        if response and response.status_code == 200:
                            self.log_result(category, f"DELETE /admin/plans/{plan_id}", True,
                                          "Plan deletion successful")
                            # Remove from cleanup list since it's already deleted
                            if plan_id in self.created_resources["plans"]:
                                self.created_resources["plans"].remove(plan_id)
                        else:
                            self.log_result(category, f"DELETE /admin/plans/{plan_id}", False,
                                          f"Plan deletion failed: {response.status_code if response else 'No response'}")
                    elif response.status_code == 403:
                        self.log_result(category, "POST /admin/plans", True,
                                      "Plan creation properly requires super_admin role (403)")
                    else:
                        self.log_result(category, "POST /admin/plans", False,
                                      f"Plan creation failed: {response.status_code}")
                else:
                    self.log_result(category, "POST /admin/plans", False, "No response")
            else:
                self.log_result(category, "GET /admin/plans", False, "Response is not a list")
        else:
            self.log_result(category, "GET /admin/plans", False, 
                          f"Failed: {response.status_code if response else 'No response'}")
            
        # Update category status
        failed_tests = [t for t in self.test_results[category]["details"] if not t["success"]]
        self.test_results[category]["status"] = "failed" if failed_tests else "passed"
        
    def test_blogs_crud(self):
        """Test Blogs CRUD operations"""
        print("\n📝 Testing Blogs CRUD...")
        category = "blogs_crud"
        
        if not self.admin_token:
            self.log_result(category, "Blogs CRUD", False, "No authentication token available")
            self.test_results[category]["status"] = "failed"
            return
            
        # Test 1: GET /api/admin/blogs (list all blogs)
        response = self.make_request("GET", "/admin/blogs")
        if response and response.status_code == 200:
            blogs = response.json()
            if isinstance(blogs, list):
                self.log_result(category, "GET /admin/blogs", True, 
                              f"Retrieved {len(blogs)} blogs (expected 4)", {"count": len(blogs)})
                
                # Test 2: POST /api/admin/blogs (create new blog)
                test_blog = {
                    "title": "Test Blog Post",
                    "content": "This is a test blog post content for testing purposes.",
                    "excerpt": "Test blog excerpt",
                    "author": "Test Author",
                    "tags": ["test", "blog"],
                    "is_published": True,
                    "meta_description": "Test meta description",
                    "meta_keywords": ["test", "blog", "admin"]
                }
                
                response = self.make_request("POST", "/admin/blogs", json=test_blog)
                if response and response.status_code == 200:
                    created_blog = response.json()
                    blog_id = created_blog.get("id")
                    self.created_resources["blogs"].append(blog_id)
                    self.log_result(category, "POST /admin/blogs", True,
                                  f"Blog created successfully: {created_blog.get('title', 'Unknown')}")
                    
                    # Test 3: PATCH /api/admin/blogs/{blog_id} (update blog)
                    update_data = {
                        "title": "Updated Test Blog Post",
                        "content": "Updated content for testing"
                    }
                    
                    response = self.make_request("PATCH", f"/admin/blogs/{blog_id}", json=update_data)
                    if response and response.status_code == 200:
                        self.log_result(category, f"PATCH /admin/blogs/{blog_id}", True,
                                      "Blog update successful")
                    else:
                        self.log_result(category, f"PATCH /admin/blogs/{blog_id}", False,
                                      f"Blog update failed: {response.status_code if response else 'No response'}")
                    
                    # Test 4: DELETE /api/admin/blogs/{blog_id} (delete blog - super admin only)
                    response = self.make_request("DELETE", f"/admin/blogs/{blog_id}")
                    if response:
                        if response.status_code == 200:
                            self.log_result(category, f"DELETE /admin/blogs/{blog_id}", True,
                                          "Blog deletion successful")
                            # Remove from cleanup list since it's already deleted
                            if blog_id in self.created_resources["blogs"]:
                                self.created_resources["blogs"].remove(blog_id)
                        elif response.status_code == 403:
                            self.log_result(category, f"DELETE /admin/blogs/{blog_id}", True,
                                          "Blog deletion properly requires super_admin role (403)")
                        else:
                            self.log_result(category, f"DELETE /admin/blogs/{blog_id}", False,
                                          f"Blog deletion failed: {response.status_code}")
                    else:
                        self.log_result(category, "DELETE blog test", False, "No response")
                else:
                    self.log_result(category, "POST /admin/blogs", False,
                                  f"Blog creation failed: {response.status_code if response else 'No response'}")
            else:
                self.log_result(category, "GET /admin/blogs", False, "Response is not a list")
        else:
            self.log_result(category, "GET /admin/blogs", False, 
                          f"Failed: {response.status_code if response else 'No response'}")
            
        # Update category status
        failed_tests = [t for t in self.test_results[category]["details"] if not t["success"]]
        self.test_results[category]["status"] = "failed" if failed_tests else "passed"
        
    def test_faqs_crud(self):
        """Test FAQs CRUD operations"""
        print("\n❓ Testing FAQs CRUD...")
        category = "faqs_crud"
        
        if not self.admin_token:
            self.log_result(category, "FAQs CRUD", False, "No authentication token available")
            self.test_results[category]["status"] = "failed"
            return
            
        # Test 1: GET /api/admin/faqs (list all FAQs)
        response = self.make_request("GET", "/admin/faqs")
        if response and response.status_code == 200:
            faqs = response.json()
            if isinstance(faqs, list):
                self.log_result(category, "GET /admin/faqs", True, 
                              f"Retrieved {len(faqs)} FAQs (expected 12)", {"count": len(faqs)})
                
                # Test 2: POST /api/admin/faqs (create new FAQ)
                test_faq = {
                    "question": "Test FAQ Question?",
                    "answer": "This is a test FAQ answer for testing purposes.",
                    "category": "testing",
                    "order": 999,
                    "is_published": True
                }
                
                response = self.make_request("POST", "/admin/faqs", json=test_faq)
                if response and response.status_code == 200:
                    created_faq = response.json()
                    faq_id = created_faq.get("id")
                    self.created_resources["faqs"].append(faq_id)
                    self.log_result(category, "POST /admin/faqs", True,
                                  f"FAQ created successfully: {created_faq.get('question', 'Unknown')}")
                    
                    # Test 3: PATCH /api/admin/faqs/{faq_id} (update FAQ)
                    update_data = {
                        "question": "Updated Test FAQ Question?",
                        "answer": "Updated test FAQ answer"
                    }
                    
                    response = self.make_request("PATCH", f"/admin/faqs/{faq_id}", json=update_data)
                    if response and response.status_code == 200:
                        self.log_result(category, f"PATCH /admin/faqs/{faq_id}", True,
                                      "FAQ update successful")
                    else:
                        self.log_result(category, f"PATCH /admin/faqs/{faq_id}", False,
                                      f"FAQ update failed: {response.status_code if response else 'No response'}")
                    
                    # Test 4: DELETE /api/admin/faqs/{faq_id} (delete FAQ - super admin only)
                    response = self.make_request("DELETE", f"/admin/faqs/{faq_id}")
                    if response:
                        if response.status_code == 200:
                            self.log_result(category, f"DELETE /admin/faqs/{faq_id}", True,
                                          "FAQ deletion successful")
                            # Remove from cleanup list since it's already deleted
                            if faq_id in self.created_resources["faqs"]:
                                self.created_resources["faqs"].remove(faq_id)
                        elif response.status_code == 403:
                            self.log_result(category, f"DELETE /admin/faqs/{faq_id}", True,
                                          "FAQ deletion properly requires super_admin role (403)")
                        else:
                            self.log_result(category, f"DELETE /admin/faqs/{faq_id}", False,
                                          f"FAQ deletion failed: {response.status_code}")
                    else:
                        self.log_result(category, "DELETE FAQ test", False, "No response")
                else:
                    self.log_result(category, "POST /admin/faqs", False,
                                  f"FAQ creation failed: {response.status_code if response else 'No response'}")
            else:
                self.log_result(category, "GET /admin/faqs", False, "Response is not a list")
        else:
            self.log_result(category, "GET /admin/faqs", False, 
                          f"Failed: {response.status_code if response else 'No response'}")
            
        # Update category status
        failed_tests = [t for t in self.test_results[category]["details"] if not t["success"]]
        self.test_results[category]["status"] = "failed" if failed_tests else "passed"
        
    def test_analytics(self):
        """Test Analytics endpoint"""
        print("\n📊 Testing Analytics...")
        category = "analytics"
        
        if not self.admin_token:
            self.log_result(category, "Analytics", False, "No authentication token available")
            self.test_results[category]["status"] = "failed"
            return
            
        # Test: GET /api/admin/analytics
        response = self.make_request("GET", "/admin/analytics")
        if response and response.status_code == 200:
            analytics = response.json()
            expected_fields = [
                "total_users", "active_users", "total_verifications", 
                "verifications_today", "revenue_total", "revenue_month", 
                "plan_distribution"
            ]
            
            has_all_fields = all(field in analytics for field in expected_fields)
            if has_all_fields:
                self.log_result(category, "GET /admin/analytics", True,
                              f"Analytics retrieved with all expected fields: {list(analytics.keys())}")
            else:
                missing_fields = [field for field in expected_fields if field not in analytics]
                self.log_result(category, "GET /admin/analytics", False,
                              f"Analytics missing fields: {missing_fields}")
        else:
            self.log_result(category, "GET /admin/analytics", False,
                          f"Failed: {response.status_code if response else 'No response'}")
            
        # Update category status
        failed_tests = [t for t in self.test_results[category]["details"] if not t["success"]]
        self.test_results[category]["status"] = "failed" if failed_tests else "passed"
        
    def test_payment_endpoints(self):
        """Test Payment endpoints"""
        print("\n💳 Testing Payment Endpoints...")
        category = "payments"
        
        # Test 1: GET /api/payments/plans (get available plans)
        response = self.make_request("GET", "/payments/plans")
        if response and response.status_code == 200:
            plans = response.json()
            if isinstance(plans, list):
                self.log_result(category, "GET /payments/plans", True, 
                              f"Retrieved {len(plans)} payment plans")
            else:
                self.log_result(category, "GET /payments/plans", False, "Response is not a list")
        else:
            self.log_result(category, "GET /payments/plans", False,
                          f"Failed: {response.status_code if response else 'No response'}")
        
        if not self.admin_token:
            self.log_result(category, "Authenticated payment tests", False, "No authentication token available")
            self.test_results[category]["status"] = "failed"
            return
            
        # Test 2: POST /api/payments/create-order (create payment order)
        # We'll test with a non-existent plan to avoid creating actual orders
        fake_plan_id = str(uuid.uuid4())
        response = self.make_request("POST", "/payments/create-order", params={"plan_id": fake_plan_id})
        if response:
            if response.status_code == 404:
                self.log_result(category, "POST /payments/create-order", True,
                              "Order creation properly returns 404 for non-existent plan")
            elif response.status_code == 403:
                self.log_result(category, "POST /payments/create-order", True,
                              "Order creation properly requires authentication (403)")
            else:
                self.log_result(category, "POST /payments/create-order", False,
                              f"Unexpected status: {response.status_code}")
        else:
            self.log_result(category, "POST /payments/create-order", False, "No response")
        
        # Test 3: POST /api/payments/verify (verify payment)
        # We'll test with fake data to check validation
        fake_verify_data = {
            "razorpay_order_id": "fake_order_id",
            "razorpay_payment_id": "fake_payment_id", 
            "razorpay_signature": "fake_signature",
            "plan_id": fake_plan_id
        }
        response = self.make_request("POST", "/payments/verify", json=fake_verify_data)
        if response:
            if response.status_code in [400, 404]:
                self.log_result(category, "POST /payments/verify", True,
                              f"Payment verification properly validates data ({response.status_code})")
            elif response.status_code == 403:
                self.log_result(category, "POST /payments/verify", True,
                              "Payment verification properly requires authentication (403)")
            else:
                self.log_result(category, "POST /payments/verify", False,
                              f"Unexpected status: {response.status_code}")
        else:
            self.log_result(category, "POST /payments/verify", False, "No response")
        
        # Test 4: GET /api/payments/history (get payment history)
        response = self.make_request("GET", "/payments/history")
        if response and response.status_code == 200:
            history = response.json()
            if isinstance(history, list):
                self.log_result(category, "GET /payments/history", True,
                              f"Retrieved {len(history)} payment records")
            else:
                self.log_result(category, "GET /payments/history", False, "Response is not a list")
        else:
            self.log_result(category, "GET /payments/history", False,
                          f"Failed: {response.status_code if response else 'No response'}")
            
        # Update category status
        failed_tests = [t for t in self.test_results[category]["details"] if not t["success"]]
        self.test_results[category]["status"] = "failed" if failed_tests else "passed"
        
    def test_authorization_levels(self):
        """Test different authorization levels"""
        print("\n🔒 Testing Authorization Levels...")
        
        # Test that admin endpoints require authentication
        endpoints_to_test = [
            ("GET", "/admin/users"),
            ("GET", "/admin/plans"),
            ("GET", "/admin/blogs"),
            ("GET", "/admin/faqs"),
            ("GET", "/admin/analytics")
        ]
        
        # Temporarily remove auth header
        original_headers = self.session.headers.copy()
        if "Authorization" in self.session.headers:
            del self.session.headers["Authorization"]
        
        for method, endpoint in endpoints_to_test:
            response = self.make_request(method, endpoint)
            if response and response.status_code == 403:
                print(f"✅ {method} {endpoint}: Properly requires authentication (403)")
            else:
                print(f"❌ {method} {endpoint}: Should require authentication but got {response.status_code if response else 'No response'}")
        
        # Restore auth headers
        self.session.headers.update(original_headers)
        
    def cleanup_created_resources(self):
        """Clean up any resources created during testing"""
        print("\n🧹 Cleaning up created resources...")
        
        if not self.admin_token:
            print("No authentication token for cleanup")
            return
        
        # Clean up plans
        for plan_id in self.created_resources["plans"]:
            response = self.make_request("DELETE", f"/admin/plans/{plan_id}")
            if response and response.status_code == 200:
                print(f"✅ Cleaned up plan: {plan_id}")
            else:
                print(f"❌ Failed to clean up plan: {plan_id}")
        
        # Clean up blogs
        for blog_id in self.created_resources["blogs"]:
            response = self.make_request("DELETE", f"/admin/blogs/{blog_id}")
            if response and response.status_code == 200:
                print(f"✅ Cleaned up blog: {blog_id}")
            else:
                print(f"❌ Failed to clean up blog: {blog_id}")
        
        # Clean up FAQs
        for faq_id in self.created_resources["faqs"]:
            response = self.make_request("DELETE", f"/admin/faqs/{faq_id}")
            if response and response.status_code == 200:
                print(f"✅ Cleaned up FAQ: {faq_id}")
            else:
                print(f"❌ Failed to clean up FAQ: {faq_id}")
        
    def run_all_tests(self):
        """Run all test suites"""
        print("🚀 Starting MailGuard Admin Panel Tests")
        print(f"📍 Base URL: {BASE_URL}")
        print(f"⏰ Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        try:
            # Authenticate first
            auth_success = self.authenticate_admin()
            
            # Run all test suites
            self.test_users_crud()
            self.test_plans_crud()
            self.test_blogs_crud()
            self.test_faqs_crud()
            self.test_analytics()
            self.test_payment_endpoints()
            
            # Test authorization levels
            self.test_authorization_levels()
            
            # Print summary
            self.print_summary()
            
        finally:
            # Always try to clean up
            self.cleanup_created_resources()
        
    def print_summary(self):
        """Print test summary"""
        print("\n" + "="*80)
        print("📋 ADMIN PANEL TEST SUMMARY")
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
    tester = AdminPanelTester()
    results = tester.run_all_tests()