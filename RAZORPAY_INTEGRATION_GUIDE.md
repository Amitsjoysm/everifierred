# 🔐 Razorpay Integration Guide for MailGuard

## Overview

This guide explains how Razorpay payment gateway is integrated into the MailGuard application and how to configure it for production use.

---

## 📋 Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Prerequisites](#prerequisites)
3. [Configuration Steps](#configuration-steps)
4. [Testing the Integration](#testing-the-integration)
5. [Going Live (Production)](#going-live-production)
6. [API Endpoints](#api-endpoints)
7. [Payment Flow](#payment-flow)
8. [Troubleshooting](#troubleshooting)

---

## 🏗️ Architecture Overview

### Components

1. **Backend (FastAPI)**
   - Handles Razorpay order creation
   - Verifies payment signatures
   - Manages payment records in MongoDB
   - Allocates credits after successful payment
   - Handles webhooks for automated updates

2. **Frontend (React)**
   - Displays pricing plans
   - Initiates Razorpay Checkout
   - Handles payment success/failure

3. **Razorpay**
   - Payment gateway service
   - Provides subscription plan management
   - Sends webhooks for payment events

### Database Collections

- `plans` - Pricing plans with Razorpay plan IDs
- `payments` - Payment transaction records
- `users` - User accounts with plan and credit information
- `payment_logs` - Audit trail of all payment attempts
- `security_logs` - Security events and fraud detection

---

## ✅ Prerequisites

### 1. Razorpay Account

- Sign up at [https://razorpay.com](https://razorpay.com)
- Complete KYC verification (for live mode)
- Get API credentials

### 2. Environment Setup

- Backend server with FastAPI
- MongoDB database
- Redis for background tasks
- Valid SSL certificate (required for production)

---

## ⚙️ Configuration Steps

### Step 1: Get Razorpay API Keys

#### For Testing (Already Configured)

```bash
Razorpay Key ID: rzp_test_RsCrbXGSd0FUz0
Razorpay Key Secret: 2btUY24dPm54AEQfH4t34798
```

#### For Production

1. Login to Razorpay Dashboard
2. Navigate to **Settings** → **API Keys**
3. Click **Generate Live Keys**
4. Copy the Key ID and Key Secret

### Step 2: Update Environment Variables

Edit `/app/backend/.env` file:

```env
# Razorpay Configuration
RAZORPAY_KEY_ID=rzp_live_YOUR_KEY_ID          # Replace with live key
RAZORPAY_KEY_SECRET=YOUR_KEY_SECRET            # Replace with live secret
RAZORPAY_WEBHOOK_SECRET=YOUR_WEBHOOK_SECRET    # From Razorpay dashboard
```

### Step 3: Create Pricing Plans in Database

Plans are already seeded with the application. To add new plans, use the Super Admin panel or run:

```bash
cd /app/backend
python3 seed_data.py
```

**Current Plans:**

| Plan | Price | Credits | Type |
|------|-------|---------|------|
| Free | ₹0 | 100 | free |
| Starter | ₹499 | 1,000 | starter |
| Professional | ₹1,999 | 5,000 | professional |
| Enterprise | ₹7,999 | 25,000 | enterprise |

### Step 4: Link Plans to Razorpay

Run the Razorpay plan linking script:

```bash
cd /app/backend
python3 link_razorpay_plans.py
```

**What this does:**

1. Creates subscription plans in Razorpay
2. Links Razorpay plan IDs to database plans
3. Enables recurring billing

**Output:**

```
✓ Created and linked Razorpay Plan: plan_XXXXXXXXXXXXX
```

### Step 5: Configure Webhooks (Production Only)

#### In Razorpay Dashboard:

1. Go to **Settings** → **Webhooks**
2. Click **Add New Webhook**
3. Enter your webhook URL:
   ```
   https://yourdomain.com/api/payments/webhook
   ```
4. Select events to listen:
   - ✅ payment.authorized
   - ✅ payment.captured
   - ✅ payment.failed
   - ✅ order.paid
   - ✅ subscription.activated
   - ✅ subscription.cancelled
5. Copy the **Webhook Secret**
6. Add it to `.env`:
   ```env
   RAZORPAY_WEBHOOK_SECRET=whsec_xxxxxxxxxxxxx
   ```

### Step 6: Restart Services

```bash
sudo supervisorctl restart backend
sudo supervisorctl restart celery-worker
```

---

## 🧪 Testing the Integration

### Test with Razorpay Test Cards

#### Successful Payment

```
Card Number: 4111 1111 1111 1111
CVV: Any 3 digits
Expiry: Any future date
OTP: Any 6 digits
```

#### Failed Payment

```
Card Number: 4111 1111 1111 1112
CVV: Any 3 digits
Expiry: Any future date
```

### Testing Flow

1. **Login as regular user:**
   - Go to: `https://yourdomain.com/login`
   - Login with your account

2. **Navigate to Pricing:**
   - Go to: `https://yourdomain.com/pricing`
   - Click **Subscribe Now** on any paid plan

3. **Complete Payment:**
   - Razorpay Checkout modal will open
   - Enter test card details
   - Complete payment

4. **Verify Success:**
   - Check dashboard for updated credits
   - Check payment history: `https://yourdomain.com/dashboard` → Payment History tab
   - Check admin panel for payment record

### Backend Testing (API)

```bash
# 1. Get all plans
curl http://localhost:8001/api/plans

# 2. Create order (requires authentication)
curl -X POST "http://localhost:8001/api/payments/create-order?plan_id=PLAN_ID" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"

# 3. Check payment history
curl -X GET "http://localhost:8001/api/payments/history" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

---

## 🚀 Going Live (Production)

### Pre-Launch Checklist

- [ ] Complete Razorpay KYC verification
- [ ] Generate live API keys
- [ ] Update `.env` with live keys
- [ ] Configure webhook URL
- [ ] Test with small real transaction
- [ ] Setup SSL certificate (HTTPS required)
- [ ] Enable webhook signature verification
- [ ] Configure proper CORS settings
- [ ] Enable rate limiting
- [ ] Setup monitoring and alerts

### Security Considerations

#### ✅ Already Implemented

1. **Payment Signature Verification**
   - All payments verified using HMAC SHA256
   - Prevents payment tampering

2. **Rate Limiting**
   - 5 requests/minute for order creation
   - 10 requests/minute for verification
   - Prevents abuse and card testing

3. **Amount Validation**
   - Server validates payment amount matches plan price
   - Prevents price manipulation

4. **Idempotency**
   - Duplicate payment prevention
   - Same order can't be processed twice

5. **Webhook Signature Verification**
   - Validates webhook requests from Razorpay
   - Prevents fake webhook attacks

6. **Security Logging**
   - All payment attempts logged
   - Security events tracked
   - Failed payment analysis

### Monitoring

**Admin Dashboard provides:**

- Total revenue
- Transaction statistics
- Success/failure rates
- Failed payment reasons
- Security events
- Fraud detection alerts

**Access:**
```
https://yourdomain.com/admin
```

---

## 📡 API Endpoints

### Public Endpoints

#### Get All Plans
```http
GET /api/plans
GET /api/payments/plans
```

**Response:**
```json
[
  {
    "id": "plan-uuid",
    "name": "Starter",
    "type": "starter",
    "price": 499.0,
    "credits_limit": 1000,
    "razorpay_plan_id_inr": "plan_XXXXX",
    "features": [...],
    "is_active": true
  }
]
```

### Authenticated Endpoints

#### Create Payment Order
```http
POST /api/payments/create-order?plan_id={plan_id}
Authorization: Bearer {jwt_token}
```

**Response:**
```json
{
  "order_id": "order_XXXXXXXXXX",
  "amount": 49900,
  "currency": "INR",
  "razorpay_key": "rzp_live_XXXXX"
}
```

#### Verify Payment
```http
POST /api/payments/verify
Authorization: Bearer {jwt_token}

Body:
{
  "razorpay_order_id": "order_XXXXX",
  "razorpay_payment_id": "pay_XXXXX",
  "razorpay_signature": "signature_XXXXX",
  "plan_id": "plan-uuid"
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Payment verified successfully",
  "credits_added": 1000
}
```

#### Get Payment History
```http
GET /api/payments/history
Authorization: Bearer {jwt_token}
```

### Admin Endpoints

#### Payment Dashboard
```http
GET /api/admin/payments/dashboard
Authorization: Bearer {admin_jwt_token}
```

#### Transaction Management
```http
GET /api/admin/payments/transactions?status=success&page=1&limit=50
Authorization: Bearer {admin_jwt_token}
```

#### Process Refund
```http
POST /api/admin/payments/refund
Authorization: Bearer {admin_jwt_token}

Body:
{
  "payment_id": "payment-uuid",
  "amount": 49900,  # Optional, full refund if not provided
  "reason": "Customer request"
}
```

---

## 🔄 Payment Flow

### User Journey

```
1. User clicks "Subscribe Now" on Pricing page
   ↓
2. Frontend calls /api/payments/create-order
   ↓
3. Backend creates Razorpay order and saves to database
   ↓
4. Frontend receives order_id and opens Razorpay Checkout
   ↓
5. User completes payment on Razorpay
   ↓
6. Razorpay sends payment details to frontend handler
   ↓
7. Frontend calls /api/payments/verify
   ↓
8. Backend verifies signature and updates:
   - Payment status → success
   - User plan → upgraded
   - User credits → increased
   ↓
9. User redirected to Dashboard with success message
   ↓
10. Razorpay sends webhook (async) for final confirmation
```

### Webhook Flow (Async)

```
1. Razorpay sends webhook to /api/payments/webhook
   ↓
2. Backend verifies webhook signature
   ↓
3. Backend checks payment status in database
   ↓
4. If not already processed:
   - Update payment status
   - Upgrade user plan
   - Add credits
   - Log transaction
   ↓
5. Send 200 OK response to Razorpay
```

---

## 🐛 Troubleshooting

### Issue 1: "Failed to create order: receipt: the length must be no more than 40"

**Solution:** ✅ Fixed in latest code. Receipt ID is now limited to 40 characters.

### Issue 2: "Payment service not configured"

**Cause:** Razorpay API keys not set in `.env`

**Solution:**
```bash
# Edit .env file
vim /app/backend/.env

# Add keys
RAZORPAY_KEY_ID=rzp_test_XXXXX
RAZORPAY_KEY_SECRET=XXXXX

# Restart backend
sudo supervisorctl restart backend
```

### Issue 3: "Failed to load pricing plans"

**Cause:** Frontend calling wrong endpoint

**Solution:** ✅ Fixed. Added `/api/plans` endpoint for backward compatibility.

### Issue 4: Credits not added after payment

**Check:**

1. Payment record in database:
```bash
cd /app/backend && python3 << 'EOF'
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

async def check_payment(email):
    client = AsyncIOMotorClient('mongodb://localhost:27017')
    db = client['email_verifier_db']
    
    user = await db.users.find_one({"email": email})
    if user:
        payments = await db.payments.find({"user_id": user['id']}).to_list(10)
        for p in payments:
            print(f"Status: {p['status']}, Amount: {p['amount']}, Plan: {p['plan_id']}")
    
    client.close()

asyncio.run(check_payment('user@example.com'))
EOF
```

2. Backend logs:
```bash
tail -100 /var/log/supervisor/backend.err.log | grep -i payment
```

### Issue 5: Webhook not working

**Check:**

1. Webhook URL is accessible (HTTPS required in production)
2. Webhook secret is configured
3. Events are selected in Razorpay dashboard
4. Check webhook logs in Razorpay dashboard

### Issue 6: "Invalid signature"

**Cause:** Signature verification failed

**Check:**
1. Razorpay key secret is correct
2. Payment details are not tampered
3. Server time is synchronized (NTP)

---

## 📊 Database Schema

### Plans Collection

```json
{
  "id": "uuid",
  "name": "Starter",
  "type": "starter",
  "price": 499,
  "credits_limit": 1000,
  "razorpay_plan_id_inr": "plan_XXXXX",
  "is_recurring": true,
  "features": [...],
  "is_active": true,
  "created_at": "2025-01-01T00:00:00Z"
}
```

### Payments Collection

```json
{
  "id": "uuid",
  "user_id": "user-uuid",
  "plan_id": "plan-uuid",
  "razorpay_order_id": "order_XXXXX",
  "razorpay_payment_id": "pay_XXXXX",
  "razorpay_signature": "signature_XXXXX",
  "amount": 49900,
  "currency": "INR",
  "status": "success",
  "payment_method": "card",
  "created_at": "2025-01-01T00:00:00Z",
  "updated_at": "2025-01-01T00:00:00Z"
}
```

---

## 🔗 Useful Links

- **Razorpay Documentation:** https://razorpay.com/docs/
- **Test Cards:** https://razorpay.com/docs/payments/payments/test-card-details/
- **Webhook Guide:** https://razorpay.com/docs/webhooks/
- **API Reference:** https://razorpay.com/docs/api/

---

## 📞 Support

For issues:

1. Check backend logs: `tail -f /var/log/supervisor/backend.err.log`
2. Check payment logs in Admin Dashboard
3. Check Razorpay dashboard for payment status
4. Contact Razorpay support for payment-specific issues

---

**Last Updated:** December 16, 2025  
**Version:** 1.0
