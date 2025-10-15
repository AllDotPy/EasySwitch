

<div align="center">

<h1>CinetPay Integration Guide</h1>
  
![CinetPay Integration](https://img.shields.io/badge/CinetPay-Integration-blue?style=for-the-badge&logo=paypal)
![EasySwitch](https://img.shields.io/badge/EasySwitch-SDK-green?style=for-the-badge)
![West Africa](https://img.shields.io/badge/West_Africa-Payments-orange?style=for-the-badge)

**Professional Mobile Money Integration for West African Markets**

*Streamline your payment processing with CinetPay through the EasySwitch SDK*

[![Documentation](https://img.shields.io/badge/docs-complete-brightgreen)](../api-reference/base-adapter.md)
[![Python](https://img.shields.io/badge/python-3.7+-blue)](https://python.org)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

</div>

---

## Overview

CinetPay is a comprehensive payment gateway that enables seamless mobile money transactions across West and Central Africa. As a leading payment service provider, CinetPay connects businesses to multiple mobile money operators, offering extensive coverage across diverse African markets and currencies. With its robust API and comprehensive mobile money network, CinetPay empowers businesses to accept payments from customers using various mobile wallets including Orange Money, MTN Mobile Money, Moov Money, and Wave.

**Why use CinetPay with EasySwitch?**

- **Wide Coverage**: Supports 10+ countries across West and Central Africa
- **Multiple Operators**: Integrates with all major mobile money providers
- **Multi-Currency**: Handles XOF, XAF, CDF, GNF, and USD
- **Flexible Channels**: Supports mobile payments with redirect-based flow
- **Real-time Processing**: Instant payment confirmation and webhook notifications
- **Secure Integration**: HMAC signature validation and comprehensive error handling

## Quick Start (5 Minutes)

For developers who want to get started immediately, ensure you have completed the [Installation](../getting-started/installation.md) steps, then:

```python
# 1. Install
pip install easyswitch

# 2. Configure (use your CinetPay credentials)
from easyswitch import EasySwitch, Provider

client = EasySwitch.from_env()  # Reads from .env file

# 3. Send a payment
from easyswitch import (
    TransactionDetail, Currency, CustomerInfo, 
    TransactionStatus, TransactionType
)

transaction = TransactionDetail(
    transaction_id="TXN-001",
    provider=Provider.CINETPAY,
    status=TransactionStatus.PENDING,
    amount=5000,  # 50.00 XOF (amount in minor units)
    currency=Currency.XOF,
    transaction_type=TransactionType.PAYMENT,
    customer=CustomerInfo(
        first_name="John",
        last_name="Doe",
        email="john@example.com",
        phone_number="+22507123456"  # E.164 format required
    ),
    reason="Test payment"
)

response = client.send_payment(transaction)
print(f"Payment URL: {response.payment_link}")
print(f"Status: {response.status}")
```

That's it! See [Complete Setup](#setup) for detailed configuration and advanced features.

## When to Use CinetPay

### Best For:
- Mobile money payments in West/Central Africa
- Multi-operator support (Orange, MTN, Moov, Wave)
- Multi-country operations (10+ countries)
- Redirect-based payment flows
- Real-time payment processing
- Cross-border transactions in Africa

### Not Ideal For:
- Automated refunds (manual process required via dashboard)
- Transaction cancellations (not supported by API)
- Card payments (CinetPay focuses on mobile money)
- Markets outside Africa
- Direct mobile money API without redirect

### Consider Alternatives If You Need:
- Automated refund processing
- Programmatic transaction cancellation
- Card payment processing
- Non-African markets
- USSD-based direct payments

## Prerequisites

Before integrating CinetPay with EasySwitch, ensure you have:

- EasySwitch library installed. For setup instructions, see [Installation](../getting-started/installation.md)
- A CinetPay merchant account (create one at [CinetPay Registration](https://app-new.cinetpay.com))
- Development and production API credentials from your CinetPay dashboard
- API key, Site ID, and Secret key for both environments
- Understanding of your target markets and supported mobile money operators

## Supported Countries & Operators

CinetPay supports mobile money transactions across multiple African countries:

| Country | Operators | Currency |
|---------|-----------|----------|
| Côte d'Ivoire | Orange Money, MTN Mobile Money, Moov Money, Wave | XOF |
| Senegal | Orange Money, Free Money, Wave | XOF |
| Mali | Orange Money, Moov Money | XOF |
| Burkina Faso | Orange Money, Moov Money | XOF |
| Niger | Orange Money, Airtel Money | XOF |
| Cameroon | Orange Money, MTN Mobile Money | XAF |
| Chad | Airtel Money, Tigo Cash | XAF |
| Central African Republic | Orange Money, Moov Money | XAF |
| Democratic Republic of Congo | Orange Money, Airtel Money, Vodacom M-Pesa | CDF |
| Guinea | Orange Money, MTN Mobile Money | GNF |

## Setup

### Getting Your CinetPay Credentials

**Step 1: Create CinetPay Account**
1. Visit [CinetPay Merchant Registration](https://app-new.cinetpay.com) to create your account
2. Choose "Merchant Account" for business use
3. Complete KYC verification process
4. Wait for account approval (usually 24-48 hours)

**Step 2: Access Your Dashboard**
1. Login to [CinetPay Merchant Portal](https://app-new.cinetpay.com)
2. Navigate to **Settings** → **API Integration**
3. Copy your credentials (keep them secure!)

### Environment Variables Setup

**Option 1: Using .env file (Recommended)**

Create a `.env` file in your project root:

```bash
# CinetPay Configuration
CINETPAY_API_KEY=cp_test_your_actual_api_key_here
CINETPAY_SITE_ID=123456
CINETPAY_SECRET=your_actual_secret_key_here
CINETPAY_CALLBACK_URL=https://yoursite.com/webhook/cinetpay
CINETPAY_ENVIRONMENT=sandbox

# Optional: Additional settings
CINETPAY_CHANNELS=MOBILE_MONEY
CINETPAY_LANG=fr
CINETPAY_CURRENCY=XOF
```

**Option 2: System Environment Variables**

```bash
# Linux/Mac
export CINETPAY_API_KEY="cp_test_your_api_key"
export CINETPAY_SITE_ID="123456"
export CINETPAY_SECRET="your_secret"
export CINETPAY_CALLBACK_URL="https://yoursite.com/webhook/cinetpay"
export CINETPAY_ENVIRONMENT="sandbox"

# Windows
set CINETPAY_API_KEY=cp_test_your_api_key
set CINETPAY_SITE_ID=123456
set CINETPAY_SECRET=your_secret
set CINETPAY_CALLBACK_URL=https://yoursite.com/webhook/cinetpay
set CINETPAY_ENVIRONMENT=sandbox
```

### Detailed Configuration Options

| Parameter      | Required | Type   | Description                                  | Sandbox Example                    | Production Example              |
|----------------|----------|--------|----------------------------------------------|------------------------------------|---------------------------------|
| `api_key`      | Yes      | string | Your CinetPay API authentication key         | `cp_test_abc123...`                | `cp_live_xyz789...`             |
| `site_id`      | Yes      | string | Unique identifier for your CinetPay site     | `"443626"`                         | `"123456"`                      |
| `secret`       | Yes      | string | Secret key for webhook signature validation  | `"MySecretKey123"`                 | `"ProdSecret456"`               |
| `callback_url` | Yes      | string | Your server endpoint for receiving webhooks  | `"https://test.mysite.com/webhook"` | `"https://mysite.com/webhook"`  |
| `environment`  | Yes      | string | Operating environment                        | `"sandbox"`                        | `"production"`                  |
| `channels`     | No       | string | Accepted payment methods                     | `"MOBILE_MONEY"`                   | `"MOBILE_MONEY,CARD"`           |
| `lang`         | No       | string | Payment page language                        | `"fr"` (French)                    | `"en"` (English)                |
| `currency`     | No       | string | Default currency for transactions            | `"XOF"`                            | `"XOF"`                         |

### Supported Payment Channels

| Channel       | Code            | Countries          | Description                   |
|---------------|-----------------|--------------------|-------------------------------|
| Mobile Money  | `MOBILE_MONEY`  | CI, SN, ML, BF, NE, CM, TD, CF, CD, GN | Orange Money, MTN, Moov, Wave |
| Bank Cards    | `CREDIT_CARD`   | Excludes GN, CD    | Visa, Mastercard, local bank cards (not available for GNF/CDF) |
| Wallet        | `WALLET`        | Various            | Electronic wallets |
| All Methods   | `ALL`           | All                | Let customer choose payment method |

### Multiple Initialization Methods

**Method 1: Environment-based (Recommended for production)**

```python
import os
from dotenv import load_dotenv
from easyswitch import EasySwitch

# Load .env file
load_dotenv()

# Initialize from environment variables
client = EasySwitch.from_env()
```

**Method 2: Dictionary-based (Good for development)**

```python
from easyswitch import EasySwitch, Provider

client = EasySwitch.from_dict({
    "providers": {
        Provider.CINETPAY: {
            "api_key": "cp_test_your_api_key",
            "callback_url": "https://yoursite.com/webhook/cinetpay",
            "environment": "sandbox",
            "extra": {
                "site_id": "443626",
                "secret": "MySecretKey123",
                "channels": "MOBILE_MONEY",
                "lang": "fr",
                "currency": "XOF"
            }
        }
    }
})
```

**Method 3: Configuration file-based**

Create `config.json`:
```json
{
    "providers": {
        "CINETPAY": {
            "api_key": "cp_test_your_api_key",
            "callback_url": "https://yoursite.com/webhook/cinetpay",
            "environment": "sandbox",
            "extra": {
                "site_id": "443626",
                "secret": "MySecretKey123",
                "channels": "MOBILE_MONEY",
                "lang": "fr"
            }
        }
    }
}
```

Load configuration:
```python
import json
from easyswitch import EasySwitch

with open('config.json', 'r') as f:
    config = json.load(f)

client = EasySwitch.from_dict(config)
```

### Environment-Specific Settings

**Sandbox (Development) Configuration:**
```python
sandbox_config = {
    "providers": {
        Provider.CINETPAY: {
            "api_key": "cp_test_your_sandbox_key",
            "callback_url": "https://your-dev-site.ngrok.io/webhook/cinetpay",
            "environment": "sandbox",
            "extra": {
                "site_id": "your_test_site_id",
                "secret": "your_test_secret",
                "channels": "MOBILE_MONEY",
                "lang": "fr"
            }
        }
    }
}
```

**Production Configuration:**
```python
production_config = {
    "providers": {
        Provider.CINETPAY: {
            "api_key": "cp_live_your_production_key",
            "callback_url": "https://yoursite.com/webhook/cinetpay",
            "environment": "production",
            "extra": {
                "site_id": "your_live_site_id",
                "secret": "your_production_secret",
                "channels": "MOBILE_MONEY,CARD",
                "lang": "fr"
            }
        }
    }
}
```

### Configuration Validation

Always validate your configuration before processing payments:

```python
def validate_cinetpay_config(client):
    """Validate CinetPay configuration"""
    try:
        config = client.config.providers[Provider.CINETPAY]
        
        # Check required fields
        required_fields = ['api_key', 'callback_url', 'environment']
        missing_fields = [field for field in required_fields if not getattr(config, field, None)]
        
        if missing_fields:
            raise ValueError(f"Missing required configuration: {missing_fields}")
        
        # Check extra fields
        extra = config.extra or {}
        required_extra = ['site_id', 'secret']
        missing_extra = [field for field in required_extra if not extra.get(field)]
        
        if missing_extra:
            raise ValueError(f"Missing required extra configuration: {missing_extra}")
        
        # Validate environment
        if config.environment not in ['sandbox', 'production']:
            raise ValueError("Environment must be 'sandbox' or 'production'")
        
        # Validate API key format
        if config.environment == 'sandbox' and not config.api_key.startswith('cp_test_'):
            print("Warning: Using non-test API key in sandbox environment")
        elif config.environment == 'production' and not config.api_key.startswith('cp_live_'):
            print("Warning: Using non-live API key in production environment")
        
        print("CinetPay configuration is valid")
        return True
        
    except Exception as e:
        print(f"Configuration validation failed: {e}")
        return False

# Usage
client = EasySwitch.from_env()
validate_cinetpay_config(client)
    }
})
```

---

## EasySwitch Methods

EasySwitch provides a unified interface for all payment operations:

### Core Methods

| Method | Description | Returns |
|--------|-------------|---------|
| `send_payment(transaction)` | Send a payment transaction | PaymentResponse |
| `check_status(transaction_id)` | Check transaction status | TransactionStatusResponse |
| `validate_webhook(payload, headers)` | Validate webhook signature | bool |
| `parse_webhook(payload, headers)` | Parse webhook into WebhookEvent | WebhookEvent |

> **Note**: `cancel_transaction()`, `refund()`, and `get_transaction_detail()` are not supported by CinetPay. See [CinetPay Limitations](#cinetpay-limitations) for alternatives.

### Configuration Methods

| Method | Description | Returns |
|--------|-------------|---------|
| `from_env(env_file)` | Initialize from environment variables | EasySwitch |
| `from_json(json_file)` | Initialize from JSON file | EasySwitch |
| `from_yaml(yaml_file)` | Initialize from YAML file | EasySwitch |
| `from_dict(config_dict)` | Initialize from Python dictionary | EasySwitch |
| `from_multi_sources(**sources)` | Initialize from multiple sources | EasySwitch |

## API Methods

### 1. Create Payment

Initiate a payment transaction using EasySwitch's `TransactionDetail` class and `send_payment` method.

```python
# Create a TransactionDetail object
transaction = TransactionDetail(
    transaction_id="TXN-123456",  # Unique ID generated by your system
    provider=Provider.CINETPAY,
    status=TransactionStatus.PENDING,
    amount=1000,  # Amount in minor units (1000 = 10.00 XOF)
    currency=Currency.XOF,
    transaction_type=TransactionType.PAYMENT,
    customer=CustomerInfo(
        first_name="Jean",
        last_name="Kouame",
        email="jean.kouame@email.com",
        phone_number="+22507123456"  # Must be in E.164 format
    ),
    reason="Product ABC Purchase",
    reference="REF-789012",  # Optional business reference
    callback_url="https://your-site.com/webhook/cinetpay",  # Override default
    return_url="https://your-site.com/success",         # Override default
    metadata={
        "order_id": "ORD-12345",   # Optional business identifier
        "customer_id": "CUST-567"  # Additional context
    }
)

# Send payment using EasySwitch
response = client.send_payment(transaction)

# Check response properties
print(f"Local Transaction ID: {transaction.transaction_id}")  # Your internal ID
print(f"CinetPay Payment Token: {response.transaction_token}")   # CinetPay's payment token
print(f"Payment URL: {response.payment_link}")              # Redirect URL
print(f"Status: {response.status}")
print(f"Is Successful: {response.is_successful}")
print(f"Is Pending: {response.is_pending}")
```

**Response Object (PaymentResponse):**

```python
PaymentResponse(
    transaction_id="TXN-123456",      # Your transaction ID (echoed back)
    provider=Provider.CINETPAY,
    status=TransactionStatus.PENDING,
    amount=1000,
    currency=Currency.XOF,
    payment_link="https://checkout.cinetpay.com/...",  # Redirect URL
    transaction_token="pay_token_abc123",           
    created_at=datetime(2024, 1, 15, 10, 30, 0),
    customer=CustomerInfo(...),
    raw_response={...}  # Raw CinetPay response
)
```

**Important Notes:**

- **Amount Format**: Always provide amounts in minor units (e.g., 1000 for 10.00 XOF)
- **Phone Format**: Phone numbers must be in E.164 format (+country_code + number)
- **Redirect Flow**: Returns `payment_link` for customer redirect to CinetPay payment page
- **Transaction ID**: Your internal ID is echoed back; CinetPay uses internal references

### 2. Check Payment Status

Retrieve the current status of a payment transaction using EasySwitch's `check_status` method.

```python
# Check transaction status (use your transaction ID)
transaction_id = "TXN-123456"
response = client.check_status(transaction_id)

status = response.status
print(f"Status: {status}")
print(f"Amount: {response.amount}")

# Check specific status types
if status == TransactionStatus.SUCCESSFUL:
    print("Payment completed successfully!")
elif status == TransactionStatus.PENDING:
    print("Payment is still processing...")
elif status == TransactionStatus.FAILED:
    print("Payment failed")
```

**Response Object (TransactionStatusResponse):**

```python
TransactionStatusResponse(
    transaction_id="TXN-123456",      # Your transaction ID
    provider=Provider.CINETPAY,
    status=TransactionStatus.SUCCESSFUL,
    amount=1000,
    data={...}  # Raw CinetPay status response
)
```

**Available TransactionStatus Values:**

```python
class TransactionStatus(str, Enum):
    PENDING = "pending"        # Transaction initiated
    SUCCESSFUL = "successful"  # Payment completed
    FAILED = "failed"         # Payment failed
    ERROR = "error"           # System error
    CANCELLED = "cancelled"   # User cancelled
    EXPIRED = "expired"       # Payment expired
    UNKNOWN = "unknown"       # Status unclear
```

## Implementation Guide

### Understanding CinetPay Payment Process

CinetPay follows a **redirect-based payment flow** where customers are redirected to CinetPay's secure payment page to complete their transaction. Here's what happens:

1. **Payment Creation**: Your app creates a payment request
2. **Customer Redirect**: Customer is redirected to CinetPay payment page
3. **Payment Processing**: Customer completes payment on CinetPay
4. **Webhook Notification**: CinetPay notifies your app about payment status
5. **Status Verification**: Your app can verify payment status anytime

### Supported Currencies and Countries

| Currency | Code | Countries | Minimum Amount |
|----------|------|-----------|----------------|
| West African CFA Franc | XOF | Côte d'Ivoire, Senegal, Mali, Burkina Faso, Niger | 100 XOF (must be multiple of 5) |
| Central African CFA Franc | XAF | Cameroon, Chad, Central African Republic | 100 XAF (must be multiple of 5) |
| Congolese Franc | CDF | Democratic Republic of Congo | 1000 CDF |
| Guinean Franc | GNF | Guinea | 1000 GNF |
| US Dollar | USD | All supported countries | 1 USD |

### Technical Payment Flow

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Your App      │    │   EasySwitch    │    │    CinetPay     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                           │
         │ 1. send_payment()     │                           │
         ├──────────────────────►│                           │
         │                       │ 2. POST /v2/payment       │
         │                       ├──────────────────────────►│
         │                       │                           │
         │                       │ 3. Payment URL            │
         │                       │◄──────────────────────────┤
         │ 4. PaymentResponse    │                           │
         │◄──────────────────────┤                           │
         │                       │                           │
         │ 5. Redirect customer  │                           │
         │   to payment_link     │                           │
         │                       │                           │
┌─────────────────┐              │                           │
│    Customer     │              │                           │
└─────────────────┘              │                           │  
         │                       │                           │
         │ 6. Complete payment   │                           │
         ├───────────────────────┼──────────────────────────►│
         │                       │                           │
         │                       │ 7. Webhook                │
         │                       │◄──────────────────────────┤
         │ 8. parse_webhook()    │                           │
         │◄──────────────────────┤                           │
         │                       │                           │
         │ 9. check_status()     │                           │
         ├──────────────────────►│                           │
         │                       │ 10. POST /v2/payment/check│
         │                       ├──────────────────────────►│
         │                       │                           │
         │                       │ 11. Status response       │
         │                       │◄──────────────────────────┤
         │ 12. Status            │                           │
         │◄──────────────────────┤                           │
```

### Customer Payment Journey

```
╔══════════════════════════════════════════════════════════════════════╗
║                          CUSTOMER PAYMENT JOURNEY                    ║
╚══════════════════════════════════════════════════════════════════════╝

┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   MERCHANT  │    │ EASYSWITCH  │    │  CINETPAY   │    │  CUSTOMER   │
│   WEBSITE   │    │   LIBRARY   │    │    API      │    │   DEVICE    │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
        │                  │                  │                  │
        │ 1. Create Order  │                  │                  │
        │ ┌──────────────┐ │                  │                  │
        │ │ Order:#1234  │ │                  │                  │
        │ │ Amount: 5000 │ │                  │                  │
        │ │ Customer     │ │                  │                  │
        │ └──────────────┘ │                  │                  │
        │                  │                  │                  │
        │ 2. Send Payment  │                  │                  │
        ├─────────────────►│                  │                  │
        │                  │ 3. Process       │                  │
        │                  ├─────────────────►│                  │
        │                  │                  │                  │
        │                  │ 4. Payment Link  │                  │
        │ 5. Redirect URL  │◄─────────────────┤                  │
        │◄─────────────────┤                  │                  │
        │                  │                  │                  │
        │ 6. Redirect Customer to Payment     │                  │
        ├─────────────────────────────────────┼─────────────────►│
        │                  │                  │                  │
        │                  │                  │ 7. Show Payment  │
        │                  │                  │    Interface     │
        │                  │                  │ ┌──────────────┐ │
        │                  │                  │ │ Enter Phone  │ │
        │                  │                  │ │ Select MoMo  │ │
        │                  │                  │ │ Confirm Pay  │ │
        │                  │                  │ └──────────────┘ │
        │                  │                  │                  │
        │                  │                  │ 8. Payment Made  │
        │                  │                  │◄─────────────────┤
        │                  │                  │                  │
        │                  │ 9. Webhook       │                  │
        │ 10. Notification │◄─────────────────┤                  │
        │◄─────────────────┤                  │                  │
        │                  │                  │                  │
        │ 11. Update Order │                  │                  │
        │ ┌──────────────┐ │                  │                  │
        │ │ Status: PAID │ │                  │                  │
        │ │ Send Receipt │ │                  │                  │
        │ │ Ship Product │ │                  │                  │
        │ └──────────────┘ │                  │                  │
        │                  │                  │                  │
        │ 12. Success Page │                  │ 13. SMS Receipt  │
        ├─────────────────────────────────────┼─────────────────►│
        │                  │                  │                  │

╔═════════════════════════════════════════════════════════════════════╗
║  PAYMENT STATES: PENDING → PROCESSING → SUCCESS                     ║
╚═════════════════════════════════════════════════════════════════════╝

```

### Transaction Fields Reference

#### Required Fields (Must be present)

| Field | Type | Format | Description | Example | Validation Rules |
|-------|------|--------|-------------|---------|------------------|
| `transaction_id` | string | Any unique string | Your unique transaction identifier | `"TXN-ORDER-001"` | Max 100 chars, alphanumeric + hyphens |
| `amount` | float | Positive number | Amount in currency base unit (converted to int internally) | `5000.0` | Min: 100 XOF, 1 USD |
| `currency` | Currency | Enum value | Transaction currency | `Currency.XOF` | XOF, XAF, CDF, GNF, USD |
| `customer.first_name` | string | Text | Customer's first name | `"Marie"` | 2-50 characters |
| `customer.last_name` | string | Text | Customer's last name | `"Kouame"` | 2-50 characters |
| `customer.phone_number` | string | E.164 format | Phone with country code | `"+22507123456"` | Must start with + |

#### Optional Fields (Recommended)

| Field | Type | Format | Description | Example | Benefits |
|-------|------|--------|-------------|---------|----------|
| `customer.email` | string | Valid email | Customer's email address | `"marie@example.com"` | Receipts, notifications |
| `reason` | string | Text | Transaction description | `"Order #12345"` | Better tracking, receipts |
| `metadata` | dict | Key-value pairs | Custom data for your use | `{"order_id": "12345"}` | Associate with your records |

#### Field Validation Examples

```python
def validate_transaction_fields(data):
    """Validate transaction data before creating payment"""
    errors = []
    
    # Validate transaction_id
    if not data.get('transaction_id'):
        errors.append("transaction_id is required")
    elif len(data['transaction_id']) > 100:
        errors.append("transaction_id must be less than 100 characters")
    
    # Validate amount
    amount = data.get('amount', 0)
    currency = data.get('currency')
    min_amounts = {
        Currency.XOF: 100,
        Currency.XAF: 100, 
        Currency.CDF: 1000,
        Currency.GNF: 1000,
        Currency.USD: 1
    }
    
    if amount < min_amounts.get(currency, 100):
        errors.append(f"Amount too low for {currency}")
    
    # CinetPay requires amounts to be multiples of 5 for XOF and XAF
    if currency in [Currency.XOF, Currency.XAF] and amount % 5 != 0:
        errors.append(f"Amount must be a multiple of 5 for {currency}")
    
    # Validate phone number
    phone = data.get('customer', {}).get('phone_number', '')
    if not phone.startswith('+'):
        errors.append("Phone number must include country code (+225...)")
    
    # Validate names
    first_name = data.get('customer', {}).get('first_name', '')
    if len(first_name) < 2:
        errors.append("First name must be at least 2 characters")
    
    return errors

# Usage
validation_errors = validate_transaction_fields(transaction_data)
if validation_errors:
    print("Validation failed:", validation_errors)
```

### Advanced Payment Creation

**Basic Payment Creation:**

```python
from easyswitch import TransactionDetail, CustomerInfo, Currency, Provider

def create_basic_payment(order_data):
    """Create a basic payment - minimum required fields"""
    
    transaction = TransactionDetail(
        transaction_id=f"TXN-{order_data['order_id']}",
        provider=Provider.CINETPAY,
        amount=order_data['amount'],
        currency=Currency.XOF,
        customer=CustomerInfo(
            first_name=order_data['customer']['first_name'],
            last_name=order_data['customer']['last_name'],
            phone_number=order_data['customer']['phone'],
            email=order_data['customer']['email']
        ),
        reason=f"Order #{order_data['order_id']}"
    )
    
    try:
        response = client.send_payment(transaction)
        return {
            'success': True,
            'payment_url': response.payment_link,
            'transaction_id': response.transaction_id
        }
    except Exception as e:
        return {'success': False, 'error': str(e)}

**Advanced Payment Creation with Metadata:**

```python
def create_advanced_payment(order_data):
    """Create payment with metadata and validation"""
    
    # Validate input data first
    validation_errors = validate_transaction_fields(order_data)
    if validation_errors:
        return {'success': False, 'errors': validation_errors}
    
    # Create transaction with metadata
    transaction = TransactionDetail(
        transaction_id=f"TXN-{order_data['order_id']}-{int(time.time())}",
        provider=Provider.CINETPAY,
        amount=float(order_data['amount']),
        currency=Currency.XOF,
        customer=CustomerInfo(
            first_name=order_data['customer']['first_name'].strip(),
            last_name=order_data['customer']['last_name'].strip(),
            phone_number=format_phone_number(order_data['customer']['phone']),
            email=order_data['customer'].get('email', '').strip() or None
        ),
        reason=f"Order #{order_data['order_id']} - {order_data.get('description', 'Payment')}",
        metadata={
            'order_id': order_data['order_id'],
            'customer_id': order_data.get('customer_id'),
            'payment_method': 'mobile_money',
            'created_at': datetime.now().isoformat(),
            'source': 'web_checkout'
        }
    )
    
    try:
        # Log payment attempt
        logger.info(f"Creating payment for order {order_data['order_id']}")
        
        response = client.send_payment(transaction)
        
        # Log success
        logger.info(f"Payment created: {response.transaction_id}")
        
        return {
            'success': True,
            'payment_url': response.payment_link,
            'transaction_id': response.transaction_id,
            'payment_token': response.transaction_token,
            'expires_at': datetime.now() + timedelta(hours=1)  # CinetPay links expire after 1 hour
        }
        
    except Exception as e:
        # Log error
        logger.error(f"Payment creation failed for order {order_data['order_id']}: {str(e)}")
        return {'success': False, 'error': str(e)}

def format_phone_number(phone):
    """Format phone number to E.164 standard"""
    phone = phone.strip().replace(' ', '').replace('-', '').replace('(', '').replace(')', '')
    
    if not phone.startswith('+'):
        # Assume Côte d'Ivoire if no country code
        if phone.startswith('0'):
            phone = '+225' + phone[1:]
        elif len(phone) == 8:
            phone = '+225' + phone
        else:
            phone = '+225' + phone
    
    return phone

**Complete E-commerce Integration Example:**

```python
import time
import logging
from datetime import datetime, timedelta
from easyswitch import EasySwitch, Provider, TransactionDetail, CustomerInfo, Currency

logger = logging.getLogger(__name__)

class PaymentService:
    """Complete payment service for e-commerce integration"""
    
    def __init__(self):
        self.client = EasySwitch.from_env()
        self.payments = {}  # In production, use database
    
    def create_checkout_payment(self, order_data):
        """Create payment for checkout process"""
        
        # Generate unique transaction ID
        transaction_id = f"TXN-{order_data['order_id']}-{int(time.time())}"
        
        # Prepare customer data
        customer_data = order_data['customer']
        
        # Create transaction
        transaction = TransactionDetail(
            transaction_id=transaction_id,
            provider=Provider.CINETPAY,
            amount=float(order_data['total_amount']),
            currency=Currency.XOF,
            customer=CustomerInfo(
                first_name=customer_data['first_name'],
                last_name=customer_data['last_name'],
                phone_number=self.format_phone(customer_data['phone']),
                email=customer_data.get('email')
            ),
            reason=f"Order #{order_data['order_id']} - {len(order_data['items'])} items",
            metadata={
                'order_id': order_data['order_id'],
                'customer_id': customer_data.get('id'),
                'items_count': len(order_data['items']),
                'shipping_address': order_data.get('shipping_address'),
                'checkout_source': 'web'
            }
        )
        
        try:
            response = self.client.send_payment(transaction)
            
            # Store payment info
            self.payments[transaction_id] = {
                'order_id': order_data['order_id'],
                'status': 'pending',
                'created_at': datetime.now(),
                'payment_url': response.payment_link,
                'amount': order_data['total_amount']
            }
            
            logger.info(f"Payment created: {transaction_id} for order {order_data['order_id']}")
            
            return {
                'success': True,
                'transaction_id': transaction_id,
                'payment_url': response.payment_link,
                'expires_in': 3600  # 1 hour
            }
            
        except Exception as e:
            logger.error(f"Payment creation failed: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'error_code': 'PAYMENT_CREATION_FAILED'
            }
    
    def format_phone(self, phone):
        """Format phone number for CinetPay"""
        phone = phone.strip().replace(' ', '').replace('-', '')
        
        if not phone.startswith('+'):
            # Add Côte d'Ivoire country code
            phone = '+225' + phone.lstrip('0')
        
        return phone
    
    def get_payment_status(self, transaction_id):
        """Get current payment status"""
        try:
            response = self.client.check_status(transaction_id)
            
            # Update local storage
            if transaction_id in self.payments:
                self.payments[transaction_id]['status'] = response.status.value
                self.payments[transaction_id]['updated_at'] = datetime.now()
            
            return {
                'success': True,
                'transaction_id': response.transaction_id,
                'status': response.status.value,
                'amount': response.amount,
                'currency': response.currency.value
            }
            
        except Exception as e:
            logger.error(f"Status check failed for {transaction_id}: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

# Usage example
payment_service = PaymentService()

order_data = {
    'order_id': 'ORD-12345',
    'total_amount': 15000,  # 150.00 XOF
    'items': [
        {'name': 'Product A', 'price': 10000, 'quantity': 1},
        {'name': 'Product B', 'price': 5000, 'quantity': 1}
    ],
    'customer': {
        'id': 'CUST-567',
        'first_name': 'Aminata',
        'last_name': 'Traore',
        'phone': '07 12 34 56 78',
        'email': 'aminata@example.com'
    },
    'shipping_address': 'Abidjan, Côte d\'Ivoire'
}

result = payment_service.create_checkout_payment(order_data)
if result['success']:
    print(f"Redirect customer to: {result['payment_url']}")
else:
    print(f"Payment failed: {result['error']}")
```

### Checking Payment Status

```python
from easyswitch import TransactionStatus

def check_payment_status(transaction_id):
    try:
        status_response = client.check_status(transaction_id)
        return {
            'transaction_id': status_response.transaction_id,
            'status': status_response.status,
            'is_successful': status_response.status == TransactionStatus.SUCCESSFUL,
            'is_pending': status_response.status == TransactionStatus.PENDING,
            'amount': status_response.amount
        }
    except Exception as e:
        return {'error': str(e)}
```

---

## Webhook Handling

### Webhook Validation and Processing

```python
from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/webhook/cinetpay', methods=['POST'])
def handle_webhook():
    try:
        payload = request.get_json()
        headers = dict(request.headers)
        
        if client.validate_webhook(payload, headers, Provider.CINETPAY):
            event = client.parse_webhook(payload, headers, Provider.CINETPAY)
            
            if event.event_type == "PAYMENT_SUCCESS":
                process_successful_payment(event)
            elif event.event_type == "PAYMENT_FAILED":
                process_failed_payment(event)
            
            return jsonify({'status': 'success'}), 200
        else:
            return jsonify({'error': 'Invalid signature'}), 401
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def process_successful_payment(event):
    print(f"Payment successful: {event.transaction_id}")

def process_failed_payment(event):
    print(f"Payment failed: {event.transaction_id}")
```

### Webhook Security

Always validate webhooks to ensure they come from CinetPay:

```python
def is_webhook_valid(payload, headers):
    return client.validate_webhook(payload, headers, Provider.CINETPAY)

@app.route('/webhook/cinetpay', methods=['POST'])
def webhook():
    if not is_webhook_valid(request.get_json(), dict(request.headers)):
        return "Unauthorized", 401
    
    event = client.parse_webhook(request.get_json(), dict(request.headers), Provider.CINETPAY)
    return "OK", 200
```

---

## Error Handling

### Common Exceptions

```python
from easyswitch.exceptions import (
    PaymentError, AuthenticationError, 
    ConfigurationError, UnsupportedOperationError
)

def safe_payment_processing(transaction_data):
    try:
        transaction = TransactionDetail(**transaction_data)
        response = client.send_payment(transaction)
        return {'success': True, 'data': response}
        
    except AuthenticationError:
        return {'success': False, 'error': 'Invalid API credentials'}
    except PaymentError as e:
        return {'success': False, 'error': f'Payment failed: {str(e)}'}
    except ConfigurationError:
        return {'success': False, 'error': 'Configuration error'}
    except UnsupportedOperationError:
        return {'success': False, 'error': 'Operation not supported'}
    except Exception as e:
        return {'success': False, 'error': f'Unexpected error: {str(e)}'}
```

### Retry Logic

```python
import time
import random

def payment_with_retry(transaction, max_attempts=3):
    for attempt in range(max_attempts):
        try:
            return client.send_payment(transaction)
        except Exception as e:
            if attempt == max_attempts - 1:
                raise e
            
            wait_time = (2 ** attempt) + random.uniform(0, 1)
            time.sleep(min(wait_time, 10))
    
    return None
```

---

## CinetPay Limitations

**Important**: CinetPay has several API limitations that affect integration design:

### Unsupported Operations

| Operation | Status | Alternative |
|-----------|--------|-------------|
| Refunds | Not supported | Manual processing via dashboard |
| Transaction Cancellation | Not supported | Contact CinetPay support |
| Partial Refunds | Not supported | Manual processing via dashboard |

### Workarounds

```python
# Example: Handle unsupported operations gracefully
def attempt_refund(transaction_id: str, amount: float, reason: str):
    """Attempt refund with fallback to manual processing"""
    try:
        # This will raise UnsupportedOperationError
        refund_response = client.refund(transaction_id, amount=amount)
        return refund_response
    except UnsupportedOperationError:
        # Log refund request for manual processing
        refund_record = {
            "transaction_id": transaction_id,
            "refund_amount": amount,
            "reason": reason,
            "status": "pending_manual_processing",
            "created_at": datetime.now(),
            "provider": "cinetpay_manual"
        }
        # Save to database for manual processing
        save_manual_refund_request(refund_record)

        # Notify administrators
        notify_manual_refund_required(refund_record)

        return {
            "status": "manual_processing_required",
            "message": "Refund request logged for manual processing",
            "reference": refund_record
        }

def save_manual_refund_request(refund_record: dict):
    """Save refund request for manual processing"""
    # Implementation depends on your system
    pass

def notify_manual_refund_required(refund_record: dict):
    """Notify administrators of manual refund requirement"""
    # Send email/notification to administrators
    pass
```

## Testing

### Test Environment Setup

CinetPay provides a sandbox environment for testing your integration:

```python
# Test configuration
test_config = {
    "debug": True,
    "providers": {
        Provider.CINETPAY: {
            "environment": "sandbox",
            "api_key": "cp_test_your_test_api_key",
            "timeout": 30,
            "extra": {
                "site_id": "your_test_site_id",
                "secret": "your_test_secret_key",
                "channels": "MOBILE_MONEY",
                "lang": "fr"
            }
        }
    }
}

test_client = EasySwitch.from_dict(test_config)
```

### Test Phone Numbers

Use these test phone numbers to simulate different payment scenarios:

| Country | Operator | Phone Number | Expected Result |
|---------|----------|--------------|-----------------|
| Côte d'Ivoire | Orange | `+22507000001` | Success |
| Côte d'Ivoire | Orange | `+22507000000` | Failure |
| Côte d'Ivoire | MTN | `+22505000001` | Success |
| Côte d'Ivoire | MTN | `+22505000000` | Failure |
| Senegal | Orange | `+22177000001` | Success |
| Senegal | Orange | `+22177000000` | Failure |

### Test Amounts

For testing different scenarios, use these amounts:

| Amount (Minor Units) | Display Amount | Expected Result |
|---------------------|----------------|-----------------|
| 100 | 1.00 XOF | Success (minimum amount) |
| 50 | 0.50 XOF | Failure (below minimum) |
| 100000 | 1000.00 XOF | Success |
| 10000000 | 100000.00 XOF | May fail (exceeds some limits) |

### Complete Testing Example

```python
import asyncio
from easyswitch import (
    EasySwitch, Provider, TransactionDetail,
    TransactionStatus, Currency, CustomerInfo
)

class CinetPayTestSuite:
    def __init__(self):
        self.test_config = {
            "debug": True,
            "providers": {
                Provider.CINETPAY: {
                    "environment": "sandbox",
                    "api_key": "cp_test_your_api_key",
                    "timeout": 30,
                    "extra": {
                        "site_id": "your_test_site_id",
                        "secret": "your_test_secret",
                        "channels": "MOBILE_MONEY",
                        "lang": "fr"
                    }
                }
            }
        }
        self.client = EasySwitch.from_dict(self.test_config)

    def test_successful_payment(self):
        """Test successful payment scenario"""
        customer = CustomerInfo(
            first_name="Test",
            last_name="User",
            email="test@example.com",
            phone_number="+22507000001"  # Success test number
        )

        transaction = TransactionDetail(
            transaction_id="TEST-SUCCESS-001",
            provider=Provider.CINETPAY,
            amount=1000,  # 10.00 XOF
            currency=Currency.XOF,
            customer=customer,
            reason="Test successful payment"
        )

        try:
            response = self.client.send_payment(transaction)
            assert response.status in [TransactionStatus.PENDING, TransactionStatus.SUCCESSFUL]
            print("Successful payment test passed")
            return response
        except Exception as e:
            print(f"Successful payment test failed: {e}")
            raise

    def test_failed_payment(self):
        """Test failed payment scenario"""
        customer = CustomerInfo(
            first_name="Test",
            last_name="User",
            email="test@example.com",
            phone_number="+22507000000"  # Failure test number
        )

        transaction = TransactionDetail(
            transaction_id="TEST-FAIL-001",
            provider=Provider.CINETPAY,
            amount=1000,
            currency=Currency.XOF,
            customer=customer,
            reason="Test failed payment"
        )

        try:
            response = self.client.send_payment(transaction)
            # Payment may initially succeed but fail later
            print("Payment created, check status for failure")
            return response
        except Exception as e:
            print(f"Failed payment test passed: {e}")
            return None

    def test_status_checking(self, transaction_id: str):
        """Test status checking functionality"""
        try:
            status_response = self.client.check_status(transaction_id)
            print(f"Status check successful: {status_response.status}")
            return status_response
        except Exception as e:
            print(f"Status check failed: {e}")
            raise

    def run_all_tests(self):
        """Run complete test suite"""
        print("Starting CinetPay integration test suite...")

        # Test successful payment
        success_response = self.test_successful_payment()

        # Test failed payment
        self.test_failed_payment()

        # Test status checking if we have a transaction
        if success_response:
            self.test_status_checking(success_response.transaction_id)

        print("Test suite completed!")

# Run tests
if __name__ == "__main__":
    test_suite = CinetPayTestSuite()
    test_suite.run_all_tests()
```

### Testing Checklist

Before going live, ensure you've tested:

- Payment creation with valid data
- Payment creation with invalid data
- Payment status checking for all status types
- Webhook validation and parsing
- Webhook handling for all event types
- Error handling for all exception types
- Different phone number formats (E.164)
- Amount validation (minimum/maximum limits, multiple of 5 for XOF/XAF)
- Different currencies (XOF, XAF, CDF, GNF, USD)
- Different mobile operators per country
- Network timeout scenarios
- Authentication with invalid credentials
- Configuration validation

## Common Issues

### Phone Number Format

Phone numbers must include country code:

```python
def format_phone_number(phone):
    phone = phone.strip().replace(' ', '').replace('-', '')
    
    if not phone.startswith('+'):
        if phone.startswith('0'):
            phone = '+225' + phone[1:]
        else:
            phone = '+225' + phone
    
    return phone

customer_phone = format_phone_number("07 12 34 56 78")
```

### Amount Validation

```python
def validate_amount(amount, currency):
    min_amounts = {
        Currency.XOF: 100,
        Currency.XAF: 100,
        Currency.CDF: 1000,
        Currency.USD: 1
    }
    
    min_amount = min_amounts.get(currency, 100)
    if amount < min_amount:
        raise ValueError(f"Minimum amount for {currency} is {min_amount}")
    
    return True
```

### Environment Configuration

```python
import os

def validate_config():
    required_vars = [
        'CINETPAY_API_KEY',
        'CINETPAY_SITE_ID', 
        'CINETPAY_SECRET',
        'CINETPAY_CALLBACK_URL'
    ]
    
    missing = [var for var in required_vars if not os.getenv(var)]
    
    if missing:
        raise ConfigurationError(f"Missing environment variables: {missing}")
    
    return True
```

---

## Production Guidelines

### Security Checklist

- Store API keys in environment variables, never in code
- Use HTTPS for all webhook URLs
- Always validate webhook signatures
- Implement proper error handling and logging
- Use strong, unique transaction IDs

### Performance Best Practices

```python
client = EasySwitch.from_env()

def process_payment(transaction_data):
    transaction = TransactionDetail(**transaction_data)
    
    try:
        response = client.send_payment(transaction)
        
        log_payment_success(transaction.transaction_id, response.payment_link)
        return response
        
    except Exception as e:
        log_payment_error(transaction.transaction_id, str(e))
        raise
```

### Monitoring

```python
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def log_payment_success(transaction_id, payment_url):
    logger.info(f"Payment created: {transaction_id} -> {payment_url}")

def log_payment_error(transaction_id, error):
    logger.error(f"Payment failed: {transaction_id} -> {error}")
```

---

## API Reference

### TransactionDetail

```python
TransactionDetail(
    transaction_id: str,
    provider: Provider,
    amount: float,
    currency: Currency,
    customer: CustomerInfo,
    reason: str = None,
    metadata: dict = None
)
```

### CustomerInfo

```python
CustomerInfo(
    first_name: str,
    last_name: str,
    phone_number: str,
    email: str = None
)
```

### PaymentResponse

```python
response.payment_link: str
response.transaction_id: str
response.transaction_token: str
```

### StatusResponse

```python
response.transaction_id: str
response.status: TransactionStatus
response.amount: float
response.currency: Currency
```

---

## Practical Use Case - E-commerce Integration

```python
from flask import Flask, request, jsonify
from easyswitch import EasySwitch, Provider, TransactionDetail, Currency, CustomerInfo

app = Flask(__name__)
client = EasySwitch.from_env()

@app.route('/create-payment', methods=['POST'])
def create_payment():
    data = request.get_json()
    
    transaction = TransactionDetail(
        transaction_id=f"TXN-{data['order_id']}",
        provider=Provider.CINETPAY,
        amount=data['amount'],
        currency=Currency.XOF,
        customer=CustomerInfo(
            first_name=data['customer']['first_name'],
            last_name=data['customer']['last_name'],
            phone_number=data['customer']['phone'],
            email=data['customer']['email']
        ),
        reason=f"Order #{data['order_id']}"
    )
    
    response = client.send_payment(transaction)
    return jsonify({
        'payment_url': response.payment_link,
        'transaction_id': response.transaction_id
    })

@app.route('/webhook/cinetpay', methods=['POST'])
def webhook():
    payload = request.get_json()
    headers = dict(request.headers)
    
    if client.validate_webhook(payload, headers, Provider.CINETPAY):
        event = client.parse_webhook(payload, headers, Provider.CINETPAY)
        return "OK", 200
    
    return "Invalid", 401
```

---

## Support and Resources

- **EasySwitch Documentation**: [Full API Reference](../api-reference/base-adapter.md)
- **CinetPay Official Docs**: [CinetPay Developer Portal](https://docs.cinetpay.com)
- **GitHub Repository**: [EasySwitch on GitHub](https://github.com/AllDotPy/EasySwitch)

For support:
- EasySwitch: [GitHub Issues](https://github.com/AllDotPy/EasySwitch/issues)
- CinetPay: Support through their merchant dashboard

---
