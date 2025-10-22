# EasySwitch😎 Python Library

# What is EasySwitch?
**EasySwitch** is a unified **Python SDK for Mobile Money** integration across major aggregators in West Africa. It provides a single, consistent interface to simplify payment processing, reduce code duplication, and accelerate development.

# Why EasySwitch?

Integrating different payment providers usually means learning different APIs, handling inconsistent error messages, and rewriting code to switch providers. EasySwitch was created to eliminate this complexity:

- 🚀 Accelerate your integrations
- 🔁 Switch providers without changing your code
- 🧱 Leverage a robust, type-safe, async-first architecture
- 🌍 Support local and international aggregators

## Currently Supported Providers

<table>
  <tr>
    <td align="center" width="33%">
      <img src="docs/assets/logo/providers/logo-cinetpay.png" height="60" alt="CinetPay"><br/>
      <strong>CinetPay</strong>
    </td>
    <td align="center" width="33%">
      <img src="docs/assets/logo/providers/logo-semoa.png" height="60" alt="Semoa"><br/>
      <strong>Semoa</strong>
    </td>
    <td align="center" width="33%">
      <img src="docs/assets/logo/providers/logo-paygate.png" height="60" alt="PayGate"><br/>
      <strong>PayGate</strong>
    </td>
  </tr>
  <tr>
    <td align="center">
      <img src="docs/assets/logo/providers/logo-bizao.jpg" height="80" alt="Bizao"><br/>
      <strong>Bizao</strong>
    </td>
    <td align="center">
      <img src="docs/assets/logo/providers/logo-fedapay.png" height="60" alt="FedaPay"><br/>
      <strong>FedaPay</strong>
    </td>
    <td align="center">
      <img src="docs/assets/logo/providers/logo-paystack.png" height="60" alt="PayStack"><br/>
      <strong>PayStack</strong>
    </td>
  </tr>
  <tr>
    <td align="center">
      <img src="docs/assets/logo/providers/logo-airtel-money.png" height="60" alt="Airtel Money"><br/>
      <strong>Airtel Money</strong>
    </td>
    <td align="center">
    </td>
    <td align="center">
    </td>
  </tr>
</table>

## 🚀 Features

- 🔌 Unified API for multiple payment gateways
- ⚙️ Supports configuration from `.env`, JSON, YAML, or native Python dict
- 🔐 Centralized management of API keys and credentials
- 📈 Fully customizable logging (file, console, rotating, compression)
- 🧩 Extensible via a plugin-like adapter registration system
- ✅ Strong **Exception** handling
- ✅ **Asynchronous** support for optimal performance
- ✅ **Automatic Retry** in case of network failures

---

## Community & Support 💬

- [Documentation](https://alldotpy.github.io/EasySwitch/) 📚 (under contructions.)
- [Issue Tracker](https://github.com/AllDotPy/EasySwitch/issues) 🐛

---

## Prerequisites

You need to have at least 3.13 version of python to be able to continue.


## Install

```sh
# Uising pip
pip install easyswitch
# Or using uv
uv add easyswitch
```

# Core Concepts

## ⚙️ Configuration
EasySwitch uses a centralized configuration object to define providers, credentials, default settings, and adapter mappings.

### **1. ⚙️ Supported Configuration sources**  

| Source               | Description                                  | Example |
|-----------------------|---------------------------------------------|---------|
| **Environment Variables**   | Load configs from a `.env` file or System Environment | [see example](#-exemple-de-fichier-env) |
| **Native Python Dictionary** | Direct configuration in your code          | [see exemple](#-configuration-depuis-un-dictionnaire) |
| **JSON File**      | Load configs from a JSON file           | [see example](#-configuration-depuis-json) |
| **YAML File**      | Load configs from a YAML file           | [see example](#-configuration-depuis-yaml) |


### **🔹 Example of `.env` file**

```ini
# This file is a sample. Copy it to .env and fill in the values.

# General configuration
EASYSWITCH_ENVIRONMENT=sandbox                  # or production
EASYSWITCH_TIMEOUT=30                           # seconds
EASYSWITCH_DEBUG=true                           # Enable debug mode

# Logging configuration
# Note: Logging configuration is only used if EASYSWITCH_LOGGING is set to true

EASYSWITCH_LOGGING=true                         # Enable file logging
EASYSWITCH_LOG_LEVEL=info                       # debug, info, warning, error
EASYSWITCH_LOG_FILE=/var/log/easyswitch.log     # Path to the log file
EASYSWITCH_CONSOLE_LOGGING=true                 # Enable console logging
EASYSWITCH_LOG_MAX_SIZE=10                      # Maximum size of the log file in MB
EASYSWITCH_LOG_BACKUPS=5                        # Number of backup log files to keep
EASYSWITCH_LOG_COMPRESS=true                    # Whether to compress old log files
EASYSWITCH_LOG_FORMAT=plain                     # Format of the log file (plain or json)
EASYSWITCH_LOG_ROTATE=true                      # Whether to rotate the log file

# Payment gateway configuration
EASYSWITCH_ENABLED_PROVIDERS=cinetpay,semoa     # Comma-separated list of enabled payment providers
EASYSWITCH_DEFAULT_PROVIDER=cinetpay            # Default payment provider
EASYSWITCH_CURRENCY=XOF                         # Default currency

# Providers configuration
# NOTE: these are standadized variables for all providers. 

# CINETPAY
# Note: Only required if EASYSWITCH_ENABLED_PROVIDERS includes 'cinetpay'
# You don't need to fill in all of these variables. Only fill in the ones you need.
EASYSWITCH_CINETPAY_API_KEY=your_cinetpay_api_key
EASYSWITCH_CINETPAY_X_SECRET=your_cinetpay_secret_key
EASYSWITCH_CINETPAY_X_STIE_ID=your_cinetpay_site_id
EASYSWITCH_CINETPAY_CALLBACK_URL=your_cinetpay_callback_url
EASYSWITCH_CINETPAY_X_CHANNELS=ALL
EASYSWITCH_CINETPAY_X_LANG=fr

# SEMOA
# Note: Only required if EASYSWITCH_ENABLED_PROVIDERS includes 'semoa'
# You don't need to fill in all of these variables. Only fill in the ones you need.
EASYSWITCH_SEMOA_API_KEY=your_semoa_api_key
EASYSWITCH_SEMOA_X_CLIENT_ID=your_semoa_client_id
EASYSWITCH_SEMOA_X_CLIENT_SECRET=your_semoa_client_secret
EASYSWITCH_SEMOA_X_USERNAME=your_semoa_username
EASYSWITCH_SEMOA_X_PASSWORD=your_semoa_password
EASYSWITCH_SEMOA_X_CALLBACK_URL=your_semoa_callback_url   # Optional
```

---

### **🔹 Example of python dictionary** 

```python
from easyswitch import (
    EasySwitch, TransactionDetail, Provider,
    TransactionStatus, Currency, TransactionType,
    CustomerInfo
)

config = {
    "debug": True,
    "providers": {
        Provider.CINETPAY: {
            "api_key": "your_api_key",
            "base_url": "https://api.exemple.com/v1", # Optional
            "callback_url": "https://api.exemple.com/v1/callback",
            "return_url": "https://api.exemple.com/v1/return",
            "environment": "production",     # Optional sandbox by default
            "extra": {
                "secret": "your_secret",
                "site_id": "your_site_id",
                "channels": "ALL",     # More details on Cinetpay's documentation.
                "lang": "fr"        # More details on Cinetpay's documentation.
            }
        },
        Provider.BIZAO: {
            "api_key": "your_api_key",
            "base_url": "https://api.exemple.com/v1", # Optional
            "callback_url": "https://api.exemple.com/v1/callback",
            "return_url": "https://api.exemple.com/v1/return",
            "environment": "production",     # Optional sandbox by default
            "timeout":30,
            "extra": {
                # Dev Configs
                "dev_client_id": "your_dev_client_id",
                "dev_client_secret": "your_dev_client_secret",
                "dev_token_url": "https://your_dev_token_url.com",     

                # Prod Configs
                "prod_client_id": "your_prod_client_id",
                "prod_client_secret": "your_prod_client_secret",
                "prod_token_url": "https://your_dev_token_url.com",

                # Global configs
                "country-code": Countries.IVORY_COAST,
                "mno-name": "orange",
                "channel": "web",
                "lang": "fr",
                "cancel_url": "https/example.com/cancel"
            }
        },
    }
}

client = EasySwitch.from_dict(config)
```

---

### **🔹 Configuration from JSON file**  

```python
client = EasySwitch.from_json("config.json")
```

---

### **🔹 Configuration from YAML file**  

```python
client = EasySwitch.from_yaml("config.yaml")
```

## Adapters
Adapters are pluggable classes that implement the logic for each payment aggregator. They provide standardized methods (send_payment, check_status, refund, etc.).

## 🧑‍💻 Usage Example
### 1. Client Initialization

```python
from easyswitch import EasySwitch
# 1. From environment variables
client = EasySwitch.from_env()

# 2. From a JSON file
client = EasySwitch.from_json("config.json")

# 3. from a Python dict
config = {
    "providers": {
        Provider.CINETPAY: {
            "api_key": "your_api_key",
            "base_url": "https://api.exemple.com/v1", # Optional
            "callback_url": "https://api.exemple.com/v1/callback",
            "return_url": "https://api.exemple.com/v1/return",
            "environment": "production"     # Optional sandbox by default
            "extra": {
                "secret": "your_secret",
                "site_id": "your_site_id",
                "channels": "ALL"     # More details on Cinetpay's documentation.
                "lang": "fr"        # More details on Cinetpay's documentation.
            }
        }
    }
}
client = EasySwitch.from_dict(config)

# 4. Merging multiple sources
client = EasySwitch.from_multi_sources(
    env_file=".env",  # Main config
    json_file="overrides.json"  # Overrides
)

# 5. Direct usage with RootConfig
from easyswitch.conf.base import RootConfig
config = RootConfig(...)
client = EasySwitch.from_config(config)
```

### 2. Create transaction (Order)

```python
from easyswitch import (
    EasySwitch, TransactionDetail, Provider,
    TransactionStatus, Currency, TransactionType,
    CustomerInfo
)

# Creating a Transaction
t = TransactionDetail(
    transaction_id = 'xveahdk-82998n9f8uhgj',
    provider = Provider.CINETPAY,
    status = TransactionStatus.PENDING, # Default value
    currency = Currency.XOF,
    amount = 150,
    transaction_type = TransactionType.PAYMENT,  # Default value
    reason = 'My First Transaction Test with EasySwitch\'s CinetPay client.',
    reference = 'my_ref',
    customer = CustomerInfo(
        phone_number = '+22890000000',
        first_name = 'Wil',
        last_name = 'Eins',
        address = '123 Rue képui, Lomé', # Optional
        city = 'Lomé',  # Optional
    )
)

```

---

### 3. Initialize Payment

```python

# Initializing Payment
res = client.send_payment(t)    # Will send payment request to CinetPay 
print(res)

'''
PaymentResponse(
    transaction_id = 'xveahdk-82998n9f8uhgj', 
    provider = 'cinetpay', 
    status = <TransactionStatus.PENDING: 'pending'>, 
    amount = 150, currency=<Currency.XOF: 'XOF'>, 
    created_at = datetime.datetime(2025, 5, 13, 16, 43, 19, 193307), 
    expires_at = None, 
    reference = 'my_ref', 
    payment_link = 'https://checkout.cinetpay.com/payment/d6a902e9b398bbbf6f600ca0ac9df8d86d865dd73157a0b2f7c67c877361b1f880d16ee44404e8a0744cf57ad85f89f56f06ae9037fb5d', 
    transaction_token = 'd6a902e9b398bbbf6f600ca0ac9df8d86d865dd73157a0b2f7c67c877361b1f880d16ee44404e8a0744cf57ad85f89f56f06ae9037fb5d', 
    customer = CustomerInfo(
        phone_number = '+22890000000', 
        first_name = 'Wil', 
        last_name = 'Eins', 
        email = None, 
        address = '123 Rue képui, Lomé', 
        city = 'Lomé', 
        country = None, 
        postal_code = None, 
        zip_code = None, 
        state = None, 
        id = None
), 
    raw_response = {
        'code': '201', 
        'message': 'CREATED', 
        'description': 'Transaction created with success', 
        'data': {
            'payment_token': 'd6a902e9b398bbbf6f600ca0ac9df8d86d865dd73157a0b2f7c67c877361b1f880d16ee44404e8a0744cf57ad85f89f56f06ae9037fb5d', 
            'payment_url': 'https://checkout.cinetpay.com/payment/d6a902e9b398bbbf6f600ca0ac9df8d86d865dd73157a0b2f7c67c877361b1f880d16ee44404e8a0744cf57ad85f89f56f06ae9037fb5d'
        }, 
        'api_response_id': '1747154599.4854'
    }, 
    metadata = {}
)
'''
```

---

### 4. Check transaction status

```python
res = client.check_status(
    t.id,   # Transaction ID
    Provider.CINETPAY   # Optional default to default provider
)
```

---

### 5. Webhook Events management

```python

# Validate a webhook
is_valid = client.validate_webhook(
    provider = Provider.CINETPAY,
    payload = request.body,
    headers = request.headers
)

# Parse a Webhook
event = client.parse_webhook(
    provider = Provider.CINETPAY,
    payload = request.body,
    headers = request.headers
)
```

---


## Integration road map
`EasySwitch` is still under heavy maintenance, we decided to ship it in this early stage so you can help us make it better.

Add Support for following Providers:

- [x] Cinetpay
- [x] Bizao
- [x] Semoa
- [x] PayGate
- [x] Fedapay
- [x] Airtel Money
- [x] PayStack
- [ ] MTN
- [ ] Kkiapay
- [ ] Orange
- [ ] PayPlus
- [ ] QOSPAY
- [ ] Paydunya

---

## **📜 Licence**  

MIT License.  

---

## **Community & Support 💬**  

For any question, please open a **Github issue**. 
- [Discord Community](https://discord.gg/Q8ZFsrkt) 💬

---

## 🤝 Contributing

We welcome contributions from the community! Please see the [CONTRIBUTING.md](CONTRIBUTING.md) guide for more information.

🚀 **Simplify your payment integrations with EasySwitch !** 🚀

<br>
<p align = 'center'>
    <img src='dotpy_blue_transparent.png?raw=true' height = '60'></img>
</p>
<p align = 'center'>Made with ❤️ By AllDotPy</p>
<!-- <p height='60' align = 'center'>© 2024 DotPy, Inc. All rights reserved.</p> -->
