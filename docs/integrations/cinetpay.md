# CinetPay Integration Guide

<div align="center">
  
![CinetPay Integration](https://img.shields.io/badge/CinetPay-Integration-blue?style=for-the-badge&logo=paypal)
![EasySwitch](https://img.shields.io/badge/EasySwitch-SDK-green?style=for-the-badge)
![West Africa](https://img.shields.io/badge/West_Africa-Payments-orange?style=for-the-badge)

**Professional Mobile Money Integration for West African Markets**

*Streamline your payment processing with CinetPay through the EasySwitch SDK*

[![Documentation](https://img.shields.io/badge/docs-complete-brightgreen)](.)
[![Python](https://img.shields.io/badge/python-3.7+-blue)](https://python.org)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

</div>

---

## Table of Contents

- [Quick Start](#quick-start)
- [Configuration](#configuration)
- [Implementation Guide](#implementation-guide)
- [Webhook Handling](#webhook-handling)
- [Error Handling](#error-handling)
- [Common Issues](#common-issues)
- [Production Guidelines](#production-guidelines)
- [API Reference](#api-reference)

---

## Quick Start

### Installation and Basic Setup

```python
from easyswitch import EasySwitch, Provider, TransactionDetail, CustomerInfo, Currency

client = EasySwitch.from_env()

transaction = TransactionDetail(
    transaction_id="TXN-001",
    provider=Provider.CINETPAY,
    amount=5000.0,
    currency=Currency.XOF,
    customer=CustomerInfo(
        first_name="John",
        last_name="Doe",
        phone_number="+22570123456",
        email="john@example.com"
    ),
    reason="Order payment"
)

response = client.send_payment(transaction)
print(f"Payment URL: {response.payment_link}")
```

## Configuration

### Environment Variables

```bash
export CINETPAY_API_KEY="your_api_key"
export CINETPAY_SITE_ID="your_site_id"
export CINETPAY_SECRET="your_secret"
export CINETPAY_CALLBACK_URL="https://yoursite.com/webhook/cinetpay"
export CINETPAY_ENVIRONMENT="sandbox"
```

### Configuration Options

| Parameter      | Required | Description           | Example                          |
|----------------|----------|-----------------------|----------------------------------|
| `api_key`      | Yes      | Your CinetPay API key | `"cp_live_abc123..."`            |
| `site_id`      | Yes      | Your CinetPay site ID | `"123456"`                       |
| `secret`       | Yes      | Your webhook secret   | `"secret_key"`                   |
| `callback_url` | Yes      | Webhook endpoint URL  | `"https://yoursite.com/webhook"` |
| `environment`  | Yes      | sandbox or production | `"sandbox"`                      |
| `channels`     | No       | Payment channels      | `"MOBILE_MONEY"`                 |
| `lang`         | No       | Interface language    | `"fr"`                           |

### Client Initialization

```python
from easyswitch import EasySwitch, Provider

client = EasySwitch.from_env()

client = EasySwitch.from_dict({
    "providers": {
        Provider.CINETPAY: {
            "api_key": "your_api_key",
            "site_id": "your_site_id",
            "secret": "your_secret",
            "callback_url": "https://yoursite.com/webhook/cinetpay",
            "environment": "sandbox",
            "extra": {
                "channels": "MOBILE_MONEY",
                "lang": "fr"
            }
        }
    }
})
```

---

## Implementation Guide


## CinetPay Payment Flow

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

## Customer Payment Journey

```
╔══════════════════════════════════════════════════════════════════════╗
║                          PAYMENT FLOW                                ║
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

### Required Transaction Fields

| Field                   | Type     | Required | Description                   |
|-------------------------|----------|----------|-------------------------------|
| `transaction_id`        | string   | Yes      | Unique transaction identifier |
| `amount`                | float    | Yes      | Amount in currency base unit  |
| `currency`              | Currency | Yes      | XOF, XAF, CDF, GNF, USD       |
| `customer.first_name`   | string   | Yes      | Customer first name           |
| `customer.last_name`    | string   | Yes      | Customer last name            |
| `customer.phone_number` | string   | Yes      | Phone with country code       |
| `customer.email`        | string   | No       | Customer email address        |
| `reason`                | string   | No       | Transaction description       |

### Creating a Payment

```python
from easyswitch import TransactionDetail, CustomerInfo, Currency, Provider

def create_payment(order_data):
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
