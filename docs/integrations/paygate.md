# PayGate Integration with EasySwitch

## Overview

[PayGate Global](https://paygateglobal.com) is the leading mobile money payment gateway in Togo, supporting Mixx By Yas (FLOOZ) and Moov (TMONEY). It provides both direct API payments and hosted payment links. EasySwitch wraps PayGate's API behind a unified interface.

## Prerequisites

- EasySwitch installed (see [Installation](../getting-started/installation.md))
- A PayGate merchant account (requires business registration)
- Your **API key** from the PayGate dashboard (available after account activation)

## Supported Features

| Feature | PayGate Support |
|---------|----------------|
| **Direct Payment** | ✅ via `direct_payment()` |
| **Payment Link** | ✅ via `send_payment()` |
| **Transaction Status** | ✅ via `check_status()` |
| **Transaction Details** | ⚠️ Falls back to `check_status()` |
| **Balance Check** | ✅ via `get_balance()` |
| **Refunds** | ❌ Not supported (manual via dashboard) |
| **Cancellation** | ❌ Not supported |
| **Webhook Validation** | ⚠️ Field presence check (no HMAC) |

## Supported Currencies

| Currency | Code | Min | Max |
|----------|------|-----|-----|
| CFA Franc (BCEAO) | `XOF` | 100.00 | 1,000,000 |

## Supported Networks

| Network | Country |
|---------|---------|
| **FLOOZ** (Mixx By Yas) | Togo |
| **TMONEY** (Moov) | Togo |

## Setup

### Minimal Configuration

```python
from easyswitch import EasySwitch, Provider

config = {
    "providers": {
        "PAYGATE": {
            "api_key": "your_paygate_api_key",
            "callback_url": "https://your-site.com/webhook/paygate",
            "environment": "production",      # PayGate does not have sandbox
        }
    },
    "default_provider": "PAYGATE",
}

client = EasySwitch.from_dict(config)
```

### Environment Variables (.env)

```ini
EASYSWITCH_ENABLED_PROVIDERS=paygate
EASYSWITCH_DEFAULT_PROVIDER=paygate
EASYSWITCH_PAYGATE_API_KEY=your_paygate_api_key
EASYSWITCH_PAYGATE_CALLBACK_URL=https://your-site.com/webhook/paygate
EASYSWITCH_PAYGATE_ENVIRONMENT=production
```

```python
client = EasySwitch.from_env()
```

## API Methods

### 1. Create Payment Link (send_payment)

Generate a payment URL that you redirect the customer to (hosted PayGate page):

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
    reason="Payment for order #1234",
    callback_url="https://your-site.com/webhook/paygate",
)

response = client.send_payment(transaction)

print(f"Payment link: {response.payment_link}")
```

### 2. Direct Payment (direct_payment)

Process a payment directly via API (no hosted page):

```python
response = client.direct_payment(transaction)

print(f"Transaction ID: {response.transaction_id}")
print(f"Reference: {response.reference}")
print(f"Status: {response.status}")
```

### 3. Check Transaction Status

```python
status_response = client.check_status("order-20240704-001")

print(f"Status: {status_response.status}")
print(f"Amount: {status_response.amount}")

if status_response.status == TransactionStatus.SUCCESSFUL:
    print("Payment completed!")
```

### 4. Check Balance

```python
balances = client.get_balance()
print(f"FLOOZ balance: {balances['flooz']}")
print(f"TMONEY balance: {balances['tmoney']}")
```

## Webhook Management

PayGate sends payment confirmation callbacks. EasySwitch validates that the required fields are present.

```python
from flask import Flask, request, jsonify

app = Flask(__name__)
client = EasySwitch.from_env()

@app.route("/webhook/paygate", methods=["POST"])
def paygate_webhook():
    payload = request.get_json()
    headers = dict(request.headers)

    event = client.parse_webhook(
        payload=payload,
        headers=headers,
    )

    if event.status == TransactionStatus.SUCCESSFUL:
        print(f"Payment {event.transaction_id} confirmed: {event.amount} XOF")
        # Fulfill order…

    return jsonify({"status": "ok"}), 200
```

### Status Mapping

| PayGate Code | EasySwitch Status | Meaning |
|-------------|-------------------|---------|
| `0` | `SUCCESSFUL` | Payment successful |
| `2` | `PENDING` | Invalid authentication token |
| `4` | `EXPIRED` | Invalid parameters |
| `6` | `CANCELLED` | Duplicate transaction detected |

## Complete Example

```python
from easyswitch import (
    EasySwitch, TransactionDetail, Currency,
    TransactionStatus, CustomerInfo,
)
from easyswitch.exceptions import PaymentError

client = EasySwitch.from_env()

tx = TransactionDetail(
    transaction_id="paygate-demo-001",
    amount=2500.00,
    currency=Currency.XOF,
    customer=CustomerInfo(
        phone_number="+22890123456",
        first_name="Demo",
        last_name="User",
    ),
    reason="Test payment via PayGate",
)

try:
    # Generate payment link
    response = client.send_payment(tx)
    print(f"Payment link: {response.payment_link}")

    # Later: verify status
    status = client.check_status(tx.transaction_id)
    print(f"Status: {status.status}")

except PaymentError as e:
    print(f"Error: {e}")
```

## Limitations

- **No sandbox**: PayGate does not provide a testing environment.
- **No refunds**: Refunds must be processed manually via the PayGate dashboard.
- **No cancellation**: Transactions cannot be cancelled via API.
- **Togo only**: PayGate only supports Togolese mobile money operators (FLOOZ, TMONEY).
- **XOF only**: Only CFA Franc is supported.
