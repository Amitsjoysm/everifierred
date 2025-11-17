"""
Seed initial data for MailGuard application
Run this script to populate the database with initial plans, blogs, and FAQs
"""

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timezone
from config import settings
import uuid


async def seed_database():
    """Seed the database with initial data"""
    client = AsyncIOMotorClient(settings.MONGO_URL)
    db = client[settings.DB_NAME]
    
    print("Starting database seeding...")
    
    # ============= Seed Plans =============
    print("\n1. Seeding pricing plans...")
    
    plans = [
        {
            "id": str(uuid.uuid4()),
            "name": "Free",
            "type": "free",
            "credits_limit": 100,
            "price": 0,
            "razorpay_plan_id": None,
            "features": [
                "100 email verifications/month",
                "Basic verification features",
                "API access",
                "Email support"
            ],
            "is_active": True,
            "created_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": str(uuid.uuid4()),
            "name": "Starter",
            "type": "starter",
            "credits_limit": 1000,
            "price": 499,
            "razorpay_plan_id": None,
            "features": [
                "1,000 email verifications/month",
                "All basic features",
                "Priority API access",
                "Bulk verification",
                "Priority email support"
            ],
            "is_active": True,
            "created_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": str(uuid.uuid4()),
            "name": "Professional",
            "type": "professional",
            "credits_limit": 5000,
            "price": 1999,
            "razorpay_plan_id": None,
            "features": [
                "5,000 email verifications/month",
                "All starter features",
                "Advanced verification",
                "Confidence scoring",
                "Webhook support",
                "24/7 priority support"
            ],
            "is_active": True,
            "created_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": str(uuid.uuid4()),
            "name": "Enterprise",
            "type": "enterprise",
            "credits_limit": 25000,
            "price": 7999,
            "razorpay_plan_id": None,
            "features": [
                "25,000 email verifications/month",
                "All professional features",
                "Dedicated account manager",
                "Custom integrations",
                "SLA guarantee",
                "White-label options"
            ],
            "is_active": True,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
    ]
    
    # Clear existing plans and insert new ones
    await db.plans.delete_many({})
    await db.plans.insert_many(plans)
    print(f"✓ Seeded {len(plans)} pricing plans")
    
    # ============= Seed Blogs =============
    print("\n2. Seeding blog posts...")
    
    blogs = [
        {
            "id": str(uuid.uuid4()),
            "slug": "how-to-verify-emails-in-excel",
            "title": "How to Verify Emails in Excel - Complete Guide 2025",
            "content": """# How to Verify Emails in Excel

Email verification is crucial for maintaining a clean email list. Here's a comprehensive guide on how to verify emails directly in Excel using various methods.

## Why Verify Emails in Excel?

- Reduce bounce rates
- Improve email deliverability
- Maintain sender reputation
- Save costs on email marketing

## Method 1: Manual Verification

While time-consuming, manual verification can be done for small lists:
1. Check for obvious typos
2. Verify domain validity
3. Look for common patterns

## Method 2: Using MailGuard API

Our API makes bulk verification simple:

1. **Export your Excel file** to CSV format
2. **Upload to MailGuard** dashboard
3. **Download results** with all verification data
4. **Import back** to Excel

## Best Practices

- Always verify before cold email campaigns
- Re-verify your list every 3-6 months
- Remove invalid emails immediately
- Use confidence scoring to prioritize contacts

## Conclusion

Verifying emails in Excel doesn't have to be complicated. With MailGuard, you can verify thousands of emails in minutes and keep your email list clean and deliverable.""",
            "excerpt": "Learn how to verify email addresses in Excel efficiently. Complete guide with methods, best practices, and tools for 2025.",
            "author": "MailGuard Team",
            "meta_title": "How to Verify Emails in Excel - Complete 2025 Guide | MailGuard",
            "meta_description": "Step-by-step guide on verifying email addresses in Excel. Learn best practices, tools, and methods to clean your email list in 2025.",
            "keywords": ["verify emails in excel", "email verification", "excel email validation", "bulk email verification"],
            "is_published": True,
            "published_at": datetime.now(timezone.utc).isoformat(),
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": str(uuid.uuid4()),
            "slug": "check-disposable-emails-free",
            "title": "How to Check Disposable Emails for Free",
            "content": """# How to Check Disposable Emails for Free

Disposable emails are temporary email addresses that users create for one-time use. They're a major problem for businesses trying to build genuine email lists.

## What Are Disposable Emails?

Disposable emails (also called temp emails or throwaway emails) are temporary email addresses that:
- Last for a limited time (minutes to days)
- Don't require real identity verification
- Are used to avoid spam
- Can't be used for long-term communication

## Why You Should Block Them

1. **Low Engagement**: Users with disposable emails rarely engage
2. **Wasted Resources**: Marketing to these addresses is pointless
3. **Skewed Analytics**: They mess up your engagement metrics
4. **Compliance Issues**: Some regulations require verified contacts

## How to Detect Disposable Emails

### Using MailGuard
Our verification service automatically detects disposable emails:
- Checks against 10,000+ known disposable domains
- Real-time detection
- API integration available

### Manual Detection
Some common disposable email domains:
- tempmail.com
- guerrillamail.com
- 10minutemail.com
- mailinator.com

## Best Practices

1. **Block at signup** - Don't let disposable emails register
2. **Verify existing lists** - Clean your database regularly
3. **Use double opt-in** - Confirm email ownership
4. **Monitor patterns** - Watch for suspicious signup patterns

## Conclusion

Detecting disposable emails is essential for maintaining a quality email list. MailGuard makes this process automatic and accurate.""",
            "excerpt": "Learn how to detect and block disposable email addresses for free. Protect your email list quality and improve engagement rates.",
            "author": "MailGuard Team",
            "meta_title": "Check Disposable Emails Free - Detection Guide | MailGuard",
            "meta_description": "Free guide to detecting disposable emails. Learn how to identify temporary email addresses and protect your email list quality.",
            "keywords": ["disposable email", "check disposable emails free", "temp email detection", "throwaway email"],
            "is_published": True,
            "published_at": datetime.now(timezone.utc).isoformat(),
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": str(uuid.uuid4()),
            "slug": "email-list-cleanup-cold-email-outreach",
            "title": "Email List Clean Up for Cold Email Outreach Success",
            "content": """# Email List Clean Up for Cold Email Outreach

Cold email outreach can be incredibly effective, but only if your email list is clean. Here's how to prepare your list for maximum deliverability and response rates.

## Why Clean Your Email List?

A dirty email list can:
- Damage your sender reputation
- Get you blacklisted
- Waste your time and money
- Reduce response rates
- Violate spam regulations

## Steps to Clean Your Email List

### 1. Remove Duplicates
Duplicate emails waste your resources and annoy recipients.

### 2. Verify Email Syntax
Check for:
- Missing @ symbols
- Invalid characters
- Incorrect domain formats

### 3. Verify Domain Validity
Ensure the domain:
- Has valid MX records
- Can receive emails
- Isn't blacklisted

### 4. SMTP Verification
Connect to mail servers to verify:
- Email address exists
- Mailbox accepts messages
- No catch-all configuration

### 5. Remove Role-Based Emails
Avoid sending to:
- info@company.com
- admin@company.com
- support@company.com

### 6. Check for Spam Traps
Spam traps are email addresses specifically created to catch spammers.

## Using MailGuard for List Cleaning

Our comprehensive verification includes:
- Syntax validation
- Domain verification
- SMTP checking
- Disposable email detection
- Spam trap identification
- Confidence scoring

## Best Practices

1. **Clean before every campaign**
2. **Maintain separate lists** for different campaigns
3. **Monitor bounce rates** closely
4. **Remove hard bounces** immediately
5. **Re-verify periodically** (every 3-6 months)

## Conclusion

A clean email list is the foundation of successful cold email outreach. Don't risk your reputation with unverified emails.""",
            "excerpt": "Master email list cleaning for cold email outreach. Learn best practices, tools, and strategies to maximize deliverability and response rates.",
            "author": "MailGuard Team",
            "meta_title": "Email List Clean Up for Cold Email Outreach | MailGuard",
            "meta_description": "Complete guide to cleaning your email list for cold email campaigns. Improve deliverability, avoid spam traps, and boost response rates.",
            "keywords": ["email list clean up", "cold email outreach", "email verification", "spam trap removal"],
            "is_published": True,
            "published_at": datetime.now(timezone.utc).isoformat(),
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": str(uuid.uuid4()),
            "slug": "b2b-email-finder-saas-startups",
            "title": "B2B Email Finder for SaaS Startups: Complete Guide",
            "content": """# B2B Email Finder for SaaS Startups

Finding and verifying B2B emails is crucial for SaaS startups looking to grow their customer base through outbound sales. This guide covers everything you need to know.

## Why Email Verification Matters for SaaS

SaaS startups face unique challenges:
- Limited marketing budgets
- Need for rapid growth
- High customer acquisition costs
- Importance of personalization

## Finding B2B Emails

### Sources for B2B Emails
1. **LinkedIn** - Professional profiles
2. **Company websites** - Contact pages
3. **Industry directories** - Specialized databases
4. **Conference attendees** - Event lists
5. **Content downloads** - Gated content

### Email Pattern Recognition
Most companies follow patterns:
- firstname.lastname@company.com
- firstname@company.com
- f.lastname@company.com

## Verifying Found Emails

Before reaching out, always verify:

### 1. Syntax Validation
Check email format is correct

### 2. Domain Verification
Ensure the company domain:
- Exists and is active
- Has valid MX records
- Can receive emails

### 3. SMTP Verification
Verify the specific email:
- Exists on the server
- Can receive messages
- Isn't a catch-all

### 4. Deliverability Check
- Not marked as spam trap
- Not on blacklists
- Has good sender score

## Using MailGuard for B2B Verification

Perfect for SaaS startups:
- **Bulk verification** - Verify entire lists
- **API integration** - Verify as you collect
- **Confidence scoring** - Prioritize best leads
- **Cost-effective** - Pay only for what you use

## Cold Email Best Practices

1. **Personalize your message** - Use company-specific info
2. **Provide value first** - Don't just pitch
3. **Keep it short** - Respect their time
4. **Clear CTA** - Make next steps obvious
5. **Follow up** - But don't spam

## Tools for SaaS Startups

### Email Finding
- LinkedIn Sales Navigator
- Hunter.io
- Apollo.io

### Verification
- **MailGuard** (best for accuracy and pricing)

### Cold Email
- Lemlist
- Woodpecker
- Reply.io

## Compliance Considerations

Always follow:
- **CAN-SPAM Act** (US)
- **GDPR** (EU)
- **CASL** (Canada)

Key requirements:
- Provide unsubscribe option
- Include physical address
- Don't use deceptive headers
- Honor opt-outs promptly

## Measuring Success

Track these metrics:
- **Open rate** - Are they reading?
- **Response rate** - Are they replying?
- **Bounce rate** - Is your list clean?
- **Unsubscribe rate** - Is your message relevant?
- **Meeting booking rate** - Is it converting?

## Conclusion

Finding and verifying B2B emails is an art and science. For SaaS startups, the key is combining quality sources with thorough verification. MailGuard makes the verification part simple and affordable.""",
            "excerpt": "Complete guide to finding and verifying B2B emails for SaaS startups. Learn sources, tools, best practices, and compliance requirements.",
            "author": "MailGuard Team",
            "meta_title": "B2B Email Finder for SaaS Startups - Complete Guide | MailGuard",
            "meta_description": "Master B2B email finding and verification for SaaS startups. Learn tools, techniques, and best practices to build quality prospect lists.",
            "keywords": ["b2b email finder", "saas startups", "email verification", "lead generation"],
            "is_published": True,
            "published_at": datetime.now(timezone.utc).isoformat(),
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
    ]
    
    await db.blogs.delete_many({})
    await db.blogs.insert_many(blogs)
    print(f"✓ Seeded {len(blogs)} blog posts")
    
    # ============= Seed FAQs =============
    print("\n3. Seeding FAQs...")
    
    faqs = [
        {
            "id": str(uuid.uuid4()),
            "question": "What is email verification?",
            "answer": "Email verification is the process of validating email addresses to ensure they are valid, active, and can receive emails. It helps reduce bounce rates and improve email deliverability.",
            "category": "general",
            "order": 1,
            "is_published": True,
            "created_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": str(uuid.uuid4()),
            "question": "How accurate is MailGuard's verification?",
            "answer": "MailGuard provides 99%+ accuracy in email verification. We use multiple verification methods including syntax validation, domain checks, SMTP verification, and disposable email detection to ensure the highest accuracy.",
            "category": "general",
            "order": 2,
            "is_published": True,
            "created_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": str(uuid.uuid4()),
            "question": "Can I verify emails in bulk?",
            "answer": "Yes! MailGuard supports bulk email verification. Simply upload a CSV or Excel file with your email list, and we'll verify all emails and provide detailed results in a downloadable file.",
            "category": "features",
            "order": 1,
            "is_published": True,
            "created_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": str(uuid.uuid4()),
            "question": "Do you offer an API?",
            "answer": "Yes, we provide a robust REST API for real-time email verification. You can integrate it into your signup forms, CRM, or any application. API documentation is available in your dashboard.",
            "category": "features",
            "order": 2,
            "is_published": True,
            "created_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": str(uuid.uuid4()),
            "question": "What is a confidence score?",
            "answer": "Confidence score is a percentage (0-100%) that indicates how confident we are that an email is valid and deliverable. Higher scores mean higher confidence. This helps you prioritize your email list.",
            "category": "features",
            "order": 3,
            "is_published": True,
            "created_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": str(uuid.uuid4()),
            "question": "How does pricing work?",
            "answer": "We offer flexible pricing plans based on the number of email verifications per month. You can start with our free plan (100 verifications/month) and upgrade as needed. Check our pricing page for details.",
            "category": "pricing",
            "order": 1,
            "is_published": True,
            "created_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": str(uuid.uuid4()),
            "question": "Can I change or cancel my plan?",
            "answer": "Yes, you can upgrade, downgrade, or cancel your plan at any time from your dashboard. Changes take effect immediately, and we'll prorate any adjustments.",
            "category": "pricing",
            "order": 2,
            "is_published": True,
            "created_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": str(uuid.uuid4()),
            "question": "Do unused credits roll over?",
            "answer": "No, unused credits do not roll over to the next month. Credits reset at the beginning of each billing cycle based on your plan.",
            "category": "pricing",
            "order": 3,
            "is_published": True,
            "created_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": str(uuid.uuid4()),
            "question": "How long does verification take?",
            "answer": "Single email verification is instant (usually under 1 second). Bulk verification speed depends on list size but typically processes 1,000-2,000 emails per minute.",
            "category": "technical",
            "order": 1,
            "is_published": True,
            "created_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": str(uuid.uuid4()),
            "question": "What file formats do you accept?",
            "answer": "We accept CSV and Excel (XLSX) files for bulk verification. Your file should have a column with email addresses. We'll detect it automatically or you can specify the column.",
            "category": "technical",
            "order": 2,
            "is_published": True,
            "created_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": str(uuid.uuid4()),
            "question": "Is my data secure?",
            "answer": "Yes! We take security seriously. All data is encrypted in transit and at rest. We never share your data with third parties and delete verification data after 30 days unless you choose to keep it.",
            "category": "security",
            "order": 1,
            "is_published": True,
            "created_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": str(uuid.uuid4()),
            "question": "Do you store verified emails?",
            "answer": "We store verification results for 30 days so you can access them from your dashboard. After that, they're automatically deleted. You can download results anytime during this period.",
            "category": "security",
            "order": 2,
            "is_published": True,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
    ]
    
    await db.faqs.delete_many({})
    await db.faqs.insert_many(faqs)
    print(f"✓ Seeded {len(faqs)} FAQs")
    
    print("\n✓ Database seeding completed successfully!")
    print("\nSummary:")
    print(f"  - Plans: {len(plans)}")
    print(f"  - Blogs: {len(blogs)}")
    print(f"  - FAQs: {len(faqs)}")
    
    client.close()


if __name__ == "__main__":
    asyncio.run(seed_database())
