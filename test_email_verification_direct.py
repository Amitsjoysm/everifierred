#!/usr/bin/env python3
"""
Direct test of email verification fallback mechanism
Tests the email_verifier.py function directly without API authentication
"""

import asyncio
import sys
import os

# Add backend directory to path
sys.path.append('/app/backend')

from email_verifier import verify_single_email
from config import settings
import logging

# Configure logging to see which API is used
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_email_verification_fallback():
    """Test email verification with fallback mechanism"""
    print("🔄 Testing Email Verification Fallback Mechanism")
    print(f"Primary API: {settings.EMAIL_VERIFIER_API}")
    print(f"Fallback API: {settings.EMAIL_VERIFIER_API_FALLBACK}")
    print("-" * 60)
    
    test_emails = [
        "test@example.com",
        "valid@gmail.com", 
        "invalid@nonexistentdomain12345.com"
    ]
    
    results = []
    
    for email in test_emails:
        print(f"\n🧪 Testing: {email}")
        try:
            result = await verify_single_email(email)
            if result:
                print(f"✅ SUCCESS: {email}")
                print(f"   Reachable: {result.is_reachable}")
                print(f"   Confidence: {result.confidence_score}%")
                print(f"   Valid Syntax: {result.is_valid_syntax}")
                print(f"   Disposable: {result.is_disposable}")
                print(f"   Deliverable: {result.is_deliverable}")
                results.append({
                    "email": email,
                    "success": True,
                    "result": result
                })
            else:
                print(f"❌ FAILED: {email} - No result returned")
                results.append({
                    "email": email,
                    "success": False,
                    "error": "No result returned"
                })
        except Exception as e:
            print(f"❌ ERROR: {email} - {str(e)}")
            results.append({
                "email": email,
                "success": False,
                "error": str(e)
            })
    
    print("\n" + "="*60)
    print("📋 SUMMARY")
    print("="*60)
    
    successful = len([r for r in results if r["success"]])
    total = len(results)
    
    print(f"Total tests: {total}")
    print(f"Successful: {successful}")
    print(f"Failed: {total - successful}")
    
    if successful > 0:
        print("\n✅ Email verification fallback mechanism is working!")
        print("   Check the logs above to see which API (primary/fallback) was used")
    else:
        print("\n❌ Email verification fallback mechanism failed!")
        print("   Both primary and fallback APIs may be unavailable")
    
    return results

if __name__ == "__main__":
    results = asyncio.run(test_email_verification_fallback())