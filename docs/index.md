# EasySwitch SDK Documentation

<p align="center">
  <strong>Unified Python SDK for Mobile Money & Payment Gateways across Africa</strong>
</p>

---

## What is EasySwitch?

EasySwitch is a **unified Python SDK** that standardises **8+ payment providers** behind a single, clean interface. Instead of learning and maintaining separate integrations for each provider, you write your payment logic **once** and switch providers with a single configuration change.

```python
from easyswitch import EasySwitch, Provider

# One client, any provider
client = EasySwitch.from_env()

# Same method works for every provider
response = client.send_payment(transaction)
```

---

## Quick Start

```python
from easyswitch import (
    EasySwitch, TransactionDetail, Currency,
    TransactionType, CustomerInfo, Provider,
)

# 1. Initialise from environment variables
client = EasySwitch.from_env()

# 2. Create a transaction
order = TransactionDetail(
    transaction_id="order-001",
    provider=Provider.CINETPAY,
    amount=1500.00,
    currency=Currency.XOF,
    customer=CustomerInfo(
        phone_number="+22890123456",
        first_name="John",
        last_name="Doe",
    ),
    reason="Test payment via EasySwitch",
)

# 3. Send payment
response = client.send_payment(order)

# 4. Check result
print(f"Status: {response.status}")
print(f"Payment link: {response.payment_link}")
```

---

## Provider Ecosystem

<div class="grid cards" markdown>

-   :material-credit-card-outline: __CinetPay__

    ---

    Checkout page, cards & Mobile Money  
    West Africa (UEMOA)

    [→ Guide](integrations/cinetpay.md)

-   :material-credit-card-outline: __PayGate__

    ---

    Direct API + Payment links  
    Togo (FLOOZ, TMONEY)

    [→ Guide](integrations/paygate.md)

-   :material-credit-card-outline: __FedaPay__

    ---

    Cards & Mobile Money  
    8+ African countries

    [→ Guide](integrations/fedapay.md)

-   :material-credit-card-outline: __Paystack__

    ---

    Cards, USSD, Bank Transfer  
    Nigeria, Ghana

    [→ Guide](integrations/paystack.md)

-   :material-cellphone: __MTN MoMo__

    ---

    USSD push (async)  
    17 African countries

    [→ Guide](integrations/mtn.md)

-   :material-cellphone: __Airtel Money__

    ---

    USSD push (async)  
    15+ African countries

    [→ Guide](integrations/airtel-money.md)

-   :material-credit-card-outline: __Semoa__

    ---

    API payments  
    West Africa

    [→ Guide](integrations/semoa.md)

-   :material-credit-card-outline: __Bizao__

    ---

    Web, USSD, TPE channels  
    West & Central Africa

    [→ Guide](integrations/bizao.md)

</div>

[→ Compare all providers](provider-matrix.md){ .md-button .md-button--primary }

---

## Core Concepts

### Unified Transaction Model

Every provider accepts and returns the same data types:

| Concept | EasySwitch Type | Description |
|---------|----------------|-------------|
| **Transaction** | `TransactionDetail` | What you send to request a payment |
| **Payment Result** | `PaymentResponse` | What you get back after sending |
| **Status Check** | `TransactionStatusResponse` | Status & amount after verification |
| **Webhook Event** | `WebhookEvent` | Normalised event from provider callbacks |
| **Customer** | `CustomerInfo` | Customer details (name, phone, email) |

### Configuration Sources

```python
# Dict (inline)
client = EasySwitch.from_dict({...})

# Environment / .env
client = EasySwitch.from_env()

# JSON file
client = EasySwitch.from_json("config.json")

# YAML file
client = EasySwitch.from_yaml("config.yaml")

# Multi-source (with overrides)
client = EasySwitch.from_multi_sources(
    env_file=".env",
    json_file="overrides.json",
)
```

### Common Operations

| Method | Purpose | Works With |
|--------|---------|------------|
| `send_payment(tx)` | Initiate a payment | All providers |
| `check_status(id)` | Check transaction status | All providers |
| `get_transaction_detail(id)` | Full transaction details | Paystack, FedaPay, MTN, Airtel |
| `refund(id, amount)` | Full or partial refund | Paystack, MTN, Airtel |
| `validate_webhook(payload, headers)` | Verify webhook signature | Most providers |
| `parse_webhook(payload, headers)` | Parse webhook into WebhookEvent | Most providers |

---

## Next Steps

| Step | Resource |
|------|----------|
| **Install the SDK** | [Installation Guide](getting-started/installation.md) |
| **Configure providers** | [Configuration Guide](getting-started/configuration.md) |
| **Pick a provider** | [Provider Feature Matrix](provider-matrix.md) |
| **Read provider guides** | [CinetPay](integrations/cinetpay.md) · [PayGate](integrations/paygate.md) · [FedaPay](integrations/fedapay.md) · [Paystack](integrations/paystack.md) · [MTN](integrations/mtn.md) · [Airtel](integrations/airtel-money.md) · [Semoa](integrations/semoa.md) · [Bizao](integrations/bizao.md) |
| **API reference** | [Shared Types](api-reference/shared-types.md) · [Config Types](api-reference/config-types.md) · [Exceptions](api-reference/exceptions.md) |
| **Contribute** | [Contributing Guide](contributing.md) |
