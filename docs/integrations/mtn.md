# MTN Mobile Money Integration with EasySwitch

## Overview

[MTN Mobile Money (MoMo)](https://momodeveloper.mtn.com) is the mobile money service from MTN Group, available in 17 African countries. It enables businesses to collect payments via the MTN MoMo subscriber base. EasySwitch wraps the MTN MoMo API (Collection) behind a unified interface with automatic OAuth2 token management.

## Prerequisites

- EasySwitch installed (see [Installation](../getting-started/installation.md))
- An MTN MoMo developer account ([momodeveloper.mtn.com](https://momodeveloper.mtn.com))
- Your **subscription key** (`Ocp-Apim-Subscription-Key`)
- Your **API secret** and **App ID** from the MTN developer portal

## Supported Features

| Feature | MTN MoMo Support |
|---------|------------------|
| **Request to Pay** | ✅ via `send_payment()` |
| **Transaction Status** | ✅ via `check_status()` |
| **Transaction Details** | ✅ via `get_transaction_detail()` |
| **Refunds (Disbursement)** | ✅ via `refund()` |
| **Cancellation** | ❌ Not supported |
| **Webhook Validation** | ✅ HMAC-SHA256 signature |
| **OAuth2 Token Mgmt** | ✅ Automatic (refresh on expiry) |

## Supported Currencies

| Currency | Code | Min |
|----------|------|-----|
| CFA Franc (BCEAO) | `XOF` | 50.00 |
| CFA Franc (BEAC) | `XAF` | 50.00 |
| Ugandan Shilling | `UGX` | 500.00 |
| Tanzanian Shilling | `TZS` | 500.00 |
| Kenyan Shilling | `KES` | 10.00 |
| Rwandan Franc | `RWF` | 100.00 |
| Zambian Kwacha | `ZMW` | 1.00 |
| Malawian Kwacha | `MWK` | 100.00 |
| Burundian Franc | `BIF` | 100.00 |
| Ethiopian Birr | `ETB` | 1.00 |
| Botswanan Pula | `BWP` | 1.00 |
| Zimbabwean Dollar | `ZWL` | 1.00 |

## Setup & Configuration

### Minimal Configuration

```python
from easyswitch import EasySwitch, Provider

config = {
    "providers": {
        Provider.MTN: {
            "api_key": "your_subscription_key",
            "api_secret": "your_api_secret",
            "callback_url": "https://your-site.com/webhook/mtn",
            "environment": "sandbox",  # or "production"
            "extra": {
                "app_id": "your_mtn_app_id",
            }
        }
    },
    "default_provider": Provider.MTN,
}

client = EasySwitch.from_dict(config)
```

### Environment Variables (.env)

```ini
EASYSWITCH_ENABLED_PROVIDERS=mtn
EASYSWITCH_DEFAULT_PROVIDER=mtn
EASYSWITCH_MTN_API_KEY=your_subscription_key
EASYSWITCH_MTN_API_SECRET=your_api_secret
EASYSWITCH_MTN_X_APP_ID=your_mtn_app_id
EASYSWITCH_MTN_CALLBACK_URL=https://your-site.com/webhook/mtn
EASYSWITCH_MTN_ENVIRONMENT=sandbox
```

```python
client = EasySwitch.from_env()
```

## API Methods

### 1. Request to Pay

MTN uses an **asynchronous payment model**: you submit a request-to-pay, MTN sends a USSD push to the customer's phone, and the customer confirms on their device. The initial response is always `PENDING` — you must poll for the final status.

```python
from easyswitch import (
    TransactionDetail, Currency, TransactionStatus,
    TransactionType, CustomerInfo, Provider
)

transaction = TransactionDetail(
    transaction_id="pay-mtn-20240704-001",
    provider=Provider.MTN,
    amount=1500.00,
    currency=Currency.XOF,
    customer=CustomerInfo(
        phone_number="+22990123456",  # Subscriber MSISDN
        first_name="John",
        last_name="Doe",
    ),
    reason="Shopping cart payment",
    callback_url="https://your-site.com/webhook/mtn",
)

response = client.send_payment(transaction)

print(f"Transaction UUID: {response.transaction_id}")
print(f"Status: {response.status}")  # Always PENDING initially
print(f"Expires at: {response.expires_at}")

# Store transaction_id — you will need it to poll for status
```

> **Important**: MTN returns a `202 Accepted` immediately. The actual payment result is delivered asynchronously. You should either poll with `check_status()` or wait for a webhook callback.

### 2. Check Payment Status

Poll for the transaction result:

```python
tx_uuid = "uuid-from-send-payment"
status_response = client.check_status(tx_uuid)

print(f"Status: {status_response.status}")
print(f"Amount: {status_response.amount}")

if status_response.status == TransactionStatus.SUCCESSFUL:
    print("Customer confirmed payment!")
elif status_response.status == TransactionStatus.FAILED:
    print("Payment was rejected")
elif status_response.status == TransactionStatus.PENDING:
    print("Customer hasn't responded yet — try again later")
```

### 3. Refund (Disbursement)

Refund a successful payment. The SDK automatically checks that the original transaction was successful before proceeding.

```python
# Full refund
refund_response = client.refund(
    transaction_id="uuid-from-original-payment",
)
print(f"Refund status: {refund_response.status}")

# Partial refund
refund_response = client.refund(
    transaction_id="uuid-from-original-payment",
    amount=500.00,
    reason="Partial refund for damaged item",
)
```

### 4. Get Transaction Details

```python
detail = client.get_transaction_detail("uuid-from-original-payment")
print(f"Reference: {detail.reference}")
print(f"Status: {detail.status}")
```

## Webhook Management

MTN sends notifications via callback URL. EasySwitch validates them using the API secret.

### Webhook Endpoint

```python
from flask import Flask, request, jsonify

app = Flask(__name__)
client = EasySwitch.from_env()

@app.route("/webhook/mtn", methods=["POST"])
def mtn_webhook():
    payload = request.get_json()
    headers = dict(request.headers)

    # Parse & validate (signature checked automatically)
    event = client.parse_webhook(
        payload=payload,
        headers=headers,
        provider=Provider.MTN,
    )

    if event.status == TransactionStatus.SUCCESSFUL:
        print(f"Payment {event.transaction_id} confirmed!")
        # Fulfill order…

    return jsonify({"status": "ok"}), 200
```

### Status Mapping

| MTN Status | EasySwitch Status | Meaning |
|-----------|-------------------|---------|
| `pending` | `PENDING` | Awaiting customer response |
| `successful` | `SUCCESSFUL` | Customer confirmed payment |
| `failed` | `FAILED` | Payment rejected |
| `rejected` | `FAILED` | Payment rejected by operator |
| `cancelled` | `CANCELLED` | Customer cancelled |
| `ongoing` | `PROCESSING` | Transaction in progress |
| `timeout` | `EXPIRED` | Customer did not respond in time |

## Complete Example

```python
from easyswitch import (
    EasySwitch, Provider, TransactionDetail,
    Currency, TransactionStatus, CustomerInfo,
)
import time

client = EasySwitch.from_env()

# 1. Create and send payment
tx = TransactionDetail(
    transaction_id="pay-001",
    provider=Provider.MTN,
    amount=2500.00,
    currency=Currency.XOF,
    customer=CustomerInfo(phone_number="+22990123456"),
    reason="Order #1234",
)
response = client.send_payment(tx)
print(f"Sent payment request, UUID: {response.transaction_id}")

# 2. Poll for status (in production, use webhooks instead)
for attempt in range(5):
    time.sleep(5)
    status = client.check_status(response.transaction_id)
    if status.status != TransactionStatus.PENDING:
        break

if status.status == TransactionStatus.SUCCESSFUL:
    print("Payment received! ✅")
else:
    print(f"Final status: {status.status}")
```

## Limitations

- **Async only**: MTN MoMo is fully asynchronous — no synchronous payment confirmation.
- **Polling required**: You must either poll or use webhooks to get the final payment result.
- **No cancellation**: Transactions cannot be cancelled once submitted.
- **Callback URL required**: MTN strongly recommends a callback URL to receive payment notifications.
