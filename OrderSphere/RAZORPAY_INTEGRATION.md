# 🚀 Razorpay Integration Guide - OrderSphere

## ✅ Integration Complete

Razorpay payment gateway has been successfully integrated into OrderSphere with **zero breaking changes** to existing functionality.

---

## 📋 What's New

### Features Added
- ✅ **Razorpay Checkout Widget** - Professional payment popup
- ✅ **Secure Payment Verification** - HMAC SHA256 signature validation
- ✅ **Order Status Tracking** - Payment status tracked (PENDING/PAID/FAILED)
- ✅ **User Notifications** - Real-time payment success alerts
- ✅ **Backward Compatible** - COD, UPI, Card methods still work

### Files Modified
1. **app.py** - Added payment API endpoints
2. **requirements.txt** - Added razorpay package
3. **setup_db.sql** - Added payment columns to orders table
4. **templates/checkout.html** - Integrated Razorpay payment flow

### Files Created
1. **migrate_payment_schema.sql** - Migration script for existing databases

---

## 🔧 Installation & Setup

### Step 1: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 2: Database Migration

**For Fresh Installation:**
```bash
mysql -u root -p < setup_db.sql
```

**For Existing Installation:**
```bash
mysql -u root -p ordersphere_db < migrate_payment_schema.sql
```

### Step 3: Environment Variables (Already Configured)

Your `.env` file already contains:
```env
RAZORPAY_KEY_ID=rzp_test_SjjftNWus3tlIp
RAZORPAY_KEY_SECRET=b8BuDH3pcCfyzYijVeVrOgFa
```

> ⚠️ **Production Note**: Replace test keys with live keys from [Razorpay Dashboard](https://dashboard.razorpay.com/app/settings/api-keys)

### Step 4: Restart Flask Application
```bash
python app.py
```

---

## 💳 Payment Flow

### User Journey
1. **Browse & Add to Cart** - Select products
2. **Proceed to Checkout** - Click "Checkout" or "Buy Now"
3. **Select Payment Method** - Choose "Razorpay"
4. **Enter Details** - Address, notes, etc.
5. **Click "Place Order"** - Order created in PENDING state
6. **Razorpay Popup Opens** - Secure payment window
7. **Complete Payment** - Enter card/UPI/wallet details
8. **Verification** - Backend verifies signature
9. **Success** - Order marked PAID, user redirected

### Backend Flow
```
POST /checkout (submit form)
  ↓
Create Order (status: PENDING)
  ↓
POST /api/create-payment
  ↓
Backend creates Razorpay order
  ↓
Return order_id + key to frontend
  ↓
Frontend opens Razorpay popup
  ↓
User completes payment
  ↓
POST /api/verify-payment (signature + payment_id)
  ↓
Backend verifies HMAC-SHA256
  ↓
UPDATE orders SET payment_status='PAID', payment_id=...
  ↓
Log transaction
  ↓
Notify user
```

---

## 🔐 Security Features

### Signature Verification
- **HMAC SHA256** signature validation ensures payment authenticity
- Prevents tampered payment data
- Verified on secure backend, never trusts frontend

### Key Management
- `RAZORPAY_KEY_SECRET` never exposed to frontend
- Only `RAZORPAY_KEY_ID` sent to browser (for Razorpay SDK)
- .env file excluded from version control

### Order Validation
- Orders verified to belong to logged-in user
- Payment can only update matching order
- Transaction logging for audit trails

---

## 📊 Database Schema Changes

### Orders Table Updates
```sql
-- New columns added:
payment_status VARCHAR(20) DEFAULT 'PENDING'   -- PENDING, PAID, FAILED
payment_id VARCHAR(100)                        -- Razorpay payment ID
razorpay_order_id VARCHAR(100)                 -- Razorpay order ID

-- New indexes:
CREATE INDEX idx_orders_payment_status ON orders(payment_status);
CREATE INDEX idx_orders_payment_id ON orders(payment_id);
```

---

## 🧪 Testing Payment Flow

### Using Razorpay Test Keys (Included)

**Test Credentials Available:**
- Key ID: `rzp_test_SjjftNWus3tlIp`
- Key Secret: `b8BuDH3pcCfyzYijVeVrOgFa`

**Test Cards for Razorpay:**
| Card Number | Expiry | CVV | Status |
|---|---|---|---|
| 4111111111111111 | Any Future | Any 3 digits | Success |
| 4111111111111113 | Any Future | Any 3 digits | Failure |

### Test Steps
1. Go to checkout page
2. Select any product, add to cart
3. Proceed to checkout
4. Select "Razorpay" payment method
5. Click "Place Order"
6. Use test card `4111111111111111`
7. Verify order status updates to PAID

---

## 📱 API Endpoints

### POST /api/create-payment
**Purpose**: Create Razorpay order

**Request**:
```json
{
  "order_id": 123,
  "amount": 999.99
}
```

**Response**:
```json
{
  "order_id": "order_1234567890abcd",
  "amount": 99999,
  "key": "rzp_test_SjjftNWus3tlIp"
}
```

### POST /api/verify-payment
**Purpose**: Verify payment signature and update order

**Request**:
```json
{
  "razorpay_order_id": "order_1234567890abcd",
  "razorpay_payment_id": "pay_1234567890abcd",
  "razorpay_signature": "9ef4dffbfd84f1318f6739..."
}
```

**Response** (Success):
```json
{
  "status": "success",
  "message": "Payment verified"
}
```

---

## 🚨 Error Handling

### Common Scenarios

**Payment Cancelled by User**
- Modal closes
- Order remains PENDING
- User can retry payment

**Network Failure During Verification**
- Frontend shows error
- Backend verifies signature when possible
- Order status can be checked manually

**Invalid Signature**
- Returns 400 error
- Order NOT updated to PAID
- Payment attempt logged

---

## 📈 Monitoring & Debugging

### Check Payment Status
```sql
SELECT order_id, payment_status, payment_id, razorpay_order_id 
FROM orders 
WHERE payment_status='PAID' 
ORDER BY ordered_at DESC;
```

### View Failed Payments
```sql
SELECT order_id, payment_status, razorpay_order_id 
FROM orders 
WHERE payment_status='PENDING' 
AND ordered_at < DATE_SUB(NOW(), INTERVAL 1 HOUR);
```

### Application Logs
Check terminal/console output for:
- `Error creating payment: ...` - Payment creation issues
- `Error verifying payment: ...` - Verification failures
- Signature validation errors

---

## 🔄 Upgrading to Production

### Before Going Live
1. ✅ Replace test keys with live Razorpay keys
2. ✅ Update `.env` file with live credentials
3. ✅ Test with actual payment methods
4. ✅ Set up email notifications
5. ✅ Enable HTTPS for payment pages
6. ✅ Test error scenarios
7. ✅ Set up monitoring/alerts
8. ✅ Update privacy policy with Razorpay terms

### Update .env for Production
```env
# Replace these with live keys from Razorpay Dashboard
RAZORPAY_KEY_ID=rzp_live_YOUR_LIVE_KEY_ID
RAZORPAY_KEY_SECRET=YOUR_LIVE_KEY_SECRET
```

---

## ❓ Troubleshooting

### Payment popup doesn't open
- Check browser console for errors
- Verify Razorpay script loads: `https://checkout.razorpay.com/v1/checkout.js`
- Check RAZORPAY_KEY_ID is valid

### "Payment failed" after successful checkout
- Verify RAZORPAY_KEY_SECRET is correct
- Check signature verification logic in `/api/verify-payment`
- Check server logs for HMAC errors

### Orders not updating to PAID
- Verify database connection is working
- Check order_id matches in database
- Verify user_id matches session

### Duplicate orders created
- Check if user refreshed/retried checkout
- Review order creation logs
- Consider adding request deduplication

---

## 📚 Additional Resources

- [Razorpay API Documentation](https://razorpay.com/docs/api/)
- [Razorpay Checkout SDK](https://razorpay.com/docs/checkout/web/)
- [Razorpay Test Credentials](https://razorpay.com/docs/payments/payment-gateway/test-mode/)
- [HMAC Signature Verification](https://razorpay.com/docs/api/payments/verify-payment-signature/)

---

## 🎯 Summary

- **Zero Breaking Changes** - Existing functionality preserved
- **Secure Implementation** - HMAC signature verification
- **User Friendly** - Checkout widget, real-time notifications
- **Production Ready** - Error handling, logging, monitoring
- **Easy to Extend** - Clean API endpoints, modular code

Ready to accept online payments! 🎉
