# 👨‍💼 Super Admin Plan Management Guide

## Overview

This comprehensive guide explains how Super Admins can manage pricing plans in the MailGuard application, including creating new plans, linking them to Razorpay, and managing existing plans.

---

## 📋 Table of Contents

1. [Accessing Admin Panel](#accessing-admin-panel)
2. [Managing Plans via UI](#managing-plans-via-ui)
3. [Managing Plans via Backend](#managing-plans-via-backend)
4. [Linking Plans to Razorpay](#linking-plans-to-razorpay)
5. [Plan Fields Explained](#plan-fields-explained)
6. [Best Practices](#best-practices)
7. [Troubleshooting](#troubleshooting)

---

## 🔐 Accessing Admin Panel

### Step 1: Login as Super Admin

**Current Super Admin Credentials:**
```
Email: amits.joys@gmail.com
Password: Admin@123
```

**Login URL:**
```
https://yourdomain.com/login
```

### Step 2: Navigate to Admin Panel

After login:
1. Click on your profile icon (top right)
2. Select **Admin Panel** from dropdown

Or directly visit:
```
https://yourdomain.com/admin
```

---

## 🎯 Managing Plans via UI

### View All Plans

1. Go to Admin Panel
2. Click on **Plans** tab
3. You'll see all existing plans in a table:
   - Plan Name
   - Type
   - Price
   - Credits Limit
   - Razorpay Plan ID
   - Active Status
   - Actions

### Create New Plan

#### Step 1: Open Create Modal

1. In Admin Panel → Plans tab
2. Click **Create Plan** button (top right)

#### Step 2: Fill Plan Details

**Form Fields:**

| Field | Description | Example |
|-------|-------------|----------|
| **Plan Name** | Display name of the plan | "Business" |
| **Plan Type** | Unique identifier (lowercase, no spaces) | "business" |
| **Price (₹)** | Monthly price in INR | 2999 |
| **Credits Limit** | Number of email verifications | 10000 |
| **Billing Cycle** | Payment frequency | "monthly" |
| **Currency** | Payment currency | "INR" |
| **Features** | List of features (one per line) | See below |
| **Active** | Enable/disable plan | ✅ Checked |

**Example Features:**
```
10,000 email verifications/month
All professional features
Priority API access
Dedicated support
Custom integrations
Advanced analytics
```

#### Step 3: Save Plan

1. Click **Create Plan** button
2. Plan will be saved to database
3. You'll see success message

**⚠️ Important:** New plan is NOT yet linked to Razorpay. See [Linking Plans to Razorpay](#linking-plans-to-razorpay).

### Edit Existing Plan

1. In Plans tab, find the plan
2. Click **Edit** button (pencil icon)
3. Modify fields as needed
4. Click **Update Plan**

**Note:** Changing price of an active plan affects new subscriptions only. Existing subscribers keep their current price.

### Delete Plan

⚠️ **Warning:** Deleting a plan is permanent!

1. In Plans tab, find the plan
2. Click **Delete** button (trash icon)
3. Confirm deletion

**Best Practice:** Instead of deleting, set `is_active` to `false` to hide the plan while preserving historical data.

---

## 💻 Managing Plans via Backend

### Method 1: Using Admin API Endpoints

#### Create Plan via API

```bash
curl -X POST "https://yourdomain.com/api/admin/plans" \
  -H "Authorization: Bearer YOUR_ADMIN_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Business",
    "type": "business",
    "price": 2999,
    "credits_limit": 10000,
    "currency": "INR",
    "billing_cycle": "monthly",
    "features": [
      "10,000 email verifications/month",
      "All professional features",
      "Priority support"
    ],
    "is_active": true
  }'
```

#### Update Plan via API

```bash
curl -X PATCH "https://yourdomain.com/api/admin/plans/PLAN_ID" \
  -H "Authorization: Bearer YOUR_ADMIN_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "price": 3499,
    "credits_limit": 12000
  }'
```

#### Delete Plan via API

```bash
curl -X DELETE "https://yourdomain.com/api/admin/plans/PLAN_ID" \
  -H "Authorization: Bearer YOUR_ADMIN_JWT_TOKEN"
```

### Method 2: Direct Database Access

```bash
cd /app/backend && python3 << 'EOF'
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timezone
import uuid

async def create_plan():
    client = AsyncIOMotorClient('mongodb://localhost:27017')
    db = client['email_verifier_db']
    
    plan = {
        "id": str(uuid.uuid4()),
        "name": "Business",
        "type": "business",
        "price": 2999,
        "credits_limit": 10000,
        "currency": "INR",
        "billing_cycle": "monthly",
        "razorpay_plan_id_inr": None,  # Will be set when linked
        "is_recurring": False,  # Will be True when linked to Razorpay
        "features": [
            "10,000 email verifications/month",
            "All professional features",
            "Priority support",
            "Custom integrations"
        ],
        "is_active": True,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.plans.insert_one(plan)
    print(f"✅ Plan created: {plan['id']}")
    
    client.close()

asyncio.run(create_plan())
EOF
```

---

## 🔗 Linking Plans to Razorpay

### Why Link Plans?

- Enables payment processing
- Creates subscription plans in Razorpay
- Allows recurring billing (if configured)
- Tracks payments and refunds

### Automatic Linking (Recommended)

#### Step 1: Ensure Razorpay Credentials

Check `/app/backend/.env`:

```env
RAZORPAY_KEY_ID=rzp_test_XXXXX        # Or rzp_live_XXXXX for production
RAZORPAY_KEY_SECRET=XXXXX
```

#### Step 2: Run Linking Script

```bash
cd /app/backend
python3 link_razorpay_plans.py
```

**What happens:**

1. Script finds all paid plans (price > 0) without Razorpay plan ID
2. Creates subscription plan in Razorpay for each
3. Updates database with Razorpay plan ID
4. Sets `is_recurring` to `true`

**Expected Output:**

```
======================================================================
  RAZORPAY SUBSCRIPTION PLAN LINKER
======================================================================

✓ Razorpay Key ID: rzp_test_XXXXX
✓ Using Test Mode

✓ Found 1 paid plan(s) to process

Processing: Business
  Plan ID: uuid-here
  Price: ₹2999
  Credits: 10000
  Creating Razorpay subscription plan...
  ✓ Created and linked Razorpay Plan: plan_XXXXXXXXXX

======================================================================
  FINAL STATUS
======================================================================

Business:
  Status: ✓ Linked
  Razorpay Plan ID: plan_XXXXXXXXXX

======================================================================
```

### Manual Linking (Advanced)

#### Step 1: Create Plan in Razorpay Dashboard

1. Login to Razorpay Dashboard
2. Go to **Products** → **Subscriptions** → **Plans**
3. Click **Create Plan**
4. Fill details:
   - Plan Name: "Business Plan"
   - Billing Cycle: Monthly
   - Amount: 299900 (₹2999 in paise)
   - Currency: INR
5. Save and copy the Plan ID (e.g., `plan_XXXXXXXXXX`)

#### Step 2: Update Database

```bash
cd /app/backend && python3 << 'EOF'
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

async def link_plan():
    client = AsyncIOMotorClient('mongodb://localhost:27017')
    db = client['email_verifier_db']
    
    await db.plans.update_one(
        {"type": "business"},  # Find your plan
        {"$set": {
            "razorpay_plan_id_inr": "plan_XXXXXXXXXX",
            "is_recurring": True
        }}
    )
    
    print("✅ Plan linked to Razorpay")
    client.close()

asyncio.run(link_plan())
EOF
```

### Verify Linking

```bash
# Check if plan is linked
curl -s http://localhost:8001/api/plans | grep -A 5 "Business"
```

Look for:
```json
{
  "name": "Business",
  "razorpay_plan_id_inr": "plan_XXXXXXXXXX",
  "is_recurring": true
}
```

---

## 📝 Plan Fields Explained

### Required Fields

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| `name` | string | Display name | Max 100 chars |
| `type` | string | Unique identifier | Lowercase, no spaces, max 50 chars |
| `price` | float | Monthly price in INR | >= 0 |
| `credits_limit` | integer | Number of verifications | > 0 |

### Optional Fields

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `price_usd` | float | null | Price in USD (for international) |
| `currency` | string | "INR" | Payment currency |
| `billing_cycle` | string | "monthly" | Billing frequency |
| `razorpay_plan_id_inr` | string | null | Razorpay plan ID for INR |
| `razorpay_plan_id_usd` | string | null | Razorpay plan ID for USD |
| `is_recurring` | boolean | false | Enable recurring billing |
| `features` | array | [] | List of features |
| `is_active` | boolean | true | Show/hide plan |

### Auto-Generated Fields

- `id` - UUID v4
- `created_at` - ISO 8601 timestamp
- `updated_at` - ISO 8601 timestamp (on updates)

---

## ✅ Best Practices

### 1. Pricing Strategy

**Recommended Plan Structure:**

```
Free Plan    → Hook users with limited credits
Starter      → Entry point for paid users (₹500-1000)
Professional → Most popular tier (₹1500-3000)
Enterprise   → High volume users (₹5000+)
```

**Pricing Psychology:**
- Make Professional plan most attractive ("Most Popular" badge)
- Show cost per verification (e.g., "₹0.50 per verification")
- Annual plans with 2 months free discount

### 2. Credits Allocation

**Formula:**
```
Price per credit = Plan Price / Credits Limit
```

**Keep consistent:**
```
Starter:       ₹499 / 1,000  = ₹0.499 per credit
Professional:  ₹1,999 / 5,000 = ₹0.399 per credit (20% discount)
Enterprise:    ₹7,999 / 25,000 = ₹0.319 per credit (36% discount)
```

### 3. Feature Differentiation

**Free Plan:**
- Basic verification
- Limited support
- Standard API access

**Paid Plans:**
- Add features progressively:
  - Starter: Bulk verification
  - Professional: Priority support, advanced analytics
  - Enterprise: Custom integrations, dedicated account manager

### 4. Plan Activation

**Before going live:**

- [ ] Test plan thoroughly with test cards
- [ ] Verify Razorpay plan is linked
- [ ] Check features list is complete
- [ ] Ensure pricing is correct
- [ ] Test payment flow end-to-end
- [ ] Set `is_active` to `true`

### 5. Handling Plan Changes

**When updating active plans:**

1. **Price Increase:**
   - Create new plan version
   - Grandfather existing users
   - Or notify users 30 days before change

2. **Price Decrease:**
   - Safe to update directly
   - Existing users benefit immediately

3. **Feature Changes:**
   - Add features: Safe to update
   - Remove features: Create new plan, deprecate old one

### 6. Free Plan Strategy

**Always have a free plan:**
- Attracts users
- Allows testing
- Builds trust
- Conversion funnel entry point

**Free plan should:**
- Have limited but useful credits (100-500)
- Show upgrade prompts when near limit
- Have all features but restricted usage

---

## 🐛 Troubleshooting

### Issue 1: Plan not showing on Pricing page

**Check:**

1. Is plan active?
```bash
cd /app/backend && python3 << 'EOF'
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

async def check():
    client = AsyncIOMotorClient('mongodb://localhost:27017')
    db = client['email_verifier_db']
    plan = await db.plans.find_one({"type": "business"})
    print(f"Active: {plan.get('is_active', False)}")
    client.close()

asyncio.run(check())
EOF
```

2. Clear browser cache
3. Check frontend console for errors

### Issue 2: "Payment service not configured" error

**Cause:** Plan not linked to Razorpay

**Solution:**
```bash
cd /app/backend
python3 link_razorpay_plans.py
```

### Issue 3: Wrong price showing

**Check:**

1. Database value:
```bash
curl -s http://localhost:8001/api/plans | grep -A 10 "Business"
```

2. Razorpay dashboard:
   - Login to Razorpay
   - Check subscription plan amount

3. If mismatch, update database:
```bash
cd /app/backend && python3 << 'EOF'
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

async def fix_price():
    client = AsyncIOMotorClient('mongodb://localhost:27017')
    db = client['email_verifier_db']
    await db.plans.update_one(
        {"type": "business"},
        {"$set": {"price": 2999}}
    )
    print("✅ Price updated")
    client.close()

asyncio.run(fix_price())
EOF
```

### Issue 4: Can't create plan via UI

**Check:**

1. Are you logged in as super_admin?
2. Check browser console for errors
3. Check backend logs:
```bash
tail -50 /var/log/supervisor/backend.err.log
```

4. Try via API to get detailed error:
```bash
curl -X POST "http://localhost:8001/api/admin/plans" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "Test", "type": "test", "price": 100, "credits_limit": 100}'
```

---

## 📊 Plan Management Workflow

### Complete Workflow for Adding New Plan

```mermaid
graph TD
    A[Login as Super Admin] --> B[Go to Admin Panel]
    B --> C[Click Plans Tab]
    C --> D[Click Create Plan]
    D --> E[Fill Plan Details]
    E --> F[Save Plan]
    F --> G[Run link_razorpay_plans.py]
    G --> H[Verify on Pricing Page]
    H --> I{Working?}
    I -->|Yes| J[Plan Live!]
    I -->|No| K[Check Logs]
    K --> G
```

### Step-by-Step Checklist

**Phase 1: Planning**
- [ ] Decide plan name and pricing
- [ ] Calculate credits allocation
- [ ] List features
- [ ] Determine target audience

**Phase 2: Creation**
- [ ] Login as super admin
- [ ] Create plan in Admin Panel
- [ ] Verify plan in database

**Phase 3: Razorpay Linking**
- [ ] Ensure Razorpay credentials in .env
- [ ] Run `link_razorpay_plans.py`
- [ ] Verify Razorpay plan ID is set
- [ ] Check Razorpay dashboard

**Phase 4: Testing**
- [ ] View plan on pricing page
- [ ] Test payment with test card
- [ ] Verify credits added after payment
- [ ] Check payment history

**Phase 5: Launch**
- [ ] Set is_active to true
- [ ] Add to marketing materials
- [ ] Monitor first transactions

---

## 📞 Support

### Database Queries

**View all plans:**
```bash
cd /app/backend && python3 << 'EOF'
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

async def view_plans():
    client = AsyncIOMotorClient('mongodb://localhost:27017')
    db = client['email_verifier_db']
    plans = await db.plans.find({}, {"_id": 0}).to_list(100)
    for p in plans:
        print(f"{p['name']}: ₹{p['price']} - {p.get('razorpay_plan_id_inr', 'Not linked')}")
    client.close()

asyncio.run(view_plans())
EOF
```

**Count active plans:**
```bash
cd /app/backend && python3 << 'EOF'
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

async def count():
    client = AsyncIOMotorClient('mongodb://localhost:27017')
    db = client['email_verifier_db']
    count = await db.plans.count_documents({"is_active": True})
    print(f"Active plans: {count}")
    client.close()

asyncio.run(count())
EOF
```

---

**Last Updated:** December 16, 2025  
**Version:** 1.0  
**Maintained by:** Development Team
