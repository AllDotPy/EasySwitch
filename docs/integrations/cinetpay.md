

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

### Step 1: Prerequisites

Before starting, ensure you have:
- **Python 3.7+** installed on your system
- A **CinetPay merchant account** (sign up at [CinetPay Registration](https://app-new.cinetpay.com/register))
- Your **API credentials** from CinetPay dashboard
- A **text editor** or IDE (VS Code, PyCharm, etc.)

### Step 2: Installation

Install EasySwitch using pip:

```bash
# Install EasySwitch SDK
pip install easyswitch

```

### Step 3: Get Your CinetPay Credentials

1. **Login to CinetPay Merchant Portal**
   - Go to [CinetPay Merchant Portal](https://app-new.cinetpay.com)
   - Navigate to **Settings** → **API Keys**

2. **Copy Your Credentials**
   ```
   API Key: cp_test_xxxxxxxxx (for sandbox) or cp_live_xxxxxxxxx (for production)
   Site ID: 123456
   Secret Key: your_secret_key_here
   ```

3. **Create Webhook Endpoint**
   - In merchant portal, go to **Webhooks**
   - Add your webhook URL: `https://yoursite.com/webhook/cinetpay`

### Step 4: Environment Setup

Create a `.env` file in your project root:

```bash
# .env file
CINETPAY_API_KEY=cp_test_your_api_key_here
CINETPAY_SITE_ID=your_site_id
CINETPAY_SECRET=your_secret_key
CINETPAY_CALLBACK_URL=https://yoursite.com/webhook/cinetpay
CINETPAY_ENVIRONMENT=sandbox
```

**Important**: Never commit your `.env` file to version control!

### Step 5: Your First Payment (Complete Example)

Create a file called `payment_example.py`:

```python
import os
from dotenv import load_dotenv  # pip install python-dotenv
from easyswitch import (
    EasySwitch, Provider, TransactionDetail, 
    CustomerInfo, Currency, TransactionStatus
)

# Load environment variables
load_dotenv()

# Initialize EasySwitch client
client = EasySwitch.from_dict({
    "providers": {
        Provider.CINETPAY: {
            "api_key": os.getenv("CINETPAY_API_KEY"),
            "callback_url": os.getenv("CINETPAY_CALLBACK_URL"),
            "environment": os.getenv("CINETPAY_ENVIRONMENT", "sandbox"),
            "extra": {
                "site_id": os.getenv("CINETPAY_SITE_ID"),
                "secret": os.getenv("CINETPAY_SECRET"),
                "channels": "MOBILE_MONEY",  # Payment method
                "lang": "fr"  # Interface language (fr/en)
            }
        }
    }
})

def create_sample_payment():
    """Create a sample payment - perfect for testing"""
    
    # Create transaction details
    transaction = TransactionDetail(
        transaction_id="TXN-DEMO-001",  # Your unique ID
        provider=Provider.CINETPAY,
        amount=1000.0,  # Amount in XOF (10.00 XOF)
        currency=Currency.XOF,  # West African CFA Franc
        customer=CustomerInfo(
            first_name="John",
            last_name="Doe", 
            phone_number="+22507123456",  # Must include country code
            email="john.doe@example.com"  # Optional but recommended
        ),
        reason="Test payment - Order #DEMO-001"  # Description
    )
    
    try:
        # Send payment request to CinetPay
        print("Creating payment...")
        response = client.send_payment(transaction)
        
        print(f"Payment created successfully!")
        print(f"Payment URL: {response.payment_link}")
        print(f"Transaction ID: {response.transaction_id}")
        print(f"Payment Token: {response.transaction_token}")
        
        return response
        
    except Exception as e:
        print(f"Payment creation failed: {str(e)}")
        return None

def check_payment_status(transaction_id):
    """Check the status of a payment"""
    
    try:
        status_response = client.check_status(transaction_id)
        
        print(f"Transaction ID: {status_response.transaction_id}")
        print(f"Status: {status_response.status}")
        print(f"Amount: {status_response.amount} {status_response.currency}")
        
        if status_response.status == TransactionStatus.SUCCESSFUL:
            print("Payment completed successfully!")
        elif status_response.status == TransactionStatus.PENDING:
            print("Payment is still pending...")
        else:
            print(f"Payment failed or cancelled: {status_response.status}")
            
        return status_response
        
    except Exception as e:
        print(f"Status check failed: {str(e)}")
        return None

# Run the example
if __name__ == "__main__":
    print("CinetPay + EasySwitch Demo")
    print("=" * 40)
    
    # Create a payment
    payment_response = create_sample_payment()
    
    if payment_response:
        print("\n" + "=" * 40)
        print("Next Steps:")
        print("1. Copy the payment URL above")
        print("2. Open it in your browser")
        print("3. Complete the payment using test credentials")
        print("4. Check payment status using the transaction ID")
        
        print("\n" + "=" * 40)
        print("Checking payment status...")
        check_payment_status(payment_response.transaction_id)
```

### Step 6: Run Your First Payment

```bash
# Run the example
python payment_example.py
```

**Expected Output:**
```
CinetPay + EasySwitch Demo
========================================
Creating payment...
Payment created successfully!
Payment URL: https://checkout.cinetpay.com/payment/xxxxx
Transaction ID: TXN-DEMO-001
Payment Token: token_xxxxx

========================================
Next Steps:
1. Copy the payment URL above
2. Open it in your browser  
3. Complete the payment using test credentials
4. Check payment status using the transaction ID
```

### Step 7: Test Payment Credentials

For **sandbox testing**, use these test credentials on the payment page:

| Provider         | Phone Number          | PIN/Password |
|------------------|-----------------------|--------------|
| Orange Money     | `+225 07 XX XX XX XX` | `1234`       |
| MTN Mobile Money | `+225 05 XX XX XX XX` | `0000`       |
| Moov Money       | `+225 01 XX XX XX XX` | `1111`       |

**Note**: Replace XX with any digits. These are test credentials for sandbox only.

### What Happens Next?

1. **Customer Journey**: User clicks payment URL → Selects payment method → Enters credentials → Payment processed
2. **Webhook Notification**: CinetPay sends real-time notification to your webhook URL
3. **Status Updates**: You can check payment status programmatically
4. **Business Logic**: Update your database, send emails, fulfill orders, etc.

### Ready for Production?

Once testing is complete:
1. Change `CINETPAY_ENVIRONMENT` to `"production"`
2. Update API key to your live credentials (`cp_live_xxxxx`)
3. Set up proper webhook handling (see [Webhook Handling](#webhook-handling))
4. Implement proper error handling and logging

## Configuration

### Getting Your CinetPay Credentials

**Step 1: Create CinetPay Account**
1. Visit [CinetPay Merchant Registration](https://app-new.cinetpay.com/register) to create your account
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
        
        print("✅ CinetPay configuration is valid")
        return True
        
    except Exception as e:
        print(f"❌ Configuration validation failed: {e}")
        return False

# Usage
client = EasySwitch.from_env()
validate_cinetpay_config(client)
    }
})
```

---

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
