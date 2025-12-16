# 🚀 MailGuard Quick Reference Guide

## Super Admin Access

**Login Credentials:**
```
Email: amits.joys@gmail.com
Password: Admin@123
```

**URLs:**
- Login: https://payment-secure-1.preview.emergentagent.com/login
- Admin Panel: https://payment-secure-1.preview.emergentagent.com/admin
- Pricing Page: https://payment-secure-1.preview.emergentagent.com/pricing

---

## Common Admin Tasks

### 1. Create New Pricing Plan

**Via Admin Panel (UI):**
1. Login as super admin
2. Go to Admin Panel → Plans tab
3. Click "Create Plan"
4. Fill in details and save

**Via Backend:**
```bash
cd /app/backend
python3 << 'EOF'
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timezone
import uuid

async def create_plan():
    client = AsyncIOMotorClient('mongodb://localhost:27017')
    db = client['email_verifier_db']
    
    plan = {
        "id": str(uuid.uuid4()),
        "name": "Custom Plan",
        "type": "custom",
        "price": 1499,
        "credits_limit": 3000,
        "currency": "INR",
        "billing_cycle": "monthly",
        "features": [
            "3,000 email verifications/month",
            "All basic features",
            "Priority support"
        ],
        "is_active": True,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.plans.insert_one(plan)
    print(f"✅ Plan created: {plan['name']}")
    client.close()

asyncio.run(create_plan())
EOF
```

### 2. Link Plan to Razorpay

**Automatic (Recommended):**
```bash
cd /app/backend
python3 link_razorpay_plans.py
```

This will:
- Find all paid plans without Razorpay ID
- Create Razorpay subscription plans
- Link them to database

### 3. View All Plans

```bash
curl -s http://localhost:8001/api/plans | python3 -m json.tool
```

### 4. Check User Credits

```bash
cd /app/backend && python3 << 'EOF'
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

async def check_user(email):
    client = AsyncIOMotorClient('mongodb://localhost:27017')
    db = client['email_verifier_db']
    user = await db.users.find_one({"email": email})
    if user:
        print(f"Email: {user['email']}")
        print(f"Plan: {user.get('plan', 'free')}")
        print(f"Credits: {user.get('credits_limit', 0) - user.get('credits_used', 0)}")
    client.close()

asyncio.run(check_user('sharinara68@gmail.com'))
EOF
```

### 5. Restart Services

```bash
# Restart all services
sudo supervisorctl restart all

# Restart specific service
sudo supervisorctl restart backend
sudo supervisorctl restart frontend
sudo supervisorctl restart celery-worker
```

### 6. Check Service Status

```bash
sudo supervisorctl status
```

### 7. View Backend Logs

```bash
# Last 50 lines
tail -50 /var/log/supervisor/backend.err.log

# Real-time monitoring
tail -f /var/log/supervisor/backend.err.log
```

---

## Razorpay Configuration

### Test Keys (Current)
```env
RAZORPAY_KEY_ID=rzp_test_RsCrbXGSd0FUz0
RAZORPAY_KEY_SECRET=2btUY24dPm54AEQfH4t34798
```

### Test Cards

**Success:**
```
Card: 4111 1111 1111 1111
CVV: Any 3 digits
Expiry: Any future date
OTP: Any 6 digits
```

**Failure:**
```
Card: 4111 1111 1111 1112
```

---

## Current Pricing Plans

| Plan | Price | Credits | Razorpay Plan ID |
|------|-------|---------|------------------|
| Free | ₹0 | 100 | - |
| Starter | ₹499 | 1,000 | plan_RsDJhTlF4csi3G |
| Professional | ₹1,999 | 5,000 | plan_RsDJiBfDVqSBPQ |
| Enterprise | ₹7,999 | 25,000 | plan_RsDJivNwIgAF1T |

---

## Troubleshooting

### Issue: Plans not loading

**Solution:**
```bash
# Check if backend is running
sudo supervisorctl status backend

# Test API endpoint
curl -s http://localhost:8001/api/plans

# Restart backend
sudo supervisorctl restart backend
```

### Issue: Payment fails with receipt error

**Fixed:** Receipt length now limited to 40 characters

**Verify fix:**
```bash
grep -n "receipt = " /app/backend/routes_payments.py
```

### Issue: Plan not linked to Razorpay

**Solution:**
```bash
cd /app/backend
python3 link_razorpay_plans.py
```

---

## Database Access

### MongoDB Connection

```bash
cd /app/backend && python3 << 'EOF'
from motor.motor_asyncio import AsyncIOMotorClient
import asyncio

async def main():
    client = AsyncIOMotorClient('mongodb://localhost:27017')
    db = client['email_verifier_db']
    
    # Your queries here
    # Example: Count users
    count = await db.users.count_documents({})
    print(f"Total users: {count}")
    
    client.close()

asyncio.run(main())
EOF
```

### Common Queries

**Count plans:**
```python
count = await db.plans.count_documents({})
```

**Find user by email:**
```python
user = await db.users.find_one({"email": "user@example.com"})
```

**List all payments:**
```python
payments = await db.payments.find({}).to_list(100)
```

---

## Documentation Files

- **Full Razorpay Guide:** `/app/RAZORPAY_INTEGRATION_GUIDE.md`
- **Admin Plan Management:** `/app/SUPER_ADMIN_PLAN_MANAGEMENT_GUIDE.md`
- **This Quick Reference:** `/app/QUICK_REFERENCE.md`

---

## API Endpoints

### Public
- `GET /api/plans` - Get all active plans
- `GET /api/health` - Health check

### Authenticated
- `POST /api/payments/create-order?plan_id={id}` - Create payment order
- `POST /api/payments/verify` - Verify payment
- `GET /api/payments/history` - Payment history

### Admin Only
- `GET /api/admin/plans` - Get all plans (including inactive)
- `POST /api/admin/plans` - Create new plan
- `PATCH /api/admin/plans/{id}` - Update plan
- `DELETE /api/admin/plans/{id}` - Delete plan
- `GET /api/admin/payments/dashboard` - Payment analytics

---

## Support

**Check logs first:**
```bash
tail -100 /var/log/supervisor/backend.err.log
```

**Test backend health:**
```bash
curl http://localhost:8001/api/health
```

**Test frontend:**
```bash
curl http://localhost:3000 | head -20
```

---

**Last Updated:** December 16, 2025
