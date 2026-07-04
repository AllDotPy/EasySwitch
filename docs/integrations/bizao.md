# Bizao Integration with EasySwitch

## Overview

[Bizao](https://bizao.com) is a mobile money aggregation platform serving West & Central Africa. It supports multiple channels (web, USSD, TPE) and provides a unified API across mobile money operators in the region. EasySwitch wraps the Bizao API with automatic OAuth2 token management.

## Prerequisites

- EasySwitch installed (see [Installation](../getting-started/installation.md))
- A Bizao merchant account
- Your **API key**, **Client ID**, and **Client Secret** for both sandbox and production

## Supported Features

| Feature | Bizao Support |
|---------|--------------|
| **Payment** | ✅ via `send_payment()` (web, USSD, TPE channels) |
| **Transaction Status** | ✅ via `check_status()` |
| **Transaction Details** | ❌ Not supported |
| **Refunds** | ❌ Not supported |
| **Cancellation** | ❌ Not supported |
| **Webhook Validation** | ✅ HMAC-SHA256 (`X-Hub-Signature` header) |

## Supported Currencies

| Currency | Code |
|----------|------|
| CFA Franc (BCEAO) | `XOF` |
| CFA Franc (BEAC) | `XAF` |
| Congolese Franc | `CDF` |
| Guinean Franc | `GNF` |
| US Dollar | `USD` |

## Setup

Bizao uses **separate credentials for sandbox and production** environments. You must configure both.

### Minimal Configuration

```python
from easyswitch import EasySwitch, Provider

config = {
    "providers": {
        "BIZAO": {
            "api_key": "your_bizao_api_key",            # Used as bearer token after auth
            "callback_url": "https://your-site.com/webhook/bizao",
            "environment": "sandbox",                    # or "production"
            "extra": {
                # Sandbox credentials
                "dev_client_id": "your_dev_client_id",
                "dev_client_secret": "your_dev_client_secret",
                "dev_token_url": "https://your-dev-auth-url.com/token",
                # Production credentials
                "prod_client_id": "your_prod_client_id",
                "prod_client_secret": "your_prod_client_secret",
                "prod_token_url": "https://your-prod-auth-url.com/token",
                # Channel config
                "country-code": "CI",                    # ISO-3166 alpha-2
                "mno-name": "orange",                    # Mobile operator name
                "channel": "web",                        # "web" | "tpe" | "ussd"
                "lang": "fr",
                "cancel_url": "https://your-site.com/cancel",
            }
        }
    },
    "default_provider": "BIZAO",
}

client = EasySwitch.from_dict(config)
```

> **Note**: Bizao uses a two-step authentication. The SDK automatically obtains an OAuth2 access token on initialization using the environment-appropriate credentials.

### Environment Variables (.env)

```ini
EASYSWITCH_ENABLED_PROVIDERS=bizao
EASYSWITCH_DEFAULT_PROVIDER=bizao
EASYSWITCH_BIZAO_API_KEY=your_bizao_api_key

# Sandbox
EASYSWITCH_BIZAO_X_DEV_CLIENT_ID=your_dev_client_id
EASYSWITCH_BIZAO_X_DEV_CLIENT_SECRET=your_dev_client_secret
EASYSWITCH_BIZAO_X_DEV_TOKEN_URL=https://your-dev-auth-url.com/token

# Production
EASYSWITCH_BIZAO_X_PROD_CLIENT_ID=your_prod_client_id
EASYSWITCH_BIZAO_X_PROD_CLIENT_SECRET=your_prod_client_secret
EASYSWITCH_BIZAO_X_PROD_TOKEN_URL=https://your-prod-auth-url.com/token

# Channel
EASYSWITCH_BIZAO_X_COUNTRY_CODE=CI
EASYSWITCH_BIZAO_X_MNO_NAME=orange
EASYSWITCH_BIZAO_X_CHANNEL=web
EASYSWITCH_BIZAO_X_LANG=fr
EASYSWITCH_BIZAO_CALLBACK_URL=https://your-site.com/webhook/bizao
EASYSWITCH_BIZAO_ENVIRONMENT=sandbox
```

```python
client = EasySwitch.from_env()
```

## API Methods

### 1. Send Payment

Bizao supports three channels: **web** (redirect), **TPE** (payment terminal), and **USSD** (mobile prompt). The channel is set in the configuration.

```python
from easyswitch import (
    TransactionDetail, Currency, TransactionStatus,
    TransactionType, CustomerInfo
)

transaction = TransactionDetail(
    transaction_id="order-20240704-001",
    amount=2500.00,
    currency=Currency.XOF,
    customer=CustomerInfo(
        phone_number="+2250123456789",     # Required for TPE/USSD channels
        first_name="John",
        last_name="Doe",
    ),
    reason="Payment for goods",
    callback_url="https://your-site.com/webhook/bizao",
    return_url="https://your-site.com/success",
    reference="invoice-2024-07",
)

response = client.send_payment(transaction)

print(f"Transaction ID: {response.transaction_id}")
print(f"Status: {response.status}")

if response.payment_link:
    print(f"Web channel - redirect customer to: {response.payment_link}")
elif response.transaction_token:
    print(f"TPE/USSD channel - use token: {response.transaction_token}")
```

> The response varies by channel:
> - **Web**: `payment_link` contains the redirect URL
> - **TPE/USSD**: `transaction_token` contains the payment token, and `customer.phone_number` is used for the USSD push

### 2. Check Transaction Status

```python
status_response = client.check_status("order-20240704-001")

print(f"Status: {status_response.status}")
print(f"Amount: {status_response.amount}")

if status_response.status == TransactionStatus.SUCCESSFUL:
    print("Payment completed!")
```

## Webhook Management

Bizao signs webhooks with an HMAC-SHA256 signature sent in the `X-Hub-Signature` header.

```python
from flask import Flask, request, jsonify

app = Flask(__name__)
client = EasySwitch.from_env()

@app.route("/webhook/bizao", methods=["POST"])
def bizao_webhook():
    payload = request.get_json()
    headers = dict(request.headers)

    event = client.parse_webhook(
        payload=payload,
        headers=headers,
    )

    if event.status == TransactionStatus.SUCCESSFUL:
        print(f"Payment {event.transaction_id} confirmed!")
        # Fulfill order…

    return jsonify({"status": "ok"}), 200
```

### Status Mapping

| Bizao Status | EasySwitch Status | Meaning |
|-------------|-------------------|---------|
| `SUCCESSFUL` / `OK` | `SUCCESSFUL` | Payment completed |
| `PENDING` / `WAITING` | `PENDING` | Awaiting processing |
| `FAILURE` / `FAILED` / `FAIL` | `FAILED` | Payment failed |
| `CANCELLED` | `CANCELLED` | Cancelled |
| `ERROR` | `ERROR` | Technical error |
| `EXPIRED` | `EXPIRED` | Payment expired |

## Complete Example

```python
from easyswitch import (
    EasySwitch, TransactionDetail, Currency,
    TransactionStatus, CustomerInfo,
)
from easyswitch.exceptions import PaymentError

client = EasySwitch.from_env()

tx = TransactionDetail(
    transaction_id="bizao-demo-001",
    amount=1500.00,
    currency=Currency.XOF,
    customer=CustomerInfo(
        phone_number="+2250123456789",
        first_name="Demo",
        last_name="User",
    ),
    reason="Demo payment via Bizao",
    callback_url="https://your-site.com/webhook/bizao",
)

try:
    response = client.send_payment(tx)
    if response.payment_link:
        print(f"Redirect customer to: {response.payment_link}")
    print(f"Status: {response.status}")

    # Check status
    status = client.check_status(response.transaction_id)
    print(f"Final status: {status.status}")

except PaymentError as e:
    print(f"Payment error: {e}")
```

## Limitations

- **No refunds**: Bizao does not support API refunds — process manually.
- **No cancellation**: Transactions cannot be cancelled once initiated.
- **No transaction details**: `get_transaction_detail()` is not supported.
- **Channel-dependent**: The payment flow (web redirect vs USSD push) depends on your channel configuration. Ensure your `callback_url` and `cancel_url` are correctly set.
- **Separate sandbox/prod credentials**: You must configure both environments.
