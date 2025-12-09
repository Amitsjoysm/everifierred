# Super Admin: Razorpay Plan Management Guide

## ✅ What's Implemented

### 1. Plan Management with Razorpay Linking

**Admin Panel → Plans Tab** now includes:

#### **Plan Creation Fields:**
- **Plan Name**: Display name (e.g., "Professional Monthly")
- **Plan Type**: Internal identifier (e.g., "professional")
- **Price (INR)**: Price in Indian Rupees
- **Price (USD)**: Price in US Dollars (for international)
- **Credits Limit**: Number of verifications included
- **Billing Cycle**: Monthly or Yearly dropdown
- **Is Recurring**: Checkbox for subscription vs one-time

#### **Razorpay Integration Fields:**
- **Razorpay Plan ID (INR)**: Link to Razorpay subscription plan for Indian customers
- **Razorpay Plan ID (USD)**: Link to Razorpay subscription plan for international customers

**Example Plan Setup:**

```
Plan Name: Professional Monthly
Type: professional
Price (INR): 1999
Price (USD): 24.99
Billing Cycle: Monthly
Is Recurring: ✓ (checked)
Razorpay Plan ID (INR): plan_abc123xyz (paste from Razorpay)
Razorpay Plan ID (USD): plan_def456uvw (paste from Razorpay)
Credits: 5000
```

---

### 2. How to Link Razorpay Plans

#### Step-by-Step:

1. **Create Plan in Razorpay First:**
   - Go to Razorpay Dashboard
   - Navigate to: Subscriptions → Plans
   - Click "+ Create Plan"
   - Fill details:
     ```
     Name: MailGuard Professional Monthly INR
     Amount: 1,999
     Currency: INR
     Period: Monthly
     ```
   - Save and **COPY the Plan ID** (e.g., `plan_abc123xyz`)

2. **Create/Edit Plan in MailGuard:**
   - Login as Super Admin
   - Go to Admin Panel → Plans
   - Click "Add Plan" or edit existing
   - Fill in basic details
   - Paste Razorpay Plan ID in appropriate field:
     - INR field for Indian plan
     - USD field for international plan
   - Save

3. **Repeat for All Combinations:**
   - Each pricing tier (Starter, Professional, Enterprise)
   - Each currency (INR, USD)
   - Each billing cycle (Monthly, Yearly)

---

### 3. Subscription Management

**Endpoints Available:**

#### **For Users:**
- `POST /api/subscriptions/create` - Create new subscription
- `GET /api/subscriptions/my-subscriptions` - View my subscriptions
- `POST /api/subscriptions/manage` - Pause/Resume/Cancel subscription

#### **For Admins:**
- `GET /api/subscriptions/admin/all` - View all subscriptions
- Filter by status: active, paused, cancelled, completed

**Features:**
- Auto-renewal handling
- Pause/Resume subscriptions
- Cancel subscriptions
- View billing history
- Track subscription status

---

### 4. Invoice Generation System

**Status:** ✅ FULLY WORKING

**Test Results:**
```
✅ Invoice generated successfully!
📄 Path: /app/backend/invoices/invoice_INV-202512-NT_123.pdf
📦 Size: 3,811 bytes
```

**Features:**
- Professional PDF invoices with company branding
- GST calculation (18% included)
- Itemized billing
- Invoice number format: `INV-YYYYMM-XXXXXX`
- Auto-generation on successful payment
- Manual generation via admin panel

**Admin Endpoints:**
- `POST /api/admin/payments/generate-invoice/{payment_id}` - Generate invoice
- `GET /api/admin/payments/download-invoice/{payment_id}` - Download PDF
- `GET /api/admin/payments/invoices` - List all invoices
- `POST /api/admin/payments/bulk-generate-invoices` - Generate for multiple payments

**Invoice Includes:**
- Company header and branding
- Invoice number and date
- Customer details (name, email, user ID)
- Payment details (payment ID, order ID, date, status)
- Itemized billing (plan name, type, credits)
- Subtotal, GST (18%), and total
- Terms and conditions
- Company contact information

---

## 📊 Recommended Plan Structure

### For India (INR):

**Starter Plans:**
```
1. Starter Monthly INR
   - Price: ₹499/month
   - Credits: 1,000/month
   - Razorpay Plan: plan_xxx_monthly_inr
   
2. Starter Yearly INR
   - Price: ₹4,990/year (₹416/month - save 17%)
   - Credits: 1,000/month
   - Razorpay Plan: plan_xxx_yearly_inr
```

**Professional Plans:**
```
3. Professional Monthly INR
   - Price: ₹1,999/month
   - Credits: 5,000/month
   - Razorpay Plan: plan_yyy_monthly_inr
   
4. Professional Yearly INR
   - Price: ₹19,990/year (₹1,666/month - save 17%)
   - Credits: 5,000/month
   - Razorpay Plan: plan_yyy_yearly_inr
```

**Enterprise Plans:**
```
5. Enterprise Monthly INR
   - Price: ₹7,999/month
   - Credits: 25,000/month
   - Razorpay Plan: plan_zzz_monthly_inr
   
6. Enterprise Yearly INR
   - Price: ₹79,990/year (₹6,666/month - save 17%)
   - Credits: 25,000/month
   - Razorpay Plan: plan_zzz_yearly_inr
```

### For International (USD):

**Starter Plans:**
```
7. Starter Monthly USD
   - Price: $6.99/month
   - Credits: 1,000/month
   - Razorpay Plan: plan_xxx_monthly_usd
   
8. Starter Yearly USD
   - Price: $69.99/year ($5.83/month - save 17%)
   - Credits: 1,000/month
   - Razorpay Plan: plan_xxx_yearly_usd
```

**Professional Plans:**
```
9. Professional Monthly USD
   - Price: $24.99/month
   - Credits: 5,000/month
   - Razorpay Plan: plan_yyy_monthly_usd
   
10. Professional Yearly USD
    - Price: $249.99/year ($20.83/month - save 17%)
    - Credits: 5,000/month
    - Razorpay Plan: plan_yyy_yearly_usd
```

**Enterprise Plans:**
```
11. Enterprise Monthly USD
    - Price: $99.99/month
    - Credits: 25,000/month
    - Razorpay Plan: plan_zzz_monthly_usd
    
12. Enterprise Yearly USD
    - Price: $999.99/year ($83.33/month - save 17%)
    - Credits: 25,000/month
    - Razorpay Plan: plan_zzz_yearly_usd
```

---

## 🧪 Testing Checklist

### Pre-Testing:
- [ ] All 12 Razorpay subscription plans created
- [ ] All plan IDs linked in MailGuard admin panel
- [ ] Webhook configured and secret added to .env
- [ ] Live keys verified in backend

### Payment Testing:
- [ ] Select plan with INR pricing
- [ ] Payment popup opens with Razorpay
- [ ] Complete payment (use small amount for testing)
- [ ] Verify subscription created in Razorpay dashboard
- [ ] Verify user plan updated in MailGuard
- [ ] Verify credits added correctly

### Invoice Testing:
- [ ] Payment successful
- [ ] Go to Admin Panel → Payments tab (TODO: need to add UI)
- [ ] Generate invoice for payment
- [ ] Download PDF invoice
- [ ] Verify invoice contains all details

### Subscription Management:
- [ ] View active subscriptions
- [ ] Pause subscription
- [ ] Resume subscription
- [ ] Cancel subscription
- [ ] Verify status updates in Razorpay

---

## 🚀 Current System Status

✅ **Completed:**
- Live Razorpay keys configured
- Multi-currency support (INR/USD)
- Billing cycle support (Monthly/Yearly)
- Plan model updated with all fields
- Admin UI for linking Razorpay plans
- Subscription management endpoints
- Invoice generation working (tested)

⏳ **Next Steps:**
1. Create 12 subscription plans in Razorpay dashboard
2. Link plan IDs in MailGuard admin panel
3. Configure webhook
4. Test subscription flow
5. Add subscription management UI (if needed)

---

## 📞 Support

If you encounter issues:
- Check backend logs: `/var/log/supervisor/backend.err.log`
- Check Razorpay dashboard for payment status
- Review security events in admin panel
- Check webhook logs in Razorpay

For Razorpay specific issues:
- Razorpay Docs: https://razorpay.com/docs/payments/subscriptions
- Razorpay Support: https://razorpay.com/support
