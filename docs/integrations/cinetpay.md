# CinetPay Integration with EasySwitch

## Overview

[CinetPay](https://cinetpay.com) is a leading mobile money payment aggregator in Francophone West & Central Africa. It supports mobile money operators across 8+ countries (UEMOA & CEMAC zones) and provides a hosted checkout page for quick integration. EasySwitch wraps the CinetPay API behind a unified interface.

## Prerequisites

- EasySwitch installed (see [Installation](../getting-started/installation.md))
- A CinetPay merchant account
- Your **API key**, **Site ID**, and **Secret key** from the CinetPay dashboard

## Supported Features

| Feature | CinetPay Support |
|---------|-----------------|
| **Payment (hosted checkout)** | ✅ via `send_payment()` |
| **Transaction Status** | ✅ via `check_status()` |
| **Transaction Details** | ❌ Not supported |
| **Refunds** | ❌ Not supported (manual via dashboard) |
| **Cancellation** | ❌ Not supported |
| **Webhook Validation** | ✅ HMAC-SHA256 via `x-token` header |

## Supported Currencies

| Currency | Code | Min | Max |
|----------|------|-----|-----|
| CFA Franc (BCEAO) | `XOF` | 100.00 | 1,000,000 |
| CFA Franc (BEAC) | `XAF` | 100.00 | 1,000,000 |
| Congolese Franc | `CDF` | 1,000.00 | 1,000,000 |
| Guinean Franc | `GNF` | 1,000.00 | 1,000,000 |
| US Dollar | `USD` | 1.00 | 10,000 |

## Setup

### Minimal Configuration

```python
from easyswitch import EasySwitch, Provider

config = {
    "providers": {
        "CINETPAY": {
            "api_key": "your_cinetpay_api_key",
            "callback_url": "https://your-site.com/webhook/cinetpay",
            "environment": "sandbox",  # or "production"
            "extra": {
                "site_id": "your_site_id",
                "secret": "your_secret_key",
                "channels": "ALL",          # "ALL" | "MOBILE_MONEY" | "CARD"
                "lang": "fr",               # "fr" | "en"
            }
        }
    },
    "default_provider": "CINETPAY",
}

client = EasySwitch.from_dict(config)
```

### Environment Variables (.env)

```ini
EASYSWITCH_ENABLED_PROVIDERS=cinetpay
EASYSWITCH_DEFAULT_PROVIDER=cinetpay
EASYSWITCH_CINETPAY_API_KEY=your_cinetpay_api_key
EASYSWITCH_CINETPAY_X_SITE_ID=your_cinetpay_site_id
EASYSWITCH_CINETPAY_X_SECRET=your_cinetpay_secret_key
EASYSWITCH_CINETPAY_CALLBACK_URL=https://your-site.com/webhook/cinetpay
EASYSWITCH_CINETPAY_X_CHANNELS=ALL
EASYSWITCH_CINETPAY_X_LANG=fr
EASYSWITCH_CINETPAY_ENVIRONMENT=sandbox
```

```python
client = EasySwitch.from_env()
```

## API Methods

### 1. Create Payment

CinetPay uses a **hosted checkout page**: `send_payment()` initialises a payment and returns a `payment_url` that you redirect the customer to.

```python
from easyswitch import (
    TransactionDetail, Currency, TransactionStatus,
    TransactionType, CustomerInfo
)

transaction = TransactionDetail(
    transaction_id="order-20240704-001",   # Must be unique per transaction
    amount=1500.00,
    currency=Currency.XOF,
    customer=CustomerInfo(
        phone_number="+22890123456",
        first_name="John",
        last_name="Doe",
        email="john@example.com",           # Optional but recommended
        city="Lomé",
        country="TG",
    ),
    reason="Payment for order #1234",
    callback_url="https://your-site.com/webhook/cinetpay",
    reference="invoice-2024-07",            # Optional: your invoice ref
)

response = client.send_payment(transaction)

print(f"Payment URL (redirect customer here): {response.payment_link}")
print(f"Transaction ID: {response.transaction_id}")
print(f"Status: {response.status}")
```

> The customer completes payment on CinetPay's hosted page. After success, CinetPay redirects back to your `callback_url` and sends a webhook.

### 2. Check Payment Status

```python
tx_id = "order-20240704-001"
status_response = client.check_status(tx_id)

print(f"Status: {status_response.status}")
print(f"Amount: {status_response.amount}")

if status_response.status == TransactionStatus.SUCCESSFUL:
    print("Payment confirmed — deliver goods!")
```

## Webhook Management

CinetPay signs webhooks with an HMAC-SHA256 token sent in the `x-token` header.

```python
from flask import Flask, request, jsonify

app = Flask(__name__)
client = EasySwitch.from_env()

@app.route("/webhook/cinetpay", methods=["POST"])
def cinetpay_webhook():
    payload = request.get_json()
    headers = dict(request.headers)

    # Parse & validate in one call (signature checked automatically)
    event = client.parse_webhook(
        payload=payload,
        headers=headers,
    )

    if event.status == TransactionStatus.SUCCESSFUL:
        print(f"Payment {event.transaction_id}: {event.amount} {event.currency} received!")
        # Fulfill order…

    return jsonify({"status": "ok"}), 200
```

### Status Mapping

| CinetPay Status | EasySwitch Status | Meaning |
|----------------|-------------------|---------|
| `SUCCESS` | `SUCCESSFUL` | Payment completed |
| `CREATED` / `PENDING` | `PENDING` | Awaiting validation |
| `WAITING_CUSTOMER_TO_VALIDATE` | `PENDING` | Waiting for customer |
| `PAYMENT_FAILED` | `FAILED` | Payment failed |
| `INSUFFICIENT_BALANCE` | `FAILED` | Insufficient funds |
| `TRANSACTION_CANCEL` | `CANCELLED` | Cancelled |
| `ABONNEMENT_OR_TRANSACTIONS_EXPIRED` | `EXPIRED` | Payment expired |
| `REFUSED` | `REFUSED` | Refused by operator |

## Complete Example

```python
from easyswitch import (
    EasySwitch, TransactionDetail, Currency,
    TransactionStatus, CustomerInfo,
)
from easyswitch.exceptions import PaymentError

client = EasySwitch.from_env()

tx = TransactionDetail(
    transaction_id="demo-order-001",
    amount=2500.00,
    currency=Currency.XOF,
    customer=CustomerInfo(
        phone_number="+22890123456",
        first_name="Demo",
        last_name="User",
    ),
    reason="Demo payment",
)

try:
    response = client.send_payment(tx)
    print(f"Redirect customer to: {response.payment_link}")
except PaymentError as e:
    print(f"Payment failed: {e}")
```

## Limitations

- **No refunds**: CinetPay does not support API refunds — process manually via dashboard.
- **No cancellation**: Transactions cannot be cancelled once initiated.
- **Hosted checkout only**: Payment must be completed on CinetPay's page (no inline/headless mode).
- **No transaction detail retrieval**: `get_transaction_detail()` raises `UnsupportedOperationError`.
