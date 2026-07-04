"""
EasySwitch - Logging Utility
"""
import logging
import os
import sys
from typing import Any, Dict, Optional, Union


def setup_logger(
    name: str = "easyswitch",
    level: Union[int, str] = logging.INFO,
    log_format: Optional[str] = None,
    log_file: Optional[str] = None,
    console: bool = True
) -> logging.Logger:
    """
    Configure and return a logger.
    
    Args:
        name: Logger name
        level: Logging level
        log_format: Log message format
        log_file: Path to log file
        console: Enable console output
        
    Returns:
        logging.Logger: Configured logger
    """
    logger = logging.getLogger(name)
    
    # Set logging level
    if isinstance(level, str):
        level = getattr(logging, level.upper(), logging.INFO)
    
    logger.setLevel(level)
    
    # Avoid duplicate handlers
    if logger.handlers:
        return logger
    
    # Default format
    if log_format is None:
        log_format = "[%(asctime)s] %(levelname)s [%(name)s.%(funcName)s:%(lineno)d] %(message)s"
    
    formatter = logging.Formatter(log_format)
    
    # Add file handler if specified
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    # Add console handler if requested
    if console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    
    return logger


def sanitize_logs(data: Dict[str, Any], sensitive_fields: Optional[list] = None) -> Dict[str, Any]:
    """
    Sanitize log data by masking sensitive information.
    
    Args:
        data: Data to sanitize
        sensitive_fields: List of sensitive fields to mask
        
    Returns:
        Dict[str, Any]: Sanitized data
    """
    if sensitive_fields is None:
        sensitive_fields = [
            "password", "api_key", "secret", "token", "private_key",
            "api_secret", "client_secret", "card_number", "cvv", "signature"
        ]
    
    sanitized = {}
    sensitive_lower = [f.lower() for f in sensitive_fields]
    
    for key, value in data.items():
        if key.lower() in sensitive_lower:
            if isinstance(value, str) and value:
                visible_chars = min(4, len(value) // 4)
                sanitized[key] = value[:visible_chars] + "*" * (len(value) - visible_chars)
            else:
                sanitized[key] = "***"
        elif isinstance(value, dict):
            sanitized[key] = sanitize_logs(value, sensitive_fields)
        elif isinstance(value, list) and value and isinstance(value[0], dict):
            sanitized[key] = [sanitize_logs(item, sensitive_fields) if isinstance(item, dict) else item for item in value]
        else:
            sanitized[key] = value
    
    return sanitized


class PaymentLogger:
    """
    Specialized logger for payment operations.
    Records payment events with appropriate information.
    """
    
    def __init__(self, logger_name: str = "easyswitch.payment"):
        """
        Initialize the payment logger.
        
        Args:
            logger_name: Logger name
        """
        self.logger = logging.getLogger(logger_name)
    
    def payment_initiated(self, provider: str, amount: float, currency: str, reference: str, **kwargs):
        """Record payment initiation."""
        self.logger.info(
            f"Payment initiated | Provider: {provider} | Amount: {amount} {currency} | Ref: {reference}",
            extra=sanitize_logs(kwargs)
        )
    
    def payment_success(self, provider: str, amount: float, currency: str, reference: str, transaction_id: str, **kwargs):
        """Record successful payment."""
        self.logger.info(
            f"Payment successful | Provider: {provider} | ID: {transaction_id} | Amount: {amount} {currency} | Ref: {reference}",
            extra=sanitize_logs(kwargs)
        )
    
    def payment_failed(self, provider: str, reference: str, reason: str, **kwargs):
        """Record failed payment."""
        self.logger.error(
            f"Payment failed | Provider: {provider} | Ref: {reference} | Reason: {reason}",
            extra=sanitize_logs(kwargs)
        )
    
    def refund_initiated(self, provider: str, transaction_id: str, amount: Optional[float] = None, **kwargs):
        """Record refund initiation."""
        amount_str = f"Amount: {amount}" if amount else "Total amount"
        self.logger.info(
            f"Refund initiated | Provider: {provider} | ID: {transaction_id} | {amount_str}",
            extra=sanitize_logs(kwargs)
        )
    
    def refund_success(self, provider: str, transaction_id: str, amount: Optional[float] = None, **kwargs):
        """Record successful refund."""
        amount_str = f"Amount: {amount}" if amount else "Total amount"
        self.logger.info(
            f"Refund successful | Provider: {provider} | ID: {transaction_id} | {amount_str}",
            extra=sanitize_logs(kwargs)
        )
    
    def refund_failed(self, provider: str, transaction_id: str, reason: str, **kwargs):
        """Record failed refund."""
        self.logger.error(
            f"Refund failed | Provider: {provider} | ID: {transaction_id} | Reason: {reason}",
            extra=sanitize_logs(kwargs)
        )
    
    def webhook_received(self, provider: str, event_type: str, transaction_id: Optional[str] = None, **kwargs):
        """Record webhook reception."""
        tx_info = f"| ID: {transaction_id}" if transaction_id else ""
        self.logger.info(
            f"Webhook received | Provider: {provider} | Event: {event_type} {tx_info}",
            extra=sanitize_logs(kwargs)
        )
    
    def api_request(self, provider: str, method: str, endpoint: str, **kwargs):
        """Record API request."""
        self.logger.debug(
            f"API request | Provider: {provider} | {method} {endpoint}",
            extra=sanitize_logs(kwargs)
        )
    
    def api_response(self, provider: str, status_code: int, endpoint: str, **kwargs):
        """Record API response."""
        log_level = logging.DEBUG if 200 <= status_code < 300 else logging.ERROR
        self.logger.log(
            log_level,
            f"API response | Provider: {provider} | Status: {status_code} | Endpoint: {endpoint}",
            extra=sanitize_logs(kwargs)
        )


# Create a default instance of the logger
payment_logger = PaymentLogger()

# Default logger configuration
logger = setup_logger(
    level=os.getenv("EASYSWITCH_LOG_LEVEL", "INFO"),
    log_file=os.getenv("EASYSWITCH_LOG_FILE"),
    console=os.getenv("EASYSWITCH_LOG_CONSOLE", "1") != "0"
)