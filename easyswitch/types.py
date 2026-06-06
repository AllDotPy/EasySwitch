"""
EasySwitch - Shared Types and Data Structures.
"""
import os
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional



####
##      AVAILABLE PROVIDER CHOICES
#####
class Provider(str, Enum):
    """ Available choices for supported Payment providers. """

    SEMOA = 'SEMOA'
    BIZAO = 'BIZAO'
    CINETPAY = 'CINETPAY'
    PAYGATE = 'PAYGATE'
    FEDAPAY = 'FEDAPAY'


####
##      SUPPORTED CURRENCIES
#####
class Currency(str, Enum):
    """Available Currencies Choices."""

    XOF = "XOF"  # CFA Franc (BCEAO)
    XAF = "XAF"  # CFA Franc (BEAC)
    NGN = "NGN"  # Nigerian Naira
    GHS = "GHS"  # Ghanaian Cedi
    EUR = "EUR"  # Euro
    USD = "USD"  # US Dollar
    CDF = "CDF"  # Congolese Franc
    GNF = "GNF"  # Guinean Franc
    KMF = "KMF"  # Comorian Franc
    GBP = "GBP"  # British Pound Sterling
    SEK = "SEK"  # Swedish Krona
    NOK = "NOK"  # Norwegian Krone
    DKK = "DKK"  # Danish Krone


####
##      SUPPORTED COUNTRIES
#####
class Countries(str, Enum):
    """Supported Countries Choices."""

    TOGO = 'TG'
    BENIN = 'BJ'
    GHANA = 'GH'
    BURKINA = 'BF'
    IVORY_COAST = 'CI'


####
##      TRANSACTION TYPES
#####
class TransactionType(str, Enum):
    """Supported transaction types."""

    PAYMENT = "payment"
    DEPOSIT = "deposit"
    WITHDRAWAL = "withdrawal"
    REFUND = "refund"
    TRANSFER = "transfer"


####
##      TRANSACTION STATUS
#####
class TransactionStatus(str, Enum):
    """Possible statues of a transaction."""

    PENDING = "pending"
    SUCCESSFUL = "successful"
    FAILED = "failed"
    ERROR = "error"
    CANCELLED = "cancelled"
    REFUSED = "refused"
    DECLINED = "declined"
    EXPIRED = "expired"
    REFUNDED = "refunded"
    PROCESSING = "processing"
    INITIATED = "initiated"
    UNKNOWN = "unknown"
    COMPLETED = "completed"
    TRANSFERRED = "transferred"


####
##      TRANSACTION STATUS RESPONSE
#####
@dataclass
class TransactionStatusResponse:
    """Standardized Transaction status response structure."""

    transaction_id: str
    provider: Provider
    status: TransactionStatus
    amount: float
    data: Dict[str, Any] = field(default_factory=dict)


####
##      CUSTOMER INFORMATION
#####
@dataclass
class CustomerInfo:
    """Customer informations."""

    phone_number: str = ""
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None
    postal_code: Optional[str] = None
    zip_code: Optional[str] = None
    state: Optional[str] = None
    id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


####
##      PAYMENT RESPONSE
#####
@dataclass
class PaymentResponse:
    """Standardized Payment response structure."""

    transaction_id: str
    provider: Provider
    status: TransactionStatus
    amount: float
    currency: Currency
    created_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    reference: Optional[str] = None
    payment_link: Optional[str] = None
    transaction_token: Optional[str] = None
    customer: Optional[CustomerInfo] = None
    raw_response: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def is_successful(self) -> bool:
        """Check if the transaction was successful."""
        return self.status == TransactionStatus.SUCCESSFUL
    
    @property
    def is_pending(self) -> bool:
        """Check if the transaction is pending."""
        return self.status in [
            TransactionStatus.PENDING,
            TransactionStatus.PROCESSING,
            TransactionStatus.INITIATED
        ]
    
    @property
    def is_failed(self) -> bool:
        """Check if the transaction failed."""
        return self.status in [
            TransactionStatus.FAILED,
            TransactionStatus.CANCELLED,
            TransactionStatus.EXPIRED
        ]


####
##      TRANSACTION DETAIL
#####
@dataclass
class TransactionDetail:
    """Standardized Transaction detail structure."""

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


####
##      WEBHOOK EVENT
#####
@dataclass
class WebhookEvent:
    """Standardized webhook event structure."""

    event_type: str
    provider: Provider
    transaction_id: str
    status: TransactionStatus
    amount: float
    currency: Currency
    created_at: Optional[datetime] = None
    raw_data: Dict[str, Any] = field(default_factory = dict)
    metadata: Dict[str, Any] = field(default_factory = dict)
    context: Dict[str,Any] = field(default_factory = dict)


####
##      API CREDENTIALS
#####
@dataclass
class ApiCredentials:
    """Authentication credentials for the API."""

    api_key: str
    api_secret: Optional[str] = None
    client_id: Optional[str] = None
    client_secret: Optional[str] = None
    merchant_id: Optional[str] = None
    token: Optional[str] = None
    master_key: Optional[str] = None
    private_key: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    app_id: Optional[str] = None
    callback_url: Optional[str] = None
    return_url: Optional[str] = None
    channels: Optional[str] = 'MOBILE_MONEY'  # Default to ALL channels
    lang: Optional[str] = 'fr'

    def load_from_env(self,provider: Provider):
        """Load credentials from environment variables."""

        for field in self.__dataclass_fields__:
            env_value = os.getenv(f'EASYSWITCH_{provider.upper()}_{field.upper()}')
            if env_value:
                setattr(self, field, env_value)
        return self
    
    def write_to_env(self,provider: Provider):
        """Write credentials to environment variables."""

        for field in self.__dataclass_fields__:
            env_value = getattr(self, field)
            if env_value:
                os.environ[f'EASYSWITCH_{provider.upper()}_{field.upper()}'] = env_value
        return self


####
##      PAGINATION META
#####
@dataclass
class PaginationMeta:
    """Standardized pagination metadata structure."""
    current_page: int
    next_page: Optional[int]
    prev_page: Optional[int]
    per_page: int
    total_pages: int
    total_count: int
