"""
EasySwitch - Base Adapter for Payment Integrations
"""
import abc
from typing import Any, ClassVar, Dict, List, Optional, Type

from easyswitch.conf import ProviderConfig
from easyswitch.exceptions import (InvalidProviderError,
                                    ValidationError)
from easyswitch.types import (Currency, PaymentResponse, TransactionDetail,
                              TransactionStatus, TransactionStatusResponse)
from easyswitch.utils import USER_AGENT
from easyswitch.utils.http import HTTPClient
from easyswitch.utils.validators import (validate_amount, validate_currency,
                                         validate_phone_number)


####
##      ADAPERS REGISTRY CLASS
#####
class AdaptersRegistry:
    """
    Registry for all payment adapters.
    This class is used to register and retrieve adapters based on their provider.
    """
    
    _registry: ClassVar[Dict[str, Type["BaseAdapter"]]] = {} # type: ignore

    @classmethod
    def register(cls, name: Optional[str] = None) -> None: # type: ignore
        """Register a new Adapter class."""

        def wrapper(adapter: Type["BaseAdapter"]):
            """Wrapper"""

            nonlocal name
            name = name or adapter.provider_name()
            name = name.upper()
            if name not in cls._registry.keys():
                cls._registry[name] = adapter
                
            return adapter

        return wrapper

    @classmethod
    def get(cls, name: str) -> Type["BaseAdapter"]: # type: ignore
        """Get an Adapter class by its name."""

        if name not in cls._registry:
            raise InvalidProviderError(
                f"Invalid Adapter name: '{name}' not found."
                )
        
        return cls._registry[name]

    @classmethod
    def all(cls) -> List[Type["BaseAdapter"]]: # type: ignore
        """Get all registered Adapters classes."""
        return list(cls._registry.values())

    @classmethod
    def clear(cls) -> None:
        """Clear the registry."""
        cls._registry.clear()

    @classmethod
    def list(cls) -> List[str]:
        """List all registered Adapters names."""
        return list(cls._registry.keys())


####
##      BASE ADAPTER CLASS
#####
class BaseAdapter(abc.ABC):
    """
    Base class for all payment adapters.
    This class defines the common interface that all adapters must implement.
    """

    REQUIRED_FIELDS: List[str] = []
    """List of required fields for the adapter."""

    SANDBOX_URL: str = ""
    """Sandbox URL for the adapter."""

    PRODUCTION_URL: str = ""
    """Production URL for the adapter."""

    ENDPOINTS: Dict[str, str] = {}
    """API endpoints for the adapter."""

    SUPPORTED_CURRENCIES: List[Currency] = []
    """List of supported currencies for the adapter."""

    MIN_AMOUNT: ClassVar[Dict[Currency, float]] = {}
    """Minimum amount for the adapter."""

    MAX_AMOUNT: ClassVar[Dict[Currency, float]] = {}
    """Maximum amount for the adapter."""

    VERSION: str = "1.0.0"
    """Adapter version"""

    # api_config: Optional[ProviderConfig] = None
    # """API credentials for the adapter."""

    client: Optional[HTTPClient] = None
    """HTTP client for the adapter."""
    
    def __init__(
        self, 
        config: ProviderConfig, 
        context: Optional[Dict[str,Any]] = None
    ):
        """
        Initialize the adapter with the provided configuration.
        
        Args:
            config: The EasySwitch configuration object
        (Note: This should contain all necessary configuration for the adapter)
        (Note: This may include API keys, endpoints, etc.)
        """
        self.config = config
        self.context = context

        # Initialize the adapter with the provided configuration
        # This may include setting up API keys, endpoints, etc.
        # This should be implemented by each specific adapter
        self._initialize_adapter()

        # check api configs
        if not self.validate_credentials():
            raise InvalidProviderError(
                f"Invalid credentials for provider {self.provider_name()}"
            )

    def _initialize_adapter(self):
        """
        Initialize the adapter with the provided configuration.
        This method should be implemented by each specific adapter.
        It should set up the API keys, endpoints, etc.
        """

        # Setting up the HTTP client
        self.client = self.get_client()

    def get_client(self) -> HTTPClient:
        """
        Get the HTTP client for the adapter.
        This method should be implemented by each specific adapter.
        It should return the HTTP client used for making API requests.
        
        Returns:
            Any: The HTTP client for the adapter
        """
        if not self.client or self.client.is_closed:
            # Initialize the HTTP client if not already initialized
            return HTTPClient(
                base_url = self._get_base_url(),
                default_headers = {
                    **self.get_headers(),
                    'User-Agent': USER_AGENT
                },
                timeout = self.config.timeout,
                debug = self.context.get('debug_mode', False)
            )
            
        # Return the HTTP client
        return self.client

    @abc.abstractmethod
    def get_headers(self, authorization=False) -> Dict[str, str]:
        """
        Get the headers for the adapter.
        This method should be implemented by each specific adapter.
        It should return the headers required for the API requests.
        
        Returns:
            Dict[str, str]: The headers for the adapter
        """
        pass

    @abc.abstractmethod
    def get_credentials(self) -> ProviderConfig:
        """
        Get the credentials for the adapter.
        This method should be implemented by each specific adapter.
        It should return the credentials required for the API requests.
        
        Returns:
            ApiCredentials: The credentials for the adapter
        """
        pass

    @classmethod
    def supports_partial_refund(cls) -> bool:
        """ True if the provider supports partial refund. """
        return False
    
    def get_context(self):
        """Return extra context attributes passed to a specific adapter"""
        return self.context or {}
    
    @abc.abstractmethod
    async def send_payment(
        self,
        transaction: TransactionDetail,
    ) -> PaymentResponse:
        """
        Send a payment request to the provider.
        This method should be implemented by each specific adapter.
        It should handle the payment process and return a standardized response.
        
        Args:
            amount: Transaction amount
            phone_number: Client's phone number
            currency: Transaction currency
            reference: Unique reference for the transaction
            customer_info: Extra information about the customer (optional)
            metadata: Custom metadata for the transaction (optional)
            
        Returns:
            PaymentResponse: A standardized response from the payment provider
        """
        pass
    
    @abc.abstractmethod
    async def check_status(self, transaction_id: str) -> TransactionStatus:
        """
        Check the status of a transaction.
        This method should be implemented by each specific adapter.
        It should return the current status of the transaction.
        
        Args:
            transaction_id: Transaction identifier
            
        Returns:
            TransactionStatus: Transaction status
        """
        pass
    
    @abc.abstractmethod
    async def cancel_transaction(self, transaction_id: str) -> bool:
        """
        Cancel a transaction if possible.
        
        Args:
            transaction_id: Transaction identifier
            (Note: Not all providers support cancellation)
            
        Returns:
            bool: True if the transaction was successfully cancelled, False otherwise
        """
        pass

    @abc.abstractmethod
    async def get_transaction_detail(self, transaction_id: str) -> TransactionDetail:
        """
        Fetch full detail for a transaction if supported.
        
        Args:
            transaction_id: Transaction identifier
            (Note: Not all providers support transaction object retrieval)
            
        Returns:
            TransactionDetail: The retrieved Transaction Details
        """
        pass
    
    @abc.abstractmethod
    async def refund(
        self,
        transaction_id: str,
        amount: Optional[float] = None,
        reason: Optional[str] = None
    ) -> PaymentResponse:
        """
        Make a refund for a transaction.
        This method should be implemented by each specific adapter.
        It should handle the refund process and return a standardized response.
        Note: If the amount is None, the full amount will be refunded.
        If the provider does not support partial refunds, this method should raise an exception.
        
        Args:
            transaction_id: Transaction identifier
            amount: The amount to refund (if None, refund the full amount)
            (Note: Not all providers support partial refunds)
            reason: Reason for the refund (optional)
            (Note: Not all providers require a reason)
            
        Returns:
            PaymentResponse: Refund request response
        """
        pass
    
    @abc.abstractmethod
    async def validate_webhook(
        self, 
        payload: Dict[str, Any], 
        headers: Dict[str, str]
    ) -> bool:
        """
        Validate an incoming webhook.
        This method should be implemented by each specific adapter.
        It should check the authenticity of the webhook and return True if valid, False otherwise.
        This is important for security reasons.
        
        Args:
            payload: The content of the webhook
            (Note: This is the body of the request)
            (Note: This may be in a different format depending on the provider)
            headers: The headers of the request
            (Note: This may contain authentication information)
            
        Returns:
            bool: True if the webhook is valid, False otherwise
        """
        pass
    
    @abc.abstractmethod
    async def parse_webhook(
        self, 
        payload: Dict[str, Any], 
        headers: Dict[str, str]
    ) -> Dict[str, Any]:
        """
        Analyse a webhook, extract relevant information and return a standardized response.
        This method should be implemented by each specific adapter.
        It should convert the webhook data into a standardized format.
        This is important for consistency across different providers and 
        should be called only after the webhook has been validated.
        
        Args:
            payload: The content of the validated webhook
            headers: The request headers
            
        Returns:
            Dict[str, Any]: The parsed webhook data
        (Note: This should be a standardized format)
        """
        pass
    
    @classmethod
    def provider_name(cls) -> str:
        """
        Get the name of the provider.
        
        Returns:
            str: The name of the provider
        """
        return cls.__name__.replace("Adapter", "").lower()
    
    @abc.abstractmethod
    def validate_credentials(self) -> bool:
        """
        Validate the credentials for the provider.
        This method should be implemented by each specific adapter to
        check if the provided credentials are valid for the specific adapter.

        Returns:
            bool: True if the credentials are valid, False otherwise
        """
        return True

    def get_required_fields(self) -> List[str]:
        """
        Get the required fields for the provider.
        
        Returns:
            List[str]: A list of required fields
        """
        return self.REQUIRED_FIELDS
    
    def validate_transaction(self, transaction: TransactionDetail) -> bool:
        """
        Validate the transaction data.
        This method should be implemented by each specific adapter to
        check if the transaction data is valid for the specific adapter.
        
        Args:
            transaction: The transaction data to validate
            
        Returns:
            bool: True if the transaction is valid, False otherwise
        """

        # Validate the amount range
        validate_amount(
            transaction.amount,
            self.MIN_AMOUNT.get(transaction.currency, 0),
        )

        # Validate the maximum amount if configured
        max_amount = self.MAX_AMOUNT.get(transaction.currency)
        if max_amount is not None and transaction.amount > max_amount:
            raise ValidationError(
                message=(
                    f"Amount {transaction.amount} exceeds maximum "
                    f"of {max_amount} for {transaction.currency.value}"
                ),
                field="amount",
            )
        
        # Validate the currency
        validate_currency(
            transaction.currency, 
            self.SUPPORTED_CURRENCIES
        )
        
        # Validate the phone number
        validate_phone_number(
            transaction.customer.phone_number
        )
        return True

    @abc.abstractmethod
    def format_transaction(self, data: TransactionDetail) -> Dict[str, Any]:
        """
        Convert the data from the standardized format to the provider-specific format.
        This method should be implemented by each specific adapter to
        convert the standardized fields to the provider-specific format.
        
        Args:
            data: The data to convert
            
        Returns:
            Dict[str, Any]: The converted data
        """
        return data
    
    @abc.abstractmethod
    def get_normalize_status(self, status: str) -> TransactionStatus:
        """
        Normalize the status from the provider to the standardized format.
        This method should be implemented by each specific adapter to
        convert the provider-specific status to the standardized format.
        
        Args:
            status: The status to normalize
            
        Returns:
            TransactionStatus: The normalized status
        """
        return TransactionStatus.UNKNOWN
    
    def _get_base_url(self) -> str:
        """
        Get the base URL for the provider.
        This method should be implemented by each specific adapter to
        return the base URL for the specific adapter.
        
        Returns:
            str: The base URL for the provider
        """
        return (
            self.SANDBOX_URL if 
            self.config.environment == "sandbox" else 
            self.PRODUCTION_URL
        )