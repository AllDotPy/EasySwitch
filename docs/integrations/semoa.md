# Semoa Integration with EasySwitch

## Overview

[Semoa](https://semoa-payments.com) is a payment aggregator serving West Africa (UEMOA zone). It provides a direct API model for mobile money payments. EasySwitch wraps the Semoa API with automatic authentication (token retrieval) behind a unified interface.

## Prerequisites

- EasySwitch installed (see [Installation](../getting-started/installation.md))
- A Semoa merchant account with API credentials
- Your **API key**, **Client ID**, **Client Secret**, **Username**, and **Password**

## Supported Features

| Feature | Semoa Support |
|---------|--------------|
| **Payment** | ✅ via `send_payment()` |
| **Transaction Status** | ✅ via `check_status()` |
| **Transaction Details** | ⚠️ via `get_transaction_detail()` (falls back to status data) |
| **Cancellation** | ✅ via `cancel_transaction()` |
| **Refunds** | ❌ Not supported |
| **Webhook Validation** | ⚠️ Basic validation (enhance with your own signature logic) |

## Supported Currencies

| Currency | Code | Min | Max |
|----------|------|-----|-----|
| CFA Franc (BCEAO) | `XOF` | 100.00 | 1,000,000 |
| CFA Franc (BEAC) | `XAF` | 100.00 | 1,000,000 |
| Euro | `EUR` | 1.00 | 10,000 |
| US Dollar | `USD` | 1.00 | 10,000 |

## Setup

### Minimal Configuration

```python
from easyswitch import EasySwitch, Provider

config = {
    "providers": {
        "SEMOA": {
            "api_key": "your_semoa_api_key",
            "callback_url": "https://your-site.com/webhook/semoa",
            "environment": "sandbox",
            "extra": {
                "client_id": "your_client_id",
                "client_secret": "your_client_secret",
                "username": "your_username",
                "password": "your_password",
            }
        }
    },
    "default_provider": "SEMOA",
}

client = EasySwitch.from_dict(config)
```

> **Important**: The SDK automatically authenticates on first request. No manual token handling is needed.

### Environment Variables (.env)

```ini
EASYSWITCH_ENABLED_PROVIDERS=semoa
EASYSWITCH_DEFAULT_PROVIDER=semoa
EASYSWITCH_SEMOA_API_KEY=your_semoa_api_key
EASYSWITCH_SEMOA_X_CLIENT_ID=your_client_id
EASYSWITCH_SEMOA_X_CLIENT_SECRET=your_client_secret
EASYSWITCH_SEMOA_X_USERNAME=your_username
EASYSWITCH_SEMOA_X_PASSWORD=your_password
EASYSWITCH_SEMOA_CALLBACK_URL=https://your-site.com/webhook/semoa
EASYSWITCH_SEMOA_ENVIRONMENT=sandbox
```

```python
client = EasySwitch.from_env()
```

## API Methods

### 1. Send Payment

Semoa uses a **direct API model**: calling `send_payment()` sends the payment request and returns a payment link if available.

```python
from easyswitch import (
    TransactionDetail, Currency, TransactionStatus,
    TransactionType, CustomerInfo
)

transaction = TransactionDetail(
    transaction_id="order-20240704-001",
    amount=5000.00,
    currency=Currency.XOF,
    customer=CustomerInfo(
        phone_number="+22890123456",
        first_name="John",
        last_name="Doe",
    ),
    reason="Payment for invoice INV-2024-07",
    callback_url="https://your-site.com/webhook/semoa",
)

response = client.send_payment(transaction)

print(f"Transaction ID: {response.transaction_id}")
print(f"Payment URL: {response.payment_link}")
print(f"Status: {response.status}")
```

### 2. Check Transaction Status

```python
status_response = client.check_status("order-20240704-001")

print(f"Status: {status_response.status}")
print(f"Amount: {status_response.amount}")

if status_response.status == TransactionStatus.SUCCESSFUL:
    print("Payment completed!")
elif status_response.status == TransactionStatus.FAILED:
    print("Payment failed")
```

### 3. Cancel a Transaction

Semoa supports transaction cancellation via the API:

```python
cancelled = client.cancel_transaction("order-20240704-001")

if cancelled:
    print("Transaction successfully cancelled")
else:
    print("Cancellation failed")
```

### 4. Get Transaction Details

```python
detail = client.get_transaction_detail("order-20240704-001")
print(f"Amount: {detail.amount}")
print(f"Status: {detail.status}")
```

## Webhook Management

Semoa's webhook signature verification is not fully documented. EasySwitch provides a pass-through validation that accepts all webhooks. For production, implement custom signature verification.

```python
from flask import Flask, request, jsonify

app = Flask(__name__)
client = EasySwitch.from_env()

@app.route("/webhook/semoa", methods=["POST"])
def semoa_webhook():
    payload = request.get_json()
    headers = dict(request.headers)

    event = client.parse_webhook(
        payload=payload,
        headers=headers,
    )

    if event.status == TransactionStatus.SUCCESSFUL:
        print(f"Payment {event.transaction_id} confirmed")
        # Fulfill order…

    return jsonify({"status": "ok"}), 200
```

### Status Mapping

| Semoa Status | EasySwitch Status | Meaning |
|-------------|-------------------|---------|
| `PENDING` | `PENDING` | Awaiting processing |
| `SUCCESSFUL` / `SUCCESS` | `SUCCESSFUL` | Payment completed |
| `FAILED` / `FAIL` | `FAILED` | Payment failed |
| `CANCELLED` / `CANCEL` | `CANCELLED` | Cancelled |
| `EXPIRED` | `EXPIRED` | Payment expired |
| `ERROR` | `ERROR` | Technical error |

## Complete Example

```python
from easyswitch import (
    EasySwitch, TransactionDetail, Currency,
    TransactionStatus, CustomerInfo,
)
from easyswitch.exceptions import PaymentError

client = EasySwitch.from_env()

tx = TransactionDetail(
    transaction_id="demo-001",
    amount=3500.00,
    currency=Currency.XOF,
    customer=CustomerInfo(
        phone_number="+22890123456",
        first_name="Demo",
        last_name="User",
    ),
    reason="Test payment via Semoa",
)

try:
    response = client.send_payment(tx)
    print(f"Payment sent. Status: {response.status}")

    # Check status after a few seconds
    status = client.check_status(response.transaction_id)
    print(f"Final status: {status.status}")

except PaymentError as e:
    print(f"Error: {e}")
```

## Limitations

- **No refunds**: Semoa does not support API refunds.
- **Authentication**: Requires multiple credential fields (username, password, client_id, client_secret, api_key) — ensure all are configured correctly.
- **Production URL**: Verify the production URL with Semoa support (the current default may be sandbox-only).
