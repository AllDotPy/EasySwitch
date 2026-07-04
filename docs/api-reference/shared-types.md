# Shared Types (`easyswitch.types`)

The `easyswitch.types` module defines the **shared enums and dataclasses** used across the SDK.
These ensure that all providers, responses, and events follow a consistent format.

---

## Provider Enum

```python
class Provider(str, Enum):
```

Represents all **supported payment aggregators**.

| Member | Value | Description |
|--------|-------|-------------|
| `CINETPAY` | `"CINETPAY"` | CinetPay |
| `SEMOA` | `"SEMOA"` | Semoa |
| `BIZAO` | `"BIZAO"` | Bizao |
| `PAYGATE` | `"PAYGATE"` | PayGate Global |
| `FEDAPAY` | `"FEDAPAY"` | FedaPay |
| `PAYSTACK` | `"PAYSTACK"` | Paystack |
| `MTN` | `"MTN"` | MTN Mobile Money |
| `AIRTEL_MONEY` | `"AIRTEL_MONEY"` | Airtel Money |
| `QOSPAY` | `"QOSPAY"` | QosPay (coming soon) |
| `PAYPLUS` | `"PAYPLUS"` | PayPlus (coming soon) |
| `KKIAPAY` | `"KKIAPAY"` | KkiaPay (coming soon) |
| `PAYDUNYA` | `"PAYDUNYA"` | PayDunya (coming soon) |

---

## Currency Enum

```python
class Currency(str, Enum):
```

| Member | Value | Description |
|--------|-------|-------------|
| `XOF` | `"XOF"` | CFA Franc BCEAO (West Africa) |
| `XAF` | `"XAF"` | CFA Franc BEAC (Central Africa) |
| `NGN` | `"NGN"` | Nigerian Naira |
| `GHS` | `"GHS"` | Ghanaian Cedi |
| `EUR` | `"EUR"` | Euro |
| `USD` | `"USD"` | US Dollar |
| `CDF` | `"CDF"` | Congolese Franc |
| `GNF` | `"GNF"` | Guinean Franc |
| `KMF` | `"KMF"` | Comorian Franc |
| `UGX` | `"UGX"` | Ugandan Shilling |
| `TZS` | `"TZS"` | Tanzanian Shilling |
| `KES` | `"KES"` | Kenyan Shilling |
| `RWF` | `"RWF"` | Rwandan Franc |
| `ZMW` | `"ZMW"` | Zambian Kwacha |
| `MWK` | `"MWK"` | Malawian Kwacha |
| `BIF` | `"BIF"` | Burundian Franc |
| `ETB` | `"ETB"` | Ethiopian Birr |
| `BWP` | `"BWP"` | Botswanan Pula |
| `ZWL` | `"ZWL"` | Zimbabwean Dollar |

---

## Countries Enum

```python
class Countries(str, Enum):
```

| Member | Value | Description |
|--------|-------|-------------|
| `TOGO` | `"TG"` | Togo |
| `BENIN` | `"BJ"` | Benin |
| `GHANA` | `"GH"` | Ghana |
| `BURKINA` | `"BF"` | Burkina Faso |
| `IVORY_COAST` | `"CI"` | Côte d'Ivoire |

---

## TransactionType Enum

```python
class TransactionType(str, Enum):
```

| Member | Value | Description |
|--------|-------|-------------|
| `PAYMENT` | `"payment"` | Customer → merchant payment |
| `DEPOSIT` | `"deposit"` | Wallet/account deposit |
| `WITHDRAWAL` | `"withdrawal"` | Wallet/account withdrawal |
| `REFUND` | `"refund"` | Refund of previous transaction |
| `TRANSFER` | `"transfer"` | Transfer between accounts |

---

## TransactionStatus Enum

```python
class TransactionStatus(str, Enum):
```

| Member | Value | Description |
|--------|-------|-------------|
| `PENDING` | `"pending"` | Awaiting processing |
| `SUCCESSFUL` | `"successful"` | Completed successfully |
| `FAILED` | `"failed"` | Failed permanently |
| `ERROR` | `"error"` | Technical error |
| `CANCELLED` | `"cancelled"` | Cancelled by user/system |
| `REFUSED` | `"refused"` | Refused by provider |
| `DECLINED` | `"declined"` | Declined (insufficient funds, etc.) |
| `EXPIRED` | `"expired"` | Payment expired |
| `REFUNDED` | `"refunded"` | Transaction refunded |
| `PROCESSING` | `"processing"` | In progress |
| `INITIATED` | `"initiated"` | Initiated but not yet sent |
| `UNKNOWN` | `"unknown"` | Unrecognised state |
| `COMPLETED` | `"completed"` | Fully completed |
| `TRANSFERRED` | `"transferred"` | Successfully transferred |

---

## Data Structures

### TransactionStatusResponse

```python
@dataclass
class TransactionStatusResponse:
    transaction_id: str
    provider: Provider
    status: TransactionStatus
    amount: float
    data: Dict[str, Any]
```

Returned by `client.check_status()`.

---

### CustomerInfo

```python
@dataclass
class CustomerInfo:
    phone_number: str = ""
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None
    postal_code: Optional[str] = None
    state: Optional[str] = None
    id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
```

Used when creating a transaction. `phone_number` is typically the only required field.

---

### PaymentResponse

```python
@dataclass
class PaymentResponse:
    transaction_id: str
    provider: Provider
    status: TransactionStatus
    amount: float
    currency: Currency
    created_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    reference: Optional[str] = None
    payment_link: Optional[str] = None     # URL to redirect customer to
    transaction_token: Optional[str] = None
    customer: Optional[CustomerInfo] = None
    raw_response: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
```

**Properties:**
- `is_successful` → `True` if `status == TransactionStatus.SUCCESSFUL`
- `is_pending` → `True` if status is `PENDING`, `PROCESSING`, or `INITIATED`
- `is_failed` → `True` if status is `FAILED`, `CANCELLED`, or `EXPIRED`

---

### TransactionDetail

```python
@dataclass
class TransactionDetail:
    transaction_id: str
    provider: Provider
    amount: float
    currency: Currency
    status: TransactionStatus = TransactionStatus.PENDING
    transaction_type: TransactionType = TransactionType.PAYMENT
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    customer: Optional[CustomerInfo] = None
    reference: Optional[str] = None
    reason: Optional[str] = None
    callback_url: Optional[str] = None
    return_url: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    raw_data: Dict[str, Any] = field(default_factory=dict)
```

The main input for `client.send_payment()`.

---

### WebhookEvent

```python
@dataclass
class WebhookEvent:
    event_type: str
    provider: Provider
    transaction_id: str
    status: TransactionStatus
    amount: float
    currency: Currency
    created_at: Optional[datetime] = None
    raw_data: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    context: Dict[str, Any] = field(default_factory=dict)
```

Returned by `client.parse_webhook()`.

---

### PaginationMeta

```python
@dataclass
class PaginationMeta:
    current_page: int
    next_page: Optional[int]
    prev_page: Optional[int]
    per_page: int
    total_pages: int
    total_count: int
```

Standardised pagination metadata (used by FedaPay's list endpoints).
