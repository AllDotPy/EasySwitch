"""
EasySwitch - Fonctions de validation
"""
import hashlib
import hmac
import json
import re
from typing import Any, Dict, Optional, Union

from easyswitch.exceptions import ValidationError


def validate_phone_number(
        phone_number: str, 
        country_code: Optional[str] = None
) -> str:
    """
    Validate and format a phone number.
    
    Args:
        phone_number: the phone number to validate
        country_code: Country code (ISO 3166-1 alpha-2)
        
    Returns:
        str: A validated and formatted phone number
        
    Raises:
        ValidationError: if the phone number is invalid
    """
    # Remove all non-digit characters
    cleaned = re.sub(r'\D', '', phone_number)
    
    # Check the min len  (at least 8 digits without country code)
    # and max len (at most 15 digits)
    if len(cleaned) < 8:
        raise ValidationError(
            message="The phone number must contain at least 8 digits.",
            field="phone_number"
        )
    
    # Handle country prefixes
    if country_code:
        country_code = country_code.upper()
        prefixes = {
            "CI": "225", # Ivory Coast
            "SN": "221", # Senegal
            "BJ": "229", # Benin
            "TG": "228", # Togo
            "BF": "226", # Burkina Faso
            "ML": "223", # Mali
            "NE": "227", # Niger
            "GH": "233", # Ghana
            "NG": "234"  # Nigeria
        }
        
        # Add country prefix if necessary
        if country_code in prefixes:
            prefix = prefixes[country_code]
            # Strip international call prefixes (00, +) already removed by \D, but double-zero remains
            cleaned = cleaned.lstrip('0')
            if not cleaned.startswith(prefix):
                cleaned = prefix + cleaned
    
    return cleaned


def validate_amount(amount: Union[float, int, str], min_value: float = 0.01) -> float:
    """
    Validates an amount.
    
    Args:
        amount: Amount to validate
        min_value: Minimum allowed value
        
    Returns:
        float: Validated amount
        
    Raises:
        ValidationError: If the amount is invalid
    """
    try:
        amount_float = float(amount)
    except (ValueError, TypeError):
        raise ValidationError(
            message="Amount must be a number",
            field="amount"
        )
    
    if amount_float < min_value:
        raise ValidationError(
            message=f"Amount must be greater than or equal to {min_value}",
            field="amount"
        )
    
    return amount_float


def validate_currency(currency: str, supported_currencies: Optional[list] = None) -> str:
    """
    Validates a currency code.
    
    Args:
        currency: Currency code to validate
        supported_currencies: List of supported currencies
        
    Returns:
        str: Validated currency code
        
    Raises:
        ValidationError: If the currency is invalid
    """
    currency_upper = currency.upper()
    
    # Default list of supported currencies if none provided
    if supported_currencies is None:
        supported_currencies = ["XOF", "XAF", "NGN", "GHS", "EUR", "USD"]
    
    if currency_upper not in supported_currencies:
        raise ValidationError(
            message=f"Unsupported currency: {currency}. Valid currencies: {', '.join(supported_currencies)}",
            field="currency"
        )
    
    return currency_upper


def validate_reference(reference: str, max_length: int = 50) -> str:
    """
    Validates a transaction reference.
    
    Args:
        reference: Reference to validate
        max_length: Maximum allowed length
        
    Returns:
        str: Validated reference
        
    Raises:
        ValidationError: If the reference is invalid
    """
    if not reference or not isinstance(reference, str):
        raise ValidationError(
            message="Reference cannot be empty",
            field="reference"
        )
    
    # Remove leading and trailing spaces
    reference = reference.strip()
    
    if len(reference) > max_length:
        raise ValidationError(
            message=f"Reference is too long (maximum {max_length} characters)",
            field="reference"
        )
    
    # Check that the reference contains only allowed characters
    if not re.match(r'^[a-zA-Z0-9_\-\.]+$', reference):
        raise ValidationError(
            message="Reference must contain only letters, numbers, hyphens, dots and underscores",
            field="reference"
        )
    
    return reference


def validate_webhook_signature(
    payload: Union[str, bytes, Dict[str, Any]],
    signature: str,
    secret: str,
    algorithm: str = 'sha256'
) -> bool:
    """
    Validates a webhook signature.
    
    Args:
        payload: Webhook payload
        signature: Signature to validate
        secret: Secret key for verification
        algorithm: Hashing algorithm to use
        
    Returns:
        bool: True if signature is valid, False otherwise
    """
    if isinstance(payload, dict):
        payload = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
    elif isinstance(payload, str):
        payload = bytes(payload.encode('utf-8'))
    
    # Calculate HMAC
    if algorithm.lower() == 'sha256':
        computed_signature = hmac.new(
            secret.encode('utf-8'),
            payload,
            hashlib.sha256
        ).hexdigest()
    elif algorithm.lower() == 'sha512':
        computed_signature = hmac.new(
            secret.encode('utf-8'),
            payload,
            hashlib.sha512
        ).hexdigest()
    else:
        raise ValueError(f"Unsupported algorithm: {algorithm}")
    
    # Compare signatures
    return hmac.compare_digest(computed_signature, signature.lower())


def validate_email(email: str) -> str:
    """
    Validates an email address.
    
    Args:
        email: Email address to validate
        
    Returns:
        str: Validated email address
        
    Raises:
        ValidationError: If the email address is invalid
    """
    # Simple regex for email validation
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    
    if not re.match(email_pattern, email):
        raise ValidationError(
            message="Invalid email address",
            field="email"
        )
    
    return email.lower()