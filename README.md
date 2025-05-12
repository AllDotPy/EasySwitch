# EasySwitch😎 Python Library

**EasySwitch** is a unified **Python SDK for Mobile Money** integration across major aggregators in West Africa. It provides a single, consistent interface to simplify payment processing, reduce code duplication, and accelerate development.

## Currently Supported Providers
- <img src = 'https://docs.cinetpay.com/images/logo-new.png' height = 60 >
- <img src = 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcR9eIXxPvwTKAgJYxFO7mR6ZGIrTaK16qFI0UsGnIQg&s' height = 60 >
<!-- - <img src = 'https://www.fedapay.com/wp-content/themes/fedapay_theme/pictures/feda-logo-blue-new.svg' height = 60 > -->
- <img src = 'https://bankassurafrik.com/wp-content/uploads/2022/07/telechargement-2.png' height = 60>

<!-- ## Next
We will add progressively support for following Providers:
- <img src = 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcT3sWIPK8p28IQhWbqKpewYYtCHZaAk6O98T4dUiEhp&s' height = 60 ></img> 
<span style = 'margin-left:10'></span>
<img src = 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQstE0NII74XhnGdDhMDWpA-7uL55uaooz3fn-yjrvl6g&s' height = 60 ></img><span style = 'margin-left:10'></span><img src = 'https://asset.brandfetch.io/idBsplB3mt/idyp_5HZE4.png' height = 55 >
</img> -->

<!-- - <img src = 'https://bankassurafrik.com/wp-content/uploads/2022/07/telechargement-2.png' height = 60 ></img>
<span style = 'margin-left:10'></span><img src = 'https://payplus.africa/img/logo.png' height = 60 ></img>
<span style = 'margin-left:10'></span>
<img src = 'https://paydunya.com/refont/images/logo/blue_logo.png' height = 60 ></img> -->


## 🚀 Features

- 🔌 Unified API for multiple payment gateways
- ⚙️ Supports configuration from `.env`, JSON, YAML, or native Python dict
- 🔐 Centralized management of API keys and credentials
- 📈 Fully customizable logging (file, console, rotating, compression)
- 🧩 Extensible via a plugin-like adapter registration system

---

## Prerequisites

You need to have at least 3.9 version of python to be able to continue.


## Install

```sh
pip install easyswitch
```

## ⚙️ Configuration Options

You can configure EasySwitch using:

1. .env file with environment variables
2. A JSON configuration file
3. A YAML configuration file
4. A native Python dictionary

### Example `.env` file
```ini
# This file is a sample. Copy it to .env and fill in the values.

# General configuration
EASYSWITCH_ENVIRONMENT=development              # or production
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

## 🧑‍💻 Usage Example

```python
from easyswitch import EasySwitch
# 1. From environment variables
client = EasySwitch.from_env()

# 2. From a JSON file
client = EasySwitch.from_json("config.json")

# 3. from a Python dict
config = {
    "environment": "sandbox",
    "providers": {
        "cinetpay": {
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

## Road map
`EasySwitch` is still under heavy maintenance, we decided to ship it in this early stage so you can help us make it better.

Add Support for following Providers:

- [x] Cinetpay
- [x] Bizao
- [x] Semoa
- [ ] Fedapay
- [ ] Kkiapay
- [ ] PayGate
- [ ] MTN
- [ ] PayPlus
- [ ] QOSPAY
- [ ] Paydunya

## 🤝 Contributing

We welcome contributions from the community! Please see the [CONTRIBUTING.md](CONTRIBUTING.md) guide for more information.

<br>
<p align = 'center'>
    <img src='dotpy_blue_transparent.png?raw=true' height = '60'></img>
</p>
<p align = 'center'>Made with ❤️ By AllDotPy</p>
<!-- <p height='60' align = 'center'>© 2024 DotPy, Inc. All rights reserved.</p> -->
