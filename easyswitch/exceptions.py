"""
EasySwitch - Custom Exceptions
"""
from typing import Any, Dict, Optional


class EasySwitchError(Exception):
    """Base Exception for EasySwitch SDK."""

    def __init__(
        self, message: str, 
        code: Optional[str] = None, 
        details: Optional[Dict[str, Any]] = None,
        **kwargs
    ):

        self.message = message
        self.code = code
        self.details = details or {}
        self.extra = kwargs
        super().__init__(self.message)


class ConfigurationError(EasySwitchError):
    """Configuration error in EasySwitch SDK."""
    pass


class AuthenticationError(EasySwitchError):
    """Authentication error with the provider."""
    pass


class InvalidRequestError(EasySwitchError):
    """Invalid request error."""
    pass


class APIError(EasySwitchError):
    """Base class for API errors."""

    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        provider: Optional[str] = None,
        raw_response: Optional[Dict[str, Any]] = None,
        **kwargs
    ):
        self.status_code = status_code
        self.provider = provider
        self.raw_response = raw_response or {}
        super().__init__(
            message=message,
            code=kwargs.get("code"),
            details={
                "status_code": status_code,
                "provider": provider,
                "raw_response": self.raw_response,
                **kwargs
            }
        )


class NetworkError(EasySwitchError):
    """Network error when communicating with the provider."""
    pass


class InvalidProviderError(EasySwitchError):
    """Invalid provider error."""
    pass


class TransactionNotFoundError(EasySwitchError):
    """Transaction not found error."""
    pass


class WebhookValidationError(EasySwitchError):
    """Webhook validation error."""
    pass


class RateLimitError(APIError):
    """Rate limit error when the API is called too frequently."""
    pass


class UnsupportedOperationError(EasySwitchError):
    """Unsupported operation error."""

    def __init__(self, message: str, provider: Optional[str] = None, **kwargs):
        self.provider = provider
        super().__init__(message=message, **kwargs)


class PaymentError(APIError):
    """Payment error when processing a payment."""
    pass


class WebhookError(APIError):
    """Webhook error when processing a webhook operation."""
    pass


class CustomerError(APIError):
    """Customer error when processing a customer creation."""
    pass


class CurrencyError(APIError):
    """Currency error when processing a transaction with an unsupported currency."""
    pass


class RefundError(APIError):
    """Refund error when processing a refund."""
    pass


class CancellationError(APIError):
    """Cancellation error when processing a cancellation."""
    pass


class BalanceError(APIError):
    """Balance error when processing a balance operation."""
    pass


class LogError(APIError):
    """Log error when processing a log operation."""
    pass


class ValidationError(EasySwitchError):
    """Validation error for request data."""
    
    def __init__(self, message: str, field: Optional[str] = None, **kwargs):
        self.field = field
        super().__init__(
            message = message,
            code = "validation_error",
            details = {"field": field, **kwargs}
        )