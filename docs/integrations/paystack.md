# Paystack Integration with EasySwitch

## Overview

[Paystack](https://paystack.com) is a leading African payment gateway powered by Stripe, serving businesses in Nigeria, Ghana, and across the continent. It supports card payments, mobile money, USSD, bank transfer, and more. EasySwitch wraps Paystack's transaction initialization and verification APIs behind a unified interface.

## Prerequisites

- EasySwitch installed (see [Installation](../getting-started/installation.md))
- A Paystack account with your **secret key** (from the Paystack dashboard)
- Your secret key (starts with `sk_`) for API authentication

## Supported Features

| Feature | Paystack Support |
|---------|-----------------|
| **Payment Initialization** | ✅ via `send_payment()` |
| **Status Verification** | ✅ via `check_status()` |
| **Transaction Details** | ✅ via `get_transaction_detail()` |
| **Refunds** | ✅ Full & partial via `refund()` |
| **Cancellation** | ❌ Not supported (use refund for reversals) |
| **Webhook Validation** | ✅ HMAC-SHA512 signature |
| **Webhook Parsing** | ✅ Standardized `WebhookEvent` |

## Supported Currencies

| Currency | Code | Min | Max |
|----------|------|-----|-----|
| Nigerian Naira | `NGN` | 50.00 | 10,000,000 |
| Ghanaian Cedi | `GHS` | 0.10 | 10,000,000 |
| US Dollar | `USD` | 2.00 | 10,000,000 |

## Setup & Configuration

### Minimal Configuration

```python
from easyswitch import EasySwitch, Provider

config = {
    "providers": {
        Provider.PAYSTACK: {
            "api_key": "sk_live_your_paystack_secret_key",
            "callback_url": "https://your-site.com/webhook/paystack",
            "environment": "sandbox",  # or "production"
        }
    },
    "default_provider": Provider.PAYSTACK,
}

client = EasySwitch.from_dict(config)
```

### Environment Variables (.env)

```ini
EASYSWITCH_ENABLED_PROVIDERS=paystack
EASYSWITCH_DEFAULT_PROVIDER=paystack
EASYSWITCH_PAYSTACK_API_KEY=sk_live_your_paystack_secret_key
EASYSWITCH_PAYSTACK_CALLBACK_URL=https://your-site.com/webhook/paystack
EASYSWITCH_PAYSTACK_ENVIRONMENT=sandbox
```

```python
client = EasySwitch.from_env()
```

### JSON Configuration

```json
{
    "default_provider": "PAYSTACK",
    "providers": {
        "PAYSTACK": {
            "api_key": "sk_live_your_paystack_secret_key",
            "callback_url": "https://your-site.com/webhook/paystack",
            "environment": "sandbox"
        }
    }
}
```

```python
client = EasySwitch.from_json("config.json")
```

## API Methods

### 1. Initialize a Payment

Paystack payments are **two-step**: you first initialize a transaction (getting a payment link), then the customer completes payment on Paystack's checkout page.

```python
from easyswitch import (
    TransactionDetail, Currency, TransactionStatus,
    TransactionType, CustomerInfo, Provider
)

transaction = TransactionDetail(
    transaction_id="order-20240704-001",
    provider=Provider.PAYSTACK,
    amount=5000.00,        # Amount in major units (NGN)
    currency=Currency.NGN,
    customer=CustomerInfo(
        email="customer@example.com",   # Required by Paystack
        phone_number="+2348012345678",
        first_name="John",
        last_name="Doe",
    ),
    reason="Premium Plan Purchase",
    callback_url="https://your-site.com/webhook/paystack",
    metadata={"order_id": "ORD-12345"},
)

response = client.send_payment(transaction)

print(f"Paystack Transaction ID: {response.transaction_id}")
print(f"Payment Link (send to customer): {response.payment_link}")
print(f"Access Code: {response.transaction_token}")
print(f"Status: {response.status}")
```

**Response highlights:**
- `response.payment_link`: Redirect the customer to this URL
- `response.transaction_token`: Access code for the transaction
- `response.reference`: Paystack transaction reference (used for verification)

### 2. Verify Transaction Status

After the customer completes (or abandons) payment, verify the status:

```python
reference = "paystack_ref_123"  # From the payment response
status_response = client.check_status(reference)

print(f"Status: {status_response.status}")
print(f"Amount: {status_response.amount}")

if status_response.status == TransactionStatus.SUCCESSFUL:
    print("Payment completed — fulfill the order!")
elif status_response.status == TransactionStatus.FAILED:
    print("Payment failed")
elif status_response.status == TransactionStatus.PENDING:
    print("Payment still pending")
```

### 3. Get Transaction Details

Retrieve full transaction details from Paystack by transaction ID:

```python
detail = client.get_transaction_detail("paystack_tx_id")
print(f"Customer: {detail.customer.email}")
print(f"Reference: {detail.reference}")
print(f"Paid at: {detail.completed_at}")
```

### 4. Refund a Transaction

Paystack supports both full and partial refunds:

```python
# Full refund
refund_response = client.refund(transaction_id="paystack_ref_123")
print(f"Refund status: {refund_response.status}")

# Partial refund
partial_refund = client.refund(
    transaction_id="paystack_ref_123",
    amount=2500.00,  # Partial amount
    reason="Customer requested partial refund",
)
```

### 5. Cancellation

```python
# Paystack does not support API cancellation
try:
    client.cancel_transaction("tx_ref")
except UnsupportedOperationError as e:
    print(f"Cancellation not supported: {e}")
    # Use refund instead
```

## Webhook Management

Paystack sends webhooks for transaction events. EasySwitch validates them using HMAC-SHA512.

### Webhook Endpoint

```python
from flask import Flask, request, jsonify

app = Flask(__name__)
client = EasySwitch.from_env()

@app.route("/webhook/paystack", methods=["POST"])
def paystack_webhook():
    payload = request.get_json()
    headers = dict(request.headers)

    # Parse & validate in one call (signature checked automatically)
    event = client.parse_webhook(
        payload=payload,
        headers=headers,
        provider=Provider.PAYSTACK,
    )

    # Handle event
    if event.event_type == "charge.success":
        print(f"Payment {event.transaction_id} succeeded: {event.amount} {event.currency}")
        # Fulfill order…

    return jsonify({"status": "ok"}), 200
```

### Status Mapping

| Paystack Status | EasySwitch Status | Meaning |
|----------------|-------------------|---------|
| `success` | `SUCCESSFUL` | Payment completed |
| `failed` | `FAILED` | Payment failed |
| `abandoned` | `CANCELLED` | Customer abandoned |
| `pending` | `PENDING` | Awaiting confirmation |
| `refund` | `REFUNDED` | Transaction refunded |

## Complete Example

```python
from easyswitch import (
    EasySwitch, Provider, TransactionDetail,
    Currency, TransactionStatus, CustomerInfo,
)
from easyswitch.exceptions import PaymentError

# 1. Initialize
client = EasySwitch.from_env()

# 2. Create transaction
tx = TransactionDetail(
    transaction_id="order-001",
    provider=Provider.PAYSTACK,
    amount=1500.00,
    currency=Currency.NGN,
    customer=CustomerInfo(
        email="buyer@example.com",
        phone_number="+2348012345678",
    ),
    reason="Digital Download",
)

try:
    # 3. Initialize payment
    response = client.send_payment(tx)
    print(f"Redirect customer to: {response.payment_link}")

    # 4. Later — verify
    status_response = client.check_status(response.reference)
    if status_response.status == TransactionStatus.SUCCESSFUL:
        print("Deliver product to customer")
    elif status_response.status == TransactionStatus.FAILED:
        print("Payment failed — notify customer")

except PaymentError as e:
    print(f"Payment error: {e}")
```

## Limitations

- **No cancellation**: Paystack does not allow cancelling a transaction via API. Use refund for post-payment reversals.
- **Requires checkout page**: Payments must be completed on Paystack's hosted page (not inline/headless).
- **Initialization-only**: `send_payment()` only initialises; actual payment happens on Paystack's side.
