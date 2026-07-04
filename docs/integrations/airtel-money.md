# Airtel Money Integration with EasySwitch

## Overview

[Airtel Money](https://www.airtel.africa/money) is the mobile money service from Airtel Africa, operating in 15+ African countries. It enables businesses to collect payments directly from Airtel subscribers via USSD push or app notification. EasySwitch wraps the Airtel Money API behind a unified interface.

## Prerequisites

- EasySwitch installed (see [Installation](../getting-started/installation.md))
- An Airtel Money merchant account with API access
- Your **API key**, **Client ID**, and **Client Secret**

## Supported Features

| Feature | Airtel Money Support |
|---------|---------------------|
| **Payment (Collections)** | ✅ via `send_payment()` |
| **Transaction Status** | ✅ via `check_status()` |
| **Transaction Details** | ✅ via `get_transaction_detail()` |
| **Refunds** | ✅ via `refund()` |
| **Cancellation** | ❌ Not supported |
| **Webhook Validation** | ✅ HMAC-SHA256 signature |

## Supported Currencies

Airtel Money supports local currencies across its operating countries. The adapter validates against the full `Currency` enum:

`XOF`, `XAF`, `NGN`, `GHS`, `UGX`, `TZS`, `KES`, `RWF`, `ZMW`, `MWK`, `BIF`, `ETB`, `BWP`, `ZWL`, `CDF`, `GNF`, `KMF`, `EUR`, `USD`

## Setup & Configuration

### Minimal Configuration

```python
from easyswitch import EasySwitch, Provider

config = {
    "providers": {
        Provider.AIRTEL_MONEY: {
            "api_key": "your_airtel_api_key",
            "api_secret": "your_airtel_api_secret",
            "callback_url": "https://your-site.com/webhook/airtel",
            "environment": "sandbox",  # or "production"
            "extra": {
                "client_id": "your_client_id",
                "client_secret": "your_client_secret",
            }
        }
    },
    "default_provider": Provider.AIRTEL_MONEY,
}

client = EasySwitch.from_dict(config)
```

### Environment Variables (.env)

```ini
EASYSWITCH_ENABLED_PROVIDERS=airtel_money
EASYSWITCH_DEFAULT_PROVIDER=airtel_money
EASYSWITCH_AIRTEL_MONEY_API_KEY=your_airtel_api_key
EASYSWITCH_AIRTEL_MONEY_API_SECRET=your_airtel_api_secret
EASYSWITCH_AIRTEL_MONEY_X_CLIENT_ID=your_client_id
EASYSWITCH_AIRTEL_MONEY_X_CLIENT_SECRET=your_client_secret
EASYSWITCH_AIRTEL_MONEY_CALLBACK_URL=https://your-site.com/webhook/airtel
EASYSWITCH_AIRTEL_MONEY_ENVIRONMENT=sandbox
```

```python
client = EasySwitch.from_env()
```

## API Methods

### 1. Send Payment

Airtel Money uses a **USSD push** model: the customer receives a prompt on their phone to confirm the payment.

```python
from easyswitch import (
    TransactionDetail, Currency, TransactionStatus,
    TransactionType, CustomerInfo, Provider
)

transaction = TransactionDetail(
    transaction_id="airtel-pay-20240704-001",
    provider=Provider.AIRTEL_MONEY,
    amount=2000.00,
    currency=Currency.XOF,
    customer=CustomerInfo(
        phone_number="+22990123456",
        first_name="John",
        last_name="Doe",
    ),
    reason="Online order payment",
    callback_url="https://your-site.com/webhook/airtel",
)

response = client.send_payment(transaction)

print(f"Transaction ID: {response.transaction_id}")
print(f"Status: {response.status}")
```

### 2. Check Payment Status

```python
status_response = client.check_status("airtel_transaction_id")

if status_response.status == TransactionStatus.SUCCESSFUL:
    print("Payment confirmed!")
elif status_response.status == TransactionStatus.FAILED:
    print("Payment failed")
```

### 3. Refund

```python
refund_response = client.refund(
    transaction_id="original_airtel_tx_id",
    amount=2000.00,
    reason="Customer returned product",
)
print(f"Refund status: {refund_response.status}")
```

## Webhook Management

### Webhook Endpoint

```python
from flask import Flask, request, jsonify

app = Flask(__name__)
client = EasySwitch.from_env()

@app.route("/webhook/airtel", methods=["POST"])
def airtel_webhook():
    payload = request.get_json()
    headers = dict(request.headers)

    event = client.parse_webhook(
        payload=payload,
        headers=headers,
        provider=Provider.AIRTEL_MONEY,
    )

    if event.status == TransactionStatus.SUCCESSFUL:
        print(f"Payment received: {event.amount} {event.currency}")

    return jsonify({"status": "ok"}), 200
```

### Status Mapping

| Airtel Code | EasySwitch Status | Meaning |
|------------|-------------------|---------|
| `ts` (Transaction Successful) | `SUCCESSFUL` | Payment completed |
| `tf` (Transaction Failed) | `FAILED` | Payment failed |
| `tp` (Transaction Pending) | `PENDING` | Awaiting confirmation |
| `ta` (Transaction Active) | `PROCESSING` | Processing in progress |
| `tn` (Transaction Not Found) | `UNKNOWN` | Invalid reference |
| `tr` (Transaction Reversed) | `REFUNDED` | Payment refunded |
| `tc` (Transaction Cancelled) | `CANCELLED` | Cancelled by user |

## Limitations

- **USSD push required**: Customer must have an Airtel Money wallet and respond to the USSD prompt.
- **No cancellation**: Transactions cannot be cancelled once initiated.
- **Sandbox access**: Requires approval from Airtel for production API keys.
