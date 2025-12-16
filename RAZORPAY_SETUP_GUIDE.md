# Razorpay Integration Setup Guide

## Current Status

✅ **Razorpay Integration: FULLY IMPLEMENTED**
- Payment order creation with rate limiting
- Payment verification with signature validation
- Webhook handler with security
- Refund management system
- Invoice generation (PDF)
- Fraud detection and analytics
- Admin dashboard for payment monitoring

## Test Mode Configuration

**Current Keys (Test Mode):**
```
RAZORPAY_KEY_ID="rzp_test_1DP5mmOlF5G5ag"
RAZORPAY_KEY_SECRET="thisissamplesecretkeyfortest123"
```

⚠️ **Note:** These are sample/test credentials. For actual payment processing, you need to:

### Option 1: Use Real Razorpay Test Keys (Recommended for Development)

1. **Create Razorpay Account:**
   - Go to https://razorpay.com
   - Sign up for a free account
   - Verify your email and phone

2. **Get Test API Keys:**
   - Login to Razorpay Dashboard
   - Go to Settings → API Keys
   - Click "Generate Test Key"
   - Copy your Test Key ID and Key Secret

3. **Update Configuration:**
   ```bash
   # Edit /app/backend/.env
   RAZORPAY_KEY_ID="rzp_test_YOUR_ACTUAL_TEST_KEY"
   RAZORPAY_KEY_SECRET="YOUR_ACTUAL_TEST_SECRET"
   ```

4. **Restart Backend:**
   ```bash
   sudo supervisorctl restart backend
   ```

### Option 2: Use Live Keys (For Production Only)

1. **Complete KYC:**
   - Submit business documents
   - Bank account details
   - GST/PAN information

2. **Activate Account:**
   - Wait for Razorpay approval
   - Account will be activated for live transactions

3. **Get Live API Keys:**
   - Go to Settings → API Keys
   - Generate Live Keys
   - **Keep these secure!**

4. **Update Configuration:**
   ```bash
   RAZORPAY_KEY_ID="rzp_live_YOUR_LIVE_KEY"
   RAZORPAY_KEY_SECRET="YOUR_LIVE_SECRET"
   ```

## Testing Payment Flow

### With Test Keys:

1. **Test Card Details** (Use these for testing):
   ```
   Card Number: 4111 1111 1111 1111
   Expiry: Any future date (e.g., 12/25)
   CVV: Any 3 digits (e.g., 123)
   Name: Any name
   ```

2. **Test UPI:**
   ```
   UPI ID: success@razorpay
   ```

3. **Test NetBanking:**
   - Select any bank
   - Will show success/failure options

### Payment Scenarios:

**Successful Payment:**
- Use card: 4111 1111 1111 1111
- Payment will be captured
- Credits will be added to user account
- Invoice will be generated

**Failed Payment:**
- Use card: 4000 0000 0000 0002
- Payment will fail
- No credits added
- Logged in security events

## Implemented Features

### 1. Payment Creation
- **Endpoint:** `POST /api/payments/create-order?plan_id={plan_id}`
- **Security:** Rate limited (5 requests/minute)
- **Features:**
  - Duplicate order prevention
  - Order expiry (10 minutes)
  - Amount validation
  - Payment logging

### 2. Payment Verification
- **Endpoint:** `POST /api/payments/verify`
- **Security:**
  - HMAC signature verification
  - Rate limited (10 requests/minute)
  - Amount validation
  - Idempotency checks
- **Features:**
  - Razorpay payment status check
  - Plan activation
  - Credit allocation
  - Transaction logging

### 3. Webhook Handler
- **Endpoint:** `POST /api/payments/webhook`
- **Security:**
  - Webhook signature verification
  - Amount validation
  - Event logging
- **Events Handled:**
  - payment.captured
  - payment.failed

### 4. Refund System
- **Endpoint:** `POST /api/admin/payments/refund`
- **Features:**
  - Full and partial refunds
  - Plan downgrade
  - Credit adjustment
  - Refund logging

### 5. Invoice Generation
- **Endpoint:** `POST /api/admin/payments/generate-invoice/{payment_id}`
- **Features:**
  - Professional PDF invoices
  - GST calculation (18%)
  - Auto-generation
  - Download capability

### 6. Admin Dashboard
- **Endpoint:** `GET /api/admin/payments/dashboard`
- **Metrics:**
  - Total revenue
  - Conversion rates
  - Top customers
  - Daily trends
  - Plan breakdown

### 7. Fraud Detection
- **Endpoint:** `GET /api/admin/payments/fraud-analysis`
- **Detection:**
  - High failure rate users
  - Rapid payment attempts
  - Amount anomalies
  - Card testing patterns

### 8. Security Monitoring
- **Endpoint:** `GET /api/admin/payments/security-events`
- **Tracked Events:**
  - Invalid signatures
  - Rate limit exceeded
  - Amount mismatches
  - Duplicate payments

## Production Checklist

Before going live:

- [ ] Replace test keys with live keys
- [ ] Configure webhook URL in Razorpay dashboard
- [ ] Set webhook secret in configuration
- [ ] Test payment flow end-to-end
- [ ] Verify webhook handling
- [ ] Test refund process
- [ ] Check invoice generation
- [ ] Review security logs
- [ ] Set up monitoring alerts
- [ ] Test fraud detection

## Webhook Configuration

### Setup in Razorpay Dashboard:

1. Go to Settings → Webhooks
2. Add webhook URL:
   ```
   https://auth-debug-35.preview.emergentagent.com/api/payments/webhook
   ```
3. Select events:
   - payment.captured
   - payment.failed
4. Copy webhook secret
5. Add to `.env`:
   ```
   RAZORPAY_WEBHOOK_SECRET="your_webhook_secret"
   ```

### Test Webhooks:

Use Razorpay's webhook testing tool in the dashboard to send test events.

## Security Features

### Built-in Protection:
1. **Rate Limiting:**
   - Order creation: 5 requests/minute
   - Verification: 10 requests/minute

2. **Signature Verification:**
   - Payment signature (HMAC SHA256)
   - Webhook signature

3. **Amount Validation:**
   - Matches plan price with 0.01 tolerance
   - Prevents overpayment/underpayment

4. **Idempotency:**
   - Prevents duplicate payment processing
   - Checks existing successful payments

5. **Security Logging:**
   - All events logged with severity
   - Audit trail maintained
   - Fraud detection alerts

## Troubleshooting

### Common Issues:

1. **"Payment service not configured"**
   - Razorpay keys missing in .env
   - Solution: Add keys and restart backend

2. **"Invalid signature"**
   - Wrong key secret
   - Solution: Verify keys match Razorpay dashboard

3. **"Order creation failed"**
   - Rate limit exceeded
   - Invalid plan ID
   - Razorpay API down
   - Solution: Check logs, verify plan exists

4. **"Payment verification failed"**
   - Invalid signature
   - Payment not captured
   - Amount mismatch
   - Solution: Check Razorpay dashboard for payment status

## Support

For Razorpay integration issues:
- Razorpay Docs: https://razorpay.com/docs
- Support: https://razorpay.com/support

For MailGuard issues:
- Check backend logs: `/var/log/supervisor/backend.err.log`
- Check payment logs in Admin Panel
- Review security events dashboard

## Current Configuration

**Backend .env location:** `/app/backend/.env`

**Required Variables:**
```env
RAZORPAY_KEY_ID=your_key_id
RAZORPAY_KEY_SECRET=your_key_secret
RAZORPAY_WEBHOOK_SECRET=your_webhook_secret (optional)
```

**After updating .env:**
```bash
sudo supervisorctl restart backend
```

The frontend will automatically use the keys from the backend API response.
