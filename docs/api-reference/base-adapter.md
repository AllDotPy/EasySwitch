# Base Adapter (`easyswitch.adapters.base`)

This module provides the foundation of EasySwitch's adapter system. Each payment provider has its own **adapter** class that implements a common interface, allowing EasySwitch to interact with any provider consistently.

---

## AdaptersRegistry

The **registry** is the central directory of all adapters. Adapters register themselves via a decorator.

```python
@AdaptersRegistry.register()            # Name is auto-derived from class name
class PaystackAdapter(BaseAdapter):
    ...
```

**Methods:**

| Method | Description |
|--------|-------------|
| `register(name=None)` | Decorator. Registers an adapter class. Name defaults to `ClassName.replace("Adapter", "").lower()` |
| `get(name)` | Returns the adapter **class** by name (case-insensitive). Raises `InvalidProviderError` if not found |
| `list()` | Returns a list of all registered adapter names |
| `all()` | Returns a list of all registered adapter classes |
| `clear()` | Clears the registry (for testing) |

---

## BaseAdapter

Abstract base class for all payment adapters. Every provider adapter must implement its methods.

### Class Attributes (set per provider)

| Attribute | Type | Description |
|-----------|------|-------------|
| `SANDBOX_URL` | `str` | Sandbox API base URL |
| `PRODUCTION_URL` | `str` | Production API base URL |
| `ENDPOINTS` | `Dict[str, str]` | API endpoint paths |
| `SUPPORTED_CURRENCIES` | `List[Currency]` | Currencies the provider supports |
| `MIN_AMOUNT` | `Dict[Currency, float]` | Minimum transaction amount per currency |
| `MAX_AMOUNT` | `Dict[Currency, float]` | Maximum transaction amount per currency |

### Constructor

```python
def __init__(self, config: ProviderConfig, context: Optional[Dict[str, Any]] = None)
```

- `config` may be a `ProviderConfig` instance or a plain dict (auto-converted)
- `context` provides additional runtime info (`debug_mode`, `log_config`, `default_currency`)

### Abstract Methods (MUST be implemented)

```python
def get_headers(self, authorization=False) -> Dict[str, str]
def get_credentials(self) -> Dict[str, Any]
def format_transaction(self, data: TransactionDetail) -> Dict[str, Any]
def get_normalize_status(self, status: str) -> TransactionStatus
def validate_credentials(self) -> bool

async def send_payment(self, transaction: TransactionDetail) -> PaymentResponse
async def check_status(self, transaction_id: str) -> TransactionStatusResponse
async def cancel_transaction(self, transaction_id: str) -> bool
async def get_transaction_detail(self, transaction_id: str) -> TransactionDetail
async def refund(self, transaction_id: str, amount=None, reason=None) -> PaymentResponse
async def validate_webhook(self, payload: Dict, headers: Dict) -> bool
async def parse_webhook(self, payload: Dict, headers: Dict) -> WebhookEvent
```

### Utility Methods

| Method | Description |
|--------|-------------|
| `get_client()` | Returns (or creates) an `HTTPClient` for the adapter |
| `get_context()` | Returns the context dict passed at construction |
| `provider_name()` | Returns the provider name (e.g. `"paystack"`) |
| `validate_transaction(tx)` | Validates amount, currency, and phone number |
| `supports_partial_refund()` | Returns `True` if provider supports partial refunds |
| `_get_base_url()` | Returns `SANDBOX_URL` or `PRODUCTION_URL` based on `config.environment` |

---

## Implementing a Custom Adapter

```python
from easyswitch.adapters.base import BaseAdapter, AdaptersRegistry
from easyswitch.types import (
    PaymentResponse, TransactionDetail, TransactionStatus,
    TransactionStatusResponse, WebhookEvent, Currency
)

@AdaptersRegistry.register()
class MyProviderAdapter(BaseAdapter):
    SANDBOX_URL = "https://sandbox.myprovider.com/api"
    PRODUCTION_URL = "https://api.myprovider.com"
    SUPPORTED_CURRENCIES = [Currency.XOF, Currency.USD]

    def validate_credentials(self) -> bool:
        return bool(self.config.api_key)

    def get_credentials(self):
        return {"api_key": self.config.api_key}

    def get_headers(self, authorization=False):
        headers = {"Content-Type": "application/json"}
        if authorization:
            headers["Authorization"] = f"Bearer {self.config.api_key}"
        return headers

    def format_transaction(self, tx: TransactionDetail) -> dict:
        return {
            "amount": tx.amount,
            "currency": tx.currency,
            "phone": tx.customer.phone_number,
        }

    def get_normalize_status(self, status: str) -> TransactionStatus:
        mapping = {"success": TransactionStatus.SUCCESSFUL, "fail": TransactionStatus.FAILED}
        return mapping.get(status.lower(), TransactionStatus.UNKNOWN)

    async def send_payment(self, tx: TransactionDetail) -> PaymentResponse:
        async with self.get_client() as client:
            response = await client.post(
                endpoint="/pay",
                json_data=self.format_transaction(tx),
                headers=self.get_headers(authorization=True),
            )
            return PaymentResponse(
                transaction_id=tx.transaction_id,
                provider=self.provider_name(),
                status=TransactionStatus.PENDING,
                amount=tx.amount,
                currency=tx.currency,
            )

    async def check_status(self, transaction_id: str) -> TransactionStatusResponse:
        ...

    async def cancel_transaction(self, transaction_id: str) -> bool:
        raise UnsupportedOperationError(
            message="Cancellation not supported",
            provider=self.provider_name(),
        )

    async def refund(self, transaction_id: str, amount=None, reason=None) -> PaymentResponse:
        raise UnsupportedOperationError(
            message="Refunds not supported",
            provider=self.provider_name(),
        )

    async def validate_webhook(self, payload: dict, headers: dict) -> bool:
        return True  # Implement HMAC verification

    async def parse_webhook(self, payload: dict, headers: dict) -> WebhookEvent:
        return WebhookEvent(
            event_type=payload.get("event", "unknown"),
            provider=self.provider_name(),
            transaction_id=payload.get("id", ""),
            status=TransactionStatus.UNKNOWN,
            amount=0,
            currency="XOF",
        )

    async def get_transaction_detail(self, transaction_id: str) -> TransactionDetail:
        raise UnsupportedOperationError(
            message="Not supported",
            provider=self.provider_name(),
        )
```

### Developer Checklist

Before publishing a new adapter, ensure you:

- [ ] Add `@AdaptersRegistry.register()` decorator
- [ ] Define `SANDBOX_URL` and `PRODUCTION_URL`
- [ ] Set `SUPPORTED_CURRENCIES`, `MIN_AMOUNT`, `MAX_AMOUNT`
- [ ] Implement `validate_credentials()` returning `bool`
- [ ] Implement `get_headers()` and `get_credentials()`
- [ ] Implement `send_payment()` and `check_status()`
- [ ] Implement `refund()` if the provider supports it
- [ ] Implement `validate_webhook()` and `parse_webhook()`
- [ ] Map provider statuses with `get_normalize_status()`
- [ ] Raise `UnsupportedOperationError(provider=self.provider_name())` for unsupported operations
- [ ] Use `async with self.get_client() as client:` for all HTTP calls
- [ ] Add the new `Provider` enum member to `easyswitch/types.py`
