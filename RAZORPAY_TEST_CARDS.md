# 💳 Razorpay Test Cards Guide

## Issue: "International cards are not supported"

This error appears in Razorpay test mode when:
1. Using actual credit/debit cards
2. Using international test cards
3. International payments not enabled in test account

---

## ✅ Solution: Use Indian Test Cards

### Successful Payment Test Cards

#### Visa (Domestic India)
```
Card Number: 4111 1111 1111 1111
CVV: 123
Expiry: 12/25 (any future date)
Name: Test User
OTP: Any 6 digits (e.g., 123456)
```

#### Mastercard (Domestic India)
```
Card Number: 5555 5555 5555 4444
CVV: 123
Expiry: 12/25 (any future date)
Name: Test User
OTP: Any 6 digits
```

#### RuPay
```
Card Number: 6521 5489 4894 8933
CVV: 123
Expiry: 12/25 (any future date)
Name: Test User
OTP: Any 6 digits
```

### Failed Payment Test Cards

#### Payment Declined
```
Card Number: 4111 1111 1111 1112
CVV: 123
Expiry: 12/25
```

#### Insufficient Funds
```
Card Number: 5555 5555 5555 5557
CVV: 123
Expiry: 12/25
```

---

## 🌍 Enable International Cards (Optional)

If you need to test international cards:

### Step 1: Login to Razorpay Dashboard
- Go to: https://dashboard.razorpay.com/
- Login with your test account

### Step 2: Enable International Cards
1. Navigate to **Settings** → **Payment Methods**
2. Find **Credit/Debit Cards** section
3. Toggle **International Cards** to ON
4. Save changes

### Step 3: International Test Cards (After enabling)

**Visa International:**
```
Card Number: 4012 8888 8888 1881
CVV: 123
Expiry: 12/25
OTP: Any 6 digits
```

**Mastercard International:**
```
Card Number: 5200 8282 8282 8210
CVV: 123
Expiry: 12/25
OTP: Any 6 digits
```

---

## 🧪 Testing Payment Flow

### Complete Test Scenario

1. **Login to MailGuard**
   - Email: sharinara68@gmail.com
   - Password: (your password)

2. **Go to Pricing Page**
   - Navigate to: https://payment-debug-14.preview.emergentagent.com/pricing

3. **Select a Plan**
   - Click "Subscribe Now" on Starter/Professional/Enterprise

4. **Enter Test Card**
   - Use: `4111 1111 1111 1111` (Visa India)
   - CVV: `123`
   - Expiry: `12/25`
   - Name: `Test User`

5. **Complete OTP**
   - Enter any 6 digits: `123456`

6. **Verify Success**
   - Should redirect to Dashboard
   - Credits should be added
   - Payment appears in history

---

## 🚫 Common Errors & Solutions

### Error 1: "International cards are not supported"

**Cause:** Using international card or real card in test mode

**Solution:** Use Indian test cards listed above
```
Card: 4111 1111 1111 1111 (Visa India)
```

### Error 2: "Your card has been declined"

**Cause:** Using decline test card or network issue

**Solution:** 
1. Use success test card: `4111 1111 1111 1111`
2. Ensure correct CVV and expiry
3. Try again after 1 minute

### Error 3: "Card number is invalid"

**Cause:** Wrong card number format

**Solution:** Double-check the card number:
- No spaces while typing
- All 16 digits correct
- Use copy-paste to avoid typos

### Error 4: "Payment cancelled by user"

**Cause:** Clicked back or cancelled payment

**Solution:** 
- Click "Subscribe Now" again
- Complete the full payment flow

---

## 📋 Test Checklist

Use this to verify payment integration:

- [ ] **Successful Payment**
  - Card: 4111 1111 1111 1111
  - Payment completes successfully
  - Credits added to account
  - Payment shows in history
  - Invoice generated

- [ ] **Failed Payment**
  - Card: 4111 1111 1111 1112
  - Payment fails gracefully
  - No credits added
  - Error message shown
  - No invoice created

- [ ] **Cancelled Payment**
  - Start payment
  - Click back/cancel
  - No credits added
  - Can retry payment

- [ ] **Multiple Plans**
  - Test all 3 paid plans
  - Verify correct amounts
  - Verify correct credits

---

## 🔍 Verify Payment in Database

After successful payment, verify in database:

```bash
cd /app/backend && python3 << 'EOF'
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

async def check_payment(email):
    client = AsyncIOMotorClient('mongodb://localhost:27017')
    db = client['email_verifier_db']
    
    # Get user
    user = await db.users.find_one({"email": email})
    if not user:
        print("❌ User not found")
        return
    
    print(f"\n✅ User: {user['email']}")
    print(f"   Plan: {user.get('plan', 'free')}")
    print(f"   Credits Limit: {user.get('credits_limit', 0)}")
    print(f"   Credits Used: {user.get('credits_used', 0)}")
    print(f"   Available: {user.get('credits_limit', 0) - user.get('credits_used', 0)}")
    
    # Get payments
    payments = await db.payments.find({"user_id": user['id']}).sort("created_at", -1).to_list(5)
    
    if payments:
        print(f"\n✅ Recent Payments: {len(payments)}")
        for p in payments:
            print(f"\n   Payment ID: {p['id']}")
            print(f"   Amount: ₹{p['amount'] / 100}")
            print(f"   Status: {p['status']}")
            print(f"   Plan: {p.get('plan_id', 'N/A')}")
            print(f"   Date: {p.get('created_at', 'N/A')}")
    else:
        print("\n⚠️  No payments found")
    
    client.close()

asyncio.run(check_payment('sharinara68@gmail.com'))
EOF
```

---

## 💡 Pro Tips

### Tip 1: Copy Card Number Carefully
```
Correct: 4111111111111111 (no spaces)
Also accepts: 4111 1111 1111 1111 (with spaces)
```

### Tip 2: Any Future Expiry Works
```
Valid: 12/25, 01/26, 12/30
Invalid: 12/20 (past date)
```

### Tip 3: Any 3-digit CVV Works
```
Valid: 123, 999, 000
Just needs to be 3 digits
```

### Tip 4: OTP in Test Mode
```
Any 6 digits work: 123456, 000000, 999999
Razorpay doesn't validate OTP in test mode
```

### Tip 5: Test in Incognito/Private Window
- Clears browser cache issues
- Prevents authentication conflicts
- Fresh session

---

## 📱 Mobile Testing

### Browser Compatibility

**Desktop:**
- ✅ Chrome
- ✅ Firefox
- ✅ Safari
- ✅ Edge

**Mobile:**
- ✅ Chrome Mobile
- ✅ Safari iOS
- ✅ Samsung Internet

### Responsive Test Cards (Same as Desktop)
```
Card: 4111 1111 1111 1111
CVV: 123
Expiry: 12/25
OTP: 123456
```

---

## 🔐 Security Notes

### Test Mode vs Live Mode

**Test Mode (Current):**
- Uses test cards only
- No real money charged
- Test credentials: `rzp_test_*`
- For development and testing

**Live Mode (Production):**
- Uses real cards
- Real money charged
- Live credentials: `rzp_live_*`
- Requires KYC verification

### Never Use Real Cards in Test Mode
- ❌ Real credit/debit cards won't work
- ❌ Will show "payment failed" or decline
- ✅ Only test cards work in test mode

---

## 📞 Support

### Issue Not Resolved?

1. **Check Backend Logs:**
   ```bash
   tail -50 /var/log/supervisor/backend.err.log | grep -i razorpay
   ```

2. **Check Razorpay Dashboard:**
   - Login to https://dashboard.razorpay.com/
   - Check test payments
   - Check payment settings

3. **Verify Razorpay Keys:**
   ```bash
   cat /app/backend/.env | grep RAZORPAY
   ```

4. **Test API Directly:**
   ```bash
   # Get plans
   curl -s http://localhost:8001/api/plans | python3 -m json.tool
   ```

---

## 📚 Related Documentation

- **Full Razorpay Guide:** `/app/RAZORPAY_INTEGRATION_GUIDE.md`
- **Admin Plan Management:** `/app/SUPER_ADMIN_PLAN_MANAGEMENT_GUIDE.md`
- **Quick Reference:** `/app/QUICK_REFERENCE.md`

---

**Last Updated:** December 16, 2025  
**Test Mode:** Active  
**Test Keys:** rzp_test_RsCrbXGSd0FUz0
