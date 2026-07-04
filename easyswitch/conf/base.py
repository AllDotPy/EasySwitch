"""
EasySwitch - Configs Base
"""

from abc import ABC, abstractmethod
from enum import Enum
from pathlib import Path
from typing import Any, Dict, Optional, Type

from pydantic import BaseModel, Field, field_validator, model_validator, ValidationInfo

from easyswitch.exceptions import ConfigurationError
from easyswitch.types import Currency, Provider


####
##     LOG LEVELs
#####
class LogLevel(str, Enum):
    """Log Levels"""

    DEBUG = 'debug'
    INFO = 'info'
    WARNING = 'warning'
    ERROR = 'error'
    CRITICAL = 'critical'


####
##      LOG FORMAT CHOICES
#####
class LogFormat(str, Enum):
    """Log Format choices."""

    PLAIN = 'plain'
    JSON = 'json'


####
##      LOGGING CONFIG MODEL CLASS
#####
class LoggingConfig(BaseModel):
    """Logging Configuration Model"""

    enabled: bool = False
    level: LogLevel = LogLevel.INFO
    file: Optional[str] = None
    console: bool = True
    max_size: int = 10  # MB
    backups: int = 5
    compress: bool = True
    format: LogFormat = LogFormat.PLAIN
    rotate: bool = True


####
##      BASE CONFIGURATION CLASS
#####
class BaseConfigModel(BaseModel):
    """Base class of all configuration models."""

    class Config:
        extra = 'forbid'  # Undefined fields are not allowed
        validate_default = True
        use_enum_values = True


####
##      PROVIDER CONFIGURATION CLASS
#####
class ProviderConfig(BaseConfigModel):
    """A configuration model for Providers."""

    api_key: Optional[str] = None
    api_secret: Optional[str] = None
    token: Optional[str] = None
    base_url: Optional[str] = None
    callback_url: Optional[str] = None
    return_url: Optional[str] = None
    timeout: int = 30
    environment: str = "sandbox"    # sandbox|production
    extra: Dict[str, Any] = {}      # Extra data (specific for each provider)

    @field_validator('environment')
    def validate_environment(cls, v):
        """ Ensure Config's environment value is valid. """

        if v not in ('sandbox', 'production'):
            raise ConfigurationError(
                "Environment must be 'sandbox' or 'production'"
            )
        return v

    @model_validator(mode='before')
    @classmethod
    def check_keys(cls, v):
        """ Ensure that at least one of api_key or api_secret is provided. """

        if not (v.get("api_key") or v.get("api_secret")):
            raise ConfigurationError(
                "At least one of 'api_key' or 'api_secret' must be provided"
            )
        return v



####
##      ROOT CONFIGURATION CLASS
#####
class RootConfig(BaseConfigModel):
    """Configuration root, represents EasySwitch config."""

    environment: str = "sandbox"
    """ API environment (sandbox|production). Applied to all providers by default. """

    timeout: int = 30
    """ Default timeout in seconds for all providers. """

    debug: bool = False
    """ If True, enable debug mode. """

    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    """ Logging configurations. """

    default_currency: str = Currency.XOF

    providers: Dict[Provider, ProviderConfig] = Field(default_factory=dict)
    """ Enabled providers. """

    default_provider: Optional[Provider] = None
    
    @field_validator('default_provider')
    @classmethod
    def validate_default_provider(cls, v, info: ValidationInfo):
        """Ensure default provider is valid."""
        
        # Ensure default provider is in enabled providers
        if v is not None:
            providers = info.data.get('providers')
            if providers and v not in providers:
                raise ValueError(
                    f"Default provider {v} must be in enabled providers"
                )
        
        # and in supported Providers
        if v is not None and v not in Provider.__members__:
            raise ValueError(
                f"Default provider {v} is not supported"
            )
        return v
    
    @field_validator('default_currency')
    def validate_default_currency(cls, v):
        """ Ensure Config's default currency value is valid. """

        if v not in Currency.__members__:
            raise ConfigurationError(
                f"Invalid default currency value '{v}'"
                f"available choices are: {Currency.__members__}."
            )
        return v


####
##      BASE CONFIGURATION SOURCE CLASS 
#####
class BaseConfigSource(ABC):
    """Base interface for all configuration sources."""

    @abstractmethod
    def load(self) -> Dict[str, Any]:
        """Loads configurations from the source."""
        pass

    @abstractmethod
    def is_valid(self) -> bool:
        """Check if the sourse is valid"""
        pass