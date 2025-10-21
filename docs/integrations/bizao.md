# Bizao Integration with EasySwitch

## Table of Contents
- [Overview](#overview)
- [Quick Start](#quick-start-5-minutes)
- [When to Use Bizao](#when-to-use-bizao)
- [Prerequisites](#prerequisites)
- [Supported Countries & Operators](#supported-countries--operators)
- [Setup](#setup)
- [Configuration](#configuration)
- [EasySwitch Methods](#easyswitch-methods)
- [API Methods](#api-methods)
- [Payment Flow Diagram](#payment-flow-diagram)
- [Practical Integration Examples](#practical-integration-examples)
- [Error Handling](#error-handling)
- [Bizao Limitations](#bizao-limitations)
- [Testing](#testing)
- [Common Pitfalls & Troubleshooting](#common-pitfalls--troubleshooting)
- [Troubleshooting Decision Tree](#troubleshooting-decision-tree)
- [Limits & Considerations](#limits--considerations)
- [Support & Resources](#support--resources)

## Overview

Bizao is a leading African mobile money aggregator that simplifies payment processing across West and Central Africa. As a comprehensive payment gateway, Bizao connects businesses to multiple mobile money operators, enabling seamless transactions across diverse markets and currencies. With its robust API and extensive mobile money network coverage, Bizao empowers businesses to accept payments from customers using various mobile wallets including MTN Mobile Money, Orange Money, Moov Money, and more.

**Why use Bizao with EasySwitch?**
- **Wide Coverage**: Supports 15+ countries across West and Central Africa
- **Multiple Operators**: Integrates with all major mobile money providers
- **Multi-Currency**: Handles XOF, XAF, CDF, GNF, and USD
- **Flexible Channels**: Supports web, TPE (point of sale), and USSD channels
- **Real-time Processing**: Instant payment confirmation and status updates

## Quick Start (5 Minutes)

For developers who want to get started immediately:

```python
# 1. Install
pip install easyswitch

# 2. Configure (use your Bizao credentials)
from easyswitch import EasySwitch, Provider

client = EasySwitch.from_env()  # Reads from .env file

# 3. Send a payment
from easyswitch import (
    TransactionDetail, Currency, CustomerInfo, 
    TransactionStatus, TransactionType
)

transaction = TransactionDetail(
    transaction_id="TXN-001",
    provider=Provider.BIZAO,
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

## When to Use Bizao

### Best For:
- Mobile money payments in West/Central Africa
- Multi-operator support (Orange, MTN, Moov, Wave)
- Multi-country operations (15+ countries)
- USSD/web/TPE payment channels
- Real-time payment processing
- Cross-border transactions in Africa

### Not Ideal For:
- Automated refunds (manual process required via dashboard)
- Transaction cancellations (not supported by API)
- Card payments (Bizao focuses on mobile money)
- Real-time transaction details beyond status (use `check_status()` instead)
- Markets outside Africa

### Consider Alternatives If You Need:
- Automated refund processing
- Programmatic transaction cancellation
- Card payment processing
- Non-African markets
- Real-time detailed transaction retrieval

## Prerequisites

Before integrating Bizao with EasySwitch, ensure you have:

- EasySwitch library installed. For setup instructions, see [Installation](../getting-started/installation.md)
- A Bizao merchant account (create one at [bizao.com](https://bizao.com))
- Development and production API credentials from your Bizao dashboard
- OAuth2 client credentials (client ID and secret) for both environments
- Understanding of your target markets and supported mobile money operators

## Supported Countries & Operators

Bizao supports mobile money transactions across multiple African countries:

| Country | Mobile Money Operators | Currency |
|---------|----------------------|----------|
| **Benin** | MTN, Moov, Celtiis | XOF |
| **Burkina Faso** | Orange, Moov | XOF |
| **Côte d'Ivoire** | MTN, Orange, Moov, Wave | XOF |
| **Guinea** | MTN, Orange | GNF |
| **Mali** | Orange, Moov | XOF |
| **Niger** | Airtel, Orange | XOF |
| **Senegal** | Orange, Free, Wave | XOF |
| **Togo** | Moov, TMoney | XOF |
| **Cameroon** | MTN, Orange | XAF |
| **Chad** | Airtel, Tigo | XAF |
| **Central African Republic** | Orange, Moov | XAF |
| **Democratic Republic of Congo** | Airtel, Orange, Vodacom | CDF |

## Setup

### Basic Configuration

```python
from easyswitch import (
    EasySwitch,
    Provider,
    TransactionDetail,
    PaymentResponse,
    TransactionStatus,
    Currency,
    TransactionType,
    CustomerInfo,
    Countries
)

# Prepare Bizao configuration
config = {
    "debug": True,
    "default_provider": Provider.BIZAO,
    "providers": {
        Provider.BIZAO: {
            "api_key": "",  # Will be set dynamically via OAuth2
            "callback_url": "https://your-domain.com/webhook/bizao",
            "return_url": "https://your-domain.com/success",
            "timeout": 60,  # timeout in seconds for HTTP requests
            "environment": "sandbox",    # 'sandbox' or 'production'
            "extra": {
                # Development credentials
                "dev_client_id": "your_dev_client_id",
                "dev_client_secret": "your_dev_client_secret",
                "dev_token_url": "https://preproduction-gateway.bizao.com/mobilemoney/oauth/token",

                # Production credentials
                "prod_client_id": "your_prod_client_id",
                "prod_client_secret": "your_prod_client_secret",
                "prod_token_url": "https://api.bizao.com/mobilemoney/oauth/token",

                # Required payment parameters
                "country-code": "CI",  # ISO country code (e.g., CI for Côte d'Ivoire)
                "mno-name": "orange",  # Mobile operator: orange, mtn, moov, wave, etc.
                "channel": "web",      # Payment channel: web, tpe, ussd
                "lang": "fr",          # Language: fr, en
                "cancel_url": "https://your-domain.com/cancel"
            }
        }
    }
}

# Initialize EasySwitch with Bizao
client = EasySwitch.from_dict(config)
```

### Alternative Configuration Methods

EasySwitch supports multiple configuration approaches:

```python
# 1. From environment variables
client = EasySwitch.from_env()

# 2. From JSON file
client = EasySwitch.from_json("config.json")

# 3. From YAML file
client = EasySwitch.from_yaml("config.yaml")

# 4. From multiple sources (with overrides)
client = EasySwitch.from_multi_sources(
    env_file=".env",
    json_file="overrides.json"
)
```

## Configuration

### Environment Variables

Create a `.env` file or set the following environment variables:

```bash
# Bizao Configuration
EASYSWITCH_BIZAO_ENVIRONMENT=sandbox
EASYSWITCH_BIZAO_CALLBACK_URL=https://your-domain.com/webhook/bizao
EASYSWITCH_BIZAO_RETURN_URL=https://your-domain.com/success
EASYSWITCH_BIZAO_TIMEOUT=60

# Development credentials
EASYSWITCH_BIZAO_DEV_CLIENT_ID=your_dev_client_id
EASYSWITCH_BIZAO_DEV_CLIENT_SECRET=your_dev_client_secret
EASYSWITCH_BIZAO_DEV_TOKEN_URL=https://preproduction-gateway.bizao.com/mobilemoney/oauth/token

# Production credentials
EASYSWITCH_BIZAO_PROD_CLIENT_ID=your_prod_client_id
EASYSWITCH_BIZAO_PROD_CLIENT_SECRET=your_prod_client_secret
EASYSWITCH_BIZAO_PROD_TOKEN_URL=https://api.bizao.com/mobilemoney/oauth/token

# Payment configuration
EASYSWITCH_BIZAO_COUNTRY_CODE=CI
EASYSWITCH_BIZAO_MNO_NAME=orange
EASYSWITCH_BIZAO_CHANNEL=web
EASYSWITCH_BIZAO_LANG=fr
EASYSWITCH_BIZAO_CANCEL_URL=https://your-domain.com/cancel
```

### Authentication

Bizao uses OAuth2 client credentials flow for authentication. EasySwitch automatically handles token acquisition and renewal:

**Authentication Flow:**
1. EasySwitch sends client credentials to token endpoint
2. Bizao returns access token
3. Access token is used for all subsequent API requests
4. Token is automatically refreshed when needed

```python
# Authentication is handled automatically during initialization
# The adapter will:
# 1. Create basic auth header from client_id:client_secret
# 2. Request access token from token_url
# 3. Store token for API requests
# 4. Handle token refresh automatically
```

> **Security Note**: Never expose your client credentials in client-side code. Always use environment variables or secure configuration management.

## EasySwitch Methods

EasySwitch provides a unified interface for all payment operations:

### Core Methods

| Method | Description | Returns |
|--------|-------------|---------|
| `send_payment(transaction)` | Send a payment transaction | `PaymentResponse` |
| `check_status(transaction_id)` | Check transaction status | `TransactionStatusResponse` |
| `validate_webhook(payload, headers)` | Validate webhook signature | `bool` |
| `parse_webhook(payload, headers)` | Parse webhook into WebhookEvent | `WebhookEvent` |

> **Note**: `cancel_transaction()`, `refund()`, and `get_transaction_detail()` are not supported by Bizao. See [Bizao Limitations](#bizao-limitations) for alternatives.

### Configuration Methods

| Method | Description | Returns |
|--------|-------------|---------|
| `from_env(env_file)` | Initialize from environment variables | `EasySwitch` |
| `from_json(json_file)` | Initialize from JSON file | `EasySwitch` |
| `from_yaml(yaml_file)` | Initialize from YAML file | `EasySwitch` |
| `from_dict(config_dict)` | Initialize from Python dictionary | `EasySwitch` |
| `from_multi_sources(**sources)` | Initialize from multiple sources | `EasySwitch` |

## API Methods

### 1. Create Payment

Initiate a payment transaction using EasySwitch's `TransactionDetail` class and `send_payment` method.

```python
# Create a TransactionDetail object
transaction = TransactionDetail(
    transaction_id="TXN-123456",  # Unique ID generated by your system
    provider=Provider.BIZAO,
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
    callback_url="https://your-site.com/webhook/bizao",  # Override default
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
print(f"Bizao Payment Token: {response.transaction_token}")   # Bizao's payment token
print(f"Payment URL: {response.payment_link}")              # Web channel only
print(f"Status: {response.status}")
print(f"Is Successful: {response.is_successful}")
print(f"Is Pending: {response.is_pending}")
```

**Response Object (PaymentResponse):**
```python
PaymentResponse(
    transaction_id="TXN-123456",      # Your transaction ID (echoed back)
    provider=Provider.BIZAO,
    status=TransactionStatus.PENDING,
    amount=1000,
    currency=Currency.XOF,
    payment_link="https://checkout.bizao.com/...",  # Web channel only
    transaction_token="pay_token_abc123",           # Empty for TPE/USSD
    created_at=datetime(2024, 1, 15, 10, 30, 0),
    customer=CustomerInfo(...),
    raw_response={...}  # Raw Bizao response
)
```

**Important Notes:**

- **Amount Format**: Always provide amounts in minor units (e.g., 1000 for 10.00 XOF)
- **Phone Format**: Phone numbers must be in E.164 format (+country_code + number)
- **Channel Behavior**:
  - **Web**: Returns `payment_link` for redirect, empty `transaction_token`
  - **TPE/USSD**: Returns `transaction_token`, empty `payment_link`, requires phone number
- **Transaction ID**: Your internal ID is echoed back; Bizao uses internal references

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
    provider=Provider.BIZAO,
    status=TransactionStatus.SUCCESSFUL,
    amount=1000,
    data={...}  # Raw Bizao status response
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

### 3. Handling Webhooks

EasySwitch provides built-in webhook validation and parsing methods for Bizao. This ensures secure and standardized webhook handling.

#### EasySwitch Webhook Methods

| Method | Description | Returns |
|--------|-------------|---------|
| `validate_webhook(payload, headers)` | Validate webhook signature only | `bool` |
| `parse_webhook(payload, headers)` | Parse webhook into WebhookEvent (calls validate_webhook internally) | `WebhookEvent` |

> **Important**: `parse_webhook()` automatically calls `validate_webhook()` internally, so you don't need to validate separately when using `parse_webhook()`.

#### Webhook Configuration with EasySwitch

Set up your webhook endpoint using EasySwitch's built-in methods:

```python
from flask import Flask, request, jsonify
from easyswitch import EasySwitch, Provider, WebhookEvent
import json

app = Flask(__name__)

# Initialize EasySwitch client
client = EasySwitch.from_env()  # or your preferred config method

@app.route('/webhook/bizao', methods=['POST'])
def handle_bizao_webhook():
    try:
        # Get webhook data
        payload = request.get_json()
        headers = dict(request.headers)

        # Parse webhook using EasySwitch (automatically validates signature)
        webhook_event = client.parse_webhook(
            payload=payload,
            headers=headers,
        )

        # Process webhook event
        process_webhook_event(webhook_event)

        return jsonify({'status': 'success'})

    except Exception as e:
        print(f"Webhook processing error: {e}")
        return jsonify({'error': 'Processing failed'}), 500

def process_webhook_event(webhook_event: WebhookEvent):
    """Process webhook event using EasySwitch WebhookEvent object"""

    # Access standardized webhook data
    event_type = webhook_event.event_type
    transaction_id = webhook_event.transaction_id
    status = webhook_event.status
    amount = webhook_event.amount
    currency = webhook_event.currency
    created_at = webhook_event.created_at

    print(f"Webhook Event: {event_type}")
    print(f"Transaction ID: {transaction_id}")
    print(f"Status: {status}")
    print(f"Amount: {amount} {currency}")

    # Handle different event types
    if event_type == "payment.initiated":
        handle_payment_initiated(webhook_event)
    elif event_type == "payment.successful":
        handle_payment_successful(webhook_event)
    elif event_type == "payment.failed":
        handle_payment_failed(webhook_event)
    elif event_type == "payment.expired":
        handle_payment_expired(webhook_event)
    else:
        print(f"Unhandled event type: {event_type}")

def handle_payment_initiated(webhook_event: WebhookEvent):
    """Handle payment initiated event"""
    print(f"Payment initiated: {webhook_event.transaction_id}")
    # Update your database
    # Send confirmation SMS/email

def handle_payment_successful(webhook_event: WebhookEvent):
    """Handle payment successful event"""
    print(f"Payment completed: {webhook_event.transaction_id}")
    # Process successful payment
    # Update order status
    # Send receipt

def handle_payment_failed(webhook_event: WebhookEvent):
    """Handle payment failed event"""
    print(f"Payment failed: {webhook_event.transaction_id}")
    # Handle failure
    # Notify customer
    # Update order status

def handle_payment_expired(webhook_event: WebhookEvent):
    """Handle payment expired event"""
    print(f"Payment expired: {webhook_event.transaction_id}")
    # Handle expiration
    # Clean up resources
```

#### Webhook Events

Bizao sends the following webhook events that are automatically parsed by EasySwitch:

| Event Type | Description | When It's Sent | EasySwitch Status |
|------------|-------------|----------------|-------------------|
| `payment.initiated` | Payment started | When payment is initiated | `PENDING` |
| `payment.processing` | Payment processing | When operator is processing | `PROCESSING` |
| `payment.successful` | Payment completed | When customer completes payment | `SUCCESSFUL` |
| `payment.failed` | Payment failed | When payment fails | `FAILED` |
| `payment.expired` | Payment expired | When payment times out | `EXPIRED` |
| `payment.cancelled` | Payment cancelled | When customer cancels | `CANCELLED` |

#### WebhookEvent Object

EasySwitch's `WebhookEvent` provides standardized access to webhook data:

```python
@dataclass
class WebhookEvent:
    event_type: str              # e.g., "payment.successful"
    provider: str                # "bizao"
    transaction_id: str          # Your transaction ID
    status: TransactionStatus    # Normalized status
    amount: float                # Transaction amount
    currency: Currency           # Currency (XOF, XAF, etc.)
    created_at: datetime         # Event timestamp
    raw_data: Dict[str, Any]     # Original webhook payload
    metadata: Dict[str, Any]     # Additional metadata
    context: Dict[str, Any]      # Extra context data
```

#### Webhook Security

EasySwitch automatically handles webhook signature validation using Bizao's signature format:

- **Signature Header**: `X-Bizao-Signature`
- **Format**: `t=<timestamp>,s=<signature>`
- **Algorithm**: HMAC-SHA256
- **Validation**: Automatic via `client.parse_webhook()` (calls `validate_webhook()` internally)

### 4. Refunding Transactions (Not Supported)

> **Important**: Bizao does not support automated refunds through their API. Refunds must be processed manually through the Bizao dashboard or by contacting their support team.

```python
# This will raise UnsupportedOperationError
try:
    refund_response = client.refund("TXN-123456", amount=500)
except UnsupportedOperationError as e:
    print(f"Refunds not supported: {e.message}")
    # Handle refund request manually
```

**Refund Alternatives:**
1. **Manual Processing**: Use Bizao merchant dashboard
2. **Support Contact**: Contact Bizao support team
3. **Business Logic**: Track refunds in your system separately

## Payment Flow Diagram

```
┌─────────────┐    ┌──────────────┐    ┌─────────────┐    ┌──────────────┐    ┌─────────────┐
│   Customer  │    │  Your App    │    │ EasySwitch  │    │    Bizao     │    │Mobile Wallet│
│             │    │              │    │             │    │              │    │             │
└─────────────┘    └──────────────┘    └─────────────┘    └──────────────┘    └─────────────┘
       │                   │                   │                   │                   │
       │ 1. Initiate       │                   │                   │                   │
       │    Payment        │                   │                   │                   │
       ├──────────────────▶│                   │                   │                   │
       │                   │ 2. send_payment() │                   │                   │
       │                   ├──────────────────▶│                   │                   │
       │                   │                   │ 3. Authenticate & │                   │
       │                   │                   │    Create Payment │                   │
       │                   │                   ├──────────────────▶│                   │
       │                   │                   │                   │ 4. Send USSD/SMS │
       │                   │                   │                   │    to Customer    │
       │                   │                   │                   ├──────────────────▶│
       │                   │ 5. PaymentResponse│                   │                   │
       │                   │    (with payment_ │                   │                   │
       │                   │     link/token)   │                   │                   │
       │                   │◀──────────────────┤                   │                   │
       │ 6. Redirect to    │                   │                   │                   │
       │    Payment Page   │                   │                   │                   │
       │◀──────────────────┤                   │                   │                   │
       │                   │                   │                   │                   │
       │ 7. Complete Payment via Mobile Wallet │                   │                   │
       ├─────────────────────────────────────────────────────────────────────────────▶│
       │                   │                   │                   │                   │
       │                   │                   │ 8. Webhook       │                   │
       │                   │                   │    Notification   │                   │
       │                   │◀─────────────────────────────────────┤                   │
       │                   │                   │                   │                   │
       │ 9. Payment        │                   │                   │                   │
       │    Confirmation   │                   │                   │                   │
       │◀──────────────────┤                   │                   │                   │
```

**Payment Flow Steps:**
1. Customer initiates payment on your application
2. Your app calls `client.send_payment()` with transaction details
3. EasySwitch authenticates with Bizao and creates payment
4. Bizao sends USSD prompt or SMS to customer's mobile wallet
5. EasySwitch returns PaymentResponse with payment link/token
6. Customer is redirected to payment page (web) or receives USSD prompt
7. Customer completes payment through their mobile wallet
8. Bizao sends webhook notification to your callback URL
9. Your app processes webhook and confirms payment to customer

## Practical Integration Examples

### E-commerce Checkout Flow

```python
from easyswitch import (
    EasySwitch, Provider, TransactionDetail,
    PaymentResponse, TransactionStatus, Currency,
    TransactionType, CustomerInfo, Countries
)
from easyswitch.exceptions import (
    PaymentError, NetworkError, AuthenticationError,
    ValidationError, UnsupportedOperationError
)
import uuid
import time
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BizaoEcommerceIntegration:
    def __init__(self, environment="sandbox"):
        """Initialize Bizao integration for e-commerce"""
        self.config = {
            "debug": True,
            "default_provider": Provider.BIZAO,
            "providers": {
                Provider.BIZAO: {
                    "environment": environment,
                    "timeout": 60,
                    "callback_url": "https://shop.example.com/webhook/bizao",
                    "return_url": "https://shop.example.com/payment/success",
                    "extra": {
                        # Load from environment variables
                        "dev_client_id": os.getenv("BIZAO_DEV_CLIENT_ID"),
                        "dev_client_secret": os.getenv("BIZAO_DEV_CLIENT_SECRET"),
                        "dev_token_url": "https://preproduction-gateway.bizao.com/mobilemoney/oauth/token",

                        "prod_client_id": os.getenv("BIZAO_PROD_CLIENT_ID"),
                        "prod_client_secret": os.getenv("BIZAO_PROD_CLIENT_SECRET"),
                        "prod_token_url": "https://api.bizao.com/mobilemoney/oauth/token",

                        "country-code": "CI",
                        "mno-name": "orange",  # Default operator
                        "channel": "web",
                        "lang": "fr",
                        "cancel_url": "https://shop.example.com/payment/cancel"
                    }
                }
            }
        }
        self.client = EasySwitch.from_dict(self.config)

    def process_checkout(
        self,
        order_id: str,
        amount: float,
        currency: Currency,
        customer: CustomerInfo,
        mobile_operator: str = "orange"
    ):
        """Process e-commerce checkout with Bizao"""
        try:
            # Generate unique transaction ID
            transaction_id = f"SHOP-{order_id}-{uuid.uuid4().hex[:8]}"

            # Update operator in config for this transaction
            self.config["providers"][Provider.BIZAO]["extra"]["mno-name"] = mobile_operator.lower()

            # Create TransactionDetail object
            transaction = TransactionDetail(
                transaction_id=transaction_id,
                provider=Provider.BIZAO,
                status=TransactionStatus.PENDING,
                amount=int(amount * 100),  # Convert to minor units
                currency=currency,
                transaction_type=TransactionType.PAYMENT,
                customer=customer,
                reason=f"Order #{order_id}",
                reference=order_id,
                metadata={
                    "order_id": order_id,
                    "customer_id": customer.id,
                    "operator": mobile_operator,
                    "checkout_session": uuid.uuid4().hex
                }
            )

            # Send payment
            response = self.client.send_payment(transaction)

            logger.info(f"Checkout initiated: {response.transaction_id}")
            return {
                'success': True,
                'transaction_id': response.transaction_id,
                'payment_link': response.payment_link,
                'payment_token': response.transaction_token,
                'status': response.status,
                'redirect_url': response.payment_link if response.payment_link else None
            }

        except ValidationError as e:
            logger.error(f"Validation error: {e}")
            return {
                'success': False,
                'error': 'Invalid payment data',
                'message': str(e)
            }
        except AuthenticationError as e:
            logger.error(f"Authentication error: {e}")
            return {
                'success': False,
                'error': 'Authentication failed',
                'message': 'Please check your Bizao credentials'
            }
        except PaymentError as e:
            logger.error(f"Payment error: {e}")
            return {
                'success': False,
                'error': 'Payment processing failed',
                'message': str(e)
            }
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return {
                'success': False,
                'error': 'Unexpected error',
                'message': 'Please try again later'
            }

    def check_payment_status(self, transaction_id: str):
        """Check payment status for order updates"""
        try:
            result = self.client.check_status(transaction_id)
            logger.info(f"Payment status checked: {result.status}")
            return {
                'success': True,
                'status': result.status,
                'amount': result.amount,
                'transaction_id': result.transaction_id
            }
        except Exception as e:
            logger.error(f"Status check failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def handle_webhook(self, payload, headers):
        """Handle Bizao webhook for order updates"""
        try:
            # Parse webhook using EasySwitch
            webhook_event = self.client.parse_webhook(
                payload=payload,
                headers=headers
            )

            # Extract order information from metadata
            order_id = webhook_event.metadata.get('order_id')

            # Update order status based on payment status
            if webhook_event.status == TransactionStatus.SUCCESSFUL:
                self.mark_order_paid(order_id)
                self.send_order_confirmation(webhook_event)
            elif webhook_event.status == TransactionStatus.FAILED:
                self.mark_order_failed(order_id)
                self.send_payment_failure_notice(webhook_event)
            elif webhook_event.status == TransactionStatus.EXPIRED:
                self.mark_order_expired(order_id)

            logger.info(f"Webhook processed for order {order_id}: {webhook_event.status}")
            return {
                'success': True,
                'order_id': order_id,
                'status': webhook_event.status
            }

        except Exception as e:
            logger.error(f"Webhook processing failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def mark_order_paid(self, order_id: str):
        """Mark order as paid in your system"""
        # Update database
        logger.info(f"Order {order_id} marked as paid")

    def mark_order_failed(self, order_id: str):
        """Mark order as failed in your system"""
        # Update database
        logger.info(f"Order {order_id} marked as failed")

    def mark_order_expired(self, order_id: str):
        """Mark order as expired in your system"""
        # Update database
        logger.info(f"Order {order_id} marked as expired")

    def send_order_confirmation(self, webhook_event: WebhookEvent):
        """Send order confirmation to customer"""
        # Send email/SMS confirmation
        logger.info(f"Order confirmation sent for {webhook_event.transaction_id}")

    def send_payment_failure_notice(self, webhook_event: WebhookEvent):
        """Send payment failure notice to customer"""
        # Send email/SMS notification
        logger.info(f"Payment failure notice sent for {webhook_event.transaction_id}")

# Usage example
def main():
    """E-commerce checkout example"""
    integration = BizaoEcommerceIntegration(environment="sandbox")

    # Customer data
    customer = CustomerInfo(
        id="CUST-123",
        first_name="Awa",
        last_name="Traore",
        email="awa.traore@example.com",
        phone_number="+22507123456"
    )

    # Process checkout
    print("Processing e-commerce checkout...")
    checkout_result = integration.process_checkout(
        order_id="ORD-789",
        amount=25.50,  # 25.50 XOF
        currency=Currency.XOF,
        customer=customer,
        mobile_operator="orange"
    )

    if checkout_result['success']:
        print(f"Checkout successful!")
        print(f"Transaction ID: {checkout_result['transaction_id']}")
        print(f"Payment URL: {checkout_result['payment_link']}")
        print(f"Status: {checkout_result['status']}")

        # Simulate status checking
        time.sleep(2)
        status_result = integration.check_payment_status(checkout_result['transaction_id'])
        if status_result['success']:
            print(f"Payment status: {status_result['status']}")
    else:
        print(f"Checkout failed: {checkout_result['error']}")

if __name__ == "__main__":
    main()
```

### Subscription Payment Example

```python
from datetime import datetime, timedelta
import schedule

class BizaoSubscriptionService:
    def __init__(self):
        self.client = EasySwitch.from_env()

    def process_monthly_subscription(self, subscription_id: str, customer: CustomerInfo):
        """Process monthly subscription payment"""
        transaction_id = f"SUB-{subscription_id}-{datetime.now().strftime('%Y%m%d')}"

        transaction = TransactionDetail(
            transaction_id=transaction_id,
            provider=Provider.BIZAO,
            amount=2000,  # 20.00 XOF monthly fee
            currency=Currency.XOF,
            customer=customer,
            reason=f"Monthly subscription {subscription_id}",
            metadata={
                "subscription_id": subscription_id,
                "billing_cycle": "monthly",
                "due_date": datetime.now().isoformat()
            }
        )

        try:
            response = self.client.send_payment(transaction)

            # Store payment record
            self.save_subscription_payment(subscription_id, response)

            # Schedule next payment
            next_payment = datetime.now() + timedelta(days=30)
            self.schedule_next_payment(subscription_id, next_payment)

            return response

        except Exception as e:
            # Handle failed subscription payment
            self.handle_subscription_failure(subscription_id, str(e))
            raise

    def save_subscription_payment(self, subscription_id: str, response: PaymentResponse):
        """Save subscription payment record"""
        # Save to database
        pass

    def schedule_next_payment(self, subscription_id: str, next_date: datetime):
        """Schedule next subscription payment"""
        # Add to payment scheduler
        pass

    def handle_subscription_failure(self, subscription_id: str, error: str):
        """Handle subscription payment failure"""
        # Notify customer, update subscription status
        pass
```

## Error Handling

Comprehensive error handling is crucial for robust payment integration. EasySwitch provides specific exception types:

```python
from easyswitch.exceptions import (
    PaymentError,
    NetworkError,
    AuthenticationError,
    ValidationError,
    ConfigurationError,
    InvalidRequestError,
    UnsupportedOperationError
)

def process_payment_safely(transaction):
    """Process payment with comprehensive error handling"""
    try:
        result = client.send_payment(transaction)
        return {
            'success': True,
            'result': result
        }

    except ValidationError as e:
        # Invalid payment data (amount, phone format, etc.)
        return {
            'success': False,
            'error': 'validation_error',
            'message': 'Please check your payment details',
            'details': str(e)
        }

    except AuthenticationError as e:
        # API credential issues
        return {
            'success': False,
            'error': 'authentication_error',
            'message': 'Unable to authenticate with Bizao',
            'details': 'Please check your API credentials'
        }

    except ConfigurationError as e:
        # Configuration issues (missing required fields)
        return {
            'success': False,
            'error': 'configuration_error',
            'message': 'Payment service configuration error',
            'details': str(e)
        }

    except NetworkError as e:
        # Network connectivity issues
        return {
            'success': False,
            'error': 'network_error',
            'message': 'Unable to connect to payment service',
            'details': 'Please check your internet connection and try again'
        }

    except PaymentError as e:
        # Payment processing errors
        return {
            'success': False,
            'error': 'payment_error',
            'message': 'Payment could not be processed',
            'details': str(e)
        }

    except UnsupportedOperationError as e:
        # Unsupported operations (refunds, cancellations)
        return {
            'success': False,
            'error': 'unsupported_operation',
            'message': 'This operation is not supported by Bizao',
            'details': str(e)
        }

    except InvalidRequestError as e:
        # Invalid request format
        return {
            'success': False,
            'error': 'invalid_request',
            'message': 'Invalid request format',
            'details': str(e)
        }

    except Exception as e:
        # Unexpected errors
        return {
            'success': False,
            'error': 'unexpected_error',
            'message': 'An unexpected error occurred',
            'details': 'Please try again later'
        }
```

### Common Error Codes

| Error Type | Common Causes | Solutions |
|------------|---------------|-----------|
| **ValidationError** | Invalid phone format, amount out of range | Check phone E.164 format, verify amounts |
| **AuthenticationError** | Invalid credentials, expired tokens | Verify client ID/secret, check environment |
| **PaymentError** | Insufficient funds, operator unavailable | Check customer balance, try different operator |
| **NetworkError** | Connection timeout, DNS issues | Check internet connectivity, retry with backoff |
| **ConfigurationError** | Missing required config fields | Verify all required `extra` fields are set |

## Bizao Limitations

**Important**: Bizao has several API limitations that affect integration design:

### Unsupported Operations

| Operation | Bizao Support | Alternative |
|-----------|---------------|-------------|
| **Refunds** | Not supported | Manual processing via dashboard |
| **Transaction Cancellation** | Not supported | Contact Bizao support |
| **Partial Refunds** | Not supported | Manual processing via dashboard |
| **Transaction Detail Retrieval** | Not supported | Use `check_status()` instead |

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
            "provider": "bizao_manual"
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

Bizao provides a sandbox environment for testing your integration:

```python
# Test configuration
test_config = {
    "debug": True,
    "providers": {
        Provider.BIZAO: {
            "environment": "sandbox",
            "timeout": 30,
            "extra": {
                "dev_client_id": "test_client_id",
                "dev_client_secret": "test_client_secret",
                "dev_token_url": "https://preproduction-gateway.bizao.com/mobilemoney/oauth/token",
                "country-code": "CI",
                "mno-name": "orange",
                "channel": "web",
                "lang": "fr",
                "cancel_url": "https://test.example.com/cancel"
            }
        }
    }
}

test_client = EasySwitch.from_dict(test_config)
```

### Test Phone Numbers

Use these test phone numbers to simulate different payment scenarios:

| Country | Operator | Test Phone Number | Expected Result |
|---------|----------|------------------|-----------------|
| **Côte d'Ivoire** | Orange | +22507000001 | Success |
| **Côte d'Ivoire** | Orange | +22507000000 | Failure |
| **Côte d'Ivoire** | MTN | +22505000001 | Success |
| **Côte d'Ivoire** | MTN | +22505000000 | Failure |
| **Senegal** | Orange | +22177000001 | Success |
| **Senegal** | Orange | +22177000000 | Failure |
| **Mali** | Orange | +22370000001 | Success |
| **Mali** | Orange | +22370000000 | Failure |

### Test Amounts

For testing different scenarios, use these amounts:

| Amount (Minor Units) | Amount (Display) | Expected Behavior |
|---------------------|------------------|-------------------|
| 100 | 1.00 XOF | Success (minimum amount) |
| 50 | 0.50 XOF | Failure (below minimum) |
| 100000 | 1000.00 XOF | Success |
| 100000000 | 1000000.00 XOF | May fail (exceeds some limits) |

### Testing Different Channels

```python
# Test Web Channel
web_config = config.copy()
web_config["providers"][Provider.BIZAO]["extra"]["channel"] = "web"
web_client = EasySwitch.from_dict(web_config)

# Test TPE Channel (requires phone number)
tpe_config = config.copy()
tpe_config["providers"][Provider.BIZAO]["extra"]["channel"] = "tpe"
tpe_client = EasySwitch.from_dict(tpe_config)

# Test USSD Channel (requires phone number)
ussd_config = config.copy()
ussd_config["providers"][Provider.BIZAO]["extra"]["channel"] = "ussd"
ussd_client = EasySwitch.from_dict(ussd_config)
```

### Complete Testing Example

```python
import asyncio
from easyswitch import (
    EasySwitch, Provider, TransactionDetail,
    TransactionStatus, Currency, CustomerInfo
)

class BizaoTestSuite:
    def __init__(self):
        self.test_config = {
            "debug": True,
            "providers": {
                Provider.BIZAO: {
                    "environment": "sandbox",
                    "timeout": 30,
                    "extra": {
                        "dev_client_id": "test_client_id",
                        "dev_client_secret": "test_client_secret",
                        "dev_token_url": "https://preproduction-gateway.bizao.com/mobilemoney/oauth/token",
                        "country-code": "CI",
                        "mno-name": "orange",
                        "channel": "web",
                        "lang": "fr",
                        "cancel_url": "https://test.example.com/cancel"
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
            provider=Provider.BIZAO,
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
            provider=Provider.BIZAO,
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

    def test_webhook_validation(self):
        """Test webhook validation"""
        # Mock webhook payload
        test_payload = {
            "event_type": "payment.successful",
            "transaction_id": "TEST-SUCCESS-001",
            "status": "SUCCESSFUL",
            "amount": 1000,
            "currency": "XOF"
        }

        test_headers = {
            "X-Bizao-Signature": "t=1234567890,s=mock_signature"
        }

        try:
            # Note: This might fail in test due to signature validation
            is_valid = self.client.validate_webhook(test_payload, test_headers)
            print(f"Webhook validation test: {is_valid}")
            return is_valid
        except Exception as e:
            print(f"Webhook validation test: {e}")
            return False

    def run_all_tests(self):
        """Run complete test suite"""
        print("Starting Bizao integration test suite...")

        # Test successful payment
        success_response = self.test_successful_payment()

        # Test failed payment
        self.test_failed_payment()

        # Test status checking if we have a transaction
        if success_response:
            self.test_status_checking(success_response.transaction_id)

        # Test webhook validation
        self.test_webhook_validation()

        print("Test suite completed!")

# Run tests
if __name__ == "__main__":
    test_suite = BizaoTestSuite()
    test_suite.run_all_tests()
```

### Testing Checklist

Before going live, ensure you've tested:

- [ ] Payment creation with valid data (web, tpe, ussd channels)
- [ ] Payment creation with invalid data
- [ ] Payment status checking for all status types
- [ ] Webhook validation and parsing
- [ ] Webhook handling for all event types
- [ ] Error handling for all exception types
- [ ] Different phone number formats (E.164)
- [ ] Amount validation (minimum/maximum limits)
- [ ] Different currencies (XOF, XAF, CDF, GNF, USD)
- [ ] Different mobile operators per country
- [ ] Network timeout scenarios
- [ ] Authentication with invalid credentials
- [ ] Configuration validation

## Common Pitfalls & Troubleshooting

### 1. Amount Formatting Issues

**Problem**: Incorrect amount handling leading to payment failures.

```python
# Wrong: Using decimal amounts
transaction.amount = 25.50  # Will cause issues

# Correct: Using minor units (cents)
transaction.amount = 2550  # 25.50 XOF in minor units
```

**Solution**: Always convert amounts to minor units (multiply by 100 for XOF/XAF).

### 2. Phone Number Format Problems

**Problem**: Phone numbers not in E.164 format.

```python
# Wrong formats
phone = "07123456"        # Missing country code
phone = "22507123456"     # Missing + prefix
phone = "+225 07 12 34 56" # Contains spaces

# Correct format
phone = "+22507123456"    # E.164 format
```

**Solution**: Always use E.164 format: `+[country_code][number]`

### 3. Configuration Validation Errors

**Problem**: Missing required configuration fields.

```python
# Incomplete configuration
config = {
    "providers": {
        Provider.BIZAO: {
            "extra": {
                "dev_client_id": "id123",
                # Missing dev_client_secret, token_url, etc.
            }
        }
    }
}
```

**Solution**: Ensure all required fields are provided:

```python
# Complete configuration
required_fields = [
    "dev_client_id", "dev_client_secret", "dev_token_url",
    "prod_client_id", "prod_client_secret", "prod_token_url",
    "country-code", "mno-name", "channel", "lang", "cancel_url"
]
```

### 4. Webhook Signature Validation Issues

**Problem**: Webhook signature validation failing.

```python
# Check webhook secret configuration
webhook_secret = "your_webhook_secret_from_bizao_dashboard"

# Ensure webhook URL is correctly configured in Bizao dashboard
callback_url = "https://yourdomain.com/webhook/bizao"
```

**Solution**:
- Verify webhook secret matches Bizao dashboard
- Ensure HTTPS is used for webhook URLs
- Check that webhook URL is accessible from Bizao servers

### 5. Channel-Specific Requirements

**Problem**: Using wrong channel configuration for use case.

| Channel | Use Case | Requires Phone | Returns Payment Link |
|---------|----------|----------------|---------------------|
| `web` | Browser-based payments | No | Yes |
| `tpe` | Point of sale terminals | Yes | No |
| `ussd` | USSD code payments | Yes | No |

**Solution**: Choose appropriate channel and provide required fields.

### 6. Timeout Handling

**Problem**: Mobile money payments taking longer than expected.

```python
# Too short timeout
timeout = 10  # Seconds

# Adequate timeout for mobile money
timeout = 60  # Seconds - mobile money can be slow
```

**Solution**: Use appropriate timeouts (60+ seconds) and implement proper retry logic.

### 7. Currency and Country Mismatch

**Problem**: Using wrong currency for target country.

```python
# Wrong currency for country
config["extra"]["country-code"] = "CI"  # Côte d'Ivoire
transaction.currency = Currency.XAF     # Wrong! CI uses XOF

# Correct currency for country
config["extra"]["country-code"] = "CI"  # Côte d'Ivoire
transaction.currency = Currency.XOF     # Correct!
```

**Solution**: Match currency to country requirements:
- West Africa (CI, SN, ML, BF, TG, BJ, NE): XOF
- Central Africa (CM, TD, CF): XAF
- DRC: CDF
- Guinea: GNF

### 8. Idempotency and Duplicate Prevention

**Problem**: Duplicate transactions due to retry logic.

```python
import uuid
from datetime import datetime

def generate_unique_transaction_id(order_id: str) -> str:
    """Generate unique transaction ID to prevent duplicates"""
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    unique_suffix = uuid.uuid4().hex[:6]
    return f"TXN-{order_id}-{timestamp}-{unique_suffix}"

# Use unique transaction IDs
transaction_id = generate_unique_transaction_id("ORDER-123")
```

**Solution**: Always generate unique transaction IDs and implement proper duplicate detection.

## Troubleshooting Decision Tree

**Payment not working? Follow this guide:**

### Step 1: Check Phone Number Format
- Is phone number in E.164 format? (+225...)
- **No?** See [Phone Number Format Problems](#2-phone-number-format-problems)
- **Yes?** Continue to Step 2

### Step 2: Check Amount Format
- Is amount in minor units? (5000 not 50.00)
- **No?** See [Amount Formatting Issues](#1-amount-formatting-issues)
- **Yes?** Continue to Step 3

### Step 3: Check Authentication
- Getting authentication errors?
- **Yes?** Check credentials in [Configuration](#configuration)
- **No?** Continue to Step 4

### Step 4: Check Currency/Country Match
- Does currency match country? (CI = XOF, CM = XAF)
- **No?** See [Currency and Country Mismatch](#7-currency-and-country-mismatch)
- **Yes?** Continue to Step 5

### Step 5: Check Configuration
- Are all required fields present in config?
- **No?** See [Configuration Validation Errors](#3-configuration-validation-errors)
- **Yes?** Continue to Step 6

### Step 6: Check Network/Timeouts
- Is the request timing out?
- **Yes?** See [Timeout Handling](#6-timeout-handling)
- **No?** Check [Error Handling](#error-handling) section

### Still Having Issues?
1. Enable debug mode: `config["debug"] = True`
2. Check logs for detailed error messages
3. Verify you're using the correct environment (sandbox/production)
4. Test with test phone numbers from [Test Phone Numbers](#test-phone-numbers)
5. Contact [Support](#support--resources)

## Limits & Considerations

### Transaction Limits

| Currency | Minimum Amount | Maximum Amount* | Notes |
|----------|---------------|-----------------|-------|
| **XOF** | 100 (1.00 XOF) | 1,000,000 (10,000.00 XOF) | West Africa |
| **XAF** | 100 (1.00 XAF) | 1,000,000 (10,000.00 XAF) | Central Africa |
| **CDF** | 1,000 (10.00 CDF) | 1,000,000 (10,000.00 CDF) | DRC |
| **GNF** | 1,000 (10.00 GNF) | 1,000,000 (10,000.00 GNF) | Guinea |
| **USD** | 1 (1.00 USD) | 10,000 (100.00 USD) | International |

*Actual limits may vary by operator and country regulations.

### Processing Times

| Operation | Expected Time | Notes |
|-----------|---------------|-------|
| **Payment Initiation** | 1-5 seconds | API response time |
| **Mobile Money Processing** | 30 seconds - 5 minutes | Operator dependent |
| **USSD Response** | 1-30 seconds | Network dependent |
| **Webhook Delivery** | 1-10 seconds | After payment completion |
| **Status Updates** | Real-time | Via webhooks |

### Rate Limits

- **API Requests**: 100 requests per minute per client
- **Authentication**: 10 token requests per minute
- **Webhook Retries**: 3 attempts with exponential backoff
- **Concurrent Transactions**: 20 per merchant per minute

## Support & Resources

### Official Resources

- **Documentation**: [docs.bizao.com](https://docs.bizao.com)
- **Dashboard**: [dashboard.bizao.com](https://dashboard.bizao.com)
- **Support**: support@bizao.com
- **Phone Support**: Available in dashboard

### EasySwitch Resources

- **Documentation**: [EasySwitch Documentation](../index.md)
- **GitHub Issues**: [Report bugs and request features](https://github.com/easyswitch/easyswitch/issues)
- **Examples**: [Integration Examples](../examples/)
- **Configuration Guide**: [Configuration Documentation](../getting-started/configuration.md)

### Getting Help

1. **Check Documentation**: Review this guide and official Bizao docs
2. **Test in Sandbox**: Use test environment to reproduce issues
3. **Review Logs**: Check debug logs for detailed error information
4. **Contact Support**: Email support teams for technical assistance
5. **Community Forum**: Connect with other developers using EasySwitch

### Best Practices Summary

**Do:**
- Always test in sandbox before production
- Use E.164 format for phone numbers
- Convert amounts to minor units
- Implement comprehensive error handling
- Use appropriate timeouts (60+ seconds)
- Generate unique transaction IDs
- Validate webhook signatures
- Monitor integration with proper logging
- Keep credentials secure
- Handle unsupported operations gracefully

**Don't:**
- Expose credentials in client-side code
- Use decimal amounts directly
- Ignore webhook signature validation
- Assume refunds/cancellations are supported
- Use short timeouts for mobile money
- Hardcode configuration values
- Skip error handling
- Ignore rate limits
- Mix currencies and countries incorrectly

### Migration Notes

When upgrading your integration:

1. **Backup Configuration**: Save current working configuration
2. **Test Incrementally**: Test each feature in sandbox
3. **Monitor Metrics**: Watch success rates and error patterns
4. **Gradual Rollout**: Deploy changes gradually
5. **Rollback Plan**: Have a rollback strategy ready

---

This comprehensive guide provides everything needed to successfully integrate Bizao with EasySwitch. For additional help or questions not covered here, please refer to the support resources above.